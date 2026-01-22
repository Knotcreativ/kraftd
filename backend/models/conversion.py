"""
Conversion Models

Pydantic models for conversion session request/response data.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ConversionStatus(str, Enum):
    """Conversion session status enum"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class ConversionCreate(BaseModel):
    """Request body for creating a new conversion"""
    user_id: str = Field(..., description="User's unique ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "usr-abc123"
            }
        }


class ConversionResponse(BaseModel):
    """Response model for conversion metadata"""
    conversion_id: str = Field(..., description="Unique conversion identifier (UUID)")
    user_id: str = Field(..., description="User's unique ID")
    status: str = Field(
        ...,
        description="Conversion status: in_progress | completed | failed"
    )
    started_at: str = Field(..., description="ISO 8601 timestamp when conversion started")
    completed_at: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp when conversion completed (null if not complete)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversion_id": "conv-abc123",
                "user_id": "usr-xyz789",
                "status": "in_progress",
                "started_at": "2026-01-22T10:30:00Z",
                "completed_at": None
            }
        }


class ConversionDetail(ConversionResponse):
    """Detailed conversion response with documents and metadata"""
    documents: List[str] = Field(
        default_factory=list,
        description="List of document IDs in this conversion"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata (IP, user agent, etc.)"
    )
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversion_id": "conv-abc123",
                "user_id": "usr-xyz789",
                "status": "in_progress",
                "started_at": "2026-01-22T10:30:00Z",
                "completed_at": None,
                "documents": ["doc-001", "doc-002"],
                "metadata": {},
                "updated_at": "2026-01-22T10:35:00Z"
            }
        }


class ConversionListResponse(BaseModel):
    """Response for listing user's conversions"""
    conversions: List[ConversionDetail] = Field(
        ...,
        description="List of conversion records"
    )
    total: int = Field(..., description="Total number of conversions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversions": [
                    {
                        "conversion_id": "conv-abc123",
                        "user_id": "usr-xyz789",
                        "status": "completed",
                        "started_at": "2026-01-22T10:30:00Z",
                        "completed_at": "2026-01-22T10:35:00Z",
                        "documents": ["doc-001"],
                        "metadata": {},
                        "updated_at": "2026-01-22T10:35:00Z"
                    }
                ],
                "total": 1
            }
        }
