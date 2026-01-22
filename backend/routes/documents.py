"""
Documents API Routes

Implements the Documents endpoints defined in /docs/api-spec.md:
- POST /api/v1/documents/upload — Upload a document file
- GET /api/v1/documents/:document_id — Get document metadata
- GET /api/v1/documents/:conversion_id/status — Get document processing status
"""

from fastapi import APIRouter, Header, UploadFile, File, Form, Request, HTTPException
from typing import Optional
import uuid
import logging

from services.documents_service import DocumentsService
from services.auth_service import AuthService
from models.document import DocumentResponse, DocumentMetadataResponse
from middleware.quota import check_quota

# Import standardized error handling
from models.errors import (
    KraftdHTTPException, ErrorCode, validation_error,
    authentication_error, authorization_error, not_found_error, quota_exceeded_error, internal_server_error
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])
documents_service = DocumentsService()
auth_service = AuthService()


def get_current_user_email(authorization: str = Header(None)) -> str:
    """
    Extract and validate the current user email from JWT token.
    
    Args:
        authorization: Bearer token from Authorization header
        
    Returns:
        User email from token payload
        
    Raises:
        KraftdHTTPException: 401 if token is missing, invalid, or expired
    """
    if not authorization:
        raise authentication_error("Missing authorization header")
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise authentication_error("Invalid authorization header format")
    
    token = parts[1]
    
    try:
        # Verify token using auth service
        payload = auth_service.verify_token(token)
        
        if payload is None:
            raise authentication_error("Invalid or expired token")
        
        email = payload.get("sub")
        if email is None:
            raise authentication_error("Invalid token")
        
        return email
        
    except KraftdHTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise authentication_error("Token verification failed")


# ===== POST /api/v1/documents/upload =====

@router.post(
    "/upload",
    status_code=201,
    response_model=DocumentResponse,
    summary="Upload a document file",
    description="Uploads a document file to Azure Blob Storage and stores metadata in Cosmos DB"
)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    conversion_id: str = Form(...),
    authorization: str = Header(None),
) -> DocumentResponse:
    """
    Upload a document file to Azure Blob Storage.
    
    Flow:
    1. Authenticate user via JWT
    2. Validate conversion_id ownership (user owns the conversion)
    3. Validate file (size, type)
    4. Upload to Azure Blob Storage
    5. Create metadata record in Cosmos DB Documents table
    6. Return document metadata
    
    Request:
        - file: Binary file upload (PDF, DOCX, Excel, Image)
        - conversion_id: UUID of the conversion session
        - Authorization: Bearer token
    
    Response:
        - document_id: Unique document identifier (UUID)
        - conversion_id: Associated conversion ID
        - filename: Original filename
        - content_type: MIME type
        - file_size: Size in bytes
        - blob_uri: Azure Blob Storage URI
        - uploaded_at: ISO 8601 timestamp
        - status: "uploaded" (processing status)
        
    Raises:
        401: Invalid or missing token
        403: User doesn't own the conversion
        404: Conversion not found
        413: File too large (>100MB)
        415: Unsupported file type
        429: Quota exceeded
        500: Upload or database error
    """
    try:
        # Step 1: Authenticate user
        user_email = get_current_user_email(authorization)
        logger.info(f"Document upload initiated by {user_email} for conversion {conversion_id}")
        
        # Step 2: Check quota
        quota_ok = await check_quota(user_email, tier="free")
        if not quota_ok:
            logger.warning(f"Quota exceeded for {user_email}")
            raise quota_exceeded_error(
                limit=0,  # Will be updated when quota service provides details
                usage=0,
                message="User quota exceeded"
            )
        
        # Step 3: Validate conversion ownership
        conversion_owner = documents_service.verify_conversion_ownership(
            conversion_id=conversion_id,
            user_email=user_email
        )
        if not conversion_owner:
            logger.warning(f"User {user_email} attempted to upload to conversion {conversion_id} they don't own")
            raise KraftdHTTPException(ErrorCode.INSUFFICIENT_PERMISSIONS, "User does not own this conversion")
        
        # Step 4: Validate file
        if file.size and file.size > 100 * 1024 * 1024:  # 100MB limit
            logger.warning(f"File too large: {file.size} bytes for {user_email}")
            raise validation_error("File size exceeds 100MB limit")
        
        allowed_types = {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "image/jpeg",
            "image/png",
            "image/tiff"
        }
        
        if file.content_type not in allowed_types:
            logger.warning(f"Unsupported file type: {file.content_type} for {user_email}")
            raise validation_error(f"Unsupported file type: {file.content_type}")
        
        # Step 5: Upload to Blob Storage and create metadata
        document_response = await documents_service.upload_document(
            file=file,
            conversion_id=conversion_id,
            user_email=user_email
        )
        
        logger.info(f"Document {document_response.document_id} uploaded successfully by {user_email}")
        return document_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise internal_server_error("Document upload failed")


