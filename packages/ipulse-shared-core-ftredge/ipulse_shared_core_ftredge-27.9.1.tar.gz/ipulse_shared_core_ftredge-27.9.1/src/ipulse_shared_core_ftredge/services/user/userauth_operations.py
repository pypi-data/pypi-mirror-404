"""
User Auth Operations - Handle Firebase Auth user creation, management, and deletion
"""
import os
import asyncio
import logging
import time
from typing import Dict, Any, Optional, Union
from firebase_admin import auth
from google.cloud import firestore
from ipulse_shared_base_ftredge.enums import ApprovalStatus
from ...models import UserAuth, UserAuthCreateNew
from ...exceptions import UserAuthError
from ..base import BaseFirestoreService


class UserauthOperations:
    """
    Handles Firebase Auth operations for user creation, management, and deletion
    """

    def __init__(self, logger: Optional[logging.Logger] = None, firestore_client: Optional[firestore.Client] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.db = firestore_client

        # Archival configuration
        self.archive_auth_on_delete = os.getenv('ARCHIVE_AUTH_ON_DELETE', 'true').lower() == 'true'
        self._archive_auth_collection_name = os.getenv(
            'ARCHIVE_AUTH_COLLECTION_NAME',
            "~archive_core_user_userauths"
        )

        if self.archive_auth_on_delete and self.db:
            # Use a generic archive service without specific typing for archived documents
            self._archive_db_service = BaseFirestoreService(
                db=self.db,
                collection_name=self._archive_auth_collection_name,
                resource_type="userauth",
                logger=self.logger
            )

    @property
    def archive_auth_collection_name(self) -> str:
        """Get the archive auth collection name"""
        return self._archive_auth_collection_name

    # User Auth Operations

    async def create_userauth(
        self,
        user_auth: UserAuthCreateNew
    ) -> str:
        """
        Creates a new Firebase Auth user and returns the UID.

        Args:
            user_auth: UserAuthCreateNew model for new user creation
        """
        self.logger.info(f"Creating Firebase Auth user for email: {user_auth.email}")
        try:
            # Create user synchronously
            loop = asyncio.get_event_loop()
            user_record = await loop.run_in_executor(
                None,
                lambda: auth.create_user(
                    email=user_auth.email,
                    email_verified=user_auth.email_verified,
                    password=user_auth.password,
                    phone_number=user_auth.phone_number,
                    display_name=user_auth.display_name,
                    disabled=user_auth.disabled
                )
            )

            user_uid = user_record.uid
            self.logger.info(f"Successfully created Firebase Auth user with UID: {user_uid}")

            # Set custom claims if provided
            if user_auth.custom_claims:
                await self.set_userauth_custom_claims(user_uid, user_auth.custom_claims)

            return user_uid

        except auth.EmailAlreadyExistsError as e:
            raise UserAuthError(
                detail=f"User with email {user_auth.email} already exists",
                operation="create_userauth",
                additional_info={"email": str(user_auth.email)}
            ) from e
        except Exception as e:
            self.logger.error(f"Failed to create Firebase Auth user: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to create Firebase Auth user: {str(e)}",
                operation="create_userauth",
                additional_info={"email": str(user_auth.email)},
                original_error=e
            ) from e

    # Firebase Auth User Management

    async def get_userauth(self, user_uid: str, get_model: bool = False) -> Optional[Union[auth.UserRecord, UserAuth]]:
        """
        Retrieves a Firebase Auth user by UID.

        Args:
            user_uid: The UID of the user to retrieve
            get_model: If True, returns a UserAuth model with data and custom claims merged

        Returns:
            Firebase Auth UserRecord if get_model=False, UserAuth model if get_model=True, or None if not found
        """
        try:
            loop = asyncio.get_event_loop()
            user_record = await loop.run_in_executor(
                None,
                auth.get_user,
                user_uid
            )

            if get_model:
                return self._create_userauth_model(user_record)

            return user_record
        except auth.UserNotFoundError:
            self.logger.warning(f"Firebase Auth user with UID '{user_uid}' not found.")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving Firebase Auth user {user_uid}: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to retrieve Firebase Auth user: {str(e)}",
                user_uid=user_uid,
                operation="get_userauth",
                original_error=e
            ) from e

    async def get_userauth_by_email(self, email: str, get_model: bool = False) -> Optional[Union[auth.UserRecord, UserAuth]]:
        """
        Retrieves a Firebase Auth user by email.

        Args:
            email: The email of the user to retrieve
            get_model: If True, returns a UserAuth model with data and custom claims merged

        Returns:
            Firebase Auth UserRecord if get_model=False, UserAuth model if get_model=True, or None if not found
        """
        try:
            loop = asyncio.get_event_loop()
            user_record = await loop.run_in_executor(
                None,
                auth.get_user_by_email,
                email
            )

            if get_model:
                return self._create_userauth_model(user_record)

            return user_record
        except auth.UserNotFoundError:
            self.logger.warning(f"Firebase Auth user with email '{email}' not found.")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving Firebase Auth user by email {email}: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to retrieve Firebase Auth user by email: {str(e)}",
                operation="get_userauth_by_email",
                original_error=e
            ) from e

    def _create_userauth_model(self, user_record: auth.UserRecord) -> UserAuth:
        """
        Creates a UserAuth model from a Firebase Auth UserRecord with merged custom claims data.

        Args:
            user_record: Firebase Auth UserRecord

        Returns:
            UserAuth model with data and custom claims merged
        """
        from datetime import datetime, timezone

        # Convert Firebase timestamps to datetime objects
        def convert_timestamp(timestamp_ms):
            if timestamp_ms:
                # Firebase timestamps are milliseconds since epoch
                try:
                    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                except (ValueError, TypeError, AttributeError):
                    return None
            return None

        # Extract custom claims
        custom_claims = user_record.custom_claims or {}

        # Build the UserAuth model
        userauth_data = {
            "email": user_record.email,
            "display_name": user_record.display_name,
            "user_uid": user_record.uid,
            "email_verified": user_record.email_verified,
            "disabled": user_record.disabled,
            "phone_number": user_record.phone_number,
            "custom_claims": custom_claims,
            "created_at": convert_timestamp(user_record.user_metadata.creation_timestamp) if user_record.user_metadata else None,
            "last_sign_in": convert_timestamp(user_record.user_metadata.last_sign_in_timestamp) if user_record.user_metadata else None,
            "last_refresh": convert_timestamp(user_record.user_metadata.last_refresh_timestamp) if user_record.user_metadata else None,
            "valid_since": convert_timestamp(user_record.tokens_valid_after_timestamp) if hasattr(user_record, 'tokens_valid_after_timestamp') else None,
            "provider_data": [
                {
                    "uid": provider.uid,
                    "email": provider.email,
                    "display_name": provider.display_name,
                    "phone_number": provider.phone_number,
                    "provider_id": provider.provider_id
                }
                for provider in (user_record.provider_data or [])
            ]
        }

        return UserAuth(**userauth_data)

    async def update_userauth(
        self,
        user_uid: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        display_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        email_verified: Optional[bool] = None,
        disabled: Optional[bool] = None
    ) -> auth.UserRecord:
        """Updates a Firebase Auth user."""
        self.logger.info(f"Updating Firebase Auth user: {user_uid}")
        try:
            loop = asyncio.get_event_loop()
            user_record = await loop.run_in_executor(
                None,
                lambda: auth.update_user(
                    uid=user_uid,
                    email=email,
                    password=password,
                    display_name=display_name,
                    phone_number=phone_number,
                    email_verified=email_verified,
                    disabled=disabled
                )
            )

            self.logger.info(f"Successfully updated Firebase Auth user: {user_uid}")
            return user_record

        except auth.UserNotFoundError as e:
            raise UserAuthError(
                detail="Firebase Auth user not found",
                user_uid=user_uid,
                operation="update_userauth"
            ) from e
        except Exception as e:
            self.logger.error(f"Failed to update Firebase Auth user {user_uid}: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to update Firebase Auth user: {str(e)}",
                user_uid=user_uid,
                operation="update_userauth",
                original_error=e
            ) from e

    # Firebase Auth Custom Claims

    async def set_userauth_custom_claims(
        self,
        user_uid: str,
        custom_claims: Dict[str, Any],
        merge_with_existing: bool = False
    ) -> bool:
        """Sets custom claims for a Firebase Auth user with optional merging"""
        try:
            if merge_with_existing:
                # Get existing claims and merge
                user_record = await self.get_userauth(user_uid)
                if user_record and user_record.custom_claims:
                    existing_claims = user_record.custom_claims.copy()
                    existing_claims.update(custom_claims)
                    custom_claims = existing_claims

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                auth.set_custom_user_claims,
                user_uid,
                custom_claims
            )

            self.logger.info(f"Successfully set Firebase custom claims for user: {user_uid}")
            return True

        except auth.UserNotFoundError as e:
            raise UserAuthError(
                detail="Firebase Auth user not found",
                user_uid=user_uid,
                operation="set_userauth_custom_claims"
            ) from e
        except Exception as e:
            self.logger.error(f"Failed to set Firebase custom claims for user {user_uid}: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to set Firebase custom claims: {str(e)}",
                user_uid=user_uid,
                operation="set_userauth_custom_claims",
                original_error=e
            ) from e

    async def get_userauth_custom_claims(self, user_uid: str) -> Optional[Dict[str, Any]]:
        """Retrieves custom claims for a Firebase Auth user"""
        try:
            user_record = await self.get_userauth(user_uid)
            return user_record.custom_claims if user_record else None
        except Exception as e:
            self.logger.error(f"Failed to get Firebase custom claims for user {user_uid}: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to get Firebase custom claims: {str(e)}",
                user_uid=user_uid,
                operation="get_userauth_custom_claims",
                original_error=e
            ) from e

    # Firebase Auth User Deletion

    async def delete_userauth(self, user_uid: str, archive: bool = True) -> bool:
        """Deletes a Firebase Auth user with optional archival."""
        if archive and self.archive_auth_on_delete and hasattr(self, '_archive_db_service'):
            try:
                user_record = await self.get_userauth(user_uid)
                if user_record:
                    await self._archive_db_service.archive_document(
                        document_data=user_record.__dict__,
                        doc_id=f"userauth_{user_uid}",
                        archive_collection=self._archive_auth_collection_name,
                        archived_by="system_deletion"
                    )
            except Exception as e:
                self.logger.error(f"Failed to archive Firebase Auth user {user_uid}: {e}", exc_info=True)
                # Do not re-raise, as we want to proceed with deletion anyway

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                auth.delete_user,
                user_uid
            )

            self.logger.info(f"Successfully deleted Firebase Auth user: {user_uid}")
            return True

        except auth.UserNotFoundError:
            self.logger.warning(f"Firebase Auth user {user_uid} not found during deletion")
            return True  # Consider non-existent user as successfully deleted
        except Exception as e:
            self.logger.error(f"Failed to delete Firebase Auth user {user_uid}: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to delete Firebase Auth user: {str(e)}",
                user_uid=user_uid,
                operation="delete_userauth",
                original_error=e
            ) from e

    # Token and Security Operations

    async def create_custom_token(
        self,
        user_uid: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """Creates a custom token for a user with optional additional claims"""
        try:
            loop = asyncio.get_event_loop()
            token = await loop.run_in_executor(
                None,
                lambda: auth.create_custom_token(user_uid, additional_claims)
            )

            self.logger.info(f"Successfully created custom token for user: {user_uid}")
            return token.decode('utf-8') if isinstance(token, bytes) else token

        except auth.UserNotFoundError as e:
            raise UserAuthError(
                detail="Firebase Auth user not found",
                user_uid=user_uid,
                operation="create_custom_token"
            ) from e
        except Exception as e:
            self.logger.error(f"Failed to create custom token for user {user_uid}: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to create custom token: {str(e)}",
                user_uid=user_uid,
                operation="create_custom_token",
                original_error=e
            ) from e

    async def verify_id_token(
        self,
        token: str,
        check_revoked: bool = False
    ) -> Dict[str, Any]:
        """Verifies an ID token and returns the token claims"""
        try:
            loop = asyncio.get_event_loop()
            claims = await loop.run_in_executor(
                None,
                lambda: auth.verify_id_token(token, check_revoked=check_revoked)
            )

            self.logger.info(f"Successfully verified ID token for user: {claims.get('uid')}")
            return claims

        except auth.ExpiredIdTokenError as e:
            raise UserAuthError(
                detail="ID token has expired",
                operation="verify_id_token",
                additional_info={"check_revoked": check_revoked}
            ) from e
        except auth.RevokedIdTokenError as e:
            raise UserAuthError(
                detail="ID token has been revoked",
                operation="verify_id_token",
                additional_info={"check_revoked": check_revoked}
            ) from e
        except auth.InvalidIdTokenError as e:
            raise UserAuthError(
                detail="Invalid ID token provided",
                operation="verify_id_token",
                additional_info={"check_revoked": check_revoked}
            ) from e
        except Exception as e:
            self.logger.error(f"Failed to verify ID token: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to verify ID token: {str(e)}",
                operation="verify_id_token",
                original_error=e
            ) from e

    async def get_user_auth_token(
        self,
        email: str,
        password: str,
        api_key: str
    ) -> Optional[str]:
        """
        Gets a user authentication token using the Firebase REST API.

        Note: This method requires the Firebase Web API key and should be used
        for testing or specific admin scenarios. For production authentication,
        prefer using the Firebase client SDKs.
        """
        import urllib.request
        import urllib.parse
        import urllib.error
        import json

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        try:
            # Use executor to run blocking HTTP request asynchronously
            loop = asyncio.get_event_loop()

            def make_request():
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )

                try:
                    with urllib.request.urlopen(req) as response:
                        return response.read().decode('utf-8'), response.status
                except urllib.error.HTTPError as e:
                    return e.read().decode('utf-8'), e.code

            response_text, status_code = await loop.run_in_executor(None, make_request)

            if status_code != 200:
                error_details = response_text
                try:
                    error_json = json.loads(response_text)
                    if "error" in error_json:
                        error_details = f"{error_json['error'].get('message', 'Unknown error')}"
                except Exception:
                    pass

                self.logger.error(f"Auth token request failed ({status_code}): {error_details}")

                # Handle specific error conditions
                if "EMAIL_NOT_FOUND" in error_details or "INVALID_PASSWORD" in error_details:
                    raise UserAuthError(
                        detail="Invalid email or password",
                        operation="get_user_auth_token",
                        additional_info={"email": email}
                    )
                elif "USER_DISABLED" in error_details:
                    raise UserAuthError(
                        detail="User account is disabled",
                        operation="get_user_auth_token",
                        additional_info={"email": email}
                    )
                elif "INVALID_EMAIL" in error_details:
                    raise UserAuthError(
                        detail="Invalid email format",
                        operation="get_user_auth_token",
                        additional_info={"email": email}
                    )
                else:
                    raise UserAuthError(
                        detail=f"Authentication failed: {error_details}",
                        operation="get_user_auth_token",
                        additional_info={"email": email, "status_code": status_code}
                    )

            result = json.loads(response_text)
            token = result.get("idToken")

            if token:
                self.logger.info(f"Successfully obtained auth token for {email}")
                return token
            else:
                raise UserAuthError(
                    detail="No token returned from authentication service",
                    operation="get_user_auth_token",
                    additional_info={"email": email}
                )

        except UserAuthError:
            raise  # Re-raise our custom errors
        except Exception as e:
            self.logger.error(f"Error getting auth token for {email}: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to get authentication token: {str(e)}",
                operation="get_user_auth_token",
                additional_info={"email": email},
                original_error=e
            ) from e

    async def revoke_refresh_tokens(self, user_uid: str) -> bool:
        """Revokes all refresh tokens for a user, forcing re-authentication"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                auth.revoke_refresh_tokens,
                user_uid
            )

            self.logger.info(f"Successfully revoked refresh tokens for user: {user_uid}")
            return True

        except auth.UserNotFoundError as e:
            raise UserAuthError(
                detail="Firebase Auth user not found",
                user_uid=user_uid,
                operation="revoke_refresh_tokens"
            ) from e
        except Exception as e:
            self.logger.error(f"Failed to revoke refresh tokens for user {user_uid}: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to revoke refresh tokens: {str(e)}",
                user_uid=user_uid,
                operation="revoke_refresh_tokens",
                original_error=e
            ) from e

    async def generate_password_reset_link(
        self,
        email: str,
        action_code_settings: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generates a password reset link for a user"""
        try:
            loop = asyncio.get_event_loop()
            link = await loop.run_in_executor(
                None,
                lambda: auth.generate_password_reset_link(email, action_code_settings)
            )

            self.logger.info(f"Successfully generated password reset link for email: {email}")
            return link

        except auth.UserNotFoundError as e:
            raise UserAuthError(
                detail="User not found with the provided email",
                operation="generate_password_reset_link",
                additional_info={"email": email}
            ) from e
        except Exception as e:
            self.logger.error(f"Failed to generate password reset link for {email}: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to generate password reset link: {str(e)}",
                operation="generate_password_reset_link",
                additional_info={"email": email},
                original_error=e
            ) from e

    async def generate_email_verification_link(
        self,
        email: str,
        action_code_settings: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generates an email verification link for a user"""
        try:
            loop = asyncio.get_event_loop()
            link = await loop.run_in_executor(
                None,
                lambda: auth.generate_email_verification_link(email, action_code_settings)
            )

            self.logger.info(f"Successfully generated email verification link for email: {email}")
            return link

        except auth.UserNotFoundError as e:
            raise UserAuthError(
                detail="User not found with the provided email",
                operation="generate_email_verification_link",
                additional_info={"email": email}
            ) from e
        except Exception as e:
            self.logger.error(f"Failed to generate email verification link for {email}: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to generate email verification link: {str(e)}",
                operation="generate_email_verification_link",
                additional_info={"email": email},
                original_error=e
            ) from e

    # Utility Methods

    async def userauth_exists(self, user_uid: str) -> bool:
        """Check if Firebase Auth user exists"""
        user_record = await self.get_userauth(user_uid)
        return user_record is not None

    async def validate_userauth_enabled(self, user_uid: str) -> bool:
        """Validate that Firebase Auth user exists and is not disabled"""
        try:
            user_record = await self.get_userauth(user_uid)
            if not user_record:
                return False
            return not user_record.disabled
        except Exception:
            return False

    async def list_userauths(
        self,
        page_token: Optional[str] = None,
        max_results: int = 1000
    ) -> auth.ListUsersPage:
        """List Firebase Auth users with pagination"""
        try:
            loop = asyncio.get_event_loop()
            page = await loop.run_in_executor(
                None,
                lambda: auth.list_users(page_token=page_token, max_results=max_results)
            )
            return page
        except Exception as e:
            self.logger.error(f"Failed to list Firebase Auth users: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to list Firebase Auth users: {str(e)}",
                operation="list_userauths",
                original_error=e
            ) from e

    # User Status Management Operations

    async def disable_userauth(
        self,
        user_uid: str,
        user_notes: str = "Administrative action - user disabled",
        disabled_by: Optional[str] = None
    ) -> bool:
        """
        Disables a Firebase Auth user and sets user notes in custom claims

        Args:
            user_uid: UID of the user to disable
            user_notes: Descriptive notes for disabling the user
            disabled_by: Who initiated the disable action

        Returns:
            True if successfully disabled
        """
        try:
            # Get current user to preserve existing custom claims
            user_record = await self.get_userauth(user_uid)
            if not user_record:
                raise UserAuthError(
                    detail="Firebase Auth user not found",
                    user_uid=user_uid,
                    operation="disable_userauth"
                )

            # Prepare timestamp and user notes
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

            # Update custom claims with user notes and status
            existing_claims = user_record.custom_claims or {}
            existing_claims["user_notes"] = user_notes
            existing_claims["disabled_at"] = timestamp
            existing_claims["user_notes_updated_at"] = timestamp

            if disabled_by:
                existing_claims["disabled_by"] = disabled_by
                existing_claims["user_notes_updated_by"] = disabled_by

            # Set custom claims first
            await self.set_userauth_custom_claims(user_uid, existing_claims)

            # Then disable the user
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: auth.update_user(uid=user_uid, disabled=True)
            )

            self.logger.info(f"Successfully disabled Firebase Auth user: {user_uid} - {user_notes}")
            return True

        except auth.UserNotFoundError as e:
            raise UserAuthError(
                detail="Firebase Auth user not found",
                user_uid=user_uid,
                operation="disable_userauth"
            ) from e
        except Exception as e:
            self.logger.error(f"Failed to disable Firebase Auth user {user_uid}: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to disable Firebase Auth user: {str(e)}",
                user_uid=user_uid,
                operation="disable_userauth",
                original_error=e
            ) from e

    async def enable_userauth(
        self,
        user_uid: str,
        user_notes: str = "Administrative action - user enabled",
        enabled_by: Optional[str] = None
    ) -> bool:
        """
        Re-enables a Firebase Auth user and updates user notes in custom claims

        Args:
            user_uid: UID of the user to enable
            user_notes: Descriptive notes for enabling the user
            enabled_by: Who initiated the enable action

        Returns:
            True if successfully enabled
        """
        try:
            # Get current user to preserve existing custom claims
            user_record = await self.get_userauth(user_uid)
            if not user_record:
                raise UserAuthError(
                    detail="Firebase Auth user not found",
                    user_uid=user_uid,
                    operation="enable_userauth"
                )

            # Prepare timestamp and user notes
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

            # Update custom claims with user notes and status
            existing_claims = user_record.custom_claims or {}
            existing_claims["user_notes"] = user_notes
            existing_claims["enabled_at"] = timestamp
            existing_claims["user_notes_updated_at"] = timestamp

            if enabled_by:
                existing_claims["enabled_by"] = enabled_by
                existing_claims["user_notes_updated_by"] = enabled_by

            # Remove disabled-specific claims
            existing_claims.pop("disabled_at", None)
            existing_claims.pop("disabled_by", None)

            # Set custom claims first
            await self.set_userauth_custom_claims(user_uid, existing_claims)

            # Then enable the user
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: auth.update_user(uid=user_uid, disabled=False)
            )

            self.logger.info(f"Successfully enabled Firebase Auth user: {user_uid} - {user_notes}")
            return True

        except auth.UserNotFoundError as e:
            raise UserAuthError(
                detail="Firebase Auth user not found",
                user_uid=user_uid,
                operation="enable_userauth"
            ) from e
        except Exception as e:
            self.logger.error(f"Failed to enable Firebase Auth user {user_uid}: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to enable Firebase Auth user: {str(e)}",
                user_uid=user_uid,
                operation="enable_userauth",
                original_error=e
            ) from e

    # User Notes Management

    async def set_user_notes(
        self,
        user_uid: str,
        user_notes: str,
        updated_by: Optional[str] = None
    ) -> bool:
        """
        Sets user notes as a custom claim for a Firebase Auth user

        Args:
            user_uid: UID of the user
            user_notes: Notes to set for the user
            updated_by: Who updated the notes

        Returns:
            True if successfully updated
        """
        try:
            # Get current user to preserve existing custom claims
            user_record = await self.get_userauth(user_uid)
            if not user_record:
                raise UserAuthError(
                    detail="Firebase Auth user not found",
                    user_uid=user_uid,
                    operation="set_user_notes"
                )

            # Update custom claims with user notes
            existing_claims = user_record.custom_claims or {}
            existing_claims["user_notes"] = user_notes

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            existing_claims["user_notes_updated_at"] = timestamp

            if updated_by:
                existing_claims["user_notes_updated_by"] = updated_by

            # Set the updated custom claims
            await self.set_userauth_custom_claims(user_uid, existing_claims)

            self.logger.info(f"Successfully set user notes for Firebase Auth user: {user_uid}")
            return True

        except auth.UserNotFoundError as e:
            raise UserAuthError(
                detail="Firebase Auth user not found",
                user_uid=user_uid,
                operation="set_user_notes"
            ) from e
        except Exception as e:
            self.logger.error(f"Failed to set user notes for Firebase Auth user {user_uid}: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to set user notes: {str(e)}",
                user_uid=user_uid,
                operation="set_user_notes",
                original_error=e
            ) from e

    async def set_user_approval_status(
        self,
        user_uid: str,
        approval_status: ApprovalStatus,
        updated_by: Optional[str] = None
    ) -> bool:
        """
        Sets user approval status as a custom claim for a Firebase Auth user

        Args:
            user_uid: UID of the user
            approval_status: ApprovalStatus enum value to set
            updated_by: Who updated the approval status

        Returns:
            True if successfully updated
        """
        try:
            # Get current user to preserve existing custom claims
            user_record = await self.get_userauth(user_uid)
            if not user_record:
                raise UserAuthError(
                    detail="Firebase Auth user not found",
                    user_uid=user_uid,
                    operation="set_user_approval_status"
                )

            # Update custom claims with approval status
            existing_claims = user_record.custom_claims or {}
            existing_claims["user_approval_status"] = approval_status.name

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            existing_claims["user_approval_status_updated_at"] = timestamp

            if updated_by:
                existing_claims["user_approval_status_updated_by"] = updated_by

            # Set the updated custom claims
            await self.set_userauth_custom_claims(user_uid, existing_claims)

            self.logger.info(f"Successfully set user approval status to {approval_status.name} for Firebase Auth user: {user_uid}")
            return True

        except auth.UserNotFoundError as e:
            raise UserAuthError(
                detail="Firebase Auth user not found",
                user_uid=user_uid,
                operation="set_user_approval_status"
            ) from e
        except Exception as e:
            self.logger.error(f"Failed to set user approval status for Firebase Auth user {user_uid}: {e}", exc_info=True)
            raise UserAuthError(
                detail=f"Failed to set user approval status: {str(e)}",
                user_uid=user_uid,
                operation="set_user_approval_status",
                original_error=e
            ) from e
