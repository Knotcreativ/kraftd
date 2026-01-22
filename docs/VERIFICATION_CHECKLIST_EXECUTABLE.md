# ✅ DEPLOYMENT VERIFICATION CHECKLIST & EXECUTION LOG
**Date:** January 18, 2026  
**Project:** KraftdIntel  
**Status:** In Progress - Configuration Verification Phase

---

## 📋 PHASE 1: CONFIGURATION VERIFICATION

### A. Static Web App Configuration
**Location:** Azure Portal > Static Web App > kraftdintel-web > Configuration

**Required Settings:**
- [ ] **Application Settings**
  - [ ] `VITE_API_URL` = `https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1`
  - [ ] Value must be EXACTLY this URL
  - [ ] Save changes if modified

- [ ] **Build Details**
  - [ ] App location: `frontend`
  - [ ] Output location: `dist`
  - [ ] Build preset: `Vite`

### B. Container App Environment Variables
**Location:** Azure Portal > Container Apps > kraftdintel-app > Settings > Environment variables

**Required Secrets (from Key Vault):**
- [ ] `COSMOS_DB_CONNECTION_STRING` - from kraftdintel-kv
- [ ] `OPENAI_API_KEY` - from kraftdintel-kv
- [ ] `JWT_SECRET` - from kraftdintel-kv
- [ ] `STORAGE_ACCOUNT_CONNECTION_STRING` - from kraftdintel-kv

**Status Check:**
- [ ] All values are populated (not blank)
- [ ] No error icons visible
- [ ] Container app shows "Running" status

### C. Key Vault Secret Verification
**Location:** Azure Portal > Key Vault > kraftdintel-kv > Secrets

**Required Secrets Present:**
- [ ] CosmosConnectionString
- [ ] OpenAIApiKey
- [ ] JwtSecret
- [ ] StorageAccountKey
- [ ] (Others as needed)

**Access Verification:**
- [ ] Container App has Key Vault read permissions
- [ ] Access policies show kraftdintel-app has "Get" permission

---

## 🔧 PHASE 2: ENDPOINT TESTING

### A. Frontend Accessibility
**Test:** Open in Browser
```
URL: https://jolly-coast-03a4f4d03.4.azurestaticapps.net
Expected: Login page appears, React app loads
```

**Results:**
- [ ] Page loads successfully (HTTP 200)
- [ ] No "404 Not Found" error
- [ ] No "CORS error" in console
- [ ] React app visible (not blank page)
- [ ] Login form displays

**F12 Console Check:**
- [ ] No red error messages
- [ ] No warnings about missing API
- [ ] No mixed content warnings

### B. Backend API Health
**Test:** Health Endpoint
```powershell
curl https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-18T..."
}
```

**Results:**
- [ ] HTTP 200 OK
- [ ] JSON response returned
- [ ] Status shows "healthy"

### C. API Documentation
**Test:** Swagger UI
```
URL: https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1/docs
Expected: Swagger UI with endpoint list
```

**Results:**
- [ ] Page loads (HTTP 200)
- [ ] Swagger UI visible
- [ ] Endpoint list displayed
- [ ] Can interact with API test tools

---

## 🔄 PHASE 3: GITHUB ACTIONS BUILD STATUS

**Location:** https://github.com/Knotcreativ/kraftd/actions

**Check Latest Workflow:**
- [ ] Find most recent workflow run
- [ ] Status should show ✅ "passed" (green checkmark)
- [ ] All jobs completed successfully

**If Failed:**
- [ ] Click on failed job
- [ ] Review build logs
- [ ] Look for error messages
- [ ] Common issues:
  - Node.js version mismatch
  - Missing dependencies
  - Build script errors
  - TypeScript compilation errors

**Last Successful Build:**
- [ ] When: _________________
- [ ] Commit: _________________
- [ ] Branch: main

---

## 🔐 PHASE 4: AUTHENTICATION FLOW

### A. User Registration
**Test:** Create new account
```
1. Go to: https://jolly-coast-03a4f4d03.4.azurestaticapps.net
2. Click "Register"
3. Fill form:
   - Name: Test User
   - Email: test@example.com
   - Password: Test@123456
4. Click "Register"
```

**Results:**
- [ ] No error message
- [ ] Redirect to login page
- [ ] Can login with new credentials
- [ ] User appears in Cosmos DB (Users collection)

**Troubleshooting if Failed:**
- [ ] Check API logs: `az containerapp logs show --name kraftdintel-app`
- [ ] Look for "register" endpoint errors
- [ ] Verify database connection string
- [ ] Check if Users collection exists

### B. User Login
**Test:** Login with registered user
```
1. Email: test@example.com
2. Password: Test@123456
3. Click "Login"
```

**Results:**
- [ ] HTTP 200 OK response
- [ ] JWT token received
- [ ] Token stored in localStorage
- [ ] Redirect to dashboard
- [ ] Welcome message appears

**Token Verification (F12 Developer Tools):**
1. Open: F12 (Developer Tools)
2. Go to: Application > Local Storage
3. Look for: `token` or `jwt` key
4. [ ] Token present and non-empty
5. [ ] Token is valid JWT format (three parts separated by dots)

**Troubleshooting if Failed:**
- [ ] Check browser console for error messages
- [ ] Verify JWT_SECRET is same in backend and frontend
- [ ] Check API response in Network tab (F12)
- [ ] Look for 401/403 errors

### C. Dashboard Access
**Test:** Authenticated page access
```
After successful login, verify:
```

**Results:**
- [ ] Dashboard page loads
- [ ] User name/email displayed
- [ ] Navigation menu visible
- [ ] No 401 Unauthorized errors
- [ ] Page elements render properly

