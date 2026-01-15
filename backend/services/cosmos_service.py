"""
Azure Cosmos DB Service

Manages singleton CosmosClient instance for database operations.
Follows Microsoft best practices: https://learn.microsoft.com/en-us/azure/cosmos-db/best-practice-python
"""

import logging
from typing import Optional, Any
from functools import lru_cache

try:
    from azure.cosmos import CosmosClient, exceptions
    COSMOS_SDK_AVAILABLE = True
except ImportError:
    COSMOS_SDK_AVAILABLE = False
    CosmosClient = Any  # Fallback type hint
    logging.warning("azure-cosmos not installed. Cosmos DB operations will be disabled.")

logger = logging.getLogger(__name__)


class CosmosService:
    """
    Manages Azure Cosmos DB connection and client.
    
    Features:
    - Singleton pattern: single client per application lifetime
    - Lazy initialization: client created on first use
    - Automatic retry configuration for transient failures
    - Proper cleanup on shutdown
    
    Usage:
        cosmos = CosmosService()
        await cosmos.initialize()
        
        # Use cosmos.get_client() in repositories
        client = cosmos.get_client()
        
        # On shutdown
        await cosmos.close()
    """
    
    _instance: Optional['CosmosService'] = None
    
    def __init__(self, endpoint: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize Cosmos service.
        
        Args:
            endpoint: Cosmos DB endpoint URL
            key: Cosmos DB primary key
        """
        if not COSMOS_SDK_AVAILABLE:
            logger.warning("Azure Cosmos SDK not available")
            self._client = None
            self._is_initialized = False
            return
        
        self.endpoint = endpoint
        self.key = key
        self._client = None
        self._is_initialized = False
        self._database = None
    
    async def initialize(self) -> None:
        """Initialize Cosmos DB client and verify connection."""
        if not COSMOS_SDK_AVAILABLE:
            logger.warning("Cosmos SDK not available, skipping initialization")
            return
        
        if self._is_initialized:
            logger.debug("Cosmos service already initialized")
            return
        
        try:
            logger.info("Initializing Cosmos DB connection...")
            
            # Create client with retry configuration
            self._client = CosmosClient(self.endpoint, self.key)
            
            # Verify connection by pinging service
            await self._client.client_connection._get_connection_policy()
            
            self._is_initialized = True
            logger.info("Cosmos DB connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            raise
    
    def get_client(self) -> Optional[Any]:
        """
        Get Cosmos DB client instance.
        
        Returns:
            CosmosClient instance or None if not initialized
        """
        if not self._is_initialized:
            logger.warning("Cosmos service not initialized. Call initialize() first.")
            return None
        return self._client
    
    async def get_database(self, database_id: str):
        """
        Get or create database reference.
        
        Args:
            database_id: Database ID
            
        Returns:
            Database reference
        """
        if not self._is_initialized or not self._client:
            raise RuntimeError("Cosmos service not initialized")
        
        try:
            database = self._client.get_database_client(database_id)
            logger.debug(f"Got database reference: {database_id}")
            return database
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Database not found: {database_id}")
            raise
    
    async def get_container(self, database_id: str, container_id: str):
        """
        Get container reference.
        
        Args:
            database_id: Database ID
            container_id: Container ID
            
        Returns:
            Container reference
        """
        if not self._is_initialized or not self._client:
            raise RuntimeError("Cosmos service not initialized")
        
        try:
            database = self._client.get_database_client(database_id)
            container = database.get_container_client(container_id)
            logger.debug(f"Got container reference: {database_id}/{container_id}")
            return container
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Container not found: {database_id}/{container_id}")
            raise
    
    async def close(self) -> None:
        """Close Cosmos DB client connection."""
        if self._client:
            try:
                self._client.close()
                self._is_initialized = False
                logger.info("Cosmos DB connection closed")
            except Exception as e:
                logger.error(f"Error closing Cosmos connection: {e}")
    
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._is_initialized


# Global singleton instance
_cosmos_service: Optional[CosmosService] = None


def get_cosmos_service() -> CosmosService:
    """Get or create global Cosmos service instance."""
    global _cosmos_service
    if _cosmos_service is None:
        from services.secrets_manager import get_secrets_manager
        
        secrets = get_secrets_manager()
        try:
            endpoint = secrets.get_cosmos_endpoint()
            key = secrets.get_cosmos_key()
        except ValueError:
            # Development mode: use None values, repositories will handle gracefully
            logger.warning("Cosmos DB credentials not configured, running in development mode")
            endpoint = None
            key = None
        
        _cosmos_service = CosmosService(endpoint, key)
    
    return _cosmos_service


async def initialize_cosmos(endpoint: Optional[str] = None, 
                           key: Optional[str] = None) -> CosmosService:
    """
    Initialize global Cosmos service.
    
    Call this during application startup.
    
    Args:
        endpoint: Optional endpoint override
        key: Optional key override
        
    Returns:
        Initialized CosmosService instance
    """
    global _cosmos_service
    
    if endpoint is None or key is None:
        from services.secrets_manager import get_secrets_manager
        secrets = get_secrets_manager()
        
        if endpoint is None:
            try:
                endpoint = secrets.get_cosmos_endpoint()
            except ValueError:
                logger.warning("COSMOS_ENDPOINT not configured")
                endpoint = None
        
        if key is None:
            try:
                key = secrets.get_cosmos_key()
            except ValueError:
                logger.warning("COSMOS_KEY not configured")
                key = None
    
    _cosmos_service = CosmosService(endpoint, key)
    await _cosmos_service.initialize()
    return _cosmos_service
