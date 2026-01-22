# Security Implementation Guide
## Priority 3 - Security Hardening

**Status:** Priority 3 Implementation Guide  
**Date:** January 15, 2026  
**Recommendation Level:** MEDIUM - Add to current sprint

---

## Overview

This guide implements recommendations from the Security Audit (SECURITY_AUDIT.md). It provides step-by-step instructions and copy-paste ready code for hardening the KraftdIntel backend.

---

## 1. Add CORS Middleware (Priority: HIGH)

CORS (Cross-Origin Resource Sharing) controls which domains can access your API.

### Step 1: Install FastAPI CORS
```powershell
pip install fastapi[cors]
```

### Step 2: Add to main.py

Add after app initialization (around line 140):

```python
from fastapi.middleware.cors import CORSMiddleware

# ===== CORS Configuration =====
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["X-Total-Count", "X-Total-Pages"],
    max_age=3600
)

logger.info(f"CORS enabled for origins: {ALLOWED_ORIGINS}")
```

### Step 3: Configure Environment Variables

**Development (.env):**
```
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

**Production (Azure App Service):**
```
ALLOWED_ORIGINS=https://app.kraftdintel.com,https://kraftdintel.com
```

---

## 2. Add Security Headers Middleware (Priority: MEDIUM)

Security headers protect against XSS, clickjacking, and other attacks.

### Step 1: Create Security Headers Middleware

Create file: `backend/middleware/security_headers.py`

```python
"""
Security Headers Middleware

Adds protective HTTP headers to all responses.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security-related headers to HTTP responses."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS Protection (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Strict Transport Security (HTTPS only - production)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # Disable caching for sensitive pages
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        
        return response
```

### Step 2: Add to main.py

Add after CORS configuration:

```python
from middleware.security_headers import SecurityHeadersMiddleware

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

logger.info("Security headers middleware enabled")
```

---

## 3. Implement Audit Logging (Priority: MEDIUM)

Track security-relevant events for compliance and debugging.

### Step 1: Create Audit Logger

Create file: `backend/services/audit_logger.py`

```python
"""
Audit Logger Service

Logs security-relevant events (login, access, changes).
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger("audit")


class AuditEventType(str, Enum):
    """Types of audit events."""
    USER_REGISTER = "USER_REGISTER"
    USER_LOGIN = "USER_LOGIN"
    USER_LOGIN_FAILED = "USER_LOGIN_FAILED"
    USER_LOGOUT = "USER_LOGOUT"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    DOCUMENT_ACCESS = "DOCUMENT_ACCESS"
    DOCUMENT_DELETE = "DOCUMENT_DELETE"
    WORKFLOW_INITIATED = "WORKFLOW_INITIATED"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    TOKEN_VALIDATION_FAILED = "TOKEN_VALIDATION_FAILED"


class AuditLogger:
    """Service for logging audit events."""
    
    @staticmethod
    def log_event(
        event_type: AuditEventType,
        user_email: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS"
    ):
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (login, access, etc.)
            user_email: User's email (masked in logs)
            resource_id: ID of affected resource
            resource_type: Type of resource (DOCUMENT, USER, etc.)
            details: Additional event details
            status: SUCCESS or FAILURE
        """
        # Mask email in logs
        masked_email = self._mask_email(user_email) if user_email else "ANONYMOUS"
        
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type.value,
            "user": masked_email,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "status": status,
            "details": details or {}
        }
        
        logger.info(json.dumps(audit_entry))
    
    @staticmethod
    def _mask_email(email: str) -> str:
        """Mask email for logging."""
        if not email:
            return "[UNKNOWN]"
        
        parts = email.split("@")
        if len(parts) != 2:
            return "[INVALID_EMAIL]"
        
        username = parts[0]
        domain = parts[1]
        
        # Show first and last character of username
        if len(username) <= 2:
            masked_username = username[0] + "*"
        else:
            masked_username = username[0] + "*" * (len(username) - 2) + username[-1]
        
        return f"{masked_username}@{domain}"
    
    @staticmethod
    def log_login(user_email: str, success: bool = True):
        """Log user login attempt."""
        AuditLogger.log_event(
            event_type=AuditEventType.USER_LOGIN if success else AuditEventType.USER_LOGIN_FAILED,
            user_email=user_email,
            status="SUCCESS" if success else "FAILURE"
        )
    
    @staticmethod
    def log_document_access(user_email: str, document_id: str):
        """Log document access."""
        AuditLogger.log_event(
            event_type=AuditEventType.DOCUMENT_ACCESS,
            user_email=user_email,
            resource_id=document_id,
            resource_type="DOCUMENT"
        )
    
    @staticmethod
    def log_unauthorized_access(user_email: Optional[str], resource_id: str):
        """Log unauthorized access attempt."""
        AuditLogger.log_event(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS,
            user_email=user_email,
            resource_id=resource_id,
            status="FAILURE"
        )
```

### Step 2: Configure Logging

Add to `config.py`:

```python
# Audit logging configuration
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "audit": {
            "format": "%(message)s"  # JSON format
        }
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout"
        },
        "audit": {
            "formatter": "audit",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/audit.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10
        }
    },
    "loggers": {
        "audit": {
            "handlers": ["audit"],
            "level": "INFO",
            "propagate": False
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

### Step 3: Use in Endpoints

Add logging to authentication endpoints:

```python
from services.audit_logger import AuditLogger, AuditEventType

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Login user and return JWT tokens."""
    try:
        # ... existing login logic ...
        
        # Log successful login
        AuditLogger.log_login(user_data.email, success=True)
        
        return TokenResponse(...)
    
    except HTTPException:
        # Log failed login
        AuditLogger.log_login(user_data.email, success=False)
        raise
