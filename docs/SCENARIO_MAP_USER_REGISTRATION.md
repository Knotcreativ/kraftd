# User Registration Scenario Mapping

**Objective:** Map complete user registration flow with all scenarios, validations, and outcomes

---

## 1. Happy Path - Successful Registration

### 1.1 User Journey Flow

```
┌─────────────────┐
│   User Visits   │
│  Registration   │ https://jolly-coast-03a4f4d03.4.azurestaticapps.net/register
│      Page       │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Frontend - Registration Form       │
│  ├─ Email field                     │
│  ├─ Password field                  │
│  ├─ First Name field                │
│  ├─ Last Name field                 │
│  ├─ Company field (optional)        │
│  └─ [Register] button               │
└────────┬────────────────────────────┘
         │ User fills form & submits
         ▼
┌──────────────────────────────────────────────┐
│  Frontend Validation                         │
│  ├─ Email format valid?                      │
│  ├─ Password >= 8 chars?                     │
│  ├─ Password has uppercase?                  │
│  ├─ Password has number?                     │
│  ├─ First Name not empty?                    │
│  └─ Last Name not empty?                     │
└────────┬─────────────────────────────────────┘
         │ ✅ All valid
         ▼
┌────────────────────────────────────────────────────┐
│  API Request                                       │
│  POST /api/v1/auth/register                       │
│  Content-Type: application/json                    │
│                                                    │
│  {                                                 │
│    "email": "user@example.com",                   │
│    "password": "SecurePass123",                   │
│    "firstName": "John",                           │
│    "lastName": "Doe",                             │
│    "company": "Acme Corp"                         │
│  }                                                │
└────────┬───────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────┐
│  Backend - Server-Side Validation                  │
│  ├─ Email format valid?                            │
│  ├─ Email not already registered?                  │
│  ├─ Password meets requirements?                   │
│  ├─ All required fields present?                   │
│  └─ Input sanitized (no SQL injection)?            │
└────────┬───────────────────────────────────────────┘
         │ ✅ All validations pass
         ▼
┌────────────────────────────────────────────────────┐
│  Password Processing                               │
│  ├─ Hash password with bcrypt                      │
│  ├─ Generate salt                                  │
│  ├─ Create password hash                           │
│  └─ Store hash (NOT plain password)                │
└────────┬───────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────┐
│  Create User Record in Cosmos DB                   │
│  {                                                 │
│    "id": "uuid-generated",                        │
│    "email": "user@example.com",                   │
│    "passwordHash": "$2b$12$abcd...",              │
│    "firstName": "John",                           │
│    "lastName": "Doe",                             │
│    "company": "Acme Corp",                        │
│    "createdAt": "2026-01-18T08:00:00Z",          │
│    "verified": false,                             │
│    "lastLogin": null,                             │
│    "status": "active"                             │
│  }                                                │
└────────┬───────────────────────────────────────────┘
         │ ✅ User created successfully
         ▼
┌────────────────────────────────────────────────────┐
│  Generate JWT Token                                │
│  Payload:                                          │
│  {                                                 │
│    "sub": "user-id",                              │
│    "email": "user@example.com",                   │
│    "iat": 1705570800,                             │
│    "exp": 1705657200                              │
│  }                                                │
│  Signed with secret key                           │
└────────┬───────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────┐
│  API Response (201 Created)                        │
│  {                                                 │
│    "id": "uuid-generated",                        │
│    "email": "user@example.com",                   │
│    "firstName": "John",                           │
│    "lastName": "Doe",                             │
│    "company": "Acme Corp",                        │
│    "createdAt": "2026-01-18T08:00:00Z",          │
│    "access_token": "eyJhbGc...",                  │
│    "token_type": "bearer"                         │
│  }                                                │
└────────┬───────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────┐
│  Frontend - Store Token                            │
│  ├─ Store in localStorage/sessionStorage           │
│  ├─ Set Authorization header for future calls      │
│  └─ Show success message                           │
└────────┬───────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────┐
│  Redirect User                                     │
│  ├─ Clear registration form                        │
│  ├─ Redirect to dashboard                          │
│  └─ Display welcome message                        │
└────────────────────────────────────────────────────┘
         │
         ▼
     ✅ REGISTRATION COMPLETE
```

### 1.2 Happy Path Data Flow

```
USER INPUT (Frontend)
    ↓
FRONTEND VALIDATION
    ↓
API REQUEST (HTTP POST)
    ↓
BACKEND VALIDATION
    ↓
PASSWORD HASHING (bcrypt)
    ↓
COSMOS DB INSERT
    ↓
JWT TOKEN GENERATION
    ↓
API RESPONSE (201)
    ↓
STORE TOKEN (Frontend)
    ↓
REDIRECT TO DASHBOARD
    ↓
✅ SUCCESS
```

