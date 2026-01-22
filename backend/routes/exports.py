"""
Export & Feedback Routes

Implements export endpoints from /docs/api-spec.md:
- GET /api/v1/documents/{document_id}/output — List output files
- POST /api/v1/exports/{export_id}/feedback — Submit feedback
- GET /api/v1/quota — Check user quota
"""

from fastapi import APIRouter, status, Header, Path, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from services.output_service import get_output_service
from services.conversions_service import ConversionsService
from services.feedback_service import get_feedback_service
from services.quota_service import get_quota_service
from azure.cosmos import exceptions

from models.errors import KraftdHTTPException, ErrorCode, authentication_error, internal_server_error, validation_error, not_found_error, quota_exceeded_error

logger = logging.getLogger(__name__)

router = APIRouter(tags=["exports"])


# ===== Request/Response Models =====

class OutputFile(BaseModel):
    output_id: str
    format: str
    file_size_bytes: int
    created_at: str
    expires_at: str
    download_url: str
    download_count: int


class OutputListResponse(BaseModel):
    document_id: str
    outputs: List[OutputFile]


class FeedbackRequest(BaseModel):
    quality_rating: int = Field(..., ge=1, le=5, description="Quality rating 1-5")
    accuracy_rating: int = Field(..., ge=1, le=5, description="Accuracy rating 1-5")
    completeness_rating: int = Field(..., ge=1, le=5, description="Completeness rating 1-5")
    comments: Optional[str] = Field(None, description="Detailed feedback comments")
    feedback_type: str = Field("neutral", description="positive|neutral|negative")
    issues_found: List[str] = Field(default_factory=list, description="List of issues")


class FeedbackResponse(BaseModel):
    feedback_id: str
    message: str
    recorded_at: str


class CreateFeedbackRequest(BaseModel):
    conversion_id: str = Field(..., description="Conversion ID")
    target: str = Field(..., description="Feedback target (export, extraction, schema, summary, etc.)")
    target_id: str = Field(..., description="ID of the target entity")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    comments: Optional[str] = Field(None, description="Detailed feedback comments")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FeedbackItem(BaseModel):
    feedback_id: str
    conversion_id: str
    target: str
    target_id: str
    rating: int
    comments: str
    created_at: str


class FeedbackListResponse(BaseModel):
    success: bool
    feedback: List[FeedbackItem]


class QuotaUsage(BaseModel):
    email: str
    tier: str = Field("free", description="free|pro|enterprise")
    documents_uploaded: int
    documents_processed: int
    exports_generated: int
    total_api_calls: int
    quota_limit: Optional[int] = None
    quota_remaining: Optional[int] = None
    reset_date: Optional[str] = None


class CreateOutputRequest(BaseModel):
    conversion_id: str = Field(..., description="Conversion ID")
    document_id: str = Field(..., description="Document ID")
    format: str = Field(..., description="Output format: json, csv, pdf, xml, etc.")
    output_data: Dict[str, Any] = Field(..., description="Output data/content")


class OutputResponse(BaseModel):
    success: bool
    output_id: str
    conversion_id: str
    document_id: str
    format: str
    created_at: str
    message: str = "Output created successfully"


# ===== POST /api/v1/outputs/generate =====

