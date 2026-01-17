from pydantic import BaseModel, EmailStr
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
