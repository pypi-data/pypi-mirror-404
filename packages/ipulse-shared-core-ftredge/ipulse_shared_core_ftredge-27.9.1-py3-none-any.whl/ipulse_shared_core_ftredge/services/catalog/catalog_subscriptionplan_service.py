"""
Subscription Plan Catalog Service

This service manages subscription plan templates stored in Firestore.
These templates are used to configure and create user subscriptions consistently.
"""

import logging
from typing import Dict, List, Optional, Any
from google.cloud import firestore
from google.cloud.firestore import Client
from ipulse_shared_base_ftredge import SubscriptionPlanName
from ipulse_shared_base_ftredge.enums.enums_status import ObjectOverallStatus
from ipulse_shared_core_ftredge.models.catalog.subscriptionplan import SubscriptionPlan
from ipulse_shared_core_ftredge.services.base.base_firestore_service import BaseFirestoreService
from ipulse_shared_core_ftredge.exceptions import ServiceError


class CatalogSubscriptionPlanService(BaseFirestoreService[SubscriptionPlan]):
    """
    Service for managing subscription plan catalog configurations.

    This service provides CRUD operations for subscription plan templates that define
    the structure and defaults for user subscriptions.
    """

    def __init__(
        self,
        firestore_client: Client,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the Subscription Plan Catalog Service.

        Args:
            firestore_client: Firestore client instance
            logger: Logger instance (optional)
        """
        super().__init__(
            db=firestore_client,
            collection_name="papp_core_catalog_subscriptionplans",
            resource_type="subscriptionplan",
            model_class=SubscriptionPlan,
            logger=logger or logging.getLogger(__name__)
        )
        self.archive_collection_name = "~archive_papp_core_catalog_subscriptionplans"

    async def create_subscriptionplan(
        self,
        subscriptionplan_id: str,
        subscription_plan: SubscriptionPlan,
        creator_uid: str
    ) -> SubscriptionPlan:
        """
        Create a new subscription plan.

        Args:
            subscriptionplan_id: Unique identifier for the plan
            subscription_plan: Subscription plan data
            creator_uid: UID of the user creating the plan

        Returns:
            Created subscription plan

        Raises:
            ServiceError: If creation fails
            ValidationError: If plan data is invalid
        """
        self.logger.info(f"Creating subscription plan: {subscriptionplan_id}")

        # Create the document
        created_doc = await self.create_document(
            doc_id=subscriptionplan_id,
            data=subscription_plan,
            creator_uid=creator_uid
        )

        # Convert back to model
        result = SubscriptionPlan.model_validate(created_doc)
        self.logger.info(f"Successfully created subscription plan: {subscriptionplan_id}")
        return result

    async def get_subscriptionplan(self, subscriptionplan_id: str) -> Optional[SubscriptionPlan]:
        """
        Retrieve a subscription plan by ID.

        Args:
            subscriptionplan_id: Unique identifier for the plan

        Returns:
            Subscription plan if found, None otherwise

        Raises:
            ServiceError: If retrieval fails
        """
        self.logger.debug(f"Retrieving subscription plan: {subscriptionplan_id}")
        doc_data = await self.get_document(subscriptionplan_id)
        if doc_data is None:
            return None
        return SubscriptionPlan.model_validate(doc_data) if isinstance(doc_data, dict) else doc_data

    async def update_subscriptionplan(
        self,
        subscriptionplan_id: str,
        updates: Dict[str, Any],
        updater_uid: str
    ) -> SubscriptionPlan:
        """
        Update a subscription plan.

        Args:
            subscriptionplan_id: Unique identifier for the plan
            updates: Fields to update
            updater_uid: UID of the user updating the plan

        Returns:
            Updated subscription plan

        Raises:
            ServiceError: If update fails
            ResourceNotFoundError: If plan not found
            ValidationError: If update data is invalid
        """
        self.logger.info(f"Updating subscription plan: {subscriptionplan_id}")

        updated_doc = await self.update_document(
            doc_id=subscriptionplan_id,
            update_data=updates,
            updater_uid=updater_uid
        )

        result = SubscriptionPlan.model_validate(updated_doc)
        self.logger.info(f"Successfully updated subscription plan: {subscriptionplan_id}")
        return result

    async def delete_subscriptionplan(
        self,
        subscriptionplan_id: str,
        archive: bool = True
    ) -> bool:
        """
        Delete a subscription plan.

        Args:
            subscriptionplan_id: Unique identifier for the plan
            archive: Whether to archive the plan before deletion

        Returns:
            True if deletion was successful

        Raises:
            ServiceError: If deletion fails
            ResourceNotFoundError: If plan not found
        """
        self.logger.info(f"Deleting subscription plan: {subscriptionplan_id}")

        if archive:
            # Get the plan data before deletion for archiving
            template = await self.get_subscriptionplan(subscriptionplan_id)
            if template:
                await self.archive_document(
                    document_data=template.model_dump(),
                    doc_id=subscriptionplan_id,
                    archive_collection=self.archive_collection_name,
                    archived_by="system"
                )

        result = await self.delete_document(subscriptionplan_id)
        self.logger.info(f"Successfully deleted subscription plan: {subscriptionplan_id}")
        return result

    async def list_subscriptionplans(
        self,
        plan_name: Optional[SubscriptionPlanName] = None,
        pulse_status: Optional[ObjectOverallStatus] = None,
        latest_version_only: bool = False,
        limit: Optional[int] = None,
        version_ordering: str = "DESCENDING"
    ) -> List[SubscriptionPlan]:
        """
        List subscription plans with optional filtering.

        Args:
            plan_name: Filter by specific plan name (FREE, BASE, PREMIUM)
            pulse_status: Filter by specific pulse status
            latest_version_only: Only return the latest version per plan
            limit: Maximum number of plans to return
            version_ordering: Order direction for version ('ASCENDING' or 'DESCENDING')

        Returns:
            List of subscription plans

        Raises:
            ServiceError: If listing fails
        """
        self.logger.debug(f"Listing subscription plans - plan_name: {plan_name}, pulse_status: {pulse_status}, latest_version_only: {latest_version_only}, version_ordering: {version_ordering}")

        # Build query filters
        filters = []
        if plan_name:
            filters.append(("plan_name", "==", plan_name.value))
        if pulse_status:
            filters.append(("pulse_status", "==", pulse_status.value))

        # Set ordering
        order_by = "plan_version"
        order_direction = firestore.Query.DESCENDING if version_ordering == "DESCENDING" else firestore.Query.ASCENDING

        # Optimize query if only the latest version of a specific plan is needed
        query_limit = limit
        if latest_version_only and plan_name:
            query_limit = 1
            # Ensure descending order to get the latest
            order_direction = firestore.Query.DESCENDING

        docs = await self.list_documents(
            filters=filters,
            order_by=order_by,
            order_direction=order_direction,
            limit=query_limit
        )

        # Convert to SubscriptionPlan models
        plans = [SubscriptionPlan.model_validate(doc) for doc in docs]

        # If we need the latest of all plans, we fetch all sorted by version
        # and then pick the first one for each plan_name in Python.
        if latest_version_only and not plan_name:
            # This assumes the list is sorted by version descending.
            if order_direction != firestore.Query.DESCENDING:
                self.logger.warning("latest_version_only is True but version_ordering is not DESCENDING. Results may not be the latest.")

            plan_groups = {}
            for plan in plans:
                key = plan.plan_name.value
                if key not in plan_groups:
                    plan_groups[key] = plan  # First one is the latest due to sorting

            return list(plan_groups.values())

        return plans


    def _get_collection(self):
        """Get the Firestore collection reference."""
        return self.db.collection(self.collection_name)

    async def subscriptionplan_exists(self, subscriptionplan_id: str) -> bool:
        """
        Check if a subscription plan exists.

        Args:
            subscriptionplan_id: Unique identifier for the plan

        Returns:
            True if plan exists, False otherwise

        Raises:
            ServiceError: If check fails
        """
        return await self.document_exists(subscriptionplan_id)

    async def validate_subscriptionplan_data(self, subscriptionplan_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate subscription plan data.

        Args:
            subscriptionplan_data: Plan data to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            SubscriptionPlan.model_validate(subscriptionplan_data)
            return True, []
        except Exception as e:
            return False, [str(e)]
