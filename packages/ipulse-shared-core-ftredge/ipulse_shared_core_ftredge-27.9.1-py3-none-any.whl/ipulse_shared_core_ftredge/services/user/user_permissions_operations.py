"""
Useriam Management Operations - Handle user permissions and access rights
"""
import logging
from typing import Dict, Optional, List
from datetime import datetime
from ipulse_shared_base_ftredge.enums.enums_iam import IAMUnit
from ...models import UserPermission
from .userstatus_operations import UserstatusOperations
from ...exceptions import IAMPermissionError, UserStatusError


class UserpermissionsOperations:
    """
    Handles IAM permissions and access rights management
    """

    def __init__(
        self,
        userstatus_ops: UserstatusOperations,
        logger: Optional[logging.Logger] = None
    ):
        self.userstatus_ops = userstatus_ops
        self.logger = logger or logging.getLogger(__name__)

    # IAM Permission Operations

    async def add_permission_to_user(
        self,
        user_uid: str,
        permission: UserPermission,
        updater_uid: Optional[str] = None
    ) -> bool:
        """
        Adds a permission to a user using a UserPermission object.

        Args:
            user_uid: The user ID to add permission to
            permission: UserPermission object containing all permission details
            updater_uid: The ID of the user performing the update

        Returns:
            True if permission was added successfully

        Raises:
            UserStatusError: If user status not found
            IAMPermissionError: If permission addition fails
        """
        self.logger.info(f"Adding {permission.iam_unit_type.value} permission for user {user_uid}: "
                        f"domain='{permission.domain}', name='{permission.permission_ref}'")

        try:
            userstatus = await self.userstatus_ops.get_userstatus(user_uid)
            if not userstatus:
                raise UserStatusError(f"UserStatus not found for user_uid {user_uid}")

            # Use the model's method to add the permission directly
            userstatus.add_permission(permission)

            # Update the user status with the modified model
            await self.userstatus_ops.update_userstatus(
                user_uid=user_uid,
                status_data=userstatus.model_dump(exclude_none=True),
                updater_uid=updater_uid or "system"
            )

            self.logger.info(f"Successfully added permission for user {user_uid}")
            return True

        except UserStatusError as e:
            self.logger.error("UserStatusError in add_permission_to_user: %s", e, exc_info=True)
            raise
        except Exception as e:
            self.logger.error("Failed to add permission for user %s: %s", user_uid, e, exc_info=True)
            raise IAMPermissionError(
                detail=f"Failed to add permission: {str(e)}",
                user_uid=user_uid,
                operation="add_permission_to_user",
                original_error=e
            ) from e

    async def remove_permission_from_user(
        self,
        user_uid: str,
        domain: Optional[str] = None,
        permission_type: Optional[IAMUnit] = None,
        permission_name: Optional[str] = None,
        source: Optional[str] = None,
        updater_uid: Optional[str] = None
    ) -> bool:
        """
        Removes permissions from a user based on flexible filter criteria.
        At least one filter criteria must be provided.

        Args:
            user_uid: The user ID to remove permission from
            domain: Optional domain filter (e.g., 'papp')
            permission_type: Optional IAM assignment type filter (GROUP, ROLE, etc.)
            permission_name: Optional permission name filter
            source: Optional source filter
            updater_uid: The ID of the user performing the update

        Returns:
            True if permission(s) were removed successfully

        Raises:
            UserStatusError: If user status not found
            IAMPermissionError: If permission removal fails
            ValueError: If no filter criteria are provided

        Examples:
            # Remove specific permission
            await remove_permission_from_user(uid, domain="papp", permission_type=IAMUnit.ROLE, permission_name="analyst")

            # Remove all permissions from a domain
            await remove_permission_from_user(uid, domain="papp")

            # Remove all permissions of a specific type
            await remove_permission_from_user(uid, permission_type=IAMUnit.ROLE)

            # Remove all permissions from a source
            await remove_permission_from_user(uid, source="subscription_123")
        """
        if not any([domain, permission_type, permission_name, source]):
            raise ValueError("At least one filter criteria must be provided")

        # Build description for logging
        filters = []
        if domain: filters.append(f"domain='{domain}'")
        if permission_type: filters.append(f"type='{permission_type.value}'")
        if permission_name: filters.append(f"name='{permission_name}'")
        if source: filters.append(f"source='{source}'")

        filter_desc = ", ".join(filters)
        self.logger.info(f"Removing permissions for user {user_uid} with filters: {filter_desc}")

        try:
            userstatus = await self.userstatus_ops.get_userstatus(user_uid)
            if not userstatus:
                raise UserStatusError(f"UserStatus not found for user_uid {user_uid}")

            # Use the model's method to remove the permission assignment
            removed_count = userstatus.remove_permission(
                domain=domain,
                iam_unit_type=permission_type,
                permission_ref=permission_name,
                source=source
            )

            if removed_count > 0:
                # Update using the full model to maintain consistency
                await self.userstatus_ops.update_userstatus(
                    user_uid=user_uid,
                    status_data=userstatus.model_dump(exclude_none=True),
                    updater_uid=updater_uid or "system"
                )
                self.logger.info(f"Successfully removed {removed_count} permission(s) for user {user_uid}")
                return True
            else:
                self.logger.warning("No matching permissions found for user %s with filters: %s", user_uid, filter_desc)
                return False

        except ValueError as e:
            self.logger.error("Invalid parameters in remove_permission_from_user: %s", e)
            raise IAMPermissionError(
                detail=f"Invalid parameters: {str(e)}",
                user_uid=user_uid,
                operation="remove_permission_from_user",
                original_error=e
            ) from e
        except UserStatusError as e:
            self.logger.error("UserStatusError in remove_permission_from_user: %s", e, exc_info=True)
            raise
        except Exception as e:
            self.logger.error("Failed to remove permission for user %s: %s", user_uid, e, exc_info=True)
            raise IAMPermissionError(
                detail=f"Failed to remove permission: {str(e)}",
                user_uid=user_uid,
                operation="remove_permission_from_user",
                original_error=e
            ) from e

    async def cleanup_expired_permissions_of_user(
        self,
        user_uid: str,
        iam_unit_type: Optional[IAMUnit] = None,
        updater_uid: Optional[str] = None
    ) -> int:
        """
        Clean up expired permissions for a user.

        Args:
            user_uid: The user identifier
            iam_unit_type: Optional filter for specific permission type
            updater_uid: The ID of the user performing the cleanup

        Returns:
            Number of permissions removed
        """
        self.logger.info(f"Cleaning up expired permissions for user {user_uid}")
        try:
            userstatus = await self.userstatus_ops.get_userstatus(user_uid)
            if not userstatus:
                raise UserStatusError(f"UserStatus not found for user_uid {user_uid}")

            removed_count = userstatus.cleanup_expired_permissions(iam_unit_type=iam_unit_type)

            if removed_count > 0:
                await self.userstatus_ops.update_userstatus(
                    user_uid=user_uid,
                    status_data=userstatus.model_dump(),
                    updater_uid=updater_uid or "system_cleanup_expired_permissions"
                )
                self.logger.info(f"Removed {removed_count} expired permissions for user {user_uid}")

            return removed_count

        except UserStatusError as e:
            self.logger.error("UserStatusError in cleanup_expired_permissions_of_user: %s", e, exc_info=True)
            raise
        except Exception as e:
            self.logger.error("Failed to cleanup expired permissions for user %s: %s", user_uid, e, exc_info=True)
            raise IAMPermissionError(
                detail=f"Failed to cleanup expired permissions: {str(e)}",
                user_uid=user_uid,
                operation="cleanup_expired_permissions",
                original_error=e
            ) from e

    async def remove_all_permissions_from_user(
        self,
        user_uid: str,
        source: Optional[str] = None,
        updater_uid: Optional[str] = None
    ) -> int:
        """
        Remove all permissions from a user, optionally filtered by source.

        Args:
            user_uid: The user identifier
            source: Optional source filter (if None, removes all permissions)
            updater_uid: The ID of the user performing the update

        Returns:
            Number of permissions removed
        """
        self.logger.info(f"Removing all permissions from user {user_uid}" +
                        (f" with source {source}" if source else ""))
        try:
            userstatus = await self.userstatus_ops.get_userstatus(user_uid)
            if not userstatus:
                raise UserStatusError(f"UserStatus not found for user_uid {user_uid}")

            removed_count = userstatus.remove_all_permissions(source=source)

            if removed_count > 0:
                await self.userstatus_ops.update_userstatus(
                    user_uid=user_uid,
                    status_data=userstatus.model_dump(),
                    updater_uid=updater_uid or "system_remove_all_permissions"
                )
                self.logger.info(f"Removed {removed_count} permissions from user {user_uid}")

            return removed_count

        except UserStatusError as e:
            self.logger.error("UserStatusError in remove_all_permissions_from_user: %s", e, exc_info=True)
            raise
        except Exception as e:
            self.logger.error("Failed to remove all permissions from user %s: %s", user_uid, e, exc_info=True)
            raise IAMPermissionError(
                detail=f"Failed to remove all permissions: {str(e)}",
                user_uid=user_uid,
                operation="remove_all_permissions",
                original_error=e
            ) from e

    async def get_permissions_of_user(
        self,
        user_uid: str,
        valid_post_expir_date: Optional[datetime] = None,
        domain: Optional[str] = None,
        iam_unit_type: Optional[IAMUnit] = None,
        source: Optional[str] = None
    ) -> List[UserPermission]:
        """
        Retrieves IAM permissions for a user with flexible filtering options.

        Args:
            user_uid: The user identifier
            valid_post_expir_date: If provided, only return permissions valid after this date
            domain: Optional domain filter
            iam_unit_type: Optional IAM unit type filter
            source: Optional source filter

        Returns:
            List of matching UserPermission objects
        """
        self.logger.info(f"Getting permissions for user {user_uid} with filters")
        try:
            userstatus = await self.userstatus_ops.get_userstatus(user_uid)
            if not userstatus:
                raise UserStatusError(f"UserStatus not found for user_uid {user_uid}")

            permissions = userstatus.iam_permissions

            # Apply filters
            if valid_post_expir_date:
                permissions = [
                    perm for perm in permissions
                    if perm.expires_at is None or perm.expires_at > valid_post_expir_date
                ]

            if domain:
                permissions = [perm for perm in permissions if perm.domain == domain]

            if iam_unit_type:
                permissions = [perm for perm in permissions if perm.iam_unit_type == iam_unit_type]

            if source:
                permissions = [perm for perm in permissions if perm.source == source]

            return permissions

        except UserStatusError as e:
            self.logger.error("UserStatusError in get_permissions_of_user: %s", e, exc_info=True)
            raise
        except Exception as e:
            self.logger.error("Failed to get permissions for user %s: %s", user_uid, e, exc_info=True)
            raise IAMPermissionError(
                detail=f"Failed to get permissions: {str(e)}",
                user_uid=user_uid,
                operation="get_user_permissions",
                original_error=e
            ) from e

    async def get_bulk_users_with_permission(
        self,
        domain: str,
        iam_unit_type: IAMUnit,
        permission_ref: str,
        limit: int = 100,
        valid_only: bool = True
    ) -> List[str]:
        """
        Get a list of user UIDs who have a specific permission.

        Note: This is a basic implementation that queries the database.
        For production use with large datasets, consider implementing
        database-level queries for better performance.

        Args:
            domain: The domain for the permission
            iam_unit_type: Type of IAM assignment
            permission_ref: The permission identifier
            limit: Maximum number of users to return (default: 100)
            valid_only: If True, only return users with valid (non-expired) permissions

        Returns:
            List of user UIDs
        """
        self.logger.info(f"Getting bulk users with permission {domain}.{iam_unit_type.value}.{permission_ref}")
        try:
            # This is a simplified implementation - in production, you would want to use
            # Firestore queries to filter users with specific permissions rather than
            # fetching all users. For now, we'll return an empty list and log a warning.

            self.logger.warning(
                "get_bulk_users_with_permission: This method requires database-level "
                "querying for optimal performance. Current implementation is not "
                "suitable for production use with large user bases."
            )

            # TODO: Implement proper Firestore querying for users with specific permissions
            # Example query structure:
            # collection('userstatuses')
            #   .where('iam_permissions', 'array_contains', {
            #       'domain': domain,
            #       'iam_unit_type': iam_unit_type.value,
            #       'permission_ref': permission_ref
            #   })
            #   .limit(limit)

            return []

        except Exception as e:
            self.logger.error("Failed to get bulk users with permission: %s", e, exc_info=True)
            raise IAMPermissionError(
                detail=f"Failed to get bulk users with permission: {str(e)}",
                operation="get_bulk_users_with_permission",
                original_error=e
            ) from e