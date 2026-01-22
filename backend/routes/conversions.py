"""
Conversions API Routes

Implements the Conversions endpoints defined in /docs/api-spec.md:
- POST /api/v1/conversions — Create a new conversion session
- GET /api/v1/conversions/:conversion_id — Get conversion metadata
"""

from fastapi import APIRouter, HTTPException, status, Depends, Header, Request
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid
import logging

from models.conversion import ConversionCreate, ConversionResponse, ConversionStatus
from services.conversions_service import ConversionsService
from services.auth_service import AuthService
from middleware.quota import check_quota

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
        HTTPException: 401 if token is missing, invalid, or expired
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    try:
        # Verify token using auth service
        payload = auth_service.verify_token(token)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return email
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "INVALID_TOKEN",
                    "message": "Invalid or missing authentication token"
                }
            )
        
        logger.info(f"Creating conversion for user: {user_email}")
        
        # 2. Check quota (middleware will handle this, but we verify here)
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "USER_NOT_FOUND",
                    "message": "User account not found"
                }
            )
        
        if user.get('quota_used', 0) >= user.get('quota_limit', 0):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "QUOTA_EXCEEDED",
                    "message": "User has reached their document conversion quota",
                    "quota_limit": user.get('quota_limit', 0),
                    "quota_used": user.get('quota_used', 0)
                }
            )
        
        # 3. Create conversion
        conversion_id = str(uuid.uuid4())
        conversion = await conversions_service.create_conversion(
            conversion_id=conversion_id,
            user_email=user_email,
            user_id=user.get('user_id')
        )
        
        # 4. Increment user quota
        await auth_service.increment_quota_used(user_email, 1)
        
        logger.info(f"Conversion created: {conversion_id} for user: {user_email}")
        
        # 5. Return response
        return ConversionResponse(
            conversion_id=conversion['conversion_id'],
            user_id=conversion['user_id'],
            status=conversion['status'],
            started_at=conversion['started_at'],
            completed_at=conversion.get('completed_at')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating conversion: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Failed to create conversion session"
            }
        )


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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "INVALID_TOKEN",
                    "message": "Invalid or missing authentication token"
                }
            )
        
        logger.info(f"Fetching conversion: {conversion_id} for user: {user_email}")
        
        # 2. Fetch conversion
        conversion = await conversions_service.get_conversion(conversion_id)
        if not conversion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "CONVERSION_NOT_FOUND",
                    "message": f"Conversion {conversion_id} does not exist"
                }
            )
        
        # 3. Verify ownership
        if conversion['user_email'] != user_email:
            logger.warning(
                f"Unauthorized access attempt to conversion {conversion_id} "
                f"by user {user_email}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "FORBIDDEN",
                    "message": "You do not have access to this conversion"
                }
            )
        
        # 4. Return conversion
        return ConversionResponse(
            conversion_id=conversion['conversion_id'],
            user_id=conversion['user_id'],
            status=conversion['status'],
            started_at=conversion['started_at'],
            completed_at=conversion.get('completed_at')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversion {conversion_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Failed to fetch conversion"
            }
        )
