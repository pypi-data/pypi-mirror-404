"""Cache-aware Firestore service base class."""
import time
from typing import TypeVar, Generic, Dict, Any, List, Optional, Union, Type, Tuple
from google.cloud import firestore
from . import BaseFirestoreService
from ...exceptions import ResourceNotFoundError, ServiceError
from ...cache.shared_cache import SharedCache
from ...models import BaseNoSQLModel

T = TypeVar('T', bound=BaseNoSQLModel)

class CacheAwareFirestoreService(BaseFirestoreService[T], Generic[T]):
    """
    Base service class that adds caching capabilities to BaseFirestoreService.
    Supports both document-level and collection-level caching.
    """

    def __init__(
        self,
        db: firestore.Client,
        collection_name: str,
        resource_type: str,
        model_class: Optional[Type[T]] = None,
        logger=None,
        document_cache: Optional[SharedCache] = None,
        collection_cache: Optional[SharedCache] = None,
        timeout: float = 30.0
    ):
        super().__init__(db, collection_name, resource_type, model_class, logger, timeout)
        self.document_cache = document_cache
        self.collection_cache = collection_cache
        self.timeout = timeout

        # Log cache configuration
        if self.document_cache:
            self.logger.info(f"Document cache enabled for {resource_type}: {self.document_cache.name}")
        if self.collection_cache:
            self.logger.info(f"Collection cache enabled for {resource_type}: {self.collection_cache.name}")

    async def get_document(self, doc_id: str, convert_to_model: bool = True) -> Union[T, Dict[str, Any]]:
        """
        Get a document with caching support.

        Args:
            doc_id: Document ID to fetch
            convert_to_model: Whether to convert to Pydantic model

        Returns:
            Document as model instance or dictionary

        Raises:
            ResourceNotFoundError: If document doesn't exist
        """
        # Check cache first
        if self.document_cache:
            start_time = time.time()
            cached_doc = self.document_cache.get(doc_id)
            cache_check_time = (time.time() - start_time) * 1000

            if cached_doc is not None:
                # SharedCache.get() already logs cache hit, only log timing if significant
                if cache_check_time > 5.0:  # Only log if cache check took >5ms
                    self.logger.debug(f"Cache HIT for document {doc_id} in {cache_check_time:.2f}ms")
                if convert_to_model and self.model_class:
                    return self._convert_to_model(cached_doc, doc_id)
                else:
                    cached_doc['id'] = doc_id
                    return cached_doc
            else:
                self.logger.debug(f"Cache MISS for document {doc_id} - checking Firestore")

        # Fetch from Firestore using parent method
        result = await super().get_document(doc_id, convert_to_model)

        # Cache the result if we have a cache and got valid data
        if self.document_cache and result is not None:
            if convert_to_model and isinstance(result, BaseNoSQLModel):
                # Cache the model's dict representation
                self._cache_document_data(doc_id, result.model_dump())
            elif isinstance(result, dict):
                # Cache the dict directly
                self._cache_document_data(doc_id, result)

        return result

    async def get_document_with_cache_info(self, doc_id: str, convert_to_model: bool = True) -> Tuple[Union[T, Dict[str, Any], None], bool]:
        """
        Get a document with cache hit information.

        Args:
            doc_id: Document ID to fetch
            convert_to_model: Whether to convert to Pydantic model

        Returns:
            Tuple of (document, cache_hit) where cache_hit indicates if from cache

        Raises:
            ResourceNotFoundError: If document doesn't exist
        """
        cache_hit = False

        # Check cache first
        if self.document_cache:
            cached_doc = self.document_cache.get(doc_id)
            if cached_doc is not None:
                cache_hit = True
                # Note: SharedCache.get() already logs cache hit at DEBUG level
                if convert_to_model and self.model_class:
                    return self._convert_to_model(cached_doc, doc_id), cache_hit
                else:
                    cached_doc['id'] = doc_id
                    return cached_doc, cache_hit

        # Cache miss - fetch from Firestore
        self.logger.debug(f"Cache MISS for document {doc_id} - checking Firestore")

        try:
            result = await super().get_document(doc_id, convert_to_model)

            # Cache the result if we have a cache and got valid data
            if self.document_cache and result is not None:
                if convert_to_model and isinstance(result, BaseNoSQLModel):
                    # Cache the model's dict representation
                    self._cache_document_data(doc_id, result.model_dump())
                elif isinstance(result, dict):
                    # Cache the dict directly
                    self._cache_document_data(doc_id, result)

            return result, cache_hit

        except ResourceNotFoundError:
            return None, cache_hit

    async def get_all_documents(self, cache_key: Optional[str] = None, as_models: bool = True) -> Union[List[T], List[Dict[str, Any]]]:
        """
        Retrieves all documents from the collection.
        Uses collection_cache if cache_key is provided and cache is available.
        Also populates document_cache for each retrieved document.

        Args:
            cache_key: Optional cache key for collection-level caching
            as_models: Whether to convert documents to Pydantic models

        Returns:
            List of documents as model instances or dicts
        """
        if cache_key and self.collection_cache:
            cached_collection_data = self.collection_cache.get(cache_key)
            if cached_collection_data is not None:
                self.logger.debug(f"Cache HIT for collection key '{cache_key}' in {self.collection_cache.name}")
                # Ensure individual documents are also in document_cache if possible
                if self.document_cache:
                    for doc_data in cached_collection_data:
                        if "id" in doc_data and not self.document_cache.get(doc_data["id"]):
                            self._cache_document_data(doc_data["id"], doc_data)

                # Convert to models if requested
                if as_models and self.model_class:
                    results = []
                    for doc_data in cached_collection_data:
                        if "id" in doc_data:
                            model_instance = self._convert_to_model(doc_data, doc_data["id"])
                            results.append(model_instance)
                    return results
                return cached_collection_data
            else:
                self.logger.debug(f"Cache MISS for collection key '{cache_key}' in {self.collection_cache.name} - checking Firestore")

        self.logger.info(f"Fetching all documents for {self.resource_type} from Firestore.")
        start_time = time.time()

        try:
            docs_stream = self.db.collection(self.collection_name).stream(timeout=self.timeout)
            docs_data_list = []
            for doc in docs_stream:
                doc_data = doc.to_dict()
                if doc_data is not None:
                    doc_data["id"] = doc.id  # Ensure 'id' field is present
                    docs_data_list.append(doc_data)

            fetch_time = (time.time() - start_time) * 1000
            self.logger.debug(f"Fetched {len(docs_data_list)} documents for {self.resource_type} from Firestore in {fetch_time:.2f}ms")

            # Cache the entire collection if cache_key and collection_cache are available
            if cache_key and self.collection_cache:
                self.collection_cache.set(cache_key, docs_data_list)
                self.logger.debug(f"Cached collection with key '{cache_key}' in {self.collection_cache.name}")

            # Populate individual document cache
            if self.document_cache:
                self.logger.debug(f"Populating document cache ({self.document_cache.name}) with {len(docs_data_list)} items for {self.resource_type}.")
                for doc_data in docs_data_list:
                    # _cache_document_data expects 'id' to be in doc_data for keying
                    self._cache_document_data(doc_data["id"], doc_data)

            # Convert to models if requested
            if as_models and self.model_class:
                results = []
                for doc_data in docs_data_list:
                    if "id" in doc_data:
                        model_instance = self._convert_to_model(doc_data, doc_data["id"])
                        results.append(model_instance)
                return results

            return docs_data_list

        except Exception as e:
            self.logger.error(f"Error fetching all documents for {self.resource_type}: {str(e)}", exc_info=True)
            raise ServiceError(operation=f"fetching all {self.resource_type}s", error=e, resource_type=self.resource_type) from e

    def _cache_document_data(self, doc_id: str, data: Dict[str, Any]):
        """Helper to cache document data if document_cache is available."""
        if self.document_cache:
            self.document_cache.set(doc_id, data)
            # Note: SharedCache.set() already logs at DEBUG level

    async def create_document(self, doc_id: str, data: Union[T, Dict[str, Any]], creator_uid: str, merge: bool = False) -> Dict[str, Any]:
        """Create document and invalidate cache."""
        result = await super().create_document(doc_id, data, creator_uid, merge)
        self._invalidate_document_cache(doc_id)
        self._invalidate_all_collection_caches()
        return result

    async def update_document(self, doc_id: str, update_data: Dict[str, Any], updater_uid: str, require_exists: bool = True) -> Dict[str, Any]:
        """Update document and invalidate cache."""
        result = await super().update_document(doc_id, update_data, updater_uid, require_exists)
        self._invalidate_document_cache(doc_id)
        self._invalidate_all_collection_caches()
        return result

    async def delete_document(self, doc_id: str, require_exists: bool = True) -> bool:
        """Delete document and invalidate cache."""
        result = await super().delete_document(doc_id, require_exists)
        self._invalidate_document_cache(doc_id)
        self._invalidate_all_collection_caches()
        return result

    def _invalidate_document_cache(self, doc_id: str) -> None:
        """Invalidate document cache for a specific document."""
        if self.document_cache:
            self.document_cache.invalidate(doc_id)
            self.logger.debug(f"Invalidated cache for document {doc_id}")

    def _invalidate_collection_cache(self, cache_key: str) -> None:
        """Invalidate collection cache for a specific cache key."""
        if self.collection_cache:
            self.collection_cache.invalidate(cache_key)
            self.logger.debug(f"Invalidated collection cache for key {cache_key}")

    def _invalidate_all_collection_caches(self) -> None:
        """Invalidate all collection cache entries."""
        if self.collection_cache:
            self.collection_cache.invalidate_all()
            self.logger.debug(f"Invalidated all collection cache entries")

    async def archive_document(
        self,
        document_data: Dict[str, Any],
        doc_id: str,
        archive_collection: str,
        archived_by: str
    ) -> bool:
        """Archive document and invalidate cache."""
        result = await super().archive_document(document_data, doc_id, archive_collection, archived_by)
        self._invalidate_document_cache(doc_id)
        self._invalidate_all_collection_caches()
        return result

    async def restore_document(
        self,
        doc_id: str,
        source_collection: str,
        target_collection: str,
        restored_by: str
    ) -> bool:
        """Restore document and invalidate cache."""
        result = await super().restore_document(doc_id, source_collection, target_collection, restored_by)
        self._invalidate_document_cache(doc_id)
        self._invalidate_all_collection_caches()
        return result
