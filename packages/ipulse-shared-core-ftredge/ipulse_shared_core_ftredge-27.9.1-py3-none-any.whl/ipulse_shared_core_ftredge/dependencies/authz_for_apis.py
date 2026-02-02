import os
import logging
from typing import Optional, Iterable, Dict, Any, List
from datetime import datetime, timedelta, timezone
import httpx
from fastapi import HTTPException, Request
from ipulse_shared_base_ftredge import ApprovalStatus
from ipulse_shared_core_ftredge.exceptions import ServiceError, ResourceNotFoundError
from ipulse_shared_core_ftredge.models import UserStatus
from ipulse_shared_core_ftredge.services import UserCoreService

# Cache TTL constant
USERSTATUS_CACHE_TTL = 60 # 60 seconds

# Authorization bypass configuration
# These paths skip userstatus fetch and OPA check (token auth still required)
# Format: comma-separated path patterns (case-insensitive substring match)
# Example: "/user/live/multistep/create-from-self-userauth,/health,/metrics"
AUTHZ_BYPASS_PATHS_ENV = os.getenv('AUTHZ_BYPASS_PATHS', '')
AUTHZ_BYPASS_PATHS = [
    path.strip().lower()
    for path in AUTHZ_BYPASS_PATHS_ENV.split(',')
    if path.strip()
]

# Default bypass paths (can be extended via env var)
# These are self-service endpoints that only require valid Firebase token
DEFAULT_BYPASS_PATHS = [
    '/user/live/multistep/create-from-self-userauth'  # Self-repair endpoint - user can only create their own profile
]

# Combine env config with defaults
ALL_BYPASS_PATHS = list(set(AUTHZ_BYPASS_PATHS + DEFAULT_BYPASS_PATHS))

class UserStatusCache:
    """Manages user status caching with dynamic invalidation"""
    def __init__(self):
        self._cache: Dict[str, UserStatus] = {}
        self._timestamps: Dict[str, datetime] = {}

    def get(self, user_uid: str) -> Optional[UserStatus]:
        """
        Retrieves user status from cache if available and valid.

        Args:
            user_uid (str): The user ID.

        Returns:
            UserStatus object if cached and valid, None otherwise
        """
        if user_uid in self._cache:
            status_obj = self._cache[user_uid]
            # Force refresh for credit-consuming or sensitive operations
            # Check TTL for normal operations
            if datetime.now() - self._timestamps[user_uid] < timedelta(seconds=USERSTATUS_CACHE_TTL):
                return status_obj
            self.invalidate(user_uid)
        return None

    def set(self, user_uid: str, status: UserStatus) -> None:
        """
        Sets user status object in the cache.

        Args:
            user_uid (str): The user ID.
            status (UserStatus): The user status object to cache.
        """
        self._cache[user_uid] = status
        self._timestamps[user_uid] = datetime.now()

    def invalidate(self, user_uid: str) -> None:
        """
        Invalidates (removes) user status from the cache.

        Args:
            user_uid (str): The user ID to invalidate.
        """
        self._cache.pop(user_uid, None)
        self._timestamps.pop(user_uid, None)

# Global cache instance
userstatus_cache = UserStatusCache()

# Replace the logger dependency with a standard logger
_module_logger = logging.getLogger(__name__)


