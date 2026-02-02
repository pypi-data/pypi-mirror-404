import json
from datetime import datetime
from enum import Enum
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
from google.api_core import datetime_helpers

class EnsureJSONEncoderCompatibility(json.JSONEncoder):
    """Custom JSON encoder that handles Firestore datetime types and other non-serializable objects."""
    def default(self, obj):
        # Handle datetime types
        if isinstance(obj, (datetime, DatetimeWithNanoseconds, datetime_helpers.DatetimeWithNanoseconds)):
            return obj.isoformat()
        # Handle enum types
        elif isinstance(obj, Enum):
            return obj.value
        # Handle pydantic models
        elif hasattr(obj, 'model_dump'):
            return obj.model_dump()
        # Default behavior for other types
        return super().default(obj)

def convert_to_json_serializable(obj):
    """
    Recursively convert objects to JSON serializable format.
    Handles datetime objects, Enums, and nested structures.

    Args:
        obj: Any Python object that might contain non-serializable types

    Returns:
        The object with all non-serializable types converted to serializable ones
    """
    # Handle None
    if obj is None:
        return None

    # Handle datetime objects (including Firestore's DatetimeWithNanoseconds)
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()

    # Handle Enum values
    elif isinstance(obj, Enum):
        return obj.value

    # Handle dictionaries
    elif isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}

    # Handle lists and tuples
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]

    # Handle sets
    elif isinstance(obj, set):
        return [convert_to_json_serializable(item) for item in obj]

    # Handle Pydantic models and other objects with model_dump method
    elif hasattr(obj, 'model_dump'):
        return convert_to_json_serializable(obj.model_dump())

    # Return primitive types as-is
    return obj
