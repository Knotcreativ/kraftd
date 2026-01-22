from fastapi import APIRouter, HTTPException, status, Depends, Header, Request
from pydantic import EmailStr, BaseModel
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
import uuid
import logging

from models.user import (
    UserRegister, UserLogin, UserProfile, TokenResponse,
    ForgotPasswordRequest, ResetPasswordRequest, PasswordResetResponse,
    VerifyEmailRequest, VerifyEmailResponse, UserRole
)
from services.auth_service import AuthService
from services.token_service import TokenService
from services.email_service import EmailService
from services.rbac_service import RBACService, Permission
from services.audit_service import AuditService, AuditEventType, AuditEvent, AuditResult
from services.tenant_service import TenantService
from services.quota_service import get_quota_service
from services.user_service import UserService
from middleware.rbac import get_current_user_with_role, require_permission

# Import standardized error handling
from models.errors import (
    KraftdHTTPException, ErrorCode, validation_error,
    authentication_error, not_found_error, internal_server_error
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory user store (for MVP - replace with Cosmos DB later)
# Key: email, Value: User object
users_db = {}

# UserService instance (will be injected with database)
user_service: Optional[UserService] = None

def set_user_service(service: UserService):
    """Inject UserService instance"""
    global user_service
    user_service = service

def get_user_service() -> UserService:
    """Get UserService instance"""
    if not user_service:
        raise HTTPException(status_code=500, detail="User service not initialized")
    return user_service

# In-memory reset token store (for MVP - replace with Redis later)
# Key: token, Value: {"email": str, "expires_at": datetime}
reset_tokens: Dict[str, dict] = {}
verification_tokens: Dict[str, dict] = {}

def get_current_user_email(authorization: str = Header(None)) -> str:
    """Extract and validate the current user from JWT token
    
    Deprecated: Use get_current_user_with_role from RBAC middleware instead.
    This function kept for backward compatibility.
    """
    if not authorization:
        raise authentication_error("Missing authorization header")
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise authentication_error("Invalid authorization header format")
    
    token = parts[1]
    
    # Use TokenService for verification (includes revocation checking)
    payload = TokenService.verify_token(token, check_revocation=True)
    
    if payload is None:
        raise authentication_error("Invalid or expired token")
    
    email = payload.get("sub")
    if email is None:
        raise authentication_error("Invalid token")
    
    return email

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, request: Request):
    """Register a new user with token generation"""
    # Check if user already exists
    try:
        user_service = get_user_service()
        existing_user = await user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise KraftdHTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code=ErrorCode.RESOURCE_ALREADY_EXISTS,
                message="Email already registered"
            )
    except Exception:
        # Fallback to in-memory check if UserService not available
        if user_data.email in users_db:
            raise KraftdHTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code=ErrorCode.RESOURCE_ALREADY_EXISTS,
                message="Email already registered"
            )
    
    # Combine first and last name
    full_name = f"{user_data.firstName} {user_data.lastName}".strip()
    
    # Create user (organization is not stored in User model currently)
    user = AuthService.create_user(
        email=user_data.email,
        name=full_name,
        organization="",  # Not stored in User model
        password=user_data.password
    )
    
    # Store user in database if available, otherwise in memory
    try:
        user_service = get_user_service()
        await user_service.create_user(user)
        logger.info(f"User stored in database: {user.email}")
    except Exception as e:
        logger.warning(f"Failed to store user in database, using in-memory storage: {e}")
        users_db[user.email] = user
    
    # Initialize user quota
    try:
        await get_quota_service().get_or_create_quota(user.email, tier="free")
        logger.info(f"Quota initialized for user {user.email}")
    except Exception as e:
        logger.error(f"Failed to initialize quota for user {user.email}: {e}")
        # Don't fail registration if quota init fails - user can still register
    
    # Get client IP and user agent for audit logging
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    
    # Generate tokens with JTI tracking (new TokenService)
    access_token, access_jti = TokenService.create_access_token(
        user.email,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    refresh_token, refresh_jti = TokenService.create_refresh_token(
        user.email,
        parent_jti=access_jti,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    
    logger.info(f"User registered: {user.email}")
    
    # Log registration event for audit trail
    try:
        tenant_id = TenantService.get_current_tenant() or "default"
        await AuditService.log_event(
            AuditEvent(
                id=None,
                tenant_id=tenant_id,
                timestamp=None,
                user_email=user.email,
                user_role="user",
                event_type=AuditEventType.REGISTER,
                action="register",
                result=AuditResult.SUCCESS,
                resource_type="user",
                resource_id=user.email,
                allowed=True,
                reason="User registration successful",
                ip_address=client_ip,
                user_agent=user_agent
            )
        )
    except Exception as e:
        logger.error(f"Error logging registration audit event: {e}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600
    )

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, request: Request):
    """Login user and return JWT tokens with JTI tracking"""
    # Get client IP and user agent for audit logging (at the start)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    tenant_id = TenantService.get_current_tenant() or "default"
    
    # Find user
    user = None
    try:
        user_service = get_user_service()
        user = await user_service.get_user_by_email(user_data.email)
    except Exception:
        # Fallback to in-memory lookup if UserService not available
        user = users_db.get(user_data.email)
    
    if user is None:
        # Log failed login (user not found)
        try:
            await AuditService.log_login(
                user_email=user_data.email,
                success=False,
                tenant_id=tenant_id,
                ip_address=client_ip,
                user_agent=user_agent,
                reason="User not found"
            )
        except Exception as e:
            logger.error(f"Error logging failed login: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not AuthService.verify_password(user_data.password, user.hashed_password):
        # Log failed login (invalid password)
        try:
            await AuditService.log_login(
                user_email=user_data.email,
                success=False,
                tenant_id=tenant_id,
                ip_address=client_ip,
                user_agent=user_agent,
                reason="Invalid password"
            )
        except Exception as e:
            logger.error(f"Error logging failed login: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if active
    if not user.is_active:
        # Log failed login (account disabled)
        try:
            await AuditService.log_login(
                user_email=user_data.email,
                success=False,
                tenant_id=tenant_id,
                ip_address=client_ip,
                user_agent=user_agent,
                reason="Account disabled"
            )
        except Exception as e:
            logger.error(f"Error logging failed login: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Generate tokens with JTI tracking (new TokenService)
    access_token, access_jti = TokenService.create_access_token(
        user.email,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    refresh_token, refresh_jti = TokenService.create_refresh_token(
        user.email,
        parent_jti=access_jti,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    
    logger.info(f"User logged in: {user.email}")
    
    # Log successful login
    try:
        await AuditService.log_login(
            user_email=user.email,
            success=True,
            tenant_id=tenant_id,
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        logger.error(f"Error logging login audit event: {e}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_token: str, request: Request):
    """Refresh access token using refresh token with rotation
    
    Implements refresh token rotation:
    1. Validates the refresh token
    2. Invalidates the old refresh token
    3. Issues new access and refresh tokens
    
    This prevents token reuse attacks.
    """
    # Get client IP and user agent for audit logging
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    
    # Perform token rotation
    result = TokenService.rotate_refresh_token(
        refresh_token,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    new_access_token, new_access_jti, new_refresh_token, new_refresh_jti = result
    
    # Extract user email for final validation
    payload = TokenService.verify_token(new_access_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to validate new tokens"
        )
    
    email = payload.get("sub")
    user = users_db.get(email)
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    logger.info(f"Token refreshed for user: {email}")
    
    # Log token refresh event
    try:
        tenant_id = TenantService.get_current_tenant() or "default"
        await AuditService.log_event(
            AuditEvent(
                id=None,
                tenant_id=tenant_id,
                timestamp=None,
                user_email=email,
                user_role="user",
                event_type=AuditEventType.TOKEN_REFRESH,
                action="refresh",
                result=AuditResult.SUCCESS,
                resource_type="token",
                resource_id="access_token",
                allowed=True,
                reason="Token refresh successful",
                ip_address=client_ip,
                user_agent=user_agent
            )
        )
    except Exception as e:
        logger.error(f"Error logging token refresh audit event: {e}")
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=3600
    )

@router.post("/logout", response_model=dict)
async def logout(email: str = Depends(get_current_user_email), request: Request = None):
    """Logout user by revoking all their active tokens
    
    Revokes all active tokens for the user, effectively logging them out
    from all sessions.
    """
    revoked_count = TokenService.revoke_user_tokens(email, reason="User logout")
    
    logger.info(f"User logged out: {email} ({revoked_count} tokens revoked)")
    
    # Log logout event
    try:
        client_ip = request.client.host if request and request.client else None
        user_agent = request.headers.get("User-Agent") if request else None
        tenant_id = TenantService.get_current_tenant() or "default"
        
        await AuditService.log_event(
            AuditEvent(
                id=None,
                tenant_id=tenant_id,
                timestamp=None,
                user_email=email,
                user_role="user",
                event_type=AuditEventType.LOGOUT,
                action="logout",
                result=AuditResult.SUCCESS,
                resource_type="user",
                resource_id=email,
                allowed=True,
                reason="User logout successful",
                ip_address=client_ip,
                user_agent=user_agent
            )
        )
    except Exception as e:
        logger.error(f"Error logging logout audit event: {e}")
    
    return {
        "message": "Successfully logged out",
        "tokens_revoked": revoked_count
    }

@router.get("/profile", response_model=UserProfile)
async def get_profile(email: str = Depends(get_current_user_email)):
    """Get current user profile"""
    user = users_db.get(email)
    if user is None:
        raise not_found_error("User", email)
    
    return UserProfile(
        email=user.email,
        name=user.name,
        organization="",  # User model doesn't have organization
        created_at=user.created_at,
        is_active=user.is_active
    )

@router.get("/validate", response_model=dict)
async def validate_token(email: str = Depends(get_current_user_email)):
    """Validate current token"""
    return {
        "email": email,
        "valid": True,
        "timestamp": datetime.utcnow().isoformat()
    }

# ===== Password Recovery Endpoints =====

@router.post("/forgot-password", response_model=dict)
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request a password reset email
    
    User provides email, receives reset link via email
    Reset token valid for 24 hours
    """
    email = request.email
    
    # Check if user exists
    user = users_db.get(email)
    if user is None:
        # Don't reveal whether email exists (security best practice)
        logger.info(f"Password reset requested for non-existent email: {email}")
        return {
            "message": "If an account exists with this email, you will receive a password reset link",
            "status": "pending"
        }
    
    try:
        # Generate reset token
        reset_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=24)
        reset_tokens[reset_token] = {
            "email": email,
            "expires_at": expires_at,
            "used": False
        }
        
        # Build reset link
        reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
        
        # Send email
        email_service = EmailService()
        sent = await email_service.send_password_reset_email(
            to_email=email,
            reset_token=reset_token,
            user_name=user.name or email.split("@")[0]
        )
        
        if sent:
            logger.info(f"Password reset email sent to {email}")
        else:
            logger.warning(f"Failed to send password reset email to {email}")
        
        # Always return same message for security
        return {
            "message": "If an account exists with this email, you will receive a password reset link",
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"Error in forgot_password: {str(e)}", exc_info=True)
        return {
            "message": "If an account exists with this email, you will receive a password reset link",
            "status": "pending"
        }


@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using token from email
    
    Token must be valid and not expired
    New password must meet requirements
    """
    token = request.token
    new_password = request.new_password
    
    # Validate token
    token_data = reset_tokens.get(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check if expired
    if datetime.utcnow() > token_data["expires_at"]:
        # Remove expired token
        del reset_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one."
        )
    
    # Check if token already used
    if token_data.get("used", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset token has already been used"
        )
    
    email = token_data["email"]
    user = users_db.get(email)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Hash new password
        hashed_password = AuthService.hash_password(new_password)
        
        # Update user
        user.hashed_password = hashed_password
        user.updated_at = datetime.utcnow()
        users_db[email] = user
        
        # Mark token as used
        reset_tokens[token]["used"] = True
        
        logger.info(f"Password successfully reset for user: {email}")
        
        return PasswordResetResponse(
            message="Password has been reset successfully. You can now login with your new password.",
            status="success",
            email=email
        )
        
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(request: VerifyEmailRequest):
    """
    Verify email address using token from verification email
    
    Token must be valid and not expired
    Marks email as verified and returns auth tokens
    """
    token = request.token
    
    # Validate token
    token_data = verification_tokens.get(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Check if expired
    if datetime.utcnow() > token_data["expires_at"]:
        # Remove expired token
        del verification_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired. Please request a new one."
        )
    
    # Check if token already used
    if token_data.get("used", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification token has already been used"
        )
    
    email = token_data["email"]
    user = users_db.get(email)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Mark email as verified
        user.email_verified = True
        user.status = "active"
        user.updated_at = datetime.utcnow()
        users_db[email] = user
        
        # Mark token as used
        verification_tokens[token]["used"] = True
        
        # Generate auth tokens
        access_token = AuthService.create_access_token(email)
        refresh_token = AuthService.create_refresh_token(email)
        
        logger.info(f"Email successfully verified for user: {email}")
        
        return VerifyEmailResponse(
            message="Email verified successfully. You are now logged in.",
            status="success",
            email=email,
            access_token=access_token,
            refresh_token=refresh_token
        )
        
    except Exception as e:
        logger.error(f"Error verifying email: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email"
        )


@router.post("/resend-verification", response_model=dict)
async def resend_verification_email(request: ForgotPasswordRequest):
    """
    Resend email verification link
    
    User provides email, receives new verification link
    Previous tokens are invalidated
    """
    email = request.email
    
    # Check if user exists
    user = users_db.get(email)
    if user is None:
        logger.info(f"Verification resend requested for non-existent email: {email}")
        return {
            "message": "If an account exists with this email, you will receive a verification link",
            "status": "pending"
        }
    
    # Check if already verified
    if user.email_verified:
        return {
            "message": "This email address is already verified",
            "status": "already_verified"
        }
    
    try:
        # Generate new verification token
        verification_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=24)
        verification_tokens[verification_token] = {
            "email": email,
            "expires_at": expires_at,
            "used": False
        }
        
        # Build verification link
        verification_link = f"http://localhost:3000/verify-email?token={verification_token}"
        
        # Send email
        email_service = EmailService()
        sent = await email_service.send_verification_email(
            to_email=email,
            verification_token=verification_token,
            user_name=user.name or email.split("@")[0]
        )
        
        if sent:
            logger.info(f"Verification email resent to {email}")
        else:
            logger.warning(f"Failed to send verification email to {email}")
        
        return {
            "message": "Verification link has been sent to your email",
            "status": "sent"
        }
        
    except Exception as e:
        logger.error(f"Error resending verification email: {str(e)}", exc_info=True)
        return {
            "message": "If an account exists with this email, you will receive a verification link",
            "status": "pending"
        }