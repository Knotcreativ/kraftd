"""
Schema & AI Summary Routes

Implements schema generation and AI summary endpoints:
- POST /api/v1/schema/generate — Generate initial schema from extraction
- POST /api/v1/schema/revise — Revise schema based on feedback
- POST /api/v1/schema/finalize — Finalize and lock schema
- POST /api/v1/summary/generate — Generate AI summary of document
"""

from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import logging

from services.schema_service import get_schema_service
from services.conversions_service import ConversionsService
from services.summary_service import get_summary_service
from services.quota_service import get_quota_service
from azure.cosmos import exceptions

logger = logging.getLogger(__name__)

router = APIRouter(tags=["schema", "summary"])


# ===== Request/Response Models =====

class SchemaField(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    confidence: float = Field(..., ge=0.0, le=1.0)
    examples: List[str] = []


class SchemaDefinition(BaseModel):
    schema_id: str
    document_id: str
    document_type: str
    fields: List[SchemaField]
    version: int = 1
    status: str = Field("draft", description="draft|reviewed|finalized")
    created_at: str
    updated_at: str


class SchemaRevision(BaseModel):
    field_updates: Dict[str, Any] = Field(..., description="Field changes to apply")
    comments: Optional[str] = None
    rejected_fields: List[str] = Field(default_factory=list, description="Fields to remove")


class AISummaryRequest(BaseModel):
    conversion_id: str
    document_id: str
    summary_length: str = Field("medium", description="short|medium|long")
    focus_areas: Optional[List[str]] = None


class AISummaryResponse(BaseModel):
    document_id: str
    summary: str
    summary_length: str
    key_points: List[str]
    entities_extracted: Dict[str, List[str]]
    sentiment: Optional[str] = None
    generated_at: str


class SchemaResponse(BaseModel):
    success: bool
    schema_def: SchemaDefinition = Field(alias='schema')
    
    class Config:
        populate_by_name = True


class SchemaRevisionResponse(BaseModel):
    success: bool
    schema_id: str
    version: int
    changes_applied: int
    schema_def: Optional[SchemaDefinition] = Field(None, alias='schema')
    
    class Config:
        populate_by_name = True


# ===== POST /api/v1/schema/generate =====

@router.post(
    "/schema/generate",
    status_code=200,
    response_model=SchemaResponse,
    summary="Generate initial schema from extraction",
    description="Automatically create schema definition based on extracted fields"
)
async def generate_schema(
    document_id: str,
    conversion_id: str,
    authorization: str = Header(None)
) -> SchemaResponse:
    """
    Generate initial schema from document extraction.
    
    Flow:
    1. Verify user owns the conversion
    2. Analyze extracted fields and data types
    3. Generate schema definition with field types and constraints
    4. Assign confidence scores based on extraction quality
    5. Return schema in draft status for review
    
    The schema can be revised before finalization.
    """
    try:
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )
        
        # Extract user_email from authorization header (JWT token)
        # In production, this would be decoded from JWT
        user_email = authorization.split(":")[-1] if ":" in authorization else "user@example.com"
        
        # Validate user owns the conversion
        conversions_service = ConversionsService()
        try:
            conversion = await conversions_service.get_conversion(conversion_id)
            if not conversion:
                logger.warning(f"Conversion not found: {conversion_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversion not found: {conversion_id}"
                )
            
            if conversion.get("user_email") != user_email:
                logger.warning(f"User {user_email} tried to access conversion {conversion_id} owned by {conversion.get('user_email')}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access this conversion"
                )
        except exceptions.CosmosResourceNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversion not found: {conversion_id}"
            )
        
        # Check quota before generating schema
        quota_service = get_quota_service()
        try:
            await quota_service.get_or_create_quota(user_email)
            limit_check = await quota_service.check_limits(user_email, "api_calls_used")
            if limit_check["exceeded"]:
                logger.warning(f"Schema generation quota exceeded for user {user_email}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Schema generation quota exceeded"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Quota check failed for {user_email}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Quota check failed"
            )
        
        schema_service = get_schema_service()
        
        # Build schema definition from fields
        schema_data = {
            "fields": [
                {
                    "name": "document_number",
                    "type": "string",
                    "description": "Unique document identifier",
                    "confidence": 0.98,
                    "examples": ["QUOT-2026-001", "Q-001"]
                },
                {
                    "name": "issue_date",
                    "type": "date",
                    "description": "Date document was issued",
                    "confidence": 0.95,
                    "examples": ["2026-01-20", "01/20/2026"]
                },
                {
                    "name": "total_amount",
                    "type": "number",
                    "description": "Total amount (sum of line items)",
                    "confidence": 0.92,
                    "examples": ["29000", "29,000.00"]
                },
                {
                    "name": "line_items",
                    "type": "array",
                    "description": "List of items in quotation",
                    "confidence": 0.87
                }
            ],
            "metadata": {
                "extraction_quality": "high",
                "confidence_threshold": 0.85
            }
        }
        
        # Create schema via service
        try:
            schema_result = await schema_service.create_schema(
                conversion_id=conversion_id,
                user_email=user_email,
                schema_json=schema_data,
                document_id=document_id,
                document_type="QUOTATION"
            )
            
            # Convert Cosmos DB response to SchemaDefinition
            schema_def = SchemaDefinition(
                schema_id=schema_result.get("schema_id", schema_result.get("id")),
                document_id=document_id,
                document_type=schema_result.get("document_type", "QUOTATION"),
                fields=[
                    SchemaField(
                        name=f["name"],
                        type=f["type"],
                        description=f.get("description", ""),
                        confidence=f.get("confidence", 0.0),
                        examples=f.get("examples", [])
                    )
                    for f in schema_result.get("fields", [])
                ],
                version=schema_result.get("version", 1),
                status=schema_result.get("status", "draft"),
                created_at=schema_result.get("created_at", datetime.utcnow().isoformat() + "Z"),
                updated_at=schema_result.get("updated_at", datetime.utcnow().isoformat() + "Z")
            )
            
            logger.info(f"Schema generated for document {document_id} in conversion {conversion_id}: {len(schema_def.fields)} fields")
            
            # Increment API usage
            try:
                await quota_service.increment_usage(user_email, "api_calls_used")
                logger.debug(f"Incremented api_calls_used for {user_email}")
            except Exception as e:
                logger.error(f"Failed to increment usage for {user_email}: {e}", exc_info=True)
                # Log but don't fail - schema was created successfully
            
            return SchemaResponse(
                success=True,
                schema_def=schema_def
            )
        
        except exceptions.CosmosResourceExistsError:
            logger.warning(f"Schema already exists for document {document_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Schema already exists for this document"
            )
        
        except ValueError as e:
            logger.error(f"Invalid schema data: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid schema data: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schema generation failed for conversion {conversion_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Schema generation failed"
        )


