"""Service for managing credit operations in a generic way."""
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from google.cloud import firestore
from ipulse_shared_core_ftredge.exceptions import ServiceError, ResourceNotFoundError, ValidationError
from ipulse_shared_core_ftredge.models import UserStatus

# Default Firestore timeout if not provided by the consuming application
DEFAULT_FIRESTORE_TIMEOUT = 15.0

class UserChargingService:
    """
    Service class for charging operations.
    Designed to be project-agnostic and directly uses UserStatus model constants.
    """

    def __init__(
        self,
        db: firestore.Client,
        logger: Optional[logging.Logger] = None,
        firestore_timeout: float = DEFAULT_FIRESTORE_TIMEOUT
    ):
        """
        Initialize the charging service.

        Args:
            db: Firestore client.
            logger: Optional logger instance. Defaults to a new logger for this module.
            firestore_timeout: Timeout for Firestore operations in seconds.
        """
        self.db = db
        # Use UserStatus constants directly
        self.users_status_collection_name = UserStatus.COLLECTION_NAME
        self.userstatus_doc_prefix = f"{UserStatus.OBJ_REF}_" # Append underscore to OBJ_REF
        self.logger = logger or logging.getLogger(__name__)
        self.timeout = firestore_timeout

        self.logger.info(
            f"UserChargingService initialized using UserStatus constants. Collection: {self.users_status_collection_name}, "
            f"Doc Prefix: {self.userstatus_doc_prefix}, Timeout: {self.timeout}s"
        )

    async def verify_enough_credits(
        self,
        user_uid: str,
        required_credits_for_resource: float,
        pre_fetched_user_credits: Optional[Dict[str, float]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify if a user has enough credits for an operation.

        Args:
            user_uid: The user's UID.
            required_credits_for_resource: The number of credits required for the operation.
            pre_fetched_user_credits: Optional dict with pre-fetched credit info.
                                      (keys: 'sbscrptn_based_insight_credits', 'extra_insight_credits')

        Returns:
            Tuple of (has_enough_credits, userstatus_data) where userstatus_data
            will be a dict with keys 'sbscrptn_based_insight_credits' and 'extra_insight_credits'.

        Raises:
            ValidationError: If required_credits_for_resource is None (pricing not properly configured).
        """
        self.logger.info(
            f"verify_enough_credits called for user {user_uid}, "
            f"required_credits={required_credits_for_resource}, "
            f"pre_fetched_credits={pre_fetched_user_credits}"
        )

        if required_credits_for_resource is None:
            self.logger.error(f"Credit cost is None for user {user_uid}, pricing not properly configured")
            raise ValidationError(
                resource_type="credit_cost",
                detail="Credit cost is not configured for this resource",
                resource_id=None, # Resource ID might not be known here, or could be passed
                additional_info={"user_uid": user_uid}
            )

        if required_credits_for_resource <= 0:
            self.logger.info(f"No credits required for user {user_uid}, bypassing credit verification")
            return True, {"sbscrptn_based_insight_credits": 0, "extra_insight_credits": 0}

        if pre_fetched_user_credits is not None:
            self.logger.info(f"Using pre-fetched credit info for user {user_uid}")
            subscription_credits = pre_fetched_user_credits.get("sbscrptn_based_insight_credits", 0)
            extra_credits = pre_fetched_user_credits.get("extra_insight_credits", 0)
            total_credits = subscription_credits + extra_credits

            self.logger.info(
                f"User {user_uid} has {total_credits} total pre-fetched credits "
                f"(subscription: {subscription_credits}, extra: {extra_credits})"
            )

            user_credits = {
                "sbscrptn_based_insight_credits": subscription_credits,
                "extra_insight_credits": extra_credits
            }

            has_enough_credits = total_credits >= required_credits_for_resource
            return has_enough_credits, user_credits

        try:
            self.logger.info(
                f"Fetching user status from Firestore for user {user_uid} (collection: {self.users_status_collection_name})"
            )
            full_userstatus_doc = await self._get_userstatus(user_uid)

            subscription_credits = full_userstatus_doc.get("sbscrptn_based_insight_credits", 0)
            extra_credits = full_userstatus_doc.get("extra_insight_credits", 0)
            total_credits = subscription_credits + extra_credits

            self.logger.info(
                f"User {user_uid} has {total_credits} total credits from Firestore "
                f"(subscription: {subscription_credits}, extra: {extra_credits})"
            )

            has_enough_credits = total_credits >= required_credits_for_resource

            user_credits = {
                "sbscrptn_based_insight_credits": subscription_credits,
                "extra_insight_credits": extra_credits
            }

            return has_enough_credits, user_credits

        except ResourceNotFoundError:
            self.logger.warning(f"User status not found for {user_uid} in {self.users_status_collection_name}. Assuming no credits.")
            return False, {"sbscrptn_based_insight_credits": 0, "extra_insight_credits": 0}
        except Exception as e:
            self.logger.error(f"Error verifying credits for user {user_uid}: {str(e)}")
            raise ServiceError(
                operation="verifying credits",
                error=e,
                resource_type="user_credits",
                resource_id=user_uid,
                additional_info={"credits_to_take": required_credits_for_resource}
            ) from e

    async def debit_credits_transaction(self, user_uid: str, credits_to_take: Optional[float], operation_details: str) -> Tuple[bool, Optional[Dict[str, float]]]:
        """
        Charge a user's credits for an operation.

        Args:
            user_uid: The user's UID.
            credits_to_take: The number of credits to charge.
            operation_details: Details about the operation (for logging).

        Returns:
            Tuple of (success_status: bool, updated_credits: Optional[Dict[str, float]])
            where updated_credits contains 'sbscrptn_based_insight_credits' and 'extra_insight_credits'
            if charging was successful.

        Raises:
            ValidationError: If credits_to_take is None (pricing not properly configured).
        """
        if credits_to_take is None:
            self.logger.error(f"Credit cost is None for user {user_uid} (charge_credits), pricing not properly configured")
            raise ValidationError(
                resource_type="credit_cost",
                detail="Credit cost is not configured for this resource (charge_credits)",
                resource_id=None,
                additional_info={"user_uid": user_uid}
            )

        if credits_to_take == 0:
            self.logger.info(f"No credits to charge for user {user_uid}, operation: {operation_details}")
            # If no charge, current credits are unchanged. Fetch them if needed by caller.
            # For simplicity here, returning None for updated_credits as no transaction occurred.
            # The caller (CreditProcessor) will handle fetching if it needs the current state.
            # Alternatively, we could fetch here, but it's cleaner if CreditProcessor handles it.
            return True, None


        try:
            userstatus_id = f"{self.userstatus_doc_prefix}{user_uid}"
            user_ref = self.db.collection(self.users_status_collection_name).document(userstatus_id)

            transaction = self.db.transaction()

            @firestore.transactional
            def update_credits_transaction(transaction_obj, current_user_ref) -> Tuple[bool, Optional[Dict[str, float]]]:
                user_doc = current_user_ref.get(transaction=transaction_obj)
                if not user_doc.exists:
                    self.logger.warning(
                        f"Cannot charge credits - user status not found for {user_uid} in {self.users_status_collection_name}"
                    )
                    return False, None

                userstatus = user_doc.to_dict()

                current_subscription_credits = userstatus.get("sbscrptn_based_insight_credits", 0.0)
                current_extra_credits = userstatus.get("extra_insight_credits", 0.0)
                total_available_credits = current_subscription_credits + current_extra_credits

                if total_available_credits < credits_to_take:
                    self.logger.warning(
                        f"Insufficient credits for user {user_uid} during transaction: "
                        f"has {total_available_credits}, needs {credits_to_take}"
                    )
                    # Return current credits if charge fails due to insufficient funds
                    return False, {
                        "sbscrptn_based_insight_credits": current_subscription_credits,
                        "extra_insight_credits": current_extra_credits
                    }

                # Calculate how much to deduct from each type of credit
                subscription_credits_deducted = min(current_subscription_credits, credits_to_take)
                remaining_charge = credits_to_take - subscription_credits_deducted
                extra_credits_deducted = min(current_extra_credits, remaining_charge)

                # This check should ideally not be needed if total_available_credits was sufficient,
                # but as a safeguard:
                if (subscription_credits_deducted + extra_credits_deducted) < credits_to_take:
                    self.logger.error(
                        f"Credit calculation error for user {user_uid}. "
                        f"Required: {credits_to_take}, Calculated deduction: {subscription_credits_deducted + extra_credits_deducted}"
                    )
                    # This case implies a logic flaw or race condition if not for the initial check.
                    # Return current credits as charge effectively failed.
                    return False, {
                        "sbscrptn_based_insight_credits": current_subscription_credits,
                        "extra_insight_credits": current_extra_credits
                    }


                new_subscription_credits = current_subscription_credits - subscription_credits_deducted
                new_extra_credits = current_extra_credits - extra_credits_deducted

                update_data: Dict[str, Any] = {
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "updated_by": "charging_service__debit_credits_transaction"  # Static identifier for this operation
                }

                if subscription_credits_deducted > 0:
                    update_data["sbscrptn_based_insight_credits"] = firestore.Increment(-subscription_credits_deducted)
                    update_data["sbscrptn_based_insight_credits_updtd_on"] = datetime.now(timezone.utc).isoformat()

                if extra_credits_deducted > 0:
                    update_data["extra_insight_credits"] = firestore.Increment(-extra_credits_deducted)
                    update_data["extra_insight_credits_updtd_on"] = datetime.now(timezone.utc).isoformat()

                transaction_obj.update(current_user_ref, update_data)

                # Return success and the calculated new credit balances
                return True, {
                    "sbscrptn_based_insight_credits": new_subscription_credits,
                    "extra_insight_credits": new_extra_credits
                }

            success, updated_credits_dict = update_credits_transaction(transaction, user_ref)

            if success:
                self.logger.info(
                    f"Successfully charged {credits_to_take} credits for user {user_uid}. "
                    f"Operation: {operation_details}. New balances: {updated_credits_dict}"
                )
            else:
                self.logger.warning(
                    f"Failed to charge {credits_to_take} credits for user {user_uid} (transaction outcome). "
                    f"Operation: {operation_details}. Current balances: {updated_credits_dict}"
                )

            return success, updated_credits_dict

        except Exception as e:
            self.logger.error(f"Error charging credits for user {user_uid}: {str(e)}")
            raise ServiceError(
                operation="charging credits",
                error=e,
                resource_type="user_credits",
                resource_id=user_uid,
                additional_info={"credits_to_take": credits_to_take}
            ) from e

    async def _get_userstatus(self, user_uid: str) -> Dict[str, Any]:
        """Get a user's status document."""
        try:
            userstatus_id = f"{self.userstatus_doc_prefix}{user_uid}"
            doc_ref = self.db.collection(self.users_status_collection_name).document(userstatus_id)

            # Using the timeout value set during initialization
            doc = await doc_ref.get(timeout=self.timeout)

            if not doc.exists:
                raise ResourceNotFoundError(
                    resource_type="userstatus", # Generic resource type
                    resource_id=userstatus_id,
                    additional_info={"collection": self.users_status_collection_name}
                )

            return doc.to_dict()

        except ResourceNotFoundError:
            raise
        except Exception as e: # Catch generic Exception to handle potential timeout errors from Firestore client
            self.logger.error(f"Error getting user status for {user_uid} from {self.users_status_collection_name}: {str(e)}")
            raise ServiceError(
                operation="getting user status",
                error=e,
                resource_type="userstatus",
                resource_id=user_uid,
                additional_info={"collection": self.users_status_collection_name}
            ) from e

