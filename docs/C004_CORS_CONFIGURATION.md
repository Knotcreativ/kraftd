# C-004: Update CORS Configuration Implementation

**Status**: NOT STARTED  
**Effort**: 1 hour  
**Priority**: HIGH - Security  

## Current Issue
CORS wildcard (*) allows requests from any origin, security risk in production.

## Implementation

### Current Code (backend/main.py):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ SECURITY RISK
    ...
)
```

### Production Fix:
```python
ALLOWED_ORIGINS = [
    "https://kraftdintel.com",
    "https://www.kraftdintel.com",
    "https://staging.kraftdintel.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)
```

### Configuration by Environment:
- **Development**: localhost:3000, 127.0.0.1:3000
- **Staging**: https://staging.kraftdintel.com
- **Production**: https://kraftdintel.com, https://www.kraftdintel.com

## Files to Modify
1. `backend/config.py` - Add CORS_ORIGINS setting
2. `backend/main.py` - Use config-based origins

## Testing
```bash
# Test valid origin
curl -H "Origin: https://kraftdintel.com" http://localhost:8000/api/v1/health

# Test invalid origin (should fail)
curl -H "Origin: https://evil.com" http://localhost:8000/api/v1/health
```

## Success Criteria
✅ Only specified origins allowed  
✅ Wildcard removed from production  
✅ Environment-specific configuration  
✅ Credentials properly handled  
