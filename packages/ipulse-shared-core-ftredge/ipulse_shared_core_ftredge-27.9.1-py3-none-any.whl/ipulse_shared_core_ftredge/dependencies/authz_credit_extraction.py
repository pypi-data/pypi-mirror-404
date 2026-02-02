"""
Utility functions for extracting credit information from authorization responses.

This module provides helper functions to extract credit information from OPA
authorization decisions, avoiding the need for complex dependency injection.
"""
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def extract_credits_from_authz_response(authz_info: Any) -> Optional[Dict[str, float]]:
    """
    Extract credit information from OPA authorization decision.

    This function replaces the complex PreFetchedCredits dependency by directly
    extracting credit information from the authorization response.

    Args:
        authz_info: Authorization information from OPA decision (typically AuthorizedRequest)

    Returns:
        Dictionary with credit information or None if not available:
        {
            "sbscrptn_based_insight_credits": float,
            "extra_insight_credits": float
        }
    """
    if not authz_info:
        logger.debug("No authorization info provided for credit extraction")
        return None

    try:
        # Handle dict-like authorization info (AuthorizedRequest typically converts to dict)
        if isinstance(authz_info, dict) and 'opa_decision' in authz_info:
            requestor_info = authz_info['opa_decision'].get("requestor_post_authz", {})
            if requestor_info:
                extracted_credits = {
                    "sbscrptn_based_insight_credits": float(requestor_info.get("sbscrptn_based_insight_credits", 0.0)),
                    "extra_insight_credits": float(requestor_info.get("extra_insight_credits", 0.0))
                }
                logger.debug("Successfully extracted credits from authz response: %s", extracted_credits)
                return extracted_credits
            else:
                logger.debug("No requestor_post_authz found in OPA decision")
                return None

        # Handle object-like authorization info with attributes
        elif hasattr(authz_info, 'opa_decision'):
            opa_decision = getattr(authz_info, 'opa_decision', {})
            if isinstance(opa_decision, dict):
                requestor_info = opa_decision.get("requestor_post_authz", {})
                if requestor_info:
                    extracted_credits = {
                        "sbscrptn_based_insight_credits": float(requestor_info.get("sbscrptn_based_insight_credits", 0.0)),
                        "extra_insight_credits": float(requestor_info.get("extra_insight_credits", 0.0))
                    }
                    logger.debug("Successfully extracted credits from authz response (object): %s", extracted_credits)
                    return extracted_credits

        logger.debug("No valid OPA decision structure found in authz_info for credit extraction")
        return None

    except (AttributeError, KeyError, TypeError, ValueError) as e:
        logger.warning("Failed to extract credits from authz response: %s", e)
        return None
