"""Core API response models."""
from typing import Generic, TypeVar, Optional, Any, Dict, List
import datetime as dt
from pydantic import BaseModel, ConfigDict


T = TypeVar('T')


class BaseAPIResponse(BaseModel, Generic[T]):
    """Base API response model for all endpoints."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    success: bool
    chargeable: bool = False  # Added chargeable attribute
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[str] = None

    # Optional fields for specific use cases
    cache_hit: Optional[bool] = None  # Whether data came from cache
    charged: Optional[bool] = None    # Whether credits were charged for this request

    metadata: Dict[str, Any] = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat()
    }


class PaginatedAPIResponse(BaseAPIResponse, Generic[T]):
    """API response for paginated data."""
    total_count: int
    page: int
    page_size: int
    items: List[T]