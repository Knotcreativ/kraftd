"""
Document Models

Pydantic models for document upload request/response data.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status enum"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadRequest(BaseModel):
    """Request body for document upload (multipart/form-data)"""
    conversion_id: str = Field(..., description="Associated conversion session ID")
    # file: UploadFile handled by FastAPI route parameter
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversion_id": "conv-abc123"
            }
        }


class DocumentResponse(BaseModel):
    """Response model for document upload"""
    document_id: str = Field(..., description="Unique document identifier (UUID)")
    conversion_id: str = Field(..., description="Associated conversion ID")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type (e.g., application/pdf)")
    file_size: int = Field(..., description="File size in bytes")
    blob_uri: str = Field(..., description="Azure Blob Storage URI")
    uploaded_at: str = Field(..., description="ISO 8601 timestamp")
    status: str = Field(
        default="uploaded",
        description="Processing status: uploaded | processing | completed | failed"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc-abc123",
                "conversion_id": "conv-xyz789",
                "filename": "invoice.pdf",
                "content_type": "application/pdf",
                "file_size": 245000,
                "blob_uri": "https://kraftdblob.blob.core.windows.net/documents/conv-xyz789/doc-abc123/invoice.pdf",
                "uploaded_at": "2026-01-22T10:30:00Z",
                "status": "uploaded"
            }
        }


class DocumentMetadataResponse(DocumentResponse):
    """Detailed document metadata response"""
    processing_started_at: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp when processing started"
    )
    processing_completed_at: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp when processing completed"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if processing failed"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc-abc123",
                "conversion_id": "conv-xyz789",
                "filename": "invoice.pdf",
                "content_type": "application/pdf",
                "file_size": 245000,
                "blob_uri": "https://kraftdblob.blob.core.windows.net/documents/conv-xyz789/doc-abc123/invoice.pdf",
                "uploaded_at": "2026-01-22T10:30:00Z",
                "status": "processing",
                "processing_started_at": "2026-01-22T10:30:15Z",
                "processing_completed_at": None,
                "error": None
            }
        }


class DocumentStatusItem(BaseModel):
    """Single document status in list"""
    document_id: str = Field(..., description="Document UUID")
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Current processing status")
    progress: int = Field(..., description="Progress percentage 0-100")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc-abc123",
                "filename": "invoice.pdf",
                "status": "processing",
                "progress": 50,
                "error": None
            }
        }


class DocumentStatusResponse(BaseModel):
    """Response for document processing status"""
    conversion_id: str = Field(..., description="The conversion ID")
    documents: List[DocumentStatusItem] = Field(
        ...,
        description="List of document statuses"
    )
    overall_progress: int = Field(
        ...,
        description="Average progress percentage across all documents"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversion_id": "conv-xyz789",
                "documents": [
                    {
                        "document_id": "doc-001",
                        "filename": "invoice.pdf",
                        "status": "completed",
                        "progress": 100,
                        "error": None
                    },
                    {
                        "document_id": "doc-002",
                        "filename": "quote.xlsx",
                        "status": "processing",
                        "progress": 50,
                        "error": None
                    }
                ],
                "overall_progress": 75
            }
        }
