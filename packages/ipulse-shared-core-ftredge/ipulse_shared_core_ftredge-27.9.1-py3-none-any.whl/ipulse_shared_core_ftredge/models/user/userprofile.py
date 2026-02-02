""" User Profile model for storing personal information and settings. """
from datetime import date, datetime
import re  # Add re import
from typing import Set, Optional, ClassVar, Dict, Any, List
from pydantic import EmailStr, Field, ConfigDict, model_validator, field_validator
from ipulse_shared_base_ftredge import Layer, Module, list_enums_as_lower_strings, SystemSubject, IAMUserType
from ..base_nosql_model import BaseNoSQLModel
# ORIGINAL AUTHOR ="Russlan Ramdowar;russlan@ftredge.com"
# CLASS_ORGIN_DATE=datetime(2024, 2, 12, 20, 5)

############################ !!!!! ALWAYS UPDATE SCHEMA VERSION , IF SCHEMA IS BEING MODIFIED !!! #################################
class UserProfile(BaseNoSQLModel):
    """
    User Profile model for storing personal information and settings.
    """
    model_config = ConfigDict(frozen=False, extra="forbid")  # Allow field modification

    # Class constants
    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = ""
    VERSION: ClassVar[int] = 5  # Incremented version for primary_usertype addition
    DOMAIN: ClassVar[str] = "_".join(list_enums_as_lower_strings(Layer.PULSE_APP, Module.CORE, SystemSubject.USER))
    OBJ_REF: ClassVar[str] = "userprofile"


    id: Optional[str] = Field(
        default=None,  # Will be auto-generated from user_uid if not provided
        description=f"User Profile ID, format: {OBJ_REF}_user_uid"
    )

    user_uid: str = Field(
        ...,
        min_length=1,
        description="User UID from Firebase Auth",
        frozen=True
    )

    # Added primary_usertype field for main role categorization
    primary_usertype: IAMUserType = Field(
        ...,
        description="Primary user type from IAMUserType enum"
    )

    # Renamed usertypes to secondary_usertypes
    secondary_usertypes: List[IAMUserType] = Field(
        default_factory=list,
        description="List of secondary user types from IAMUserType enum"
    )

    # Rest of the fields remain the same
    email: EmailStr = Field(
        ...,
        description="Email address",
        frozen=True
    )
    organizations_uids: Set[str] = Field(
        default_factory=set,
        description="Organization UIDs the user belongs to"
    )

    # System identification (read-only)
    provider_id: str = Field(
        ...,
        description="User provider ID",
        frozen=True
    )
    aliases: Optional[Dict[str, str]] = Field(
        default=None,
        description="User aliases. With alias as key and description as value."
    )

    # User-editable fields
    username: str = Field(
        default="",  # Made optional with empty default - will be auto-generated
        max_length=12,  # Updated to 12 characters
        pattern="^[a-zA-Z0-9_]+$",  # Allow underscore
        description="Username (public display name), max 12 chars, alphanumeric and underscore. Auto-generated from email if not provided."
    )
    dob: Optional[date] = Field(
        default=None,
        description="Date of birth"
    )
    first_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="First name"
    )
    last_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Last name"
    )
    mobile: Optional[str] = Field(
        default=None,
        pattern=r"^\+?[1-9]\d{1,14}$",  # Added 'r' prefix for raw string
        description="Mobile phone number"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the user"
    )

    # Remove audit fields as they're inherited from BaseNoSQLModel

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

    @model_validator(mode='before')
    @classmethod
    def populate_username(cls, data: Any) -> Any:
        """
        Generates or sanitizes the username.
        If username is provided and non-empty, it's sanitized and truncated to 10 chars.
        If not provided or empty, it's generated from the email (part before '@'),
        sanitized, and truncated to 10 chars.
        If no email is available, generates a default username.
        """
        if not isinstance(data, dict):
            # Not a dict, perhaps an instance already, skip
            return data

        email = data.get('email')
        username = data.get('username')

        # Check if username is provided and non-empty
        if username and isinstance(username, str) and username.strip():
            # Sanitize and truncate provided username
            sanitized_username = re.sub(r'[^a-zA-Z0-9_]', '', username)
            data['username'] = sanitized_username[:12] if sanitized_username else "user"
        elif email and isinstance(email, str):
            # Generate from email
            email_prefix = email.split('@')[0]
            sanitized_prefix = re.sub(r'[^a-zA-Z0-9_]', '', email_prefix)
            data['username'] = sanitized_prefix[:12] if sanitized_prefix else "user"
        else:
            # Fallback if no email or username provided
            data['username'] = "user"

        return data

    @model_validator(mode='before')
    @classmethod
    def convert_datetime_to_date(cls, data: Any) -> Any:
        """
        Convert datetime objects to date objects for date fields.
        This handles the case where Firestore returns datetime objects
        but the model expects date objects (e.g., dob field).
        """
        if not isinstance(data, dict):
            return data

        # Handle dob field specifically
        if 'dob' in data and isinstance(data['dob'], datetime):
            data['dob'] = data['dob'].date()

        return data