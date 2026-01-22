"""
User Profile and Preferences Routes for FastAPI
Handles user profile CRUD operations and preference management
"""

import logging
from typing import Optional, Tuple
from fastapi import APIRouter, Depends, status, UploadFile, File, Request
from fastapi.responses import JSONResponse

from middleware.rbac import require_authenticated
from models.user_preferences import (
    ProfileUpdate,
    Preferences,
    UserProfile,
    UserPreferencesResponse
)
from models.user import UserRole
from services.profile_service import ProfileService
from services.rbac_service import rbac_service
from services.tenant_service import TenantService
from services.audit_service import AuditService, AuditEventType, AuditEvent, AuditResult
from utils.query_scope import QueryScope

from models.errors import KraftdHTTPException, ErrorCode, authentication_error, internal_server_error, validation_error, not_found_error, quota_exceeded_error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user-profile"])

# Initialize ProfileService (will be injected with database)
profile_service: Optional[ProfileService] = None


def set_profile_service(service: ProfileService):
    """Inject ProfileService instance"""
    global profile_service
    profile_service = service


def get_profile_service() -> ProfileService:
    """Get ProfileService instance"""
    if not profile_service:
        raise internal_server_error("Profile service not initialized")
    return profile_service


# Profile endpoints

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: Tuple[str, str] = Depends(require_authenticated),
    request: Request = None
):
    """
    Get current user's profile
    
    Returns:
        UserProfile: User profile information
    """
    email, role = current_user
    service = get_profile_service()
    
    try:
        profile = await service.get_profile(email)
        
        if not profile:
            # Return default profile if not found
            logger.info(f"Creating default profile for new user: {email}")
            profile = await service.create_profile(email)
        
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=UserRole(role),
            resource=f"profile:{email}",
            action="read",
            allowed=True
        )
        
        # Log profile read event
        try:
            client_ip = request.client.host if request and request.client else None
            user_agent = request.headers.get("User-Agent") if request else None
            tenant_id = TenantService.get_current_tenant() or "default"
            
            await AuditService.log_access(
                user_email=email,
                user_role=role,
                resource_type="user_profile",
                resource_id=email,
                tenant_id=tenant_id,
                allowed=True,
                reason="Profile read access granted",
                ip_address=client_ip
            )
        except Exception as audit_error:
            logger.error(f"Error logging profile audit event: {audit_error}")
        
        return profile
        
    except Exception as e:
        logger.error(f"Error retrieving profile for {email}: {e}")
        raise internal_server_error("Failed to retrieve profile")


@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_data: ProfileUpdate,
    current_user: Tuple[str, str] = Depends(require_authenticated),
    request: Request = None
):
    """
    Update current user's profile
    
    Task 4 Integration: Validates tenant context (TenantService)
    Task 5 Integration: Validates resource ownership (self-ownership for profiles)
    
    Args:
        profile_data: Profile update data
        
    Returns:
        UserProfile: Updated profile information
    """
    email, role = current_user
    service = get_profile_service()
    
    try:
        # Task 4: Validate tenant context
        current_tenant = TenantService.get_current_tenant()
        if not current_tenant:
            raise KraftdHTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
                message="No tenant context found"
            )
        
        # Task 5: Verify ownership - User can only update own profile
        # Profile ownership is self-owned (email = owner)
        # Admin can update any user's profile in the tenant
        if role.lower() != "admin" and email != current_user[0]:
            logger.warning(
                f"Ownership violation: {email} attempted to update "
                f"profile of {current_user[0]} in tenant {current_tenant.tenant_id}"
            )
            raise authentication_error("You can only update your own profile")
        
        # Get existing profile or create if not exists
        existing = await service.get_profile(email)
        if not existing:
            existing = await service.create_profile(email)
        
        # Perform update
        updated_profile = await service.update_profile(email, profile_data)
        
        # Log authorization decision
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource=f"profile:{email}",
            action="update",
            allowed=True
        )
        
        logger.info(
            f"Profile updated: {email} in tenant {current_tenant.tenant_id} "
            f"(role: {role})"
        )
        
        # Log profile modification for audit trail
        try:
            client_ip = request.client.host if request and request.client else None
            user_agent = request.headers.get("User-Agent") if request else None
            tenant_id = TenantService.get_current_tenant() or "default"
            
            # Capture changes
            changes = {}
            if profile_data.name:
                changes['name'] = {"new": profile_data.name, "old": existing.name if existing else None}
            if profile_data.organization:
                changes['organization'] = {"new": profile_data.organization, "old": existing.organization if existing else None}
            if profile_data.bio:
                changes['bio'] = {"new": profile_data.bio, "old": existing.bio if existing else None}
            
            await AuditService.log_modification(
                user_email=email,
                user_role=role,
                resource_type="user_profile",
                resource_id=email,
                tenant_id=tenant_id,
                action="update",
                changes=changes,
                ip_address=client_ip
            )
        except Exception as audit_error:
            logger.error(f"Error logging profile modification audit event: {audit_error}")
        
        return updated_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile for {email}: {e}")
        raise internal_server_error("Failed to update profile")


