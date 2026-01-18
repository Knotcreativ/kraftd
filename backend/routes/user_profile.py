"""
User Profile and Preferences Routes for FastAPI
Handles user profile CRUD operations and preference management
"""

import logging
from typing import Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse

from middleware.rbac import require_authenticated
from models.user_preferences import (
    ProfileUpdate,
    Preferences,
    UserProfile,
    UserPreferencesResponse
)
from services.profile_service import ProfileService
from services.rbac_service import rbac_service

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile service not initialized"
        )
    return profile_service


# Profile endpoints

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: Tuple[str, str] = Depends(require_authenticated())
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
            user_role=role,
            resource="profile",
            resource_id=email,
            action="read",
            allowed=True
        )
        
        return profile
        
    except Exception as e:
        logger.error(f"Error retrieving profile for {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )


@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_data: ProfileUpdate,
    current_user: Tuple[str, str] = Depends(require_authenticated())
):
    """
    Update current user's profile
    
    Args:
        profile_data: Profile update data
        
    Returns:
        UserProfile: Updated profile information
    """
    email, role = current_user
    service = get_profile_service()
    
    try:
        # Verify user owns this profile
        existing = await service.get_profile(email)
        if not existing:
            existing = await service.create_profile(email)
        
        updated_profile = await service.update_profile(email, profile_data)
        
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource="profile",
            resource_id=email,
            action="update",
            allowed=True
        )
        
        return updated_profile
        
    except Exception as e:
        logger.error(f"Error updating profile for {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/profile/avatar", response_model=dict)
async def upload_profile_avatar(
    file: UploadFile = File(...),
    current_user: Tuple[str, str] = Depends(require_authenticated())
):
    """
    Upload user profile avatar
    
    Args:
        file: Avatar image file
        
    Returns:
        dict: Upload response with avatar URL
    """
    email, role = current_user
    
    try:
        # Validate file type
        allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {allowed_types}"
            )
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large. Maximum size: 5MB"
            )
        
        # TODO: Upload to Azure Blob Storage or similar
        # For now, generate a mock avatar URL
        avatar_url = f"https://api.kraftdintel.com/avatars/{email}"
        
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource="profile.avatar",
            resource_id=email,
            action="upload",
            allowed=True
        )
        
        logger.info(f"Avatar uploaded for user: {email}")
        
        return {
            "success": True,
            "avatar_url": avatar_url,
            "message": "Avatar uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading avatar for {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar"
        )


# Preferences endpoints

@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: Tuple[str, str] = Depends(require_authenticated())
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
            user_role=role,
            resource="preferences",
            resource_id=email,
            action="read",
            allowed=True
        )
        
        return preferences
        
    except Exception as e:
        logger.error(f"Error retrieving preferences for {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preferences"
        )


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_data: Preferences,
    current_user: Tuple[str, str] = Depends(require_authenticated())
):
    """
    Update current user's preferences
    
    Args:
        preferences_data: Updated preferences
        
    Returns:
        UserPreferencesResponse: Updated preferences
    """
    email, role = current_user
    service = get_profile_service()
    
    try:
        updated_prefs = await service.update_preferences(email, preferences_data)
        
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource="preferences",
            resource_id=email,
            action="update",
            allowed=True
        )
        
        return updated_prefs
        
    except Exception as e:
        logger.error(f"Error updating preferences for {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )


# Admin endpoints (future)

@router.get("/profiles")
async def list_all_profiles(
    skip: int = 0,
    limit: int = 10,
    current_user: Tuple[str, str] = Depends(require_authenticated())
):
    """
    List all user profiles (admin only)
    
    Args:
        skip: Number of profiles to skip
        limit: Maximum number of profiles to return
        
    Returns:
        list: List of user profiles
    """
    email, role = current_user
    service = get_profile_service()
    
    # Note: RBAC check should be added here to ensure admin-only access
    # This will be implemented in a follow-up task
    
    try:
        profiles = await service.get_all_profiles(skip=skip, limit=limit)
        
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource="profiles",
            resource_id="all",
            action="list",
            allowed=True
        )
        
        return {"profiles": profiles, "count": len(profiles)}
        
    except Exception as e:
        logger.error(f"Error retrieving profiles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profiles"
        )


@router.get("/export")
async def export_user_data(
    current_user: Tuple[str, str] = Depends(require_authenticated())
):
    """
    Export all user data (GDPR compliance)
    
    Returns:
        dict: User profile and preferences data
    """
    email, role = current_user
    service = get_profile_service()
    
    try:
        data = await service.export_profile_data(email)
        
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource="user-data",
            resource_id=email,
            action="export",
            allowed=True
        )
        
        logger.info(f"User data exported for: {email}")
        
        return data
        
    except Exception as e:
        logger.error(f"Error exporting data for {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export user data"
        )