---

## 2. Error Scenarios

### 2.1 Invalid Email Format

```
User Input: "invalidemail"
              ↓
Frontend Validation: ❌ Invalid email format
              ↓
Show Error: "Please enter a valid email address"
              ↓
Prevent API call
              ↓
User corrects and retries
```

**Frontend Validation Rule:**
```javascript
/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
```

**Response:** ❌ 422 Unprocessable Entity (if submitted)

---

### 2.2 Weak Password

```
User Input: Password = "weak"
              ↓
Frontend Validation: ❌ Too short (< 8 characters)
              ↓
Show Error: "Password must be at least 8 characters"
              ↓
Frontend also checks:
  ├─ Must have uppercase letter
  ├─ Must have number
  └─ Must have special character (optional)
              ↓
Prevent API call
```

**Password Requirements:**
- ✅ Minimum 8 characters
- ✅ At least 1 uppercase letter (A-Z)
- ✅ At least 1 number (0-9)
- ✅ At least 1 special character (optional but recommended)

**Examples:**
- ❌ "password" - no uppercase, no number
- ❌ "Password" - no number
- ❌ "Password1" - ✅ VALID
- ✅ "P@ssw0rd" - STRONG

---

### 2.3 Email Already Registered

```
User Input: email = "existing@example.com"
              ↓
Frontend: Passes validation ✅
              ↓
API Request: POST /auth/register
              ↓
Backend Query: SELECT * FROM users WHERE email = ?
              ↓
Result: User already exists ❌
              ↓
Backend Response: 409 Conflict
{
  "detail": "Email already registered",
  "code": "EMAIL_EXISTS"
}
              ↓
Frontend: Show error message
"This email is already registered. Try logging in instead."
              ↓
Provide link to login page
```

**Status Code:** `409 Conflict`

**Error Message:** `"Email already registered"`

---

### 2.4 Missing Required Field

```
User Input: First Name left empty
              ↓
Frontend Validation: ❌ Required field
              ↓
Show Error: "First Name is required"
              ↓
Prevent form submission
              ↓
OR
              ↓
Backend receives incomplete data
              ↓
Backend Validation: ❌ Missing firstName
              ↓
Response: 422 Unprocessable Entity
{
  "detail": "Missing required field: firstName"
}
```

**Required Fields:**
- ✅ email
- ✅ password
- ✅ firstName
- ✅ lastName
- ⭕ company (optional)

---

### 2.5 Server Error During Registration

```
User Input: Valid data, all checks pass ✅
              ↓
API Request: Sent successfully
              ↓
Backend: Password hashing ✅
              ↓
Backend: Database insert fails ❌
              (Connection timeout, duplicate key, etc.)
              ↓
Response: 500 Internal Server Error
{
  "detail": "An error occurred while creating user account"
}
              ↓
Frontend: Show generic error
"Registration failed. Please try again."
              ↓
Log error to server logs
              ↓
Admin notified (optional)
              ↓
User can retry
```

**Status Code:** `500 Internal Server Error`

---

## 3. Edge Cases & Special Scenarios

### 3.1 Slow Network - Duplicate Submit

```
User submits form (network is slow)
              ↓
(No response for 5 seconds)
              ↓
User clicks submit again ❌
              ↓
Two API requests sent simultaneously
              ↓
Both reach backend
              ↓
Backend creates 2 users?
              ↓
MITIGATION:
  ├─ Disable button after first click ✅
  ├─ Add "registering..." indicator
  └─ Database unique constraint on email ✅
```

**Solution Implemented:**
- Frontend: Disable [Register] button while request in progress
- Backend: Database unique index on email prevents duplicates
- User sees: "Creating account..." spinner

---

### 3.2 Special Characters in Email

```
User Input: test+tag@example.com
              ↓
Frontend: Email validation passes ✅
              ↓
Backend: Email validation passes ✅
              ↓
Database: Stored as-is ✅
              ↓
Login: Uses exact email match ✅
              ↓
✅ Valid email accepted
```

**Special Cases:**
- ✅ `user+tag@example.com` - Plus addressing
- ✅ `user.name@example.com` - Dot in local part
- ✅ `user_name@example.com` - Underscore
- ❌ `user@example..com` - Double dots
- ❌ `@example.com` - No local part
- ❌ `user@` - No domain

---

### 3.3 Case Sensitivity in Email

```
User 1 Registration: Test@Example.com
              ↓
Email lowercased: test@example.com ✅
              ↓
Stored in DB: test@example.com
              ↓
User 2 Registration: test@EXAMPLE.COM
              ↓
Email lowercased: test@example.com
              ↓
Database check: Already exists ✅
              ↓
Response: 409 Conflict - Email already registered
```

