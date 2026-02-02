"""
Generic multi-collection cache-aware Firestore service.

This service extends CacheAwareFirestoreService to support dynamic collection operations
while maintaining all proven infrastructure patterns. It's designed to be generic and
reusable across different model types.
"""
from typing import Dict, Any, List, Optional, Union, Type, TypeVar, Generic
from google.cloud import firestore
from .cache_aware_firestore_service import CacheAwareFirestoreService
from ...exceptions import ServiceError, ValidationError, ResourceNotFoundError
from ...cache.shared_cache import SharedCache
from ...models import BaseNoSQLModel
import logging

# Generic type for BaseNoSQLModel subclasses
T = TypeVar('T', bound=BaseNoSQLModel)


class MultiCollectionCacheAwareFirestoreService(CacheAwareFirestoreService[T], Generic[T]):
    """
    Generic multi-collection extension of CacheAwareFirestoreService.

    This service extends the proven CacheAwareFirestoreService infrastructure to support
    dynamic collection operations based on storage_location_path while maintaining
    all caching, error handling, and CRUD capabilities.

    This is a generic base class that can be extended for specific model types.
    """

    def __init__(self,
                 db: firestore.Client,
                 logger: logging.Logger,
                 model_class: Type[T],
                 resource_type: str,
                 base_collection_name: str,
                 timeout: float = 30.0):

        # Initialize the parent CacheAwareFirestoreService with a base collection
        # We'll override the collection_name dynamically per operation
        super().__init__(
            db=db,
            collection_name=base_collection_name,  # Base collection name
            resource_type=resource_type,
            model_class=model_class,
            logger=logger,
            document_cache=None,  # We'll manage caches per collection
            collection_cache=None,  # We'll manage caches per collection
            timeout=timeout
        )

        # Cache for per-collection cache instances
        self._collection_caches: Dict[str, Dict[str, SharedCache]] = {}

        self.logger.info(f"MultiCollectionCacheAwareFirestoreService initialized for {resource_type}")

    def _get_collection_caches(self, storage_location_path: str) -> Dict[str, SharedCache]:
        """Get or create cache instances for a specific storage location."""
        if storage_location_path not in self._collection_caches:
            # Create collection-specific cache instances
            # No need for safe_name transformation - dots are fine in strings

            document_cache = SharedCache(
                name=f"MultiColDoc_{storage_location_path}",
                ttl=600.0,  # 10 minutes
                enabled=True,
                logger=self.logger
            )

            collection_cache = SharedCache(
                name=f"MultiColCollection_{storage_location_path}",
                ttl=600.0,  # 10 minutes
                enabled=True,
                logger=self.logger
            )

            self._collection_caches[storage_location_path] = {
                'document': document_cache,
                'collection': collection_cache
            }

            self.logger.info(f"Created cache instances for collection: {storage_location_path}")

        return self._collection_caches[storage_location_path]

    def _set_collection_context(self, storage_location_path: str):
        """Set the collection context for the current operation."""
        # Update the collection name for this operation
        self.collection_name = storage_location_path

        # Update the cache references for this collection
        caches = self._get_collection_caches(storage_location_path)
        self.document_cache = caches['document']
        self.collection_cache = caches['collection']

    async def get_document_from_collection(self,
                                         storage_location_path: str,
                                         doc_id: str,
                                         convert_to_model: bool = True) -> Union[T, Dict[str, Any], None]:
        """
        Get a document from a specific collection using the cache-aware infrastructure.
        """
        try:
            # Set collection context
            self._set_collection_context(storage_location_path)

            # Use the parent's cache-aware get_document method
            return await super().get_document(doc_id, convert_to_model)

        except ResourceNotFoundError:
            self.logger.info(f"Document {doc_id} not found in {storage_location_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting document {doc_id} from {storage_location_path}: {str(e)}", exc_info=True)
            raise ServiceError(
                operation=f"getting document from {storage_location_path}",
                error=e,
                resource_type=self.resource_type,
                resource_id=doc_id
            ) from e

    async def get_all_documents_from_collection(self,
                                              storage_location_path: str,
                                              cache_key: Optional[str] = None) -> List[T]:
        """
        Get all documents from a specific collection using cache-aware infrastructure.
        """
        try:
            # Set collection context
            self._set_collection_context(storage_location_path)

            # Use cache key if not provided
            if not cache_key:
                cache_key = f"all_documents_{storage_location_path}"

            # Use the parent's cache-aware get_all_documents method
            results = await super().get_all_documents(cache_key=cache_key, as_models=True)

            # Ensure we return model instances
            model_results: List[T] = []
            for item in results:
                if isinstance(item, BaseNoSQLModel) and self.model_class and isinstance(item, self.model_class):
                    model_results.append(item)  # type: ignore
                elif isinstance(item, dict) and self.model_class:
                    try:
                        model_results.append(self.model_class.model_validate(item))
                    except Exception as e:
                        self.logger.warning(f"Failed to convert dict to model: {e}")

            return model_results

        except Exception as e:
            self.logger.error(f"Error getting all documents from {storage_location_path}: {str(e)}", exc_info=True)
            raise ServiceError(
                operation=f"getting all documents from {storage_location_path}",
                error=e,
                resource_type=self.resource_type
            ) from e

    async def create_document_in_collection(self,
                                          storage_location_path: str,
                                          doc_id: str,
                                          data: Union[T, Dict[str, Any]],
                                          creator_uid: str,
                                          merge: bool = False) -> Dict[str, Any]:
        """
        Create a document in a specific collection using cache-aware infrastructure.
        Automatically handles cache invalidation.
        """
        try:
            # Set collection context
            self._set_collection_context(storage_location_path)

            # Use the parent's cache-aware create_document method
            return await super().create_document(doc_id, data, creator_uid, merge)

        except Exception as e:
            self.logger.error(f"Error creating document {doc_id} in {storage_location_path}: {str(e)}", exc_info=True)
            raise ServiceError(
                operation=f"creating document in {storage_location_path}",
                error=e,
                resource_type=self.resource_type,
                resource_id=doc_id
            ) from e

    async def update_document_in_collection(self,
                                          storage_location_path: str,
                                          doc_id: str,
                                          update_data: Dict[str, Any],
                                          updater_uid: str,
                                          require_exists: bool = True) -> Dict[str, Any]:
        """
        Update a document in a specific collection using cache-aware infrastructure.
        Automatically handles cache invalidation.
        """
        try:
            # Set collection context
            self._set_collection_context(storage_location_path)

            # Use the parent's cache-aware update_document method
            return await super().update_document(doc_id, update_data, updater_uid, require_exists)

        except Exception as e:
            self.logger.error(f"Error updating document {doc_id} in {storage_location_path}: {str(e)}", exc_info=True)
            raise ServiceError(
                operation=f"updating document in {storage_location_path}",
                error=e,
                resource_type=self.resource_type,
                resource_id=doc_id
            ) from e

    async def delete_document_from_collection(self,
                                            storage_location_path: str,
                                            doc_id: str,
                                            require_exists: bool = True) -> bool:
        """
        Delete a document from a specific collection using cache-aware infrastructure.
        Automatically handles cache invalidation.
        """
        try:
            # Set collection context
            self._set_collection_context(storage_location_path)

            # Use the parent's cache-aware delete_document method
            return await super().delete_document(doc_id, require_exists)

        except Exception as e:
            self.logger.error(f"Error deleting document {doc_id} from {storage_location_path}: {str(e)}", exc_info=True)
            raise ServiceError(
                operation=f"deleting document from {storage_location_path}",
                error=e,
                resource_type=self.resource_type,
                resource_id=doc_id
            ) from e

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for all collections managed by this service."""
        stats = {}
        for storage_path, caches in self._collection_caches.items():
            stats[storage_path] = {
                'document_cache': caches['document'].get_stats(),
                'collection_cache': caches['collection'].get_stats()
            }
        return stats