# ===== GET /api/v1/documents/:document_id =====

@router.get(
    "/{document_id}",
    status_code=200,
    response_model=DocumentMetadataResponse,
    summary="Get document metadata",
    description="Retrieves metadata for a specific document"
)
async def get_document(
    request: Request,
    document_id: str,
    authorization: str = Header(None),
) -> DocumentMetadataResponse:
    """
    Get document metadata.
    
    Flow:
    1. Authenticate user via JWT
    2. Fetch document from Cosmos DB
    3. Verify user ownership (user owns the conversion)
    4. Return document metadata
    
    Response:
        - document_id: Unique document identifier
        - conversion_id: Associated conversion
        - filename: Original filename
        - content_type: MIME type
        - file_size: Size in bytes
        - blob_uri: Azure Blob Storage URI
        - status: Current processing status
        - uploaded_at: ISO 8601 timestamp
        - processing_started_at: When extraction started
        - processing_completed_at: When extraction finished
        
    Raises:
        401: Invalid or missing token
        403: User doesn't own the document's conversion
        404: Document not found
        500: Database error
    """
    try:
        # Step 1: Authenticate user
        user_email = get_current_user_email(authorization)
        logger.info(f"Document metadata request for {document_id} by {user_email}")
        
        # Step 2 & 3: Fetch and verify ownership
        document = documents_service.get_document(
            document_id=document_id,
            user_email=user_email
        )
        
        if not document:
            logger.warning(f"Document {document_id} not found or not owned by {user_email}")
            raise not_found_error("document", document_id)
        
        logger.info(f"Document metadata retrieved for {document_id}")
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document retrieval error: {e}")
        raise internal_server_error("Failed to retrieve document")


# ===== GET /api/v1/documents/:conversion_id/status =====

@router.get(
    "/{conversion_id}/status",
    status_code=200,
    summary="Get document processing status",
    description="Retrieves the processing status of all documents in a conversion"
)
async def get_document_status(
    request: Request,
    conversion_id: str,
    authorization: str = Header(None),
):
    """
    Get processing status for all documents in a conversion.
    
    Response:
        - conversion_id: The conversion ID
        - documents: List of document statuses
            - document_id: UUID
            - filename: Original filename
            - status: "uploaded" | "processing" | "completed" | "failed"
            - progress: 0-100 percent
            - error: Error message if status is "failed"
        - overall_progress: Average progress across all documents
        
    Raises:
        401: Invalid or missing token
        403: User doesn't own the conversion
        404: Conversion not found
        500: Database error
    """
    try:
        # Authenticate user
        user_email = get_current_user_email(authorization)
        logger.info(f"Document status request for conversion {conversion_id} by {user_email}")
        
        # Verify conversion ownership
        conversion_owner = documents_service.verify_conversion_ownership(
            conversion_id=conversion_id,
            user_email=user_email
        )
        if not conversion_owner:
            logger.warning(f"User {user_email} attempted to access conversion {conversion_id} they don't own")
            raise KraftdHTTPException(ErrorCode.INSUFFICIENT_PERMISSIONS, "User does not own this conversion")
        
        # Get status
        status_response = documents_service.get_conversion_document_status(
            conversion_id=conversion_id
        )
        
        logger.info(f"Document status retrieved for conversion {conversion_id}")
        return status_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status retrieval error: {e}")
        raise internal_server_error("Failed to retrieve document status")