**Implementation:**
- Email normalized to lowercase before storage
- Email comparison case-insensitive
- Prevents duplicate accounts with different cases

---

### 3.4 Very Long Input

```
User Input: 
  firstName = "A" (repeated 1000 times)
  email = "a@b.com" (repeated 100 times)
              ↓
Frontend: Input field max-length enforced ✅
  ├─ firstName: max 50 characters
  ├─ lastName: max 50 characters
  ├─ email: max 254 characters
  └─ company: max 100 characters
              ↓
User can't enter more than limit
              ↓
Database validation: Additional check ✅
              ↓
✅ Protected against buffer overflow
```

**Field Length Limits:**
- firstName: max 50 chars
- lastName: max 50 chars
- email: max 254 chars (RFC standard)
- company: max 100 chars
- password: max 128 chars (hashed to 60)

---

## 4. Security Scenarios

### 4.1 SQL Injection Attempt

```
User Input (in email):
  " OR 1=1 --"
              ↓
Frontend: Email validation rejects ❌
  (Invalid format)
              ↓
If bypassed and reaches backend:
  ↓
Database Query (parameterized):
  SELECT * FROM users WHERE email = @email
              ↓
Parameter binding prevents injection ✅
  email = " OR 1=1 --"  (treated as literal string)
              ↓
No match found
              ↓
Registration proceeds normally
              ↓
✅ Protected against SQL injection
```

**Implementation:**
- Parameterized queries (ORM)
- Input validation
- No string concatenation in SQL

---

### 4.2 Password Verification

```
User Registration:
  password = "MyP@ss123"
              ↓
Backend Hashing:
  ├─ Generate salt
  ├─ Hash: bcrypt(password, salt)
  └─ Result: $2b$12$N9qo8uLO...
              ↓
Store in DB: passwordHash (NOT password)
              ↓
Later - User Login:
  ├─ User enters: "MyP@ss123"
  ├─ Hash entered password with stored salt
  ├─ Compare: bcrypt(input) == stored hash?
  └─ ✅ Match = valid password
              ↓
❌ If user enters "MyPassword123" - No match
              ↓
✅ Protected against password exposure
```

**Password Security:**
- Never store plain passwords ✅
- Use bcrypt with salt ✅
- Hashes are one-way (irreversible) ✅
- Each password has unique salt ✅

---

### 4.3 Token After Registration

```
User Registration Successful:
  ↓
Backend Issues JWT Token:
  Header: { alg: "HS256", typ: "JWT" }
  Payload: { sub: user-id, email: email, exp: ... }
  Signature: HMAC-SHA256(secret)
              ↓
Frontend Stores Token:
  localStorage.setItem('auth_token', token)
              ↓
Subsequent Requests:
  Authorization: Bearer eyJhbGc...
              ↓
Backend Validates Token:
  ├─ Signature valid? (using secret)
  ├─ Expired? (check exp timestamp)
  ├─ User still exists?
  └─ ✅ All checks pass
              ↓
Request allowed with user context
              ↓
❌ If token tampered: Signature invalid
              ↓
✅ Protected against token forgery
```

**Token Security:**
- Cryptographically signed ✅
- Expiration time included ✅
- Secret key protects from tampering ✅
- Verified on every API call ✅

---

## 5. Test Scenarios - Executive Summary

| Scenario | Input | Expected | Status |
|----------|-------|----------|--------|
| **Happy Path** | Valid data | 201, user created, token issued | ⏳ To Test |
| **Invalid Email** | "notanemail" | 422, email validation error | ⏳ To Test |
| **Weak Password** | "weak" | 422, password validation error | ⏳ To Test |
| **Email Exists** | existing@ex.com | 409, conflict error | ⏳ To Test |
| **Missing Field** | No firstName | 422, required field error | ⏳ To Test |
| **SQL Injection** | " OR 1=1 --" | 422, rejected | ⏳ To Test |
| **Special Chars** | test+tag@ex.com | 201, accepted | ⏳ To Test |
| **Case Insensitive** | Test@EX.com | 409, duplicate | ⏳ To Test |
| **Long Input** | 1000 char firstName | Truncated/rejected | ⏳ To Test |
| **Server Error** | Valid data, DB fails | 500, error logged | ⏳ To Test |

---

## 6. Registration Flow - API Contract

### 6.1 Request Specification

```http
POST /api/v1/auth/register HTTP/1.1
Host: kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io
Content-Type: application/json

{
  "email": "john.doe@example.com",
  "password": "SecureP@ss123",
  "firstName": "John",
  "lastName": "Doe",
  "company": "Acme Corporation"
}
```