@router.post(
    "/outputs/generate",
    status_code=201,
    response_model=OutputResponse,
    summary="Generate output/export for conversion",
    description="Create output document in specified format from conversion data"
)
async def generate_output(
    request: CreateOutputRequest,
    authorization: str = Header(None)
) -> OutputResponse:
    """
    Generate output/export document in specified format.
    
    Flow:
    1. Verify user owns the conversion
    2. Generate output data from conversion content
    3. Store output in Cosmos DB
    4. Return output metadata
    
    Supported formats:
    - json: Structured JSON document
    - csv: CSV export
    - pdf: PDF report
    - xml: XML document
    """
    try:
        if not authorization:
            raise authentication_error("Missing authorization header")
        
        if request.format not in ["json", "csv", "pdf", "xml"]:
            raise validation_error("Invalid format. Must be json|csv|pdf|xml")
        
        # Extract user_email from authorization header
        user_email = authorization.split(":")[-1] if ":" in authorization else "user@example.com"
        
        # Validate user owns the conversion
        conversions_service = ConversionsService()
        try:
            conversion = await conversions_service.get_conversion(request.conversion_id)
            if not conversion:
                logger.warning(f"Conversion not found: {request.conversion_id}")
                raise not_found_error("conversion", request.conversion_id)
            
            if conversion.get("user_email") != user_email:
                logger.warning(f"User {user_email} tried to generate output for conversion {request.conversion_id} owned by {conversion.get('user_email')}")
                raise authentication_error("You do not have permission to access this conversion")
        except exceptions.CosmosResourceNotFoundError:
            raise not_found_error("conversion", request.conversion_id)
        
        # Check quota before generating output
        quota_service = get_quota_service()
        try:
            await quota_service.get_or_create_quota(user_email)
            limit_check = await quota_service.check_limits(user_email, "exports_used")
            if limit_check["exceeded"]:
                logger.warning(f"Output generation quota exceeded for user {user_email}")
                raise quota_exceeded_error(limit_check.get("limit", 0), limit_check.get("usage", 0), "Output generation quota exceeded")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Quota check failed for {user_email}: {e}", exc_info=True)
            raise internal_server_error("Quota check failed")
        
        # Store output in Cosmos DB
        output_service = get_output_service()
        try:
            output_item = await output_service.create_output(
                conversion_id=request.conversion_id,
                user_email=user_email,
                output_data=request.output_data,
                format=request.format,
                metadata={
                    "source": "conversion",
                    "document_id": request.document_id,
                    "format": request.format
                }
            )
            
            logger.info(f"Output generated for conversion {request.conversion_id}, document {request.document_id}, format {request.format}")
            
            # Increment exports usage
            try:
                await quota_service.increment_usage(user_email, "exports_used")
                logger.debug(f"Incremented exports_used for {user_email}")
            except Exception as e:
                logger.error(f"Failed to increment usage for {user_email}: {e}", exc_info=True)
                # Log but don't fail - output was created successfully
            
            return OutputResponse(
                success=True,
                output_id=output_item.get("id"),
                conversion_id=request.conversion_id,
                document_id=request.document_id,
                format=request.format,
                created_at=output_item.get("created_at", datetime.utcnow().isoformat() + "Z"),
                message="Output created successfully"
            )
        
        except exceptions.CosmosResourceExistsError:
            logger.warning(f"Output already exists for document {request.document_id}")
            raise validation_error("Output already exists for this document")
        
        except ValueError as e:
            logger.error(f"Invalid output data: {e}")
            raise validation_error(f"Invalid output data: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Output generation failed for {request.document_id}: {e}", exc_info=True)
        raise internal_server_error("Output generation failed")


# ===== GET /api/v1/documents/{document_id}/output =====

