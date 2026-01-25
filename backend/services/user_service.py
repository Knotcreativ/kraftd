"""
User Service for persistent user management
Handles CRUD operations for users using Cosmos DB
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import os

from models.user import User, UserRole
from services.cosmos_service import CosmosService

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing users with Cosmos DB"""

    DATABASE_ID = os.getenv("COSMOS_DATABASE", "KraftdDB")
    USERS_CONTAINER = "users"

    def __init__(self, cosmos_service: CosmosService):
        """
        Initialize UserService with Cosmos DB service

        Args:
            cosmos_service: CosmosService instance
        """
        self.cosmos_service = cosmos_service
        self.users_container = None

    async def initialize(self):
        """Initialize container references"""
        if not self.cosmos_service or not self.cosmos_service.is_initialized():
            logger.warning("Cosmos service not initialized")
            return

        try:
            self.users_container = await self.cosmos_service.get_container(
                self.DATABASE_ID,
                self.USERS_CONTAINER
            )
            logger.info("UserService initialized with Cosmos DB")
        except Exception as e:
            logger.error(f"Failed to initialize UserService: {e}")
            raise
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email
        
        Args:
            email: User email
            
        Returns:
            User object if found, None otherwise
        """
        if not self.users_container:
            logger.warning("UserService not initialized")
            return None
            
        try:
            # Try direct point read first (most efficient)
            user_data = await self.users_container.read_item(email, email)
            
            return User(
                email=user_data["email"],
                name=user_data["name"],
                hashed_password=user_data["hashed_password"],
                created_at=datetime.fromisoformat(user_data["created_at"]),
                is_active=user_data.get("is_active", True),
                role=UserRole(user_data.get("role", "user"))
            )
            
        except Exception as e:
            logger.debug(f"Direct read failed for {email}, trying query: {e}")
            try:
                # Fallback to query
                query = "SELECT * FROM c WHERE c.email = @email"
                parameters = [{"name": "@email", "value": email}]
                
                results = list(self.users_container.query_items(
                    query=query,
                    parameters=parameters,
                    partition_key=email
                ))
                
                if results:
                    user_data = results[0]
                    return User(
                        email=user_data["email"],
                        name=user_data["name"],
                        hashed_password=user_data["hashed_password"],
                        created_at=datetime.fromisoformat(user_data["created_at"]),
                        is_active=user_data.get("is_active", True),
                        role=UserRole(user_data.get("role", "user"))
                    )
            except Exception as e2:
                logger.error(f"Query also failed for {email}: {e2}")
                
        return None

    async def create_user(self, user: User) -> User:
        """
        Create a new user
        
        Args:
            user: User object to create
            
        Returns:
            Created user object
        """
        if not self.users_container:
            raise Exception("UserService not initialized")
            
        try:
            user_data = {
                "id": user.email,  # Use email as ID for point reads
                "email": user.email,
                "name": user.name,
                "hashed_password": user.hashed_password,
                "created_at": user.created_at.isoformat(),
                "is_active": user.is_active,
                "role": user.role.value
            }
            
            await self.users_container.upsert_item(user_data)
            logger.info(f"Created user: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Error creating user {user.email}: {e}")
            raise