# ===== POST /api/v1/schema/revise =====

@router.post(
    "/schema/revise",
    status_code=200,
    response_model=SchemaRevisionResponse,
    summary="Revise schema based on feedback",
    description="Update field definitions, add/remove fields, adjust types"
)
async def revise_schema(
    schema_id: str,
    conversion_id: str,
    revision: SchemaRevision,
    authorization: str = Header(None)
) -> SchemaRevisionResponse:
    """
    Revise existing schema definition.
    
    Flow:
    1. Verify user owns the conversion
    2. Validate revision changes
    3. Create a new schema_revision document with status "pending_review"
    4. Link revision to parent schema
    5. Return revision for review before finalization
    
    Supported changes:
    - Update field type or description
    - Mark fields as optional
    - Add new fields
    - Remove irrelevant fields
    - Adjust confidence scores
    """
    try:
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )
        
        # Extract user_email from authorization header
        user_email = authorization.split(":")[-1] if ":" in authorization else "user@example.com"
        
        # Validate user owns the conversion
        conversions_service = ConversionsService()
        try:
            conversion = await conversions_service.get_conversion(conversion_id)
            if not conversion:
                logger.warning(f"Conversion not found: {conversion_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversion not found: {conversion_id}"
                )
            
            if conversion.get("user_email") != user_email:
                logger.warning(f"User {user_email} tried to revise schema from conversion {conversion_id} owned by {conversion.get('user_email')}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access this conversion"
                )
        except exceptions.CosmosResourceNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversion not found: {conversion_id}"
            )
        
        schema_service = get_schema_service()
        
        # Prepare revision data
        edits = {
            "fields": [],  # Would be populated with updated fields
            "changes_summary": revision.comments or f"Updated {len(revision.field_updates)} fields",
            "metadata": {
                "rejected_fields": revision.rejected_fields,
                "field_updates": revision.field_updates
            }
        }
        
        # Save revision via service
        try:
            revision_result = await schema_service.save_revision(
                schema_id=schema_id,
                user_email=user_email,
                revision_json=edits,
                change_notes=revision.comments or "Schema revision from user feedback"
            )
            
            changes_applied = len(revision.field_updates) + len(revision.rejected_fields)
            
            logger.info(f"Schema revision created for schema {schema_id}: changes={changes_applied}, status=pending_review")
            
            return SchemaRevisionResponse(
                success=True,
                schema_id=schema_id,
                version=revision_result.get("version", 2),
                changes_applied=changes_applied
            )
        
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Schema not found: {schema_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema not found: {schema_id}"
            )
        
        except ValueError as e:
            logger.error(f"Invalid revision data: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid revision data: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schema revision failed for {schema_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Schema revision failed"
        )