**API Call Verification (F12 Network Tab):**
1. Open: F12 > Network tab
2. Clear network log
3. Perform action (e.g., navigate to dashboard)
4. Review requests:
   - [ ] All API calls return 2xx status
   - [ ] No 401 Unauthorized
   - [ ] No CORS errors
   - [ ] No 500 Server Errors

---

## 📊 PHASE 5: DATABASE CONNECTIVITY

### A. Cosmos DB Account Status
**Location:** Azure Portal > Cosmos DB > kraftdintel-cosmos

**Check:**
- [ ] Account status: "Online"
- [ ] Region: UAE North
- [ ] API: NoSQL

### B. Collections Verification
**Location:** Data Explorer in Cosmos DB

**Check Collections:**
- [ ] `Users` collection exists
  - [ ] Partition key: `/email`
  - [ ] Indexes configured
  
- [ ] `Documents` collection exists
  - [ ] Partition key: `/owner_email`
  
- [ ] `Workflows` collection exists
  - [ ] Partition key: `/owner_email`

**Data Check:**
- [ ] Users collection should have 1+ records (registration test)
- [ ] No error querying data
- [ ] Query response time reasonable (< 1 second)

### C. Connection String Validation
**Test:** Verify connection string works

**Check in Key Vault:**
1. Get secret: `CosmosConnectionString`
2. Value should start with: `mongodb://` or `AccountEndpoint=https://`
3. Contains password
4. Contains database name

---

## 🚨 PHASE 6: COMMON ISSUES & SOLUTIONS

### Issue: SWA shows "404 Not Found"
**Cause:** Frontend build failed or not deployed  
**Fix:**
1. Check GitHub Actions: All jobs passed?
2. Review build logs for errors
3. Ensure `npm run build` produces `dist/` folder
4. Trigger new workflow: Push to main branch

### Issue: API returns "Connection refused"
**Cause:** Container App not running  
**Fix:**
1. Check Container App status: Running?
2. Check replica count: ≥ 1?
3. View logs: `az containerapp logs show --name kraftdintel-app`
4. Restart if needed

### Issue: "CORS error" in browser console
**Cause:** VITE_API_URL not set or incorrect  
**Fix:**
1. Static Web App > Configuration
2. Verify `VITE_API_URL` is set EXACTLY
3. Must match backend API URL
4. Rebuild: Push to main branch
5. Wait for GitHub Actions to complete

### Issue: "401 Unauthorized" on login
**Cause:** JWT secret mismatch or auth error  
**Fix:**
1. Verify JWT_SECRET in Container App matches code
2. Check API logs for auth errors
3. Ensure Users collection has data
4. Test with curl: 
   ```
   curl -X POST https://api-url/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"Test@123456"}'
   ```

### Issue: Database "connection timeout"
**Cause:** Connection string invalid or DB unreachable  
**Fix:**
1. Verify connection string in Key Vault
2. Check Cosmos DB account is "Online"
3. Verify firewall rules (if any)
4. Restart Container App to reset connection pool

---

## 📈 PHASE 7: PERFORMANCE & MONITORING

### A. Response Time Baselines
**Target Metrics:**
- [ ] Frontend page load: < 3 seconds
- [ ] API response: < 500ms
- [ ] Database query: < 200ms
- [ ] Login flow: < 1 second total

**Measure (F12 Network Tab):**
1. Open DevTools
2. Go to Network tab
3. Reload page
4. Record load times
5. Document results

### B. Application Insights
**Location:** Azure Portal > Log Analytics workspace

**Check:**
- [ ] Telemetry data flowing
- [ ] Request count shows (should be > 0)
- [ ] Error rate acceptable (< 1%)
- [ ] No unexpected exceptions
- [ ] Performance metrics visible

**Custom Queries:**
```kusto
// Recent requests
requests | top 10 by timestamp desc

// Error rate
requests | where success == false | summarize count()

// Latency
requests | summarize avg(duration), max(duration) by name
```

---

## 📋 FINAL VERIFICATION CHECKLIST

### Pre-Launch Verification
- [ ] All 9 Azure resources deployed ✅
- [ ] Configuration verified ⏳
- [ ] Environment variables set ⏳
- [ ] Frontend loads ⏳
- [ ] Backend API responds ⏳
- [ ] Database connected ⏳
- [ ] Registration flow works ⏳
- [ ] Login flow works ⏳
- [ ] Dashboard accessible ⏳
- [ ] No console errors ⏳
- [ ] Monitoring active ⏳

### Go/No-Go Decision
```
ALL CHECKS PASSED: ✅ READY FOR PRODUCTION
FAILURES FOUND: ❌ REMEDIATE BEFORE LAUNCH
```

---

## 🎯 EXECUTION LOG

**Started:** January 18, 2026, 14:45 UTC+4  
**Phase 1 - Configuration:** [ ] Not Started
**Phase 2 - Endpoints:** [ ] Not Started
**Phase 3 - GitHub Actions:** [ ] Not Started
**Phase 4 - Authentication:** [ ] Not Started
**Phase 5 - Database:** [ ] Not Started
**Phase 6 - Troubleshooting:** [ ] Not Needed
**Phase 7 - Monitoring:** [ ] Not Started
**Final Review:** [ ] Pending

---

## 📞 NEXT STEPS

1. **Immediately:** Open Azure Portal configuration pages (links provided)
2. **Then:** Verify each configuration setting
3. **Next:** Test endpoints (frontend, API health)
4. **Then:** Test authentication flow (register, login)
5. **Finally:** Verify monitoring and sign-off

**Estimated Time:** 30-45 minutes to complete all phases

---

**Document Version:** 1.0  
**Last Updated:** January 18, 2026  
**Status:** Ready for Execution
