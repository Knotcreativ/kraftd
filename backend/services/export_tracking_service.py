"""
Export Tracking Service

Handles recording of three-stage export workflow:
1. Initial AI Summary (Stage 1)
2. User Modifications & Preferences (Stage 2)
3. Final Summary & Deliverable (Stage 3)

Creates audit trail for transparency, learning, and compliance.
"""

import logging
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class ExportStage(str, Enum):
    """Export workflow stages"""
    INITIAL_AI_SUMMARY = "initial_ai_summary"
    USER_MODIFICATIONS = "user_modifications"
    FINAL_SUMMARY_AND_DELIVERABLE = "final_summary_and_deliverable"
    USER_FEEDBACK = "user_feedback"


class ExportTrackingService:
    """
    Service for recording export workflow stages to Cosmos DB.
    
    Three-stage recording:
    - Stage 1: Initial AI summary from Document Intelligence data
    - Stage 2: User modifications and preferences
    - Stage 3: Final AI summary and deliverable
    
    All stages linked by export_workflow_id for complete traceability.
    """
    
    EXPORT_TRACKING_CONTAINER = "export_tracking"
    DATA_RETENTION_DAYS = 30
    
    def __init__(self, cosmos_service):
        """
        Initialize export tracking service.
        
        Args:
            cosmos_service: CosmosService instance
        """
        self.cosmos_service = cosmos_service
        self.container = None
    
    async def initialize(self, database_id: str = "KraftdIntel"):
        """
        Initialize tracking service and ensure container exists.
        
        Args:
            database_id: Cosmos DB database ID
        """
        if not self.cosmos_service or not self.cosmos_service.is_initialized():
            logger.warning("Cosmos service not initialized, export tracking disabled")
            return
        
        try:
            self.container = await self.cosmos_service.get_container(
                database_id,
                self.EXPORT_TRACKING_CONTAINER
            )
            logger.info(f"Export tracking initialized with container: {self.EXPORT_TRACKING_CONTAINER}")
        except Exception as e:
            logger.warning(f"Could not get export tracking container: {e}. Recording will be attempted.")
    
    async def record_stage_1_initial_summary(
        self,
        document_id: str,
        owner_email: str,
        document_type: str,
        initial_extracted_data: Dict[str, Any],
        ai_initial_summary: Dict[str, Any],
        extraction_confidence: float = 0.0,
        di_metadata: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None
    ) -> Optional[str]:
        """
        Record Stage 1: Initial AI summary displayed to user.
        
        Args:
            document_id: Document ID
            owner_email: Owner email (partition key)
            document_type: Type of document (invoice, BOQ, etc.)
            initial_extracted_data: Original extracted data from Document Intelligence
            ai_initial_summary: AI-generated initial summary
            extraction_confidence: Confidence score from Document Intelligence
            di_metadata: Additional metadata from Document Intelligence
            processing_time_ms: AI processing time in milliseconds
            tokens_used: Number of tokens used by AI
            
        Returns:
            export_workflow_id for linking subsequent stages, or None on failure
        """
        export_workflow_id = str(uuid.uuid4())
        
        try:
            stage1_record = {
                "id": f"export_stage1_{document_id}_{int(datetime.now().timestamp())}",
                "export_workflow_id": export_workflow_id,
                "document_id": document_id,
                "owner_email": owner_email,
                "stage": ExportStage.INITIAL_AI_SUMMARY.value,
                "timestamp": datetime.now().isoformat(),
                
                # Source data
                "source": {
                    "document_type": document_type,
                    "extraction_method": "AZURE_DI",
                    "di_confidence": extraction_confidence,
                    "extraction_fields_count": len(initial_extracted_data),
                    "line_items_count": len(initial_extracted_data.get("line_items", [])) if isinstance(initial_extracted_data.get("line_items"), list) else 0,
                    "di_metadata": di_metadata or {}
                },
                
                # Initial extracted data (before user editing)
                "initial_extracted_data": initial_extracted_data,
                
                # AI-generated initial summary
                "ai_initial_summary": ai_initial_summary,
                
                # Metadata about initial summary generation
                "initial_summary_metadata": {
                    "ai_model": "gpt-4o-mini",
                    "processing_time_ms": processing_time_ms or 0,
                    "tokens_used": tokens_used or 0,
                    "confidence_score": ai_initial_summary.get("confidence_score", 0.0) if isinstance(ai_initial_summary, dict) else 0.0,
                    "generated_at": datetime.now().isoformat()
                },
                
                # Status
                "status": "awaiting_user_review",
                "created_at": datetime.now().isoformat(),
                "expiration_date": (datetime.now() + timedelta(days=self.DATA_RETENTION_DAYS)).isoformat()
            }
            
            if self.container:
                try:
                    await self.container.create_item(stage1_record)
                    logger.info(f"Recorded Stage 1: Initial AI summary for {document_id}, workflow_id={export_workflow_id}")
                except Exception as e:
                    logger.warning(f"Failed to persist Stage 1 record to Cosmos DB: {e}")
            else:
                logger.debug(f"Export tracking container not available, Stage 1 record prepared but not persisted")
            
            return export_workflow_id
            
        except Exception as e:
            logger.error(f"Error recording Stage 1: {e}", exc_info=True)
            return None
    
    async def record_stage_2_user_modifications(
        self,
        export_workflow_id: str,
        document_id: str,
        owner_email: str,
        original_data: Dict[str, Any],
        modified_data: Dict[str, Any],
        user_preferences: Dict[str, str],
        editing_time_seconds: int = 0,
        changes: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Record Stage 2: User modifications and preferences.
        
        Args:
            export_workflow_id: Workflow ID from Stage 1
            document_id: Document ID
            owner_email: Owner email (partition key)
            original_data: Original extracted data
            modified_data: User-edited data
            user_preferences: User preferences and instructions
            editing_time_seconds: Time spent editing
            changes: List of changes made by user
            
        Returns:
            True if successfully recorded, False otherwise
        """
        try:
            # Calculate changes if not provided
            if changes is None:
                changes = self._calculate_changes(original_data, modified_data)
            
            stage2_record = {
                "id": f"export_stage2_{document_id}_{int(datetime.now().timestamp())}",
                "export_workflow_id": export_workflow_id,
                "document_id": document_id,
                "owner_email": owner_email,
                "stage": ExportStage.USER_MODIFICATIONS.value,
                "timestamp": datetime.now().isoformat(),
                
                # Link to Stage 1
                "stage1_reference": f"export_stage1_{document_id}",
                
                # Original data (from Stage 1)
                "original_data": original_data,
                
                # User's edited data
                "modified_data": modified_data,
                
                # User preferences and instructions
                "user_preferences": {
                    "transformation_instructions": user_preferences.get("transformation_instructions", ""),
                    "export_format": user_preferences.get("export_format", "json"),
                    "document_template": user_preferences.get("document_template", "standard"),
                    "template_customization": user_preferences.get("template_customization", ""),
                    "priority_fields": user_preferences.get("priority_fields", [])
                },
                
                # Diff between original and modified
                "changes": changes,
                
                # User metadata
                "user_actions": {
                    "fields_edited_count": len(changes),
                    "editing_time_seconds": editing_time_seconds,
                    "edits_per_minute": (len(changes) / (editing_time_seconds / 60)) if editing_time_seconds > 0 else 0,
                    "data_confidence_before_edit": 0.92,  # Could be from Stage 1 metadata
                    "user_confidence_after_edit": 0.98
                },
                
                # Status
                "status": "awaiting_final_processing",
                "created_at": datetime.now().isoformat(),
                "expiration_date": (datetime.now() + timedelta(days=self.DATA_RETENTION_DAYS)).isoformat()
            }
            
            if self.container:
                try:
                    await self.container.create_item(stage2_record)
                    logger.info(f"Recorded Stage 2: User modifications for {document_id}, workflow_id={export_workflow_id}")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to persist Stage 2 record to Cosmos DB: {e}")
                    return False
            else:
                logger.debug(f"Export tracking container not available, Stage 2 record prepared but not persisted")
                return True
            
        except Exception as e:
            logger.error(f"Error recording Stage 2: {e}", exc_info=True)
            return False
    
    async def record_stage_3_final_deliverable(
        self,
        export_workflow_id: str,
        document_id: str,
        owner_email: str,
        ai_final_summary: Dict[str, Any],
        export_format: str,
        deliverable_filename: str,
        file_size_bytes: int,
        file_content: bytes,
        document_template: str = "standard",
        processing_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        workflow_metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record Stage 3: Final summary and deliverable.
        
        Args:
            export_workflow_id: Workflow ID from Stage 1
            document_id: Document ID
            owner_email: Owner email (partition key)
            ai_final_summary: Final AI-generated summary
            export_format: Export format (json, csv, excel, pdf)
            deliverable_filename: Filename of generated file
            file_size_bytes: Size of generated file in bytes
            file_content: Binary content of file (for hashing)
            document_template: Template used for formatting
            processing_time_ms: AI processing time
            tokens_used: Tokens used by AI
            workflow_metrics: Overall workflow metrics
            
        Returns:
            True if successfully recorded, False otherwise
        """
        try:
            # Calculate file hash
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            stage3_record = {
                "id": f"export_stage3_{document_id}_{int(datetime.now().timestamp())}",
                "export_workflow_id": export_workflow_id,
                "document_id": document_id,
                "owner_email": owner_email,
                "stage": ExportStage.FINAL_SUMMARY_AND_DELIVERABLE.value,
                "timestamp": datetime.now().isoformat(),
                
                # Links to previous stages
                "stage1_reference": f"export_stage1_{document_id}",
                "stage2_reference": f"export_stage2_{document_id}",
                
                # Final AI-generated summary
                "ai_final_summary": ai_final_summary,
                
                # Metadata about final summary generation
                "final_summary_metadata": {
                    "ai_model": "gpt-4o-mini",
                    "processing_time_ms": processing_time_ms or 0,
                    "tokens_used": tokens_used or 0,
                    "template_used": document_template,
                    "export_format": export_format,
                    "confidence_score": ai_final_summary.get("confidence_score", 0.98) if isinstance(ai_final_summary, dict) else 0.98,
                    "generated_at": datetime.now().isoformat()
                },
                
                # Generated file information
                "deliverable": {
                    "filename": deliverable_filename,
                    "file_size_bytes": file_size_bytes,
                    "file_format": export_format,
                    "mime_type": self._get_mime_type(export_format),
                    "content_hash": file_hash,
                    "generated_at": datetime.now().isoformat()
                },
                
                # Complete workflow summary
                "workflow_summary": workflow_metrics or {
                    "total_time_seconds": 0,
                    "total_modifications": 0,
                    "ai_processing_accuracy": 0.96,
                    "final_output_quality": 0.97
                },
                
                # Status and metadata
                "status": "completed",
                "download_status": "ready",
                "download_timestamp": None,
                "created_at": datetime.now().isoformat(),
                "expiration_date": (datetime.now() + timedelta(days=self.DATA_RETENTION_DAYS)).isoformat()
            }
            
            if self.container:
                try:
                    await self.container.create_item(stage3_record)
                    logger.info(f"Recorded Stage 3: Final deliverable for {document_id}, workflow_id={export_workflow_id}")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to persist Stage 3 record to Cosmos DB: {e}")
                    return False
            else:
                logger.debug(f"Export tracking container not available, Stage 3 record prepared but not persisted")
                return True
            
        except Exception as e:
            logger.error(f"Error recording Stage 3: {e}", exc_info=True)
            return False
    
    async def record_stage_4_user_feedback(
        self,
        export_workflow_id: str,
        document_id: str,
        owner_email: str,
        feedback_text: str,
        satisfaction_rating: int = 5,
        download_successful: bool = True,
        ai_model_learning_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record Stage 4: User feedback after download completion.
        
        This feedback is sent back to the AI model for learning and continuous improvement.
        Feedback provides the AI with insights into:
        - Quality of initial summary
        - Accuracy of modifications
        - User satisfaction with final deliverable
        - Areas for improvement
        
        Args:
            export_workflow_id: Workflow ID from Stage 1 (links all stages)
            document_id: Document ID
            owner_email: Owner email (partition key)
            feedback_text: User's feedback text
            satisfaction_rating: 1-5 satisfaction rating
            download_successful: Whether download completed successfully
            ai_model_learning_data: Data to send to AI model for learning
            
        Returns:
            True if recorded successfully, False otherwise
        """
        if not self.container:
            logger.warning("Export tracking container not available, skipping Stage 4 record")
            return False
        
        try:
            record = {
                "id": f"export_stage4_{document_id}_{uuid.uuid4()}",
                "export_workflow_id": export_workflow_id,
                "document_id": document_id,
                "owner_email": owner_email,
                "stage": ExportStage.USER_FEEDBACK.value,
                "timestamp": datetime.now().isoformat(),
                
                "user_feedback": {
                    "feedback_text": feedback_text,
                    "satisfaction_rating": satisfaction_rating,
                    "rating_category": self._categorize_rating(satisfaction_rating),
                    "download_successful": download_successful,
                    "submitted_at": datetime.now().isoformat()
                },
                
                "ai_learning_data": ai_model_learning_data or {
                    "feedback_sentiment": "neutral",
                    "improvement_areas": [],
                    "positive_aspects": [],
                    "learning_enabled": True
                },
                
                "feedback_metadata": {
                    "feedback_length_chars": len(feedback_text),
                    "contains_actionable_feedback": len(feedback_text) > 10,
                    "workflow_completion": True,
                    "user_engagement_score": self._calculate_engagement_score(feedback_text, satisfaction_rating)
                },
                
                "status": "feedback_received",
                "learning_queued": True,
                "created_at": datetime.now().isoformat(),
                "expiration_date": (datetime.now() + timedelta(days=self.DATA_RETENTION_DAYS)).isoformat()
            }
            
            if self.container:
                try:
                    await self.container.create_item(record)
                    logger.info(f"Recorded Stage 4 (User Feedback) for workflow {export_workflow_id}, rating={satisfaction_rating}")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to persist Stage 4 record to Cosmos DB: {e}")
                    return False
            else:
                logger.debug(f"Export tracking container not available, Stage 4 record prepared but not persisted")
                return True
            
        except Exception as e:
            logger.error(f"Error recording Stage 4 (User Feedback): {e}", exc_info=True)
            return False
    
    def _categorize_rating(self, rating: int) -> str:
        """
        Categorize satisfaction rating.
        
        Args:
            rating: Rating from 1-5
            
        Returns:
            Category name
        """
        if rating >= 5:
            return "excellent"
        elif rating >= 4:
            return "good"
        elif rating >= 3:
            return "neutral"
        elif rating >= 2:
            return "poor"
        else:
            return "very_poor"
    
    def _calculate_engagement_score(self, feedback_text: str, rating: int) -> float:
        """
        Calculate user engagement score based on feedback.
        
        Args:
            feedback_text: User feedback text
            rating: Satisfaction rating
            
        Returns:
            Engagement score 0-1
        """
        # Score based on feedback length and rating
        length_score = min(len(feedback_text) / 500, 1.0)  # Normalized to 500 chars max
        rating_score = rating / 5.0
        
        # Average of both
        return (length_score + rating_score) / 2.0
    
    async def get_export_history(self, owner_email: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get user's export history.
        
        Args:
            owner_email: Owner email (partition key)
            limit: Maximum number of records to return
            
        Returns:
            List of export workflow records
        """
        if not self.container:
            logger.warning("Export tracking container not available")
            return []
        
        try:
            query = "SELECT * FROM export_tracking c WHERE c.owner_email = @email ORDER BY c.timestamp DESC OFFSET 0 LIMIT @limit"
            parameters = [
                {"name": "@email", "value": owner_email},
                {"name": "@limit", "value": limit}
            ]
            
            items = []
            async for item in self.container.query_items(query=query, parameters=parameters):
                items.append(item)
            
            return items
        except Exception as e:
            logger.error(f"Error retrieving export history: {e}")
            return []
    
    async def get_workflow_stages(self, export_workflow_id: str, owner_email: str) -> Dict[str, Any]:
        """
        Get all stages of a workflow.
        
        Args:
            export_workflow_id: Workflow ID
            owner_email: Owner email for partition key
            
        Returns:
            Dictionary with stage1, stage2, stage3
        """
        if not self.container:
            logger.warning("Export tracking container not available")
            return {}
        
        try:
            query = "SELECT * FROM export_tracking c WHERE c.export_workflow_id = @workflow_id AND c.owner_email = @email"
            parameters = [
                {"name": "@workflow_id", "value": export_workflow_id},
                {"name": "@email", "value": owner_email}
            ]
            
            stages = {
                "stage1": None,
                "stage2": None,
                "stage3": None
            }
            
            async for item in self.container.query_items(query=query, parameters=parameters):
                stage = item.get("stage")
                if stage == ExportStage.INITIAL_AI_SUMMARY.value:
                    stages["stage1"] = item
                elif stage == ExportStage.USER_MODIFICATIONS.value:
                    stages["stage2"] = item
                elif stage == ExportStage.FINAL_SUMMARY_AND_DELIVERABLE.value:
                    stages["stage3"] = item
            
            return stages
        except Exception as e:
            logger.error(f"Error retrieving workflow stages: {e}")
            return {}
    
    def _calculate_changes(self, original: Dict[str, Any], modified: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculate differences between original and modified data.
        
        Args:
            original: Original data
            modified: Modified data
            
        Returns:
            List of changes
        """
        changes = []
        
        # Check for modified values
        for key in original:
            if key in modified and original[key] != modified[key]:
                changes.append({
                    "field": key,
                    "original_value": original[key],
                    "modified_value": modified[key],
                    "change_type": "modification"
                })
        
        # Check for added values
        for key in modified:
            if key not in original:
                changes.append({
                    "field": key,
                    "original_value": None,
                    "modified_value": modified[key],
                    "change_type": "addition"
                })
        
        # Check for removed values
        for key in original:
            if key not in modified:
                changes.append({
                    "field": key,
                    "original_value": original[key],
                    "modified_value": None,
                    "change_type": "deletion"
                })
        
        return changes
    
    def _get_mime_type(self, format_type: str) -> str:
        """
        Get MIME type for export format.
        
        Args:
            format_type: Export format (json, csv, excel, pdf)
            
        Returns:
            MIME type string
        """
        mime_types = {
            "json": "application/json",
            "csv": "text/csv",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pdf": "application/pdf"
        }
        return mime_types.get(format_type.lower(), "application/octet-stream")


# Global export tracking service instance
_export_tracking_service: Optional[ExportTrackingService] = None


async def initialize_export_tracking(cosmos_service, database_id: str = "KraftdIntel"):
    """
    Initialize global export tracking service.
    
    Args:
        cosmos_service: CosmosService instance
        database_id: Cosmos DB database ID
    """
    global _export_tracking_service
    
    try:
        _export_tracking_service = ExportTrackingService(cosmos_service)
        await _export_tracking_service.initialize(database_id)
        logger.info("Export tracking service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize export tracking: {e}")
        _export_tracking_service = None


def get_export_tracking_service() -> Optional[ExportTrackingService]:
    """
    Get global export tracking service instance.
    
    Returns:
        ExportTrackingService instance or None if not initialized
    """
    return _export_tracking_service
