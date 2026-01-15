"""
User Repository

Handles all user-related database operations using repository pattern.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from repositories.base import BaseRepository
from services.cosmos_service import get_cosmos_service

logger = logging.getLogger(__name__)

# Constants
DATABASE_ID = "kraftdintel"
CONTAINER_ID = "users"


class UserRepository(BaseRepository):
    """
    Repository for user management in Cosmos DB.
    
    Partition key: /email
    Enables efficient queries by user email.
    """
    
    def __init__(self):
        """Initialize user repository with Cosmos service."""
        self._cosmos_service = get_cosmos_service()
        self._container = None
    
    @property
    async def container(self):
        """Get container reference (lazy loading)."""
        if self._container is None:
            if not self._cosmos_service.is_initialized():
                logger.warning("Cosmos service not initialized, unable to access container")
                return None
            
            try:
                self._container = await self._cosmos_service.get_container(
                    DATABASE_ID, CONTAINER_ID
                )
            except Exception as e:
                logger.error(f"Failed to get container: {e}")
                return None
        
        return self._container
    
    async def create_user(self, email: str, name: str, organization: str,
                         hashed_password: str) -> Dict[str, Any]:
        """
        Create new user in database.
        
        Args:
            email: User email (partition key)
            name: User full name
            organization: User organization
            hashed_password: Bcrypt hashed password
            
        Returns:
            Created user document
            
        Raises:
            ValueError: If user already exists
        """
        user_data = {
            "id": email,  # Email is unique identifier
            "email": email,
            "name": name,
            "organization": organization,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "is_active": True,
            "subscription_tier": "basic",
        }
        
        logger.info(f"Creating user: {email}")
        return await self.create(user_data, email)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user by email (partition key).
        
        Optimized point read operation.
        
        Args:
            email: User email
            
        Returns:
            User document if found, None otherwise
        """
        logger.debug(f"Getting user: {email}")
        return await self.read(email, email)
    
    async def user_exists(self, email: str) -> bool:
        """
        Check if user exists by email.
        
        Args:
            email: User email
            
        Returns:
            True if user exists, False otherwise
        """
        logger.debug(f"Checking if user exists: {email}")
        return await self.exists(email, email)
    
    async def update_user(self, email: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update existing user.
        
        Args:
            email: User email (partition key)
            updates: Fields to update
            
        Returns:
            Updated user document
            
        Raises:
            ValueError: If user not found
        """
        logger.info(f"Updating user: {email}")
        
        # Remove protected fields
        updates.pop("id", None)
        updates.pop("email", None)
        updates.pop("created_at", None)
        
        return await self.update(email, email, updates)
    
    async def update_user_password(self, email: str, 
                                  new_hashed_password: str) -> Dict[str, Any]:
        """
        Update user password.
        
        Args:
            email: User email
            new_hashed_password: New bcrypt hashed password
            
        Returns:
            Updated user document
        """
        logger.info(f"Updating password for user: {email}")
        return await self.update_user(email, {
            "hashed_password": new_hashed_password
        })
    
    async def deactivate_user(self, email: str) -> Dict[str, Any]:
        """
        Deactivate user account.
        
        Args:
            email: User email
            
        Returns:
            Updated user document
        """
        logger.info(f"Deactivating user: {email}")
        return await self.update_user(email, {"is_active": False})
    
    async def get_active_users_count(self) -> int:
        """
        Get count of active users.
        
        Returns:
            Number of active users
        """
        query = "SELECT VALUE COUNT(1) FROM users WHERE is_active = true"
        try:
            results = await self.read_by_query(query)
            count = results[0] if results else 0
            logger.debug(f"Active users count: {count}")
            return count
        except Exception as e:
            logger.error(f"Error getting active users count: {e}")
            return 0
