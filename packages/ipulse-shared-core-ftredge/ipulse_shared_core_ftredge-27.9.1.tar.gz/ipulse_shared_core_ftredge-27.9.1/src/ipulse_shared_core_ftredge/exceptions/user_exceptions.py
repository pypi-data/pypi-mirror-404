"""Custom exceptions for UserCoreService operations"""
from typing import Optional, Dict, Any
from .base_exceptions import BaseServiceException


class UserCoreError(BaseServiceException):
    """Base exception for UserCore operations"""
    def __init__(
        self,
        detail: str,
        user_uid: Optional[str] = None,
        operation: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            status_code=500,
            detail=detail,
            resource_type="UserCore",
            resource_id=user_uid,
            additional_info=additional_info,
            original_error=original_error
        )
        self.operation = operation


class UserProfileError(UserCoreError):
    """Exception for UserProfile operations"""
    def __init__(
        self,
        detail: str,
        user_uid: Optional[str] = None,
        operation: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            detail=detail,
            user_uid=user_uid,
            operation=operation,
            additional_info=additional_info,
            original_error=original_error
        )
        self.resource_type = "UserProfile"


class UserStatusError(UserCoreError):
    """Exception for UserStatus operations"""
    def __init__(
        self,
        detail: str,
        user_uid: Optional[str] = None,
        operation: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            detail=detail,
            user_uid=user_uid,
            operation=operation,
            additional_info=additional_info,
            original_error=original_error
        )
        self.resource_type = "UserStatus"


class UserAuthError(UserCoreError):
    """Exception for Firebase Auth operations"""
    def __init__(
        self,
        detail: str,
        user_uid: Optional[str] = None,
        operation: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            detail=detail,
            user_uid=user_uid,
            operation=operation,
            additional_info=additional_info,
            original_error=original_error
        )
        self.resource_type = "UserAuth"


class SubscriptionError(UserCoreError):
    """Exception for subscription operations"""
    def __init__(
        self,
        detail: str,
        user_uid: Optional[str] = None,
        plan_id: Optional[str] = None,
        operation: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        additional_info = additional_info or {}
        if plan_id:
            additional_info['plan_id'] = plan_id

        super().__init__(
            detail=detail,
            user_uid=user_uid,
            operation=operation,
            additional_info=additional_info,
            original_error=original_error
        )
        self.resource_type = "Subscription"
        self.plan_id = plan_id


class IAMPermissionError(UserCoreError):
    """Exception for IAM permission operations"""
    def __init__(
        self,
        detail: str,
        user_uid: Optional[str] = None,
        domain: Optional[str] = None,
        permission: Optional[str] = None,
        operation: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        additional_info = additional_info or {}
        if domain:
            additional_info['domain'] = domain
        if permission:
            additional_info['permission'] = permission

        super().__init__(
            detail=detail,
            user_uid=user_uid,
            operation=operation,
            additional_info=additional_info,
            original_error=original_error
        )
        self.resource_type = "IAMPermission"
        self.domain = domain
        self.permission = permission


class UserCreationError(UserCoreError):
    """Exception for user creation operations"""
    def __init__(
        self,
        detail: str,
        email: Optional[str] = None,
        user_uid: Optional[str] = None,
        failed_component: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        additional_info = additional_info or {}
        if email:
            additional_info['email'] = email
        if failed_component:
            additional_info['failed_component'] = failed_component

        super().__init__(
            detail=detail,
            user_uid=user_uid,
            operation="create_user",
            additional_info=additional_info,
            original_error=original_error
        )
        self.resource_type = "UserCreation"
        self.email = email
        self.failed_component = failed_component


class UserDeletionError(UserCoreError):
    """Exception for user deletion operations"""
    def __init__(
        self,
        detail: str,
        user_uid: Optional[str] = None,
        deletion_target: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        additional_info = additional_info or {}
        if deletion_target:
            additional_info['deletion_target'] = deletion_target

        super().__init__(
            detail=detail,
            user_uid=user_uid,
            operation="delete_user",
            additional_info=additional_info,
            original_error=original_error
        )
        self.resource_type = "UserDeletion"
        self.deletion_target = deletion_target


class UserValidationError(UserCoreError):
    """Exception for user data validation"""
    def __init__(
        self,
        detail: str,
        user_uid: Optional[str] = None,
        validation_field: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        additional_info = additional_info or {}
        if validation_field:
            additional_info['validation_field'] = validation_field

        super().__init__(
            detail=detail,
            user_uid=user_uid,
            operation="validate_user_core_data",
            additional_info=additional_info,
            original_error=original_error
        )
        self.resource_type = "UserValidation"
        self.validation_field = validation_field
