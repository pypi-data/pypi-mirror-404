import json
import datetime
from typing import Any
from enum import Enum
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle special types like datetimes, UUIDs, and Pydantic models."""

    def default(self, obj: Any) -> Any:
        # Handle datetime objects
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

        # Handle date objects
        elif isinstance(obj, datetime.date):
            return obj.isoformat()

        # Handle time objects
        elif isinstance(obj, datetime.time):
            return obj.isoformat()

        # Handle UUID objects
        elif isinstance(obj, UUID):
            return str(obj)

        # Handle Decimal objects
        elif isinstance(obj, Decimal):
            return float(obj)

        # Handle Enum objects
        elif isinstance(obj, Enum):
            return obj.value

        # Handle Pydantic models - exclude computed fields
        elif isinstance(obj, BaseModel):
            return obj.model_dump(exclude_computed=True)

        # Handle sets by converting to sorted lists for consistent output
        elif isinstance(obj, set):
            return sorted(list(obj))

        # For everything else, use the default encoder
        return super().default(obj)
