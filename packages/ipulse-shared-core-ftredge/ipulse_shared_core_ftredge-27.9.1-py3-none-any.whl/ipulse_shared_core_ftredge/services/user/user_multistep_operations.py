"""
User Multistep Operations - Complete user lifecycle operations

Handles complete user creation and deletion operations that span across
Firebase Auth, UserProfile, and UserStatus in coordinated transactions.
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple, cast
from google.cloud import firestore
from ipulse_shared_base_ftredge.enums import IAMUserType
from ...models import UserProfile, UserStatus, UserAuth, UserAuthCreateNew, UserType
from .userauth_operations import UserauthOperations
from .userprofile_operations import UserprofileOperations
from .userstatus_operations import UserstatusOperations
from .user_subscription_operations import UsersubscriptionOperations
from .user_permissions_operations import UserpermissionsOperations
from ..catalog.catalog_usertype_service import CatalogUserTypeService
from ..catalog.catalog_subscriptionplan_service import CatalogSubscriptionPlanService

from ...exceptions import (
    UserCreationError
)


class UsermultistepOperations:
    """
    Handles complete user lifecycle operations including coordinated creation and deletion
    of Firebase Auth users, UserProfile, and UserStatus documents.
    """

    def __init__(
        self,
        userprofile_ops: UserprofileOperations,
        userstatus_ops: UserstatusOperations,
        userauth_ops: UserauthOperations,
        usersubscription_ops: UsersubscriptionOperations,
        useriam_ops: UserpermissionsOperations,
        catalog_usertype_service: CatalogUserTypeService,
        catalog_subscriptionplan_service: CatalogSubscriptionPlanService,
        logger: Optional[logging.Logger] = None
    ):
        self.userprofile_ops = userprofile_ops
        self.userstatus_ops = userstatus_ops
        self.userauth_ops = userauth_ops
        self.usersubscription_ops = usersubscription_ops
        self.useriam_ops = useriam_ops
        self.catalog_usertype_service = catalog_usertype_service
        self.catalog_subscriptionplan_service = catalog_subscriptionplan_service
        self.logger = logger or logging.getLogger(__name__)

    def _validate_usertype_consistency(
        self,
        userprofile: UserProfile,
        custom_claims: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Validate usertype consistency between UserProfile and custom claims.

        Args:
            userprofile: UserProfile model to validate
            custom_claims: Custom claims to validate against

        Raises:
            UserCreationError: If usertypes are inconsistent
        """
        if not custom_claims:
            return  # No claims to validate against

        userauth_primary_usertype = custom_claims.get("primary_usertype")
        userauth_secondary_usertypes = custom_claims.get("secondary_usertypes", [])

        # Convert to strings for comparison
        userprofile_primary_str = str(userprofile.primary_usertype)
        userprofile_secondary_strs = [str(ut) for ut in userprofile.secondary_usertypes]

        # Validate primary usertype consistency
        if userauth_primary_usertype and userauth_primary_usertype != userprofile_primary_str:
            raise UserCreationError(
                f"Primary usertype mismatch between UserProfile ({userprofile_primary_str}) "
                f"and custom claims ({userauth_primary_usertype})"
            )

        # Validate secondary usertypes consistency
        if userauth_secondary_usertypes and set(userauth_secondary_usertypes) != set(userprofile_secondary_strs):
            raise UserCreationError(
                f"Secondary usertypes mismatch between UserProfile ({userprofile_secondary_strs}) "
                f"and custom claims ({userauth_secondary_usertypes})"
            )

    # Complete User Creation Methods - New Strategic API

    async def create_user_from_models(
        self,
        userprofile: UserProfile,
        userstatus: UserStatus,
        userauth: Optional[UserAuthCreateNew] = None,
        validate_userauth_consistency: bool = False,
        validate_userauth_exists: bool = False
    ) -> Tuple[str, UserProfile, UserStatus]:
        """
        Create a complete user from ready UserAuthCreateNew, UserProfile, and UserStatus models.

        This method efficiently commits pre-configured models to database.

        For new user creation (when userauth is provided):
        - Creates Firebase Auth user first to get the actual UID
        - Creates new UserProfile and UserStatus models with the Firebase UID
        - Original models serve as templates

        For existing user (when userauth is None):
        - Models should already have all subscription and permission configuration applied
        - Uses the user_uid from the models to work with existing Firebase Auth user

        Args:
            userprofile: Complete UserProfile model (template for new user, or ready for existing user)
            userstatus: Complete UserStatus model (template for new user, or ready for existing user)
            userauth: Optional UserAuthCreateNew model. If provided, creates new Firebase Auth user
            validate_userauth_consistency: If True, validates userauth is consistent with userprofile
            validate_userauth_exists: If True, validates userauth exists in Firebase Auth

        Returns:
            Tuple of (user_uid, userprofile, userstatus)
        """
        firebase_user_uid = None

        # Validate that UserProfile and UserStatus have matching user_uid
        if userprofile.user_uid != userstatus.user_uid:
            raise UserCreationError(f"UserProfile and UserStatus user_uid mismatch: {userprofile.user_uid} != {userstatus.user_uid}")

        try:
            # Step 1: Handle Firebase Auth user creation or validation
            if userauth:
                # Creating new user - Firebase will generate UID

                # Validate usertype consistency if requested
                if validate_userauth_consistency:
                    self._validate_usertype_consistency(userprofile, userauth.custom_claims)

                # Create Firebase Auth user with all configuration
                self.logger.info("Creating Firebase Auth user with custom claims for email: %s", userauth.email)
                firebase_user_uid = await self.userauth_ops.create_userauth(userauth)

                # Create new models with the Firebase UID, using original models as templates
                userprofile_data = userprofile.model_dump()
                userprofile_data['user_uid'] = firebase_user_uid
                # Remove id so it gets auto-generated from user_uid
                userprofile_data.pop('id', None)
                final_userprofile = UserProfile(**userprofile_data)

                userstatus_data = userstatus.model_dump()
                userstatus_data['user_uid'] = firebase_user_uid
                # Remove id so it gets auto-generated from user_uid
                userstatus_data.pop('id', None)
                final_userstatus = UserStatus(**userstatus_data)

                user_uid = firebase_user_uid

            else:
                # Working with existing user - use models as-is
                user_uid = userprofile.user_uid
                final_userprofile = userprofile
                final_userstatus = userstatus

                # Validate userauth exists if requested (only if validate_userauth_exists is True)
                if validate_userauth_exists:
                    if not await self.userauth_ops.userauth_exists(user_uid):
                        raise UserCreationError(f"Firebase Auth user {user_uid} does not exist")

                    # Validate userauth consistency if requested
                    if validate_userauth_consistency:
                        existing_userauth = await self.userauth_ops.get_userauth(user_uid, get_model=True)
                        if existing_userauth and existing_userauth.custom_claims:
                            self._validate_usertype_consistency(userprofile, existing_userauth.custom_claims)

            # Step 2: Create UserProfile and UserStatus atomically using transaction
            try:
                # Execute transaction with nested transactional function
                @firestore.transactional
                def create_user_documents(transaction_obj):
                    """Create both UserProfile and UserStatus documents atomically"""
                    # Create UserProfile document reference
                    profile_ref = self.userprofile_ops.db_service.db.collection(
                        self.userprofile_ops.profile_collection_name
                    ).document(f"{UserProfile.OBJ_REF}_{user_uid}")

                    # Create UserStatus document reference
                    status_ref = self.userstatus_ops._status_db_service.db.collection(
                        self.userstatus_ops.status_collection_name
                    ).document(f"{UserStatus.OBJ_REF}_{user_uid}")

                    # Set both documents in transaction
                    transaction_obj.set(profile_ref, final_userprofile.model_dump(exclude_none=True))
                    transaction_obj.set(status_ref, final_userstatus.model_dump(exclude_none=True))

                    return True

                # Execute the transaction
                transaction = self.userprofile_ops.db_service.db.transaction()
                success = create_user_documents(transaction)

                if success:
                    self.logger.info("Successfully created UserProfile and UserStatus atomically for user: %s (with %d IAM permissions)",
                                   user_uid, len(final_userstatus.iam_permissions))

            except Exception as transaction_error:
                self.logger.error("Failed to create user documents atomically for %s: %s", user_uid, str(transaction_error))
                raise UserCreationError(f"Atomic user document creation failed: {str(transaction_error)}") from transaction_error

            # Step 3: Fetch final state to return
            final_profile = await self.userprofile_ops.get_userprofile(user_uid)
            final_status = await self.userstatus_ops.get_userstatus(user_uid)

            if not final_profile or not final_status:
                raise UserCreationError("Failed to retrieve user documents after creation.")

            self.logger.info("Successfully created user from ready models: %s", user_uid)
            return user_uid, final_profile, final_status

        except Exception as e:
            # Only cleanup Firebase Auth user if one was created (Firestore docs auto-rollback via transaction)
            if firebase_user_uid:
                try:
                    await self.userauth_ops.delete_userauth(firebase_user_uid)
                    self.logger.info("Successfully deleted orphaned Firebase Auth user: %s", firebase_user_uid)
                except Exception as delete_e:
                    self.logger.error("Failed to delete orphaned Firebase Auth user %s: %s", firebase_user_uid, delete_e, exc_info=True)

            raise UserCreationError(f"Failed to create user from models: {str(e)}") from e

    async def create_user_from_manual_usertype(
        self,
        userprofile: UserProfile,
        usertype: UserType,
        userauth: Optional[UserAuthCreateNew] = None,
        extra_insight_credits_override: Optional[int] = None,
        voting_credits_override: Optional[int] = None,
        subscriptionplan_id_override: Optional[str] = None,
        creator_uid: Optional[str] = None,
        apply_usertype_associated_subscriptionplan: bool = True,
        validate_userauth_consistency: bool = False,
        validate_userauth_exists: bool = False
    ) -> Tuple[str, UserProfile, UserStatus]:
        """
        Create a complete user with manual UserType configuration.

        This method builds UserStatus from usertype defaults and applies subscription/permissions
        in memory before committing to database. Organizations are always taken from usertype.

        Args:
            userprofile: Complete UserProfile model (mandatory)
            usertype: Manual UserType configuration (mandatory)
            userauth: Optional UserAuth model. If not provided, assumes user exists
            extra_insight_credits_override: Override extra credits from usertype
            voting_credits_override: Override voting credits from usertype
            subscriptionplan_id_override: Override subscription plan from usertype default
            creator_uid: Who is creating this user
            apply_usertype_associated_subscriptionplan: Whether to apply the usertype's default subscription plan
            validate_userauth_consistency: If True, validates userauth is consistent with userprofile
            validate_userauth_exists: If True, validates userauth exists in Firebase Auth

        Returns:
            Tuple of (user_uid, userprofile, userstatus)
        """
        try:
            # Always use organizations from usertype
            final_organizations = set(usertype.default_organizations)
            final_extra_credits = extra_insight_credits_override if extra_insight_credits_override is not None else usertype.default_extra_insight_credits
            final_voting_credits = voting_credits_override if voting_credits_override is not None else usertype.default_voting_credits

            # Build initial UserStatus from usertype defaults
            userstatus = UserStatus(
                user_uid=userprofile.user_uid,
                organizations_uids=final_organizations,
                iam_permissions=usertype.granted_iam_permissions or [],
                extra_insight_credits=final_extra_credits,
                voting_credits=final_voting_credits,
                metadata={},
                created_by=creator_uid or f"system_manual_usertype_{userprofile.user_uid}",
                updated_by=creator_uid or f"system_manual_usertype_{userprofile.user_uid}"
            )

            # Apply subscription to UserStatus in memory if plan specified
            plan_to_apply = subscriptionplan_id_override or usertype.default_subscriptionplan_if_unpaid
            if plan_to_apply and apply_usertype_associated_subscriptionplan:
                try:
                    self.logger.info("Applying subscription plan %s to UserStatus", plan_to_apply)

                    # Fetch subscription plan from catalog
                    subscription_plan = await self.catalog_subscriptionplan_service.get_subscriptionplan(plan_to_apply)
                    if not subscription_plan:
                        self.logger.warning("Subscription plan %s not found in catalog, skipping application", plan_to_apply)
                    else:
                        # Create UserSubscription using the helper method from subscription operations
                        # Pass usertype's default auto-renewal end if specified, otherwise use plan default
                        usertype_auto_renewal_end = getattr(usertype, 'default_subscriptionplan_auto_renewal_end', None)
                        user_subscription = self.usersubscription_ops.create_subscription_from_subscriptionplan(
                            plan=subscription_plan,
                            source=f"usertype_default_{creator_uid or 'system'}",
                            granted_at=None,  # Will use current time
                            auto_renewal_end=usertype_auto_renewal_end  # Usertype override or None for plan default
                        )

                        # Apply subscription to UserStatus (this updates credits and permissions)
                        userstatus.apply_subscription(
                            subscription=user_subscription,
                            add_associated_permissions=True,
                            remove_previous_subscription_permissions=False,  # First subscription, no existing ones
                            granted_by=creator_uid or f"system_manual_usertype_{userprofile.user_uid}"
                        )

                        self.logger.info("Successfully applied subscription plan %s to UserStatus", plan_to_apply)

                except Exception as e:
                    self.logger.error("Failed to apply subscription plan %s to UserStatus: %s", plan_to_apply, e)
                    # Don't fail user creation if subscription application fails
            elif plan_to_apply:
                self.logger.info("Subscription plan %s will be applied after user creation (apply_usertype_associated_subscriptionplan=False)", plan_to_apply)

            # Create user from ready models
            return await self.create_user_from_models(
                userprofile=userprofile,
                userstatus=userstatus,
                userauth=userauth,
                validate_userauth_consistency=validate_userauth_consistency,
                validate_userauth_exists=validate_userauth_exists
            )

        except Exception as e:
            self.logger.error("Failed to create user from manual usertype: %s", e)
            raise UserCreationError(f"Failed to create user from manual usertype: {str(e)}") from e

    async def create_user_from_catalog_usertype(
        self,
        usertype_id: str,
        userprofile: UserProfile,
        userauth: Optional[UserAuthCreateNew] = None,
        extra_insight_credits_override: Optional[int] = None,
        voting_credits_override: Optional[int] = None,
        subscriptionplan_id_override: Optional[str] = None,
        creator_uid: Optional[str] = None,
        apply_usertype_associated_subscriptionplan: bool = True,
        validate_userauth_consistency: bool = False,
        validate_userauth_exists: bool = False
    ) -> Tuple[str, UserProfile, UserStatus]:
        """
        Create a complete user based on UserType catalog configuration.

        This method fetches UserType from catalog and creates a user with
        appropriate defaults, allowing selective overrides. Organizations are always taken from usertype.

        Args:
            usertype_id: ID of the UserType configuration to fetch from catalog (mandatory)
            userprofile: Complete UserProfile model (mandatory)
            userauth: Optional UserAuth model. If not provided, assumes user exists
            extra_insight_credits_override: Override extra credits from usertype
            voting_credits_override: Override voting credits from usertype
            subscriptionplan_id_override: Override subscription plan from usertype default
            creator_uid: Who is creating this user
            apply_usertype_associated_subscriptionplan: Whether to apply the usertype's default subscription plan
            validate_userauth_consistency: If True, validates userauth is consistent with userprofile
            validate_userauth_exists: If True, validates userauth exists in Firebase Auth

        Returns:
            Tuple of (user_uid, userprofile, userstatus)
        """
        try:
            # Step 1: Fetch UserType configuration from catalog
            self.logger.info("Fetching usertype configuration for: %s", usertype_id)
            usertype_config = await self.catalog_usertype_service.get_usertype(usertype_id)
            if not usertype_config:
                raise UserCreationError(f"UserType {usertype_id} not found in catalog")

            # Step 2: Create user using manual usertype method
            return await self.create_user_from_manual_usertype(
                userprofile=userprofile,
                usertype=usertype_config,
                userauth=userauth,
                extra_insight_credits_override=extra_insight_credits_override,
                voting_credits_override=voting_credits_override,
                subscriptionplan_id_override=subscriptionplan_id_override,
                creator_uid=creator_uid,
                apply_usertype_associated_subscriptionplan=apply_usertype_associated_subscriptionplan,
                validate_userauth_consistency=validate_userauth_consistency,
                validate_userauth_exists=validate_userauth_exists
            )

        except Exception as e:
            self.logger.error("Failed to create user from catalog usertype %s: %s", usertype_id, e)
            raise UserCreationError(f"Failed to create user from catalog usertype {usertype_id}: {str(e)}") from e

    # Complete User Deletion

    async def delete_user(
        self,
        user_uid: str,
        delete_auth_user: bool = True,
        delete_profile: bool = True,
        delete_status: bool = True,
        updater_uid: str = "system_deletion",
        archive: bool = True
    ) -> Dict[str, Any]:
        """
        Delete a user holistically, including their auth, profile, and status.

        Args:
            user_uid: The UID of the user to delete.
            delete_auth_user: Whether to delete the Firebase Auth user.
            delete_profile: Whether to delete the UserProfile document.
            delete_status: Whether to delete the UserStatus document.
            updater_uid: The identifier of the entity performing the deletion.
            archive: Whether to archive documents before deletion. Defaults to True.

        Returns:
            A dictionary with the results of the deletion operations.
        """
        results = {
            "auth_deleted_successfully": not delete_auth_user,
            "profile_deleted_successfully": not delete_profile,
            "status_deleted_successfully": not delete_status,
            "errors": []
        }

        # Delete UserProfile
        if delete_profile:
            try:
                results["profile_deleted_successfully"] = await self.userprofile_ops.delete_userprofile(
                    user_uid, updater_uid, archive=archive
                )
            except Exception as e:
                error_msg = f"Failed to delete user profile for {user_uid}: {e}"
                self.logger.error(error_msg, exc_info=True)
                results["errors"].append(error_msg)

        # Delete UserStatus
        if delete_status:
            try:
                results["status_deleted_successfully"] = await self.userstatus_ops.delete_userstatus(
                    user_uid, updater_uid, archive=archive
                )
            except Exception as e:
                error_msg = f"Failed to delete user status for {user_uid}: {e}"
                self.logger.error(error_msg, exc_info=True)
                results["errors"].append(error_msg)

        # Delete Firebase Auth user
        if delete_auth_user:
            try:
                # Assuming delete_userauth also accepts an archive flag for consistency
                results["auth_deleted_successfully"] = await self.userauth_ops.delete_userauth(user_uid, archive=archive)
            except Exception as e:
                error_msg = f"Failed to delete Firebase Auth user {user_uid}: {e}"
                self.logger.error(error_msg, exc_info=True)
                results["errors"].append(error_msg)

        return results

    async def batch_delete_users(
        self,
        user_uids: List[str],
        delete_auth_user: bool,
        delete_profile: bool = True,
        delete_status: bool = True,
        updater_uid: str = "system_batch_deletion",
        archive: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Batch delete multiple users holistically.

        Args:
            user_uids: A list of user UIDs to delete.
            delete_auth_user: Whether to delete the Firebase Auth users.
            delete_profile: Whether to delete the UserProfile documents.
            delete_status: Whether to delete the UserStatus documents.
                updater_uid: The identifier of the entity performing the deletion.
            archive: Overrides the default archival behavior for all users in the batch.

        Returns:
            A dictionary where keys are user UIDs and values are deletion result dictionaries.
        """
        batch_results = {}
        for user_uid in user_uids:
            batch_results[user_uid] = await self.delete_user(
                user_uid=user_uid,
                delete_auth_user=delete_auth_user,
                delete_profile=delete_profile,
                delete_status=delete_status,
                updater_uid=updater_uid,
                archive=archive
            )
        return batch_results

    # Document-level batch operations

    async def batch_delete_user_core_docs(
        self,
        user_uids: List[str],
        updater_uid: str = "system_batch_deletion"
    ) -> Dict[str, Tuple[bool, bool, Optional[str]]]:
        """Batch delete multiple users' documents (profile and status only)"""
        batch_results: Dict[str, Tuple[bool, bool, Optional[str]]] = {}

        # Process sequentially to avoid overwhelming the database
        for user_uid in user_uids:
            self.logger.info("Batch deletion: Processing user_uid: %s", user_uid)
            item_deleted_by = f"{updater_uid}_batch_item_{user_uid}"

            try:
                # Use delete_user but only for documents, not auth
                result = await self.delete_user(
                    user_uid=user_uid,
                    delete_auth_user=False,  # Only delete documents
                    delete_profile=True,
                    delete_status=True,
                    updater_uid=item_deleted_by
                )

                batch_results[user_uid] = (
                    result["profile_deleted_successfully"],
                    result["status_deleted_successfully"],
                    result["errors"][0] if result["errors"] else None
                )
            except Exception as e:
                self.logger.error(f"Batch deletion failed for user {user_uid}: {e}", exc_info=True)
                batch_results[user_uid] = (False, False, str(e))

        return batch_results

    # Utility Methods

    async def user_exists_fully(self, user_uid: str) -> Dict[str, bool]:
        """Check if complete user exists (Auth, Profile, Status)"""
        return {
            "auth_exists": await self.userauth_ops.userauth_exists(user_uid),
            "profile_exists": (await self.userprofile_ops.get_userprofile(user_uid)) is not None,
            "status_exists": (await self.userstatus_ops.get_userstatus(user_uid)) is not None
        }

    async def validate_user_fully_enabled(
        self,
        user_uid: str,
        email_verified_must: bool = True,
        approved_must: bool = True,
        active_subscription_must: bool = True,
        valid_permissions_must: bool = True
    ) -> Dict[str, Any]:
        """
        Validate complete user integrity and operational readiness

        This method performs comprehensive validation to ensure a user is:
        - Complete (auth, profile, status exist)
        - Consistent (matching UIDs and usertypes across components)
        - Enabled (auth enabled, approved status)
        - Operational (active subscription, valid permissions)

        Args:
            user_uid: The UID of the user to validate
            email_verified_must: If True, email must be verified for full enablement (default: True)
            approved_must: If True, approval status must be APPROVED for full enablement (default: True)
            active_subscription_must: If True, active subscription required for full enablement (default: True)
            valid_permissions_must: If True, valid permissions required for full enablement (default: True)

        Returns:
            Dict with validation results including status, errors, and detailed checks
        """
        validation_results = {
            "user_uid": user_uid,
            "exists": {"auth_exists": False, "profile_exists": False, "status_exists": False},
            "is_complete": False,
            "missing_components": [],
            "validation_errors": [],
            "is_fully_enabled": False,
            "detailed_checks": {
                "auth_enabled": False,
                "email_verified": False,
                "approval_status_approved": False,
                "uid_consistency": False,
                "usertype_consistency": False,
                "has_active_subscription": False,
                "has_valid_permissions": False
            }
        }

        try:
            # Get all user components in parallel for efficiency
            userauth_result, userprofile_result, userstatus_result = await asyncio.gather(
                self.userauth_ops.get_userauth(user_uid, get_model=True),
                self.userprofile_ops.get_userprofile(user_uid),
                self.userstatus_ops.get_userstatus(user_uid),
                return_exceptions=True
            )

            # Handle exceptions and determine existence
            validation_results["exists"]["auth_exists"] = not isinstance(userauth_result, Exception) and userauth_result is not None
            validation_results["exists"]["profile_exists"] = not isinstance(userprofile_result, Exception) and userprofile_result is not None
            validation_results["exists"]["status_exists"] = not isinstance(userstatus_result, Exception) and userstatus_result is not None

            validation_results["is_complete"] = all(validation_results["exists"].values())
            validation_results["missing_components"] = [k for k, v in validation_results["exists"].items() if not v]

            # If user is not complete, skip detailed validations
            if not validation_results["is_complete"]:
                validation_results["validation_errors"].append("User is incomplete - missing components")
                return validation_results

            # If we have exceptions instead of models, handle them
            if isinstance(userauth_result, Exception):
                validation_results["validation_errors"].append(f"Auth retrieval error: {str(userauth_result)}")
                return validation_results
            if isinstance(userprofile_result, Exception):
                validation_results["validation_errors"].append(f"Profile retrieval error: {str(userprofile_result)}")
                return validation_results
            if isinstance(userstatus_result, Exception):
                validation_results["validation_errors"].append(f"Status retrieval error: {str(userstatus_result)}")
                return validation_results

            # Additional null checks - should not happen if exists checks passed, but for safety
            if not userauth_result or not userprofile_result or not userstatus_result:
                validation_results["validation_errors"].append("Retrieved user components are null despite existence checks passing")
                return validation_results

            # Type narrow the results to the actual model types after validation
            userauth_record = cast(UserAuth, userauth_result)  # Now known to be UserAuth
            userprofile = cast(UserProfile, userprofile_result)  # Now known to be UserProfile
            userstatus = cast(UserStatus, userstatus_result)  # Now known to be UserStatus

            # Now perform detailed validations with valid models

            # 1. Auth enabled validation (uses the UserAuth model disabled field)
            validation_results["detailed_checks"]["auth_enabled"] = not userauth_record.disabled
            if userauth_record.disabled:
                validation_results["validation_errors"].append("Firebase Auth user is disabled")

            # 2. Email verification validation
            validation_results["detailed_checks"]["email_verified"] = userauth_record.email_verified
            if email_verified_must and not userauth_record.email_verified:
                validation_results["validation_errors"].append("User email is not verified")

            # 3. UID consistency validation
            auth_uid = getattr(userauth_record, 'uid', None) or getattr(userauth_record, 'user_uid', None)
            uids_consistent = (
                auth_uid == user_uid and
                userprofile.user_uid == user_uid and
                userstatus.user_uid == user_uid
            )
            validation_results["detailed_checks"]["uid_consistency"] = uids_consistent
            if not uids_consistent:
                validation_results["validation_errors"].append(
                    f"UID inconsistency detected - Auth: {auth_uid}, "
                    f"Profile: {userprofile.user_uid}, Status: {userstatus.user_uid}"
                )

            # 4. Usertype consistency validation
            userauth_claims = userauth_record.custom_claims or {}
            userauth_primary = userauth_claims.get("primary_usertype")
            userauth_secondary = userauth_claims.get("secondary_usertypes", [])

            userprofile_primary_str = str(userprofile.primary_usertype)
            userprofile_secondary_strs = [str(ut) for ut in userprofile.secondary_usertypes]

            usertypes_consistent = (
                userauth_primary == userprofile_primary_str and
                set(userauth_secondary) == set(userprofile_secondary_strs)
            )
            validation_results["detailed_checks"]["usertype_consistency"] = usertypes_consistent
            if not usertypes_consistent:
                validation_results["validation_errors"].append(
                    f"Usertype inconsistency - Auth primary: {userauth_primary}, "
                    f"Profile primary: {userprofile_primary_str}, "
                    f"Auth secondary: {userauth_secondary}, "
                    f"Profile secondary: {userprofile_secondary_strs}"
                )

            # 5. Approval status validation
            user_approval_status = userauth_claims.get("user_approval_status")
            approval_approved = user_approval_status == "APPROVED"
            validation_results["detailed_checks"]["approval_status_approved"] = approval_approved
            if approved_must and not approval_approved:
                validation_results["validation_errors"].append(
                    f"User approval status is not APPROVED (current: {user_approval_status})"
                )

            # 6. Active subscription validation - use UserStatus methods
            has_active_subscription = userstatus.is_subscription_active()
            validation_results["detailed_checks"]["has_active_subscription"] = has_active_subscription
            if active_subscription_must and not has_active_subscription:
                validation_results["validation_errors"].append("User has no active subscription")

            # 7. Valid permissions validation - use UserStatus get_valid_permissions method
            valid_permissions = userstatus.get_valid_permissions()
            has_valid_permissions = len(valid_permissions) > 0

            validation_results["detailed_checks"]["has_valid_permissions"] = has_valid_permissions
            if valid_permissions_must and not has_valid_permissions:
                validation_results["validation_errors"].append("User has no valid (non-expired) IAM permissions")

            # Overall validation result - only consider checks that are required based on flags
            required_checks = []
            required_checks.append(validation_results["detailed_checks"]["auth_enabled"])  # Always required
            required_checks.append(validation_results["detailed_checks"]["uid_consistency"])  # Always required
            required_checks.append(validation_results["detailed_checks"]["usertype_consistency"])  # Always required

            if email_verified_must:
                required_checks.append(validation_results["detailed_checks"]["email_verified"])
            if approved_must:
                required_checks.append(validation_results["detailed_checks"]["approval_status_approved"])
            if active_subscription_must:
                required_checks.append(validation_results["detailed_checks"]["has_active_subscription"])
            if valid_permissions_must:
                required_checks.append(validation_results["detailed_checks"]["has_valid_permissions"])

            validation_results["is_fully_enabled"] = all(required_checks)

        except Exception as e:
            validation_results["validation_errors"].append(f"Validation process error: {str(e)}")

        return validation_results

    async def update_user_usertype(
        self,
        user_uid: str,
        primary_usertype: Optional['IAMUserType'] = None,
        secondary_usertypes: Optional[List['IAMUserType']] = None,
        updater_uid: str = "system_usertype_update"
    ) -> Tuple[UserProfile, Dict[str, Any]]:
        """
        Update user's primary and/or secondary usertypes efficiently across UserProfile and Firebase Auth.

        This method leverages existing operations to update usertypes efficiently without
        unnecessary fetching and model conversions.

        Args:
            user_uid: The UID of the user to update
            primary_usertype: New primary usertype (optional, keeps existing if None)
            secondary_usertypes: New secondary usertypes list (optional, keeps existing if None)
            updater_uid: Who is performing this update

        Returns:
            Tuple of (updated_userprofile, updated_custom_claims)
        """
        try:
            self.logger.info("Updating usertypes for user: %s", user_uid)

            # Build update payloads
            profile_update_data = {}
            claims_update_data = {}

            if primary_usertype is not None:
                profile_update_data['primary_usertype'] = primary_usertype
                claims_update_data['primary_usertype'] = str(primary_usertype)

            if secondary_usertypes is not None:
                profile_update_data['secondary_usertypes'] = secondary_usertypes
                claims_update_data['secondary_usertypes'] = [str(ut) for ut in secondary_usertypes]

            # Nothing to update
            if not profile_update_data:
                current_profile = await self.userprofile_ops.get_userprofile(user_uid)
                if not current_profile:
                    raise UserCreationError(f"User profile not found: {user_uid}")
                user_record = await self.userauth_ops.get_userauth(user_uid)
                return current_profile, user_record.custom_claims if user_record else {}

            # Update both in parallel for efficiency
            await asyncio.gather(
                self.userprofile_ops.update_userprofile(user_uid, profile_update_data, updater_uid),
                self.userauth_ops.set_userauth_custom_claims(user_uid, claims_update_data)
            )

            # Get updated data for return
            updated_profile, user_record = await asyncio.gather(
                self.userprofile_ops.get_userprofile(user_uid),
                self.userauth_ops.get_userauth(user_uid)
            )

            if not updated_profile:
                raise UserCreationError(f"Failed to retrieve updated user profile: {user_uid}")

            updated_claims = user_record.custom_claims if user_record else {}

            self.logger.info("Successfully updated usertypes for user: %s", user_uid)
            return updated_profile, updated_claims

        except Exception as e:
            self.logger.error("Failed to update usertypes for user %s: %s", user_uid, e)
            raise UserCreationError(f"Failed to update usertypes for user {user_uid}: {str(e)}") from e
