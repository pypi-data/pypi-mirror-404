"""
Subscription Management Operations - Handle user subscriptions and related operations
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from google.cloud import firestore
from google.cloud.exceptions import GoogleCloudError
from ipulse_shared_base_ftredge.enums import SubscriptionPlanName, SubscriptionStatus
from ...models import UserSubscription, SubscriptionPlan
from ...exceptions import SubscriptionError, UserStatusError, ServiceError
from .userstatus_operations import UserstatusOperations
from .user_permissions_operations import UserpermissionsOperations


class UsersubscriptionOperations:
    """
    Handles subscription-related operations for users
    """

    def __init__(
        self,
        firestore_client: firestore.Client,
        userstatus_ops: UserstatusOperations,
        permissions_ops: UserpermissionsOperations,
        logger: Optional[logging.Logger] = None,
        timeout: float = 10.0
    ):
        self.db = firestore_client
        self.userstatus_ops = userstatus_ops
        self.permissions_ops = permissions_ops
        self.logger = logger or logging.getLogger(__name__)
        self.timeout = timeout

    def create_subscription_from_subscriptionplan(
        self,
        plan: SubscriptionPlan,
        source: str,
        granted_at: Optional[datetime] = None,
        auto_renewal_end: Optional[datetime] = None
    ) -> UserSubscription:
        """
        Common helper function to create a UserSubscription from a SubscriptionPlan.

        Args:
            plan: The subscription plan to convert
            source: Source identifier for the subscription
            granted_at: Optional granted timestamp (defaults to now)
            auto_renewal: Optional auto-renewal override

        Returns:
            UserSubscription object
        """
        # Use provided granted_at or default to now
        start_date = granted_at or datetime.now(timezone.utc)

        # Calculate end date based on plan validity
        if not plan.plan_validity_cycle_length or not plan.plan_validity_cycle_unit:
            raise SubscriptionError(
                detail="Missing or invalid subscription duration fields",
                plan_id=plan.id or "unknown",
                operation="_create_subscription_from_plan"
            )

        end_date = UserSubscription.calculate_cycle_end_date(
            start_date,
            plan.plan_validity_cycle_length,
            plan.plan_validity_cycle_unit
        )

        # Use provided auto_renewal_end or default from plan
        effective_auto_renewal_end = auto_renewal_end if auto_renewal_end is not None else plan.plan_default_auto_renewal_end

        try:
            # Validate plan name
            plan_name_enum = SubscriptionPlanName(plan.plan_name)
        except ValueError as e:
            raise SubscriptionError(
                detail=f"Invalid plan name '{plan.plan_name}': {str(e)}",
                plan_id=plan.id or "unknown",
                operation="_create_subscription_from_plan",
                original_error=e
            ) from e

        return UserSubscription(
            plan_name=plan_name_enum,
            plan_version=plan.plan_version,
            plan_id=plan.id or f"{plan.plan_name}_{plan.plan_version}",
            cycle_start_datetime=start_date,
            cycle_end_datetime=end_date,
            validity_time_length=plan.plan_validity_cycle_length,
            validity_time_unit=plan.plan_validity_cycle_unit,
            auto_renew_end_datetime=effective_auto_renewal_end,
            status=SubscriptionStatus.ACTIVE,
            granted_iam_permissions=plan.granted_iam_permissions or [],
            fallback_plan_id=plan.fallback_plan_id_if_current_plan_expired,
            price_paid_usd=float(plan.plan_per_cycle_price_usd if plan.plan_per_cycle_price_usd is not None else 0.0),
            created_by=source,
            updated_by=source,
            subscription_based_insight_credits_per_update=int(plan.subscription_based_insight_credits_per_update if plan.subscription_based_insight_credits_per_update is not None else 0),
            subscription_based_insight_credits_update_freq_h=int(plan.subscription_based_insight_credits_update_freq_h if plan.subscription_based_insight_credits_update_freq_h is not None else 24),
            extra_insight_credits_per_cycle=int(plan.extra_insight_credits_per_cycle if plan.extra_insight_credits_per_cycle is not None else 0),
            voting_credits_per_update=int(plan.voting_credits_per_update if plan.voting_credits_per_update is not None else 0),
            voting_credits_update_freq_h=int(plan.voting_credits_update_freq_h if plan.voting_credits_update_freq_h is not None else 744),
        )

    async def fetch_subscriptionplan_and_apply_subscription_to_user(
        self,
        user_uid: str,
        plan_id: str,
        updater_uid: str,
        source: str = "system_default_config",
        granted_at: Optional[datetime] = None,
        auto_renewal_end: Optional[datetime] = None
    ) -> UserSubscription:
        """
        Fetch a subscription plan from catalog service and apply to user.

        Args:
            user_uid: User ID to apply subscription to
            plan_id: Plan ID to fetch and apply
            updater_uid: Who is applying the subscription
            source: Source identifier
            granted_at: Optional granted timestamp (overrides plan defaults)
            auto_renewal_end: Optional auto-renewal end date (overrides plan defaults)

        Returns:
            Applied UserSubscription

        Raises:
            SubscriptionError: If plan not found or application fails
        """
        self.logger.info("Fetching and applying subscription plan %s to user %s", plan_id, user_uid)

        try:
            # Import the catalog service (lazy import to avoid circular dependencies)
            from ...services.catalog.catalog_subscriptionplan_service import CatalogSubscriptionPlanService

            # Initialize catalog service using our existing firestore client
            catalog_service = CatalogSubscriptionPlanService(firestore_client=self.db, logger=self.logger)

            # Fetch the plan from catalog
            catalog_plan = await catalog_service.get_subscriptionplan(plan_id)
            if not catalog_plan:
                raise SubscriptionError(
                    detail=f"Subscription plan '{plan_id}' not found in catalog",
                    user_uid=user_uid,
                    plan_id=plan_id,
                    operation="fetch_and_apply_subscriptionplan_to_user"
                )

            # Apply the subscription plan to user
            return await self.apply_subscriptionplan(
                user_uid=user_uid,
                subscriptionplan=catalog_plan,
                updater_uid=updater_uid,
                source=source,
                granted_at=granted_at,
                auto_renewal_end=auto_renewal_end,
                add_associated_permissions=True
            )

        except SubscriptionError:
            # Re-raise subscription errors as-is
            raise
        except Exception as e:
            self.logger.error("Failed to fetch and apply subscription plan %s: %s", plan_id, e, exc_info=True)
            raise SubscriptionError(
                detail=f"Failed to fetch and apply subscription plan: {str(e)}",
                user_uid=user_uid,
                plan_id=plan_id,
                operation="fetch_and_apply_subscriptionplan_to_user",
                original_error=e
            ) from e

    async def apply_subscriptionplan(
        self,
        user_uid: str,
        subscriptionplan: SubscriptionPlan,
        updater_uid: str,
        source: str = "system_default_config",
        granted_at: Optional[datetime] = None,
        auto_renewal_end: Optional[datetime] = None,
        add_associated_permissions: bool = True
    ) -> UserSubscription:
        """
        Apply a ready subscription plan to a user.

        Args:
            user_uid: User ID to apply subscription to
            subscriptionplan: Ready SubscriptionPlan object
            updater_uid: Who is applying the subscription
            source: Source identifier
            granted_at: Optional granted timestamp (overrides plan defaults)
            auto_renewal: Optional auto-renewal setting (overrides plan defaults)
            add_associated_permissions: If True, adds IAM permissions from the subscription

        Returns:
            Applied UserSubscription
        """
        self.logger.info("Applying subscription plan %s to user %s", subscriptionplan.id, user_uid)

        # Get user status
        userstatus = await self.userstatus_ops.get_userstatus(user_uid)
        if not userstatus:
            raise UserStatusError(
                detail=f"Userstatus not found for user_uid {user_uid}",
                user_uid=user_uid,
                operation="apply_subscriptionplan"
            )

        try:
            # Create subscription from plan using helper
            subscription = self.create_subscription_from_subscriptionplan(
                plan=subscriptionplan,
                source=f"{source}:{updater_uid}",
                granted_at=granted_at,
                auto_renewal_end=auto_renewal_end
            )

            # Apply subscription to user (this will handle removing existing permissions and adding new ones)
            permissions_added = userstatus.apply_subscription(
                subscription,
                add_associated_permissions=add_associated_permissions,
                remove_previous_subscription_permissions=True,
                granted_by=f"UsersubscriptionOperations.apply:{source}:{updater_uid}"
            )

            # Update user status metadata
            userstatus.updated_at = datetime.now(timezone.utc)
            userstatus.updated_by = f"UsersubscriptionOperations.apply:{source}:{updater_uid}"

            # Save to database
            await self.userstatus_ops.update_userstatus(
                user_uid=user_uid,
                status_data=userstatus.model_dump(exclude_none=True),
                updater_uid=f"UsersubscriptionOperations:{source}:{updater_uid}"
            )

            self.logger.info("Successfully applied subscription %s for user %s", subscription.plan_id, user_uid)
            if add_associated_permissions:
                self.logger.info("Applied %d IAM permissions from new subscription for user %s", permissions_added, user_uid)

            return subscription

        except Exception as e:
            self.logger.error("Failed to apply subscription to user status: %s", e, exc_info=True)
            raise SubscriptionError(
                detail=f"Failed to apply subscription to user: {str(e)}",
                user_uid=user_uid,
                plan_id=subscriptionplan.id,
                operation="apply_subscriptionplan",
                original_error=e
            ) from e

    async def get_user_active_subscription(self, user_uid: str) -> Optional[UserSubscription]:
        """Get the user's currently active subscription"""
        userstatus = await self.userstatus_ops.get_userstatus(user_uid)
        if userstatus and userstatus.active_subscription and userstatus.active_subscription.is_active():
            self.logger.info("Active subscription found for user %s: %s", user_uid, userstatus.active_subscription.plan_id)
            return userstatus.active_subscription

        self.logger.info("No active subscription found for user %s", user_uid)
        return None

    async def update_user_subscription(
        self,
        user_uid: str,
        subscription_updates: dict,
        updater_uid: str = "admin_update"
    ) -> Optional[UserSubscription]:
        """
        Update user's active subscription with new values.
        Useful for admin corrections or payment-related updates.

        Args:
            user_uid: User ID
            subscription_updates: Dictionary of fields to update
            updater_uid: Who is making the update

        Returns:
            Updated UserSubscription or None if no active subscription
        """
        self.logger.info("Updating subscription for user %s", user_uid)

        userstatus = await self.userstatus_ops.get_userstatus(user_uid)
        if not userstatus:
            raise UserStatusError(
                detail=f"Userstatus not found for user_uid {user_uid}",
                user_uid=user_uid,
                operation="update_user_subscription"
            )

        if not userstatus.active_subscription:
            self.logger.info("No active subscription to update for user %s", user_uid)
            return None

        try:
            # Update the subscription
            subscription_dict = userstatus.active_subscription.model_dump()
            subscription_dict.update(subscription_updates)
            subscription_dict['updated_at'] = datetime.now(timezone.utc)
            subscription_dict['updated_by'] = updater_uid

            updated_subscription = UserSubscription(**subscription_dict)

            # Apply updated subscription
            userstatus.apply_subscription(updated_subscription, granted_by=f"UsersubscriptionOperations.update:{updater_uid}")
            userstatus.updated_at = datetime.now(timezone.utc)
            userstatus.updated_by = f"UsersubscriptionOperations.update:{updater_uid}"

            await self.userstatus_ops.update_userstatus(
                user_uid=user_uid,
                status_data=userstatus.model_dump(exclude_none=True),
                updater_uid=f"UsersubscriptionOperations:{updater_uid}"
            )

            self.logger.info("Successfully updated subscription for user %s", user_uid)
            return updated_subscription

        except Exception as e:
            self.logger.error("Failed to update subscription for user %s: %s", user_uid, e, exc_info=True)
            raise SubscriptionError(
                detail=f"Failed to update subscription: {str(e)}",
                user_uid=user_uid,
                operation="update_user_subscription",
                original_error=e
            ) from e

    async def cancel_user_subscription(
        self,
        user_uid: str,
        updater_uid: str,
        reason: Optional[str] = None
    ) -> bool:
        """Cancel a user's active subscription"""
        self.logger.info("Attempting to cancel subscription for user %s. Reason: %s", user_uid, reason)

        userstatus = await self.userstatus_ops.get_userstatus(user_uid)
        if not userstatus:
            raise UserStatusError(
                detail=f"Userstatus not found for user_uid {user_uid}",
                user_uid=user_uid,
                operation="cancel_user_subscription"
            )

        effective_canceller = f"UsersubscriptionOperations.cancel:{updater_uid}:{reason or 'not_specified'}"

        if userstatus.active_subscription and userstatus.active_subscription.status == SubscriptionStatus.ACTIVE:
            try:
                self.logger.info("Cancelling active subscription %s for user %s",
                               userstatus.active_subscription.plan_id, user_uid)

                # Revoke the subscription and its associated IAM permissions in one call
                revoked_permissions = userstatus.revoke_subscription(remove_associated_permissions=True)
                if revoked_permissions > 0:
                    self.logger.info("Revoked %d IAM permissions from cancelled subscription for user %s", revoked_permissions, user_uid)
                else:
                    self.logger.info("No IAM permissions to revoke from cancelled subscription for user %s", user_uid)

                userstatus.updated_at = datetime.now(timezone.utc)
                userstatus.updated_by = effective_canceller

                await self.userstatus_ops.update_userstatus(
                    user_uid=user_uid,
                    status_data=userstatus.model_dump(exclude_none=True),
                    updater_uid=effective_canceller
                )

                self.logger.info("Successfully cancelled subscription for user %s", user_uid)
                return True

            except Exception as e:
                self.logger.error("Failed to cancel subscription: %s", e, exc_info=True)
                raise SubscriptionError(
                    detail=f"Failed to cancel subscription: {str(e)}",
                    user_uid=user_uid,
                    operation="cancel_user_subscription",
                    original_error=e
                ) from e
        else:
            self.logger.info("No active subscription to cancel for user %s", user_uid)
            return False

    async def downgrade_user_subscription_to_fallback_subscriptionplan(
        self,
        user_uid: str,
        reason: str = "subscription_expired"
    ) -> Optional[UserSubscription]:
        """
        Downgrade user to their fallback plan.

        Args:
            user_uid: User ID
            reason: Reason for downgrade

        Returns:
            New UserSubscription if fallback plan exists, None otherwise
        """
        self.logger.info("Attempting to downgrade user %s to fallback plan. Reason: %s", user_uid, reason)

        userstatus = await self.userstatus_ops.get_userstatus(user_uid)
        if not userstatus:
            raise UserStatusError(
                detail=f"Userstatus not found for user_uid {user_uid}",
                user_uid=user_uid,
                operation="downgrade_to_fallback_plan"
            )

        # Check if user has an active subscription with a fallback plan
        if not userstatus.active_subscription:
            self.logger.info("No active subscription for user %s - cannot downgrade", user_uid)
            return None

        fallback_plan_id = userstatus.active_subscription.fallback_plan_id
        if not fallback_plan_id:
            self.logger.info("No fallback plan configured for user %s", user_uid)
            return None

        try:
            # Fetch the fallback plan using catalog service first
            try:
                # Import the catalog service (lazy import to avoid circular dependencies)
                from ...services.catalog.catalog_subscriptionplan_service import CatalogSubscriptionPlanService

                # Initialize catalog service using our existing firestore client
                catalog_service = CatalogSubscriptionPlanService(firestore_client=self.db, logger=self.logger)

                # Fetch the fallback plan from catalog
                fallback_plan = await catalog_service.get_subscriptionplan(fallback_plan_id)
                if not fallback_plan:
                    self.logger.error("Fallback plan %s not found in catalog", fallback_plan_id)
                    return None

            except (GoogleCloudError, ServiceError) as e:
                self.logger.error("Failed to fetch fallback plan %s from catalog: %s", fallback_plan_id, e)
                return None

            # Store the current subscription plan_id for logging
            current_plan_id = userstatus.active_subscription.plan_id

            # Create new subscription from fallback plan with updated granted_at
            new_subscription = self.create_subscription_from_subscriptionplan(
                plan=fallback_plan,
                source=f"downgrade_from_{current_plan_id}:{reason}",
                granted_at=datetime.now(timezone.utc),  # Set to now for downgrade
                auto_renewal_end=fallback_plan.plan_default_auto_renewal_end
            )

            # Apply the new subscription to user (this will handle revoking existing permissions and adding new ones)
            permissions_added = userstatus.apply_subscription(
                new_subscription,
                add_associated_permissions=True,
                remove_previous_subscription_permissions=True,
                granted_by=f"UsersubscriptionOperations:downgrade:{reason}"
            )
            userstatus.updated_at = datetime.now(timezone.utc)
            userstatus.updated_by = f"UsersubscriptionOperations:downgrade:{reason}"

            await self.userstatus_ops.update_userstatus(
                user_uid=user_uid,
                status_data=userstatus.model_dump(exclude_none=True),
                updater_uid=f"downgrade:{reason}"
            )

            self.logger.info("Applied %d IAM permissions from fallback subscription for user %s", permissions_added, user_uid)

            self.logger.info(
                "Successfully downgraded user %s from %s to fallback plan %s",
                user_uid, current_plan_id, fallback_plan_id
            )
            return new_subscription

        except Exception as e:
            self.logger.error("Failed to downgrade user %s to fallback plan: %s", user_uid, e, exc_info=True)
            raise SubscriptionError(
                detail=f"Failed to downgrade to fallback plan: {str(e)}",
                user_uid=user_uid,
                plan_id=fallback_plan_id,
                operation="downgrade_to_fallback_plan",
                original_error=e
            ) from e

    ######################################################################
    ######################### Subscription Lifecycle Support Methods #####
    ######################################################################
    # Note: The main review method has been moved to UserStatusOperations
    # as it manages overall user status, not just subscriptions