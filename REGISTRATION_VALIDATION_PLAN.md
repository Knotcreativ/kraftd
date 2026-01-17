# Registration Process Validation Plan

**Date:** January 18, 2026  
**Status:** ⏳ Pending Backend Restart (CORS fix deployed)  
**Objective:** Validate complete registration flow from frontend to database

---

## 🔧 Issue Identified & Fixed

### Problem
Backend returning **404 Not Found** for:
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`  
- `GET /api/v1/health`

**Root Cause:** Missing CORS middleware configuration

### Solution Applied
✅ **Added CORS Configuration** to [backend/main.py](backend/main.py)
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Status:** ✅ Code committed and pushed to GitHub (commit: 77039d2)

### Next Step
⏳ **Container App Restart Required** - The backend container needs to be restarted to load the updated code
- Current state: Old container running (no CORS)
- Needed: New container with CORS enabled

---

## 📋 Registration Validation Test Plan

Once backend is restarted and online, follow this complete test plan:

### Test 1: Health Check ✅
**Objective:** Verify backend is responding

```bash
GET /api/v1/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-18T10:30:00Z",
  "uptime_seconds": 1234
}
```

**Success Criteria:**
- ✅ HTTP 200
- ✅ `status: "healthy"`
- ✅ Response time < 500ms

---

### Test 2: Registration Request (API Level)
**Objective:** Test backend registration endpoint directly

**Request:**
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "testuser123@kraftdintel.test",
  "password": "TestPassword123!@#"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Registration successful. Please login with your credentials."
}
```

**Success Criteria:**
- ✅ HTTP 200 (or 201 Created)
- ✅ `success: true`
- ✅ User created in Cosmos DB
- ✅ No error messages

**Failure Scenarios:**
- ❌ `"error": "User already exists"` (HTTP 409) - User registered twice
- ❌ `"error": "Invalid email format"` (HTTP 400) - Bad email
- ❌ `"error": "Password too weak"` (HTTP 400) - Weak password
- ❌ `"error": "Email required"` (HTTP 400) - Missing email
- ❌ `"error": "Password required"` (HTTP 400) - Missing password

---

### Test 3: Duplicate Registration (Error Handling)
**Objective:** Verify duplicate user prevention

**Request:**
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "testuser123@kraftdintel.test",
  "password": "DifferentPassword456!@#"
}
```

**Expected Response:**
```json
{
  "error": "User already exists",
  "message": "An account with this email already exists. Please login or use a different email."
}
```

**Success Criteria:**
- ✅ HTTP 409 Conflict
- ✅ `error: "User already exists"`
- ✅ No duplicate user created
- ✅ Clear error message

---

### Test 4: Cosmos DB Verification
**Objective:** Verify user record created correctly in database

**Check in Cosmos DB:**
1. Go to Azure Portal → Cosmos DB → kraftdintel-db
2. Select **Users** container
3. Run query:
```sql
SELECT * FROM c WHERE c.email = "testuser123@kraftdintel.test"
```

**Expected Result:**
```json
{
  "id": "user_uuid_1234",
  "email": "testuser123@kraftdintel.test",
  "password_hash": "bcrypt_hash_here",
  "created_at": "2026-01-18T10:30:00Z",
  "owner_email": "testuser123@kraftdintel.test",
  "documents_count": 0,
  "last_login": null
}
```

**Success Criteria:**
- ✅ User record exists
- ✅ Password is bcrypt hashed (not plaintext)
- ✅ `created_at` timestamp is recent
- ✅ `documents_count: 0`
- ✅ `last_login: null` (user hasn't logged in yet)

---

### Test 5: Frontend Registration Flow
**Objective:** Complete registration through the UI

**Steps:**
1. Open https://jolly-coast-03a4f4d03.4.azurestaticapps.net
2. Click "Register" button
3. Fill form:
   - **Email:** testuser456@kraftdintel.test
   - **Password:** FrontEndTest789!@#
   - **Confirm Password:** FrontEndTest789!@#
4. Click "Create Account" button
5. Wait for response

**Expected Behavior:**
- ✅ Input fields validate in real-time
- ✅ "Create Account" button is enabled
- ✅ Show loading indicator while processing
- ✅ Success notification appears: "Account created successfully!"
- ✅ Auto-redirect to login page
- ✅ Can now login with credentials

**Success Criteria:**
- ✅ No errors in browser console (F12)
- ✅ Network tab shows: `POST /api/v1/auth/register` with status 200
- ✅ User record in Cosmos DB
- ✅ Can login with registered credentials

---

### Test 6: Login After Registration
**Objective:** Verify newly registered user can login

**Steps:**
1. From login page (after registration)
2. Fill form:
   - **Email:** testuser456@kraftdintel.test
   - **Password:** FrontEndTest789!@#
3. Click "Login" button
4. Wait for response

**Expected Behavior:**
- ✅ Login processes
- ✅ JWT tokens generated
- ✅ Tokens stored in localStorage
- ✅ Redirect to dashboard
- ✅ Dashboard loads with "No documents" message

**Token Verification (Browser Console):**
```javascript
// In F12 Console, run:
localStorage.getItem('accessToken')      // Should return JWT
localStorage.getItem('refreshToken')     // Should return JWT
localStorage.getItem('user')             // Should return user info

