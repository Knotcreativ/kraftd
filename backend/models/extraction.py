"""
Extraction data models for multi-document OCR/Document Intelligence results.

Comprehensive structure includes:
- Timestamp + Owner ID
- Document metadata (uploaded doc + extraction data per document)
- AI model summary after review
- User modifications + conversion preferences
- Transformed document data with ID + AI summary
- Download confirmation + feedback
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Document upload metadata."""
    file_name: str
    file_type: str  # PDF, DOCX, XLSX, IMAGE
    file_size_bytes: Optional[int] = None
    uploaded_at: datetime
    file_hash: Optional[str] = None  # For duplicate detection


class ExtractionData(BaseModel):
    """Raw extraction data from OCR/Document Intelligence."""
    text: str
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)  # Base64 or URLs
    key_value_pairs: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extraction_method: str  # "direct_parse", "ocr", "azure_di"
    extraction_duration_ms: int = 0


class AIAnalysisSummary(BaseModel):
    """AI model analysis after document review."""
    key_insights: str
    supplier_information: Optional[Dict[str, Any]] = None
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    model_used: str = "gpt-4o-mini"
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserModification(BaseModel):
    """User-made modifications to extracted data."""
    original_field: str
    original_value: Any
    modified_value: Any
    modification_reason: Optional[str] = None
    modified_at: datetime
    modified_by: str  # User email


class UserModifications(BaseModel):
    """Container for all user modifications."""
    modifications: List[UserModification] = Field(default_factory=list)
    total_modifications: int = 0
    last_modified_at: Optional[datetime] = None
    last_modified_by: Optional[str] = None


class ConversionPreferences(BaseModel):
    """User preferences for document conversion/export."""
    output_format: str = "pdf"  # pdf, json, csv, xlsx
    include_ai_summary: bool = True
    include_original_extraction: bool = True
    include_user_modifications: bool = True
    timezone: Optional[str] = None
    language: Optional[str] = None
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class TransformedDocumentData(BaseModel):
    """Final transformed/processed document data."""
    document_data: Dict[str, Any]
    ai_summary_integrated: Dict[str, Any]
    user_modifications_applied: bool = False
    transformation_id: str
    transformation_timestamp: datetime
    transformation_method: str


class DownloadInfo(BaseModel):
    """Download tracking information."""
    download_count: int = 0
    last_downloaded_at: Optional[datetime] = None
    download_urls: Dict[str, str] = Field(default_factory=dict)  # format -> URL
    export_status: str = "ready"  # pending, processing, ready, failed


class Feedback(BaseModel):
    """User feedback on extraction quality and results."""
    quality_rating: Optional[int] = None  # 1-5
    accuracy_rating: Optional[int] = None  # 1-5
    completeness_rating: Optional[int] = None  # 1-5
    comments: Optional[str] = None
    feedback_type: Optional[str] = None  # positive, negative, neutral, suggestion
    submitted_at: Optional[datetime] = None
    submitted_by: Optional[str] = None


class ExtractionRecord(BaseModel):
    """
    Complete extraction record for a single document from a single source.
    
    Partition key: /owner_email
    ID format: {document_id}:{source}
    """
    # Identity
    id: str = Field(default="", description="Format: {document_id}:{source}")
    owner_email: str  # Partition key
    document_id: str
    source: str  # "direct_parse", "ocr", "azure_di"
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Document Information
    document: DocumentMetadata
    
    # Raw Extraction Data
    extraction_data: ExtractionData
    
    # AI Analysis Summary
    ai_summary: Optional[AIAnalysisSummary] = None
    
    # User Modifications
    user_modifications: UserModifications = Field(default_factory=UserModifications)
    
    # Conversion Preferences
    conversion_preferences: ConversionPreferences = Field(default_factory=ConversionPreferences)
    
    # Transformed Data
    transformed_data: Optional[TransformedDocumentData] = None
    
    # Download Information
    download_info: DownloadInfo = Field(default_factory=DownloadInfo)
    
    # Feedback
    feedback: Optional[Feedback] = None
    
    # Status & Metadata
    status: str = "extracted"  # extracted, reviewed, transformed, exported, archived
    tags: List[str] = Field(default_factory=list)
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc-001:direct_parse",
                "owner_email": "user@example.com",
                "document_id": "doc-001",
                "source": "direct_parse",
                "created_at": "2026-01-19T10:30:00Z",
                "updated_at": "2026-01-19T10:35:00Z",
                "document": {
                    "file_name": "supplier_quotation.pdf",
                    "file_type": "PDF",
                    "file_size_bytes": 2048576,
                    "uploaded_at": "2026-01-19T10:30:00Z",
                    "file_hash": "abc123..."
                },
                "status": "extracted"
            }
        }
