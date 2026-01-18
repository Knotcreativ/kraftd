"""Verification token service for email verification."""

import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

# In-memory token storage (replace with Redis in production)
# Format: {token_hash: {"email": str, "created_at": datetime, "expires_at": datetime}}
_verification_tokens: Dict[str, Dict] = {}

TOKEN_EXPIRY_HOURS = 24


class VerificationTokenService:
    """Service for generating and validating email verification tokens"""
    
    @staticmethod
    def generate_token(email: str) -> Tuple[str, str]:
        """Generate a verification token for an email
        
        Args:
            email: Email address to generate token for
            
        Returns:
            Tuple of (token, token_hash) where:
            - token: The plain token to send to user (via email link)
            - token_hash: The hash to store in database/cache
        """
        # Generate a secure random token
        token = secrets.token_urlsafe(32)
        
        # Create hash of token for storage
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Store token metadata
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=TOKEN_EXPIRY_HOURS)
        
        _verification_tokens[token_hash] = {
            "email": email,
            "created_at": now,
            "expires_at": expires_at
        }
        
        logger.info(f"Generated verification token for {email}")
        return token, token_hash
    
    @staticmethod
    def verify_token(token: str) -> Optional[str]:
        """Verify a token and return the associated email
        
        Args:
            token: The plain token from the verification link
            
        Returns:
            Email address if token is valid, None otherwise
        """
        # Hash the provided token
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Check if token exists
        if token_hash not in _verification_tokens:
            logger.warning(f"Invalid verification token attempted")
            return None
        
        token_data = _verification_tokens[token_hash]
        
        # Check if token has expired
        if datetime.utcnow() > token_data["expires_at"]:
            logger.warning(f"Expired verification token for {token_data['email']}")
            # Clean up expired token
            del _verification_tokens[token_hash]
            return None
        
        email = token_data["email"]
        
        # Clean up used token
        del _verification_tokens[token_hash]
        
        logger.info(f"Verified email for {email}")
        return email
    
    @staticmethod
    def invalidate_token(token: str) -> bool:
        """Invalidate a token (used after verification)
        
        Args:
            token: The plain token to invalidate
            
        Returns:
            True if token was invalidated, False if not found
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        if token_hash in _verification_tokens:
            del _verification_tokens[token_hash]
            return True
        
        return False
    
    @staticmethod
    def cleanup_expired_tokens() -> int:
        """Remove all expired tokens from storage
        
        Returns:
            Number of tokens cleaned up
        """
        now = datetime.utcnow()
        expired_hashes = [
            token_hash
            for token_hash, data in _verification_tokens.items()
            if now > data["expires_at"]
        ]
        
        for token_hash in expired_hashes:
            del _verification_tokens[token_hash]
        
        if expired_hashes:
            logger.info(f"Cleaned up {len(expired_hashes)} expired tokens")
        
        return len(expired_hashes)
