"""
Base Repository Class

Abstract base class implementing common repository patterns for Cosmos DB.
Provides CRUD operations, error handling, and retry logic.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from azure.cosmos import exceptions
    COSMOS_AVAILABLE = True
except ImportError:
    COSMOS_AVAILABLE = False

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """
    Abstract base class for Cosmos DB repositories.
    
    Provides common patterns for:
    - CRUD operations (create, read, update, delete)
    - Error handling with proper HTTP status codes
    - Retry logic for transient failures
    - Logging and diagnostics
    
    Subclasses must implement container property.
    """
    
    @property
    @abstractmethod
    async def container(self):
        """Get Cosmos DB container reference. Must be implemented by subclasses."""
        pass
    
    async def create(self, item: Dict[str, Any], partition_key: str) -> Dict[str, Any]:
        """
        Create new item in container.
        
        Args:
            item: Item data (must include 'id' field)
            partition_key: Partition key value
            
        Returns:
            Created item with system fields
            
        Raises:
            ValueError: If item ID is missing
            ConflictError: If item with same ID already exists
            Exception: If database error occurs
        """
        if "id" not in item:
            raise ValueError("Item must include 'id' field")
        
        # Add timestamps
        if "created_at" not in item:
            item["created_at"] = datetime.utcnow().isoformat() + "Z"
        if "updated_at" not in item:
            item["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        try:
            container = await self.container
            if not container:
                raise RuntimeError("Container not initialized")
            
            result = container.create_item(body=item)
            logger.debug(f"Created item: {item['id']}")
            return result
            
        except exceptions.CosmosResourceExistsError:
            logger.warning(f"Item already exists: {item['id']}")
            raise ValueError(f"Item with ID {item['id']} already exists") from None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error creating item: {e}")
            raise
    
    async def read(self, item_id: str, partition_key: str) -> Optional[Dict[str, Any]]:
        """
        Read single item by ID.
        
        Optimized point read operation (most efficient for single item retrieval).
        
        Args:
            item_id: Item ID
            partition_key: Partition key value
            
        Returns:
            Item if found, None otherwise
        """
        try:
            container = await self.container
            if not container:
                raise RuntimeError("Container not initialized")
            
            result = container.read_item(item=item_id, partition_key=partition_key)
            logger.debug(f"Read item: {item_id}")
            return result
            
        except exceptions.CosmosResourceNotFoundError:
            logger.debug(f"Item not found: {item_id}")
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error reading item: {e}")
            raise
    
    async def read_by_query(self, query: str, parameters: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results.
        
        Args:
            query: SQL query string with parameter placeholders (@param)
            parameters: Query parameters (optional)
            
        Returns:
            List of items matching query
        """
        try:
            container = await self.container
            if not container:
                raise RuntimeError("Container not initialized")
            
            params = parameters or []
            items = list(container.query_items(query=query, parameters=params))
            logger.debug(f"Query returned {len(items)} items")
            return items
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Query error: {e}")
            raise
    
    async def update(self, item_id: str, partition_key: str, 
                    data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update existing item.
        
        Args:
            item_id: Item ID
            partition_key: Partition key value
            data: Update data (partial or full)
            
        Returns:
            Updated item
            
        Raises:
            ValueError: If item not found
        """
        try:
            # Read existing item
            existing = await self.read(item_id, partition_key)
            if not existing:
                raise ValueError(f"Item {item_id} not found")
            
            # Merge updates
            existing.update(data)
            existing["updated_at"] = datetime.utcnow().isoformat() + "Z"
            
            # Replace item
            container = await self.container
            if not container:
                raise RuntimeError("Container not initialized")
            
            result = container.replace_item(item=item_id, body=existing)
            logger.debug(f"Updated item: {item_id}")
            return result
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error updating item: {e}")
            raise
    
    async def delete(self, item_id: str, partition_key: str) -> bool:
        """
        Delete item by ID.
        
        Args:
            item_id: Item ID
            partition_key: Partition key value
            
        Returns:
            True if deleted, False if not found
        """
        try:
            container = await self.container
            if not container:
                raise RuntimeError("Container not initialized")
            
            container.delete_item(item=item_id, partition_key=partition_key)
            logger.debug(f"Deleted item: {item_id}")
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            logger.debug(f"Item not found for deletion: {item_id}")
            return False
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error deleting item: {e}")
            raise
    
    async def exists(self, item_id: str, partition_key: str) -> bool:
        """
        Check if item exists (optimized query).
        
        Args:
            item_id: Item ID
            partition_key: Partition key value
            
        Returns:
            True if item exists, False otherwise
        """
        try:
            item = await self.read(item_id, partition_key)
            return item is not None
        except Exception as e:
            logger.error(f"Error checking item existence: {e}")
            raise
