# User Authentication Flow Diagrams

## 1. Complete Registration → Login → Dashboard Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      START: Login Page                          │
│                                                                 │
│  ┌─ Sign In ───────────────────────────────┐                  │
│  │                                         │                  │
│  │  Email: ________________                │                  │
│  │  Password: ________________             │                  │
│  │                                         │                  │
│  │  [Sign In]  Don't have account? Reg.   │                  │
│  └─────────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
   [Sign In]                  [Register]
        │                         │
        │          ┌──────────────┴──────────────┐
        │          │                             │
        │          ▼                             ▼
        │    ┌──────────────────────┐    ┌──────────────────────┐
        │    │ Registration Form    │    │ Registration Success │
        │    │                      │    │                      │
        │    │ Email: ___           │    │ ✓ Success!           │
        │    │ Password: ___        │    │                      │
        │    │ Name: ___            │    │ Email: newuser@e...  │
        │    │ ☑ Terms             │    │                      │
        │    │ ☑ Privacy           │    │ [Go to Login]        │
        │    │                      │    │                      │
        │    │ [Create Account]     │    └──────────┬───────────┘
        │    └──────────┬───────────┘               │
        │               │                           │
        │               └───────────────────────────┘
        │                           │
        ▼                           ▼
   ┌─────────────────────────────────────┐
   │  Backend: POST /api/v1/auth/login   │
   │  Backend: POST /api/v1/auth/register│
   │                                     │
   │  1. Verify credentials              │
   │  2. Check password (bcrypt)         │
   │  3. Generate JWT tokens             │
   │  4. Return {access, refresh, ...}   │
   └──────────────────┬──────────────────┘
                      │
                      ▼
   ┌─────────────────────────────────────┐
   │  Frontend: Store Tokens             │
   │                                     │
   │  localStorage.accessToken = ...     │
   │  localStorage.refreshToken = ...    │
   │  localStorage.expiresAt = ...       │
   │  setIsAuthenticated(true)           │
   └──────────────────┬──────────────────┘
                      │
                      ▼
   ┌─────────────────────────────────────┐
   │  Dashboard Page                     │
   │                                     │
   │  ┌─────────────────────────────┐   │
   │  │ Docs & Procurement [Logout] │   │
   │  ├─────────────────────────────┤   │
   │  │ Upload Document             │   │
   │  │                             │   │
   │  │ Your Documents              │   │
   │  │ [empty]                     │   │
   │  └─────────────────────────────┘   │
   │                                     │
   │  ✅ Protected Route Accessed        │
   └──────────────────┬──────────────────┘
                      │
                 [Click Logout]
                      │
                      ▼
   ┌─────────────────────────────────────┐
   │  Frontend: logout()                 │
   │                                     │
   │  localStorage.removeItem(...)       │
   │  setIsAuthenticated(false)          │
   │  navigate('/login')                 │
   └──────────────────┬──────────────────┘
                      │
                      ▼
   ┌─────────────────────────────────────┐
   │  Back to Login Page                 │
   │  (Start Over)                       │
   └─────────────────────────────────────┘
```

---

## 2. Login Request/Response Flow

```
CLIENT                          SERVER
  │                               │
  │  POST /api/v1/auth/login      │
  │  {                            │
  │    "email": "user@e...",      │
  │    "password": "Pass..."      │
  │  }                            │
  ├──────────────────────────────>│
  │                               │
  │                         ┌─────┴──────┐
  │                         │ Processing:│
  │                         │ 1. Find    │
  │                         │    user    │
  │                         │ 2. Verify  │
  │                         │    pwd     │
  │                         │ 3. Gen JWT │
  │                         └─────┬──────┘
  │                               │
  │  200 OK {                     │
  │    "accessToken": "...",      │
  │    "refreshToken": "...",     │
  │    "expires_in": 3600,        │
  │    "token_type": "bearer"     │
  │  }                            │
  │<──────────────────────────────┤
  │                               │
  ├─ Store in localStorage ──────>│
  │                               │
  ├─ Add to headers ─────────────>│
  │                               │
  │  GET /api/v1/auth/profile     │
  │  Headers: {                   │
  │    "Authorization":           │
  │      "Bearer eyJh..."         │
  │  }                            │
  ├──────────────────────────────>│
  │                               │
  │                         ┌─────┴──────┐
  │                         │ Verify JWT │
  │                         │ Get user   │
  │                         └─────┬──────┘
  │                               │
  │  200 OK {                     │
  │    "user_id": "...",          │
  │    "email": "...",            │
  │    "created_at": "..."        │
  │  }                            │
  │<──────────────────────────────┤
  │                               │
```

---

## 3. Token Lifecycle

```
    ┌──────────────────────────────────────┐
    │  Immediate After Login               │
    │                                      │
    │  accessToken:  {valid until +60min}  │
    │  refreshToken: {valid until +7 days}│
    └────────────┬─────────────────────────┘
                 │
           [Use Access Token]
                 │
                 │ ┌──────────────────────┐
                 ├─→ API Calls OK         │
                 │ └──────────────────────┘
                 │
         ┌───────┴──────────┐
         │                  │
    +30 min            +60 min
         │                  │
    ┌────┴────┐     ┌───────┴──────────┐
    │ Still   │     │ Token Expired!   │
    │ Valid   │     │ (401 Response)   │
    │ ✓ OK    │     │ 
    └─────────┘     │ Interceptor:
                    │ Send refreshToken
                    │ Get new accessToken
                    │ Retry request
                    └─────────────────────┐
                                          │
                                    [Success]
                                          │
                                    Continue...
                                          │
         [+7 days from login]
                 │
    ┌────────────┴──────────────┐
    │ Refresh Token Expires!    │
    │ Cannot refresh anymore    │
    │ User must login again     │
    └───────────────────────────┘
