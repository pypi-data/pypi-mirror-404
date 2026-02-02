"""Module for shared caching functionality that can be used across microservices."""
import time
import logging
import traceback
import inspect
import asyncio
import threading
from typing import Dict, Any, Optional, TypeVar, Generic, Callable, Tuple,Awaitable

T = TypeVar('T')

class SharedCache(Generic[T]):
    """
    Generic shared cache implementation that can be used across services.

    Attributes:
        name: The name of the cache for logging and identification.
        ttl: Time-to-live in seconds for cached items.
        enabled: Whether the cache is enabled.
        logger: Logger for cache operations.
        _cache: Dictionary holding cached values.
        _timestamps: Dictionary holding timestamps for each cached item.
    """

    def __init__(
        self,
        name: str,
        ttl: float,
        enabled: bool = True,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the cache with name, TTL and enabled state."""
        self.name = name
        self.ttl = ttl
        self.enabled = enabled
        self.logger = logger or logging.getLogger(__name__)
        self._cache: Dict[str, T] = {}
        self._timestamps: Dict[str, float] = {}

        # Thread-safe attributes
        self.lock = threading.RLock()  # Changed from threading.Lock()
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.evictions = 0

        self.logger.info(f"{name} cache initialized. Enabled: {enabled}, TTL: {ttl} seconds")

    def get(self, key: str) -> Optional[T]:
        """
        Get a value from the cache if it exists and hasn't expired.

        Args:
            key: The cache key to retrieve.

        Returns:
            The cached value if found and valid, None otherwise.
        """
        if not self.enabled:
            return None

        with self.lock:
            try:
                if key in self._cache:
                    timestamp = self._timestamps.get(key, 0)
                    if time.time() - timestamp < self.ttl:
                        self.hits += 1
                        self.logger.debug(f"Cache hit for {key} in {self.name}")
                        return self._cache[key]
                    else:
                        # Expired item, remove it
                        self.invalidate(key)
                        self.logger.debug(f"Cache expired for {key} in {self.name}")
                else:
                    self.misses += 1
            except Exception as e:
                self.logger.error(f"Error getting item from {self.name} cache with key {key}: {str(e)}")
                self.logger.error(traceback.format_exc())

            return None

    def set(self, key: str, value: T) -> None:
        """
        Set a value in the cache.

        Args:
            key: The cache key to set.
            value: The value to cache.
        """
        if not self.enabled:
            return

        with self.lock:
            try:
                if len(self._cache) >= 1000 and key not in self._cache:
                    # Basic LRU-like eviction: remove the first item found (not true LRU)
                    try:
                        oldest_key = next(iter(self._cache))
                        self.invalidate(oldest_key)
                        self.evictions += 1
                    except StopIteration:
                        # Cache was empty, which shouldn't happen if len >= max_size > 0
                        pass # Or log an error

                self._cache[key] = value
                self._timestamps[key] = time.time()
                self.sets += 1
                self.logger.debug(f"Cached item {key} in {self.name}")
            except Exception as e:
                self.logger.error(f"Error setting item in {self.name} cache with key {key}: {str(e)}")
                self.logger.error(traceback.format_exc())

    def invalidate(self, key: str) -> None:
        """
        Remove a specific key from the cache.

        Args:
            key: The cache key to invalidate.
        """
        with self.lock:
            try:
                self._cache.pop(key, None)
                self._timestamps.pop(key, None)
                self.evictions += 1
                self.logger.debug(f"Invalidated cache for {key} in {self.name}")
            except Exception as e:
                self.logger.error(f"Error invalidating cache in {self.name} for key {key}: {str(e)}")
                self.logger.error(traceback.format_exc())

    def invalidate_all(self) -> None:
        """Clear all cached items."""
        with self.lock:
            try:
                cache_size = len(self._cache)
                self._cache.clear()
                self._timestamps.clear()
                self.evictions += cache_size
                self.logger.info(f"Invalidated all {cache_size} entries in {self.name} cache")
            except Exception as e:
                self.logger.error(f"Error invalidating all cache entries in {self.name}: {str(e)}")
                self.logger.error(traceback.format_exc())

    def get_or_set(
        self,
        key: str,
        data_loader: Callable[[], T]
    ) -> Tuple[T, bool]:
        """
        Get a value from cache or set it using the data_loader if missing or expired.

        Args:
            key: The cache key.
            data_loader: Function to load data if not in cache.

        Returns:
            Tuple of (data, was_cached) where was_cached indicates if from cache.
        """
        try:
            cached_data = self.get(key)
            if cached_data is not None:
                return cached_data, True

            # Not in cache or expired, load the data
            self.logger.debug(f"Cache miss for {key} in {self.name}, loading data...")

            # Check if the data_loader is a coroutine function
            if inspect.iscoroutinefunction(data_loader):
                self.logger.error(
                    f"Error in get_or_set for {key} in {self.name}: "
                    f"data_loader is a coroutine function which is not supported. "
                    f"Use a regular function that returns a value, not a coroutine."
                )
                # Fall back to running the coroutine in the event loop if possible
                try:
                    loop = asyncio.get_event_loop()
                    fresh_data = loop.run_until_complete(data_loader())
                except Exception as coro_err:
                    self.logger.error(f"Failed to execute coroutine data_loader: {str(coro_err)}")
                    raise RuntimeError(f"Cannot use coroutine data_loader in cache: {str(coro_err)}")
            else:
                # Regular function, just call it
                fresh_data = data_loader()

            if fresh_data is not None:  # Only cache if we got valid data
                self.set(key, fresh_data)

            if fresh_data is None:
                raise ValueError(f"Data loader returned None for key {key} in {self.name}")
            return fresh_data, False
        except Exception as e:
            self.logger.error(f"Error in get_or_set for {key} in {self.name}: {str(e)}")
            self.logger.error(traceback.format_exc())

            # Since this is a critical function, re-raise the exception
            # after logging it, but add context about the cache
            raise RuntimeError(f"Cache error in {self.name} for key {key}: {str(e)}") from e

    async def async_get_or_set(
        self,
        key: str,
        async_data_loader: Callable[[], Awaitable[T]]
    ) -> Tuple[T, bool]:
        """
        Async version of get_or_set for use with async data loaders.

        Args:
            key: The cache key.
            async_data_loader: Async function to load data if not in cache.

        Returns:
            Tuple of (data, was_cached) where was_cached indicates if from cache.
        """
        if not self.enabled:
            self.logger.debug(f"Cache {self.name} is disabled. Loading data directly for key {key}.")
            try:
                fresh_data = await async_data_loader()
                if fresh_data is None:
                    self.logger.error(f"Async data loader returned None for key {key} in disabled cache {self.name}")
                    raise ValueError(f"Async data loader returned None for key {key} in {self.name} (cache disabled)")
                return fresh_data, False
            except Exception as e:
                self.logger.error(f"Error in async_data_loader for key {key} in disabled cache {self.name}: {str(e)}")
                self.logger.error(traceback.format_exc())
                raise RuntimeError(f"Cache error (disabled) in {self.name} for key {key}: {str(e)}") from e

        try:
            cached_data = self.get(key) # self.get() is synchronous, assumed to be fast.
            if cached_data is not None:
                self.logger.debug(f"Cache HIT for key {key} in {self.name} (async_get_or_set)")
                return cached_data, True

            self.logger.debug(f"Cache MISS for key {key} in {self.name} (async_get_or_set). Loading data.")
            # Not in cache or expired, load the data asynchronously
            fresh_data = await async_data_loader()

            if fresh_data is not None:  # Only cache if we got valid data
                self.set(key, fresh_data)
            else:
                # Log an error if data_loader returns None, as it's unexpected.
                self.logger.error(f"Async data loader returned None for key {key} in {self.name}")
                raise ValueError(f"Async data loader returned None for key {key} in {self.name}")

            return fresh_data, False
        except Exception as e:
            self.logger.error(f"Error in async_get_or_set for key {key} in {self.name}: {str(e)}")
            self.logger.error(traceback.format_exc())
            # Re-raise the exception after logging, adding context
            raise RuntimeError(f"Cache error in {self.name} for key {key} (async): {str(e)}") from e

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the current cache state."""
        with self.lock:
            try:
                # Clean up expired items before reporting size
                current_time = time.time()
                # Corrected: Use self._timestamps to find expired keys
                expired_keys = [k for k, ts in self._timestamps.items() if current_time - ts >= self.ttl]
                for k in expired_keys:
                    self._cache.pop(k, None)
                    self._timestamps.pop(k, None)
                    self.evictions += 1

                return {
                    "name": self.name,
                    "enabled": self.enabled,
                    "ttl_seconds": self.ttl,
                    "item_count": len(self._cache),
                    "first_20_keys": list(self._cache.keys())[:20],  # Limit to first 20 keys
                    "total_keys": len(self._cache.keys()),
                    "memory_usage_estimate_megabytes": round(
                        sum(len(str(k)) + self._estimate_size(v) for k, v in self._cache.items()) / (1024 * 1024),
                        3
                    ),
                    "hits": self.hits,
                    "misses": self.misses,
                    "sets": self.sets,
                    "evictions": self.evictions,
                    "default_ttl": self.ttl
                }
            except Exception as e:
                self.logger.error(f"Error getting stats for {self.name} cache: {str(e)}")
                self.logger.error(traceback.format_exc())
                return {
                    "name": self.name,
                    "enabled": self.enabled,
                    "error": str(e),
                    "ttl_seconds": self.ttl,
                    "item_count": len(self._cache) if self._cache else 0
                }

    def _estimate_size(self, obj: Any) -> int:
        """Estimate the memory size of an object in bytes."""
        try:
            if obj is None:
                return 0
            if isinstance(obj, (str, bytes, bytearray)):
                return len(obj)
            if isinstance(obj, (int, float, bool)):
                return 8
            if isinstance(obj, dict):
                return sum(len(str(k)) + self._estimate_size(v) for k, v in obj.items())
            if isinstance(obj, (list, tuple, set)):
                return sum(self._estimate_size(i) for i in obj)
            # For other objects, use a rough approximation
            return len(str(obj))
        except Exception:
            # If we can't estimate, return a reasonable default
            return 100

    def __str__(self) -> str:
        return f"SharedCache(name='{self.name}', size={len(self._cache)}, max_size={self.max_size}, hits={self.hits}, misses={self.misses})"
