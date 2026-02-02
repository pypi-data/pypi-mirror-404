"""Credit-related API response models."""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from .base_api_response import BaseAPIResponse

T = TypeVar('T')


class UserCreditBalance(BaseModel):
    """User's current credit balance."""
    sbscrptn_based_insight_credits: float
    extra_insight_credits: float


class UpdatedUserCreditInfo(BaseModel):
    """Information about credit charging attempt and results."""
    charge_attempted: bool
    charge_successful: bool
    cost_incurred: float
    items_processed_for_charge: int
    user_balance: UserCreditBalance


class CreditChargeableAPIResponse(BaseAPIResponse[T], Generic[T]):
    """API response for endpoints that may charge credits."""
    updated_user_credit_info: Optional[UpdatedUserCreditInfo] = None