async def get_userstatus(
    user_uid: str,
    user_core_service: UserCoreService,
    force_fresh: bool = False,
    logger: Optional[logging.Logger] = None
) -> tuple[UserStatus, bool]:
    """
    Lightweight fetch of user status with caching.
    Returns UserStatus objects directly for better performance.

    Args:
        user_uid: User ID to fetch status for
        user_core_service: UserCoreService for data retrieval
        force_fresh: Whether to bypass cache
        logger: Optional logger instance to use.

    Returns:
        Tuple of (UserStatus object, whether cache was used)
    """
    log = logger if logger else _module_logger
    cache_used = False

    # Check cache first unless forced fresh
    if not force_fresh:
        cached_status = userstatus_cache.get(user_uid)
        if cached_status:
            cache_used = True
            return cached_status, cache_used

    try:
        status_obj = await user_core_service.get_userstatus(user_uid)
        if not status_obj:
            raise ResourceNotFoundError(
                resource_type="UserStatus",
                resource_id=user_uid,
                additional_info={"message": "User status not found"}
            )

        # Ensure we have a UserStatus object
        if not isinstance(status_obj, UserStatus):
            # If it's a dict, convert to UserStatus
            if isinstance(status_obj, dict):
                status_obj = UserStatus(**status_obj)
            else:
                raise ValueError(f"Expected UserStatus object or dict, got {type(status_obj)}")

    except ResourceNotFoundError:
        # Let ResourceNotFoundError bubble up as 404 - this is a user issue, not a server error
        log.warning(f"User status not found for user {user_uid} during authorization")
        raise
    except Exception as e:
        # Only wrap true service errors (database failures, network issues, etc) in ServiceError
        log.error(f"Service error fetching user status via UserCoreService: {str(e)}")
        raise ServiceError(
            operation="fetching user status for authz via UserCoreService",
            error=e,
            resource_type="UserStatus",
            resource_id=user_uid
        ) from e

    # Cache the UserStatus object only if it's a real UserStatus instance
    if (not force_fresh) and isinstance(status_obj, UserStatus):
        userstatus_cache.set(user_uid, status_obj)

    return status_obj, cache_used

def _validate_resource_fields(fields: Dict[str, Any]) -> List[str]:
    """
    Filter out invalid fields similar to BaseFirestoreService validation.
    Returns only fields that have actual values to update.
    """
    valid_fields = {
        k: v for k, v in fields.items()
        if v is not None and not (isinstance(v, (list, dict, set)) and len(v) == 0)
    }
    return list(valid_fields.keys())

async def extract_request_fields(request: Request, logger: Optional[logging.Logger] = None) -> Optional[List[str]]:
    """
    Extract fields from request body for both PATCH and POST methods.
    For GET and DELETE methods, return None as they typically don't have a body.
    """
    log = logger if logger else _module_logger
    # Skip body extraction for GET and DELETE requests
    if request.method.upper() in ["GET", "DELETE", "HEAD", "OPTIONS"]:
        return None

    try:
        body = await request.json()
        if isinstance(body, dict):
            if request.method.upper() == "PATCH":
                return _validate_resource_fields(body)
            if request.method.upper() == "POST":
                # For POST, we want to include all fields being set
                return list(body.keys())
        elif hasattr(body, 'model_dump'):
            data = body.model_dump(exclude_unset=True)
            if request.method.upper() == "PATCH":
                return _validate_resource_fields(data)
            if request.method.upper() == "POST":
                return list(data.keys())

        return None

    except Exception as e:
        log.warning(f"Could not extract fields from request body: {str(e)}")
        return None  # Return None instead of raising an error

