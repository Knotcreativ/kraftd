from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class User(BaseModel):
    """User model stored in Cosmos DB"""
    id: str  # email-based
    email: str
    name: str
    organization: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

class UserRegister(BaseModel):
    """Request model for user registration"""
    email: EmailStr
    name: str
    organization: str
    password: str

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
