"""
Base Firestore service class

Moved from services/base_firestore_service.py to prevent circular imports.
This provides the foundation for all Firestore-based services.
"""

import json
import logging
from datetime import datetime, timezone, date
from typing import Any, AsyncGenerator, Dict, Generic, List, Optional, TypeVar, Type, Union

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from pydantic import BaseModel, ValidationError

from ...exceptions import ResourceNotFoundError, ServiceError, ValidationError as ServiceValidationError

# Type variable for the model type
T = TypeVar('T', bound=BaseModel)


def _sanitize_firestore_data(data: Any) -> Any:
    """
    Recursively sanitize data before sending to Firestore.
    Converts datetime.date objects to datetime.datetime objects since Firestore
    only supports datetime.datetime, not datetime.date.
    """
    if isinstance(data, date) and not isinstance(data, datetime):
        # Convert date to datetime (start of day in UTC)
        return datetime.combine(data, datetime.min.time()).replace(tzinfo=timezone.utc)

    if isinstance(data, BaseModel):
        # Convert Pydantic model to dict and sanitize recursively
        return _sanitize_firestore_data(data.model_dump())

    if isinstance(data, dict):
        # Recurse into dictionaries
        return {k: _sanitize_firestore_data(v) for k, v in data.items()}

    if isinstance(data, list):
        # Recurse into lists
        return [_sanitize_firestore_data(item) for item in data]

    # Return everything else as-is (str, int, float, bool, datetime, etc.)
    return data


