""" User Status model for tracking user subscription and access rights. """
from datetime import datetime, timezone, timedelta
from typing import Set, Optional, Dict, List, ClassVar, Any
from pydantic import Field, ConfigDict, model_validator, field_validator
from ipulse_shared_base_ftredge import Layer, Module, list_enums_as_lower_strings, SystemSubject, TimeUnit
from ipulse_shared_base_ftredge.enums.enums_iam import IAMUnit
from .user_subscription import UserSubscription
from ..base_nosql_model import BaseNoSQLModel
from .user_permissions import UserPermission



############################ !!!!! ALWAYS UPDATE SCHEMA VERSION , IF SCHEMA IS BEING MODIFIED !!! #################################
class UserStatus(BaseNoSQLModel):
    """
    User Status model for tracking user subscription and access rights.
    """
    # Set frozen=False to allow modification of attributes
    model_config = ConfigDict(frozen=False, extra="forbid")

    # Class constants
    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = ""
    VERSION: ClassVar[int] = 7  # Major version bump for flattened IAM permissions structure
    DOMAIN: ClassVar[str] = "_".join(list_enums_as_lower_strings(Layer.PULSE_APP, Module.CORE, SystemSubject.USER))
    OBJ_REF: ClassVar[str] = "userstatus"
    COLLECTION_NAME: ClassVar[str] = "papp_core_user_userstatuss"


    id: Optional[str] = Field(
        default=None,  # Will be auto-generated from user_uid if not provided
        description=f"User ID, format: {OBJ_REF}_user_uid"
    )

    user_uid: str = Field(
        ...,
        min_length=1,
        description="User UID from Firebase Auth",
        frozen=True
    )

    # Added organizations field for consistency with UserProfile
    organizations_uids: Set[str] = Field(
        default_factory=set,
        description="Organization UIDs the user belongs to"
    )

    # Simplified IAM permissions structure - flattened for easier management
    iam_permissions: List[UserPermission] = Field(
        default_factory=list,
        description="List of all IAM permission assignments for this user"
    )

    # Changed from dictionary to single Optional subscription
    active_subscription: Optional[UserSubscription] = Field(
        default=None,
        description="The user's currently active subscription, if any"
    )

    # Credit management fields
    sbscrptn_based_insight_credits: Optional[int] = Field(
        default=0,
        ge=0,  # Must be >= 0
        description="Subscription-based insight credits (expire with subscription)"
    )

    sbscrptn_based_insight_credits_updtd_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp for subscription credits"
    )

    extra_insight_credits: Optional[int] = Field(
        default=0,
        ge=0,  # Must be >= 0
        description="Additional purchased insight credits (non-expiring)"
    )

    extra_insight_credits_updtd_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp for extra credits"
    )

    voting_credits: Optional[int] = Field(
        default=0,
        ge=0,  # Must be >= 0
        description="Voting credits for user"
    )

    voting_credits_updtd_on: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp for voting credits"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the user status"
    )

    @field_validator('user_uid')
    @classmethod
    def validate_user_uid(cls, v: str) -> str:
        """Validate that user_uid is not empty string."""
        if not v or not v.strip():
            raise ValueError("user_uid cannot be empty or whitespace-only")
        return v.strip()

    @model_validator(mode='before')
    @classmethod
    def ensure_id_exists(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensures the id field exists and matches expected format, or generates it from user_uid.
        This runs BEFORE validation, guaranteeing id will be present for validators.
        """
        if not isinstance(data, dict):
            return data

        user_uid = data.get('user_uid')
        if not user_uid:
            return data  # Let field validation handle missing user_uid

        expected_id = f"{cls.OBJ_REF}_{user_uid}"

        # If id is already provided, validate it matches expected format
        if data.get('id'):
            if data['id'] != expected_id:
                raise ValueError(f"Invalid id format. Expected '{expected_id}', got '{data['id']}'")
            return data

        # If id is not provided, generate it from user_uid
        data['id'] = expected_id
        return data


    ########################################################################
    ############ ######### IAM Permission Management ######### #############
    ########################################################################

    def get_valid_permissions(
        self,
        domain: Optional[str] = None,
        iam_unit_type: Optional[IAMUnit] = None,
        permission_ref: Optional[str] = None
    ) -> List[UserPermission]:
        """
        Get all valid (non-expired) permissions, optionally filtered.

        Args:
            domain: Filter by domain (e.g., 'papp')
            iam_unit_type: Filter by IAM unit type (GROUP, ROLE, etc.)
            permission_ref: Filter by permission reference name

        Returns:
            List of valid permissions matching the filters
        """
        valid_permissions = [perm for perm in self.iam_permissions if perm.is_valid()]

        if domain is not None:
            valid_permissions = [perm for perm in valid_permissions if perm.domain == domain]

        if iam_unit_type is not None:
            valid_permissions = [perm for perm in valid_permissions if perm.iam_unit_type == iam_unit_type]

        if permission_ref is not None:
            valid_permissions = [perm for perm in valid_permissions if perm.permission_ref == permission_ref]

        return valid_permissions

    def add_permission(self, permission: UserPermission) -> None:
        """
        Add a single permission assignment.

        Args:
            permission: UserPermission object to add
        """
        self.iam_permissions.append(permission)

    def add_permission_from_fields(
        self,
        domain: str,
        iam_unit_type: IAMUnit,
        permission_ref: str,
        source: str,
        expires_at: datetime,
        granted_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a permission assignment using individual fields (convenience method).

        Args:
            domain: The domain for the permission (e.g., 'papp')
            iam_unit_type: Type of IAM assignment (GROUP, ROLE, etc.)
            permission_ref: The name/identifier of the permission to add
            source: Source identifier for this assignment (e.g., subscription ID)
            expires_at: Expiration date (mandatory - no permanent permissions)
            granted_by: Who granted this permission
            metadata: Optional metadata for the assignment
        """
        permission = UserPermission(
            domain=domain,
            iam_unit_type=iam_unit_type,
            permission_ref=permission_ref,
            source=source,
            expires_at=expires_at,
            granted_by=granted_by,
            metadata=metadata or {}
        )
        self.add_permission(permission)

    def remove_permission(
        self,
        domain: Optional[str] = None,
        iam_unit_type: Optional[IAMUnit] = None,
        permission_ref: Optional[str] = None,
        source: Optional[str] = None
    ) -> int:
        """
        Remove permission assignments matching the criteria.
        At least one filter criteria must be provided.

        Args:
            domain: Optional domain filter (e.g., 'papp')
            iam_unit_type: Optional IAM assignment type filter (GROUP, ROLE, etc.)
            permission_ref: Optional permission name/identifier filter
            source: Optional source filter

        Returns:
            Number of permissions removed

        Raises:
            ValueError: If no filter criteria are provided
        """
        if not any([domain, iam_unit_type, permission_ref, source]):
            raise ValueError("At least one filter criteria must be provided")

        initial_count = len(self.iam_permissions)

        def matches_criteria(perm: UserPermission) -> bool:
            """Check if permission matches the removal criteria"""
            if domain is not None and perm.domain != domain:
                return False
            if iam_unit_type is not None and perm.iam_unit_type != iam_unit_type:
                return False
            if permission_ref is not None and perm.permission_ref != permission_ref:
                return False
            if source is not None and perm.source != source:
                return False
            return True

        self.iam_permissions = [perm for perm in self.iam_permissions if not matches_criteria(perm)]

        return initial_count - len(self.iam_permissions)

    def remove_all_permissions(self, source: Optional[str] = None) -> int:
        """
        Remove all permission assignments, optionally filtered by source.

        Args:
            source: Optional source filter (if None, removes all permissions)

        Returns:
            Number of permissions removed
        """
        initial_count = len(self.iam_permissions)

        if source is None:
            self.iam_permissions = []
        else:
            self.iam_permissions = [perm for perm in self.iam_permissions if perm.source != source]

        return initial_count - len(self.iam_permissions)

    def cleanup_expired_permissions(self, iam_unit_type: Optional[IAMUnit] = None) -> int:
        """
        Remove all expired permission assignments of a specific type or all types.

        Args:
            iam_unit_type: If provided, only remove this type of permissions

        Returns:
            Number of removed permission assignments
        """
        initial_count = len(self.iam_permissions)

        if iam_unit_type is None:
            self.iam_permissions = [perm for perm in self.iam_permissions if perm.is_valid()]
        else:
            self.iam_permissions = [
                perm for perm in self.iam_permissions
                if perm.is_valid() or perm.iam_unit_type != iam_unit_type
            ]

        return initial_count - len(self.iam_permissions)

    ########################################################################
    ############ #########   User Subscription Management  ######### #############
    ########################################################################

    def update_user_permissions_from_subscription(self, subscription: UserSubscription, granted_by: Optional[str] = None) -> int:
        """
        Update user permissions based on a subscription.
        Uses the new flattened permission structure.

        Args:
            subscription: Subscription to apply
            granted_by: Who granted this permission (user ID, system process, etc.)

        Returns:
            Number of permission assignments added
        """
        added_count = 0
        # Use the subscription plan_id as the source (which already contains "subscription" and version)
        source = subscription.plan_id

        # The granted_iam_permissions in Subscription is now List[UserPermission]
        # We add each permission directly with subscription expiration

        for permission in subscription.granted_iam_permissions:
            # Create a new permission with subscription's expiration date and source
            self.add_permission_from_fields(
                domain=permission.domain,
                iam_unit_type=permission.iam_unit_type,
                permission_ref=permission.permission_ref,
                source=source,
                expires_at=subscription.cycle_end_datetime_safe,
                granted_by=granted_by
            )
            added_count += 1

        return added_count

    # Method instead of computed field
    def is_subscription_active(self) -> bool:
        """Check if the user has an active subscription."""
        if self.active_subscription:
            return self.active_subscription.is_active()
        return False


    def apply_subscription(self, subscription: UserSubscription, add_associated_permissions: bool = True, remove_previous_subscription_permissions: bool = True, granted_by: Optional[str] = None) -> int:
        """
        Apply a subscription's benefits to the user status.
        This updates credits, permissions, and sets the active subscription.

        Args:
            subscription: The subscription to apply
            add_associated_permissions: If True, adds IAM permissions from the subscription
            remove_previous_subscription_permissions: If True, removes IAM permissions from any existing subscription
            granted_by: Who granted this permission (user ID, system process, etc.)

        Returns:
            Number of permissions added (0 if add_associated_permissions=False)
        """
        if not subscription:
            return 0

        permissions_added = 0

        # Remove existing subscription permissions if requested
        if remove_previous_subscription_permissions and self.active_subscription:
            # Use the subscription plan_id as the source (which already contains "subscription" and version)
            source = self.active_subscription.plan_id
            removed_permissions = self.remove_all_permissions(source=source)
            if removed_permissions > 0:
                pass  # Note: We don't return this count as it's not part of the "added" permissions

        # Add IAM permissions from subscription if requested
        if add_associated_permissions:
            permissions_added = self.update_user_permissions_from_subscription(subscription, granted_by=granted_by)

        # Update subscription-based credits
        credits_per_update = subscription.subscription_based_insight_credits_per_update
        if credits_per_update > 0:
            self.sbscrptn_based_insight_credits = credits_per_update
            self.sbscrptn_based_insight_credits_updtd_on = datetime.now(timezone.utc)

        # Update voting credits directly from subscription attributes
        voting_credits = subscription.voting_credits_per_update
        if voting_credits > 0:
            self.voting_credits = voting_credits
            self.voting_credits_updtd_on = datetime.now(timezone.utc)

        # Set as active subscription
        self.active_subscription = subscription

        return permissions_added

    def revoke_subscription(self, remove_associated_permissions: bool = True) -> int:
        """
        Revoke the current subscription benefits.
        This clears subscription-based credits and removes the active subscription.
        Optionally also revokes associated IAM permissions.

        Args:
            remove_associated_permissions: If True, removes all IAM permissions
                                         associated with the current subscription

        Returns:
            Number of permissions removed (0 if remove_associated_permissions=False or no subscription)
        """
        if not self.active_subscription:
            return 0

        permissions_removed = 0

        # Revoke associated IAM permissions if requested
        if remove_associated_permissions:
            # Use the subscription plan_id as the source (which already contains "subscription" and version)
            source = self.active_subscription.plan_id
            permissions_removed = self.remove_all_permissions(source=source)

        # Clear subscription-based credits and active subscription
        self.sbscrptn_based_insight_credits = 0
        self.sbscrptn_based_insight_credits_updtd_on = datetime.now(timezone.utc)
        self.active_subscription = None

        return permissions_removed

    ########################################################################
    ############ #########   Credit Management  ######### #############
    ########################################################################

    def should_update_subscription_credits(self) -> bool:
        """
        Check if subscription-based credits should be updated based on the cycle timing.

        Credits should be updated if:
        1. User has an active subscription
        2. The last update was before the current cycle period started

        Returns:
            True if credits should be updated, False otherwise
        """
        if not self.active_subscription or not self.active_subscription.is_active():
            return False

        now = datetime.now(timezone.utc)
        cycle_start = self.active_subscription.cycle_start_datetime
        update_frequency_hours = self.active_subscription.subscription_based_insight_credits_update_freq_h

        # Calculate when the next credit update should happen based on cycle start
        # We need to find the most recent cycle boundary that has passed
        hours_since_cycle_start = (now - cycle_start).total_seconds() / 3600
        completed_periods = int(hours_since_cycle_start // update_frequency_hours)

        if completed_periods == 0:
            # We haven't completed even one period yet
            return False

        # Calculate when the last period should have ended
        last_period_end = cycle_start + timedelta(hours=completed_periods * update_frequency_hours)

        # Check if our last update was before this period ended
        return self.sbscrptn_based_insight_credits_updtd_on < last_period_end

    def update_subscription_credits(self) -> int:
        """
        Update subscription-based credits if needed.

        Returns:
            Amount of credits added (0 if no update needed)
        """
        if not self.should_update_subscription_credits() or not self.active_subscription:
            return 0

        final_credits = self.active_subscription.subscription_based_insight_credits_per_update

        if final_credits > 0:
            self.sbscrptn_based_insight_credits = final_credits
            self.sbscrptn_based_insight_credits_updtd_on = datetime.now(timezone.utc)

        return final_credits