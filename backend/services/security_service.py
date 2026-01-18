"""
Phase 8: Security Hardening Service

Implements:
1. HttpOnly Cookie Management
2. Rate Limiting Tracking
3. Account Lockout Mechanism
4. CSRF Token Generation & Validation
"""

import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


# ===== 1. HTTPONLY COOKIE MANAGEMENT =====

class HttpOnlyCookieManager:
    """Manages secure HttpOnly cookie configuration."""
    
    @staticmethod
    def get_access_token_cookie_settings() -> dict:
        """Get settings for access token cookie."""
        return {
            "key": "access_token",
            "httponly": True,
            "secure": True,  # HTTPS only in production
            "samesite": "lax",
            "max_age": 3600,  # 1 hour
            "path": "/",
            "domain": None,  # Will be set by FastAPI
        }
    
    @staticmethod
    def get_refresh_token_cookie_settings() -> dict:
        """Get settings for refresh token cookie."""
        return {
            "key": "refresh_token",
            "httponly": True,
            "secure": True,  # HTTPS only in production
            "samesite": "lax",
            "max_age": 7 * 24 * 3600,  # 7 days
            "path": "/",
            "domain": None,  # Will be set by FastAPI
        }
    
    @staticmethod
    def get_csrf_token_cookie_settings() -> dict:
        """Get settings for CSRF token cookie (not HttpOnly - JS needs to read it)."""
        return {
            "key": "csrf-token",
            "httponly": False,  # JavaScript needs to read this
            "secure": True,  # HTTPS only in production
            "samesite": "lax",
            "max_age": 3600,  # 1 hour
            "path": "/",
            "domain": None,
        }


# ===== 2. RATE LIMITING TRACKER =====

class RateLimitTracker:
    """
    Tracks rate limiting per IP for login and registration.
    
    Stores: {ip_address: {"count": int, "reset_at": datetime}}
    """
    
    def __init__(self):
        self._limits: Dict[str, Dict] = {}
    
    def is_rate_limited(self, ip_address: str, limit: int = 5, window_minutes: int = 1) -> bool:
        """
        Check if IP address has exceeded rate limit.
        
        Args:
            ip_address: Client IP address
            limit: Maximum requests allowed (default: 5)
            window_minutes: Time window in minutes (default: 1)
            
        Returns:
            True if rate limited, False if within limit
        """
        if ip_address not in self._limits:
            return False
        
        entry = self._limits[ip_address]
        
        # Check if window has expired
        if datetime.utcnow() > entry["reset_at"]:
            del self._limits[ip_address]
            return False
        
        # Check if limit exceeded
        return entry["count"] >= limit
    
    def record_attempt(self, ip_address: str, window_minutes: int = 1):
        """
        Record an attempt for an IP address.
        
        Args:
            ip_address: Client IP address
            window_minutes: Time window in minutes (default: 1)
        """
        if ip_address not in self._limits:
            self._limits[ip_address] = {
                "count": 0,
                "reset_at": datetime.utcnow() + timedelta(minutes=window_minutes)
            }
        
        self._limits[ip_address]["count"] += 1
    
    def get_remaining_attempts(self, ip_address: str, limit: int = 5) -> int:
        """Get remaining attempts before rate limit."""
        if ip_address not in self._limits:
            return limit
        
        entry = self._limits[ip_address]
        if datetime.utcnow() > entry["reset_at"]:
            return limit
        
        return max(0, limit - entry["count"])
    
    def reset(self, ip_address: str):
        """Reset rate limit for IP address."""
        if ip_address in self._limits:
            del self._limits[ip_address]


# ===== 3. ACCOUNT LOCKOUT MANAGER =====