class BaseFirestoreService(Generic[T]):
    """
    Base service class for Firestore operations using Pydantic models

    This class provides common CRUD operations for Firestore collections
    with type safety through Pydantic models.
    """

    def __init__(
        self,
        db: firestore.Client,
        collection_name: str,
        resource_type: str,
        model_class: Optional[Type[T]] = None,
        logger: Optional[logging.Logger] = None,
        timeout: float = 10.0
    ):
        """
        Initialize the BaseFirestoreService

        Args:
            db: Firestore client instance
            collection_name: Name of the Firestore collection
            resource_type: Resource type name for error reporting
            model_class: Pydantic model class for the resource
            logger: Logger instance for logging operations
            timeout: Default timeout for Firestore operations
        """
        self.db = db
        self.collection_name = collection_name
        self.resource_type = resource_type
        self.model_class = model_class
        self.logger = logger or logging.getLogger(__name__)
        self.timeout = timeout

    def _get_collection(self) -> firestore.CollectionReference:
        """Get the Firestore collection reference"""
        return self.db.collection(self.collection_name)

    def _convert_to_model(self, doc_dict: Dict[str, Any], doc_id: str) -> T:
        """
        Convert Firestore document data to Pydantic model

        Args:
            doc_dict: Document data from Firestore
            doc_id: Document ID

        Returns:
            Pydantic model instance

        Raises:
            ServiceValidationError: If validation fails
        """
        if not self.model_class:
            raise ServiceError(
                operation="convert_to_model",
                error=ValueError("No model class specified"),
                resource_type=self.resource_type,
                resource_id=doc_id
            )

        try:
            # Add ID to the document data if not present
            if 'id' not in doc_dict:
                doc_dict['id'] = doc_id

            return self.model_class(**doc_dict)
        except ValidationError as e:
            raise ServiceValidationError(
                resource_type=self.resource_type,
                detail=f"Validation failed: {str(e)}",
                resource_id=doc_id,
                additional_info={"validation_errors": e.errors()}
            )

    async def get_document(self, doc_id: str, convert_to_model: bool = True) -> Union[T, Dict[str, Any]]:
        """
        Get a document by ID

        Args:
            doc_id: Document ID
            convert_to_model: Whether to convert to Pydantic model

        Returns:
            Document as a model instance or dict.

        Raises:
            ResourceNotFoundError: If document doesn't exist
            ServiceError: If an error occurs during retrieval
        """
        try:
            doc_ref = self._get_collection().document(doc_id)
            doc = doc_ref.get()

            if not doc.exists:
                raise ResourceNotFoundError(
                    resource_type=self.resource_type,
                    resource_id=doc_id
                )

            doc_dict = doc.to_dict()
            if not doc_dict:
                # This case should ideally not be reached if doc.exists is true,
                # but as a safeguard:
                raise ServiceError(
                    operation="get_document",
                    error=ValueError("Document exists but data is empty."),
                    resource_type=self.resource_type,
                    resource_id=doc_id
                )

            if convert_to_model and self.model_class:
                return self._convert_to_model(doc_dict, doc_id)
            else:
                doc_dict['id'] = doc_id
                return doc_dict

        except ResourceNotFoundError:
            raise
        except Exception as e:
            raise ServiceError(
                operation="get_document",
                error=e,
                resource_type=self.resource_type,
                resource_id=doc_id
            )

    async def create_document(
        self,
        doc_id: str,
        data: Union[T, Dict[str, Any]],
        creator_uid: str,
        merge: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new document

        Args:
            doc_id: Document ID
            data: Document data as model instance or dict
            creator_uid: UID of the user creating the document
            merge: Whether to merge with existing document

        Returns:
            Created document as dict

        Raises:
            ServiceError: If an error occurs during creation
        """
        try:
            # Convert model to dict if necessary
            if isinstance(data, BaseModel):
                doc_dict = data.model_dump()
            else:
                doc_dict = data.copy()

            # Sanitize data for Firestore (convert date objects to datetime)
            doc_dict = _sanitize_firestore_data(doc_dict)

            # Ensure ID is set correctly
            doc_dict['id'] = doc_id

            # Add metadata
            now = datetime.now(timezone.utc)
            if 'created_at' not in doc_dict:
                doc_dict['created_at'] = now
            if 'created_by' not in doc_dict:
                doc_dict['created_by'] = creator_uid
            doc_dict['updated_at'] = now
            doc_dict['updated_by'] = creator_uid

            # Create document
            doc_ref = self._get_collection().document(doc_id)
            doc_ref.set(doc_dict, merge=merge)

            return doc_dict

        except Exception as e:
            if isinstance(e, ServiceValidationError):
                raise
            raise ServiceError(
                operation=f"creating {self.resource_type}",
                error=e,
                resource_type=self.resource_type,
                resource_id=doc_id
            )

    async def update_document(
        self,
        doc_id: str,
        update_data: Dict[str, Any],
        updater_uid: str,
        require_exists: bool = True
    ) -> Dict[str, Any]:
        """
        Update an existing document

        Args:
            doc_id: Document ID
            update_data: Fields to update
            updater_uid: UID of the user updating the document
            require_exists: Whether to require the document to exist

        Returns:
            Updated document as dict

        Raises:
            ValidationError: If update_data is empty
            ResourceNotFoundError: If document doesn't exist and require_exists is True
            ServiceError: If an error occurs during update
        """
        # Validate update data is not empty
        if not update_data:
            raise ServiceValidationError(
                resource_type=self.resource_type,
                detail="Update data cannot be empty"
            )

        try:
            doc_ref = self._get_collection().document(doc_id)

            if require_exists:
                doc = doc_ref.get()
                if not doc.exists:
                    raise ResourceNotFoundError(
                        resource_type=self.resource_type,
                        resource_id=doc_id
                    )

            # Add update timestamp and user
            updates = update_data.copy()

            # Sanitize data for Firestore (convert date objects to datetime)
            updates = _sanitize_firestore_data(updates)

            updates['updated_at'] = datetime.now(timezone.utc)
            updates['updated_by'] = updater_uid

            # Update document
            doc_ref.update(updates)

            # Get updated document
            updated_doc = doc_ref.get()
            return updated_doc.to_dict() if updated_doc.exists else {}

        except ResourceNotFoundError:
            raise
        except Exception as e:
            raise ServiceError(
                operation="update_document",
                error=e,
                resource_type=self.resource_type,
                resource_id=doc_id
            )

    async def delete_document(self, doc_id: str, require_exists: bool = True) -> bool:
        """
        Delete a document

        Args:
            doc_id: Document ID
            require_exists: Whether to require the document to exist

        Returns:
            True if deleted, False if not found and require_exists is False

        Raises:
            ResourceNotFoundError: If document doesn't exist and require_exists is True
            ServiceError: If an error occurs during deletion
        """
        try:
            doc_ref = self._get_collection().document(doc_id)

            if require_exists:
                doc = doc_ref.get()
                if not doc.exists:
                    raise ResourceNotFoundError(
                        resource_type=self.resource_type,
                        resource_id=doc_id
                    )

            doc_ref.delete()
            return True

        except ResourceNotFoundError:
            if require_exists:
                raise
            return False
        except Exception as e:
            raise ServiceError(
                operation="delete_document",
                error=e,
                resource_type=self.resource_type,
                resource_id=doc_id
            )

    async def document_exists(self, doc_id: str) -> bool:
        """
        Check if a document exists

        Args:
            doc_id: Document ID

        Returns:
            True if document exists, False otherwise

        Raises:
            ServiceError: If an error occurs during check
        """
        try:
            doc_ref = self._get_collection().document(doc_id)
            doc = doc_ref.get()  # Remove await - this is synchronous
            return doc.exists
        except Exception as e:
            raise ServiceError(
                operation="document_exists",
                error=e,
                resource_type=self.resource_type,
                resource_id=doc_id
            )

    async def list_documents(
        self,
        limit: Optional[int] = None,
        start_after: Optional[str] = None,
        order_by: Optional[str] = None,
        order_direction: str = firestore.Query.ASCENDING,
        filters: Optional[List[tuple]] = None,
        as_models: bool = True
    ) -> Union[List[T], List[Dict[str, Any]]]:
        """
        List documents with optional filtering and pagination

        Args:
            limit: Maximum number of documents to return
            start_after: Document ID to start after for pagination
            order_by: Field to order by
            order_direction: Direction to order by (e.g., "ASCENDING", "DESCENDING")
            filters: List of field filters as tuples (field, operator, value)
            as_models: Whether to convert documents to Pydantic models

        Returns:
            List of documents as model instances or dicts

        Raises:
            ServiceError: If an error occurs during listing
        """
        try:
            query = self._get_collection()

            # Apply filters
            if filters:
                for filter_condition in filters:
                    field, operator, value = filter_condition
                    query = query.where(field, operator, value)

            # Apply ordering
            if order_by:
                query = query.order_by(order_by, direction=order_direction)

            # Apply pagination
            if start_after:
                start_doc = await self._get_collection().document(start_after).get()
                if start_doc.exists:
                    query = query.start_after(start_doc)

            if limit:
                query = query.limit(limit)

            # Execute query
            docs = query.get()

            # Convert to models
            results = []
            for doc in docs:
                doc_dict = doc.to_dict()
                if doc_dict is None:
                    continue  # Skip documents that don't exist

                if as_models and self.model_class:
                    model_instance = self._convert_to_model(doc_dict, doc.id)
                    results.append(model_instance)
                else:
                    doc_dict['id'] = doc.id
                    results.append(doc_dict)

            return results

        except Exception as e:
            raise ServiceError(
                operation="list_documents",
                error=e,
                resource_type=self.resource_type
            )

    async def archive_document(
        self,
        document_data: Dict[str, Any],
        doc_id: str,
        archive_collection: str,
        archived_by: str
    ) -> bool:
        """
        Archive a document by copying it to an archive collection with metadata

        Args:
            document_data: The document data to archive
            doc_id: Document ID
            archive_collection: Name of the archive collection
            archived_by: UID of the user performing the archive

        Returns:
            True if archival was successful

        Raises:
            ServiceError: If an error occurs during archival
        """
        try:
            # Generate unique archive document ID to handle duplicates
            archive_timestamp = datetime.now(timezone.utc)
            timestamp_str = archive_timestamp.strftime("%Y%m%d_%H%M%S_%f")[:-3]  # microseconds to milliseconds
            unique_archive_doc_id = f"{doc_id}_{timestamp_str}"

            # Add archival metadata
            archive_data = document_data.copy()
            archive_data.update({
                "archived_at": archive_timestamp,
                "archived_by": archived_by,
                "updated_at": archive_timestamp,
                "updated_by": archived_by,
                "original_collection": self.collection_name,
                "original_doc_id": doc_id
            })

            # Store in archive collection with unique ID
            archive_ref = self.db.collection(archive_collection).document(unique_archive_doc_id)
            archive_ref.set(archive_data, timeout=self.timeout)

            self.logger.info(f"Successfully archived {self.resource_type} {doc_id} to {archive_collection} as {unique_archive_doc_id}")
            return True

        except Exception as e:
            raise ServiceError(
                operation="archive_document",
                error=e,
                resource_type=self.resource_type,
                resource_id=doc_id
            )

    async def restore_document(
        self,
        doc_id: str,
        source_collection: str,
        target_collection: str,
        restored_by: str
    ) -> bool:
        """
        Restore a document from an archive collection to the target collection

        Args:
            doc_id: Document ID to restore
            source_collection: Archive collection name to restore from
            target_collection: Target collection name to restore to
            restored_by: UID of the user performing the restore

        Returns:
            True if restoration was successful

        Raises:
            ServiceError: If an error occurs during restoration
            ResourceNotFoundError: If document not found in archive
        """
        try:
            # Get document from archive collection
            archive_ref = self.db.collection(source_collection).document(doc_id)
            archive_doc = archive_ref.get(timeout=self.timeout)

            if not archive_doc.exists:
                raise ResourceNotFoundError(
                    resource_type=self.resource_type,
                    resource_id=doc_id,
                    additional_info={"message": f"Document not found in archive collection {source_collection}"}
                )

            archive_data = archive_doc.to_dict()
            if not archive_data:
                raise ServiceError(
                    operation="restore_document",
                    error=ValueError("Archive document data is empty"),
                    resource_type=self.resource_type,
                    resource_id=doc_id
                )

            # Prepare restored data (remove archive metadata)
            restored_data = archive_data.copy()

            # Remove archive-specific fields
            archive_fields_to_remove = [
                "archived_at", "archived_by", "original_collection",
                "original_doc_id", "restored_at", "restored_by"
            ]
            for field in archive_fields_to_remove:
                restored_data.pop(field, None)

            # Add restoration metadata
            restored_data.update({
                "restored_at": datetime.now(timezone.utc),
                "restored_by": restored_by,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": restored_by
            })

            # Restore to target collection
            target_ref = self.db.collection(target_collection).document(doc_id)
            target_ref.set(restored_data, timeout=self.timeout)

            # Remove from archive collection
            archive_ref.delete()

            self.logger.info(f"Successfully restored {self.resource_type} {doc_id} from {source_collection} to {target_collection}")
            return True

        except ResourceNotFoundError:
            raise
        except Exception as e:
            raise ServiceError(
                operation="restore_document",
                error=e,
                resource_type=self.resource_type,
                resource_id=doc_id
            )


