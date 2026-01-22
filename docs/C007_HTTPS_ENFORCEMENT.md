# C-007: HTTPS Enforcement Implementation

**Status**: NOT STARTED  
**Effort**: 1 hour  
**Priority**: HIGH - Security  

## Objective
Enforce HTTPS in production environment with security headers.

## Implementation

### 1. HTTPS Middleware
```python
class HTTPSRedirectMiddleware:
    async def __call__(self, request, call_next):
        if request.url.scheme != "https" and not DEBUG:
            # Redirect HTTP to HTTPS
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=url)
        return await call_next(request)
```

### 2. Security Headers
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

### 3. Configuration
```yaml
# Environment-specific
HTTPS_REQUIRED: true  # Production only
HSTS_MAX_AGE: 31536000  # 1 year
SECURE_COOKIES: true
```

### 4. Application Settings
- Ensure TLS 1.2+ only
- Use strong cipher suites
- Certificate pinning if needed

## Deployment Configuration

### Azure Container Apps
- Configure custom domain with TLS
- Enable HTTPS Only
- Use managed certificates

### Dockerfile
```dockerfile
ENV HTTPS_REQUIRED=true
ENV HSTS_MAX_AGE=31536000
```

## Files to Modify
1. `backend/main.py` - Add HTTPS middleware
2. `backend/config.py` - HTTPS configuration
3. `Dockerfile` - Set environment variables
4. `docker-compose.yml` - Configure for local HTTPS (optional)

## Testing
```bash
# Test HTTPS redirect
curl -i http://localhost:8000/api/v1/health
# Should get 307 redirect to https

# Test security headers
curl -I https://localhost:8000/api/v1/health
# Check for Strict-Transport-Security header
```

## Success Criteria
✅ All HTTP traffic redirects to HTTPS  
✅ HSTS header configured  
✅ Security headers present  
✅ TLS 1.2+ only  
✅ Strong cipher suites  
