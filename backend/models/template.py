"""Template Models for KRAFTD Document Generation System

Implements LAYER 4: Workflow Intelligence - Document Templates

Templates enable dynamic generation of various procurement documents:
- Quotation Summaries (HTML, PDF)
- Comparison Matrices (Excel)
- Purchase Orders (DOCX, PDF)
- Invoice Templates (HTML, PDF)
- Custom Reports (Excel, PDF)

All templates use Jinja2 for variable substitution and business logic.
"""

from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TemplateCategory(str, Enum):
    """Available template categories"""
    QUOTATION_SUMMARY = "quotation_summary"
    COMPARISON_MATRIX = "comparison_matrix"
    PURCHASE_ORDER = "purchase_order"
    INVOICE = "invoice"
    CUSTOM_REPORT = "custom_report"
    EMAIL_NOTIFICATION = "email_notification"
    APPROVAL_FORM = "approval_form"


class TemplateFormat(str, Enum):
    """Output format for generated documents"""
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    JSON = "json"
    EMAIL = "email"


class TemplateVariable(BaseModel):
    """Variable used in template"""
    name: str
    description: str
    data_type: str  # string, number, date, array, object
    required: bool = True
    default_value: Optional[Any] = None
    example_value: Optional[Any] = None


class TemplateField(BaseModel):
    """Field configuration in template"""
    field_name: str
    source_path: str  # e.g., "quote.total_amount" or "supplier.name"
    data_type: str  # string, number, date, boolean, currency
    required: bool = True
    format_spec: Optional[str] = None  # e.g., "currency_2dp" or "date_mmddyyyy"
    validation_rule: Optional[str] = None  # e.g., "min:0|max:1000000"


class Template(BaseModel):
    """Core template document model"""
    id: str  # UUID-based template ID
    name: str
    description: Optional[str] = None
    category: TemplateCategory
    format: TemplateFormat
    content: str  # Jinja2 template content
    variables: List[TemplateVariable] = []
    fields: List[TemplateField] = []
    version: str = "1.0"
    is_active: bool = True
    is_default: bool = False
    created_by: str  # User ID
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Template name must be 1-100 characters"""
        if not v or len(v) < 1 or len(v) > 100:
            raise ValueError('Template name must be 1-100 characters')
        return v


class TemplateCreateRequest(BaseModel):
    """Request to create a new template"""
    name: str
    description: Optional[str] = None
    category: TemplateCategory
    format: TemplateFormat
    content: str  # Jinja2 template
    variables: List[TemplateVariable] = []
    fields: List[TemplateField] = []
    is_default: bool = False
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Template content must not be empty"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Template content cannot be empty')
        return v


class TemplateUpdateRequest(BaseModel):
    """Request to update an existing template"""
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[List[TemplateVariable]] = None
    fields: Optional[List[TemplateField]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class TemplateGenerateRequest(BaseModel):
    """Request to generate document from template"""
    template_id: str
    data: Dict[str, Any]  # Context variables for template rendering
    output_format: Optional[TemplateFormat] = None  # Override template's default format
    include_metadata: bool = False  # Include generation metadata in response


class TemplateGenerateResponse(BaseModel):
    """Response from template generation"""
    status: str  # "success" or "error"
    document_id: Optional[str] = None
    content: Optional[str] = None  # For HTML, JSON
    content_base64: Optional[str] = None  # For PDF, DOCX, XLSX (base64 encoded)
    format: TemplateFormat
    generated_at: datetime
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # If include_metadata=True


class TemplateListResponse(BaseModel):
    """Response from list templates endpoint"""
    total_count: int
    templates: List[Template]
    filters_applied: Optional[Dict[str, Any]] = None


class TemplateErrorResponse(BaseModel):
    """Error response for template endpoints"""
    status: str = "error"
    error_code: str
    error_message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
