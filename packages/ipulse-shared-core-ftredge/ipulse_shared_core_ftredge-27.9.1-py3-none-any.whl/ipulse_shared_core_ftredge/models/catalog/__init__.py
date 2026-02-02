"""
Models for default configurations
"""

from .subscriptionplan import SubscriptionPlan, ProrationMethod, PlanUpgradePath
from .usertype import UserType
__all__ = [
    "UserType",
    "SubscriptionPlan"
]
