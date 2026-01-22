# C-006: Enforce API Rate Limiting Implementation

**Status**: NOT STARTED  
**Effort**: 2 hours  
**Priority**: MEDIUM - Security  

## Current State
- Basic rate limiting in place (60 req/min global)
- No per-endpoint configuration
- No per-user limiting
- No rate limit headers in response

## Enhancement Plan

### 1. Per-Endpoint Rate Limits
```python
@app.post("/api/v1/auth/login")
@rate_limit(requests=5, window="1m")  # 5 logins per minute
async def login():
    pass

@app.post("/api/v1/auth/register")
@rate_limit(requests=3, window="1h")  # 3 registrations per hour
async def register():
    pass

@app.get("/api/v1/health")
@rate_limit(requests=100, window="1m")  # Health checks allowed
async def health():
    pass
```

### 2. Per-User Rate Limiting
```python
@rate_limit_per_user(
    requests=100,
    window="1h",
    key="user_id"
)
async def get_user_documents(current_user):
    pass
```

### 3. Rate Limit Response Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705598400
Retry-After: 60
```

### 4. Backend Storage
Options:
- Redis (recommended for production)
- In-memory (for development)
- Azure Cache for Redis

### 5. Configuration by Environment
```yaml
# Development
RATE_LIMIT_ENABLED: false

# Staging
RATE_LIMIT_REQUESTS_PER_MINUTE: 60
RATE_LIMIT_REQUESTS_PER_HOUR: 1000

# Production
RATE_LIMIT_REQUESTS_PER_MINUTE: 30
RATE_LIMIT_REQUESTS_PER_HOUR: 500
```

## Implementation Steps
1. Set up Redis connection
2. Create decorator for per-endpoint limits
3. Create decorator for per-user limits
4. Add rate limit headers to responses
5. Configure by environment
6. Monitor and adjust limits based on usage

## Files to Modify
1. `backend/rate_limit.py` - Enhanced limiting
2. `backend/main.py` - Apply decorators to endpoints
3. `backend/config.py` - Rate limit configuration

## Success Criteria
✅ Per-endpoint rate limiting  
✅ Per-user rate limiting  
✅ Rate limit headers in responses  
✅ Redis backend configured  
✅ Environment-specific configuration  
✅ Monitoring and alerting  