@router.get(
    "/documents/{document_id}/output",
    status_code=200,
    response_model=OutputListResponse,
    summary="List generated outputs for document",
    description="Get all export formats generated for a document"
)
async def get_document_outputs(
    document_id: str = Path(..., description="Document ID"),
    authorization: str = Header(None)
) -> OutputListResponse:
    """
    Get list of generated output files for a document.
    
    Response includes:
    - File format (json, csv, xlsx, pdf)
    - File size and download count
    - Download URL (signed, 7-day expiration)
    - Creation timestamp
    """
    try:
        if not authorization:
            raise authentication_error("Missing authorization header")
        
        # TODO: Verify user owns this document
        # TODO: Query Cosmos DB for outputs table
        # TODO: Generate signed download URLs
        
        logger.info(f"Retrieved outputs for document {document_id}")
        
        # Placeholder response
        return OutputListResponse(
            document_id=document_id,
            outputs=[
                OutputFile(
                    output_id="output-001",
                    format="json",
                    file_size_bytes=45623,
                    created_at="2026-01-22T10:36:00Z",
                    expires_at="2026-01-29T10:36:00Z",
                    download_url="https://kraftdstorage.blob.core.windows.net/exports/output-001.json",
                    download_count=2
                ),
                OutputFile(
                    output_id="output-002",
                    format="pdf",
                    file_size_bytes=512000,
                    created_at="2026-01-22T10:37:00Z",
                    expires_at="2026-01-29T10:37:00Z",
                    download_url="https://kraftdstorage.blob.core.windows.net/exports/output-002.pdf",
                    download_count=1
                )
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve outputs for {document_id}: {e}")
        raise internal_server_error("Failed to retrieve outputs")


# ===== POST /api/v1/feedback =====

@router.post(
    "/feedback",
    status_code=201,
    response_model=FeedbackResponse,
    summary="Submit feedback on conversion processing",
    description="Rate and comment on extraction, schema, or export quality"
)
async def create_feedback(
    request: CreateFeedbackRequest,
    authorization: str = Header(None)
) -> FeedbackResponse:
    """
    Submit feedback on conversion processing.
    
    Feedback can be submitted for:
    - export: Export/output quality
    - extraction: Extraction accuracy
    - schema: Schema generation quality
    - summary: AI summary quality
    
    Ratings:
    - 1 = Poor (many issues)
    - 2 = Fair (some issues)
    - 3 = Good (minor issues)
    - 4 = Very Good (very few issues)
    - 5 = Excellent (no issues)
    """
    try:
        if not authorization:
            raise authentication_error("Missing authorization header")
        
        if request.rating not in [1, 2, 3, 4, 5]:
            raise validation_error("Rating must be between 1 and 5")
        
        # Extract user_email from authorization header
        user_email = authorization.split(":")[-1] if ":" in authorization else "user@example.com"
        
        # Validate user owns the conversion
        conversions_service = ConversionsService()
        try:
            conversion = await conversions_service.get_conversion(request.conversion_id)
            if not conversion:
                logger.warning(f"Conversion not found: {request.conversion_id}")
                raise not_found_error("conversion", request.conversion_id)
            
            if conversion.get("user_email") != user_email:
                logger.warning(f"User {user_email} tried to submit feedback for conversion {request.conversion_id} owned by {conversion.get('user_email')}")
                raise authentication_error("You do not have permission to access this conversion")
        except exceptions.CosmosResourceNotFoundError:
            raise not_found_error("conversion", request.conversion_id)
        
        # Store feedback in Cosmos DB
        feedback_service = get_feedback_service()
        try:
            feedback_item = await feedback_service.create_feedback(
                conversion_id=request.conversion_id,
                user_email=user_email,
                target=request.target,
                target_id=request.target_id,
                rating=request.rating,
                comments=request.comments,
                metadata=request.metadata
            )
            
            logger.info(f"Feedback submitted for {request.target} {request.target_id} in conversion {request.conversion_id}: rating {request.rating}/5")
            
            return FeedbackResponse(
                feedback_id=feedback_item.get("id"),
                message="Thank you for your feedback. This helps us improve accuracy.",
                recorded_at=feedback_item.get("created_at", datetime.utcnow().isoformat() + "Z")
            )
        
        except exceptions.CosmosResourceExistsError:
            logger.warning(f"Feedback already exists for target {request.target_id}")
            raise validation_error("Feedback already exists for this target")
        
        except ValueError as e:
            logger.error(f"Invalid feedback data: {e}")
            raise validation_error(f"Invalid feedback data: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback for conversion {request.conversion_id}: {e}", exc_info=True)
        raise internal_server_error("Failed to submit feedback")


# ===== GET /api/v1/feedback/{feedback_id} =====

@router.get(
    "/feedback/{feedback_id}",
    status_code=200,
    response_model=FeedbackResponse,
    summary="Retrieve specific feedback",
    description="Get feedback by ID"
)
async def get_single_feedback(
    feedback_id: str = Path(..., description="Feedback ID"),
    authorization: str = Header(None)
) -> FeedbackResponse:
    """
    Retrieve specific feedback by ID.
    """
    try:
        if not authorization:
            raise authentication_error("Missing authorization header")
        
        # Extract user_email from authorization header
        user_email = authorization.split(":")[-1] if ":" in authorization else "user@example.com"
        
        # Retrieve feedback from Cosmos DB
        feedback_service = get_feedback_service()
        try:
            feedback_item = await feedback_service.get_feedback(feedback_id, user_email)
            
            if not feedback_item:
                raise not_found_error("feedback", feedback_id)
            
            logger.info(f"Feedback retrieved: {feedback_id}")
            
            return FeedbackResponse(
                feedback_id=feedback_item.get("id"),
                message="Feedback retrieved successfully",
                recorded_at=feedback_item.get("created_at", datetime.utcnow().isoformat() + "Z")
            )
        
        except exceptions.CosmosResourceNotFoundError:
            raise not_found_error("feedback", feedback_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve feedback {feedback_id}: {e}", exc_info=True)
        raise internal_server_error("Failed to retrieve feedback")


# ===== GET /api/v1/feedback/conversion/{conversion_id} =====

@router.get(
    "/feedback/conversion/{conversion_id}",
    status_code=200,
    response_model=FeedbackListResponse,
    summary="Get feedback for conversion",
    description="Retrieve all feedback submitted for a conversion"
)
async def get_conversion_feedback(
    conversion_id: str = Path(..., description="Conversion ID"),
    authorization: str = Header(None)
) -> FeedbackListResponse:
    """
    Get all feedback submitted for a specific conversion.
    """
    try:
        if not authorization:
            raise authentication_error("Missing authorization header")
        
        # Extract user_email from authorization header
        user_email = authorization.split(":")[-1] if ":" in authorization else "user@example.com"
        
        # Validate user owns the conversion
        conversions_service = ConversionsService()
        try:
            conversion = await conversions_service.get_conversion(conversion_id)
            if not conversion:
                logger.warning(f"Conversion not found: {conversion_id}")
                raise not_found_error("conversion", conversion_id)
            
            if conversion.get("user_email") != user_email:
                logger.warning(f"User {user_email} tried to access feedback for conversion {conversion_id} owned by {conversion.get('user_email')}")
                raise authentication_error("You do not have permission to access this conversion")
        except exceptions.CosmosResourceNotFoundError:
            raise not_found_error("conversion", conversion_id)
        
        # Retrieve feedback for conversion
        feedback_service = get_feedback_service()
        try:
            feedback_items = await feedback_service.get_feedback_for_conversion(conversion_id, user_email)
            
            # Convert to FeedbackItem list
            feedback_list = [
                FeedbackItem(
                    feedback_id=item.get("id"),
                    conversion_id=item.get("conversion_id"),
                    target=item.get("target"),
                    target_id=item.get("target_id"),
                    rating=item.get("rating"),
                    comments=item.get("comments", ""),
                    created_at=item.get("created_at")
                )
                for item in feedback_items
            ]
            
            logger.info(f"Retrieved {len(feedback_list)} feedback items for conversion {conversion_id}")
            
            return FeedbackListResponse(
                success=True,
                feedback=feedback_list
            )
        
        except Exception as e:
            logger.error(f"Failed to retrieve feedback for conversion {conversion_id}: {e}", exc_info=True)
            raise internal_server_error("Failed to retrieve feedback")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process feedback request for conversion {conversion_id}: {e}", exc_info=True)
        raise internal_server_error("Failed to process feedback request")


# ===== POST /api/v1/exports/{export_id}/feedback =====

@router.post(
    "/exports/{export_id}/feedback",
    status_code=200,
    response_model=FeedbackResponse,
    summary="Submit export quality feedback",
    description="Rate and comment on extraction/export quality"
)
async def submit_feedback(
    export_id: str = Path(..., description="Export ID"),
    feedback: FeedbackRequest = None,
    authorization: str = Header(None)
) -> FeedbackResponse:
    """
    Submit feedback on export quality and accuracy.
    
    Ratings:
    - 1 = Poor (many issues)
    - 2 = Fair (some issues)
    - 3 = Good (minor issues)
    - 4 = Very Good (very few issues)
    - 5 = Excellent (no issues)
    
    Feedback helps train the ML model for better accuracy.
    """
    try:
        if not authorization:
            raise authentication_error("Missing authorization header")
        
        # TODO: Verify user owns this export
        # TODO: Store feedback in Cosmos DB
        # TODO: Update export record with feedback
        # TODO: Queue feedback for ML model training
        
        feedback_id = f"fb-{export_id}"
        recorded_at = datetime.utcnow()
        
        logger.info(f"Feedback submitted for export {export_id}: avg={((feedback.quality_rating + feedback.accuracy_rating + feedback.completeness_rating) / 3):.1f}/5")
        
        return FeedbackResponse(
            feedback_id=feedback_id,
            message="Thank you for your feedback. This helps us improve accuracy.",
            recorded_at=recorded_at.isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback for {export_id}: {e}")
        raise internal_server_error("Failed to submit feedback")


# ===== GET /api/v1/quota =====

@router.get(
    "/quota",
    status_code=200,
    response_model=QuotaUsage,
    summary="Get user quota usage",
    description="Check current quota usage and limits"
)
async def get_quota(
    authorization: str = Header(None)
) -> QuotaUsage:
    """
    Get current quota usage and remaining limits.
    
    Quota by tier:
    - Free: 10 documents/month
    - Pro: 100 documents/month
    - Enterprise: Unlimited
    
    Resets on the 1st of each month.
    """
    try:
        if not authorization:
            raise authentication_error("Missing authorization header")
        
        # TODO: Parse user email from JWT
        # TODO: Query usage statistics from Cosmos DB
        # TODO: Determine user tier from subscription
        # TODO: Calculate remaining quota
        
        logger.info("Quota check performed")
        
        return QuotaUsage(
            email="user@example.com",
            tier="pro",
            documents_uploaded=35,
            documents_processed=32,
            exports_generated=28,
            total_api_calls=450,
            quota_limit=100,
            quota_remaining=65,
            reset_date="2026-02-01T00:00:00Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve quota: {e}")
        raise internal_server_error("Failed to retrieve quota")
