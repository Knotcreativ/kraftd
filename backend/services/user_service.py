"""
User Service for persistent user management
Handles CRUD operations for users using Cosmos DB
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from models.user import User, UserRole
from services.cosmos_service import CosmosService

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing users with Cosmos DB"""

    DATABASE_ID = "KraftdIntel"
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
