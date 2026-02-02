"""
User Charging Operations

Handles all credit-related operations for users including:
- Credit verification and charging transactions
- Single item and batch processing workflows
- Credit addition and management operations

Follows the established UserCoreService operation class pattern with dependency injection
and consistent error handling.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable, Awaitable, TypeVar, Tuple
from google.cloud import firestore

from ...models.user.userstatus import UserStatus
from ipulse_shared_core_ftredge.exceptions import ValidationError
from .userstatus_operations import UserstatusOperations

T = TypeVar('T')


class UserChargingOperations:
    """Handles all credit-related operations for users following UserCoreService patterns."""

    def __init__(
        self,
        userstatus_ops: UserstatusOperations,
        logger,
        timeout: float = 10.0,
        bypass_credit_check: bool = False
    ):
        """
        Initialize UserChargingOperations with dependency injection pattern.

        Args:
            userstatus_ops: UserstatusOperations instance for user data access
            logger: Logger instance for operation logging
            timeout: Operation timeout in seconds
            bypass_credit_check: If True, bypasses credit checks for debugging/testing
        """
        self.userstatus_ops = userstatus_ops
        self.db = userstatus_ops.db  # Get firestore client from userstatus_ops
        self.logger = logger
        self.timeout = timeout
        self.bypass_credit_check = bypass_credit_check

        # Use UserStatus constants following established patterns
        self.users_status_collection_name = UserStatus.COLLECTION_NAME
        self.userstatus_doc_prefix = f"{UserStatus.OBJ_REF}_"

    # ========================================================================
    # LOW-LEVEL CREDIT OPERATIONS (from UserChargingService)
    # ========================================================================

    async def verify_enough_credits(
        self,
        user_uid: str,
        required_credits_for_resource: float,
        credits_extracted_from_authz_response: Optional[Dict[str, float]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify if user has sufficient credits for a resource.

        Args:
            user_uid: User's UID
            required_credits_for_resource: Credits required for the operation
            pre_fetched_user_credits: Optional pre-fetched credit information

        Returns:
            Tuple of (has_enough_credits: bool, user_credits: Dict)

        Raises:
            ValidationError: If validation fails
        """
        if required_credits_for_resource is None:
            raise ValidationError(
                resource_type="credit_cost",
                detail="Credit cost is not configured for this resource (verify_enough_credits)",
                resource_id=None,
                additional_info={"user_uid": user_uid}
            )

        if required_credits_for_resource < 0:
            raise ValidationError(
                resource_type="credit_cost",
                detail="Credit cost cannot be negative (verify_enough_credits)",
                resource_id=user_uid,
                additional_info={"user_uid": user_uid, "cost": required_credits_for_resource}
            )

        if required_credits_for_resource == 0:
            self.logger.info(f"No credits required for user {user_uid}, bypassing credit verification")
            return True, {"sbscrptn_based_insight_credits": 0, "extra_insight_credits": 0}

        if credits_extracted_from_authz_response is not None:
            self.logger.info("Using credits extracted from authorization response for user %s", user_uid)
            subscription_credits = credits_extracted_from_authz_response.get("sbscrptn_based_insight_credits", 0)
            extra_credits = credits_extracted_from_authz_response.get("extra_insight_credits", 0)
            total_credits = subscription_credits + extra_credits

            self.logger.info(
                "User %s has %s total extracted credits (subscription: %s, extra: %s)",
                user_uid, total_credits, subscription_credits, extra_credits
            )

            user_credits = {
                "sbscrptn_based_insight_credits": subscription_credits,
                "extra_insight_credits": extra_credits
            }

            has_enough_credits = total_credits >= required_credits_for_resource
            return has_enough_credits, user_credits

        try:
            self.logger.info(
                "Fetching user status from Firestore for user %s (collection: %s)",
                user_uid, self.users_status_collection_name
            )
            user_status = await self.userstatus_ops.get_userstatus(user_uid, convert_to_model=True)
            if not user_status:
                raise ValidationError(
                    resource_type="user_credit_verification",
                    detail="User status not found for user %s" % user_uid,
                    resource_id=user_uid,
                    additional_info={"user_uid": user_uid}
                )

            # user_status is a UserStatus model
            subscription_credits = user_status.sbscrptn_based_insight_credits or 0
            extra_credits = user_status.extra_insight_credits or 0
            total_credits = subscription_credits + extra_credits

            self.logger.info(
                "User %s has %s total credits from Firestore (subscription: %s, extra: %s)",
                user_uid, total_credits, subscription_credits, extra_credits
            )

            has_enough_credits = total_credits >= required_credits_for_resource

            user_credits = {
                "sbscrptn_based_insight_credits": subscription_credits,
                "extra_insight_credits": extra_credits
            }

            return has_enough_credits, user_credits

        except Exception as e:
            self.logger.error(f"Error verifying credits for user {user_uid}: {str(e)}", exc_info=True)
            raise ValidationError(
                resource_type="user_credit_verification",
                detail=f"Failed to verify credits for user: {str(e)}",
                resource_id=user_uid,
                additional_info={"user_uid": user_uid, "required_credits": required_credits_for_resource}
            ) from e

    async def debit_credits_transaction(
        self,
        user_uid: str,
        credits_to_take: Optional[float],
        operation_details: str
    ) -> Tuple[bool, Optional[Dict[str, float]]]:
        """
        Charge credits from user account using Firestore transaction.

        Args:
            user_uid: User's UID
            credits_to_take: Amount of credits to charge
            operation_details: Description of the operation for logging

        Returns:
            Tuple of (charge_successful: bool, updated_credits: Optional[Dict])

        Raises:
            ValidationError: If charging fails due to validation issues
        """
        if credits_to_take is None:
            raise ValidationError(
                resource_type="credit_cost",
                detail="Credit cost is not configured for this resource (charge_credits)",
                resource_id=None,
                additional_info={"user_uid": user_uid}
            )

        if credits_to_take < 0:
            raise ValidationError(
                resource_type="credit_cost",
                detail="Credit cost cannot be negative (charge_credits)",
                resource_id=user_uid,
                additional_info={"user_uid": user_uid, "cost": credits_to_take}
            )

        if credits_to_take == 0:
            self.logger.info(f"No credits to charge for user {user_uid}, operation: {operation_details}")
            return True, None

        try:
            # Execute transaction with nested transactional function
            @firestore.transactional
            def debit_credits_transaction(transaction_obj):
                """Transactional function to debit (remove) user credits"""
                userstatus_id = f"{self.userstatus_doc_prefix}{user_uid}"
                user_ref = self.db.collection(self.users_status_collection_name).document(userstatus_id)

                user_doc = user_ref.get(transaction=transaction_obj)
                if not user_doc.exists:
                    self.logger.warning(
                        f"Cannot charge credits - user status not found for {user_uid} in {self.users_status_collection_name}"
                    )
                    return False, None

                # Convert to UserStatus object for better handling
                userstatus_data = user_doc.to_dict()
                userstatus = UserStatus(**userstatus_data)

                # Use object properties instead of dict access
                current_subscription_credits = userstatus.sbscrptn_based_insight_credits or 0.0
                current_extra_credits = userstatus.extra_insight_credits or 0.0
                total_available_credits = current_subscription_credits + current_extra_credits

                if total_available_credits < credits_to_take:
                    self.logger.warning(
                        f"Insufficient credits for user {user_uid} during transaction: "
                        f"has {total_available_credits}, needs {credits_to_take}"
                    )
                    return False, {
                        "sbscrptn_based_insight_credits": current_subscription_credits,
                        "extra_insight_credits": current_extra_credits
                    }

                # Calculate deductions (subscription credits first, then extra)
                subscription_credits_deducted = min(current_subscription_credits, credits_to_take)
                remaining_charge = credits_to_take - subscription_credits_deducted
                extra_credits_deducted = min(current_extra_credits, remaining_charge)

                # Safety check
                if (subscription_credits_deducted + extra_credits_deducted) < credits_to_take:
                    self.logger.error(
                        f"Credit calculation error for user {user_uid}. "
                        f"Required: {credits_to_take}, Calculated deduction: {subscription_credits_deducted + extra_credits_deducted}"
                    )
                    return False, {
                        "sbscrptn_based_insight_credits": current_subscription_credits,
                        "extra_insight_credits": current_extra_credits
                    }

                new_subscription_credits = current_subscription_credits - subscription_credits_deducted
                new_extra_credits = current_extra_credits - extra_credits_deducted

                update_data: Dict[str, Any] = {
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "updated_by": "charging_service__debit_credits_transaction"
                }

                if subscription_credits_deducted > 0:
                    update_data["sbscrptn_based_insight_credits"] = firestore.Increment(-subscription_credits_deducted)
                    update_data["sbscrptn_based_insight_credits_updtd_on"] = datetime.now(timezone.utc).isoformat()

                if extra_credits_deducted > 0:
                    update_data["extra_insight_credits"] = firestore.Increment(-extra_credits_deducted)
                    update_data["extra_insight_credits_updtd_on"] = datetime.now(timezone.utc).isoformat()

                transaction_obj.update(user_ref, update_data)

                return True, {
                    "sbscrptn_based_insight_credits": new_subscription_credits,
                    "extra_insight_credits": new_extra_credits
                }

            transaction = self.db.transaction()
            charged, updated_credits = debit_credits_transaction(transaction)

            if charged:
                self.logger.info(
                    f"Successfully charged {credits_to_take} credits for user {user_uid}. "
                    f"Operation: {operation_details}"
                )
            else:
                self.logger.warning(f"Failed to charge credits for user {user_uid}. Operation: {operation_details}")

            return charged, updated_credits

        except Exception as e:
            self.logger.error(f"Error charging credits for user {user_uid}: {str(e)}", exc_info=True)
            raise ValidationError(
                resource_type="user_credit_transaction",
                detail=f"Failed to charge credits for user: {str(e)}",
                resource_id=user_uid,
                additional_info={"user_uid": user_uid, "credits_to_take": credits_to_take}
            ) from e

    async def credit_credits_transaction(
        self,
        user_uid: str,
        extra_credits_to_add: float = 0.0,
        subscription_credits_to_add: float = 0.0,
        reason: str = "",
        updater_uid: str = "system"
    ) -> Tuple[bool, Optional[Dict[str, float]]]:
        """
        Add credits to user account (extra and/or subscription credits).

        Args:
            user_uid: User's UID
            extra_credits_to_add: Amount of extra credits to add (must be non-negative)
            subscription_credits_to_add: Amount of subscription credits to add (must be non-negative)
            reason: Reason for adding credits
            updater_uid: UID of user/system adding credits

        Returns:
            Tuple of (success: bool, updated_credits: Optional[Dict])

        Raises:
            ValidationError: If adding credits fails
        """
        if extra_credits_to_add < 0 or subscription_credits_to_add < 0:
            raise ValidationError(
                resource_type="credit_amount",
                detail="Credit amounts must be non-negative",
                resource_id=user_uid,
                additional_info={
                    "user_uid": user_uid,
                    "extra_credits_to_add": extra_credits_to_add,
                    "subscription_credits_to_add": subscription_credits_to_add
                }
            )

        if extra_credits_to_add == 0 and subscription_credits_to_add == 0:
            raise ValidationError(
                resource_type="credit_amount",
                detail="At least one credit type must have a positive amount",
                resource_id=user_uid,
                additional_info={
                    "user_uid": user_uid,
                    "extra_credits_to_add": extra_credits_to_add,
                    "subscription_credits_to_add": subscription_credits_to_add
                }
            )

        try:
            # Execute transaction with nested transactional function
            @firestore.transactional
            def credit_credits_transaction(transaction_obj):
                """Transactional function to credit (add) extra and/or subscription credits"""
                userstatus_id = f"{self.userstatus_doc_prefix}{user_uid}"
                user_ref = self.db.collection(self.users_status_collection_name).document(userstatus_id)

                user_doc = user_ref.get(transaction=transaction_obj)
                if not user_doc.exists:
                    self.logger.warning(
                        f"Cannot add credits - user status not found for {user_uid} in {self.users_status_collection_name}"
                    )
                    return False, None

                # Convert to UserStatus object for better handling
                userstatus_data = user_doc.to_dict()
                userstatus = UserStatus(**userstatus_data)

                # Use object properties instead of dict access
                current_extra_credits = userstatus.extra_insight_credits or 0.0
                current_subscription_credits = userstatus.sbscrptn_based_insight_credits or 0.0

                new_extra_credits = current_extra_credits + extra_credits_to_add
                new_subscription_credits = current_subscription_credits + subscription_credits_to_add

                update_data = {
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "updated_by": f"charging_service__credit_credits_transaction__{updater_uid}"
                }

                # Add extra credits if specified
                if extra_credits_to_add > 0:
                    update_data["extra_insight_credits"] = firestore.Increment(extra_credits_to_add)
                    update_data["extra_insight_credits_updtd_on"] = datetime.now(timezone.utc).isoformat()

                # Add subscription credits if specified
                if subscription_credits_to_add > 0:
                    update_data["sbscrptn_based_insight_credits"] = firestore.Increment(subscription_credits_to_add)
                    update_data["sbscrptn_based_insight_credits_updtd_on"] = datetime.now(timezone.utc).isoformat()

                transaction_obj.update(user_ref, update_data)

                return True, {
                    "sbscrptn_based_insight_credits": new_subscription_credits,
                    "extra_insight_credits": new_extra_credits
                }

            transaction = self.db.transaction()
            success, updated_credits = credit_credits_transaction(transaction)

            if success:
                credit_details = []
                if extra_credits_to_add > 0:
                    credit_details.append(f"{extra_credits_to_add} extra credits")
                if subscription_credits_to_add > 0:
                    credit_details.append(f"{subscription_credits_to_add} subscription credits")

                self.logger.info(
                    f"Successfully added {' and '.join(credit_details)} for user {user_uid}. "
                    f"Reason: {reason}. Updated by: {updater_uid}"
                )
            else:
                self.logger.warning(
                    f"Failed to add credits for user {user_uid}. "
                    f"Extra: {extra_credits_to_add}, Subscription: {subscription_credits_to_add}. "
                    f"Reason: {reason}"
                )

            return success, updated_credits

        except Exception as e:
            self.logger.error(
                f"Error adding credits for user {user_uid} "
                f"(extra: {extra_credits_to_add}, subscription: {subscription_credits_to_add}): {str(e)}",
                exc_info=True
            )
            raise ValidationError(
                resource_type="user_credit_addition",
                detail=f"Failed to add credits for user: {str(e)}",
                resource_id=user_uid,
                additional_info={
                    "user_uid": user_uid,
                    "extra_credits_to_add": extra_credits_to_add,
                    "subscription_credits_to_add": subscription_credits_to_add,
                    "reason": reason
                }
            ) from e

    # ========================================================================
    # HIGH-LEVEL ORCHESTRATION OPERATIONS (from ChargingProcessor)
    # ========================================================================

    async def process_single_item_charging(
        self,
        user_uid: str,
        item_id: str,
        get_cost_func: Callable[[], Awaitable[Optional[float]]],
        credits_extracted_from_authz_response: Optional[Dict[str, float]] = None,
        operation_description: str = "Resource access"
    ) -> Dict[str, Any]:
        """
        Process credit check and charging for a single item.

        Args:
            user_uid: User's UID
            item_id: ID of the item being accessed
            get_cost_func: Async function that returns the cost for the item
            credits_extracted_from_authz_response: Optional extracted credit information from authorization
            operation_description: Description for the charging operation

        Returns:
            Dict with keys:
            - access_granted: bool
            - charge_successful: bool (only meaningful if access_granted is True)
            - cost: Optional[float]
            - reason: str (explanation if access denied)
            - updated_user_credits: Optional[Dict] (credits after charging, if applicable)
        """
        self.logger.info(f"Processing single item credit check for user {user_uid}, item {item_id}")
        updated_user_credits = None

        try:
            # Get the credit cost for this item
            credit_cost = await get_cost_func()

            # If item is free or cost not configured, allow access immediately
            if credit_cost is None or credit_cost <= 0:
                if credit_cost is None:
                    self.logger.info(f"Item {item_id} has no configured credit cost, treating as free.")

                # For free items, no need to fetch or verify credits
                return {
                    'access_granted': True,
                    'charge_successful': True,  # No charge needed
                    'cost': credit_cost if credit_cost is not None else 0.0,
                    'reason': 'free_item',
                    'updated_user_credits': None  # No credits involved for free items
                }

            # Check for debug mode bypass
            if self.bypass_credit_check:
                self.logger.info("Bypassing credit check for item %s due to debug mode", item_id)
                if credits_extracted_from_authz_response:
                    updated_user_credits = credits_extracted_from_authz_response
                else:
                    try:
                        _, current_user_credits_from_verify = await self.verify_enough_credits(user_uid, 0, None)
                        updated_user_credits = current_user_credits_from_verify
                    except Exception:
                        self.logger.warning("Could not fetch current credits for user %s during debug bypass.", user_uid)
                return {
                    'access_granted': True,
                    'charge_successful': True,
                    'cost': credit_cost,
                    'reason': 'debug_bypass',
                    'updated_user_credits': updated_user_credits
                }

            # Verify user has enough credits
            has_credits, current_user_credits_from_verify = await self.verify_enough_credits(
                user_uid=user_uid,
                required_credits_for_resource=credit_cost,
                credits_extracted_from_authz_response=credits_extracted_from_authz_response
            )
            updated_user_credits = current_user_credits_from_verify

            if not has_credits:
                self.logger.warning(f"User {user_uid} has insufficient credits for item {item_id} (cost: {credit_cost})")
                return {
                    'access_granted': False,
                    'charge_successful': False,
                    'cost': credit_cost,
                    'reason': 'insufficient_credits',
                    'updated_user_credits': updated_user_credits
                }

            # Charge the user
            charged, calculated_updated_credits = await self.debit_credits_transaction(
                user_uid=user_uid,
                credits_to_take=credit_cost,
                operation_details=operation_description
            )

            if calculated_updated_credits is not None:
                updated_user_credits = calculated_updated_credits

            return {
                'access_granted': True,
                'charge_successful': charged,
                'cost': credit_cost,
                'reason': 'charged' if charged else 'charge_failed',
                'updated_user_credits': updated_user_credits
            }

        except ValidationError as ve:
            self.logger.error("Validation error for item %s, user %s: %s", item_id, user_uid, str(ve))
            try:
                _, updated_user_credits = await self.verify_enough_credits(user_uid, 0, credits_extracted_from_authz_response)
            except Exception:
                pass
            ve.additional_info = ve.additional_info or {}
            ve.additional_info['updated_user_credits'] = updated_user_credits
            raise
        except Exception as e:
            self.logger.error("Unexpected error during credit processing for item %s, user %s: %s", item_id, user_uid, str(e), exc_info=True)
            current_user_credits_on_error = None
            try:
                _, current_user_credits_on_error = await self.verify_enough_credits(user_uid, 0, credits_extracted_from_authz_response)
            except Exception:
                pass
            return {
                'access_granted': False,
                'charge_successful': False,
                'cost': None,
                'reason': f'error: {str(e)}',
                'updated_user_credits': current_user_credits_on_error
            }

    async def process_batch_items_charging(
        self,
        user_uid: str,
        items: List[Dict[str, Any]],
        credits_extracted_from_authz_response: Optional[Dict[str, float]] = None,
        operation_description: str = "Batch resource access"
    ) -> Dict[str, Any]:
        """
        Process credit check and charging for a batch of items.

        Args:
            user_uid: User's UID
            items: List of dicts with keys: 'id', 'data', 'get_cost_func'
            credits_extracted_from_authz_response: Optional extracted credit information from authorization
            operation_description: Description for the charging operation

        Returns:
            Dict with keys:
            - accessible_items: List[Dict] (items user can access)
            - charge_successful: bool
            - total_cost: float
            - paid_items_count: int
            - free_items_count: int
            - updated_user_credits: Optional[Dict] (credits after charging, if applicable)
        """
        self.logger.info(f"Processing batch credit check for user {user_uid}, {len(items)} items")
        updated_user_credits = None

        if not items:
            return {
                'accessible_items': [],
                'charge_successful': True,
                'total_cost': 0.0,
                'paid_items_count': 0,
                'free_items_count': 0,
                'updated_user_credits': None
            }

        try:
            # Separate free and paid items
            free_items = []
            paid_items = []
            total_cost = 0.0

            for item in items:
                try:
                    cost = await item['get_cost_func']()
                    if cost is None or cost <= 0:
                        free_items.append(item)
                    else:
                        paid_items.append(item)
                        total_cost += cost
                except Exception as cost_err:
                    self.logger.error(f"Error getting cost for item {item.get('id', 'unknown')}: {cost_err}")
                    free_items.append(item)

            self.logger.info(f"User {user_uid}: {len(free_items)} free items, {len(paid_items)} paid items (total cost: {total_cost})")

            # If no paid items, return all free items
            if not paid_items:
                if credits_extracted_from_authz_response:
                    updated_user_credits = credits_extracted_from_authz_response
                else:
                    try:
                        _, current_user_credits_from_verify = await self.verify_enough_credits(user_uid, 0, None)
                        updated_user_credits = current_user_credits_from_verify
                    except Exception:
                        self.logger.warning("Could not fetch current credits for user %s for free batch.", user_uid)

                return {
                    'accessible_items': free_items,
                    'charge_successful': True,
                    'total_cost': 0.0,
                    'paid_items_count': 0,
                    'free_items_count': len(free_items),
                    'updated_user_credits': updated_user_credits
                }

            # Check for debug mode bypass
            if self.bypass_credit_check:
                self.logger.info("Bypassing credit check for %s paid items due to debug mode", len(paid_items))
                if credits_extracted_from_authz_response:
                    updated_user_credits = credits_extracted_from_authz_response
                else:
                    try:
                        _, current_user_credits_from_verify = await self.verify_enough_credits(user_uid, 0, None)
                        updated_user_credits = current_user_credits_from_verify
                    except Exception:
                        self.logger.warning("Could not fetch current credits for user %s during debug bypass for batch.", user_uid)

                return {
                    'accessible_items': free_items + paid_items,
                    'charge_successful': True,
                    'total_cost': total_cost,
                    'paid_items_count': len(paid_items),
                    'free_items_count': len(free_items),
                    'updated_user_credits': updated_user_credits
                }

            # Verify user has enough credits for total cost
            has_credits, current_user_credits_from_verify = await self.verify_enough_credits(
                user_uid,
                total_cost,
                credits_extracted_from_authz_response=credits_extracted_from_authz_response
            )
            updated_user_credits = current_user_credits_from_verify

            if not has_credits:
                self.logger.warning(f"User {user_uid} has insufficient credits for batch (cost: {total_cost}). Returning free items only.")
                return {
                    'accessible_items': free_items,
                    'charge_successful': False,
                    'total_cost': total_cost,
                    'paid_items_count': len(paid_items),
                    'free_items_count': len(free_items),
                    'updated_user_credits': updated_user_credits
                }

            # Charge the user for all paid items
            charged, calculated_updated_credits = await self.debit_credits_transaction(
                user_uid,
                total_cost,
                f"{operation_description} ({len(paid_items)} items, total cost: {total_cost})"
            )

            if calculated_updated_credits is not None:
                updated_user_credits = calculated_updated_credits

            return {
                'accessible_items': free_items + paid_items,
                'charge_successful': charged,
                'total_cost': total_cost,
                'paid_items_count': len(paid_items),
                'free_items_count': len(free_items),
                'updated_user_credits': updated_user_credits
            }

        except ValidationError as ve:
            self.logger.error("Validation error during batch credit check for user %s: %s", user_uid, str(ve))
            try:
                _, current_user_credits_from_verify = await self.verify_enough_credits(user_uid, 0, credits_extracted_from_authz_response)
                updated_user_credits = current_user_credits_from_verify
            except Exception:
                pass
            ve.additional_info = ve.additional_info or {}
            ve.additional_info['updated_user_credits'] = updated_user_credits
            raise
        except Exception as e:
            self.logger.error("Unexpected error during batch credit check for user %s: %s", user_uid, str(e), exc_info=True)
            current_credits_on_error = None
            try:
                _, current_credits_on_error = await self.verify_enough_credits(user_uid, 0, credits_extracted_from_authz_response)
                updated_user_credits = current_credits_on_error
            except Exception:
                pass
            return {
                'accessible_items': [],  # Safe default - no items accessible on error
                'charge_successful': False,
                'total_cost': 0.0,  # Safe default
                'paid_items_count': 0,  # Safe default
                'free_items_count': 0,  # Safe default
                'updated_user_credits': updated_user_credits
            }
