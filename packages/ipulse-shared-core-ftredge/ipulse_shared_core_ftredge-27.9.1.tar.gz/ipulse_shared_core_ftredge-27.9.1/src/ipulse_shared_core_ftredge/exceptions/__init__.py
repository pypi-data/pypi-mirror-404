"""
Exception module for ipulse_shared_core_ftredge

This module centralizes all exceptions to prevent circular import dependencies.
All services import exceptions from here instead of from each other.
"""

# Import all exceptions from submodules
from .base_exceptions import (
    BaseServiceException,
    ServiceError,
    ValidationError,
    ResourceNotFoundError,
    AuthorizationError
)

from .user_exceptions import (
    UserCoreError,
    UserCreationError,
    UserDeletionError,
    UserValidationError,
    UserProfileError,
    UserStatusError,
    UserAuthError,
    SubscriptionError,
    IAMPermissionError
)

__all__ = [
    # Base exceptions
    'BaseServiceException',
    'ServiceError',
    'ValidationError',
    'ResourceNotFoundError',
    'AuthorizationError',

    # User-specific exceptions
    'UserCoreError',
    'UserCreationError',
    'UserDeletionError',
    'UserValidationError',
    'UserProfileError',
    'UserStatusError',
    'UserAuthError',
    'SubscriptionError',
    'IAMPermissionError'
]
