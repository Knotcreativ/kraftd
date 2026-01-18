"""Template Routes for KRAFTD Document Generation API

Endpoints for managing and generating documents from templates.
Implements LAYER 4: Workflow Intelligence - Document Templates.

Routes:
  GET    /api/v1/templates           - List all templates
  GET    /api/v1/templates/{id}      - Get template details
  POST   /api/v1/templates           - Create new template
  PUT    /api/v1/templates/{id}      - Update template
  DELETE /api/v1/templates/{id}      - Delete template
  POST   /api/v1/templates/{id}/generate - Generate document from template
  GET    /api/v1/templates/category/{category} - Get templates by category
  POST   /api/v1/templates/{id}/duplicate - Duplicate template
"""

import logging
from typing import Optional, Tuple
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Query, Body, Depends
from pydantic import BaseModel

from models.template import (
    Template, TemplateCategory, TemplateFormat,
    TemplateCreateRequest, TemplateUpdateRequest,
    TemplateGenerateRequest, TemplateGenerateResponse,
    TemplateListResponse, TemplateErrorResponse
)
from models.user import UserRole
from services.template_storage import TemplateStorageService, initialize_sample_templates
from services.template_service import TemplateService, TemplateValidationService
from services.rbac_service import RBACService, Permission
from middleware.rbac import (
    get_current_user_with_role, require_permission, require_authenticated
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

# Initialize sample templates on first import
_initialized = False
if not _initialized:
    try:
        initialize_sample_templates("system")
        _initialized = True
        logger.info("Sample templates initialized")
    except Exception as e:
        logger.warning(f"Could not initialize sample templates: {e}")




# ============================================================================
# LIST & RETRIEVE TEMPLATES
# ============================================================================

@router.get("", response_model=TemplateListResponse)
async def list_templates(
    category: Optional[TemplateCategory] = Query(None),
    created_by: Optional[str] = Query(None),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Tuple[str, UserRole] = Depends(require_authenticated())
):
    """
    List all templates with optional filtering
    
    Query Parameters:
      category: Filter by category (quotation_summary, comparison_matrix, purchase_order, etc.)
      created_by: Filter by creator user ID
      active_only: Only return active templates (default: true)
      skip: Number of results to skip (pagination)
      limit: Maximum results to return (1-100, default: 50)
    
    Returns:
      TemplateListResponse with templates array and metadata
    """
    try:
        email, role = current_user
        
        # Get filtered templates from storage
        templates = TemplateStorageService.get_templates(
            category=category,
            created_by=created_by,
            active_only=active_only
        )
        
        # Apply pagination
        total_count = len(templates)
        templates = templates[skip : skip + limit]
        
        logger.info(f"Listed {len(templates)} templates (total: {total_count}) by user {email}")
        
        return TemplateListResponse(
            total_count=total_count,
            templates=templates,
            filters_applied={
                "category": str(category) if category else None,
                "created_by": created_by,
                "active_only": active_only
            }
        )
        
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list templates: {str(e)}"
        )


@router.get("/{template_id}", response_model=Template)
async def get_template(
    template_id: str,
    current_user: Tuple[str, UserRole] = Depends(require_authenticated())
):
    """
    Get a specific template by ID
    
    Args:
      template_id: Template UUID
      
    Returns:
      Template object with all details
    """
    try:
        email, role = current_user
        
        template = TemplateStorageService.get_template(template_id)
        
        if not template:
            logger.warning(f"Template not found: {template_id} (requested by {email})")
            raise HTTPException(
                status_code=404,
                detail=f"Template '{template_id}' not found"
            )
        
        logger.debug(f"Retrieved template: {template_id} by user {email}")
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve template: {str(e)}"
        )


@router.get("/category/{category}", response_model=TemplateListResponse)
async def get_templates_by_category(
    category: TemplateCategory,
    current_user: Tuple[str, UserRole] = Depends(require_authenticated())
):
    """
    Get all templates in a specific category
    
    Args:
      category: Template category enum value
      
    Returns:
      TemplateListResponse with matching templates
    """
    try:
        email, role = current_user
        
        templates = TemplateStorageService.get_templates(
            category=category,
            active_only=True
        )
        
        logger.info(f"Retrieved {len(templates)} templates in category {category} by user {email}")
        
        return TemplateListResponse(
            total_count=len(templates),
            templates=templates,
            filters_applied={"category": str(category)}
        )
        
    except Exception as e:
        logger.error(f"Error retrieving templates by category: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve templates: {str(e)}"
        )


# ============================================================================
# CREATE & UPDATE TEMPLATES
# ============================================================================

