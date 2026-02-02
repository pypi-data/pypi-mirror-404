from datetime import datetime, timezone
from typing import Any , Optional, ClassVar
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
import dateutil.parser

class BaseNoSQLModel(BaseModel):
    """Base model with common fields and configuration"""
    # CRITICAL: Use extra="ignore" instead of extra="forbid" for NoSQL resilience.
    # This prevents service failures when Firestore schema evolves (new fields added).
    # Only model-defined fields are serialized to API responses - UI is protected.
    # Extra fields in Firestore are silently ignored, not exposed to consumers.
    model_config = ConfigDict(frozen=False, extra="ignore")

    # Required class variables that must be defined in subclasses
    SCHEMA_ID: ClassVar[str]
    SCHEMA_NAME: ClassVar[str]
    VERSION: ClassVar[int]
    DOMAIN: ClassVar[str]
    OBJ_REF: ClassVar[str]

    # Schema versioning - these will be auto-populated from class variables
    schema_version: int = Field(
        default=None,  # Will be auto-populated by model_validator
        description="Version of this Class == version of DB Schema",
        frozen=True  # Keep schema version frozen for data integrity
    )

    schema_id: str = Field(
        default=None,  # Will be auto-populated by model_validator
        description="Identifier for the schema this document adheres to"
    )
    schema_name: str = Field(
        default=None,  # Will be auto-populated by model_validator
        description="Name of the schema this document adheres to"
    )

    # Audit fields - created fields are frozen after creation, updated fields are mutable
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), frozen=True)
    created_by: Optional[str] = Field(default=None, frozen=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = Field(default=None)

    @model_validator(mode='before')
    @classmethod
    def populate_schema_fields(cls, values):
        """Auto-populate schema fields from class variables if not provided"""
        if isinstance(values, dict):
            # Set if not already provided or if None
            if ('schema_version' not in values or values.get('schema_version') is None) and hasattr(cls, 'VERSION'):
                values['schema_version'] = cls.VERSION
            if ('schema_id' not in values or values.get('schema_id') is None) and hasattr(cls, 'SCHEMA_ID'):
                values['schema_id'] = cls.SCHEMA_ID
            if ('schema_name' not in values or values.get('schema_name') is None) and hasattr(cls, 'SCHEMA_NAME'):
                values['schema_name'] = cls.SCHEMA_NAME
        return values

    @classmethod
    def get_collection_name(cls) -> str:
        """Generate standard collection name"""
        return f"{cls.DOMAIN}_{cls.OBJ_REF}s"

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> datetime:
        """
        Ensures that datetime fields are properly parsed into datetime objects.
        Handles both datetime objects (from Firestore) and ISO format strings (from APIs).
        """
        if isinstance(v, datetime):
            # If it's already a datetime object (including Firestore's DatetimeWithNanoseconds),
            # return it directly.
            return v

        if isinstance(v, str):
            # If it's a string, parse it into a datetime object.
            try:
                return dateutil.parser.isoparse(v)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid datetime string format: {v} - {e}")

        # If the type is not a datetime or a string, it's an unsupported format.
        raise ValueError(f"Unsupported type for datetime parsing: {type(v)}")