class AccountLockoutManager:
    """
    Manages account lockout after failed login attempts.
    
    Locks account for 15 minutes after 5 failed attempts.
    Stores: {email: {"count": int, "locked_until": datetime}}
    """
    
    def __init__(self):
        self._lockouts: Dict[str, Dict] = {}
    
    def is_account_locked(self, email: str) -> bool:
        """Check if account is locked."""
        if email not in self._lockouts:
            return False
        
        lockout = self._lockouts[email]
        
        # Check if lockout has expired
        if datetime.utcnow() > lockout["locked_until"]:
            del self._lockouts[email]
            return False
        
        return lockout["count"] >= 5
    
    def get_lockout_remaining_minutes(self, email: str) -> int:
        """Get remaining minutes until account is unlocked."""
        if email not in self._lockouts or not self.is_account_locked(email):
            return 0
        
        remaining = self._lockouts[email]["locked_until"] - datetime.utcnow()
        return int(remaining.total_seconds() / 60) + 1
    
    def record_failed_attempt(self, email: str, lockout_minutes: int = 15):
        """
        Record a failed login attempt.
        
        Args:
            email: User email
            lockout_minutes: Minutes to lock account after 5 attempts
        """
        if email not in self._lockouts:
            self._lockouts[email] = {
                "count": 0,
                "locked_until": datetime.utcnow() + timedelta(minutes=lockout_minutes)
            }
        
        self._lockouts[email]["count"] += 1
        
        # If this is the 5th attempt, set lock time
        if self._lockouts[email]["count"] == 5:
            self._lockouts[email]["locked_until"] = datetime.utcnow() + timedelta(minutes=lockout_minutes)
            logger.warning(f"Account locked after 5 failed attempts: {email}")
    
    def reset_failed_attempts(self, email: str):
        """
        Reset failed login attempts for email.
        Called on successful login.
        
        Args:
            email: User email
        """
        if email in self._lockouts:
            del self._lockouts[email]
    
    def cleanup_expired_lockouts(self):
        """Remove expired lockouts from memory."""
        expired = [
            email for email, lockout in self._lockouts.items()
            if datetime.utcnow() > lockout["locked_until"]
        ]
        for email in expired:
            del self._lockouts[email]


# ===== 4. CSRF TOKEN MANAGER =====

class CSRFTokenManager:
    """
    Manages CSRF tokens for form submission protection.
    
    Tokens are generated for GET requests and validated on POST requests.
    Stores: {token: {"created_at": datetime, "expires_at": datetime}}
    """
    
    def __init__(self):
        self._tokens: Dict[str, Dict] = {}
    
    def generate_token(self, token_lifetime_hours: int = 1) -> str:
        """
        Generate a new CSRF token.
        
        Args:
            token_lifetime_hours: How long token is valid (default: 1 hour)
            
        Returns:
            CSRF token string (32 bytes, URL-safe base64)
        """
        token = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        
        self._tokens[token] = {
            "created_at": now,
            "expires_at": now + timedelta(hours=token_lifetime_hours)
        }
        
        return token
    
    def validate_token(self, token: str) -> bool:
        """
        Validate a CSRF token.
        
        Args:
            token: Token to validate
            
        Returns:
            True if valid, False if invalid or expired
        """
        if token not in self._tokens:
            logger.warning("CSRF token not found")
            return False
        
        token_data = self._tokens[token]
        
        # Check if expired
        if datetime.utcnow() > token_data["expires_at"]:
            logger.warning("CSRF token expired")
            del self._tokens[token]
            return False
        
        # Token is valid, delete it (one-time use)
        del self._tokens[token]
        return True
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens from memory."""
        expired = [
            token for token, data in self._tokens.items()
            if datetime.utcnow() > data["expires_at"]
        ]
        for token in expired:
            del self._tokens[token]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired CSRF tokens")


# ===== GLOBAL INSTANCES =====

# Initialize global security managers
rate_limit_tracker = RateLimitTracker()
account_lockout_manager = AccountLockoutManager()
csrf_token_manager = CSRFTokenManager()


# ===== HELPER FUNCTIONS =====

def get_client_ip(request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check for X-Forwarded-For header (behind proxy)
    if hasattr(request, 'headers'):
        forwarded = request.headers.get('x-forwarded-for')
        if forwarded:
            return forwarded.split(',')[0].strip()
    
    # Fallback to direct client connection
    if hasattr(request, 'client') and request.client:
        return request.client.host
    
    return "unknown"
