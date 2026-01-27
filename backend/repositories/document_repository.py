"""
Document Repository

Handles all document-related database operations using repository pattern.
"""

import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from repositories.base import BaseRepository
from services.cosmos_service import get_cosmos_service

logger = logging.getLogger(__name__)

# Constants
DATABASE_ID = os.getenv("COSMOS_DATABASE", "KraftdDB")
CONTAINER_ID = "documents"


class DocumentStatus(str, Enum):
    """Document processing and workflow status."""
    # Core processing statuses
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"
    # Workflow statuses
    REVIEW_PENDING = "REVIEW_PENDING"
    ESTIMATION_IN_PROGRESS = "ESTIMATION_IN_PROGRESS"
    QUOTES_NORMALIZED = "QUOTES_NORMALIZED"
    COMPARISON_DONE = "COMPARISON_DONE"
    PROPOSAL_GENERATED = "PROPOSAL_GENERATED"
    PO_GENERATED = "PO_GENERATED"


class DocumentRepository(BaseRepository):
    """
    Repository for document management in Cosmos DB.
    
    Partition key: /owner_email
    Enables efficient per-user document queries.
    
    Note: TTL configured for automatic cleanup (90 days default).
    """
    
    def __init__(self):
        """Initialize document repository with Cosmos service."""
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
    
    async def create_document(self, document_id: str, owner_email: str,
                             filename: str, document_type: str,
                             **kwargs) -> Dict[str, Any]:
        """
        Create new document in database.
        
        Args:
            document_id: Unique document ID
            owner_email: Owner email (partition key)
            filename: Original filename
            document_type: Document type (INVOICE, PO, QUOTE, etc.)
            **kwargs: Additional document fields
            
        Returns:
            Created document
            
        Raises:
            ValueError: If document already exists
        """
        document_data = {
            "id": document_id,
            "owner_email": owner_email,  # Partition key
            "filename": filename,
            "document_type": document_type,
            "status": DocumentStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            **kwargs
        }
        
        logger.info(f"Creating document: {document_id} for user: {owner_email}")
        return await self.create(document_data, owner_email)
    
    async def get_document(self, document_id: str, owner_email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document by ID.
        
        Args:
            document_id: Document ID
            owner_email: Owner email (partition key)
            
        Returns:
            Document if found, None otherwise
        """
        logger.debug(f"Getting document: {document_id}")
        return await self.read(document_id, owner_email)
    
    async def get_user_documents(self, owner_email: str) -> List[Dict[str, Any]]:
        """
        Get all documents for a specific user (partition query).
        
        Efficient query within single partition.
        
        Args:
            owner_email: Owner email
            
        Returns:
            List of user's documents
        """
        query = """
            SELECT * FROM documents 
            WHERE owner_email = @email
            ORDER BY created_at DESC
        """
        
        try:
            logger.debug(f"Getting documents for user: {owner_email}")
            return await self.read_by_query(query, [
                {"name": "@email", "value": owner_email}
            ])
        except Exception as e:
            logger.error(f"Error getting user documents: {e}")
            return []
    
    async def get_documents_by_status(self, owner_email: str, 
                                     status: str) -> List[Dict[str, Any]]:
        """
        Get documents by status for a specific user.
        
        Args:
            owner_email: Owner email
            status: Document status
            
        Returns:
            List of documents with specified status
        """
        query = """
            SELECT * FROM documents 
            WHERE owner_email = @email AND status = @status
            ORDER BY created_at DESC
        """
        
        try:
            logger.debug(f"Getting {status} documents for user: {owner_email}")
            return await self.read_by_query(query, [
                {"name": "@email", "value": owner_email},
                {"name": "@status", "value": status}
            ])
        except Exception as e:
            logger.error(f"Error getting documents by status: {e}")
            return []
    
    async def get_documents_by_type(self, owner_email: str,
                                   document_type: str) -> List[Dict[str, Any]]:
        """
        Get documents by type for a specific user.
        
        Args:
            owner_email: Owner email
            document_type: Document type (INVOICE, PO, etc.)
            
        Returns:
            List of documents of specified type
        """
        query = """
            SELECT * FROM documents 
            WHERE owner_email = @email AND document_type = @type
            ORDER BY created_at DESC
        """
        
        try:
            logger.debug(f"Getting {document_type} documents for user: {owner_email}")
            return await self.read_by_query(query, [
                {"name": "@email", "value": owner_email},
                {"name": "@type", "value": document_type}
            ])
        except Exception as e:
            logger.error(f"Error getting documents by type: {e}")
            return []
    
    async def update_document_status(self, document_id: str, owner_email: str,
                                    status: str) -> Dict[str, Any]:
        """
        Update document processing status.
        
        Args:
            document_id: Document ID
            owner_email: Owner email (partition key)
            status: New status
            
        Returns:
            Updated document
            
        Raises:
            ValueError: If document not found
        """
        logger.info(f"Updating document {document_id} status to: {status}")
        
        # Validate status
        valid_statuses = [s.value for s in DocumentStatus]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        
        return await self.update(document_id, owner_email, {
            "status": status
        })
    
    async def update_document(self, document_id: str, owner_email: str,
                            updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update document fields.
        
        Args:
            document_id: Document ID
            owner_email: Owner email (partition key)
            updates: Fields to update
            
        Returns:
            Updated document
            
        Raises:
            ValueError: If document not found
        """
        logger.info(f"Updating document: {document_id}")
        
        # Remove protected fields
        updates.pop("id", None)
        updates.pop("owner_email", None)
        updates.pop("created_at", None)
        
        return await self.update(document_id, owner_email, updates)
    
    async def delete_document(self, document_id: str, owner_email: str) -> bool:
        """
        Delete document permanently.
        
        Args:
            document_id: Document ID
            owner_email: Owner email (partition key)
            
        Returns:
            True if deleted, False if not found
        """
        logger.info(f"Deleting document: {document_id}")
        return await self.delete(document_id, owner_email)
    
    async def get_user_documents_count(self, owner_email: str) -> int:
        """
        Get count of documents for user.
        
        Args:
            owner_email: Owner email
            
        Returns:
            Number of documents
        """
        query = "SELECT VALUE COUNT(1) FROM documents WHERE owner_email = @email"
        
        try:
            results = await self.read_by_query(query, [
                {"name": "@email", "value": owner_email}
            ])
            count = results[0] if results else 0
            logger.debug(f"Document count for {owner_email}: {count}")
            return count
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0
    
    async def archive_old_documents(self, owner_email: str, days: int = 90) -> int:
        """
        Archive documents older than specified days.
        
        Args:
            owner_email: Owner email
            days: Number of days to keep (older docs archived)
            
        Returns:
            Number of archived documents
        """
        logger.info(f"Archiving documents older than {days} days for: {owner_email}")
        
        try:
            # Calculate cutoff date
            from datetime import timedelta
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
            
            # Find old documents
            old_docs = await self.read_by_query(
                """
                SELECT * FROM documents 
                WHERE owner_email = @email AND created_at < @cutoff
                """,
                [
                    {"name": "@email", "value": owner_email},
                    {"name": "@cutoff", "value": cutoff_date}
                ]
            )
            
            # Archive them
            archived_count = 0
            for doc in old_docs:
                try:
                    await self.update_document_status(
                        doc["id"],
                        owner_email,
                        DocumentStatus.ARCHIVED.value
                    )
                    archived_count += 1
                except Exception as e:
                    logger.warning(f"Failed to archive document {doc['id']}: {e}")
            
            logger.info(f"Archived {archived_count} documents")
            return archived_count
            
        except Exception as e:
            logger.error(f"Error archiving old documents: {e}")
            return 0