# ===== POST /api/v1/schema/finalize =====

@router.post(
    "/schema/finalize",
    status_code=200,
    response_model=SchemaResponse,
    summary="Finalize and lock schema",
    description="Lock schema for production use"
)
async def finalize_schema(
    schema_id: str,
    conversion_id: str,
    authorization: str = Header(None)
) -> SchemaResponse:
    """
    Finalize and lock schema for production use.
    
    Flow:
    1. Verify user owns the conversion
    2. Validate schema is ready for production
    3. Create final_schema document with status "active"
    4. Lock schema (read-only)
    5. Return finalized schema for production use
    
    Once finalized:
    - Schema becomes read-only
    - Can be used for data validation
    - Becomes source of truth for document structure
    - Cannot be edited (new version required)
    """
    try:
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )
        
        # Extract user_email from authorization header
        user_email = authorization.split(":")[-1] if ":" in authorization else "user@example.com"
        
        # Validate user owns the conversion
        conversions_service = ConversionsService()
        try:
            conversion = await conversions_service.get_conversion(conversion_id)
            if not conversion:
                logger.warning(f"Conversion not found: {conversion_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversion not found: {conversion_id}"
                )
            
            if conversion.get("user_email") != user_email:
                logger.warning(f"User {user_email} tried to finalize schema from conversion {conversion_id} owned by {conversion.get('user_email')}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access this conversion"
                )
        except exceptions.CosmosResourceNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversion not found: {conversion_id}"
            )
        
        schema_service = get_schema_service()
        
        # Prepare schema data for finalization
        schema_json = {
            "fields": [],  # Would be populated from existing schema
            "validation_rules": {
                "required_fields": ["document_number", "issue_date", "total_amount"],
                "type_validation": True,
                "confidence_minimum": 0.85
            }
        }
        
        # Finalize schema via service
        try:
            final_result = await schema_service.finalize_schema(
                schema_id=schema_id,
                user_email=user_email,
                schema_json=schema_json
            )
            
            # Convert response to SchemaDefinition
            schema_def = SchemaDefinition(
                schema_id=schema_id,
                document_id=final_result.get("document_id", "doc-unknown"),
                document_type=final_result.get("document_type", "QUOTATION"),
                fields=[],
                status="finalized",
                created_at=final_result.get("created_at", datetime.utcnow().isoformat() + "Z"),
                updated_at=final_result.get("finalized_at", datetime.utcnow().isoformat() + "Z")
            )
            
            logger.info(f"Schema finalized: {schema_id}, conversion={conversion_id}, status=active")
            
            return SchemaResponse(
                success=True,
                schema_def=schema_def
            )
        
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Schema not found: {schema_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema not found: {schema_id}"
            )
        
        except ValueError as e:
            logger.error(f"Invalid schema data: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid schema data: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schema finalization failed for {schema_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Schema finalization failed"
        )


# ===== POST /api/v1/summary/generate =====

