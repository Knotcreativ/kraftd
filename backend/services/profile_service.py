"""
Profile Service for user profile and preferences management
Handles CRUD operations for user profiles and preferences using Cosmos DB
"""

import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime

from models.user_preferences import (
    ProfileUpdate, 
    Preferences, 
    UserProfile,
    UserPreferencesResponse
)

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for managing user profiles and preferences with Cosmos DB"""
    
    DATABASE_ID = os.getenv("COSMOS_DATABASE", "KraftdDB")
    PROFILES_CONTAINER = "user_profiles"
    PREFERENCES_CONTAINER = "user_preferences"
    
    def __init__(self, cosmos_service):
        """
        Initialize ProfileService with Cosmos DB service
        
        Args:
            cosmos_service: CosmosService instance
        """
        self.cosmos_service = cosmos_service
        self.profiles_container = None
        self.preferences_container = None
    
    async def initialize(self):
        """Initialize container references"""
        if not self.cosmos_service or not self.cosmos_service.is_initialized():
            logger.warning("Cosmos service not initialized")
            return
        
        try:
            self.profiles_container = await self.cosmos_service.get_container(
                self.DATABASE_ID,
                self.PROFILES_CONTAINER
            )
            self.preferences_container = await self.cosmos_service.get_container(
                self.DATABASE_ID,
                self.PREFERENCES_CONTAINER
            )
            logger.info("ProfileService containers initialized")
        except Exception as e:
            logger.warning(f"Could not initialize containers: {e}")
            self.profiles_container = None
            self.preferences_container = None
    
    async def get_profile(self, email: str) -> Optional[UserProfile]:
        """
        Get user profile by email
        
        Args:
            email: User email address
            
        Returns:
            UserProfile object or None if not found
        """
        if not self.profiles_container:
            logger.warning(f"Profiles container not initialized")
            return None
        
        try:
            response = self.profiles_container.read_item(
                item=email,
                partition_key=email
            )
            
            # Remove Cosmos DB system fields
            response.pop("_rid", None)
            response.pop("_self", None)
            response.pop("_etag", None)
            response.pop("_attachments", None)
            response.pop("_ts", None)
            
            return UserProfile(**response)
            
        except Exception as e:
            logger.debug(f"Profile not found for user: {email}")
            return None
    
    async def create_profile(
        self, 
        email: str, 
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> UserProfile:
        """
        Create a new user profile
        
        Args:
            email: User email address
            first_name: User's first name (optional)
            last_name: User's last name (optional)
            
        Returns:
            Created UserProfile object
        """
        if not self.profiles_container:
            logger.warning("Profiles container not initialized - creating in-memory profile")
            # Fallback: create default profile in-memory
            now = datetime.utcnow()
            profile_data = {
                "id": email,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "phone": None,
                "bio": None,
                "company": None,
                "job_title": None,
                "location": None,
                "website": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            return UserProfile(**profile_data)
        
        try:
            now = datetime.utcnow()
            profile_data = {
                "id": email,  # Cosmos DB requires 'id' field
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "phone": None,
                "bio": None,
                "company": None,
                "job_title": None,
                "location": None,
                "website": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            
            # Check if already exists
            existing = await self.get_profile(email)
            if existing:
                logger.debug(f"Profile already exists for user: {email}")
                return existing
            
            self.profiles_container.create_item(body=profile_data)
            logger.info(f"Profile created for user: {email}")
            
            return UserProfile(**profile_data)
            
        except Exception as e:
            logger.error(f"Error creating profile for {email}: {e}")
            raise
    
    async def update_profile(
        self, 
        email: str, 
        profile_data: ProfileUpdate
    ) -> UserProfile:
        """
        Update user profile
        
        Args:
            email: User email address
            profile_data: ProfileUpdate object with fields to update
            
        Returns:
            Updated UserProfile object
        """
        if not self.profiles_container:
            logger.error("Profiles container not initialized")
            raise RuntimeError("Database not initialized")
        
        try:
            # Get existing profile
            existing = await self.get_profile(email)
            if not existing:
                logger.warning(f"Profile not found for user: {email}")
                return None
            
            # Prepare update
            update_dict = existing.dict()
            update_data = profile_data.dict(exclude_unset=True)
            update_dict.update(update_data)
            update_dict["updated_at"] = datetime.utcnow().isoformat()
            update_dict["id"] = email  # Ensure ID is set
            
            # Replace item in Cosmos DB
            self.profiles_container.replace_item(
                item=email,
                body=update_dict
            )
            
            logger.info(f"Profile updated for user: {email}")
            return UserProfile(**update_dict)
            
        except Exception as e:
            logger.error(f"Error updating profile for {email}: {e}")
            raise
    
    async def delete_profile(self, email: str) -> bool:
        """
        Delete user profile and preferences
        
        Args:
            email: User email address
            
        Returns:
            True if profile was deleted, False otherwise
        """
        if not self.profiles_container or not self.preferences_container:
            logger.error("Containers not initialized")
            raise RuntimeError("Database not initialized")
        
        try:
            # Check if exists
            existing = await self.get_profile(email)
            if not existing:
                logger.warning(f"Profile not found for user: {email}")
                return False
            
            # Delete profile
            self.profiles_container.delete_item(
                item=email,
                partition_key=email
            )
            
            # Also delete preferences
            try:
                self.preferences_container.delete_item(
                    item=email,
                    partition_key=email
                )
            except Exception as e:
                logger.debug(f"Preferences not found for user: {email}")
            
            logger.info(f"Profile deleted for user: {email}")
            return True
                
        except Exception as e:
            logger.error(f"Error deleting profile for {email}: {e}")
            raise
    
    # Preferences management
    
    async def get_preferences(self, email: str) -> Optional[UserPreferencesResponse]:
        """
        Get user preferences
        
        Args:
            email: User email address
            
        Returns:
            UserPreferencesResponse object or None if not found
        """
        if not self.preferences_container:
            logger.debug(f"Preferences container not initialized, returning defaults")
            return UserPreferencesResponse(
                email=email,
                preferences=Preferences(),
                updated_at=datetime.utcnow()
            )
        
        try:
            prefs = self.preferences_container.read_item(
                item=email,
                partition_key=email
            )
            
            # Remove Cosmos DB system fields
            prefs.pop("_rid", None)
            prefs.pop("_self", None)
            prefs.pop("_etag", None)
            prefs.pop("_attachments", None)
            prefs.pop("_ts", None)
            
            # Fix datetime if it's a string
            if isinstance(prefs.get("updated_at"), str):
                prefs["updated_at"] = datetime.fromisoformat(prefs["updated_at"])
            
            return UserPreferencesResponse(**prefs)
            
        except Exception as e:
            logger.debug(f"Preferences not found for user: {email}, returning defaults")
            # Return default preferences
            return UserPreferencesResponse(
                email=email,
                preferences=Preferences(),
                updated_at=datetime.utcnow()
            )
    
    async def create_preferences(self, email: str) -> UserPreferencesResponse:
        """
        Create default preferences for new user
        
        Args:
            email: User email address
            
        Returns:
            Created UserPreferencesResponse object
        """
        if not self.preferences_container:
            logger.error("Preferences container not initialized")
            raise RuntimeError("Database not initialized")
        
        try:
            now = datetime.utcnow()
            prefs_data = {
                "id": email,  # Cosmos DB requires 'id' field
                "email": email,
                "preferences": Preferences().dict(),
                "updated_at": now.isoformat()
            }
            
            # Check if already exists
            existing = await self.get_preferences(email)
            if existing.preferences.dict() != Preferences().dict():
                logger.debug(f"Preferences already exist for user: {email}")
                return existing
            
            self.preferences_container.create_item(body=prefs_data)
            logger.info(f"Preferences created for user: {email}")
            
            # Fix datetime
            prefs_data["updated_at"] = datetime.fromisoformat(prefs_data["updated_at"])
            return UserPreferencesResponse(**prefs_data)
            
        except Exception as e:
            logger.error(f"Error creating preferences for {email}: {e}")
            raise
    
    async def update_preferences(
        self, 
        email: str, 
        preferences_data: Preferences
    ) -> UserPreferencesResponse:
        """
        Update user preferences
        
        Args:
            email: User email address
            preferences_data: Preferences object with updated values
            
        Returns:
            Updated UserPreferencesResponse object
        """
        if not self.preferences_container:
            logger.error("Preferences container not initialized")
            raise RuntimeError("Database not initialized")
        
        try:
            now = datetime.utcnow()
            update_dict = {
                "id": email,
                "email": email,
                "preferences": preferences_data.dict(),
                "updated_at": now.isoformat()
            }
            
            # Try to replace existing, if not found create new
            try:
                self.preferences_container.replace_item(
                    item=email,
                    body=update_dict
                )
            except Exception:
                # Create if doesn't exist
                self.preferences_container.create_item(body=update_dict)
            
            logger.info(f"Preferences updated for user: {email}")
            
            # Fix datetime
            update_dict["updated_at"] = datetime.fromisoformat(update_dict["updated_at"])
            return UserPreferencesResponse(**update_dict)
            
        except Exception as e:
            logger.error(f"Error updating preferences for {email}: {e}")
            raise
    
    async def get_all_profiles(self, skip: int = 0, limit: int = 10, tenant_id: Optional[str] = None) -> list:
        """
        Get all user profiles (admin operation)
        
        Filters profiles by tenant if tenant_id is provided.
        
        Args:
            skip: Number of profiles to skip
            limit: Maximum number of profiles to return
            tenant_id: Optional tenant ID to filter profiles
            
        Returns:
            List of UserProfile objects filtered by tenant if provided
        """
        if not self.profiles_container:
            logger.warning("Profiles container not initialized")
            return []
        
        try:
            # If tenant_id provided, filter by tenant_id field
            if tenant_id:
                query = "SELECT * FROM c WHERE c.tenant_id = @tenant_id ORDER BY c.created_at DESC OFFSET @skip LIMIT @limit"
                items = list(self.profiles_container.query_items(
                    query=query,
                    parameters=[
                        {"name": "@tenant_id", "value": tenant_id},
                        {"name": "@skip", "value": skip},
                        {"name": "@limit", "value": limit}
                    ]
                ))
            else:
                # Without tenant filtering (use with caution - admin only)
                query = "SELECT * FROM c ORDER BY c.created_at DESC OFFSET @skip LIMIT @limit"
                items = list(self.profiles_container.query_items(
                    query=query,
                    parameters=[
                        {"name": "@skip", "value": skip},
                        {"name": "@limit", "value": limit}
                    ]
                ))
            
            # Remove Cosmos DB system fields
            profiles = []
            for item in items:
                item.pop("_rid", None)
                item.pop("_self", None)
                item.pop("_etag", None)
                item.pop("_attachments", None)
                item.pop("_ts", None)
                profiles.append(UserProfile(**item))
            
            tenant_context = f"tenant:{tenant_id}" if tenant_id else "all"
            logger.info(f"Retrieved {len(profiles)} profiles from {tenant_context} (skip={skip}, limit={limit})")
            return profiles
            
        except Exception as e:
            logger.error(f"Error retrieving profiles: {e}")
            raise
    
    async def export_profile_data(self, email: str) -> Dict[str, Any]:
        """
        Export all user data (GDPR compliance)
        
        Args:
            email: User email address
            
        Returns:
            Dictionary containing profile and preferences
        """
        try:
            profile = await self.get_profile(email)
            preferences = await self.get_preferences(email)
            
            return {
                "profile": profile.dict() if profile else None,
                "preferences": preferences.dict() if preferences else None,
                "exported_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting data for {email}: {e}")
            raise
