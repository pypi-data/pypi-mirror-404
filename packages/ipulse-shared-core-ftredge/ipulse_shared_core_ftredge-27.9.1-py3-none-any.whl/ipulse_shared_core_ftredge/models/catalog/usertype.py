"""
User Defaults Model

This module defines the configuration templates for user type defaults that are stored in Firestore.
These templates are used to create user profiles and statuses with consistent default settings
based on their user type (superadmin, admin, internal, authenticated, anonymous).
"""

from typing import Dict, Any, Optional, ClassVar, List
from datetime import datetime
from pydantic import Field, ConfigDict, field_validator, model_validator
from ipulse_shared_base_ftredge import Layer, Module, list_enums_as_lower_strings, SystemSubject, ObjectOverallStatus
from ipulse_shared_base_ftredge.enums.enums_iam import IAMUserType
from ipulse_shared_core_ftredge.models.base_nosql_model import BaseNoSQLModel
from ipulse_shared_core_ftredge.models.user.user_permissions import UserPermission

# ORIGINAL AUTHOR ="russlan.ramdowar;russlan@ftredge.com"
# CLASS_ORIGIN_DATE="2025-06-27"


############################################ !!!!! ALWAYS UPDATE SCHEMA VERSION IF SCHEMA IS BEING MODIFIED !!! ############################################
class UserType(BaseNoSQLModel):
    """
    Configuration template for user type defaults stored in Firestore.
    These templates define the default settings applied when creating users of specific types.
    """

    model_config = ConfigDict(extra="forbid")

    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = ""
    VERSION: ClassVar[int] = 1
    DOMAIN: ClassVar[str] = "_".join(list_enums_as_lower_strings(Layer.PULSE_APP, Module.CORE.name, SystemSubject.CATALOG.name))
    OBJ_REF: ClassVar[str] = "usertype"

    id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this user type template (e.g., 'superadmin_1', 'authenticated_1'). Auto-generated if not provided.",
        frozen=True
    )

    version: int = Field(
        ...,
        ge=1,
        description="Version of this user type template",
        frozen=True
    )

    pulse_status: ObjectOverallStatus = Field(
        default=ObjectOverallStatus.ACTIVE,
        description="Overall status of this user type configuration"
    )

    # User type configuration
    primary_usertype: IAMUserType = Field(
        ...,
        description="Primary user type for this configuration template",
        frozen=True
    )

    secondary_usertypes: List[IAMUserType] = Field(
        default_factory=list,
        description="Secondary user types automatically assigned to users of this primary type",
        frozen=True
    )

    # Organization defaults
    default_organizations: List[str] = Field(
        default_factory=list,
        description="Default organization UIDs for users of this type",
        frozen=True
    )

    # IAM permissions structure - simplified flattened list
    granted_iam_permissions: List[UserPermission] = Field(
        default_factory=list,
        description="Default IAM permissions granted to users of this type.",
        frozen=True
    )

    default_extra_insight_credits: int = Field(
        default=0,
        ge=0,
        description="Default extra insight credits for users of this type",
        frozen=True
    )

    default_voting_credits: int = Field(
        default=0,
        ge=0,
        description="Default voting credits for users of this type",
        frozen=True
    )

    # Subscription defaults
    default_subscriptionplan_if_unpaid: Optional[str] = Field(
        default=None,
        description="Default subscription plan ID to assign if user has no active subscription",
        frozen=True
    )

    default_subscriptionplan_auto_renewal_end: Optional[datetime] = Field(
        default=None,
        description="Default auto-renewal end date to apply when assigning default_subscriptionplan_if_unpaid",
        frozen=True
    )

    # Additional metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for this user type configuration",
        frozen=True
    )

    @model_validator(mode='before')
    @classmethod
    def set_id_if_not_provided(cls, data: Any) -> Any:
        """Generate an ID from primary_usertype and version if not provided."""
        if isinstance(data, dict):
            primary_usertype = data.get('primary_usertype')
            version = data.get('version')
            provided_id = data.get('id')

            if primary_usertype and version is not None:
                primary_usertype_str = str(primary_usertype)
                expected_id = f"{primary_usertype_str}_{version}"

                if provided_id is None:
                    # Auto-generate ID
                    data['id'] = expected_id
                else:
                    # Validate provided ID matches expected format
                    if provided_id != expected_id:
                        raise ValueError(
                            f"Invalid ID format. Expected '{expected_id}' based on "
                            f"primary_usertype='{primary_usertype_str}' and version={version}, "
                            f"but got '{provided_id}'. ID must follow format: {{primary_usertype}}_{{version}}"
                        )
        return data

    @property
    def usertype_id(self) -> str:
        """Get the ID as a non-optional string. ID is always set after validation."""
        if self.id is None:
            raise ValueError("UserType ID is not set - this should not happen after model validation")
        return self.id

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

    @field_validator('secondary_usertypes')
    @classmethod
    def validate_secondary_usertypes(cls, v: List[IAMUserType]) -> List[IAMUserType]:
        """Validate secondary user types list."""
        # Remove duplicates while preserving order
        seen = set()
        unique_list = []
        for user_type in v:
            if user_type not in seen:
                seen.add(user_type)
                unique_list.append(user_type)
        return unique_list