# ✅ STATIC WEB APP DEPLOYMENT - FINAL CONFIGURATION

**Date:** January 18, 2026  
**Status:** 🟢 SWA Created and Ready  
**Next:** Add environment variables and verify

---

## Quick Start

### 1️⃣ Add Environment Variable (2 minutes)

**Via Azure Portal (Easiest):**
```
Portal → Static Web App → Configuration → + Add
Name: VITE_API_URL
Value: https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1
Click: Save
```

**Via CLI:**
```powershell
az staticwebapp appsettings set `
  --name kraftdintel-web `
  --resource-group kraftdintel-rg `
  --setting-names VITE_API_URL="https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1"
```

### 2️⃣ Monitor Build (3-5 minutes)
- GitHub → Actions → Wait for build to complete
- Expected status: ✅ Success (green checkmark)

### 3️⃣ Test Frontend (2 minutes)
1. Open SWA URL in browser (get from Portal)
2. Should see login page
3. Try to register new account
4. Login should work
5. Dashboard should display

### 4️⃣ Full Smoke Tests (5 minutes)
Follow comprehensive test plan below

---

## SWA Information

```
Name:            kraftdintel-web
Resource Group:  kraftdintel-rg
Status:          ✅ Created & Ready
URL:             Get from Azure Portal → Overview
Build Preset:    Vite
App Location:    /frontend
Output Location: /dist
Branch:          main
Repository:      github.com/Knotcreativ/kraftd
```

**To find SWA URL:**
1. Azure Portal → Static Web Apps → kraftdintel-web
2. Click "Overview"
3. Copy "URL" field (format: `https://NAME-XXXXX.azurestaticapps.net`)

---

## Environment Variables to Add

| Name | Value | Purpose |
|------|-------|---------|
| `VITE_API_URL` | `https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1` | Backend API endpoint |

These are read by frontend at build time via Vite.

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────┐
│          Kraftd MVP Production Deployment       │
├─────────────────────────────────────────────────┤
│                                                 │
│  Frontend (Static Web App - West Europe)        │
│  ├─ URL: https://kraftdintel-web...            │
│  ├─ Build: Vite (React + TypeScript)           │
│  ├─ Hosting: Azure Static Web Apps (Free)      │
│  └─ CI/CD: GitHub Actions (auto-deploy)        │
│                                                 │
│  ↓ HTTPS/API Gateway ↓                         │
│                                                 │
│  Backend API (Container Apps - UAE North)      │
│  ├─ URL: https://kraftdintel-app...            │
│  ├─ Runtime: Python 3.11 + FastAPI            │
│  ├─ Compute: Container Apps (Autoscale)       │
│  └─ Health: /health endpoint (GET)             │
│                                                 │
│  ↓ Database Connection ↓                       │
│                                                 │
│  Database (Cosmos DB - UAE North)              │
│  ├─ Collections: Users, Documents, Workflows   │
│  ├─ Throughput: Auto-scale (400-4000 RU/s)   │
│  └─ Access: API authentication via JWT         │
│                                                 │
│  Monitoring (Application Insights)             │
│  ├─ Logs: All API calls, errors                │
│  ├─ Metrics: Response time, throughput         │
│  └─ Alerts: Failed requests, high latency      │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Comprehensive Smoke Tests

### Test 1: Frontend Loads ✅
```bash
# Check frontend is accessible
curl -I https://[swa-url]/
# Expected: HTTP 200 (or 301 redirect to /login)
```

Steps:
1. Open SWA URL in browser
2. Page should load in < 2 seconds
3. Should see Kraftd login page
4. Check browser console (F12) - no errors
5. All images/CSS loaded

**Acceptance:** ✅ Page loads, no 404 or errors

---

### Test 2: Register New Account ✅

Steps:
1. Click "Register" or "Sign Up" button
2. Fill in form:
   - Email: `test-user-001@kraft.test`
   - Password: `TestPass123!@`
   - Confirm Password: `TestPass123!@`
