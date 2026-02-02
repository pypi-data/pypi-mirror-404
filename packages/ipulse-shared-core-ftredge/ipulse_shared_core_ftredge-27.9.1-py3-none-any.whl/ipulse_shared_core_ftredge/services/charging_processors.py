"""Reusable credit checking and charging utilities for services."""
import os
from typing import Dict, Any, List, Optional, Callable, Awaitable, TypeVar
from ipulse_shared_core_ftredge.services.user_charging_service import UserChargingService, ValidationError
import logging

T = TypeVar('T')

class ChargingProcessor:
    """Handles credit checking and charging for both single item and batch access."""

    def __init__(self, user_charging_service: UserChargingService, logger: logging.Logger):
        self.user_charging_service = user_charging_service
        self.logger = logger

    async def process_single_item_charging(
        self,
        user_uid: str,
        item_id: str,
        get_cost_func: Callable[[], Awaitable[Optional[float]]],
        pre_fetched_credits: Optional[Dict[str, float]] = None,
        operation_description: str = "Resource access"
    ) -> Dict[str, Any]:
        """
        Process credit check and charging for a single item.

        Args:
            user_uid: User's UID
            item_id: ID of the item being accessed
            get_cost_func: Async function that returns the cost for the item
            pre_fetched_credits: Optional pre-fetched credit information
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
        updated_user_credits = None # Initialize

        try:
            # Get the credit cost for this item
            credit_cost = await get_cost_func()

            # If item is free or cost not configured, allow access
            if credit_cost is None or credit_cost <= 0:
                if credit_cost is None:
                    self.logger.info(f"Item {item_id} has no configured credit cost, treating as free.")

                # For free items, provide current credits if available
                if pre_fetched_credits:
                    updated_user_credits = pre_fetched_credits
                elif self.user_charging_service: # Attempt to get current credits if not pre-fetched
                    try:
                        _, current_user_credits_from_verify = await self.user_charging_service.verify_enough_credits(user_uid=user_uid, required_credits_for_resource=0, pre_fetched_user_credits=None)
                        updated_user_credits = current_user_credits_from_verify
                    except Exception: # pylint: disable=broad-except
                        self.logger.warning(f"Could not fetch current credits for user {user_uid} for free item.")

                return {
                    'access_granted': True,
                    'charge_successful': True,  # No charge needed
                    'cost': credit_cost if credit_cost is not None else 0.0,
                    'reason': 'free_item',
                    'updated_user_credits': updated_user_credits
                }

            # Check for debug mode bypass
            if os.getenv("BYPASS_CREDIT_CHECK", "").lower() == "true":
                self.logger.info(f"Bypassing credit check for item {item_id} due to debug mode")
                # Similar to free items, provide current credits if available
                if pre_fetched_credits:
                    updated_user_credits = pre_fetched_credits
                elif self.user_charging_service:
                    try:
                        _, current_user_credits_from_verify = await self.user_charging_service.verify_enough_credits(user_uid=user_uid, required_credits_for_resource=0, pre_fetched_user_credits=None)
                        updated_user_credits = current_user_credits_from_verify
                    except Exception: # pylint: disable=broad-except
                        self.logger.warning(f"Could not fetch current credits for user {user_uid} during debug bypass.")
                return {
                    'access_granted': True,
                    'charge_successful': True,
                    'cost': credit_cost,
                    'reason': 'debug_bypass',
                    'updated_user_credits': updated_user_credits
                }

            # Verify credit service is available
            if not self.user_charging_service:
                self.logger.error("UserChargingService not initialized.")
                return {
                    'access_granted': False,
                    'charge_successful': False,
                    'cost': credit_cost,
                    'reason': 'service_unavailable',
                    'updated_user_credits': None
                }

            # Verify user has enough credits
            has_credits, current_user_credits_from_verify = await self.user_charging_service.verify_enough_credits(
                user_uid,
                credit_cost,
                pre_fetched_user_credits=pre_fetched_credits
            )
            # Store current credits from verification, might be used if charge fails
            updated_user_credits = current_user_credits_from_verify


            if not has_credits:
                self.logger.warning(f"User {user_uid} has insufficient credits for item {item_id} (cost: {credit_cost})")
                return {
                    'access_granted': False,
                    'charge_successful': False,
                    'cost': credit_cost,
                    'reason': 'insufficient_credits',
                    'updated_user_credits': updated_user_credits # Return credits state at time of failure
                }

            # Charge the user - this now returns (bool, Optional[Dict])
            charged, calculated_updated_credits = await self.user_charging_service.debit_credits_transaction(
                user_uid,
                credit_cost,
                operation_description
            )

            # Use the credits returned by charge_credits if successful
            if calculated_updated_credits is not None:
                updated_user_credits = calculated_updated_credits


            return {
                'access_granted': True, # Access granted because verify_enough_credits passed
                'charge_successful': charged,
                'cost': credit_cost,
                'reason': 'charged' if charged else 'charge_failed',
                'updated_user_credits': updated_user_credits
            }

        except ValidationError as ve:
            self.logger.error(f"Validation error for item {item_id}, user {user_uid}: {str(ve)}")
            # Try to get current credits to return
            if self.user_charging_service:
                try:
                    _, updated_user_credits = await self.user_charging_service.verify_enough_credits(user_uid, 0, pre_fetched_credits)
                except Exception: # pylint: disable=broad-except
                    pass # Keep updated_user_credits as None
            ve.additional_info = ve.additional_info or {}
            ve.additional_info['updated_user_credits'] = updated_user_credits
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during credit processing for item {item_id}, user {user_uid}: {str(e)}", exc_info=True)
            # Try to get current credits to return
            current_user_credits_on_error = None
            if self.user_charging_service:
                try:
                    _, current_user_credits_on_error = await self.user_charging_service.verify_enough_credits(user_uid, 0, pre_fetched_credits)
                except Exception: # pylint: disable=broad-except
                    pass
            return {
                'access_granted': False,
                'charge_successful': False,
                'cost': None, # Cost might not be determined if error was early
                'reason': f'error: {str(e)}',
                'updated_user_credits': current_user_credits_on_error
            }
    async def process_batch_items_charging(
        self,
        user_uid: str,
        items: List[Dict[str, Any]],
        pre_fetched_credits: Optional[Dict[str, float]] = None,
        operation_description: str = "Batch resource access"
    ) -> Dict[str, Any]:
        """
        Process credit check and charging for a batch of items.

        Args:
            user_uid: User's UID
            items: List of dicts with keys: 'id', 'data', 'get_cost_func'
            pre_fetched_credits: Optional pre-fetched credit information
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
        updated_user_credits = None # Initialize

        if not items:
            return {
                'accessible_items': [],
                'charge_successful': True,
                'total_cost': 0.0,
                'paid_items_count': 0,
                'free_items_count': 0,
                'updated_user_credits': None
            }

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
            if pre_fetched_credits:
                updated_user_credits = pre_fetched_credits
            elif self.user_charging_service:
                try:
                    _, current_user_credits_from_verify = await self.user_charging_service.verify_enough_credits(user_uid, 0, None)
                    updated_user_credits = current_user_credits_from_verify

                except Exception: # pylint: disable=broad-except
                    self.logger.warning(f"Could not fetch current credits for user {user_uid} for free batch.")

            return {
                'accessible_items': free_items,
                'charge_successful': True,
                'total_cost': 0.0,
                'paid_items_count': 0,
                'free_items_count': len(free_items),
                'updated_user_credits': updated_user_credits
            }

        # Check for debug mode bypass
        if os.getenv("BYPASS_CREDIT_CHECK", "").lower() == "true":
            self.logger.info(f"Bypassing credit check for {len(paid_items)} paid items due to debug mode")
            if pre_fetched_credits:
                updated_user_credits = pre_fetched_credits
            elif self.user_charging_service:
                try:
                    _, current_user_credits_from_verify = await self.user_charging_service.verify_enough_credits(user_uid, 0, None)
                    updated_user_credits = current_user_credits_from_verify
                except Exception: # pylint: disable=broad-except
                    self.logger.warning(f"Could not fetch current credits for user {user_uid} during debug bypass for batch.")

            return {
                'accessible_items': free_items + paid_items,
                'charge_successful': True,
                'total_cost': total_cost,
                'paid_items_count': len(paid_items),
                'free_items_count': len(free_items),
                'updated_user_credits': updated_user_credits
            }

        # Verify credit service is available
        if not self.user_charging_service:
            self.logger.error("UserChargingService not initialized for batch processing.")
            return {
                'accessible_items': free_items,
                'charge_successful': False,
                'total_cost': total_cost,
                'paid_items_count': len(paid_items),
                'free_items_count': len(free_items),
                'updated_user_credits': None
            }

        try:
            # Verify user has enough credits for total cost
            has_credits, current_user_credits_from_verify = await self.user_charging_service.verify_enough_credits(
                user_uid,
                total_cost,
                pre_fetched_user_credits=pre_fetched_credits
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
                    'updated_user_credits': updated_user_credits # Return credits state at time of failure
                }

            # Charge the user for all paid items
            charged, calculated_updated_credits = await self.user_charging_service.debit_credits_transaction(
                user_uid,
                total_cost,
                f"{operation_description} ({len(paid_items)} items, total cost: {total_cost})"
            )

            if calculated_updated_credits is not None:
                updated_user_credits = calculated_updated_credits


            # Return all items (free + paid) since credits were verified (even if charge failed post-verification)
            return {
                'accessible_items': free_items + paid_items,
                'charge_successful': charged,
                'total_cost': total_cost,
                'paid_items_count': len(paid_items),
                'free_items_count': len(free_items),
                'updated_user_credits': updated_user_credits
            }

        except ValidationError as ve:
            self.logger.error(f"Validation error during batch credit check for user {user_uid}: {str(ve)}")
            if self.user_charging_service:
                try:
                    _, current_user_credits_from_verify = await self.user_charging_service.verify_enough_credits(user_uid, 0, pre_fetched_credits)
                    updated_user_credits = current_user_credits_from_verify
                except Exception: # pylint: disable=broad-except
                    pass
            ve.additional_info = ve.additional_info or {}
            ve.additional_info['updated_user_credits'] = updated_user_credits
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during batch credit check for user {user_uid}: {str(e)}", exc_info=True)
            current_credits_on_error = None
            if self.user_charging_service:
                try:
                    _, current_credits_on_error = await self.user_charging_service.verify_enough_credits(user_uid, 0, pre_fetched_credits)
                    updated_user_credits = current_credits_on_error
                except Exception: # pylint: disable=broad-except
                    pass
            return {
                'accessible_items': free_items, # Only free items if error
                'charge_successful': False,
                'total_cost': total_cost, # This is the cost of paid items that were attempted
                'paid_items_count': len(paid_items),
                'free_items_count': len(free_items),
                'updated_user_credits': updated_user_credits
            }
