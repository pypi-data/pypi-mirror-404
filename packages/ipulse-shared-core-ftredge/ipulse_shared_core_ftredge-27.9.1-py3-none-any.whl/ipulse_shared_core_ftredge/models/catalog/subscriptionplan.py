"""
Subscription Plan Defaults Model

This module defines the configuration templates for subscription plans that are stored in Firestore.
These templates are used to create actual user subscriptions with consistent settings.
"""

from typing import Dict, Any, Optional, ClassVar, List
from enum import StrEnum
from datetime import datetime, timezone, timedelta
from pydantic import Field, ConfigDict, field_validator,model_validator, BaseModel
from ipulse_shared_base_ftredge import (Layer, Module, list_enums_as_lower_strings,
                                        SystemSubject, SubscriptionPlanName,ObjectOverallStatus,
                                        SubscriptionStatus, TimeUnit)
from ..base_nosql_model import BaseNoSQLModel
from ..user.user_permissions import UserPermission


class ProrationMethod(StrEnum):
    """Methods for handling proration when upgrading plans."""
    IMMEDIATE = "immediate"
    PRORATED = "prorated"
    END_OF_CYCLE = "end_of_cycle"


class Proration(BaseModel):
    """Defines the proration behavior for subscription changes."""
    pro_rata_billing: bool = Field(
        default=True,
        description="If true, charge a pro-rated amount for the remaining time in the current billing cycle."
    )
    proration_date: Optional[int] = Field(
        default=None,
        description="The specific date to use for proration calculations, if applicable."
    )


class PlanUpgradePath(BaseModel):
    """Represents an upgrade path from a source plan to the plan where this path is defined."""

    price_usd: float = Field(
        ...,
        ge=0,
        description="Price for upgrading to this plan in USD"
    )

    proration_method: ProrationMethod = Field(
        ...,
        description="How to handle proration when upgrading"
    )


