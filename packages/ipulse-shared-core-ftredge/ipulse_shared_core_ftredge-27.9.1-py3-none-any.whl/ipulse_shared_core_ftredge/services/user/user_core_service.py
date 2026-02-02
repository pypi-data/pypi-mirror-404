"""
Enhanced UserCoreService - Comprehensive user management orchestration

This service orchestrates all user-related operations by composing specialized
operation classes for different concerns:
- Firebase Auth User Management
- User Profile and Status Management
- User Deletion Operations
- Subscription Management
- IAM Management
- Configuration by UserType

Can be used by Firebase Cloud Functions, admin tools, service APIs, admin tools, and tests.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from google.cloud import firestore
from firebase_admin.auth import UserRecord
from ipulse_shared_base_ftredge import ApprovalStatus, IAMUnit, IAMUserType
from ...models import UserProfile, UserStatus, UserAuth, UserAuthCreateNew, UserSubscription, UserType, SubscriptionPlan, UserPermission


# Import specialized operation classes
from .userprofile_operations import UserprofileOperations
from .userstatus_operations import UserstatusOperations
from .user_subscription_operations import UsersubscriptionOperations
from .user_permissions_operations import UserpermissionsOperations
from .userauth_operations import UserauthOperations
from .user_multistep_operations import UsermultistepOperations
from .user_charging_operations import UserChargingOperations
from ..catalog.catalog_usertype_service import CatalogUserTypeService
from ..catalog.catalog_subscriptionplan_service import CatalogSubscriptionPlanService


class UserCoreService:
    """
    Enhanced UserCoreService - Orchestrates all user-related operations

    This service provides a unified interface for all user management operations
    by composing specialized operation classes. It maintains backward compatibility
    while providing enhanced functionality and better organization.
    """

    def __init__(
        self,
        firestore_client: firestore.Client,
        logger: Optional[logging.Logger] = None,
        default_timeout: float = 10.0,
        profile_collection: Optional[str] = None,
        status_collection: Optional[str] = None,
        bypass_credit_check: bool = False
    ):
        """
        Initialize the Enhanced UserCoreService

        Args:
            firestore_client: Initialized Firestore client
            logger: Optional logger instance
            default_timeout: Default timeout for Firestore operations
            profile_collection: Collection name for user profiles
            status_collection: Collection name for user statuses
            bypass_credit_check: If True, bypasses credit checks for debugging/testing
        """
        self.db = firestore_client
        self.logger = logger or logging.getLogger(__name__)
        self.timeout = default_timeout

        self.profile_collection_name = profile_collection or UserProfile.get_collection_name()
        self.status_collection_name = status_collection or UserStatus.get_collection_name()

        # Initialize specialized operation classes in dependency order
        self.userauth_ops = UserauthOperations(
            logger=self.logger
        )

        self.userprofile_ops = UserprofileOperations(
            firestore_client=self.db,
            logger=self.logger,
            timeout=self.timeout,
            profile_collection=self.profile_collection_name,
        )

        self.userstatus_ops = UserstatusOperations(
            firestore_client=self.db,
            logger=self.logger,
            timeout=self.timeout,
            status_collection=self.status_collection_name,
        )

        self.usepermission_ops = UserpermissionsOperations(
            userstatus_ops=self.userstatus_ops,
            logger=self.logger
        )

        self.user_subscription_ops = UsersubscriptionOperations(
            firestore_client=self.db,
            userstatus_ops=self.userstatus_ops,
            permissions_ops=self.usepermission_ops,
            logger=self.logger,
            timeout=self.timeout
        )

        # Initialize charging operations
        self.user_charging_ops = UserChargingOperations(
            userstatus_ops=self.userstatus_ops,
            logger=self.logger,
            timeout=self.timeout,
            bypass_credit_check=bypass_credit_check
        )

        # Initialize catalog services
        self.catalog_usertype_service = CatalogUserTypeService(
            firestore_client=self.db,
            logger=self.logger
        )

        self.catalog_subscriptionplan_service = CatalogSubscriptionPlanService(
            firestore_client=self.db,
            logger=self.logger
        )

        # Initialize multistep operations last as it depends on other operations
        self.usermultistep_ops = UsermultistepOperations(
            userprofile_ops=self.userprofile_ops,
            userstatus_ops=self.userstatus_ops,
            userauth_ops=self.userauth_ops,
            usersubscription_ops=self.user_subscription_ops,
            useriam_ops=self.usepermission_ops,
            catalog_usertype_service=self.catalog_usertype_service,
            catalog_subscriptionplan_service=self.catalog_subscriptionplan_service,
            logger=self.logger
        )


    ######################################################################
    ######################### Complete User Creation ####################
    ######################################################################

    async def create_user_from_models(
        self,
        userprofile: UserProfile,
        userstatus: UserStatus,
        userauth: Optional[UserAuthCreateNew] = None,
        validate_userauth_consistency: bool = False,
        validate_userauth_exists: bool = False
    ) -> Tuple[str, UserProfile, UserStatus]:
        """
        Create a complete user from ready UserAuth, UserProfile, and UserStatus models.

        Delegates to UsermultistepOperations for the actual creation.
        """
        return await self.usermultistep_ops.create_user_from_models(
            userprofile=userprofile,
            userstatus=userstatus,
            userauth=userauth,
            validate_userauth_consistency=validate_userauth_consistency,
            validate_userauth_exists=validate_userauth_exists
        )

    async def create_user_from_manual_usertype(
        self,
        userprofile: UserProfile,
        usertype: UserType,
        userauth: Optional[UserAuthCreateNew] = None,
        extra_insight_credits_override: Optional[int] = None,
        voting_credits_override: Optional[int] = None,
        subscriptionplan_id_override: Optional[str] = None,
        created_by: Optional[str] = None,
        apply_usertype_associated_subscriptionplan: bool = True,
        validate_userauth_consistency: bool = False,
        validate_userauth_exists: bool = False
    ) -> Tuple[str, UserProfile, UserStatus]:
        """
        Create a complete user with manual UserType configuration.

        Delegates to UsermultistepOperations for the actual creation.
        """
        return await self.usermultistep_ops.create_user_from_manual_usertype(
            userprofile=userprofile,
            usertype=usertype,
            userauth=userauth,
            extra_insight_credits_override=extra_insight_credits_override,
            voting_credits_override=voting_credits_override,
            subscriptionplan_id_override=subscriptionplan_id_override,
            creator_uid=created_by,
            apply_usertype_associated_subscriptionplan=apply_usertype_associated_subscriptionplan,
            validate_userauth_consistency=validate_userauth_consistency,
            validate_userauth_exists=validate_userauth_exists
        )

    async def create_user_from_catalog_usertype(
        self,
        usertype_id: str,
        userprofile: UserProfile,
        userauth: Optional[UserAuthCreateNew] = None,
        extra_insight_credits_override: Optional[int] = None,
        voting_credits_override: Optional[int] = None,
        subscriptionplan_id_override: Optional[str] = None,
        created_by: Optional[str] = None,
        apply_usertype_associated_subscriptionplan: bool = True,
        validate_userauth_consistency: bool = False,
        validate_userauth_exists: bool = False
    ) -> Tuple[str, UserProfile, UserStatus]:
        """
        Create a complete user based on UserType catalog configuration.

        Delegates to UsermultistepOperations for the actual creation.
        """
        return await self.usermultistep_ops.create_user_from_catalog_usertype(
            usertype_id=usertype_id,
            userprofile=userprofile,
            userauth=userauth,
            extra_insight_credits_override=extra_insight_credits_override,
            voting_credits_override=voting_credits_override,
            subscriptionplan_id_override=subscriptionplan_id_override,
            creator_uid=created_by,
            apply_usertype_associated_subscriptionplan=apply_usertype_associated_subscriptionplan,
            validate_userauth_consistency=validate_userauth_consistency,
            validate_userauth_exists=validate_userauth_exists
        )

    ######################################################################
    ######################### User Validation ############################
    ######################################################################

    async def user_exists_fully(self, user_uid: str) -> Dict[str, bool]:
        """Check if complete user exists (Auth, Profile, Status)"""
        return await self.usermultistep_ops.user_exists_fully(user_uid=user_uid)

    async def validate_user_fully_enabled(
        self,
        user_uid: str,
        email_verified_must: bool = True,
        approved_must: bool = True,
        active_subscription_must: bool = True,
        valid_permissions_must: bool = True
    ) -> Dict[str, Any]:
        """
        Validate complete user integrity and operational readiness with configurable requirements.

        Delegates to UsermultistepOperations for comprehensive validation.
        """
        return await self.usermultistep_ops.validate_user_fully_enabled(
            user_uid=user_uid,
            email_verified_must=email_verified_must,
            approved_must=approved_must,
            active_subscription_must=active_subscription_must,
            valid_permissions_must=valid_permissions_must
        )

    ######################################################################
    ######################### User Deletion ##############################
    ######################################################################

    async def delete_user(
        self,
        user_uid: str,
        updater_uid: str,
        delete_auth_user: bool = True,
        delete_profile: bool = True,
        delete_status: bool = True,
        archive: bool = True
    ) -> Dict[str, Any]:
        """
        Delete a user holistically, including their auth, profile, and status.

        Delegates to UsermultistepOperations for the actual deletion.
        """
        return await self.usermultistep_ops.delete_user(
            user_uid=user_uid,
            delete_auth_user=delete_auth_user,
            delete_profile=delete_profile,
            delete_status=delete_status,
            updater_uid=updater_uid,
            archive=archive
        )

    async def batch_delete_users(
        self,
        user_uids: List[str],
        updater_uid: str,
        delete_auth_user: bool,
        delete_profile: bool = True,
        delete_status: bool = True,
        archive: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Batch delete multiple users holistically.

        Delegates to UsermultistepOperations for the actual deletion.
        """
        return await self.usermultistep_ops.batch_delete_users(
            user_uids=user_uids,
            delete_auth_user=delete_auth_user,
            delete_profile=delete_profile,
            delete_status=delete_status,
            updater_uid=updater_uid,
            archive=archive
        )

    ######################################################################
    ######################### UserAuth Operations ########################
    ######################################################################

    async def create_userauth(self, userauth: UserAuthCreateNew) -> str:
        """Create a Firebase Auth user"""
        return await self.userauth_ops.create_userauth(user_auth=userauth)

    async def get_userauth(self, user_uid: str, get_model: bool = False) -> Union[UserRecord, UserAuth, None]:
        """Get Firebase Auth user details"""
        return await self.userauth_ops.get_userauth(user_uid=user_uid, get_model=get_model)

    async def get_userauth_by_email(self, email: str, get_model: bool = False) -> Union[UserRecord, UserAuth, None]:
        """Get Firebase Auth user by email"""
        return await self.userauth_ops.get_userauth_by_email(email=email, get_model=get_model)

    async def userauth_exists(self, user_uid: str) -> bool:
        """Check if Firebase Auth user exists"""
        return await self.userauth_ops.userauth_exists(user_uid=user_uid)

    async def update_userauth(
        self,
        user_uid: str,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
        password: Optional[str] = None,
        email_verified: Optional[bool] = None,
        disabled: Optional[bool] = None
    ) -> UserRecord:
        """Update Firebase Auth user"""
        return await self.userauth_ops.update_userauth(
            user_uid=user_uid,
            email=email,
            display_name=display_name,
            password=password,
            email_verified=email_verified,
            disabled=disabled
        )

    async def delete_userauth(self, user_uid: str, archive: bool = True) -> bool:
        """Delete Firebase Auth user"""
        return await self.userauth_ops.delete_userauth(user_uid=user_uid, archive=archive)

    async def set_userauth_custom_claims(self, user_uid: str, custom_claims: Dict[str, Any], merge_with_existing: bool = False) -> bool:
        """Set custom claims for Firebase Auth user"""
        return await self.userauth_ops.set_userauth_custom_claims(
            user_uid=user_uid,
            custom_claims=custom_claims,
            merge_with_existing=merge_with_existing
        )

    async def enable_userauth(self, user_uid: str, notes: str = "") -> bool:
        """Enable Firebase Auth user"""
        return await self.userauth_ops.enable_userauth(user_uid=user_uid, user_notes=notes)

    async def disable_userauth(self, user_uid: str, notes: str = "") -> bool:
        """Disable Firebase Auth user"""
        return await self.userauth_ops.disable_userauth(user_uid=user_uid, user_notes=notes)

    async def revoke_refresh_tokens(self, user_uid: str) -> bool:
        """Revoke all refresh tokens for a user"""
        return await self.userauth_ops.revoke_refresh_tokens(user_uid=user_uid)

    async def set_user_approval_status(self, user_uid: str, status: ApprovalStatus, notes: str = "") -> bool:
        """Set user approval status in custom claims"""
        return await self.userauth_ops.set_user_approval_status(user_uid=user_uid, approval_status=status, updated_by=notes)

    # Token and Security Operations

    async def create_custom_token(
        self,
        user_uid: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """Creates a custom token for a user with optional additional claims"""
        return await self.userauth_ops.create_custom_token(
            user_uid=user_uid,
            additional_claims=additional_claims
        )

    async def verify_id_token(
        self,
        token: str,
        check_revoked: bool = False
    ) -> Dict[str, Any]:
        """Verifies an ID token and returns the token claims"""
        return await self.userauth_ops.verify_id_token(
            token=token,
            check_revoked=check_revoked
        )

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
        return await self.userauth_ops.get_user_auth_token(
            email=email,
            password=password,
            api_key=api_key
        )

    async def generate_password_reset_link(
        self,
        email: str,
        action_code_settings: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generates a password reset link for a user"""
        return await self.userauth_ops.generate_password_reset_link(
            email=email,
            action_code_settings=action_code_settings
        )

    async def generate_email_verification_link(
        self,
        email: str,
        action_code_settings: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generates an email verification link for a user"""
        return await self.userauth_ops.generate_email_verification_link(
            email=email,
            action_code_settings=action_code_settings
        )

    ######################################################################
    ######################### UserProfile Operations ####################
    ######################################################################

    async def create_userprofile(self, userprofile: UserProfile, creator_uid: Optional[str] = None) -> UserProfile:
        """Create a UserProfile document"""
        return await self.userprofile_ops.create_userprofile(userprofile=userprofile, creator_uid=creator_uid)

    async def get_userprofile(self, user_uid: str) -> Optional[UserProfile]:
        """Get a UserProfile by user UID"""
        return await self.userprofile_ops.get_userprofile(user_uid=user_uid)

    async def update_userprofile(self, user_uid: str, updates: Dict[str, Any], updater_uid: str) -> UserProfile:
        """Update a UserProfile"""
        return await self.userprofile_ops.update_userprofile(user_uid=user_uid, profile_data=updates, updater_uid=updater_uid)

    async def delete_userprofile(self, user_uid: str, updater_uid: str, archive: bool = True) -> bool:
        """Delete a UserProfile"""
        return await self.userprofile_ops.delete_userprofile(user_uid=user_uid, updater_uid=updater_uid, archive=archive)

    async def userprofile_exists(self, user_uid: str) -> bool:
        """Check if a UserProfile exists"""
        return await self.userprofile_ops.userprofile_exists(user_uid=user_uid)

    async def validate_userprofile_data(
        self,
        profile_data: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, list[str]]:
        """Validate UserProfile data"""
        return await self.userprofile_ops.validate_userprofile_data(profile_data=profile_data)

    ######################################################################
    ######################### UserStatus Operations ######################
    ######################################################################

    async def create_userstatus(self, userstatus: UserStatus, creator_uid: Optional[str] = None) -> UserStatus:
        """Create a UserStatus document"""
        return await self.userstatus_ops.create_userstatus(userstatus=userstatus, creator_uid=creator_uid)

    async def get_userstatus(self, user_uid: str) -> Optional[UserStatus]:
        """Get a UserStatus by user UID"""
        return await self.userstatus_ops.get_userstatus(user_uid=user_uid)

    async def update_userstatus(self, user_uid: str, updates: Dict[str, Any], updater_uid: str) -> UserStatus:
        """Update a UserStatus"""
        return await self.userstatus_ops.update_userstatus(user_uid=user_uid, status_data=updates, updater_uid=updater_uid)

    async def delete_userstatus(self, user_uid: str, updater_uid: str, archive: bool = True) -> bool:
        """Delete a UserStatus"""
        return await self.userstatus_ops.delete_userstatus(user_uid=user_uid, updater_uid=updater_uid, archive=archive)

    async def userstatus_exists(self, user_uid: str) -> bool:
        """Check if a UserStatus exists"""
        return await self.userstatus_ops.userstatus_exists(user_uid=user_uid)

    async def validate_userstatus_data(
        self,
        status_data: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, list[str]]:
        """Validate UserStatus data"""
        return await self.userstatus_ops.validate_userstatus_data(status_data=status_data)

    async def validate_and_cleanup_user_permissions(
        self,
        user_uid: str,
        updater_uid: str
    ) -> int:
        """Validate and cleanup expired permissions for a user"""
        return await self.userstatus_ops.validate_and_cleanup_user_permissions(user_uid=user_uid, updater_uid=updater_uid)

    ######################################################################
    ######################### Subscription Operations ###################
    ######################################################################

    async def fetch_subscriptionplan_and_apply_subscription_to_user(
        self,
        user_uid: str,
        plan_id: str,
        updater_uid: str,
        source: str = "user_core_service",
        granted_at: Optional[datetime] = None,
        auto_renewal_end: Optional[datetime] = None
    ) -> UserSubscription:
        """Fetch a subscription plan from catalog and apply to user"""
        return await self.user_subscription_ops.fetch_subscriptionplan_and_apply_subscription_to_user(
            user_uid=user_uid,
            plan_id=plan_id,
            updater_uid=updater_uid,
            source=source,
            granted_at=granted_at,
            auto_renewal_end=auto_renewal_end
        )

    async def apply_subscriptionplan_to_user(
        self,
        user_uid: str,
        subscriptionplan: SubscriptionPlan,
        updater_uid: str,
        source: str = "user_core_service",
        granted_at: Optional[datetime] = None,
        auto_renewal_end: Optional[datetime] = None
    ) -> UserSubscription:
        """Apply a subscription plan directly to user (plan already fetched)"""
        return await self.user_subscription_ops.apply_subscriptionplan(
            user_uid=user_uid,
            subscriptionplan=subscriptionplan,
            updater_uid=updater_uid,
            source=source,
            granted_at=granted_at,
            auto_renewal_end=auto_renewal_end
        )

    async def cancel_user_subscription(self, user_uid: str, updater_uid: str) -> bool:
        """Cancel a user's active subscription"""
        return await self.user_subscription_ops.cancel_user_subscription(user_uid=user_uid, updater_uid=updater_uid)

    async def get_user_active_subscription(self, user_uid: str) -> Optional[UserSubscription]:
        """Get a user's active subscription"""
        return await self.user_subscription_ops.get_user_active_subscription(user_uid=user_uid)

    async def update_user_subscription(
        self,
        user_uid: str,
        subscription_data: Dict[str, Any],
        updater_uid: str
    ) -> Optional[UserSubscription]:
        """Update a user's subscription"""
        return await self.user_subscription_ops.update_user_subscription(user_uid=user_uid, subscription_updates=subscription_data, updater_uid=updater_uid)

    async def downgrade_user_subscription_to_fallback_subscriptionplan(
        self,
        user_uid: str,
        reason: str = "subscription_expired"
    ) -> Optional[UserSubscription]:
        """Downgrade user subscription to fallback plan"""
        return await self.user_subscription_ops.downgrade_user_subscription_to_fallback_subscriptionplan(
            user_uid=user_uid, reason=reason
        )

    ######################################################################
    ######################### IAM/Permissions Operations ################
    ######################################################################

    async def add_permission_to_user(
        self,
        user_uid: str,
        permission: UserPermission,
        updater_uid: str
    ) -> bool:
        """Add a permission to a user (returns success boolean)"""
        return await self.usepermission_ops.add_permission_to_user(user_uid=user_uid, permission=permission, updater_uid=updater_uid)

    async def get_permissions_of_user(self, user_uid: str) -> List[UserPermission]:
        """Get a user's permissions"""
        return await self.usepermission_ops.get_permissions_of_user(user_uid=user_uid)

    async def remove_all_permissions_from_user(self, user_uid: str, updater_uid: str, source: Optional[str] = None) -> int:
        """Remove all permissions from a user"""
        return await self.usepermission_ops.remove_all_permissions_from_user(user_uid=user_uid, source=source, updater_uid=updater_uid)

    async def remove_permission_from_user(
        self,
        user_uid: str,
        domain: Optional[str] = None,
        permission_type: Optional[IAMUnit] = None,
        permission_name: Optional[str] = None,
        source: Optional[str] = None,
        updater_uid: Optional[str] = None
    ) -> bool:
        """Remove specific permission(s) from a user based on filter criteria"""
        return await self.usepermission_ops.remove_permission_from_user(
            user_uid=user_uid,
            domain=domain,
            permission_type=permission_type,
            permission_name=permission_name,
            source=source,
            updater_uid=updater_uid
        )

    async def cleanup_expired_permissions_of_user(
        self,
        user_uid: str,
        updater_uid: str,
        iam_unit_type: Optional[IAMUnit] = None
    ) -> int:
        """Remove expired permissions from a user"""
        return await self.usepermission_ops.cleanup_expired_permissions_of_user(user_uid=user_uid, iam_unit_type=iam_unit_type, updater_uid=updater_uid)

    async def get_bulk_users_with_permission(
        self,
        domain: str,
        iam_unit_type: IAMUnit,
        permission_ref: str,
        limit: int = 100,
        valid_only: bool = True
    ) -> List[str]:
        """Get bulk users who have a specific permission"""
        return await self.usepermission_ops.get_bulk_users_with_permission(
            domain=domain,
            iam_unit_type=iam_unit_type,
            permission_ref=permission_ref,
            limit=limit,
            valid_only=valid_only
        )

    async def update_user_usertype(
        self,
        user_uid: str,
        primary_usertype: Optional['IAMUserType'] = None,
        secondary_usertypes: Optional[List['IAMUserType']] = None,
        updater_uid: str = "system_usertype_update"
    ) -> Tuple[UserProfile, Dict[str, Any]]:
        """
        Update user's primary and/or secondary usertypes efficiently across UserProfile and Firebase Auth.

        Args:
            user_uid: The UID of the user to update
            primary_usertype: New primary usertype (optional, keeps existing if None)
            secondary_usertypes: New secondary usertypes list (optional, keeps existing if None)
            updater_uid: Who is performing this update

        Returns:
            Tuple of (updated_userprofile, updated_custom_claims)
        """
        return await self.usermultistep_ops.update_user_usertype(
            user_uid=user_uid,
            primary_usertype=primary_usertype,
            secondary_usertypes=secondary_usertypes,
            updater_uid=updater_uid
        )

    ######################################################################
    ####################### User Charging Operations ####################
    ######################################################################

    async def verify_user_has_enough_credits(
        self,
        user_uid: str,
        required_credits: float,
        credits_extracted_from_authz_response: Optional[Dict[str, float]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify if user has sufficient credits for a resource.
        Delegates to UserChargingOperations.
        """
        return await self.user_charging_ops.verify_enough_credits(
            user_uid=user_uid,
            required_credits_for_resource=required_credits,
            credits_extracted_from_authz_response=credits_extracted_from_authz_response
        )

    async def debit_credits_from_user_transaction(
        self,
        user_uid: str,
        credits_to_take: float,
        operation_details: str
    ) -> Tuple[bool, Optional[Dict[str, float]]]:
        """
        Charge credits from user account using Firestore transaction.
        Delegates to UserChargingOperations.
        """
        return await self.user_charging_ops.debit_credits_transaction(
            user_uid=user_uid,
            credits_to_take=credits_to_take,
            operation_details=operation_details
        )

    async def credit_credits_to_user_transaction(
        self,
        user_uid: str,
        extra_credits_to_add: float = 0.0,
        subscription_credits_to_add: float = 0.0,
        reason: str = "",
        updater_uid: str = "system"
    ) -> Tuple[bool, Optional[Dict[str, float]]]:
        """
        Add credits to user account (extra and/or subscription credits).
        Delegates to UserChargingOperations.
        """
        return await self.user_charging_ops.credit_credits_transaction(
            user_uid=user_uid,
            extra_credits_to_add=extra_credits_to_add,
            subscription_credits_to_add=subscription_credits_to_add,
            reason=reason,
            updater_uid=updater_uid
        )

    async def process_single_item_charge(
        self,
        user_uid: str,
        item_id: str,
        get_cost_func,
        credits_extracted_from_authz_response: Optional[Dict[str, float]] = None,
        operation_description: str = "Resource access"
    ) -> Dict[str, Any]:
        """
        Process credit check and charging for a single item.
        Delegates to UserChargingOperations.
        """
        return await self.user_charging_ops.process_single_item_charging(
            user_uid=user_uid,
            item_id=item_id,
            get_cost_func=get_cost_func,
            credits_extracted_from_authz_response=credits_extracted_from_authz_response,
            operation_description=operation_description
        )

    async def process_batch_charge(
        self,
        user_uid: str,
        items: List[Dict[str, Any]],
        credits_extracted_from_authz_response: Optional[Dict[str, float]] = None,
        operation_description: str = "Batch resource access"
    ) -> Dict[str, Any]:
        """
        Process credit check and charging for batch items.
        Delegates to UserChargingOperations.
        """
        return await self.user_charging_ops.process_batch_items_charging(
            user_uid=user_uid,
            items=items,
            credits_extracted_from_authz_response=credits_extracted_from_authz_response,
            operation_description=operation_description
        )

    ######################################################################
    ####################### User Subscription/Status Review #############
    ######################################################################

    async def review_and_clean_active_subscription_credits_and_permissions(
        self,
        user_uid: str,
        updater_uid: str = "system_review",
        review_auto_renewal: bool = True,
        apply_fallback: bool = True,
        clean_expired_permissions: bool = True,
        review_credits: bool = True
    ) -> Dict[str, Any]:
        """
        Orchestrate a comprehensive review and cleanup of a user's active subscription, credits, and permissions.
        Delegates to UserstatusOperations for the actual logic.
        """
        return await self.userstatus_ops.review_and_clean_active_subscription_credits_and_permissions(
            user_uid=user_uid,
            updater_uid=updater_uid,
            review_auto_renewal=review_auto_renewal,
            apply_fallback=apply_fallback,
            clean_expired_permissions=clean_expired_permissions,
            review_credits=review_credits
        )