@router.post("", response_model=Template, status_code=201)
async def create_template(
    request: TemplateCreateRequest = Body(...),
    current_user: Tuple[str, UserRole] = Depends(require_permission(Permission.TEMPLATES_CREATE))
):
    """
    Create a new template
    
    Request Body:
      name: Template name (1-100 chars, required)
      description: Optional description
      category: Template category (quotation_summary, comparison_matrix, etc.)
      format: Output format (html, pdf, docx, xlsx, json, email)
      content: Jinja2 template content
      variables: List of template variables with descriptions
      fields: List of field mappings for data extraction
      is_default: Whether this is default for its category
    
    Validation:
      - Template name must be 1-100 characters
      - Content must not be empty
      - Jinja2 syntax is validated
    
    Returns:
      Created Template object with ID and metadata
    """
    try:
        email, role = current_user
        
        # Validate Jinja2 syntax
        validation = TemplateValidationService.validate_jinja2_syntax(request.content)
        if not validation["valid"]:
            logger.warning(f"Invalid template syntax: {validation['error']} (by {email})")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid template syntax: {validation['error']}"
            )
        
        # Create template - use current user's email as creator
        template = TemplateStorageService.create_template(request, email)
        
        logger.info(f"Template created: {template.id} by {email} (role: {role})")
        
        # Log authorization decision
        rbac_service = RBACService()
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource="template",
            resource_id=template.id,
            action="create",
            allowed=True
        )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create template: {str(e)}"
        )


@router.put("/{template_id}", response_model=Template)
async def update_template(
    template_id: str,
    request: TemplateUpdateRequest = Body(...),
    current_user: Tuple[str, UserRole] = Depends(require_authenticated())
):
    """
    Update an existing template
    
    Args:
      template_id: Template UUID
      request: Update request with fields to modify
      
    Returns:
      Updated Template object
    """
    try:
        email, role = current_user
        
        # Check if template exists
        template = TemplateStorageService.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template '{template_id}' not found"
            )
        
        # Authorization: Admin can update any template, User can only update own
        rbac_service = RBACService()
        
        # Check if user has permission to update
        if role != UserRole.ADMIN:
            # Check ownership for non-admin users
            if template.created_by != email:
                logger.warning(f"Unauthorized template update attempt: {email} tried to update {template_id} created by {template.created_by}")
                rbac_service.log_authorization_decision(
                    user_email=email,
                    user_role=role,
                    resource="template",
                    resource_id=template_id,
                    action="update",
                    allowed=False
                )
                raise HTTPException(
                    status_code=403,
                    detail="You do not have permission to update this template"
                )
        
        # Validate new content if provided
        if request.content:
            validation = TemplateValidationService.validate_jinja2_syntax(request.content)
            if not validation["valid"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid template syntax: {validation['error']}"
                )
        
        # Update template
        updated = TemplateStorageService.update_template(template_id, request)
        
        logger.info(f"Template updated: {template_id} by {email} (role: {role})")
        
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource="template",
            resource_id=template_id,
            action="update",
            allowed=True
        )
        
        return updated
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update template: {str(e)}"
        )


# ============================================================================
# DELETE & DUPLICATE TEMPLATES
# ============================================================================

@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: str,
    current_user: Tuple[str, UserRole] = Depends(require_authenticated())
):
    """
    Delete a template
    
    Args:
      template_id: Template UUID
    """
    try:
        email, role = current_user
        
        # Get template to check ownership
        template = TemplateStorageService.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template '{template_id}' not found"
            )
        
        # Authorization: Admin can delete any template, User can only delete own
        rbac_service = RBACService()
        
        if role != UserRole.ADMIN:
            # Check ownership for non-admin users
            if template.created_by != email:
                logger.warning(f"Unauthorized template deletion attempt: {email} tried to delete {template_id} created by {template.created_by}")
                rbac_service.log_authorization_decision(
                    user_email=email,
                    user_role=role,
                    resource="template",
                    resource_id=template_id,
                    action="delete",
                    allowed=False
                )
                raise HTTPException(
                    status_code=403,
                    detail="You do not have permission to delete this template"
                )
        
        success = TemplateStorageService.delete_template(template_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Template '{template_id}' not found"
            )
        
        logger.info(f"Template deleted: {template_id} by {email} (role: {role})")
        
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource="template",
            resource_id=template_id,
            action="delete",
            allowed=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete template: {str(e)}"
        )


