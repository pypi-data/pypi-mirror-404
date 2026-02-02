"""Base classes for service exceptions with enhanced logging"""
from typing import Optional, Any, Dict
import traceback
import logging
from fastapi import HTTPException

class BaseServiceException(HTTPException):
    """Base class for service exceptions with enhanced logging"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.additional_info = additional_info or {}
        self.original_error = original_error

        # Get full traceback if there's an original error
        if original_error and hasattr(original_error, '__traceback__'):
            self.traceback = ''.join(traceback.format_exception(
                type(original_error),
                original_error,
                original_error.__traceback__
            ))
        else:
            self.traceback = ''.join(traceback.format_stack())

        # Build detailed message
        detail_msg = f"{detail}"
        if resource_type:
            detail_msg += f" [Resource Type: {resource_type}]"
        if resource_id:
            detail_msg += f" [ID: {resource_id}]"

        super().__init__(status_code=status_code, detail=detail_msg)

    def log_error(self, logger: logging.Logger):
        """Log error with full context"""
        error_context = {
            "status_code": self.status_code,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "detail": self.detail,
            **self.additional_info
        }

        log_message = f"""
            Service Error Occurred:
            Status Code: {self.status_code}
            Resource Type: {self.resource_type}
            Resource ID: {self.resource_id}
            Detail: {self.detail}
            Additional Info: {self.additional_info}
            {'Original Error: ' + str(self.original_error) if self.original_error else ''}
            Traceback:
            {self.traceback}
                    """

        logger.error(log_message, extra=error_context)


class ServiceError(BaseServiceException):
    """Generic service error with enhanced logging"""
    def __init__(
        self,
        operation: str,
        error: Any,  # Allow string or exception
        resource_type: str,
        resource_id: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ):
        # If a string is passed as an error, wrap it in a generic Exception
        if isinstance(error, str):
            original_error = Exception(error)
            error_detail = error
        else:
            original_error = error
            error_detail = str(error)

        super().__init__(
            status_code=500,
            detail=f"Error during {operation}: {error_detail}",
            resource_type=resource_type,
            resource_id=resource_id,
            additional_info=additional_info,
            original_error=original_error
        )


class ResourceNotFoundError(BaseServiceException):
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        additional_info: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=404,
            detail="Resource not found",
            resource_type=resource_type,
            resource_id=resource_id,
            additional_info=additional_info
        )


class AuthorizationError(BaseServiceException):
    def __init__(
        self,
        action: str,
        resource_type: str = "authorization",
        resource_id: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            status_code=403,
            detail=f"Not authorized to {action}",
            resource_type=resource_type,
            resource_id=resource_id,
            additional_info=additional_info,
            original_error=original_error
        )

class ValidationError(BaseServiceException):
    def __init__(
        self,
        resource_type: str,
        detail: str,
        resource_id: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=422,
            detail=detail,
            resource_type=resource_type,
            resource_id=resource_id,
            additional_info=additional_info
        )


class ConfigurationError(BaseServiceException):
    def __init__(
        self,
        detail: str,
        resource_type: str = "configuration",
        resource_id: Optional[str] = None,
        operation: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        if operation:
            detail = f"{detail} (Operation: {operation})"

        super().__init__(
            status_code=500,
            detail=detail,
            resource_type=resource_type,
            resource_id=resource_id,
            additional_info=additional_info,
            original_error=original_error
        )
