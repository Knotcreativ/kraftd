"""
Conversions Service

Business logic for conversion session management.
Handles creation, retrieval, and status updates for conversion sessions.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging
import uuid

from services.cosmos_service import CosmosService

logger = logging.getLogger(__name__)


class ConversionsService:
    """
    Service for managing conversion sessions.
    
    A conversion is the core unit of work — represents a single document
    processing workflow from upload through export.
    """
    
    def __init__(self):
        """Initialize the service with Cosmos DB connection"""
        self.cosmos = CosmosService()
        self.container_name = "conversions"
    
    async def create_conversion(
        self,
        conversion_id: str,
        user_email: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Create a new conversion session.
        
        Args:
            conversion_id: UUID for the conversion
            user_email: Email of the user (partition key)
            user_id: User's unique ID
        
        Returns:
            Dict with conversion metadata
        
        Raises:
            Exception: If database insert fails
        """
        conversion_record = {
            "id": conversion_id,
            "conversion_id": conversion_id,
            "user_email": user_email,  # Partition key
            "user_id": user_id,
            "status": "in_progress",  # in_progress | completed | failed
            "started_at": datetime.utcnow().isoformat() + "Z",
            "completed_at": None,
            "documents": [],  # Will be populated as docs are uploaded
            "metadata": {
                "created_by_ip": None,
                "user_agent": None
            }
        }
        
        try:
            # Insert into Cosmos DB
            result = await self.cosmos.create_item(
                container_name=self.container_name,
                item=conversion_record
            )
            
            logger.info(f"Conversion created: {conversion_id} for user: {user_email}")
            return result
        
        except Exception as e:
            logger.error(
                f"Error creating conversion {conversion_id}: {str(e)}",
                exc_info=True
            )
            raise
    
    async def get_conversion(self, conversion_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a conversion by ID.
        
        Args:
            conversion_id: UUID of the conversion
        
        Returns:
            Dict with conversion data, or None if not found
        """
        try:
            # Query Cosmos DB
            query = "SELECT * FROM c WHERE c.conversion_id = @conversion_id"
            result = await self.cosmos.query_items(
                container_name=self.container_name,
                query=query,
                parameters=[
                    {"name": "@conversion_id", "value": conversion_id}
                ]
            )
            
            if result and len(result) > 0:
                return result[0]
            return None
        
        except Exception as e:
            logger.error(
                f"Error fetching conversion {conversion_id}: {str(e)}",
                exc_info=True
            )
            raise
    
    async def get_conversions_by_user(self, user_email: str) -> list:
        """
        Retrieve all conversions for a user.
        
        Args:
            user_email: Email of the user
        
        Returns:
            List of conversion records
        """
        try:
            # Query Cosmos DB with partition key
            query = "SELECT * FROM c WHERE c.user_email = @user_email ORDER BY c.started_at DESC"
            result = await self.cosmos.query_items(
                container_name=self.container_name,
                query=query,
                parameters=[
                    {"name": "@user_email", "value": user_email}
                ]
            )
            
            return result
        
        except Exception as e:
            logger.error(
                f"Error fetching conversions for user {user_email}: {str(e)}",
                exc_info=True
            )
            raise
    
    async def update_conversion_status(
        self,
        conversion_id: str,
        status: str,
        user_email: str
    ) -> Dict[str, Any]:
        """
        Update conversion status.
        
        Args:
            conversion_id: UUID of the conversion
            status: New status (in_progress | completed | failed)
            user_email: Email of the user (partition key)
        
        Returns:
            Updated conversion record
        """
        try:
            conversion = await self.get_conversion(conversion_id)
            if not conversion:
                raise ValueError(f"Conversion {conversion_id} not found")
            
            # Update record
            conversion["status"] = status
            conversion["updated_at"] = datetime.utcnow().isoformat() + "Z"
            
            if status == "completed":
                conversion["completed_at"] = datetime.utcnow().isoformat() + "Z"
            
            # Upsert in Cosmos DB
            result = await self.cosmos.upsert_item(
                container_name=self.container_name,
                item=conversion
            )
            
            logger.info(
                f"Conversion status updated: {conversion_id} → {status}"
            )
            return result
        
        except Exception as e:
            logger.error(
                f"Error updating conversion {conversion_id}: {str(e)}",
                exc_info=True
            )
            raise
    
    async def add_document_to_conversion(
        self,
        conversion_id: str,
        document_id: str,
        user_email: str
    ) -> Dict[str, Any]:
        """
        Add a document to a conversion.
        
        Args:
            conversion_id: UUID of the conversion
            document_id: UUID of the document
            user_email: Email of the user (partition key)
        
        Returns:
            Updated conversion record
        """
        try:
            conversion = await self.get_conversion(conversion_id)
            if not conversion:
                raise ValueError(f"Conversion {conversion_id} not found")
            
            # Add document if not already present
            if "documents" not in conversion:
                conversion["documents"] = []
            
            if document_id not in conversion["documents"]:
                conversion["documents"].append(document_id)
            
            # Upsert in Cosmos DB
            result = await self.cosmos.upsert_item(
                container_name=self.container_name,
                item=conversion
            )
            
            logger.info(
                f"Document {document_id} added to conversion {conversion_id}"
            )
            return result
        
        except Exception as e:
            logger.error(
                f"Error adding document to conversion {conversion_id}: {str(e)}",
                exc_info=True
            )
            raise
    
    async def delete_conversion(
        self,
        conversion_id: str,
        user_email: str
    ) -> bool:
        """
        Delete a conversion (archive or soft-delete).
        
        Args:
            conversion_id: UUID of the conversion
            user_email: Email of the user (partition key)
        
        Returns:
            True if deleted successfully
        """
        try:
            conversion = await self.get_conversion(conversion_id)
            if not conversion:
                return False
            
            # Soft delete: mark as archived
            conversion["status"] = "archived"
            conversion["deleted_at"] = datetime.utcnow().isoformat() + "Z"
            
            # Upsert in Cosmos DB
            await self.cosmos.upsert_item(
                container_name=self.container_name,
                item=conversion
            )
            
            logger.info(f"Conversion archived: {conversion_id}")
            return True
        
        except Exception as e:
            logger.error(
                f"Error deleting conversion {conversion_id}: {str(e)}",
                exc_info=True
            )
            raise
