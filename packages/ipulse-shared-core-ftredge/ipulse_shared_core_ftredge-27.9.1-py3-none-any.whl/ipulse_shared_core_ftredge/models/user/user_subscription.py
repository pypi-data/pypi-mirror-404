from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import uuid
from typing import Optional, ClassVar, Dict, Any, List
from pydantic import Field, ConfigDict, model_validator
from ipulse_shared_base_ftredge import Layer, Module, list_enums_as_lower_strings, SystemSubject, SubscriptionPlanName, SubscriptionStatus, TimeUnit
from ..base_nosql_model import BaseNoSQLModel
from .user_permissions import UserPermission
# ORIGINAL AUTHOR ="russlan.ramdowar;russlan@ftredge.com"
# CLASS_ORGIN_DATE=datetime(2024, 2, 12, 20, 5)


DEFAULT_SUBSCRIPTION_PLAN = SubscriptionPlanName.FREE_SUBSCRIPTION
DEFAULT_SUBSCRIPTION_STATUS = SubscriptionStatus.ACTIVE

############################################ !!!!! ALWAYS UPDATE SCHEMA VERSION , IF SCHEMA IS BEING MODIFIED !!! ############################################
class UserSubscription(BaseNoSQLModel):
    """
    Represents a single subscription cycle with enhanced flexibility and tracking.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = ""
    VERSION: ClassVar[int] = 3  # Incremented version for direct fields instead of computed
    DOMAIN: ClassVar[str] = "_".join(list_enums_as_lower_strings(Layer.PULSE_APP, Module.CORE, SystemSubject.SUBSCRIPTION))
    OBJ_REF: ClassVar[str] = "subscription"


    # Unique identifier for this specific subscription instance - now auto-generated
    id: Optional[str] = Field(
        default=None,  # Will be auto-generated using UUID if not provided
        description="Unique identifier for this subscription instance"
    )

    # Plan identification
    plan_name: SubscriptionPlanName = Field(
        ...,  # Required field, no default
        description="Subscription Plan Name"
    )

    plan_version: int = Field(
        ...,  # Required field, no default
        description="Version of the subscription plan"
    )

    # Direct field instead of computed
    plan_id: str = Field(
        ...,  # Required field, no default
        description="Combined plan identifier (plan_name_plan_version)"
    )

    # Cycle duration fields
    cycle_start_datetime: datetime = Field(
        ...,  # Required field, no default
        description="Subscription Cycle Start Date"
    )

    # Direct field instead of computed - will be auto-calculated
    cycle_end_datetime: Optional[datetime] = Field(
        default=None,  # Optional during creation, auto-calculated by validator
        description="Subscription Cycle End Date (auto-calculated if not provided during creation)"
    )

    # Fields for cycle calculation
    validity_time_length: int = Field(
        ...,  # Required field, no default
        description="Length of subscription validity period (e.g., 1, 3, 12)"
    )

    validity_time_unit: str = Field(
        ...,  # Required field, no default
        description="Unit of subscription validity ('minute', 'hour', 'day', 'week', 'month', 'year')"
    )

    # Renewal and status fields
    auto_renew_end_datetime: Optional[datetime] = Field(
        default=None,
        description="End datetime for auto-renewal period. If None, no auto-renewal. If set, auto-renewal is active until this time."
    )

    status: SubscriptionStatus = Field(
        ...,  # Required field, no default
        description="Subscription Status (active, trial, pending_confirmation, etc.)"
    )

    # IAM permissions structure - simplified flattened list
    granted_iam_permissions: List[UserPermission] = Field(
        default_factory=list,
        description="IAM permissions granted by this subscription"
    )

    fallback_plan_id: Optional[str] = Field(
        default=None,  # Optional field with None default
        description="ID of the plan to fall back to if this subscription expires"
    )

    price_paid_usd: float = Field(
        ...,  # Required field, no default
        description="Amount paid for this subscription in USD"
    )

    payment_ref: Optional[str] = Field(
        default=None,
        description="Reference to payment transaction"
    )

    # Credit management fields
    subscription_based_insight_credits_per_update: int = Field(
        default=0,
        description="Number of insight credits to add on each update"
    )

    subscription_based_insight_credits_update_freq_h: int = Field(
        default=24,
        description="Frequency of insight credits update in hours"
    )

    extra_insight_credits_per_cycle: int = Field(
        default=0,
        description="Additional insight credits granted per subscription cycle"
    )

    voting_credits_per_update: int = Field(
        default=0,
        description="Number of voting credits to add on each update"
    )

    voting_credits_update_freq_h: int = Field(
        default=62,
        description="Frequency of voting credits update in hours"
    )

    # General metadata for extensibility
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the subscription"
    )

    @model_validator(mode='before')
    @classmethod
    def ensure_id_exists(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensures the id field exists by generating it using UUID if needed.
        """
        if not isinstance(data, dict):
            return data

        # If id is already provided and non-empty, leave it alone
        if data.get('id'):
            return data

        # Generate a UUID-based id if not provided
        data['id'] = str(uuid.uuid4())
        return data

    @model_validator(mode='before')
    @classmethod
    def auto_calculate_cycle_end_date(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Auto-calculate cycle_end_datetime if not provided, based on cycle_start_datetime,
        validity_time_length, and validity_time_unit.
        """
        if not isinstance(data, dict):
            return data

        # Only calculate if cycle_end_datetime is not already provided or is the default
        if ('cycle_end_datetime' not in data or
            data['cycle_end_datetime'] is None or
            # Check if it's the default factory value (close to now)
            (isinstance(data.get('cycle_end_datetime'), datetime) and
             abs((data['cycle_end_datetime'] - datetime.now(timezone.utc)).total_seconds()) < 5)):

            cycle_start_datetime = data.get('cycle_start_datetime')
            validity_time_length = data.get('validity_time_length')
            validity_time_unit = data.get('validity_time_unit')

            if cycle_start_datetime and validity_time_length and validity_time_unit:
                data['cycle_end_datetime'] = cls.calculate_cycle_end_date(
                    cycle_start_datetime, validity_time_length, validity_time_unit
                )
            else:
                raise ValueError(
                    "Cannot create subscription without cycle_end_datetime. "
                    "Either provide cycle_end_datetime directly or provide "
                    "cycle_start_datetime, validity_time_length, and validity_time_unit for auto-calculation."
                )

        return data

    @model_validator(mode='after')
    def validate_cycle_end_date_required(self) -> 'UserSubscription':
        """
        Ensures cycle_end_datetime is NEVER None after all processing.
        This is a business rule validation that must always pass.
        """
        if self.cycle_end_datetime is None:
            raise ValueError(
                "cycle_end_datetime is required and cannot be None. "
                "This is a critical business rule violation."
            )
        return self

    @property
    def cycle_end_datetime_safe(self) -> datetime:
        """
        Get cycle_end_datetime with guaranteed non-None value.
        This property enforces the business rule that cycle_end_datetime is never None after validation.
        """
        if self.cycle_end_datetime is None:
            raise ValueError(
                "cycle_end_datetime is None - this violates the business rule. "
                "Subscription model validation should have prevented this."
            )
        return self.cycle_end_datetime

    # Helper method to calculate cycle end date
    @classmethod
    def calculate_cycle_end_date(cls, start_date: datetime, validity_length: int, validity_unit: str) -> datetime:
        """Calculate the end date based on start date and validity period."""
        if validity_unit == "minute":
            return start_date + relativedelta(minutes=validity_length)
        elif validity_unit == "hour":
            return start_date + relativedelta(hours=validity_length)
        elif validity_unit == "day":
            return start_date + relativedelta(days=validity_length)
        elif validity_unit == "week":
            return start_date + relativedelta(weeks=validity_length)
        elif validity_unit == "year":
            return start_date + relativedelta(years=validity_length)
        else:  # Default to months
            return start_date + relativedelta(months=validity_length)

    # Methods for subscription management
    def is_active(self) -> bool:
        """Check if the subscription is currently active."""
        now = datetime.now(timezone.utc)
        return (
            self.status == SubscriptionStatus.ACTIVE and
            self.cycle_start_datetime <= now <= self.cycle_end_datetime_safe
        )

    def is_expired(self) -> bool:
        """Check if the subscription has expired."""
        now = datetime.now(timezone.utc)
        return now > self.cycle_end_datetime_safe

    def subscription_time_remaining(self, unit: TimeUnit = TimeUnit.SECOND, with_auto_renew: bool = False) -> float:
        """
        Calculate time remaining in the subscription.

        Args:
            unit: Time unit to return (using TimeUnit enum)
            with_auto_renew: Whether to consider auto-renewal cycles until auto_renew_end_datetime

        Returns:
            Time remaining in the specified unit as float
        """
        now = datetime.now(timezone.utc)

        if with_auto_renew and self.auto_renew_end_datetime:
            # Calculate with auto-renewal logic
            # If auto-renewal ends before/at current cycle end, only current cycle matters
            if self.auto_renew_end_datetime <= self.cycle_end_datetime_safe:
                if now >= self.cycle_end_datetime_safe:
                    return 0.0
                time_diff = self.cycle_end_datetime_safe - now
            else:
                # If we're past the auto-renewal end date, no time remaining
                if now >= self.auto_renew_end_datetime:
                    return 0.0

                # Calculate the last cycle end date that falls within auto_renew_end_datetime
                last_cycle_end = self._calculate_last_cycle_end_within_auto_renew()

                # Calculate time from now until that last cycle end
                if now >= last_cycle_end:
                    return 0.0

                time_diff = last_cycle_end - now
        else:
            # Basic time calculation without auto-renewal
            if now >= self.cycle_end_datetime_safe:
                return 0.0
            time_diff = self.cycle_end_datetime_safe - now

        # Convert to the requested unit
        return self._convert_time_to_unit(time_diff.total_seconds(), unit.value)

    def _calculate_last_cycle_end_within_auto_renew(self) -> datetime:
        """
        Calculate the last cycle end date that falls within the auto_renew_end_datetime period.

        Returns:
            The last cycle end date before auto_renew_end_datetime expires
        """
        if not self.auto_renew_end_datetime:
            return self.cycle_end_datetime_safe

        # Start with current cycle end
        current_cycle_end = self.cycle_end_datetime_safe

        # Keep adding cycle lengths until we pass auto_renew_end_datetime
        while current_cycle_end < self.auto_renew_end_datetime:
            # Calculate next cycle end by adding the cycle length
            next_cycle_end = self.calculate_cycle_end_date(
                start_date=current_cycle_end,
                validity_length=self.validity_time_length,
                validity_unit=self.validity_time_unit
            )

            # If the next cycle would end after auto_renew_end_datetime, we stop
            if next_cycle_end > self.auto_renew_end_datetime:
                break

            current_cycle_end = next_cycle_end

        return current_cycle_end

    def _convert_time_to_unit(self, total_seconds: float, unit: str) -> float:
        """
        Convert seconds to the specified time unit.

        Args:
            total_seconds: Total seconds to convert
            unit: Target unit (string value from TimeUnit enum)

        Returns:
            Time in the specified unit as float
        """
        conversions = {
            'second': 1.0,
            'minute': 60.0,
            'hour': 3600.0,
            'day': 3600.0 * 24.0,
            'week': 3600.0 * 24.0 * 7.0,
            'month': 3600.0 * 24.0 * 30.0,  # Approximate 30 days per month
            'year': 3600.0 * 24.0 * 365.0,  # Approximate 365 days per year
        }

        divisor = conversions.get(unit.lower(), 1.0)
        return total_seconds / divisor