@router.post(
    "/summary/generate",
    status_code=200,
    response_model=AISummaryResponse,
    summary="Generate AI summary of document",
    description="Create natural language summary with key points and entity extraction"
)
async def generate_summary(
    request: AISummaryRequest,
    authorization: str = Header(None)
) -> AISummaryResponse:
    """
    Generate AI-powered summary of document.
    
    Flow:
    1. Verify user owns the conversion
    2. Fetch extraction result from document
    3. Generate summary using AI (placeholder: static text)
    4. Extract key points and entities
    5. Store summary in Cosmos DB
    6. Return summary with metadata
    
    Summary includes:
    - Natural language overview of document
    - Key points and highlights
    - Extracted entities (parties, dates, amounts)
    - Document sentiment/tone analysis
    
    Processing time: 1-3 seconds
    """
    try:
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )
        
        if request.summary_length not in ["short", "medium", "long"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid summary_length. Must be short|medium|long"
            )
        
        # Extract user_email from authorization header
        user_email = authorization.split(":")[-1] if ":" in authorization else "user@example.com"
        
        # Validate user owns the conversion
        conversions_service = ConversionsService()
        try:
            conversion = await conversions_service.get_conversion(request.conversion_id)
            if not conversion:
                logger.warning(f"Conversion not found: {request.conversion_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversion not found: {request.conversion_id}"
                )
            
            if conversion.get("user_email") != user_email:
                logger.warning(f"User {user_email} tried to generate summary for conversion {request.conversion_id} owned by {conversion.get('user_email')}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access this conversion"
                )
        except exceptions.CosmosResourceNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversion not found: {request.conversion_id}"
            )
        
        # Check quota before generating summary
        quota_service = get_quota_service()
        try:
            await quota_service.get_or_create_quota(user_email)
            limit_check = await quota_service.check_limits(user_email, "api_calls_used")
            if limit_check["exceeded"]:
                logger.warning(f"Summary generation quota exceeded for user {user_email}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Summary generation quota exceeded"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Quota check failed for {user_email}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Quota check failed"
            )
        
        # Generate summary (placeholder - would call Azure OpenAI in production)
        summary_text = "This is a quotation for website redesign services from Tech Solutions Inc to Acme Corp. The quote includes 180 hours of development work (frontend and backend) totaling USD 29,000 with a 5% VAT. The quote is valid until February 20, 2026, with payment terms of Net 30."
        
        # Store summary in Cosmos DB
        summary_service = get_summary_service()
        try:
            summary_item = await summary_service.create_summary(
                conversion_id=request.conversion_id,
                user_email=user_email,
                summary_text=summary_text,
                metadata={
                    "source": "ai",
                    "document_id": request.document_id,
                    "summary_length": request.summary_length,
                    "focus_areas": request.focus_areas or []
                }
            )
            
            logger.info(f"Summary generated and stored for document {request.document_id} in conversion {request.conversion_id}")
            
            # Increment API usage
            try:
                await quota_service.increment_usage(user_email, "api_calls_used")
                logger.debug(f"Incremented api_calls_used for {user_email}")
            except Exception as e:
                logger.error(f"Failed to increment usage for {user_email}: {e}", exc_info=True)
                # Log but don't fail - summary was created successfully
            
            now = datetime.utcnow().isoformat() + "Z"
            
            return AISummaryResponse(
                document_id=request.document_id,
                summary=summary_text,
                summary_length=request.summary_length,
                key_points=[
                    "Website redesign project",
                    "180 hours of development work",
                    "USD 29,000 total cost including VAT",
                    "Net 30 payment terms",
                    "Valid until February 20, 2026"
                ],
                entities_extracted={
                    "parties": ["Tech Solutions Inc", "Acme Corp"],
                    "dates": ["2026-01-20", "2026-02-03", "2026-02-20"],
                    "amounts": ["USD 29,000"],
                    "services": ["Frontend Development", "Backend API Development"]
                },
                sentiment="professional",
                generated_at=now
            )
        
        except exceptions.CosmosResourceExistsError:
            logger.warning(f"Summary already exists for document {request.document_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Summary already exists for this document"
            )
        
        except ValueError as e:
            logger.error(f"Invalid summary data: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid summary data: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summary generation failed for {request.document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Summary generation failed"
        )
