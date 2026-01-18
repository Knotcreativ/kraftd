from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

class User(BaseModel):
    """User model stored in Cosmos DB
    
    Implements KRAFTD User Specification
    """
    id: str  # UUID-based
    email: str
    name: Optional[str] = None
    hashed_password: str
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
    """
    # Required fields
    email: EmailStr
    password: str
    acceptTerms: bool
    acceptPrivacy: bool
    
    # Optional fields
    name: Optional[str] = None
    marketingOptIn: bool = False
    
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
    """Request model for user login"""
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    """Response model for user profile"""
    email: str
    name: str
    organization: str
    created_at: datetime
    is_active: bool

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
