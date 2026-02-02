
""" User IAM model for tracking user permissions and access rights. """
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from ipulse_shared_base_ftredge.enums.enums_iam import IAMUnit

class UserPermission(BaseModel):
    """
    A single permission assignment with full context.
    Flattened structure for easier management and querying.
    """
    model_config = ConfigDict(frozen=False)

    domain: str = Field(
        ...,
        description="The domain for this permission (e.g., 'papp', 'papp/oracle')"
    )
    iam_unit_type: IAMUnit = Field(
        ...,
        description="Type of IAM assignment (GROUP, ROLE, etc.)"
    )
    permission_ref: str = Field(
        ...,
        description="The permission reference/name (e.g., 'sysadmin_group', 'analyst')"
    )
    source: str = Field(
        ...,
        description="Source of this assignment (e.g., subscription plan ID, 'manual_grant')"
    )
    expires_at: datetime = Field(
        ...,
        description="When this assignment expires (mandatory - no permanent permissions)"
    )
    granted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this permission was granted"
    )
    granted_by: Optional[str] = Field(
        default=None,
        description="Who granted this permission (user ID or system identifier)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for this permission assignment"
    )

    def is_valid(self) -> bool:
        """Check if the permission is currently valid (not expired)."""
        # Ensure both datetimes are timezone-aware for comparison
        current_time = datetime.now(timezone.utc)
        expires_time = self.expires_at

        # If expires_at is timezone-naive, assume it's UTC
        if expires_time.tzinfo is None:
            expires_time = expires_time.replace(tzinfo=timezone.utc)

        return current_time <= expires_time

    def __str__(self) -> str:
        """Human-readable representation of the permission."""
        return f"{self.domain}/{self.iam_unit_type}/{self.permission_ref} from {self.source} (expires: {self.expires_at})"