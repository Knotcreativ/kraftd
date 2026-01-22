# C-008: Token Revocation on Logout Implementation

**Status**: NOT STARTED  
**Effort**: 2 hours  
**Priority**: HIGH - Security  

## Current Issue
Tokens remain valid even after logout - users can be tracked via stolen tokens indefinitely.

## Solution: Token Blacklist System

### 1. Token Blacklist Storage
Options:
- Redis (recommended, fast expiration)
- Database (persistent, slower)
- In-memory (development only)

### 2. Implementation Architecture
```
User Logout
    ↓
Extract token
    ↓
Add to blacklist
    ↓
Return success
    ↓
On subsequent requests, check if token in blacklist
```

### 3. Token Blacklist Model
```python
class TokenBlacklist(BaseModel):
    token: str
    user_id: str
    blacklisted_at: datetime
    expires_at: datetime  # Same as token expiration
    reason: str  # "logout", "password_change", etc.
```

### 4. Redis Implementation
```python
# Add token to blacklist
redis.setex(
    f"blacklist:{token_id}",
    token_expiration_seconds,
    user_id
)

# Check if token blacklisted
if redis.exists(f"blacklist:{token_id}"):
    raise InvalidTokenError("Token has been revoked")
```

### 5. Logout Endpoint Enhancement
```python
@app.post("/api/v1/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    token = request.headers.get("Authorization").split(" ")[1]
    
    # Add to blacklist
    add_to_blacklist(token, current_user["user_id"])
    
    # Clear session
    # Clear cookies if applicable
    
    return {"message": "Logged out successfully"}
```

### 6. Token Verification with Blacklist
```python
def verify_token(token: str):
    # Check if blacklisted first
    if is_blacklisted(token):
        raise InvalidTokenError("Token has been revoked")
    
    # Then verify signature
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return payload
```

### 7. Automatic Cleanup
- Blacklist entries expire automatically in Redis
- No manual cleanup needed
- Old entries removed by TTL

### 8. Additional Features
- Password change: Revoke all tokens
- Security breach: Revoke all user tokens
- Device logout: Revoke specific device tokens
- Session management: Multiple concurrent sessions

## Files to Modify
1. `backend/services/auth_service.py` - Add blacklist logic
2. `backend/routes/auth.py` - Implement logout endpoint
3. `backend/config.py` - Blacklist configuration
4. `requirements.txt` - Add redis package

## Configuration
```yaml
TOKEN_BLACKLIST_ENABLED: true
TOKEN_BLACKLIST_BACKEND: redis  # or database
REDIS_URL: redis://localhost:6379
```

## Testing
```bash
# Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"password"}' | jq -r '.access_token')

# Use token (should work)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/protected

# Logout
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/auth/logout

# Try using token again (should fail)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/protected
# Expected: 401 Token has been revoked
```

## Success Criteria
✅ Tokens revoked on logout  
✅ Revoked tokens rejected on API access  
✅ Blacklist cleaned up automatically  
✅ Password changes revoke all tokens  
✅ Security breach revocation works  