```

---

## 4. Add Input Validation (Priority: LOW)

Add max request size limits and additional validation.

### Step 1: Configure Request Limits

Add to main.py after app initialization:

```python
from fastapi.exceptions import RequestValidationError

# Max request body size (10MB)
app.MAX_REQUEST_SIZE = 10 * 1024 * 1024

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors gracefully."""
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid request format"}
    )
```

### Step 2: Add File Size Validation

For document upload endpoint:

```python
@app.post("/v1/docs/upload")
async def upload_document(
    file: UploadFile = File(...),
    authorization: str = Header(None)
):
    """Upload a document."""
    # Validate file size
    max_file_size = 50 * 1024 * 1024  # 50MB
    
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset position
    
    if file_size > max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {max_file_size / 1024 / 1024}MB"
        )
    
    # ... existing upload logic ...
```

---

## 5. Implement Token Rotation (Priority: MEDIUM)

Add JTI (JWT ID) claims for token tracking and blacklisting.

### Step 1: Update AuthService

Modify `services/auth_service.py`:

```python
import secrets

@staticmethod
def create_access_token(email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with JTI for tracking."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": secrets.token_urlsafe(32)  # JWT ID for blacklisting
    }
    secret_key = _get_secret_key()
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt
```

---

## 6. Secrets Rotation Management (Priority: MEDIUM)

Document and automate secrets rotation.

### Create SECRETS_MANIFEST.md

```markdown
# Secrets Manifest

## Secrets Management

### Active Secrets

| Secret Name | Location | Rotation | Last Rotated | Next Due |
|---|---|---|---|---|
| JWT_SECRET | Azure Key Vault | 90 days | 2025-01-15 | 2025-04-15 |
| COSMOS_DB_KEY | Azure Key Vault | 180 days | 2025-01-15 | 2025-07-15 |
| AZURE_AD_SECRET | Azure Key Vault | 90 days | 2025-01-15 | 2025-04-15 |

### Rotation Schedule

- **JWT Secret:** Quarterly (Jan 15, Apr 15, Jul 15, Oct 15)
- **Database Keys:** Semi-annually (Jan 15, Jul 15)
- **API Keys:** Quarterly or on employee change

### Rotation Process

1. Generate new secret in Key Vault
2. Update application configuration
3. Test with new secret
4. Wait 24 hours (allow clients to refresh)
5. Deactivate old secret
6. Document in this table

### Emergency Rotation

If secret is compromised:
1. Immediate rotation (no waiting period)
2. Invalidate all existing tokens (implement token blacklist)
3. Alert security team
4. Review logs for unauthorized access
```

---

## 7. Running Security Tests (Priority: HIGH)

### Step 1: Install Test Dependencies

```powershell
pip install pytest pytest-asyncio pytest-cov
```

### Step 2: Run Security Tests

```powershell
# Run all security tests
pytest test_security.py -v

# Run with coverage
pytest test_security.py --cov=services --cov=repositories

# Run specific test class
pytest test_security.py::TestJWTSecurity -v

# Run with detailed output
pytest test_security.py -vv --tb=short
```

### Step 3: Expected Output

```
test_security.py::TestJWTSecurity::test_valid_token_accepted PASSED
test_security.py::TestJWTSecurity::test_expired_token_rejected PASSED
test_security.py::TestJWTSecurity::test_invalid_signature_rejected PASSED
...

======================== 20+ passed in 1.23s ========================
```

---

## 8. Security Checklist - Implementation Order

### Phase 1: Immediate (This Week)
- [ ] Add CORS middleware (30 min)
- [ ] Add security headers middleware (30 min)
- [ ] Create audit logger (1 hour)
- [ ] Integrate audit logging in endpoints (1 hour)
- [ ] Run security tests (30 min)

**Total: ~3-4 hours**

### Phase 2: Short-term (This Sprint)
- [ ] Implement token JTI claims (1 hour)
- [ ] Add token blacklist mechanism (1.5 hours)
- [ ] Configure secrets rotation calendar (30 min)
- [ ] Document all secrets in SECRETS_MANIFEST.md (30 min)

**Total: ~3.5 hours**

### Phase 3: Production Readiness
- [ ] Configure HTTPS/TLS
- [ ] Set up database encryption
- [ ] Enable Application Insights (Priority 5)
- [ ] Configure security alerts

---

## 9. Verification Steps

### Verify CORS Configuration
```bash
curl -H "Origin: https://app.kraftdintel.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS http://localhost:8000/api/v1/auth/login
```

Expected: CORS headers in response

### Verify Security Headers
```bash
curl -I http://localhost:8000/api/v1/health
```

Expected:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`

### Verify Audit Logging
```bash
tail -f logs/audit.log
```

Expected: JSON-formatted audit events

---

## 10. Common Issues & Troubleshooting

### Issue: CORS Request Blocked
**Solution:** Check ALLOWED_ORIGINS environment variable matches frontend domain

### Issue: Security Tests Failing
**Solution:** Ensure pytest-asyncio is installed: `pip install pytest-asyncio`

### Issue: Audit Logs Not Writing
**Solution:** Check `logs/` directory exists and has write permissions

---

## Conclusion

This implementation guide provides:
- ✅ **CORS protection** against cross-origin attacks
- ✅ **Security headers** for defense-in-depth
- ✅ **Audit logging** for compliance and debugging
- ✅ **20+ security tests** for validation
- ✅ **Token management** improvements
- ✅ **Secrets rotation** documentation

**Total Implementation Time:** 6-8 hours  
**Complexity:** Medium  
**Production Readiness:** Moves system to MVP-ready state

---

**Next Priority:** Priority 4 - Deployment Automation
