"""
User Profile Operations - CRUD operations for UserProfile
"""
import os
import logging
from typing import Dict, Any, Optional
from google.cloud import firestore
from pydantic import ValidationError as PydanticValidationError

from ...models import UserProfile
from ...exceptions import ResourceNotFoundError, UserProfileError
from ..base import BaseFirestoreService


class UserprofileOperations:
    """
    Handles CRUD operations for UserProfile documents
    """

    def __init__(
        self,
        firestore_client: firestore.Client,
        logger: Optional[logging.Logger] = None,
        timeout: float = 10.0,
        profile_collection: Optional[str] = None,
    ):
        collection_name = profile_collection or UserProfile.get_collection_name()
        self.db_service = BaseFirestoreService[UserProfile](
            db=firestore_client,
            collection_name=collection_name,
            resource_type="UserProfile",
            model_class=UserProfile,
            logger=logger,
            timeout=timeout
        )
        self.logger = logger or logging.getLogger(__name__)
        self.profile_collection_name = collection_name

        # Archival configuration
        self.archive_profile_on_delete = os.getenv('ARCHIVE_PROFILE_ON_DELETE', 'true').lower() == 'true'
        self.archive_profile_collection_name = os.getenv(
            'ARCHIVE_PROFILE_COLLECTION_NAME',
            f"~archive_{self.profile_collection_name}"
        )

    async def get_userprofile(self, user_uid: str) -> Optional[UserProfile]:
        """Fetches a user profile from Firestore."""
        self.logger.info(f"Fetching user profile for UID: {user_uid}")
        try:
            profile_data = await self.db_service.get_document(f"{UserProfile.OBJ_REF}_{user_uid}", convert_to_model=True)
            if profile_data and isinstance(profile_data, UserProfile):
                return profile_data
            return None
        except ResourceNotFoundError:
            self.logger.warning(f"UserProfile not found for UID: {user_uid}")
            return None
        except Exception as e:
            self.logger.error("Error fetching user profile for %s: %s", user_uid, e, exc_info=True)
            raise UserProfileError(
                detail=f"Failed to fetch user profile: {str(e)}",
                user_uid=user_uid,
                operation="get_userprofile",
                original_error=e
            ) from e

    async def create_userprofile(self, userprofile: UserProfile, creator_uid: Optional[str] = None) -> UserProfile:
        """Creates a new user profile in Firestore."""
        self.logger.info(f"Creating user profile for UID: {userprofile.user_uid}")
        try:
            doc_id = f"{UserProfile.OBJ_REF}_{userprofile.user_uid}"
            effective_creator_uid = creator_uid or userprofile.user_uid
            await self.db_service.create_document(doc_id, userprofile.model_dump(exclude_none=True), creator_uid=effective_creator_uid)
            self.logger.info(f"Successfully created user profile for UID: {userprofile.user_uid}")
            return userprofile
        except Exception as e:
            self.logger.error(f"Error creating user profile for {userprofile.user_uid}: {e}", exc_info=True)
            raise UserProfileError(
                detail=f"Failed to create user profile: {str(e)}",
                user_uid=userprofile.user_uid,
                operation="create_userprofile",
                original_error=e
            )

    async def update_userprofile(self, user_uid: str, profile_data: Dict[str, Any], updater_uid: str) -> UserProfile:
        """Updates an existing user profile in Firestore."""
        self.logger.info(f"Updating user profile for UID: {user_uid}")
        try:
            doc_id = f"{UserProfile.OBJ_REF}_{user_uid}"
            await self.db_service.update_document(doc_id, profile_data, updater_uid)
            updated_profile = await self.get_userprofile(user_uid)
            if not updated_profile:
                raise ResourceNotFoundError(
                    resource_type="UserProfile",
                    resource_id=doc_id
                )
            self.logger.info(f"Successfully updated user profile for UID: {user_uid}")
            return updated_profile
        except ResourceNotFoundError as e:
            self.logger.error(f"Cannot update non-existent user profile for {user_uid}")
            raise e
        except Exception as e:
            self.logger.error(f"Error updating user profile for {user_uid}: {e}", exc_info=True)
            raise UserProfileError(
                detail=f"Failed to update user profile: {str(e)}",
                user_uid=user_uid,
                operation="update_userprofile",
                original_error=e
            )

    async def delete_userprofile(self, user_uid: str, updater_uid: str = "system_deletion", archive: bool = True) -> bool:
        """Delete (archive and delete) user profile"""
        profile_doc_id = f"{UserProfile.OBJ_REF}_{user_uid}"
        should_archive = archive if archive is not None else self.archive_profile_on_delete

        try:
            # Get profile data for archival
            profile_data = await self.db_service.get_document(profile_doc_id, convert_to_model=False)

            if profile_data:
                # Ensure we have a dict for archival
                profile_dict = profile_data if isinstance(profile_data, dict) else profile_data.__dict__

                # Archive if enabled
                if should_archive:
                    await self.db_service.archive_document(
                        document_data=profile_dict,
                        doc_id=profile_doc_id,
                        archive_collection=self.archive_profile_collection_name,
                        archived_by=updater_uid
                    )

                # Delete the original document
                await self.db_service.delete_document(profile_doc_id)
                self.logger.info(f"Successfully deleted user profile: {profile_doc_id}")
                return True
            else:
                self.logger.warning(f"User profile {profile_doc_id} not found for deletion")
                return True  # Consider non-existent as successfully deleted

        except Exception as e:
            self.logger.error(f"Failed to delete user profile {profile_doc_id}: {e}", exc_info=True)
            raise UserProfileError(
                detail=f"Failed to delete user profile: {str(e)}",
                user_uid=user_uid,
                operation="delete_userprofile",
                original_error=e
            )



    async def userprofile_exists(self, user_uid: str) -> bool:
        """Check if a user profile exists."""
        return await self.db_service.document_exists(f"{UserProfile.OBJ_REF}_{user_uid}")

    async def validate_userprofile_data(
        self,
        profile_data: Optional[Dict[str, Any]] = None,
    ) -> tuple[bool, list[str]]:
        """Validate user profile data without creating documents"""
        errors = []
        if profile_data:
            try:
                UserProfile(**profile_data)
            except PydanticValidationError as e:
                errors.append(f"Profile validation error: {str(e)}")
        return len(errors) == 0, errors