3. Click "Create Account" or "Register"
4. Expected: Success message or redirect to login

**Acceptance:** ✅ Account created, can login

**Failure diagnosis:**
- Error message should appear
- Check browser console (F12) → Network tab
- Look for API error responses
- Common errors: "Email already registered", "Password too weak"

---

### Test 3: Login ✅

Steps:
1. Use credentials from Test 2
2. Email: `test-user-001@kraft.test`
3. Password: `TestPass123!@`
4. Click "Login" or "Sign In"
5. Expected: Redirect to dashboard

**Acceptance:** ✅ Login succeeds, JWT token stored

**Check token storage:**
```javascript
// In browser console (F12):
localStorage.getItem('token')  // Should show JWT
localStorage.getItem('user')   // Should show user info
```

---

### Test 4: Dashboard Loads ✅

After successful login:

Steps:
1. Page should redirect to dashboard
2. Expected elements:
   - User greeting (Hello, Test User)
   - Document list (empty initially)
   - "Upload Document" button
   - Navigation menu
3. Check console for API calls (F12 → Network)
4. Should see GET request to `/api/v1/documents` (HTTP 200)

**Acceptance:** ✅ Dashboard displays with no API errors

---

### Test 5: Backend Health Check ✅

```bash
# Test backend is alive
curl https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1/health

# Expected response (HTTP 200):
# {"status": "healthy", "version": "1.0"}
```

If fails:
- Backend API may be restarting
- Wait 1-2 minutes
- Try again
- Check Application Insights logs

---

### Test 6: Document Upload ✅

Steps:
1. Click "Upload Document" button
2. Select test PDF file (< 25MB, any size works)
3. Click "Upload" or "Choose File" then "Submit"
4. Expected:
   - Upload progress shows
   - File appears in document list
   - Status shows "pending" or "uploaded"
   - No error messages

**File size validation:**
- ✅ < 25MB: Upload succeeds (HTTP 201)
- ❌ > 25MB: Upload rejected (HTTP 413 "Payload Too Large")
- ❌ Invalid type (.exe, .zip): Rejected (HTTP 400 "Unsupported format")

**Acceptance:** ✅ File uploads, appears in list, status pending

---

### Test 7: Document Processing ✅

Steps:
1. After upload, click "Process" or "Analyze" on document
2. Expected:
   - Status changes to "processing"
   - Progress bar appears
   - "X% complete" updates
   - Takes 1-3 minutes for RFQ documents
3. When complete:
   - Status changes to "completed"
   - ✅ Completeness score displays (0-100%)
   - Can click to view extracted data

**For faster testing:**
- Use small PDF (1-2 pages)
- Simple documents process faster
- Complex RFQs take longer

**Acceptance:** ✅ Processing starts, completes, score displays

---

### Test 8: Export/Download ✅

Steps:
1. On completed document, click "Export" or "Download"
2. Select format from dropdown:
   - PDF
   - Excel (XLSX)
   - JSON
   - Structured Data
   - Summary
3. Click "Export" or "Download"
4. Expected:
   - File downloads to Downloads folder
   - Correct file type
   - Data is complete (not empty)

**Acceptance:** ✅ File downloads in selected format

---

### Test 9: Logout ✅

Steps:
1. Click "Logout" or "Sign Out"
2. Expected:
   - Redirect to login page
   - Token cleared from localStorage
   - Cannot access dashboard without re-login

**Acceptance:** ✅ Session ends, token cleared

---

### Test 10: API Performance ✅

Open browser DevTools (F12) → Network tab, then:

1. Login - should complete in < 1 second
2. Load dashboard - should complete in < 2 seconds
3. Upload file (10MB) - should complete in < 10 seconds
4. Process document - should start within < 5 seconds

**Performance targets:**
| Operation | Target | Max |
|-----------|--------|-----|
| Login | 500ms | 2s |
| Dashboard load | 1000ms | 3s |
| Upload (10MB) | 5s | 15s |
| Process start | 2s | 5s |
| Completeness calc | 180s | 300s |

