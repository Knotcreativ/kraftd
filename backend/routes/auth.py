from fastapi import APIRouter, HTTPException, status, Depends, Header
from pydantic import EmailStr
from typing import Optional
from datetime import datetime

from models.user import UserRegister, UserLogin, UserProfile, TokenResponse
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory user store (for MVP - replace with Cosmos DB later)
# Key: email, Value: User object
users_db = {}

def get_current_user_email(authorization: str = Header(None)) -> str:
    """Extract and validate the current user from JWT token"""
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
    payload = AuthService.verify_token(token)
    
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

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new user"""
    # Check if user already exists
    if user_data.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = AuthService.create_user(
        email=user_data.email,
        name=user_data.name,
        organization=user_data.organization,
        password=user_data.password
    )
    
    # Store user
    users_db[user.email] = user
    
    # Generate tokens
    access_token = AuthService.create_access_token(user.email)
    refresh_token = AuthService.create_refresh_token(user.email)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600
    )

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Login user and return JWT tokens"""
    # Find user
    user = users_db.get(user_data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not AuthService.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Generate tokens
    access_token = AuthService.create_access_token(user.email)
    refresh_token = AuthService.create_refresh_token(user.email)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_token: str):
    """Refresh access token using refresh token"""
    payload = AuthService.verify_token(refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    email = payload.get("sub")
    user = users_db.get(email)
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new access token
    access_token = AuthService.create_access_token(email)
    new_refresh_token = AuthService.create_refresh_token(email)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=3600
    )

@router.get("/profile", response_model=UserProfile)
async def get_profile(email: str = Depends(get_current_user_email)):
    """Get current user profile"""
    user = users_db.get(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserProfile(
        email=user.email,
        name=user.name,
        organization=user.organization,
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
