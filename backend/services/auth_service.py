import jwt
import os
import logging
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional, Dict, Any
from models.user import User, TokenPayload
from services.secrets_manager import get_secrets_manager

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Secret key is loaded dynamically from Key Vault (or env variables in dev)
def _get_secret_key() -> str:
    """Get JWT secret key from secure storage."""
    secrets = get_secrets_manager()
    return secrets.get_jwt_secret()

class AuthService:
    """Service for handling authentication operations"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(email: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {
            "sub": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        secret_key = _get_secret_key()
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(email: str) -> str:
        """Create a JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "sub": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        secret_key = _get_secret_key()
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            secret_key = _get_secret_key()
            payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                return None
            return payload
        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    @staticmethod
    def create_user(email: str, name: str, organization: str, password: str) -> User:
        """Create a new user object (not persisted yet)"""
        hashed_password = AuthService.hash_password(password)
        now = datetime.utcnow()
        
        return User(
            id=email,  # Use email as ID for simplicity
            email=email,
            name=name,
            organization=organization,
            hashed_password=hashed_password,
            created_at=now,
            updated_at=now,
            is_active=True
        )
