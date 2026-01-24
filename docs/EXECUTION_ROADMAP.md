# KraftdIntel Execution Roadmap: Critical Actions for Market Launch

**Status:** READY TO EXECUTE  
**Target Completion:** January 24-31, 2026  
**Estimated Total Time:** 4-5 hours  

---

## CRITICAL ACTIONS (Must Complete Before Launch)

### ACTION #1: Merge SWA Configuration Fix [⏱️ 10 minutes]

**What:** Merge the `fix/swa-config-align` branch to main  
**Why:** Current main has incorrect staticwebapp.json pointing to `frontend-next`, causing SWA deployment to fail  
**Current State:** Branch exists, ready to merge

#### Steps:

1. **Create/Review PR on GitHub**
   ```
   Go to: https://github.com/Knotcreativ/kraftd/pull/new/fix/swa-config-align
   Review the 3 files changed:
   - staticwebapp.json: appLocation frontend-next → frontend
   - frontend/staticwebapp.config.json: Simplified routes
   - docs/FRONTEND_DUPLICATES.md: Added duplicates report
   Click "Create Pull Request"
   ```

2. **Merge PR**
   ```
   After review, click "Merge pull request"
   Confirm delete of branch (optional)
   ```

3. **Verify GitHub Actions Triggers**
   ```
   Go to: Actions tab → azure-static-web-apps workflow
   Should see new workflow run START automatically
   Wait for completion (~3-5 minutes)
   Expected: ✅ Build succeeded, Deploy succeeded
   ```

4. **Validate Frontend Deployment**
   ```
   Visit: https://green-mushroom-06da9040f.1.azurestaticapps.net/
   Expected: Login page loads, no 404 errors
   Check browser console: No "Failed to load /src/main.tsx" errors
   ```

**Validation Checklist:**
- [ ] PR merged to main
- [ ] GitHub Actions workflow completed successfully
- [ ] Frontend URL loads without 404s
- [ ] No JavaScript console errors

---

### ACTION #2: Resolve Backend TODOs [⏱️ 1.5 hours]

#### TODO #1: Email Verification Implementation (Line 903)

**File:** `backend/main.py`  
**Current State:** Placeholder comment  
**Required For:** User account security

**Implementation Plan:**

```python
# 1. Update user model to include verification fields
# File: backend/models/user.py
class User(BaseModel):
    email: str
    verified: bool = False
    verification_code: Optional[str] = None
    verification_code_expires: Optional[datetime] = None
    
# 2. Add verification endpoints to main.py (around line 903)
@app.post("/api/v1/register")
async def register(user: UserRegister):
    # Generate 6-digit verification code
    import random
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    # Store user with code and 24-hour expiration
    user_data = {
        'email': user.email,
        'password_hash': hash_password(user.password),
        'verified': False,
        'verification_code': code,
        'verification_code_expires': datetime.utcnow() + timedelta(hours=24)
    }
    
    # Save to Cosmos DB
    await cosmos.create_item('users', user_data)
    
    # Send verification email
    await send_verification_email(user.email, code)
    
    return {"message": "Registration successful. Check your email."}

@app.post("/api/v1/verify-email")
async def verify_email(email: str, code: str):
    # Get user from database
    user = await cosmos.query_item('users', {'email': email})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify code matches and hasn't expired
    if user['verification_code'] != code:
        raise HTTPException(status_code=400, detail="Invalid code")
    
    if datetime.fromisoformat(user['verification_code_expires']) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Code expired")
    
    # Mark as verified
    user['verified'] = True
    user['verification_code'] = None
    user['verification_code_expires'] = None
    
    await cosmos.update_item('users', user)
    
    return {"message": "Email verified successfully"}

@app.post("/api/v1/resend-verification")
async def resend_verification(email: str):
    user = await cosmos.query_item('users', {'email': email})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get('verified'):
        raise HTTPException(status_code=400, detail="Already verified")
    
    # Generate new code
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    user['verification_code'] = code
    user['verification_code_expires'] = (datetime.utcnow() + timedelta(hours=24)).isoformat()
    
    await cosmos.update_item('users', user)
    await send_verification_email(email, code)
    
    return {"message": "Verification code resent"}

# 3. Helper function for sending email
async def send_verification_email(email: str, code: str):
    """Send verification email via Azure Email Service or SendGrid"""
    # TODO: Configure email service in config.py
    # Recommendation: Use Azure Communication Services
    # or SendGrid for production
    pass
```

**Testing:**
```bash
# 1. Unit test
cd backend
python -m pytest tests/test_auth.py -v

# 2. Manual test
curl -X POST http://localhost:8000/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
# Expected: Returns 200 with "Check your email" message

# 3. Verify code in database
# Check Cosmos DB that user has verification_code populated
```

---

#### TODO #2: Auth Context Extraction (Line 1720)

