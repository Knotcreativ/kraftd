"""Rate limiting middleware for Kraftd Docs Backend."""
import time
import logging
from typing import Dict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

class RateLimitStore:
    """Store for rate limit tracking."""
    
    def __init__(self):
        """Initialize rate limit store."""
        self.requests: Dict[str, list] = {}  # client_id -> [timestamp, timestamp, ...]
        self.cleanup_interval = 60  # seconds
        self.last_cleanup = time.time()
    
    def is_allowed(self, client_id: str, requests_per_minute: int, requests_per_hour: int) -> bool:
        """Check if client is within rate limits."""
        now = time.time()
        
        # Cleanup old entries periodically
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup(now)
        
        # Initialize if needed
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove old requests outside the hour window
        one_hour_ago = now - 3600
        self.requests[client_id] = [t for t in self.requests[client_id] if t > one_hour_ago]
        
        # Check per-hour limit
        if len(self.requests[client_id]) >= requests_per_hour:
            return False
        
        # Check per-minute limit
        one_minute_ago = now - 60
        recent_requests = [t for t in self.requests[client_id] if t > one_minute_ago]
        if len(recent_requests) >= requests_per_minute:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True
    
    def get_retry_after(self, client_id: str) -> int:
        """Get seconds until client can make next request."""
        if client_id not in self.requests or not self.requests[client_id]:
            return 0
        
        now = time.time()
        oldest_request = min(self.requests[client_id])
        
        # Next slot opens after 60 seconds from oldest recent request
        retry_time = oldest_request + 60
        retry_after = max(0, int(retry_time - now) + 1)
        return retry_after
    
    def _cleanup(self, now: float):
        """Remove old entries."""
        one_hour_ago = now - 3600
        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [t for t in self.requests[client_id] if t > one_hour_ago]
            if not self.requests[client_id]:
                del self.requests[client_id]
        self.last_cleanup = now

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        """Initialize middleware."""
        super().__init__(app)
        self.store = RateLimitStore()
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        logger.info(f"Rate limiting enabled: {requests_per_minute} req/min, {requests_per_hour} req/hour")
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path in ["/", "/health"]:
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_id = request.client.host if request.client else "unknown"
        
        # Check rate limit
        if not self.store.is_allowed(client_id, self.requests_per_minute, self.requests_per_hour):
            retry_after = self.store.get_retry_after(client_id)
            logger.warning(f"Rate limit exceeded for client {client_id}")
            
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after_seconds": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        
        return response
