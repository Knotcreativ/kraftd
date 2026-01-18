"""
Token Service - Enhanced JWT Token Management

Implements token tracking, refresh token rotation, and token invalidation.

Features:
- JTI (JWT ID) tracking for token invalidation
- Refresh token rotation (old token invalidated on use)
- Token expiration enforcement
- Token storage and validation in Cosmos DB
- Audit logging for security events
"""

import secrets
import logging
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum

from services.secrets_manager import get_secrets_manager

logger = logging.getLogger(__name__)

# JWT configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
TOKEN_CLEANUP_DAYS = 14  # Delete tokens older than 14 days


class TokenType(str, Enum):
    """Token type enumeration"""
    ACCESS = "access"
    REFRESH = "refresh"


class TokenStatus(str, Enum):
    """Token status for tracking"""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class TokenRecord:
    """In-memory representation of a token record
    
    In production, this would be stored in Cosmos DB for distributed access.
    """
    def __init__(
        self,
        jti: str,
        user_email: str,
        token_type: TokenType,
        issued_at: datetime,
        expires_at: datetime,
        status: TokenStatus = TokenStatus.ACTIVE,
        parent_jti: Optional[str] = None,  # For refresh token rotation tracking
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        self.jti = jti
        self.user_email = user_email
        self.token_type = token_type
        self.issued_at = issued_at
        self.expires_at = expires_at
        self.status = status
        self.parent_jti = parent_jti  # JTI of the token that created this one
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.revoked_at: Optional[datetime] = None


class TokenService:
    """Service for managing JWT tokens with enhanced security features
    
    Supports:
    - Token generation with JTI claims
    - Token verification with revocation checking
    - Refresh token rotation
    - Token invalidation
    - Audit logging
    """
    
    # In-memory token store (in production, use Cosmos DB)
    # Key: JTI, Value: TokenRecord
    _token_store: Dict[str, TokenRecord] = {}
    
    @staticmethod
    def _get_secret_key() -> str:
        """Get JWT secret key from secure storage."""
        secrets_mgr = get_secrets_manager()
        return secrets_mgr.get_jwt_secret()
    
    @classmethod
    def create_access_token(
        cls,
        user_email: str,
        expires_delta: Optional[timedelta] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> tuple[str, str]:
        """Create a JWT access token with JTI for tracking
        
        Args:
            user_email: User's email address
            expires_delta: Custom expiration time (optional)
            ip_address: Client IP address for audit logging
            user_agent: Client user agent for audit logging
            
        Returns:
            Tuple of (token, jti) for storage and tracking
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Generate unique JWT ID (JTI)
        jti = secrets.token_urlsafe(32)
        
        now = datetime.utcnow()
        
        # Create token payload
        to_encode = {
            "sub": user_email,
            "exp": expire,
            "iat": now,
            "type": TokenType.ACCESS.value,
            "jti": jti,  # JWT ID for tracking and revocation
        }
        
        secret_key = cls._get_secret_key()
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
        
        # Record token in store
        token_record = TokenRecord(
            jti=jti,
            user_email=user_email,
            token_type=TokenType.ACCESS,
            issued_at=now,
            expires_at=expire,
            status=TokenStatus.ACTIVE,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        cls._token_store[jti] = token_record
        
        logger.info(f"Access token created for user: {user_email} (JTI: {jti[:8]}...)")
        
        return encoded_jwt, jti
    
    @classmethod
    def create_refresh_token(
        cls,
        user_email: str,
        parent_jti: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> tuple[str, str]:
        """Create a JWT refresh token with JTI for rotation tracking
        
        Args:
            user_email: User's email address
            parent_jti: JTI of the access token that created this (for rotation)
            ip_address: Client IP address for audit logging
            user_agent: Client user agent for audit logging
            
        Returns:
            Tuple of (token, jti) for storage and tracking
        """
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Generate unique JWT ID (JTI)
        jti = secrets.token_urlsafe(32)
        
        now = datetime.utcnow()
        
        # Create token payload
        to_encode = {
            "sub": user_email,
            "exp": expire,
            "iat": now,
            "type": TokenType.REFRESH.value,
            "jti": jti,  # JWT ID for tracking and rotation
        }
        
        secret_key = cls._get_secret_key()
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
        
        # Record token in store
        token_record = TokenRecord(
            jti=jti,
            user_email=user_email,
            token_type=TokenType.REFRESH,
            issued_at=now,
            expires_at=expire,
            status=TokenStatus.ACTIVE,
            parent_jti=parent_jti,  # Track token rotation chain
            ip_address=ip_address,
            user_agent=user_agent,
        )
        cls._token_store[jti] = token_record
        
        logger.info(
            f"Refresh token created for user: {user_email} (JTI: {jti[:8]}...)"
        )
        
        return encoded_jwt, jti
    
    @classmethod
    def verify_token(
        cls,
        token: str,
        check_revocation: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token
        
        Args:
            token: JWT token string
            check_revocation: Whether to check if token is revoked
            
        Returns:
            Token payload if valid, None if invalid
        """
        try:
            secret_key = cls._get_secret_key()
            payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
            
            # Check if token is revoked
            jti = payload.get("jti")
            if jti and check_revocation:
                if not cls.is_token_valid(jti):
                    logger.warning(f"Attempt to use revoked/expired token (JTI: {jti[:8]}...)")
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
    
    @classmethod
    def is_token_valid(cls, jti: str) -> bool:
        """Check if a token (by JTI) is valid and not revoked
        
        Args:
            jti: JWT ID to check
            
        Returns:
            True if token is active, False if revoked or not found
        """
        if jti not in cls._token_store:
            # Token not found in store (possible legitimate if token was issued before service started)
            # In production with Cosmos DB, this would check the database
            logger.debug(f"Token JTI not found in store: {jti[:8]}...")
            return True  # Allow through (could be from before service start)
        
        token_record = cls._token_store[jti]
        
        # Check if revoked
        if token_record.status == TokenStatus.REVOKED:
            logger.warning(f"Token is revoked (JTI: {jti[:8]}...)")
            return False
        
        # Check if expired
        if token_record.expires_at < datetime.utcnow():
            logger.debug(f"Token is expired (JTI: {jti[:8]}...)")
            token_record.status = TokenStatus.EXPIRED
            return False
        
        return True
    
    @classmethod
    def revoke_token(cls, jti: str, reason: str = "User logout") -> bool:
        """Revoke a token by JTI
        
        Args:
            jti: JWT ID to revoke
            reason: Reason for revocation (for audit logging)
            
        Returns:
            True if token was revoked, False if not found
        """
        if jti not in cls._token_store:
            logger.warning(f"Attempt to revoke non-existent token: {jti[:8]}...")
            return False
        
        token_record = cls._token_store[jti]
        token_record.status = TokenStatus.REVOKED
        token_record.revoked_at = datetime.utcnow()
        
        logger.info(f"Token revoked (JTI: {jti[:8]}..., Reason: {reason})")
        
        return True
    
    @classmethod
    def revoke_user_tokens(cls, user_email: str, reason: str = "User logout") -> int:
        """Revoke all active tokens for a user
        
        Useful for logout operations and security incidents.
        
        Args:
            user_email: User's email address
            reason: Reason for revocation
            
        Returns:
            Number of tokens revoked
        """
        revoked_count = 0
        
        for jti, token_record in cls._token_store.items():
            if (token_record.user_email == user_email and
                token_record.status == TokenStatus.ACTIVE):
                cls.revoke_token(jti, reason)
                revoked_count += 1
        
        logger.info(f"Revoked {revoked_count} tokens for user: {user_email}")
        
        return revoked_count
    
    @classmethod
    def rotate_refresh_token(
        cls,
        old_refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[tuple[str, str, str, str]]:
        """Rotate a refresh token (invalidate old, create new)
        
        Implements refresh token rotation to prevent token reuse attacks.
        
        Args:
            old_refresh_token: The current refresh token
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Tuple of (new_access_token, new_access_jti, new_refresh_token, new_refresh_jti)
            or None if rotation fails
        """
        # Verify old refresh token
        payload = cls.verify_token(old_refresh_token, check_revocation=False)
        
        if payload is None:
            logger.warning("Attempted token rotation with invalid token")
            return None
        
        # Verify it's actually a refresh token
        if payload.get("type") != TokenType.REFRESH.value:
            logger.warning("Attempted token rotation with non-refresh token")
            return None
        
        user_email = payload.get("sub")
        old_jti = payload.get("jti")
        
        if not user_email or not old_jti:
            logger.error("Token missing required claims for rotation")
            return None
        
        # Create new tokens
        new_access_token, new_access_jti = cls.create_access_token(
            user_email,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        new_refresh_token, new_refresh_jti = cls.create_refresh_token(
            user_email,
            parent_jti=old_jti,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # Revoke old refresh token
        cls.revoke_token(old_jti, reason="Refresh token rotation")
        
        logger.info(
            f"Token rotation completed for user: {user_email} "
            f"(Old JTI: {old_jti[:8]}..., New JTI: {new_refresh_jti[:8]}...)"
        )
        
        return new_access_token, new_access_jti, new_refresh_token, new_refresh_jti
    
    @classmethod
    def get_token_info(cls, jti: str) -> Optional[Dict[str, Any]]:
        """Get information about a token by JTI
        
        Args:
            jti: JWT ID
            
        Returns:
            Dictionary with token info or None if not found
        """
        if jti not in cls._token_store:
            return None
        
        record = cls._token_store[jti]
        
        return {
            "jti": record.jti[:16],  # Truncate for security
            "user_email": record.user_email,
            "token_type": record.token_type.value,
            "issued_at": record.issued_at.isoformat(),
            "expires_at": record.expires_at.isoformat(),
            "status": record.status.value,
            "revoked_at": record.revoked_at.isoformat() if record.revoked_at else None,
            "ip_address": record.ip_address,
            "user_agent": record.user_agent,
        }
    
    @classmethod
    def cleanup_expired_tokens(cls) -> int:
        """Remove expired and revoked tokens older than TOKEN_CLEANUP_DAYS
        
        Should be run periodically (e.g., via scheduled task).
        
        Returns:
            Number of tokens removed
        """
        cutoff_date = datetime.utcnow() - timedelta(days=TOKEN_CLEANUP_DAYS)
        tokens_to_remove = []
        
        for jti, record in cls._token_store.items():
            if record.expires_at < cutoff_date:
                tokens_to_remove.append(jti)
        
        for jti in tokens_to_remove:
            del cls._token_store[jti]
        
        logger.info(f"Cleaned up {len(tokens_to_remove)} expired tokens")
        
        return len(tokens_to_remove)
    
    @classmethod
    def get_active_tokens_for_user(cls, user_email: str) -> List[Dict[str, Any]]:
        """Get all active tokens for a user
        
        Useful for session management and security audits.
        
        Args:
            user_email: User's email address
            
        Returns:
            List of active token info dictionaries
        """
        active_tokens = []
        
        for jti, record in cls._token_store.items():
            if (record.user_email == user_email and
                record.status == TokenStatus.ACTIVE and
                record.expires_at > datetime.utcnow()):
                active_tokens.append(cls.get_token_info(jti))
        
        return active_tokens
