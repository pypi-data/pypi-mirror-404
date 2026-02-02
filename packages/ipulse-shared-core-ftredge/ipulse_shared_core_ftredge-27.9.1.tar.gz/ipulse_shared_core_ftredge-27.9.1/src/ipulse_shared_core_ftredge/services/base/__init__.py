"""
Base service classes for ipulse_shared_core_ftredge

This module provides base service classes without importing any concrete services,
preventing circular import dependencies.
"""

from .base_firestore_service import BaseFirestoreService
from .cache_aware_firestore_service import CacheAwareFirestoreService
from .multi_collection_cache_aware_firestore_service import MultiCollectionCacheAwareFirestoreService

__all__ = [
    'BaseFirestoreService',
    'CacheAwareFirestoreService'
]