@router.post("/{template_id}/duplicate", response_model=Template, status_code=201)
async def duplicate_template(
    template_id: str,
    new_name: str = Query(..., min_length=1, max_length=100),
    current_user: Tuple[str, UserRole] = Depends(require_permission(Permission.TEMPLATES_CREATE))
):
    """
    Create a copy of an existing template
    
    Query Parameters:
      new_name: Name for the duplicated template
      
    Returns:
      New Template object
    """
    try:
        email, role = current_user
        
        # Check template exists
        template = TemplateStorageService.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template '{template_id}' not found"
            )
        
        duplicated = TemplateStorageService.duplicate_template(
            template_id, new_name, email
        )
        
        if not duplicated:
            raise HTTPException(
                status_code=404,
                detail=f"Template '{template_id}' not found"
            )
        
        logger.info(f"Template duplicated: {template_id} -> {duplicated.id} by {email} (role: {role})")
        
        rbac_service = RBACService()
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource="template",
            resource_id=duplicated.id,
            action="duplicate",
            allowed=True
        )
        
        return duplicated
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to duplicate template: {str(e)}"
        )


# ============================================================================
# GENERATE DOCUMENTS FROM TEMPLATES
# ============================================================================

@router.post("/{template_id}/generate", response_model=TemplateGenerateResponse)
async def generate_document(
    template_id: str,
    request: TemplateGenerateRequest = Body(...),
    current_user: Tuple[str, UserRole] = Depends(require_permission(Permission.DOCUMENTS_CREATE))
):
    """
    Generate a document from a template
    
    This endpoint renders a Jinja2 template with provided data and returns
    the generated document in the specified format.
    
    Request Body:
      template_id: Template UUID (in path)
      data: Dictionary of context variables for template rendering
      output_format: Optional format override (html, pdf, docx, xlsx, json, email)
      include_metadata: Include generation metadata in response
    
    Response:
      TemplateGenerateResponse with:
      - status: "success" or "error"
      - content: Rendered HTML/JSON content
      - content_base64: Binary content (PDF, DOCX, XLSX) base64 encoded
      - format: Output format
      - generated_at: Generation timestamp
      - file_name: Suggested filename
      - error_message: If error occurred
    
    Examples:
      Generate HTML quotation summary:
      {
        "template_id": "uuid...",
        "data": {
          "quote_title": "Quote-001",
          "supplier_name": "ACME Inc",
          "items": [
            {"description": "Widget", "quantity": 100, "unit_price": 10}
          ],
          "grand_total": 1000
        },
        "output_format": "html"
      }
    
    Returns:
      Generated document with content
    """
    try:
        email, role = current_user
        
        # Get template
        template = TemplateStorageService.get_template(template_id)
        if not template:
            logger.warning(f"Template not found: {template_id} (requested by {email})")
            raise HTTPException(
                status_code=404,
                detail=f"Template '{template_id}' not found"
            )
        
        # Record usage
        TemplateStorageService.record_usage(template_id)
        
        # Determine output format
        output_format = request.output_format or template.format
        
        # Generate document
        service = TemplateService()
        result = service.generate_document(
            template.content,
            request.data,
            str(output_format)
        )
        
        if not result.get("success"):
            logger.error(f"Document generation failed: {result.get('error')}")
            raise HTTPException(
                status_code=400,
                detail=f"Document generation failed: {result.get('error')}"
            )
        
        # Create response
        filename = f"{template.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        response = TemplateGenerateResponse(
            status="success",
            document_id=str(uuid4()),
            content=result.get("content"),
            format=output_format,
            generated_at=datetime.utcnow(),
            file_name=filename
        )
        
        logger.info(f"Document generated from template {template_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate document: {str(e)}"
        )


# ============================================================================
# TEMPLATE VALIDATION & PREVIEW
# ============================================================================

class TemplateValidateRequest(BaseModel):
    """Request to validate template syntax"""
    content: str


class TemplateValidateResponse(BaseModel):
    """Response from validation"""
    valid: bool
    variables: list
    error: Optional[str] = None


@router.post("/validate", response_model=TemplateValidateResponse)
async def validate_template_syntax(
    request: TemplateValidateRequest = Body(...),
    authorization: Optional[str] = Header(None)
):
    """
    Validate Jinja2 template syntax without saving
    
    Request Body:
      content: Template content to validate
    
    Returns:
      Validation result with variables found
    """
    try:
        validation = TemplateValidationService.validate_jinja2_syntax(request.content)
        
        return TemplateValidateResponse(
            valid=validation["valid"],
            variables=validation["variables"],
            error=validation.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error validating template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}"
        )


# ============================================================================
# STATISTICS & ADMIN
# ============================================================================

@router.get("/admin/statistics")
async def get_statistics(authorization: Optional[str] = Header(None)):
    """
    Get template system statistics (admin only)
    
    Returns:
      Statistics about stored templates, usage, categories, etc.
    """
    try:
        stats = TemplateStorageService.get_statistics()
        
        logger.debug("Template statistics retrieved")
        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            **stats
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )
