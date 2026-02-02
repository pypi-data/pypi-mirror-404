"""
Userstatus Operations - CRUD operations for Userstatus
"""
import os
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING

from google.cloud import firestore
from pydantic import ValidationError as PydanticValidationError

from ...models import UserStatus
from ...exceptions import ResourceNotFoundError, UserStatusError
from ..base import BaseFirestoreService

# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    from .user_subscription_operations import UsersubscriptionOperations
    from .user_permissions_operations import UserpermissionsOperations


class UserstatusOperations:
    """
    Handles CRUD operations for Userstatus documents
    """

    def __init__(
        self,
        firestore_client: firestore.Client,
        logger: Optional[logging.Logger] = None,
        timeout: float = 10.0,
        status_collection: Optional[str] = None,
        subscription_ops: Optional["UsersubscriptionOperations"] = None,
        permissions_ops: Optional["UserpermissionsOperations"] = None
    ):
        self.db = firestore_client
        self.logger = logger or logging.getLogger(__name__)
        self.timeout = timeout

        # Optional dependencies for comprehensive operations
        self.subscription_ops = subscription_ops
        self.permissions_ops = permissions_ops

        self.status_collection_name = status_collection or UserStatus.get_collection_name()

        # Archival configuration
        self.archive_userstatus_on_delete = os.getenv('ARCHIVE_USERSTATUS_ON_DELETE', 'true').lower() == 'true'
        self.archive_userstatus_collection_name = os.getenv(
            'ARCHIVE_USERSTATUS_COLLECTION_NAME',
            "~archive_core_user_userstatuss"
        )

        # Initialize DB service
        self._status_db_service = BaseFirestoreService[UserStatus](
            db=self.db,
            collection_name=self.status_collection_name,
            resource_type=UserStatus.OBJ_REF,
            model_class=UserStatus,
            logger=self.logger,
            timeout=self.timeout
        )

    async def get_userstatus(self, user_uid: str, convert_to_model: bool = True) -> Optional[UserStatus]:
        """Retrieve a user status by UID"""
        userstatus_id = f"{UserStatus.OBJ_REF}_{user_uid}"

        try:
            userstatus = await self._status_db_service.get_document(
                userstatus_id,
                convert_to_model=convert_to_model
            )
            if userstatus:
                self.logger.debug("Successfully retrieved user status for %s", user_uid)
                # Always return a UserStatus model to match the return type
                if isinstance(userstatus, dict):
                    return UserStatus(**userstatus)
                return userstatus
            else:
                self.logger.debug("User status not found for %s", user_uid)
                return None

        except ResourceNotFoundError:
            self.logger.debug("User status not found for %s", user_uid)
            return None
        except Exception as e:
            self.logger.error("Failed to fetch user status for %s: %s", user_uid, str(e), exc_info=True)
            raise UserStatusError(
                detail=f"Failed to fetch user status: {str(e)}",
                user_uid=user_uid,
                operation="get_userstatus",
                original_error=e
            ) from e

    async def create_userstatus(self, userstatus: UserStatus, creator_uid: Optional[str] = None) -> UserStatus:
        """Create a new user status"""
        self.logger.info(f"Creating user status for UID: {userstatus.user_uid}")
        try:
            doc_id = f"{UserStatus.OBJ_REF}_{userstatus.user_uid}"
            effective_creator_uid = creator_uid or userstatus.user_uid
            await self._status_db_service.create_document(doc_id, userstatus, effective_creator_uid)
            self.logger.info("Successfully created user status for UID: %s", userstatus.user_uid)
            return userstatus
        except Exception as e:
            self.logger.error("Error creating user status for %s: %s", userstatus.user_uid, e, exc_info=True)
            raise UserStatusError(
                detail=f"Failed to create user status: {str(e)}",
                user_uid=userstatus.user_uid,
                operation="create_userstatus",
                original_error=e
            ) from e

    async def update_userstatus(self, user_uid: str, status_data: Dict[str, Any], updater_uid: str) -> UserStatus:
        """Update a user status"""
        userstatus_id = f"{UserStatus.OBJ_REF}_{user_uid}"

        # Remove system fields that shouldn't be updated
        update_data = status_data.copy()
        update_data.pop('user_uid', None)
        update_data.pop('id', None)
        update_data.pop('created_at', None)
        update_data.pop('created_by', None)

        try:
            updated_doc_dict = await self._status_db_service.update_document(
                doc_id=userstatus_id,
                update_data=update_data,
                updater_uid=updater_uid
            )
            self.logger.info("Userstatus for %s updated successfully by %s", user_uid, updater_uid)
            return UserStatus(**updated_doc_dict)
        except ResourceNotFoundError as exc:
            raise UserStatusError(
                detail="User status not found",
                user_uid=user_uid,
                operation="update_userstatus"
            ) from exc
        except Exception as e:
            self.logger.error("Error updating Userstatus for %s: %s", user_uid, str(e), exc_info=True)
            raise UserStatusError(
                detail=f"Failed to update user status: {str(e)}",
                user_uid=user_uid,
                operation="update_userstatus",
                original_error=e
            ) from e

    async def delete_userstatus(self, user_uid: str, updater_uid: str = "system_deletion", archive: Optional[bool] = True) -> bool:
        """Delete (archive and delete) user status"""
        status_doc_id = f"{UserStatus.OBJ_REF}_{user_uid}"
        should_archive = archive if archive is not None else self.archive_userstatus_on_delete

        try:
            # Get status data for archival
            status_data = await self._status_db_service.get_document(status_doc_id, convert_to_model=False)

            if status_data:
                # Ensure we have a dict for archival
                status_dict = status_data if isinstance(status_data, dict) else status_data.__dict__

                # Archive if enabled
                if should_archive:
                    await self._status_db_service.archive_document(
                        document_data=status_dict,
                        doc_id=status_doc_id,
                        archive_collection=self.archive_userstatus_collection_name,
                        archived_by=updater_uid
                    )

                # Delete the original document
                await self._status_db_service.delete_document(status_doc_id)
                self.logger.info("Successfully deleted user status: %s", status_doc_id)
                return True
            else:
                self.logger.warning("User status %s not found for deletion", status_doc_id)
                return True  # Consider non-existent as successfully deleted

        except ResourceNotFoundError:
            self.logger.debug("User status %s not found for deletion (idempotent)", status_doc_id)
            return True  # Idempotent - already "deleted"
        except Exception as e:
            self.logger.error("Failed to delete user status %s: %s", status_doc_id, str(e), exc_info=True)
            raise UserStatusError(
                detail=f"Failed to delete user status: {str(e)}",
                user_uid=user_uid,
                operation="delete_userstatus",
                original_error=e
            ) from e

    async def validate_userstatus_data(
        self,
        status_data: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, list[str]]:
        """Validate user status data without creating documents"""
        errors = []
        if status_data:
            try:
                UserStatus(**status_data)
            except PydanticValidationError as e:
                errors.append(f"Status validation error: {str(e)}")
        return len(errors) == 0, errors

    async def validate_and_cleanup_user_permissions(
        self, user_uid: str, updater_uid: str, delete_expired: bool = True
    ) -> int:
        """Validate and clean up expired IAM permissions for a user."""
        userstatus = await self.get_userstatus(user_uid)
        if not userstatus:
            self.logger.warning("Userstatus not found for %s, cannot validate permissions.", user_uid)
            return 0

        removed_count = userstatus.cleanup_expired_permissions()

        if removed_count > 0 and delete_expired:
            await self.update_userstatus(
                user_uid,
                userstatus.model_dump(exclude_none=True),
                updater_uid=updater_uid
            )
            self.logger.info("Removed %d expired permissions for user %s.", removed_count, user_uid)

        return removed_count

    async def userstatus_exists(self, user_uid: str) -> bool:
        """Check if a user status exists."""
        return await self._status_db_service.document_exists(f"{UserStatus.OBJ_REF}_{user_uid}")

    ######################################################################
    ######################### Comprehensive Review Methods #############
    ######################################################################

    async def review_and_clean_active_subscription_credits_and_permissions(
        self,
        user_uid: str,
        updater_uid: str = "system_review",
        review_auto_renewal: bool = True,
        apply_fallback: bool = True,
        clean_expired_permissions: bool = True,
        review_credits: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive review of user's active subscription, credits, and permissions.
        This method handles:
        1. Subscription lifecycle (auto-renewal, fallback, expiration)
        2. Credit management based on subscription cycle timing
        3. Permission cleanup and management

        This is designed to be called on every authz request for comprehensive user state management.

        Args:
            user_uid: User UID to review
            updater_uid: User ID performing the review
            account_for_auto_renewal: Whether to auto-renew expired cycles if auto_renew_end_datetime is valid
            apply_fallback: Whether to apply fallback plans when subscriptions expire
            clean_expired_permissions: Whether to clean expired permissions
            review_credits: Whether to review and update subscription-based credits

        Returns:
            Dict containing detailed results of the review and actions taken
        """
        from datetime import datetime, timezone
        from ipulse_shared_base_ftredge.enums import SubscriptionStatus
        from ...models import UserSubscription

        self.logger.info("Starting comprehensive subscription, credits, and permissions review for user %s", user_uid)

        result = {
            'user_uid': user_uid,
            'timestamp': datetime.now(timezone.utc),
            'actions_taken': [],
            'subscription_status': None,
            'subscription_renewed': False,
            'fallback_applied': False,
            'subscription_revoked': False,
            'permissions_cleaned': 0,
            'permissions_added': 0,
            'credits_updated': 0,
            'error': None,
            'original_subscription': None,
            'final_subscription': None,
            'updated_userstatus': None  # Will be populated with the updated UserStatus
        }

        try:
            # Get current user status
            userstatus = await self.get_userstatus(user_uid)
            if not userstatus:
                result['actions_taken'].append('no_userstatus_found')
                return result

            # Always add the current userstatus to result (will be updated if database changes occur)
            result['updated_userstatus'] = userstatus

            # Check if there's an active subscription
            if not userstatus.active_subscription:
                result['actions_taken'].append('no_active_subscription')

                # Clean expired permissions if requested
                if clean_expired_permissions:
                    expired_permissions = userstatus.cleanup_expired_permissions()
                    if expired_permissions > 0:
                        result['permissions_cleaned'] = expired_permissions
                        result['actions_taken'].append('cleaned_expired_permissions')

                        # Save changes and update the result with the updated userstatus
                        updated_userstatus = await self.update_userstatus(
                            user_uid=user_uid,
                            status_data=userstatus.model_dump(exclude_none=True),
                            updater_uid=f"review:{updater_uid}"
                        )
                        result['updated_userstatus'] = updated_userstatus

                return result

            # Store original subscription for comparison
            result['original_subscription'] = userstatus.active_subscription
            now = datetime.now(timezone.utc)

            # Use the subscription's is_active() method to check current status
            if userstatus.active_subscription.is_active():
                result['subscription_status'] = str(SubscriptionStatus.ACTIVE)
                result['final_subscription'] = userstatus.active_subscription
                result['actions_taken'].append('subscription_still_active')

                # Update credits if subscription is active and review_credits is enabled
                if review_credits:
                    credits_updated = userstatus.update_subscription_credits()
                    if credits_updated > 0:
                        result['credits_updated'] = credits_updated
                        result['actions_taken'].append('updated_subscription_credits')

                # Clean expired permissions if requested
                if clean_expired_permissions:
                    expired_permissions = userstatus.cleanup_expired_permissions()
                    if expired_permissions > 0:
                        result['permissions_cleaned'] = expired_permissions
                        result['actions_taken'].append('cleaned_expired_permissions_only')

                # Save changes if any updates were made
                if result['credits_updated'] > 0 or result['permissions_cleaned'] > 0:
                    updated_userstatus = await self.update_userstatus(
                        user_uid=user_uid,
                        status_data=userstatus.model_dump(exclude_none=True),
                        updater_uid=f"review:{updater_uid}"
                    )
                    result['updated_userstatus'] = updated_userstatus

                return result

            # Subscription is not active - determine why and what to do
            subscription = userstatus.active_subscription

            # Check if cycle is expired but auto-renewal is still valid
            if (review_auto_renewal and
                subscription.auto_renew_end_datetime and
                now <= subscription.auto_renew_end_datetime and
                now > subscription.cycle_end_datetime_safe):

                # Attempt auto-renewal by extending the cycle
                try:
                    # Calculate new cycle start date (where the last cycle ended)
                    new_cycle_start = subscription.cycle_end_datetime_safe

                    # Create new subscription with updated cycle start date
                    subscription_dict = subscription.model_dump()
                    subscription_dict.update({
                        'cycle_start_datetime': new_cycle_start,
                        'cycle_end_datetime': None,  # Let the model auto-calculate this
                        'updated_at': now,
                        'updated_by': f"UserstatusOperations.auto_renew:{updater_uid}"
                    })

                    renewed_subscription = UserSubscription(**subscription_dict)

                    # Apply the renewed subscription
                    userstatus.apply_subscription(
                        renewed_subscription,
                        add_associated_permissions=True,
                        remove_previous_subscription_permissions=True,
                        granted_by=f"UserstatusOperations.review.auto_renew:{updater_uid}"
                    )

                    result['subscription_renewed'] = True
                    result['subscription_status'] = str(userstatus.active_subscription.status)
                    result['final_subscription'] = renewed_subscription
                    result['actions_taken'].append('auto_renewed_cycle')

                except (ValueError, UserStatusError) as renewal_error:
                    self.logger.error("Auto-renewal failed for user %s: %s", user_uid, renewal_error)
                    result['error'] = f"Auto-renewal failed: {str(renewal_error)}"
                    result['actions_taken'].append('auto_renewal_failed')
                    # Continue to fallback logic

            # If auto-renewal didn't happen or failed, check for fallback
            if not result['subscription_renewed']:
                if apply_fallback and subscription.fallback_plan_id:
                    try:
                        # We need subscription_ops to handle the fallback plan logic
                        if self.subscription_ops:
                            # Import the catalog service to get fallback plan
                            from ...services.catalog.catalog_subscriptionplan_service import CatalogSubscriptionPlanService

                            catalog_service = CatalogSubscriptionPlanService(firestore_client=self.db, logger=self.logger)
                            fallback_plan = await catalog_service.get_subscriptionplan(subscription.fallback_plan_id)

                            if fallback_plan:
                                # Create new subscription from fallback plan
                                fallback_subscription = self.subscription_ops.create_subscription_from_subscriptionplan(
                                    plan=fallback_plan,
                                    source=f"fallback_from_{subscription.plan_id}:review:{updater_uid}",
                                    granted_at=now,
                                    auto_renewal_end=fallback_plan.plan_default_auto_renewal_end
                                )

                                # Apply fallback subscription
                                permissions_added = userstatus.apply_subscription(
                                    fallback_subscription,
                                    add_associated_permissions=True,
                                    remove_previous_subscription_permissions=True,
                                    granted_by=f"UserstatusOperations.review.fallback:{updater_uid}"
                                )

                                result['fallback_applied'] = True
                                result['subscription_status'] = str(userstatus.active_subscription.status)
                                result['final_subscription'] = fallback_subscription
                                result['permissions_added'] = permissions_added
                                result['actions_taken'].append('applied_fallback_plan')

                            else:
                                self.logger.warning("Fallback plan %s not found for user %s", subscription.fallback_plan_id, user_uid)
                                result['actions_taken'].append('fallback_plan_not_found')
                        else:
                            self.logger.warning("Cannot apply fallback - subscription_ops not available")
                            result['actions_taken'].append('fallback_unavailable_no_subscription_ops')

                    except (ValueError, UserStatusError) as fallback_error:
                        self.logger.error("Fallback application failed for user %s: %s", user_uid, fallback_error)
                        result['error'] = f"Fallback failed: {str(fallback_error)}"
                        result['actions_taken'].append('fallback_failed')
                        # Continue to revocation logic

            # If no renewal or fallback happened, revoke the subscription
            if not result['subscription_renewed'] and not result['fallback_applied']:
                permissions_cleaned = userstatus.revoke_subscription(remove_associated_permissions=True)
                result['subscription_revoked'] = True
                result['subscription_status'] = None
                result['permissions_cleaned'] = permissions_cleaned
                result['actions_taken'].append('subscription_revoked')

            # Clean up all expired permissions (not just those associated with the subscription)
            if clean_expired_permissions:
                additional_expired = userstatus.cleanup_expired_permissions()
                if additional_expired > 0:
                    result['permissions_cleaned'] += additional_expired
                    result['actions_taken'].append('cleaned_additional_expired_permissions')

            # Save all changes to database
            updated_userstatus = await self.update_userstatus(
                user_uid=user_uid,
                status_data=userstatus.model_dump(exclude_none=False),  # Include None values for proper updates
                updater_uid=f"review:{updater_uid}"
            )

            # Add the updated UserStatus to the result
            result['updated_userstatus'] = updated_userstatus

            self.logger.info(
                "Completed comprehensive review for user %s. Status: %s, Actions: %s",
                user_uid, result['subscription_status'], result['actions_taken']
            )

        except Exception as e:
            self.logger.error("Comprehensive review failed for user %s: %s", user_uid, e, exc_info=True)
            result['error'] = str(e)
            result['actions_taken'].append('review_failed')
            # Re-raise for proper error handling
            raise

        return result
