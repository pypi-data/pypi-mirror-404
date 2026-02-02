from typing import Optional, Annotated
from fastapi import Request, HTTPException, Depends, Header
from firebase_admin import auth
from ..models.user.userauth import UserAuth

async def verify_firebase_token(
    request: Request,
    x_forwarded_authorization: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
) -> UserAuth:
    """
    Verify Firebase ID token and return a UserAuth instance with authenticated user data.

    Args:
        request: FastAPI request object
        x_forwarded_authorization: Authorization header from proxy/load balancer
        authorization: Standard authorization header

    Returns:
        UserAuth instance with verified user data

    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    # Get token from either x-forwarded-authorization or authorization header
    token = x_forwarded_authorization or authorization

    if not token or token == "None" or not token.strip():
        raise HTTPException(
            status_code=401,
            detail="Authorization token is missing"
        )

    try:
        # Handle potential Header object or string
        if hasattr(token, '__str__') and not isinstance(token, str):
            # If it's a Header object or similar, convert to string
            token_str = str(token)
            # Check if the string representation looks like a Header object's repr
            if 'annotation=' in token_str or 'required=' in token_str:
                # This means we got the internal representation of a Header object
                # In this case, we need to extract the actual value
                if hasattr(token, 'default'):
                    token_str = str(token.default) if token.default is not None else ""
                else:
                    token_str = ""
            elif token_str == "None":
                token_str = ""
        else:
            # It's already a string
            token_str = token if isinstance(token, str) else str(token)

        # Check if we still have an empty or None token
        if not token_str or token_str == "None":
            raise HTTPException(
                status_code=401,
                detail="Authorization token is missing"
            )

        # Remove 'Bearer ' prefix if present
        token_str = token_str.replace("Bearer ", "")

        # Verify the token
        decoded_token = auth.verify_id_token(token_str)

        # Create UserAuth instance from decoded token
        email = decoded_token.get('email')
        if not email:
            raise ValueError("Token must contain user email")
        user_auth = UserAuth(
            email=email,
            password=None,  # No password for token-based auth
            display_name=decoded_token.get('name'),
            user_uid=decoded_token.get('uid'),
            email_verified=decoded_token.get('email_verified', False),
            custom_claims=decoded_token.get('custom_claims', {}),
            phone_number=decoded_token.get('phone_number'),
            # Note: provider_data, metadata, and timestamps would come from getUserRecord() if needed
        )

        # Store the full decoded token in request state for use in authorization middleware
        # This maintains backward compatibility with existing authorization code
        request.state.user = decoded_token

        return user_auth

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        ) from e

# Type alias for dependency injection
AuthUser = Annotated[UserAuth, Depends(verify_firebase_token)]