```

---

## 4. Error Handling Paths

```
Login Form Submission
        │
        ▼
┌───────────────────┐
│ Valid Credentials?│
└────┬────────┬────┘
     │        │
    YES      NO
     │        │
     ▼        ▼
  Success  ┌─────────────────────┐
     │     │ Invalid Credentials │
     │     │ Error Message:      │
     │     │ "Invalid email or   │
     │     │  password"          │
     │     └──────────┬──────────┘
     │                │
     ▼                ▼
┌──────────────┐  ┌─────────────────┐
│ Store Tokens │  │ Stay on Login   │
│ Set Auth=T   │  │ No Tokens Stored│
│ Navigate to  │  │ Clear Error on  │
│ Dashboard    │  │ Next Attempt    │
└──────────┬───┘  └─────────────────┘
           │
           ▼
    ┌────────────────┐
    │ Dashboard Load │
    │ Validate Token │
    └────┬───────┬───┘
         │       │
       Valid   Expired
         │       │
         ▼       ▼
      Success ┌──────────────┐
             │ Refresh Token│
             │ Get New      │
             │ Access Token │
             └──────┬───────┘
                    │
              ┌─────┴─────┐
              │           │
            OK      ┌─────┴─────┐
              │     │ Refresh   │
              │     │ Token Too │
              │     │ Old -     │
              │     │ Logout    │
              │     │ Redirect  │
              ▼     │ to Login  │
         Continue   └───────────┘
```

---

## 5. Authentication State Machine

```
                    ┌─────────────┐
                    │  Initial    │
                    │ (Not Logged)│
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
        [Register]              [Login with Credentials]
              │                         │
              ▼                         ▼
      ┌───────────────┐        ┌──────────────┐
      │ Registration  │        │   Login      │
      │ Success       │        │   Success    │
      └───────┬───────┘        └──────┬───────┘
              │                       │
              └───────────┬───────────┘
                          │
                          ▼
             ┌────────────────────────┐
             │   Authenticated ✅      │
             │                        │
             │  isAuthenticated=true  │
             │  accessToken stored    │
             │  refreshToken stored   │
             └────────┬─────────────┬─┘
                      │             │
              [Load Dashboard]      │
                      │             │
              [Make API Calls       │
               w/ Bearer Token]     │
                      │             │
                      ├─ Token     │
                      │ Expires    │
                      │            │
                      ▼            │
              ┌──────────────┐     │
              │ Refresh Token│     │
              │ Auto-refresh │     │
              │ access token │     │
              └──────┬───────┘     │
                     │             │
                   [OK]       [Click Logout]
                     │             │
                     └─────┬───────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │  Logout            │
                  │  Clear Tokens      │
                  │  isAuth=false      │
                  └────────┬───────────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │  Not Authenticated │
                  │  Back to Login     │
                  └────────────────────┘
```

---

## 6. Session Timeline

```
T+0min  │ User logs in
        │ ├─ accessToken issued (60 min validity)
        │ └─ refreshToken issued (7 day validity)
        │
T+30min │ ✅ Access token still valid
        │ └─ All API calls work normally
        │
T+55min │ ✅ Access token still valid (5 min left)
        │
T+60min │ ❌ Access token EXPIRED
        │ ├─ Next API call returns 401
        │ ├─ Frontend interceptor catches 401
        │ ├─ Sends refreshToken to backend
        │ ├─ Backend validates refreshToken
        │ ├─ Issues new accessToken (another 60 min)
        │ ├─ Original API call retried
        │ └─ User doesn't notice anything!
        │
T+1hr   │ ✅ Fresh access token now valid
T+2hr   │ (until T+2hr from initial login)
T+3hr   │
...
T+7d    │ ❌ Refresh token EXPIRED
        │ ├─ Cannot refresh anymore
        │ ├─ User must login again
        │ └─ Redirected to /login
```

---

## 7. Protected Route Guard

```
User Navigates to /dashboard
        │
        ▼
┌──────────────────────┐
│ Dashboard.tsx        │
│ useEffect            │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Check:               │
│ if (!isAuthenticated)│
└────────┬─────────────┘
         │
    ┌────┴─────┐
    │           │
   YES         NO
    │           │
    ▼           ▼
┌──────────┐ ┌────────────────┐
│ Redirect │ │ Load Page      │
│ to /login│ │ Fetch data     │
│          │ │ Display        │
└──────────┘ │ dashboard      │
             └────────────────┘
```

---

## Summary

These diagrams show:

1. **Complete User Journey**: Registration → Login → Dashboard → Logout
2. **Request/Response Flow**: Client-server interaction
3. **Token Lifecycle**: When tokens are valid and what happens on expiration
4. **Error Handling**: What happens on invalid credentials
5. **State Machine**: Authentication states and transitions
6. **Session Timeline**: Token validity over time
7. **Protected Routes**: How dashboard guards against unauthenticated access

All flows are implemented and tested in the current system. ✅