############################################ !!!!! ALWAYS UPDATE SCHEMA VERSION IF SCHEMA IS BEING MODIFIED !!! ############################################
class SubscriptionPlan(BaseNoSQLModel):
    """
    Configuration template for subscription plans stored in Firestore.
    These templates define the default settings applied when creating user subscriptions.
    """

    model_config = ConfigDict(extra="forbid")
    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = ""
    VERSION: ClassVar[int] = 2
    DOMAIN: ClassVar[str] = "_".join(list_enums_as_lower_strings(Layer.PULSE_APP, Module.CORE, SystemSubject.CATALOG))
    OBJ_REF: ClassVar[str] = "subscriptionplan"

    id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this plan template (e.g., 'free_subscription_1'). Auto-generated if not provided.",
        frozen=True
    )

    plan_name: SubscriptionPlanName = Field(
        ...,
        description="Subscription plan type (FREE, BASE, PREMIUM)",
        frozen=True
    )

    plan_version: int = Field(
        ...,
        ge=1,
        description="Version of this plan template",
        frozen=True
    )

    pulse_status: ObjectOverallStatus = Field(
        default=ObjectOverallStatus.ACTIVE,
        description="Overall status of this subscription plan configuration"
    )

    # Display information
    display_name: str = Field(
        ...,
        min_length=1,
        description="Human-readable plan name",
        frozen=True
    )

    description: str = Field(
        ...,
        min_length=1,
        description="Description of what this plan includes",
        frozen=True
    )

    granted_iam_permissions: List[UserPermission] = Field(
        default_factory=list,
        description="List of all IAM permission granted by this plan",
        frozen=True
    )

    # Credit configuration
    subscription_based_insight_credits_per_update: int = Field(
        ...,
        ge=0,
        description="Number of insight credits added per update cycle",
        frozen=True
    )

    subscription_based_insight_credits_update_freq_h: int = Field(
        ...,
        gt=0,
        description="How often insight credits are updated (in hours)",
        frozen=True
    )

    extra_insight_credits_per_cycle: int = Field(
        ...,
        ge=0,
        description="Bonus insight credits granted per subscription cycle",
        frozen=True
    )

    voting_credits_per_update: int = Field(
        ...,
        ge=0,
        description="Number of voting credits added per update cycle",
        frozen=True
    )

    voting_credits_update_freq_h: int = Field(
        ...,
        gt=0,
        description="How often voting credits are updated (in hours)",
        frozen=True
    )

    # Plan cycle configuration
    plan_validity_cycle_length: int = Field(
        ...,
        gt=0,
        description="Length of each subscription cycle (e.g., 1, 3, 12)",
        frozen=True
    )

    plan_validity_cycle_unit: TimeUnit = Field(
        ...,
        description="Unit for the cycle length (month, year, etc.)",
        frozen=True
    )

    # Pricing
    plan_per_cycle_price_usd: float = Field(
        ...,
        ge=0,
        description="Price per subscription cycle in USD",
        frozen=True
    )

    # Features and customization
    plan_extra_features: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional features enabled by this plan",
        frozen=True
    )

    # Upgrade paths
    plan_upgrade_paths: Dict[str, PlanUpgradePath] = Field(
        default_factory=dict,
        description="Defines valid upgrade paths TO this plan FROM other plans (source_plan_id -> upgrade_details)",
        frozen=True
    )

    # Default settings
    plan_default_auto_renewal_end: Optional[datetime] = Field(
        default=None,
        description="Default auto-renewal setting for new subscriptions",
        frozen=True
    )

    plan_default_status: SubscriptionStatus = Field(
        ...,
        description="Default status for new subscriptions with this plan",
        frozen=True
    )

    # Fallback configuration
    fallback_plan_id_if_current_plan_expired: Optional[str] = Field(
        None,
        description="Plan to fall back to when this plan expires (None for no fallback)",
        frozen=True
    )

    @model_validator(mode='before')
    @classmethod
    def set_id_if_not_provided(cls, data: Any) -> Any:
        """Generate an ID from plan_name and plan_version if not provided."""
        if isinstance(data, dict):
            plan_name = data.get('plan_name')
            plan_version = data.get('plan_version')
            provided_id = data.get('id')

            if plan_name and plan_version is not None:
                plan_name_str = str(plan_name)
                expected_id = f"{plan_name_str}_{plan_version}"

                if provided_id is None:
                    # Auto-generate ID
                    data['id'] = expected_id
                else:
                    # Validate provided ID matches expected format
                    if provided_id != expected_id:
                        raise ValueError(
                            f"Invalid ID format. Expected '{expected_id}' based on "
                            f"plan_name='{plan_name_str}' and plan_version={plan_version}, "
                            f"but got '{provided_id}'. ID must follow format: {{plan_name}}_{{plan_version}}"
                        )
        return data


    @field_validator('granted_iam_permissions')
    @classmethod
    def validate_iam_permissions(cls, v: List[UserPermission]) -> List[UserPermission]:
        """Validate IAM permissions structure."""
        if not isinstance(v, list):
            raise ValueError("granted_iam_permissions must be a list")

        for i, permission in enumerate(v):
            if not isinstance(permission, UserPermission):
                raise ValueError(f"Permission at index {i} must be a UserPermission instance")

        return v

    @field_validator('plan_upgrade_paths')
    @classmethod
    def validate_upgrade_paths(cls, v: Dict[str, PlanUpgradePath]) -> Dict[str, PlanUpgradePath]:
        """Validate upgrade paths."""
        for source_plan_id, upgrade_path in v.items():
            if not isinstance(source_plan_id, str) or not source_plan_id.strip():
                raise ValueError(f"Source plan ID must be a non-empty string, got: {source_plan_id}")

            if not isinstance(upgrade_path, PlanUpgradePath):
                raise ValueError(f"Upgrade path for '{source_plan_id}' must be a PlanUpgradePath instance")

        return v

    def get_cycle_duration_hours(self) -> int:
        """Calculate the total duration of one cycle in hours."""
        unit_to_hours = {
            TimeUnit.MINUTE: 1/60,
            TimeUnit.HOUR: 1,
            TimeUnit.DAY: 24,
            TimeUnit.WEEK: 24 * 7,
            TimeUnit.MONTH: 24 * 30,  # Approximate
            TimeUnit.YEAR: 24 * 365,  # Approximate
        }
        multiplier = unit_to_hours.get(self.plan_validity_cycle_unit, 24 * 30)
        return int(self.plan_validity_cycle_length * multiplier)