**File:** `backend/main.py`  
**Current State:** Hardcoded owner email  
**Required For:** Multi-tenant isolation, proper document ownership

**Implementation Plan:**

```python
# 1. Create auth utilities (if not exist)
# File: backend/middleware/auth.py
from fastapi import Depends, HTTPException
from jose import jwt, JWTError

async def get_current_user(request: Request) -> dict:
    """Extract authenticated user from JWT token"""
    token = request.headers.get("Authorization")
    
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    
    # Remove "Bearer " prefix
    token = token.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET"),
            algorithms=["HS256"]
        )
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"email": email}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# 2. Update line 1720 in main.py
# BEFORE:
owner_email = "default@kraftdintel.com"  # TODO: Get from auth context

# AFTER:
current_user = await get_current_user(request)
owner_email = current_user["email"]

# 3. Apply to all document routes
@app.get("/api/v1/documents")
async def get_documents(request: Request):
    current_user = await get_current_user(request)
    
    # Query documents where partition key = user email
    docs = await cosmos.query_items(
        'documents',
        f"SELECT * FROM c WHERE c.user_email = '{current_user['email']}'"
    )
    
    return docs

@app.post("/api/v1/documents")
async def create_document(request: Request, doc_data: DocumentCreate):
    current_user = await get_current_user(request)
    
    doc = {
        'id': str(uuid.uuid4()),
        'user_email': current_user['email'],  # Set from auth context
        'title': doc_data.title,
        'created_at': datetime.utcnow().isoformat()
    }
    
    await cosmos.create_item('documents', doc)
    return doc
```

**Testing:**
```bash
# 1. Unit test
cd backend
python -m pytest tests/test_auth_context.py -v

# 2. Manual test with JWT token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"test"}' | jq -r '.access_token')

curl -X GET http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer $TOKEN"
# Expected: Returns only documents where user_email matches token
```

**Completion Criteria:**
- [ ] Email verification fully implemented and tested
- [ ] Auth context extracted in all document routes
- [ ] All pytest tests passing: `python -m pytest backend/tests/ -v`
- [ ] No TODOs/FIXMEs remaining in main.py

---

### ACTION #3: Archive Deprecated Frontend [⏱️ 30 minutes]

**What:** Move `frontend-next/` to archive and remove from CI/CD  
**Why:** Dual frontends create confusion and increase maintenance burden  
**Current State:** frontend-next exists but isn't used in GitHub Actions

#### Steps:

```bash
# 1. Create archive directory (if not exists)
mkdir -p ARCHIVE_OUTDATED_DOCS

# 2. Move frontend-next to archive
mv frontend-next ARCHIVE_OUTDATED_DOCS/frontend-next-deprecated

# 3. Verify no references in CI/CD
grep -r "frontend-next" .github/workflows/
# Should return nothing (or only in archived files)

# 4. Verify staticwebapp.json doesn't reference it
grep "frontend-next" staticwebapp.json
# Should return nothing

# 5. Commit changes
git add -A
git commit -m "chore: archive deprecated Next.js frontend to archive

- Moved frontend-next/ to ARCHIVE_OUTDATED_DOCS/frontend-next-deprecated/
- This was an experimental frontend, Vite (frontend/) is production target
- Reduces repo clutter and confusion
- No impact on active builds (GitHub Actions uses frontend/)"

# 6. Push to main
git push origin main
```

**Verification:**
- [ ] `frontend-next/` moved to `ARCHIVE_OUTDATED_DOCS/`
- [ ] No broken imports in active code
- [ ] staticwebapp.json uses `frontend/` only
- [ ] GitHub Actions still targets `frontend/`

---

## HIGH-PRIORITY ACTIONS (Complete Before First Users)

### ACTION #4: Frontend Build & Validation [⏱️ 15 minutes]

```bash
# 1. Install dependencies
cd frontend
npm ci

# 2. Build for production
npm run build

# 3. Verify dist/ folder created
ls -la dist/
# Should see: index.html, assets/, manifest.json

# 4. Check for production readiness
# - No /src/ references in HTML
# - No source maps (*.map files)
# - Assets are bundled and minified

# 5. Optional: Test locally
npm run preview
# Visit http://localhost:4173
# Should see fully functional app
```

**Expected Output:**
```
✓ 512 modules transformed.
✓ built in 2.64s

dist/
├── index.html        (entry point)
├── assets/
│   ├── app-xxx.js    (minified)
│   ├── vendor-yyy.js (minified)
│   └── style-zzz.css (minified)
└── manifest.json     (vite metadata)
```

---

### ACTION #5: Backend Tests [⏱️ 20 minutes]

