"""
Profile Service for user profile and preferences management
Handles CRUD operations for user profiles and preferences
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pymongo.errors import DuplicateKeyError

from models.user_preferences import (
    ProfileUpdate, 
    Preferences, 
    UserProfile,
    UserPreferencesResponse
)

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for managing user profiles and preferences"""
    
    def __init__(self, db):
        """
        Initialize ProfileService with database connection
        
        Args:
            db: Database connection object (Cosmos DB or MongoDB)
        """
        self.db = db
        self.profiles_collection = db.get_collection("user_profiles")
        self.preferences_collection = db.get_collection("user_preferences")
    
    async def get_profile(self, email: str) -> Optional[UserProfile]:
        """
        Get user profile by email
        
        Args:
            email: User email address
            
        Returns:
            UserProfile object or None if not found
        """
        try:
            profile = self.profiles_collection.find_one({"email": email})
            if not profile:
                logger.info(f"Profile not found for user: {email}")
                return None
            
            # Remove MongoDB _id field
            profile.pop("_id", None)
            return UserProfile(**profile)
            
        except Exception as e:
            logger.error(f"Error retrieving profile for {email}: {e}")
            raise
    
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
        try:
            now = datetime.utcnow()
            profile_data = {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "phone": None,
                "bio": None,
                "company": None,
                "job_title": None,
                "location": None,
                "website": None,
                "created_at": now,
                "updated_at": now
            }
            
            self.profiles_collection.insert_one(profile_data)
            logger.info(f"Profile created for user: {email}")
            
            return UserProfile(**profile_data)
            
        except DuplicateKeyError:
            logger.warning(f"Profile already exists for user: {email}")
            return await self.get_profile(email)
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
        try:
            # Only update fields that are provided
            update_dict = profile_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()
            
            result = self.profiles_collection.find_one_and_update(
                {"email": email},
                {"$set": update_dict},
                return_document=True
            )
            
            if not result:
                logger.warning(f"Profile not found for user: {email}")
                return None
            
            result.pop("_id", None)
            logger.info(f"Profile updated for user: {email}")
            return UserProfile(**result)
            
        except Exception as e:
            logger.error(f"Error updating profile for {email}: {e}")
            raise
    
    async def delete_profile(self, email: str) -> bool:
        """
        Delete user profile (soft delete by marking as inactive)
        
        Args:
            email: User email address
            
        Returns:
            True if profile was deleted, False otherwise
        """
        try:
            result = self.profiles_collection.delete_one({"email": email})
            
            if result.deleted_count > 0:
                logger.info(f"Profile deleted for user: {email}")
                # Also delete preferences
                self.preferences_collection.delete_one({"email": email})
                return True
            else:
                logger.warning(f"Profile not found for user: {email}")
                return False
                
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
        try:
            prefs = self.preferences_collection.find_one({"email": email})
            if not prefs:
                logger.info(f"Preferences not found for user: {email}, returning defaults")
                # Return default preferences
                return UserPreferencesResponse(
                    email=email,
                    preferences=Preferences(),
                    updated_at=datetime.utcnow()
                )
            
            prefs.pop("_id", None)
            return UserPreferencesResponse(**prefs)
            
        except Exception as e:
            logger.error(f"Error retrieving preferences for {email}: {e}")
            raise
    
    async def create_preferences(self, email: str) -> UserPreferencesResponse:
        """
        Create default preferences for new user
        
        Args:
            email: User email address
            
        Returns:
            Created UserPreferencesResponse object
        """
        try:
            now = datetime.utcnow()
            prefs_data = {
                "email": email,
                "preferences": Preferences().dict(),
                "updated_at": now
            }
            
            self.preferences_collection.insert_one(prefs_data)
            logger.info(f"Preferences created for user: {email}")
            
            return UserPreferencesResponse(**prefs_data)
            
        except DuplicateKeyError:
            logger.warning(f"Preferences already exist for user: {email}")
            return await self.get_preferences(email)
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
        try:
            now = datetime.utcnow()
            update_dict = {
                "preferences": preferences_data.dict(),
                "updated_at": now
            }
            
            result = self.preferences_collection.find_one_and_update(
                {"email": email},
                {"$set": update_dict},
                return_document=True,
                upsert=True  # Create if doesn't exist
            )
            
            result.pop("_id", None)
            logger.info(f"Preferences updated for user: {email}")
            return UserPreferencesResponse(**result)
            
        except Exception as e:
            logger.error(f"Error updating preferences for {email}: {e}")
            raise
    
    async def get_all_profiles(self, skip: int = 0, limit: int = 10) -> list:
        """
        Get all user profiles (admin operation)
        
        Args:
            skip: Number of profiles to skip
            limit: Maximum number of profiles to return
            
        Returns:
            List of UserProfile objects
        """
        try:
            profiles = list(self.profiles_collection.find().skip(skip).limit(limit))
            
            for profile in profiles:
                profile.pop("_id", None)
            
            logger.info(f"Retrieved {len(profiles)} profiles (skip={skip}, limit={limit})")
            return [UserProfile(**p) for p in profiles]
            
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
