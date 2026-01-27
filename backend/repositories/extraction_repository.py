"""
Repository for storing and retrieving comprehensive extraction results per document per source.

Enables per-document isolation with rich data structure:
- Timestamp + Owner ID grouping
- Document metadata and raw extraction data
- AI model summaries and analysis
- User modifications and conversion preferences
- Transformed data with download tracking
- Feedback and quality metrics
"""

import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

from repositories.base import BaseRepository
from services.cosmos_service import get_cosmos_service
from models.extraction import (
    ExtractionRecord,
    DocumentMetadata,
    ExtractionData,
    AIAnalysisSummary,
    UserModifications,
    ConversionPreferences,
    DownloadInfo,
    Feedback
)

logger = logging.getLogger(__name__)

# Constants
DATABASE_ID = os.getenv("COSMOS_DATABASE", "KraftdDB")
CONTAINER_ID = "extractions"


class ExtractionRepository(BaseRepository):
    """
    Repository for comprehensive extraction results with per-document isolation.
    
    Database: kraftdintel
    Container: extractions
    Partition Key: /owner_email
    Item ID: {document_id}:{source}
    
    Complete data structure includes:
    - Document metadata (filename, type, upload timestamp)
    - Raw extraction data (text, tables, images, metadata)
    - AI analysis summary (insights, risks, recommendations)
    - User modifications tracking
    - Conversion preferences
    - Transformed/final document data
    - Download information and tracking
    - User feedback on extraction quality
    
    Example item:
      {
        "id": "doc-001:direct_parse",
        "owner_email": "user@example.com",
        "document_id": "doc-001",
        "source": "direct_parse",
        "created_at": "2026-01-19T10:30:00Z",
        "document": {...},
        "extraction_data": {...},
        "ai_summary": {...},
        "user_modifications": {...},
        "conversion_preferences": {...},
        "transformed_data": {...},
        "download_info": {...},
        "feedback": {...},
        "status": "extracted"
      }
    """

    def __init__(self):
        self._cosmos_service = get_cosmos_service()
        self._container = None

    @property
    async def container(self):
        if self._container is None:
            if not self._cosmos_service.is_initialized():
                logger.warning("Cosmos service not initialized, unable to access extractions container")
                return None
            try:
                self._container = await self._cosmos_service.get_container(
                    DATABASE_ID, CONTAINER_ID
                )
            except Exception as e:
                logger.error(f"Failed to get extractions container: {e}")
                return None
        return self._container
    
    async def create_extraction(
        self,
        document_id: str,
        owner_email: str,
        source: str,
        extraction_data: ExtractionData,
        document_metadata: DocumentMetadata,
        ai_summary: Optional[AIAnalysisSummary] = None,
        conversion_preferences: Optional[ConversionPreferences] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create comprehensive extraction record with per-document isolation.
        
        Args:
            document_id: ID of the document being extracted
            owner_email: Email of document owner (partition key)
            source: Extraction source (direct_parse, ocr, azure_di)
            extraction_data: Raw extracted data
            document_metadata: Document information (filename, type, upload time)
            ai_summary: Optional AI analysis summary
            conversion_preferences: Optional user conversion preferences
        
        Returns:
            Created extraction record or None
        """
        try:
            item_id = f"{document_id}:{source}"
            
            # Build record with all fields
            record = ExtractionRecord(
                id=item_id,
                owner_email=owner_email,
                document_id=document_id,
                source=source,
                document=document_metadata,
                extraction_data=extraction_data,
                ai_summary=ai_summary,
                conversion_preferences=conversion_preferences or ConversionPreferences(),
                status="extracted"
            )
            
            record_dict = record.model_dump(mode="json")
            
            logger.info(f"Creating comprehensive extraction record for {document_id} [{source}]")
            return await self.create(record_dict, owner_email)
        except Exception as e:
            logger.error(f"Error creating extraction record: {e}")
            return None
    
    async def get_extraction_by_id(
        self,
        document_id: str,
        source: str,
        owner_email: str
    ) -> Optional[ExtractionRecord]:
        """
        Get a specific extraction record by document ID and source.
        
        Args:
            document_id: Document ID
            source: Extraction source
            owner_email: Owner email (partition key)
        
        Returns:
            ExtractionRecord or None
        """
        try:
            item_id = f"{document_id}:{source}"
            # Using base class read method
            item = await self.read(item_id, owner_email)
            if item:
                return ExtractionRecord(**item)
            return None
        except Exception as e:
            logger.error(f"Error reading extraction: {e}")
            return None
    
    async def get_extractions_for_document(
        self,
        owner_email: str,
        document_id: str
    ) -> List[ExtractionRecord]:
        """
        Get all extraction results for a single document (all sources).
        
        Returns extractions from all sources (direct_parse, ocr, azure_di)
        for the given document, ensuring per-document isolation.
        
        Args:
            owner_email: Owner email (partition key)
            document_id: Document ID to query
        
        Returns:
            List of ExtractionRecords for the document
        """
        try:
            query = "SELECT * FROM c WHERE c.document_id = @doc_id"
            params = [{"name": "@doc_id", "value": document_id}]
            
            items = await self.read_by_query(query, params)
            return [ExtractionRecord(**item) for item in items]
        except Exception as e:
            logger.error(f"Error querying extractions for document: {e}")
            return []
    
    async def get_extractions_for_user(
        self,
        owner_email: str,
        limit: int = 100
    ) -> List[ExtractionRecord]:
        """
        Get all extractions for a user (across all documents).
        
        Args:
            owner_email: Owner email (partition key)
            limit: Maximum number of records to return
        
        Returns:
            List of ExtractionRecords for the user
        """
        try:
            query = f"SELECT * FROM c WHERE c.owner_email = @owner ORDER BY c.created_at DESC OFFSET 0 LIMIT {limit}"
            params = [{"name": "@owner", "value": owner_email}]
            
            items = await self.read_by_query(query, params)
            return [ExtractionRecord(**item) for item in items]
        except Exception as e:
            logger.error(f"Error querying extractions for user: {e}")
            return []
    
    async def update_extraction(
        self,
        document_id: str,
        source: str,
        owner_email: str,
        updates: Dict[str, Any]
    ) -> Optional[ExtractionRecord]:
        """
        Update an existing extraction record.
        
        Args:
            document_id: Document ID
            source: Extraction source
            owner_email: Owner email (partition key)
            updates: Dictionary of fields to update
        
        Returns:
            Updated ExtractionRecord or None
        """
        try:
            item_id = f"{document_id}:{source}"
            updates["updated_at"] = datetime.utcnow().isoformat() + "Z"
            
            item = await self.update(item_id, updates, owner_email)
            if item:
                return ExtractionRecord(**item)
            return None
        except Exception as e:
            logger.error(f"Error updating extraction: {e}")
            return None
    
    async def update_ai_summary(
        self,
        document_id: str,
        source: str,
        owner_email: str,
        ai_summary: AIAnalysisSummary
    ) -> Optional[ExtractionRecord]:
        """Update AI summary for an extraction."""
        return await self.update_extraction(
            document_id,
            source,
            owner_email,
            {"ai_summary": ai_summary.model_dump(mode="json")}
        )
    
    async def update_user_modifications(
        self,
        document_id: str,
        source: str,
        owner_email: str,
        modifications: UserModifications
    ) -> Optional[ExtractionRecord]:
        """Update user modifications for an extraction."""
        return await self.update_extraction(
            document_id,
            source,
            owner_email,
            {"user_modifications": modifications.model_dump(mode="json")}
        )
    
    async def update_feedback(
        self,
        document_id: str,
        source: str,
        owner_email: str,
        feedback: Feedback
    ) -> Optional[ExtractionRecord]:
        """Update user feedback for an extraction."""
        return await self.update_extraction(
            document_id,
            source,
            owner_email,
            {"feedback": feedback.model_dump(mode="json")}
        )
    
    async def update_download_info(
        self,
        document_id: str,
        source: str,
        owner_email: str,
        download_info: DownloadInfo
    ) -> Optional[ExtractionRecord]:
        """Update download information for an extraction."""
        return await self.update_extraction(
            document_id,
            source,
            owner_email,
            {"download_info": download_info.model_dump(mode="json")}
        )
    
    async def delete_extraction(
        self,
        document_id: str,
        source: str,
        owner_email: str
    ) -> bool:
        """
        Delete extraction for a specific document and source.
        
        Args:
            document_id: Document ID
            source: Extraction source
            owner_email: Owner email (partition key)
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            item_id = f"{document_id}:{source}"
            await self.delete(item_id, owner_email)
            return True
        except Exception as e:
            logger.error(f"Error deleting extraction: {e}")
            return False
    
    async def delete_extractions_for_document(
        self,
        document_id: str,
        owner_email: str
    ) -> bool:
        """
        Delete all extractions for a document (all sources).
        
        Args:
            document_id: Document ID
            owner_email: Owner email (partition key)
        
        Returns:
            True if all deleted, False otherwise
        """
        try:
            extractions = await self.get_extractions_for_document(owner_email, document_id)
            all_deleted = True
            for extraction in extractions:
                if not await self.delete_extraction(document_id, extraction.source, owner_email):
                    all_deleted = False
            return all_deleted
        except Exception as e:
            logger.error(f"Error deleting extractions for document: {e}")
            return False