```bash
# 1. Navigate to backend
cd backend

# 2. Install test dependencies (if needed)
pip install pytest pytest-asyncio pytest-cov

# 3. Run all tests
python -m pytest tests/ -v --tb=short

# 4. Check coverage (optional)
python -m pytest tests/ --cov=backend --cov-report=html

# 5. Run specific test suites
python -m pytest tests/test_auth.py -v       # Auth tests
python -m pytest tests/test_cosmos.py -v     # Database tests
python -m pytest tests/test_api.py -v        # API endpoint tests
```

**Expected:** All tests pass with no warnings

---

### ACTION #6: Environment Variables [⏱️ 10 minutes]

```bash
# 1. Verify .env exists
ls -la .env

# 2. Check for placeholder values
cat .env | grep -E "PLACEHOLDER|your-|XXX|TODO"
# Should return nothing (all values set)

# 3. Verify critical variables set
cat .env | grep -E "COSMOS|OPENAI|JWT|DATABASE"

# 4. Sensitive check (don't print values, just verify keys exist)
echo "Checking .env completeness:"
for var in COSMOS_ENDPOINT COSMOS_KEY OPENAI_KEY JWT_SECRET AZURE_STORAGE_CONNECTION_STRING; do
    grep -q "^${var}=" .env && echo "✓ $var" || echo "✗ $var MISSING"
done
```

---

## TESTING & VALIDATION

### Smoke Test Suite [⏱️ 20 minutes]

```bash
#!/bin/bash
# scripts/smoke_test.sh

echo "=== KraftdIntel Pre-Launch Smoke Test ==="
echo ""

# 1. Frontend tests
echo "1. Testing Frontend..."
FRONTEND_URL="https://green-mushroom-06da9040f.1.azurestaticapps.net"
curl -s -o /dev/null -w "Frontend Status: %{http_code}\n" "$FRONTEND_URL"
# Expected: 200

# 2. Backend API tests
echo "2. Testing Backend API..."
API_URL="https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1"

# Health check (if implemented)
curl -s "$API_URL/health" 2>/dev/null || echo "⚠️  Health endpoint not available"

# 3. Database connection test
echo "3. Testing Database..."
python test_cosmos_connection.py
# Expected: Connection successful

# 4. Authentication test
echo "4. Testing Authentication..."
# Try login with test account
curl -X POST "$API_URL/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}' \
  2>/dev/null | jq .
# Expected: Either 200 (success) or 401 (auth failed) - NOT 500 errors

echo ""
echo "=== Smoke Test Complete ==="
```

---

## DEPLOYMENT TIMELINE

### Day 1 (Today): Critical Fixes
- ✅ 9:00 - Review this document
- ✅ 9:30 - Merge fix/swa-config-align PR (ACTION #1)
- ✅ 10:00 - Validate SWA deployment
- ✅ 10:30 - Start Backend TODOs (ACTION #2)

### Day 2: Code Completion
- ✅ 9:00 - Complete Email Verification implementation
- ✅ 11:00 - Complete Auth Context extraction
- ✅ 2:00 - Run full test suite
- ✅ 3:00 - Archive frontend-next (ACTION #3)

### Day 3: Final Validation
- ✅ 9:00 - Frontend build (ACTION #4)
- ✅ 9:30 - Backend tests (ACTION #5)
- ✅ 10:00 - Environment setup (ACTION #6)
- ✅ 10:30 - Smoke test suite
- ✅ 11:00 - Ready for launch ✅

---

## Success Criteria

**All of the following must be TRUE before launch:**

- [ ] staticwebapp.json merged and SWA deployment successful
- [ ] Frontend loads at https://green-mushroom-06da9040f.1.azurestaticapps.net/
- [ ] Email verification implemented and tested
- [ ] Auth context extraction implemented
- [ ] All backend tests pass: `pytest tests/ -v`
- [ ] frontend-next archived
- [ ] Frontend build creates dist/ with production assets
- [ ] .env has all production credentials (no placeholders)
- [ ] Smoke tests passing
- [ ] No console errors in browser
- [ ] No 500 errors in backend API

---

## Emergency Rollback Plan

If deployment fails after merge:

```bash
# 1. Identify issue
git log --oneline -5

# 2. Rollback last commit
git revert HEAD
git push origin main
# GitHub Actions re-triggers

# 3. Fix locally
# - Edit staticwebapp.json or routes config
# - Test locally

# 4. Re-deploy
git add <fixed-files>
git commit -m "fix: correct SWA configuration"
git push origin main
```

---

## Post-Launch Monitoring

**First 24 hours:**
- [ ] Monitor Application Insights errors
- [ ] Check SWA deployment logs
- [ ] Verify API response times < 500ms
- [ ] Monitor Cosmos DB throughput

**First week:**
- [ ] Collect user feedback
- [ ] Monitor error rates
- [ ] Review performance metrics
- [ ] Patch any critical issues

---

**Document Status:** Ready to Execute  
**Last Updated:** January 24, 2026  
**Estimated Completion:** January 27, 2026
