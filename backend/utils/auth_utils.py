"""
Authentication Utilities - Password hashing, JWT management, and security helpers

Provides secure password handling and JWT token operations.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import jwt
import bcrypt

from services.secrets_manager import get_secrets_manager

logger = logging.getLogger(__name__)

# JWT Configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))


class PasswordService:
    """Service for password hashing and verification using bcrypt"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt
        
        Bcrypt has a 72-byte limit, so we truncate the password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        try:
            # Encode to UTF-8 and truncate to 72 bytes (bcrypt limit)
            password_bytes = password.encode('utf-8')[:72]
            
            # Generate salt and hash
            salt = bcrypt.gensalt(rounds=12)  # 12 rounds recommended for production
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against its hash
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored hash to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            # Encode to UTF-8 and truncate to 72 bytes (bcrypt limit)
            password_bytes = plain_password.encode('utf-8')[:72]
            hashed_bytes = hashed_password.encode('utf-8')
            
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False


class JWTService:
    """Service for JWT token creation and verification"""
    
    @staticmethod
    def _get_secret_key() -> str:
        """Get JWT secret key from secure storage"""
        try:
            secrets_mgr = get_secrets_manager()
            return secrets_mgr.get_jwt_secret()
        except Exception:
            # Fallback to environment variable for development
            return os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    
    @classmethod
    def create_access_token(
        cls,
        subject: str,  # Typically user email
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a JWT access token
        
        Args:
            subject: Token subject (typically user email)
            expires_delta: Custom expiration time
            additional_claims: Extra claims to add to token
            
        Returns:
            JWT token string
        """
        try:
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            
            payload = {
                "sub": subject,
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "access",
                "jti": secrets.token_urlsafe(16),  # JWT ID for token invalidation
            }
            
            # Add custom claims
            if additional_claims:
                payload.update(additional_claims)
            
            secret_key = cls._get_secret_key()
            token = jwt.encode(payload, secret_key, algorithm=ALGORITHM)
            
            return token
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise
    
    @classmethod
    def create_refresh_token(
        cls,
        subject: str,  # Typically user email
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT refresh token
        
        Args:
            subject: Token subject (typically user email)
            expires_delta: Custom expiration time
            
        Returns:
            JWT token string
        """
        try:
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            
            payload = {
                "sub": subject,
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "refresh",
                "jti": secrets.token_urlsafe(16),  # JWT ID for token invalidation
            }
            
            secret_key = cls._get_secret_key()
            token = jwt.encode(payload, secret_key, algorithm=ALGORITHM)
            
            return token
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise
    
    @classmethod
    def verify_token(
        cls,
        token: str,
        token_type: Optional[str] = None,  # "access" or "refresh"
    ) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token to verify
            token_type: Expected token type (optional validation)
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            secret_key = cls._get_secret_key()
            payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
            
            # Validate token type if specified
            if token_type and payload.get("type") != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None


class AuthUtils:
    """Utility functions for authentication"""
    
    @staticmethod
    def is_password_valid(password: str, min_length: int = 8) -> tuple[bool, str]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            min_length: Minimum password length
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        if not any(c in "!@#$%^&*()-_=+[]{}|;:',.<>?/" for c in password):
            return False, "Password must contain at least one special character"
        
        return True, ""
    
    @staticmethod
    def is_email_valid(email: str) -> bool:
        """
        Simple email validation
        
        Args:
            email: Email to validate
            
        Returns:
            True if email format is valid
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