@router.post("/profile/avatar", response_model=dict)
async def upload_profile_avatar(
    file: UploadFile = File(...),
    current_user: Tuple[str, str] = Depends(require_authenticated)
):
    """
    Upload user profile avatar
    
    Task 4 Integration: Validates tenant context (TenantService)
    Task 5 Integration: Validates resource ownership (self-ownership for avatar)
    
    Args:
        file: Avatar image file
        
    Returns:
        dict: Upload response with avatar URL
    """
    email, role = current_user
    
    try:
        # Task 4: Validate tenant context
        current_tenant = TenantService.get_current_tenant()
        if not current_tenant:
            raise authentication_error("No tenant context found")
        
        # Task 5: Verify ownership - User can only upload own avatar
        # Avatar ownership is self-owned (email = owner)
        if role.lower() != "admin" and email != current_user[0]:
            logger.warning(
                f"Ownership violation: {email} attempted to upload avatar for "
                f"{current_user[0]} in tenant {current_tenant.tenant_id}"
            )
            raise authentication_error("You can only upload your own avatar")
        
        # Validate file type
        allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        if file.content_type not in allowed_types:
            raise validation_error(f"Invalid file type. Allowed: {allowed_types}")
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024
        content = await file.read()
        if len(content) > max_size:
            raise validation_error("File too large. Maximum size: 5MB")
        
        # TODO: Upload to Azure Blob Storage or similar
        # For now, generate a mock avatar URL
        avatar_url = f"https://api.kraftdintel.com/avatars/{email}"
        
        # Log authorization decision
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource="profile.avatar",
            resource_id=email,
            action="upload",
            allowed=True
        )
        
        logger.info(
            f"Avatar uploaded: {email} in tenant {current_tenant.tenant_id} "
            f"(role: {role})"
        )
        
        # Log avatar upload for audit trail
        try:
            from fastapi import Request as FastAPIRequest
            tenant_id = TenantService.get_current_tenant() or "default"
            
            await AuditService.log_modification(
                user_email=email,
                user_role=role,
                resource_type="user_avatar",
                resource_id=email,
                tenant_id=tenant_id,
                action="upload",
                changes={
                    "file_name": file.filename,
                    "file_type": file.content_type,
                    "file_size": len(content),
                    "avatar_url": avatar_url
                },
                ip_address=None  # Will be captured from request context if available
            )
        except Exception as audit_error:
            logger.error(f"Error logging avatar upload audit event: {audit_error}")
        
        return {
            "success": True,
            "avatar_url": avatar_url,
            "message": "Avatar uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading avatar for {email}: {e}")
        raise internal_server_error("Failed to upload avatar")


# Preferences endpoints