**Field Validations:**
- email: Valid email format, max 254 chars, must be unique
- password: Min 8 chars, at least 1 uppercase, 1 number
- firstName: Required, max 50 chars, no special chars
- lastName: Required, max 50 chars, no special chars
- company: Optional, max 100 chars

---

### 6.2 Success Response (201)

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "email": "john.doe@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "company": "Acme Corporation",
  "createdAt": "2026-01-18T08:30:00Z",
  "verified": false,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmNDdhYzEwYi01OGNjLTQzNzItYTU2Ny0wZTAyYjJjM2Q0NzkiLCJlbWFpbCI6ImpvaG4uZG9lQGV4YW1wbGUuY29tIiwiaWF0IjoxNzA1NTcwNjAwLCJleHAiOjE3MDU2NTcwMDB9.signature",
  "token_type": "bearer"
}
```

---

### 6.3 Error Responses

**422 Unprocessable Entity - Invalid Email**
```json
{
  "detail": "Invalid email format",
  "code": "INVALID_EMAIL"
}
```

**422 Unprocessable Entity - Weak Password**
```json
{
  "detail": "Password must contain at least one uppercase letter, one number, and be at least 8 characters long",
  "code": "WEAK_PASSWORD"
}
```

**409 Conflict - Email Exists**
```json
{
  "detail": "Email already registered",
  "code": "EMAIL_EXISTS"
}
```

**422 Unprocessable Entity - Missing Field**
```json
{
  "detail": "Missing required field: firstName",
  "code": "MISSING_FIELD"
}
```

**500 Internal Server Error**
```json
{
  "detail": "An error occurred while processing your request",
  "code": "INTERNAL_SERVER_ERROR"
}
```

---

## 7. State Transitions

```
┌─────────────┐
│   Unknown   │
│    User     │
└──────┬──────┘
       │ Clicks Register
       │ Fills Form
       │ Submits
       ▼
┌─────────────────┐
│  Registering... │ (Loading state)
└────────┬────────┘
         │
         ├─ Validation Error? → Show error, stay on form
         │
         ├─ Email exists? → Show error, suggest login
         │
         └─ Success? → Create user
                       │
                       ▼
            ┌──────────────────┐
            │  Registered      │
            │  (Not Verified)  │ (if email verification enabled)
            │                  │
            │  OR              │
            │                  │
            │  Registered      │
            │  (Verified) ✅   │ (immediate verification)
            └──────────┬───────┘
                       │
                       │ Redirect with token
                       │
                       ▼
            ┌──────────────────┐
            │   Authenticated  │
            │   (Logged In)    │
            │                  │
            │   Can access:    │
            │   ├─ Dashboard   │
            │   ├─ Profile     │
            │   └─ API calls   │
            └──────────────────┘
```

---

## 8. Testing Checklist for Phase 2

### Frontend Tests
- [ ] Registration form loads
- [ ] Email field validation works
- [ ] Password field validation works
- [ ] Required field validation works
- [ ] Form submission triggers API call
- [ ] Loading indicator shows during request
- [ ] Success message displays
- [ ] Redirect to dashboard on success
- [ ] Error messages display properly
- [ ] Form clears on successful registration

### API Tests
- [ ] POST /auth/register with valid data returns 201
- [ ] POST /auth/register with invalid email returns 422
- [ ] POST /auth/register with weak password returns 422
- [ ] POST /auth/register with duplicate email returns 409
- [ ] POST /auth/register with missing field returns 422
- [ ] Response includes JWT token
- [ ] Token is valid and can be used for API calls
- [ ] Password is hashed (not stored plain)

### Database Tests
- [ ] User record created in Cosmos DB
- [ ] Email is unique (no duplicates)
- [ ] Password field is hashed (bcrypt)
- [ ] User metadata (firstName, lastName, company) stored correctly
- [ ] createdAt timestamp recorded
- [ ] Default fields (verified, status) set correctly

### Security Tests
- [ ] SQL injection attempt rejected
- [ ] XSS attempt rejected
- [ ] CSRF protection working
- [ ] Password not returned in responses
- [ ] Token includes expiration
- [ ] Token cannot be forged without secret

---

## 9. Monitoring & Logging

### Metrics to Track
- Total registrations per day
- Failed registration attempts
- Most common validation errors
- Average registration completion time
- Registration to first login time

### Logs to Monitor
- Every registration request (email, timestamp)
- Every failed registration (reason, timestamp)
- Every password hash operation
- Every database insert
- Every token generation

---

## Summary

**User Registration** is a critical user flow with multiple success and error paths. This scenario map covers:

✅ Happy path (successful registration)  
✅ All validation error scenarios  
✅ Edge cases and special characters  
✅ Security protections  
✅ API contract specifications  
✅ Testing checklist  

**Ready to test:** Proceed with Phase 2 manual or automated tests