// Tokens should look like:
// eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ...
```

**Success Criteria:**
- ✅ Both tokens present in localStorage
- ✅ Tokens are valid JWT format (3 base64 segments separated by dots)
- ✅ Dashboard displays
- ✅ Navigation bar shows user email

---

### Test 7: Token Expiration Handling
**Objective:** Verify token refresh mechanism

**Steps:**
1. Login successfully
2. Wait 61+ minutes (or manually set system clock forward)
3. Make any API request (e.g., GET /documents)

**Expected Behavior (Option A - Automatic Refresh):**
- ✅ Detect expired access token
- ✅ Use refresh token to get new access token
- ✅ Retry original request
- ✅ User doesn't notice interruption

**Expected Behavior (Option B - Force Re-login):**
- ✅ Detect expired token
- ✅ Clear localStorage
- ✅ Redirect to login page
- ✅ Message: "Session expired, please login again"

**Success Criteria:**
- ✅ One of the above behaviors happens
- ✅ No API errors (500, 503, etc.)
- ✅ User is not left in broken state

---

### Test 8: Security Validation
**Objective:** Verify password security

**Password Requirements Check:**
1. Try weak passwords:
   - `password` (no numbers/special chars)
   - `123456` (no letters)
   - `abc` (too short)

**Expected Behavior:**
- ✅ Frontend validates and shows error
- ✅ Backend also validates and rejects
- ✅ Clear error messages guide user

**Password Hashing Check (Backend):**
```python
# In backend logs, should see:
# Hashing password with bcrypt
# Password hashed successfully
# User stored with hash (not plaintext)
```

**Success Criteria:**
- ✅ Passwords never logged in plaintext
- ✅ Bcrypt hashing confirmed in DB
- ✅ Security standards met

---

### Test 9: Error Recovery
**Objective:** Verify user can recover from errors

**Test Cases:**

**A) Network Error During Registration**
1. Disable internet/network
2. Try to register
3. Show network error message
4. Re-enable network
5. Retry registration

**Expected Behavior:**
- ✅ Error message shown
- ✅ User can retry
- ✅ Registration succeeds on retry
- ✅ No duplicate user created

**B) Server Error (500)**
1. Backend temporarily unavailable
2. Try to register
3. Show: "Server error, please try again"
4. Retry after server recovers

**Expected Behavior:**
- ✅ Clear error message
- ✅ User can retry
- ✅ Works after recovery

**C) Invalid Input**
1. Try email: `not-an-email`
2. Try password: `` (empty)
3. Try email: `test@test` (no TLD)

**Expected Behavior:**
- ✅ Frontend shows validation error
- ✅ User can fix and retry
- ✅ Backend validates too (never trust frontend)

---

### Test 10: Metrics & Monitoring
**Objective:** Verify registration is being tracked

**Check Application Insights:**
1. Azure Portal → Application Insights → kraftdintel-app
2. Click "Analytics" (Kusto Queries)
3. Run:
```kusto
// Count registration attempts
requests
| where name contains "register"
| summarize count() by success, resultCode
```

**Expected Result:**
```
success  resultCode  count
true     200         5 (successful registrations)
false    409         2 (duplicates)
false    400         3 (validation errors)
```

**Success Criteria:**
- ✅ Registrations are being logged
- ✅ Success/failure tracked
- ✅ Performance metrics available
- ✅ Errors are captured for debugging

---

## 📊 Registration Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│              User Registration Flow                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Frontend: Browser                                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 1. User opens login page                         │  │
│  │ 2. Clicks "Register" button                      │  │
│  │ 3. Fills email & password                        │  │
│  │ 4. Frontend validates input                      │  │
│  │ 5. Sends POST /auth/register                     │  │
│  └──────────────────────────────────────────────────┘  │
│                      ↓                                   │
│  Backend: FastAPI Server                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 1. Receives registration request                 │  │
│  │ 2. Validates email format                        │  │
│  │ 3. Validates password strength                   │  │
│  │ 4. Checks if user exists in Cosmos DB            │  │
│  │ 5. Hashes password with bcrypt                   │  │
│  │ 6. Creates user document                         │  │
│  │ 7. Stores in Cosmos DB                           │  │
│  │ 8. Returns success response                      │  │
│  └──────────────────────────────────────────────────┘  │
│                      ↓                                   │
│  Database: Cosmos DB                                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Users Container:                                 │  │
│  │ {                                                │  │
│  │   "id": "user_123",                              │  │
│  │   "email": "user@test.com",                      │  │
│  │   "password_hash": "bcrypt_hash",                │  │
│  │   "created_at": "2026-01-18T10:30:00Z",         │  │
│  │   "documents_count": 0                           │  │
│  │ }                                                │  │
│  └──────────────────────────────────────────────────┘  │
│                      ↓                                   │
│  Frontend Response & UX                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 1. Shows success notification                    │  │
│  │ 2. Redirects to login page                       │  │
│  │ 3. User can now login                            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Checklist - Complete Registration Validation

- [ ] **Health Check** - Backend responds to /health
- [ ] **API Test** - POST /auth/register works
- [ ] **Duplicate Prevention** - Can't register twice
- [ ] **Database** - User created in Cosmos DB
- [ ] **Frontend UI** - Registration form renders
- [ ] **Frontend Submission** - Form submits successfully
- [ ] **Login** - Can login after registration
- [ ] **Tokens** - JWT tokens stored in localStorage
- [ ] **Security** - Password is bcrypt hashed
- [ ] **Error Handling** - Errors shown to user
- [ ] **Monitoring** - Events logged in Application Insights
- [ ] **Performance** - Registration < 2 seconds

---

## 🚀 Next Steps

1. **Restart Backend Container** (pending)
   - Container needs to reload code with CORS fix
   - Can be done via:
     - Azure Portal (Container Apps → Restart)
     - `az containerapp update` command
     - CI/CD pipeline (when set up)

2. **Run Tests** (after restart)
   - Execute all 10 tests above
   - Document results
   - Fix any issues

3. **Production Readiness**
   - All tests passing
   - Performance acceptable
   - Error handling working
   - Security validated

---

## 📞 Troubleshooting

### If Backend Still Returns 404
- ✅ Code is deployed (commit 77039d2 on main branch)
- ⏳ Container hasn't restarted yet
- **Action:** Manually restart Container App in Azure Portal

### If Password Hashing Fails
- Check bcrypt library is installed
- Verify in backend logs for hashing confirmation
- Test with CLI: `python -c "import bcrypt; print(bcrypt.hashpw(b'test', bcrypt.gensalt()))"`

### If Cosmos DB Connection Fails
- Check connection string is set
- Verify firewall rules allow connection
- Check DB exists and Users container exists
- Review backend logs for connection errors

---

**Status:** ⏳ Awaiting Backend Container Restart

Once complete, all tests will validate the registration process end-to-end.
