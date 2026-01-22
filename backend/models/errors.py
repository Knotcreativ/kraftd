"""
Standardized Error Handling Models and Exceptions

This module provides consistent error response formats and exception handling
across all API endpoints in the KraftdIntel backend.
"""

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime


class ErrorCode(str, Enum):
    """Standardized error codes for consistent API responses."""

    # Authentication & Authorization
    INVALID_TOKEN = "INVALID_TOKEN"
    MISSING_TOKEN = "MISSING_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    USER_NOT_FOUND = "USER_NOT_FOUND"

    # Quota & Limits
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Resource Errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_ACCESS_DENIED = "RESOURCE_ACCESS_DENIED"

    # Validation Errors
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_VALUE = "INVALID_FIELD_VALUE"

    # Processing Errors
    PROCESSING_FAILED = "PROCESSING_FAILED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    CONVERSION_FAILED = "CONVERSION_FAILED"
    UPLOAD_FAILED = "UPLOAD_FAILED"

    # System Errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"

    # File/Upload Errors
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    FILE_PROCESSING_ERROR = "FILE_PROCESSING_ERROR"


class ErrorDetail(BaseModel):
    """Detailed error information for structured error responses."""

    field: Optional[str] = Field(None, description="Field that caused the error")
    value: Optional[Any] = Field(None, description="Invalid value that was provided")
    constraint: Optional[str] = Field(None, description="Validation constraint that was violated")


class APIErrorResponse(BaseModel):
    """Standardized API error response format."""

    success: bool = Field(False, description="Always false for error responses")
    error: ErrorCode = Field(..., description="Standardized error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed field-level errors")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the error")
    path: Optional[str] = Field(None, description="API path that caused the error")

    class Config:
        json_encoders = {
            ErrorCode: lambda v: v.value
        }


class KraftdHTTPException(HTTPException):
    """
    Extended HTTPException with standardized error information.

    This exception provides consistent error responses across all endpoints.
    """

    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize KraftdHTTPException.

        Args:
            status_code: HTTP status code
            error_code: Standardized error code
            message: Human-readable error message
            details: Optional field-level error details
            headers: Optional HTTP headers
        """
        self.error_code = error_code
        self.details = details or []

        # Create structured error response
        error_response = APIErrorResponse(
            success=False,
            error=error_code,
            message=message,
            details=details,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

        super().__init__(
            status_code=status_code,
            detail=error_response.model_dump(),
            headers=headers
        )


# ===== Convenience Functions for Common Errors =====

def authentication_error(message: str = "Authentication required") -> KraftdHTTPException:
    """Create authentication error (401)."""
    return KraftdHTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code=ErrorCode.INVALID_TOKEN,
        message=message,
        headers={"WWW-Authenticate": "Bearer"}
    )


def authorization_error(message: str = "Insufficient permissions") -> KraftdHTTPException:
    """Create authorization error (403)."""
    return KraftdHTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
        message=message
    )


def not_found_error(resource_type: str, resource_id: str) -> KraftdHTTPException:
    """Create resource not found error (404)."""
    return KraftdHTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code=ErrorCode.RESOURCE_NOT_FOUND,
        message=f"{resource_type} not found: {resource_id}"
    )


def quota_exceeded_error(limit: int, usage: int, message: Optional[str] = None) -> KraftdHTTPException:
    """Create quota exceeded error (429)."""
    if not message:
        message = f"Quota exceeded: {usage}/{limit}"

    return KraftdHTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        error_code=ErrorCode.QUOTA_EXCEEDED,
        message=message,
        details=[
            ErrorDetail(
                field="quota",
                value=f"{usage}/{limit}",
                constraint="usage must not exceed limit"
            )
        ]
    )


def validation_error(message: str, details: Optional[List[ErrorDetail]] = None) -> KraftdHTTPException:
    """Create validation error (400)."""
    return KraftdHTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code=ErrorCode.INVALID_REQUEST,
        message=message,
        details=details
    )


def internal_server_error(message: str = "Internal server error") -> KraftdHTTPException:
    """Create internal server error (500)."""
    return KraftdHTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        message=message
    )


def service_unavailable_error(message: str = "Service temporarily unavailable") -> KraftdHTTPException:
    """Create service unavailable error (503)."""
    return KraftdHTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_code=ErrorCode.SERVICE_UNAVAILABLE,
        message=message
    )


# ===== Legacy Compatibility =====

def create_legacy_error_response(error_code: str, message: str, **kwargs) -> Dict[str, Any]:
    """
    Create legacy error response format for backward compatibility.

    This maintains compatibility with existing endpoints that expect
    dictionary error responses.
    """
    response = {
        "error": error_code,
        "message": message
    }
    response.update(kwargs)
    return response