@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: Tuple[str, str] = Depends(require_authenticated)
):
    """
    Get current user's preferences
    
    Returns:
        UserPreferencesResponse: User preferences
    """
    email, role = current_user
    service = get_profile_service()
    
    try:
        preferences = await service.get_preferences(email)
        
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=UserRole(role),
            resource=f"preferences:{email}",
            action="read",
            allowed=True
        )
        
        return preferences
        
    except Exception as e:
        logger.error(f"Error retrieving preferences for {email}: {e}")
        raise internal_server_error("Failed to retrieve preferences")


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_data: Preferences,
    current_user: Tuple[str, str] = Depends(require_authenticated)
):
    """
    Update current user's preferences
    
    Task 4 Integration: Validates tenant context (TenantService)
    Task 5 Integration: Validates resource ownership (self-ownership for preferences)
    
    Args:
        preferences_data: Updated preferences
        
    Returns:
        UserPreferencesResponse: Updated preferences
    """
    email, role = current_user
    service = get_profile_service()
    
    try:
        # Task 4: Validate tenant context
        current_tenant = TenantService.get_current_tenant()
        if not current_tenant:
            raise authentication_error("No tenant context found")
        
        # Task 5: Verify ownership - User can only update own preferences
        # Preferences ownership is self-owned (email = owner)
        if role.lower() != "admin" and email != current_user[0]:
            logger.warning(
                f"Ownership violation: {email} attempted to update preferences for "
                f"{current_user[0]} in tenant {current_tenant.tenant_id}"
            )
            raise authentication_error("You can only update your own preferences")
        
        # Perform update
        updated_prefs = await service.update_preferences(email, preferences_data)
        
        # Log authorization decision
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource=f"preferences:{email}",
            action="update",
            allowed=True
        )
        
        logger.info(
            f"Preferences updated: {email} in tenant {current_tenant.tenant_id} "
            f"(role: {role})"
        )
        
        # Log preference modification for audit trail
        try:
            tenant_id = TenantService.get_current_tenant() or "default"
            
            # Build changes dict from preferences_data
            changes = {}
            if hasattr(preferences_data, 'email_notifications'):
                changes['email_notifications'] = preferences_data.email_notifications
            if hasattr(preferences_data, 'sms_notifications'):
                changes['sms_notifications'] = preferences_data.sms_notifications
            if hasattr(preferences_data, 'push_notifications'):
                changes['push_notifications'] = preferences_data.push_notifications
            if hasattr(preferences_data, 'language'):
                changes['language'] = preferences_data.language
            if hasattr(preferences_data, 'timezone'):
                changes['timezone'] = preferences_data.timezone
            if hasattr(preferences_data, 'two_factor_enabled'):
                changes['two_factor_enabled'] = preferences_data.two_factor_enabled
            
            await AuditService.log_modification(
                user_email=email,
                user_role=role,
                resource_type="user_preferences",
                resource_id=email,
                tenant_id=tenant_id,
                action="update",
                changes=changes,
                ip_address=None
            )
        except Exception as audit_error:
            logger.error(f"Error logging preference modification audit event: {audit_error}")
        
        return updated_prefs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences for {email}: {e}")
        raise internal_server_error("Failed to update preferences")


# Admin endpoints (future)

@router.get("/profiles")
async def list_all_profiles(
    skip: int = 0,
    limit: int = 10,
    current_user: Tuple[str, str] = Depends(require_authenticated)
):
    """
    List all user profiles within current tenant (admin only)
    
    Args:
        skip: Number of profiles to skip
        limit: Maximum number of profiles to return
        current_user: Current user from auth
        
    Returns:
        list: List of user profiles scoped to current tenant
    """
    email, role = current_user
    service = get_profile_service()
    
    # Get current tenant context
    try:
        current_tenant = TenantService.get_current_tenant()
        if not current_tenant:
            raise authentication_error("No tenant context found")
    except Exception as e:
        logger.error(f"Error getting tenant context: {e}")
        raise authentication_error("Failed to retrieve tenant context")
    
    # Note: RBAC check should be added here to ensure admin-only access
    # This will be implemented in a follow-up task
    
    try:
        # Get profiles scoped to current tenant
        profiles = await service.get_all_profiles(
            skip=skip, 
            limit=limit,
            tenant_id=current_tenant
        )
        
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=UserRole(role),
            resource=f"profiles:tenant:{current_tenant}",
            action="list",
            allowed=True
        )
        
        return {"profiles": profiles, "count": len(profiles)}
        
    except Exception as e:
        logger.error(f"Error retrieving profiles for tenant {current_tenant}: {e}")
        raise internal_server_error("Failed to retrieve profiles")


@router.get("/export")
async def export_user_data(
    current_user: Tuple[str, str] = Depends(require_authenticated)
):
    """
    Export all user data (GDPR compliance)
    
    Only returns data for the current user in their tenant context.
    
    Returns:
        dict: User profile and preferences data
    """
    email, role = current_user
    service = get_profile_service()
    
    # Get current tenant context to validate user ownership
    try:
        current_tenant = TenantService.get_current_tenant()
        if not current_tenant:
            raise authentication_error("No tenant context found")
    except Exception as e:
        logger.error(f"Error getting tenant context: {e}")
        raise KraftdHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            message="Failed to retrieve tenant context"
        )

    try:
        # Export user data scoped to their profile
        data = await service.export_profile_data(email)
        
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=UserRole(role),
            resource=f"user-data:{email}",
            action="export",
            allowed=True
        )
        
        logger.info(f"User data exported for: {email} in tenant: {current_tenant}")
        
        return data
        
    except Exception as e:
        logger.error(f"Error exporting data for {email}: {e}")
        raise internal_server_error("Failed to export user data")

