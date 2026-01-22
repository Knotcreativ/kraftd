"""
Conversions API Routes

Implements the Conversions endpoints defined in /docs/api-spec.md:
- POST /api/v1/conversions — Create a new conversion session
- GET /api/v1/conversions/:conversion_id — Get conversion metadata
"""

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid
import logging

from models.conversion import ConversionCreate, ConversionResponse, ConversionStatus
from services.conversions_service import ConversionsService
from services.auth_service import AuthService
from services.quota_service import get_quota_service
from middleware.quota import check_quota

# Import standardized error handling
from models.errors import (
    KraftdHTTPException, ErrorCode, validation_error,
    authentication_error, not_found_error, quota_exceeded_error, internal_server_error
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversions", tags=["conversions"])
conversions_service = ConversionsService()
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


# ===== POST /api/v1/conversions =====

@router.post(
    "",
    status_code=201,
    response_model=ConversionResponse,
    summary="Create a new conversion session",
    description="Creates a new conversion session. Checks user quota before creation."
)
async def create_conversion(
    request: Request,
    authorization: str = Header(None)
) -> ConversionResponse:
    """
    Create a new conversion session.
    
    Flow:
    1. Authenticate user via JWT
    2. Check user quota (via middleware)
    3. Generate conversion_id (UUID)
    4. Create record in Conversions table
    5. Return conversion metadata
    
    Args:
        authorization: Bearer token (JWT)
    
    Returns:
        ConversionResponse with conversion_id and status
    
    Raises:
        401 UNAUTHORIZED — Invalid or missing token
        429 QUOTA_EXCEEDED — User at quota limit
        500 INTERNAL_SERVER_ERROR — Database error
    
    Example:
        POST /api/v1/conversions
        Authorization: Bearer eyJhbGc...
        
        Response (201):
        {
            "conversion_id": "conv-abc123",
            "user_id": "usr-xyz789",
            "status": "in_progress",
            "started_at": "2026-01-22T10:30:00Z",
            "completed_at": null
        }
    """
    try:
        # 1. Authenticate user
        user_email = get_current_user_email(authorization)
        if not user_email:
            raise authentication_error("Invalid or missing authentication token")
        
        logger.info(f"Creating conversion for user: {user_email}")
        
        # 2. Check quota via QuotaService
        quota_service = get_quota_service()
        try:
            # Initialize or retrieve existing quota
            await quota_service.get_or_create_quota(user_email)
            
            # Check if user has exceeded conversions limit
            limit_check = await quota_service.check_limits(user_email, "conversions_used")
            if limit_check["exceeded"]:
                logger.warning(f"Conversion quota exceeded for user {user_email}")
                raise quota_exceeded_error(
                    limit=limit_check["limit"],
                    usage=limit_check["usage"],
                    message="User has reached their conversion quota"
                )
        except Exception as e:
            logger.error(f"Quota check failed for {user_email}: {e}", exc_info=True)
            raise internal_server_error("Quota check failed")
        
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise not_found_error("user", user_email)
        
        # 3. Create conversion
        conversion_id = str(uuid.uuid4())
        conversion = await conversions_service.create_conversion(
            conversion_id=conversion_id,
            user_email=user_email,
            user_id=user.get('user_id')
        )
        
        # 4. Increment conversion usage
        try:
            await quota_service.increment_usage(user_email, "conversions_used")
            logger.debug(f"Incremented conversions_used for {user_email}")
        except Exception as e:
            logger.error(f"Failed to increment usage for {user_email}: {e}", exc_info=True)
            # Log but don't fail - conversion was created successfully
        
        logger.info(f"Conversion created: {conversion_id} for user: {user_email}")
        
        # 5. Return response
        return ConversionResponse(
            conversion_id=conversion['conversion_id'],
            user_id=conversion['user_id'],
            status=conversion['status'],
            started_at=conversion['started_at'],
            completed_at=conversion.get('completed_at')
        )
    
    except KraftdHTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating conversion: {str(e)}", exc_info=True)
        raise internal_server_error("Failed to create conversion session")


# ===== GET /api/v1/conversions/:conversion_id =====

@router.get(
    "/{conversion_id}",
    response_model=ConversionResponse,
    summary="Get conversion metadata",
    description="Retrieve metadata for a specific conversion session"
)
async def get_conversion(
    conversion_id: str,
    authorization: str = Header(None)
) -> ConversionResponse:
    """
    Get conversion metadata and status.
    
    Flow:
    1. Authenticate user via JWT
    2. Fetch conversion from database
    3. Verify user ownership
    4. Return conversion metadata
    
    Args:
        conversion_id: UUID of the conversion to fetch
        authorization: Bearer token (JWT)
    
    Returns:
        ConversionResponse with complete metadata
    
    Raises:
        401 UNAUTHORIZED — Invalid or missing token
        403 FORBIDDEN — User does not own this conversion
        404 NOT_FOUND — Conversion does not exist
        500 INTERNAL_SERVER_ERROR — Database error
    
    Example:
        GET /api/v1/conversions/conv-abc123
        Authorization: Bearer eyJhbGc...
        
        Response (200):
        {
            "conversion_id": "conv-abc123",
            "user_id": "usr-xyz789",
            "status": "in_progress",
            "started_at": "2026-01-22T10:30:00Z",
            "completed_at": null
        }
    """
    try:
        # 1. Authenticate user
        user_email = get_current_user_email(authorization)
        if not user_email:
            raise authentication_error("Invalid or missing authentication token")
        
        logger.info(f"Fetching conversion: {conversion_id} for user: {user_email}")
        
        # 2. Fetch conversion
        conversion = await conversions_service.get_conversion(conversion_id)
        if not conversion:
            raise not_found_error("conversion", conversion_id)
        
        # 3. Verify ownership
        if conversion['user_email'] != user_email:
            logger.warning(
                f"Unauthorized access attempt to conversion {conversion_id} "
                f"by user {user_email}"
            )
            raise KraftdHTTPException(ErrorCode.INSUFFICIENT_PERMISSIONS, "You do not have access to this conversion")
        
        # 4. Return conversion
        return ConversionResponse(
            conversion_id=conversion['conversion_id'],
            user_id=conversion['user_id'],
            status=conversion['status'],
            started_at=conversion['started_at'],
            completed_at=conversion.get('completed_at')
        )
    
    except KraftdHTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversion {conversion_id}: {str(e)}", exc_info=True)
        raise internal_server_error("Failed to fetch conversion")