If slower, check:
- Network tab for slow requests
- Application Insights logs
- Browser DevTools Performance tab

---

## Monitoring & Logs

### View Application Insights Logs

1. Azure Portal → Search "Application Insights"
2. Select: `kraftdintel-app` (not the web app)
3. Click "Logs" (Kusto Query Language)
4. Use queries:

```kusto
// All requests
requests | order by timestamp desc

// Only errors
requests | where success == false | order by timestamp desc

// API response times
requests | where name contains "api" | project timestamp, name, duration, success

// Exception logs
exceptions | order by timestamp desc
```

### View SWA Build Logs

1. GitHub → Knotcreativ/kraftd → Actions
2. Click latest workflow run
3. Click "Build and deploy" job
4. View logs for build errors
5. Common issues:
   - Missing environment variables
   - TypeScript errors
   - Missing npm packages

---

## Common Issues & Solutions

### ❌ Frontend shows 404
```
Issue: Page not found
Causes: 
  - SWA not fully deployed
  - Wrong URL
  - Build failed
Solution:
  - Check SWA status in Portal (should be "Ready")
  - Wait 5 more minutes
  - Clear cache (Ctrl+Shift+Delete)
  - Check GitHub Actions for build errors
```

### ❌ Cannot connect to API
```
Issue: Network error, API returns 500, CORS error
Causes:
  - VITE_API_URL not set
  - Backend API down
  - CORS not configured
Solution:
  - Add VITE_API_URL env var to SWA
  - Wait for GitHub build to complete
  - Check backend health: /health endpoint
  - Check Application Insights for errors
```

### ❌ Registration fails
```
Issue: "Email already exists" or "Invalid request"
Causes:
  - Email format invalid
  - Password requirements not met
  - Database connection issue
  - User already registered
Solution:
  - Use valid email (test@kraft.test)
  - Password: Min 8 chars, 1 upper, 1 number, 1 special
  - Try different email
  - Check DB connection in logs
```

### ❌ Upload rejected
```
Issue: "File too large" or "Unsupported format"
Causes:
  - File > 25MB (new limit)
  - File type not supported (.exe, .zip, etc.)
  - File corrupted
Solution:
  - Use file < 25MB
  - Supported: PDF, DOCX, XLSX, PPTX, TXT, etc.
  - Try different file
  - Check error message in console
```

### ❌ Processing never starts
```
Issue: Document stays "pending" forever
Causes:
  - Processing container not running
  - Invalid document format
  - Processing queue full
Solution:
  - Wait 2-3 minutes
  - Try different document
  - Check Application Insights logs
  - Restart backend container if needed
```

---

## Deployment Complete Checklist

### Before Going Live
- [ ] VITE_API_URL environment variable added to SWA
- [ ] GitHub Actions build completed successfully (green ✅)
- [ ] Frontend loads without errors
- [ ] Backend health check passes
- [ ] All 10 smoke tests pass

### Post-Deployment (Ongoing)
- [ ] Monitor Application Insights daily
- [ ] Check for errors in logs
- [ ] Review performance metrics
- [ ] Test API health endpoint weekly
- [ ] Backup Cosmos DB (automated)
- [ ] Review container logs for warnings

### Team Communication
- [ ] Notify team Kraftd MVP is live
- [ ] Share SWA URL with users
- [ ] Share test account credentials
- [ ] Document known issues
- [ ] Provide support contact

---

## Summary

✅ **What's Done:**
- Backend API: Live
- Database: Ready
- Frontend: Built
- Static Web App: Created

⏳ **What's Left:**
1. Add VITE_API_URL env var (2 min)
2. Wait for GitHub build (5 min)
3. Run smoke tests (10 min)

🎯 **Total Time:** ~15-20 minutes to production ready

---

**Status:** 🟢 **READY FOR FINAL CONFIGURATION**

Proceed with adding environment variables to complete deployment.