# Main authorization function with configurable timeout
async def authorizeAPIRequest(
    request: Request,
    user_core_service: UserCoreService,  # UserCoreService instance for better integration
    request_resource_fields: Optional[Iterable[str]] = None,
    logger: Optional[logging.Logger] = None

) -> Dict[str, Any]:
    """
    Authorize API request based on user status and OPA policies.
    Enhanced to use UserCoreService when available and fetch usertype from Firebase custom claims.

    Args:
        request: The incoming request
        user_core_service: UserCoreService instance for better integration
        request_resource_fields: Fields being accessed/modified in the request
        logger: Optional logger instance to use.

    Returns:
        Authorization result containing decision details

    Raises:
        HTTPException: For authorization failures (403) or service errors (500)
    """
    log = logger if logger else _module_logger
    opa_decision = None
    try:
        # Extract fields for both PATCH and POST if not provided
        if not request_resource_fields:
            request_resource_fields = await extract_request_fields(request, logger=log)

        # Extract request context and Firebase user claims
        firebase_user = request.state.user
        log.debug(f"Firebase user: {firebase_user}")
        user_uid = firebase_user.get('uid')
        if not user_uid:
            log.debug(f"Authorization denied for {request.method} {request.url.path}: No user UID found")
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this resource"
            )

        # OPTIMIZATION: Bypass userstatus fetch and OPA check for self-service endpoints
        # These paths only require valid token auth (already verified by middleware)
        request_path_lower = request.url.path.lower()
        if any(bypass_path in request_path_lower for bypass_path in ALL_BYPASS_PATHS):
            # Security check: For user-scoped endpoints, verify user is acting on their own resource
            # Extract UID from path (e.g., /userprofiles/{uid} or /userstatuss/{uid})
            path_parts = request.url.path.split('/')
            # Check if path contains a UID segment after common resource names
            resource_uid = None
            for i, part in enumerate(path_parts):
                if part.lower() in ['userprofiles', 'userstatuss', 'users']:
                    if i + 1 < len(path_parts):
                        resource_uid = path_parts[i + 1]
                        break

            # If we extracted a resource UID, verify it matches the authenticated user
            # For endpoints without a UID in the path (like multistep/create-from-self), skip this check
            if resource_uid and resource_uid != user_uid:
                log.warning(f"Authorization bypass denied: user {user_uid} attempted to access resource for {resource_uid}")
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to access this resource"
                )

            log.info(f"Authorization bypass for {request.method} {request.url.path}: self-service endpoint, token auth sufficient")
            return {
                "used_cached_status": False,
                "required_fresh_status": False,
                "status_retrieved_at": datetime.now(timezone.utc).isoformat(),
                "opa_decision": {"allow": True, "bypass": True, "reason": "self-service endpoint"},
                "bypassed": True
            }

        # Get usertype information from Firebase custom claims (primary source)
        primary_usertype = firebase_user.get('primary_usertype')
        secondary_usertypes = firebase_user.get('secondary_usertypes', [])
        user_approval_status = firebase_user.get('user_approval_status', str(ApprovalStatus.UNKNOWN))

        # Determine if we need fresh status for permissions and credits
        force_fresh = _should_force_fresh_status(request)
        user_status_obj, cache_used = await get_userstatus(
            user_uid=user_uid,
            user_core_service=user_core_service,
            force_fresh=force_fresh,
            logger=log
        )

        # Perform comprehensive review and cleanup synchronously to ensure accurate auth data
        log.debug(f"Comprehensive review for userstatus : {user_status_obj} during authz")
        if user_core_service:
            try:
                review_result = await user_core_service.review_and_clean_active_subscription_credits_and_permissions(
                    user_uid=user_uid,
                    updater_uid="Auto-AuthzMiddlewareDependency",
                    review_auto_renewal=True,
                    apply_fallback=True,
                    clean_expired_permissions=True,
                    review_credits=True
                )
                log.debug(f"Review result for userstatus : {review_result} during authz")
                # Refresh user status after comprehensive review if any actions were taken
                if review_result.get('actions_taken'):
                    log.info(f"Authz middleware performed comprehensive review for user {user_uid}: {review_result['actions_taken']}")
                    # Use the updated UserStatus returned from the review function
                    if 'updated_userstatus' in review_result:
                        user_status_obj = review_result['updated_userstatus']
                        # Invalidate cache since we updated the user status
                        userstatus_cache.invalidate(user_uid)
                        # Update cache with the new status
                        userstatus_cache.set(user_uid, user_status_obj)

            except Exception as e:
                log.warning(f"Comprehensive review failed for user {user_uid} during auth: {str(e)}")
                # Continue with existing status if review fails

        # Get valid permissions after comprehensive review
        valid_permissions_objs = user_status_obj.get_valid_permissions()

        # Convert UserPermission objects to minimal serializable format for OPA
        valid_permissions = [
            {
                "domain": perm.domain,
                "iam_unit_type": str(perm.iam_unit_type),  # Convert enum to string
                "permission_ref": perm.permission_ref
            }
            for perm in valid_permissions_objs
        ]

        # Extract active subscription plan ID
        active_subscription_plan_id = None
        if user_status_obj.active_subscription is not None:
            active_subscription_plan_id = user_status_obj.active_subscription.plan_id

        # Format the authz_input for OPA (optimized for speed)
        authz_input = {
            "api_url": request.url.path,
            "requestor": {
                "uid": user_uid,
                "primary_usertype": primary_usertype,
                "secondary_usertypes": secondary_usertypes,
                "email_verified": firebase_user.get("email_verified", False),
                "user_approval_status": user_approval_status,
                "iam_permissions": valid_permissions,
                "sbscrptn_based_insight_credits": user_status_obj.sbscrptn_based_insight_credits or 0,
                "extra_insight_credits": user_status_obj.extra_insight_credits or 0,
                "active_subscription_plan_id": active_subscription_plan_id
            },
            "method": request.method.lower(),
            "request_resource_fields": request_resource_fields
        }

        # PERFORMANCE OPTIMIZATION: Skip convert_to_json_serializable() and json.dumps()
        # The authz_input structure above contains only JSON-safe types:
        # - strings, integers, booleans, lists of strings, and simple dicts
        # - No datetime objects, enums, or complex Pydantic models
        # - httpx.post(json=...) handles serialization efficiently
        # This saves ~2-5ms per request on a high-frequency auth endpoint

        # Query OPA (optimized for speed - no unnecessary serialization)
        opa_url = f"{os.getenv('OPA_SERVER_URL', 'http://localhost:8181')}{os.getenv('OPA_DECISION_PATH', '/v1/data/http/authz/ingress/decision')}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    opa_url,
                    json={"input": authz_input},
                    timeout=5.0
                )

                if response.status_code != 200:
                    log.error(f"OPA authorization failed: {response.text}")
                    raise HTTPException(
                        status_code=500,
                        detail="Authorization service error"
                    )

                result = response.json()
                # Log the OPA decision at INFO level in production so Cloud Run logs capture it
                try:
                    decision_summary = result.get("result")
                except Exception:
                    decision_summary = result
                log.info(f"OPA decision for {request.method} {request.url.path}: status={response.status_code}, decision={decision_summary}")
                # Handle OPA response format
                if "result" not in result:
                    log.warning("OPA response missing 'result' field")
                    raise HTTPException(
                        status_code=500,
                        detail="Authorization service error: OPA response format unexpected"
                    )

                opa_decision = result["result"]
                allow = opa_decision.get("allow", False)

                # Handle authorization denial
                if not allow:
                    # Extract denial reason from OPA decision
                    denial_reason = opa_decision.get("reason", "unknown reason")
                    errors_pre = opa_decision.get("errors_pre_microservices", [])
                    errors_post = opa_decision.get("errors_post_microservices", [])

                    # Log denial at WARNING level so production logs surface potential authz problems
                    log.warning(f"OPA DENIED {request.method} {request.url.path} - Reason: {denial_reason}, "
                                f"Pre-errors: {errors_pre}, Post-errors: {errors_post}")

                    # Create detailed error message for debugging
                    error_details = f"Not authorized to {request.method} {request.url.path}"
                    if denial_reason and denial_reason != "unknown reason":
                        error_details += f" - Reason: {denial_reason}"

                    raise HTTPException(
                        status_code=403,
                        detail=error_details
                    )

            except httpx.RequestError as e:
                log.error(f"Failed to connect to OPA: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Authorization service temporarily unavailable"
                ) from e

        # More descriptive metadata about the data freshness
        return {
            "used_cached_status": cache_used,
            "required_fresh_status": force_fresh,
            "status_retrieved_at": datetime.now(timezone.utc).isoformat(),
            "opa_decision": opa_decision
        }

    except HTTPException:
        # Re-raise HTTPExceptions as-is (they're already properly formatted)
        raise
    except Exception as e:
        # Only log unexpected errors at ERROR level
        log.error(f"Unexpected error during authorization for {request.method} {request.url.path}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal authorization error"
        )

def _should_force_fresh_status(request: Request) -> bool:
    """
    Determine if we should force a fresh status check based on the request path patterns
    and HTTP methods
    """
    # Path patterns that indicate credit-sensitive operations
    credit_sensitive_patterns = [
        'prediction',
        'user-statuses',
        'historic'
    ]
    # Methods that require fresh status
    sensitive_methods = {'post', 'patch', 'put', 'delete'}

    path = request.url.path.lower()
    method = request.method.lower()

    return (
        any(pattern in path for pattern in credit_sensitive_patterns) or
        method in sensitive_methods
    )
