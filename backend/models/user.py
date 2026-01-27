from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """User role enumeration for role-based access control"""
    ADMIN = "admin"               # Full system access
    SYSTEM_ADMIN = "system_admin" # System administrator
    TENANT_ADMIN = "tenant_admin" # Tenant administrator
    USER = "user"                 # Standard user (default)
    VIEWER = "viewer"             # Read-only access
    GUEST = "guest"               # Unauthenticated access

class User(BaseModel):
    """User model stored in Cosmos DB
    
    Implements KRAFTD User Specification with role-based access control
    """
    id: str  # UUID-based
    email: str
    name: Optional[str] = None
    hashed_password: str
    role: UserRole = UserRole.USER  # User role for RBAC
    permissions: List[str] = []      # Custom permissions (future use)
    email_verified: bool = False
    marketing_opt_in: bool = False
    accepted_terms_at: Optional[datetime] = None
    accepted_privacy_at: Optional[datetime] = None
    terms_version: str = "v1.0"
    privacy_version: str = "v1.0"
    created_at: datetime
    updated_at: datetime
    status: str = "pending_verification"  # pending_verification, active, suspended
    is_active: bool = True

class UserRegister(BaseModel):
    """Request model for user registration
    
    Implements KRAFTD Registration Specification
    Accepts firstName and lastName as separate fields (matches frontend signup)
    """
    # Required fields
    email: EmailStr
    password: str
    firstName: str
    lastName: str
    acceptTerms: bool
    acceptPrivacy: bool
    
    # Optional fields
    marketingOptIn: bool = False
    recaptchaToken: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password must be at most 128 characters')
        if ' ' in v:
            raise ValueError('Password cannot contain spaces')
        return v
    
    @field_validator('acceptTerms')
    @classmethod
    def validate_terms(cls, v):
        """Terms of Service must be accepted"""
        if not v:
            raise ValueError('You must agree to the Terms of Service')
        return v
    
    @field_validator('acceptPrivacy')
    @classmethod
    def validate_privacy(cls, v):
        """Privacy Policy must be accepted"""
        if not v:
            raise ValueError('You must agree to the Privacy Policy')
        return v

class UserLogin(BaseModel):
    """Request model for user login
    
    Includes optional fields sent from frontend (rememberMe, marketingOptIn, recaptchaToken)
    to avoid validation errors when frontend includes them
    """
    email: EmailStr
    password: str
    rememberMe: bool = False
    marketingOptIn: bool = False
    recaptchaToken: str

class UserProfile(BaseModel):
    """Response model for user profile"""
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    created_at: str
    updated_at: str

class TokenResponse(BaseModel):
    """Response model for token responses"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 1 hour

class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # email
    exp: int
    iat: int

class RefreshRequest(BaseModel):
    """Request model for token refresh"""
    refresh_token: str

class VerifyEmailRequest(BaseModel):
    """Request to reset password with token"""
    token: str
    new_password: str
    confirm_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password must be at most 128 characters')
        if ' ' in v:
            raise ValueError('Password cannot contain spaces')
        return v
    
    @field_validator('confirm_password')
    @classmethod
    def validate_confirm(cls, v, info):
        """Ensure passwords match"""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v

class PasswordResetResponse(BaseModel):
    """Response after password reset"""
    message: str
    status: str = "success"
    email: Optional[str] = None

class VerifyEmailRequest(BaseModel):
    """Request to verify email with token"""
    token: str

class VerifyEmailResponse(BaseModel):
    """Response after email verification"""
    message: str
    status: str = "success"
    email: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
