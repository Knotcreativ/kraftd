"""
Documents Service

Business logic for document upload, storage, and metadata management.
Handles Azure Blob Storage integration and Cosmos DB metadata persistence.
"""

from fastapi import UploadFile
from uuid import uuid4
from datetime import datetime
import logging
from typing import Optional, Dict, List

from services.cosmos_service import CosmosService
from services.blob_service import get_blob_client, upload_file_to_blob, get_blob_uri

logger = logging.getLogger(__name__)


class DocumentsService:
    """Service for document upload and metadata management"""
    
    def __init__(self):
        """Initialize documents service"""
        self.cosmos_service = CosmosService()
        self.documents_container = "documents"
        self.conversions_container = "conversions"
    
    async def upload_document(
        self,
        file: UploadFile,
        conversion_id: str,
        user_email: str,
    ) -> Dict:
        """
        Upload document file to Azure Blob Storage and create metadata record.
        
        Args:
            file: FastAPI UploadFile object
            conversion_id: Associated conversion session ID
            user_email: User email (owner)
        
        Returns:
            DocumentResponse dict with document_id, blob_uri, metadata
        
        Raises:
            Exception: If upload or metadata creation fails
        """
        try:
            # Generate document ID
            document_id = str(uuid4())
            logger.info(f"Uploading document {document_id} for conversion {conversion_id}")
            
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            
            # Upload to Blob Storage
            blob_name = f"{conversion_id}/{document_id}/{file.filename}"
            blob_uri = await self._upload_to_blob_storage(
                blob_name=blob_name,
                content=file_content,
                content_type=file.content_type
            )
            logger.info(f"Document uploaded to blob: {blob_uri}")
            
            # Create metadata record in Cosmos DB
            now = datetime.utcnow().isoformat() + "Z"
            
            document_metadata = {
                "id": document_id,
                "document_id": document_id,
                "conversion_id": conversion_id,
                "user_email": user_email,
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": file_size,
                "blob_uri": blob_uri,
                "blob_name": blob_name,
                "status": "uploaded",
                "uploaded_at": now,
                "processing_started_at": None,
                "processing_completed_at": None,
                "error": None,
                "metadata": {
                    "ip_address": "unknown",  # Would get from request if available
                    "user_agent": "unknown"
                }
            }
            
            # Insert into Cosmos DB
            response = self.cosmos_service.create_item(
                container=self.documents_container,
                item=document_metadata
            )
            logger.info(f"Document metadata created in Cosmos DB: {document_id}")
            
            # Update conversion to include this document
            self._add_document_to_conversion(
                conversion_id=conversion_id,
                document_id=document_id,
                user_email=user_email
            )
            
            return {
                "document_id": document_id,
                "conversion_id": conversion_id,
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": file_size,
                "blob_uri": blob_uri,
                "uploaded_at": now,
                "status": "uploaded"
            }
            
        except Exception as e:
            logger.error(f"Document upload failed: {e}")
            raise
    
    async def _upload_to_blob_storage(
        self,
        blob_name: str,
        content: bytes,
        content_type: str
    ) -> str:
        """
        Upload file content to Azure Blob Storage.
        
        Args:
            blob_name: Blob path (e.g., "conversion-id/document-id/filename.pdf")
            content: File content bytes
            content_type: MIME type
        
        Returns:
            Full blob URI
        """
        try:
            # Upload using blob_service helper
            blob_uri = upload_file_to_blob(
                container_name="documents",
                blob_name=blob_name,
                file_content=content,
                content_type=content_type,
                overwrite=True
            )
            
            logger.debug(f"Blob uploaded: {blob_uri}")
            return blob_uri
            
        except Exception as e:
            logger.error(f"Blob storage upload failed: {e}")
            raise
    
    def get_document(
        self,
        document_id: str,
        user_email: str
    ) -> Optional[Dict]:
        """
        Retrieve document metadata from Cosmos DB.
        Verifies user owns the associated conversion.
        
        Args:
            document_id: Document ID to retrieve
            user_email: User email (must own conversion)
        
        Returns:
            Document metadata dict or None if not found/not owned
        """
        try:
            # Query document
            query = "SELECT * FROM documents WHERE documents.id = @id"
            parameters = [{"name": "@id", "value": document_id}]
            
            items = self.cosmos_service.query_items(
                container=self.documents_container,
                query=query,
                parameters=parameters
            )
            
            if not items or len(items) == 0:
                logger.warning(f"Document {document_id} not found")
                return None
            
            document = items[0]
            
            # Verify ownership
            if document.get("user_email") != user_email:
                logger.warning(f"User {user_email} attempted to access document {document_id} they don't own")
                return None
            
            logger.info(f"Document metadata retrieved: {document_id}")
            return {
                "document_id": document.get("document_id"),
                "conversion_id": document.get("conversion_id"),
                "filename": document.get("filename"),
                "content_type": document.get("content_type"),
                "file_size": document.get("file_size"),
                "blob_uri": document.get("blob_uri"),
                "status": document.get("status"),
                "uploaded_at": document.get("uploaded_at"),
                "processing_started_at": document.get("processing_started_at"),
                "processing_completed_at": document.get("processing_completed_at"),
                "error": document.get("error")
            }
            
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            raise
    
    def verify_conversion_ownership(
        self,
        conversion_id: str,
        user_email: str
    ) -> bool:
        """
        Verify that a user owns a conversion.
        
        Args:
            conversion_id: Conversion ID to check
            user_email: User email
        
        Returns:
            True if user owns conversion, False otherwise
        """
        try:
            query = "SELECT * FROM conversions WHERE conversions.id = @id"
            parameters = [{"name": "@id", "value": conversion_id}]
            
            items = self.cosmos_service.query_items(
                container=self.conversions_container,
                query=query,
                parameters=parameters
            )
            
            if not items or len(items) == 0:
                logger.warning(f"Conversion {conversion_id} not found")
                return False
            
            conversion = items[0]
            is_owner = conversion.get("user_email") == user_email
            
            if is_owner:
                logger.debug(f"Conversion {conversion_id} verified for {user_email}")
            else:
                logger.warning(f"User {user_email} does not own conversion {conversion_id}")
            
            return is_owner
            
        except Exception as e:
            logger.error(f"Conversion ownership verification failed: {e}")
            return False
    
    def _add_document_to_conversion(
        self,
        conversion_id: str,
        document_id: str,
        user_email: str
    ) -> bool:
        """
        Add document ID to conversion's documents array.
        
        Args:
            conversion_id: Conversion ID
            document_id: Document ID to add
            user_email: User email (for verification)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Query conversion
            query = "SELECT * FROM conversions WHERE conversions.id = @id"
            parameters = [{"name": "@id", "value": conversion_id}]
            
            items = self.cosmos_service.query_items(
                container=self.conversions_container,
                query=query,
                parameters=parameters
            )
            
            if not items or len(items) == 0:
                logger.warning(f"Conversion {conversion_id} not found for document addition")
                return False
            
            conversion = items[0]
            
            # Add document ID to array
            if "documents" not in conversion:
                conversion["documents"] = []
            
            if document_id not in conversion["documents"]:
                conversion["documents"].append(document_id)
            
            # Update in Cosmos DB
            self.cosmos_service.upsert_item(
                container=self.conversions_container,
                item=conversion
            )
            
            logger.info(f"Document {document_id} added to conversion {conversion_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document to conversion: {e}")
            return False
    
    def get_conversion_document_status(
        self,
        conversion_id: str
    ) -> Dict:
        """
        Get processing status for all documents in a conversion.
        
        Args:
            conversion_id: Conversion ID
        
        Returns:
            Status response with documents array and overall progress
        """
        try:
            query = """
                SELECT documents.id, documents.filename, documents.status, documents.error
                FROM documents
                WHERE documents.conversion_id = @conversion_id
            """
            parameters = [{"name": "@conversion_id", "value": conversion_id}]
            
            documents = self.cosmos_service.query_items(
                container=self.documents_container,
                query=query,
                parameters=parameters
            )
            
            # Calculate progress
            status_map = {
                "uploaded": 10,
                "processing": 50,
                "completed": 100,
                "failed": 0
            }
            
            documents_status = []
            total_progress = 0
            
            for doc in documents:
                status = doc.get("status", "uploaded")
                progress = status_map.get(status, 0)
                
                documents_status.append({
                    "document_id": doc.get("id"),
                    "filename": doc.get("filename"),
                    "status": status,
                    "progress": progress,
                    "error": doc.get("error")
                })
                
                total_progress += progress
            
            overall_progress = int(total_progress / len(documents)) if documents else 0
            
            logger.info(f"Status retrieved for conversion {conversion_id}: {len(documents)} documents")
            
            return {
                "conversion_id": conversion_id,
                "documents": documents_status,
                "overall_progress": overall_progress
            }
            
        except Exception as e:
            logger.error(f"Document status retrieval failed: {e}")
            raise
