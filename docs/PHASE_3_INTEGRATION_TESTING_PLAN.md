# Phase 3: Integration Testing Plan
**Status:** PREPARED FOR EXECUTION  
**Trigger:** When Backend Container App deployment completes (~10 minutes from Phase 2 push)  
**Target Timeline:** 30-45 minutes  
**Success Criteria:** All frontend-to-backend flows working, zero integration errors  

---

## 1. Deployment Status

### Current Status
- ✅ **Frontend:** LIVE at https://kraftd.io
- 🟢 **Backend:** Deploying via GitHub Actions (commit 3827ba2)
  - Building Docker image in Azure Container Registry
  - Pushing to kraftdintel.azurecr.io/kraftdintel:latest
  - Deploying to Container Apps (kraftdintel-app, UAE North)
  - **ETA:** ~10 minutes from Phase 2 push
  - **Monitoring:** https://github.com/Knotcreativ/kraftd/actions

### Service Endpoints
| Component | Status | URL | Region |
|-----------|--------|-----|--------|
| Frontend | ✅ LIVE | https://kraftd.io | West Europe (CDN) |
| Backend | ⏳ DEPLOYING | https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io | UAE North |
| Cosmos DB | ✅ Ready | Internal endpoint | UAE North |
| Storage | ✅ Ready | Azure Blob Storage | Geo-redundant |
| Key Vault | ✅ Ready | Internal access | UAE North |

---

## 2. Pre-Testing Verification

### 2.1 Backend Health Check (First Step)
Once backend Container App finishes deploying:

```bash
# Check Container App status
az containerapp show --name kraftdintel-app --resource-group kraftdintel-rg --query provisioningState

# Test health endpoint
curl -i https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/health

# Expected Response:
# HTTP/1.1 200 OK
# Content-Type: application/json
# {"status": "healthy", "version": "1.0", "timestamp": "2024-..."}
```

### 2.2 Backend Environment Verification
```bash
# Check if environment variables loaded from Key Vault
# Check container logs for:
# ✓ FastAPI startup message
# ✓ Uvicorn running on 0.0.0.0:8000
# ✓ Cosmos DB connection initialized
# ✓ Azure Storage client ready
# ✓ OpenAI API configured
```

---

## 3. Integration Test Scenarios

### Test Group 1: Authentication Flow (Critical Path)
**Objective:** Verify user registration, login, and session management

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| IT-1 | User Registration | 1. Open https://kraftd.io<br>2. Click "Sign Up"<br>3. Enter email, password<br>4. Submit form | 201 Created response, user stored in Cosmos DB | **CRITICAL** |
| IT-2 | User Login | 1. Registered user email/pass<br>2. Click "Login"<br>3. Submit credentials | 200 OK, JWT token returned, redirect to dashboard | **CRITICAL** |
| IT-3 | Session Persistence | 1. Login<br>2. Close browser tab<br>3. Reopen https://kraftd.io | User stays logged in (token in localStorage) | **CRITICAL** |
| IT-4 | Logout | 1. Logged-in user<br>2. Click logout<br>3. Check redirect | Redirect to login, token cleared, session ended | **HIGH** |
| IT-5 | Unauthorized Access | 1. No token<br>2. Try accessing /dashboard API | 401 Unauthorized response | **HIGH** |

### Test Group 2: Document Upload & Processing (Core Feature)
**Objective:** Verify file upload, Azure Storage integration, and document processing

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| IT-6 | File Upload (PDF) | 1. Login<br>2. Click "Upload Document"<br>3. Select sample.pdf<br>4. Submit | File stored in Azure Blob Storage, metadata in Cosmos DB, 200 OK | **CRITICAL** |
| IT-7 | File Upload (Image) | 1. Login<br>2. Upload JPG/PNG<br>3. Submit | File processed, OCR triggered (Tesseract), status = processing | **HIGH** |
| IT-8 | File Upload (Large) | 1. Upload 50MB+ file<br>2. Check response time | Files chunked/streamed, no timeout, status = uploading | **MEDIUM** |
| IT-9 | Upload Progress | 1. Start large file upload<br>2. Observe progress bar | Progress updates real-time (1-10 second intervals) | **MEDIUM** |
| IT-10 | Document Processing | 1. PDF uploaded<br>2. Wait for processing<br>3. Check extracted data | Text extracted correctly, metadata parsed, AI analysis ready | **CRITICAL** |

### Test Group 3: AI-Powered Features (Advanced)
**Objective:** Verify OpenAI integration, extraction, and analysis

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| IT-11 | Text Extraction | 1. Document processed<br>2. View "Extracted Text" tab | Complete text from document visible, proper formatting | **HIGH** |
| IT-12 | AI Analysis | 1. Extracted text ready<br>2. Click "Analyze with AI"<br>3. Select analysis type | 200 OK, GPT-4 response returned in 5-15 seconds | **HIGH** |
| IT-13 | Key Insights | 1. Run analysis<br>2. Check "Key Insights" section | Summarized bullet points, actionable insights extracted | **MEDIUM** |
| IT-14 | Metadata Extraction | 1. Business doc uploaded<br>2. Run metadata extraction | Company name, date, amount, parties extracted accurately | **MEDIUM** |
| IT-15 | Multi-Document Analysis | 1. Upload 5 documents<br>2. Run batch analysis | All documents processed in parallel, results aggregated | **MEDIUM** |

### Test Group 4: Data & Storage Integration
**Objective:** Verify Cosmos DB and Azure Storage work correctly with frontend

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| IT-16 | Document List Load | 1. Login<br>2. View dashboard<br>3. Check document list | All user documents appear, sorted by date, loaded in <2s | **HIGH** |
| IT-17 | Document Details | 1. Click on document<br>2. View details page | All metadata displayed (upload date, size, status, extraction results) | **HIGH** |
| IT-18 | Document Delete | 1. Click delete on document<br>2. Confirm | Document removed from UI and Cosmos DB, file deleted from Blob Storage | **MEDIUM** |
| IT-19 | Document Download | 1. Click download<br>2. Check file size | Original file downloaded correctly, file integrity verified | **MEDIUM** |
| IT-20 | Data Consistency | 1. Edit document metadata<br>2. Refresh page<br>3. Check data | Changes persisted in Cosmos DB, appear immediately on reload | **HIGH** |

### Test Group 5: API Endpoints (Backend Direct Testing)
**Objective:** Direct API testing via Postman/curl (parallel to UI testing)

| Test ID | Test Name | Method | Endpoint | Expected Response | Priority |
|---------|-----------|--------|----------|-------------------|----------|
| IT-21 | Health Check | GET | `/health` | 200, JSON with status:healthy | **CRITICAL** |
| IT-22 | Register User | POST | `/auth/register` | 201, user created with ID | **CRITICAL** |
| IT-23 | Login | POST | `/auth/login` | 200, JWT token, expires_in | **CRITICAL** |
| IT-24 | Get User Profile | GET | `/users/me` (auth required) | 200, user object | **HIGH** |
| IT-25 | Upload Document | POST | `/documents/upload` | 201, document_id, storage_url | **CRITICAL** |
| IT-26 | List Documents | GET | `/documents?skip=0&limit=10` | 200, array of user's documents | **HIGH** |
| IT-27 | Get Document | GET | `/documents/{id}` | 200, document with all metadata | **HIGH** |
| IT-28 | Delete Document | DELETE | `/documents/{id}` | 204 No Content, doc removed | **MEDIUM** |
| IT-29 | Extract Text | POST | `/documents/{id}/extract` | 200, extracted_text, confidence | **HIGH** |
| IT-30 | Analyze Document | POST | `/documents/{id}/analyze` | 200 (async), task_id or results | **HIGH** |

---

## 4. Testing Tools & Environment

### Browser DevTools (For UI Testing)
**What to Monitor:**
- **Network tab:** All API requests, response times, status codes
- **Console:** JavaScript errors, warnings, API response logs
- **Storage:** JWT token in localStorage, session data
- **Performance:** Page load times, rendering performance
- **Application:** Cookie inspection, local storage content

### curl Commands (For API Testing)
```bash
# Set variables
$BACKEND_URL = "https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io"
$TOKEN = "" # Will be set after login

# Health check
curl -i "$BACKEND_URL/health"

# Register
curl -X POST "$BACKEND_URL/auth/register" `
  -H "Content-Type: application/json" `
  -d '{"email":"test@example.com","password":"TestPass123"}'

# Login
curl -X POST "$BACKEND_URL/auth/login" `
  -H "Content-Type: application/json" `
  -d '{"email":"test@example.com","password":"TestPass123"}'

# Get user (requires token)
curl -X GET "$BACKEND_URL/users/me" `
  -H "Authorization: Bearer $TOKEN"
```

### Postman Collection
**Will Create:**
- Integration Testing Postman collection
- All 30 API endpoints
- Pre-request scripts (token extraction)
- Tests (assertions for status codes, response structure)
- Environment variables (URLs, tokens)

### Monitoring
**Real-time Logs:**
```bash
# Container App logs
az containerapp logs show --name kraftdintel-app --resource-group kraftdintel-rg --follow

# Application Insights (if enabled)
az monitor app-insights query --app kraftdintel-insights --analytics-query "traces | order by timestamp desc | limit 100"
```

---

## 5. Testing Schedule

### Phase 3a: Backend Verification (Immediate)
**When:** Upon backend deployment completion  
**Duration:** 5-10 minutes

- ✓ Health check endpoint
- ✓ Container logs review
- ✓ Environment variables verification
- ✓ Cosmos DB connectivity test
- ✓ Storage account access test

### Phase 3b: Frontend-to-Backend Integration (10-15 min)
**When:** After backend verified healthy  
**Duration:** 20-30 minutes

- ✓ **Test Group 1:** Authentication (5 scenarios)
- ✓ **Test Group 2:** Document Upload (5 scenarios)
- ✓ **Test Group 3:** AI Features (5 scenarios)
- ✓ **Test Group 4:** Data Integration (5 scenarios)

### Phase 3c: API Direct Testing (Parallel)
**When:** Concurrent with UI testing  
**Duration:** 15-20 minutes

- ✓ **Test Group 5:** API Endpoints (10 scenarios)
- ✓ Postman collection execution
- ✓ Load testing (5 concurrent users)

### Phase 3d: Documentation & Issue Resolution
**When:** After all tests  
**Duration:** 10-15 minutes

- Document any failures
- Log issues with steps to reproduce
- Create fixes if needed
- Rerun failed scenarios

---

## 6. Success Criteria

### Critical Path (Must Pass)
- ✅ Backend health endpoint returns 200
- ✅ User registration works end-to-end
- ✅ User login works and JWT token returned
- ✅ Document upload to Azure Storage succeeds
- ✅ Document metadata stored in Cosmos DB
- ✅ Frontend displays user's documents
- ✅ Document download retrieves correct file

### High Priority (Should Pass)
- ✅ AI analysis processes documents
- ✅ Text extraction works
- ✅ Metadata parsing succeeds
- ✅ Document deletion works
- ✅ All API endpoints respond with correct status codes
- ✅ Page load times < 3 seconds
- ✅ API response times < 2 seconds

### Medium Priority (Nice to Have)
- ✅ Real-time progress updates
- ✅ Batch document processing
- ✅ Advanced filtering
- ✅ Performance under load (5 concurrent users)

---

## 7. Issue Tracking

### Issue Template
```
ID: IT-XXX-001
Test: [Test scenario name]
Severity: CRITICAL | HIGH | MEDIUM | LOW
Status: OPEN | IN PROGRESS | RESOLVED
Steps to Reproduce:
1. 
2. 
3. 
Expected: 
Actual: 
Error Message: 
Logs: [Container App logs, console output]
Resolution: 
```

---

## 8. Next Phase (Phase 4: Production Validation)

**After Phase 3 completes successfully:**

### Phase 4 Activities (45-60 minutes)
1. **Load Testing:** 10-50 concurrent users
2. **Security Scanning:** OWASP, SSL/TLS, CORS
3. **Performance Benchmarking:** Response times, throughput
4. **Monitoring Setup:** Azure Monitor, alerts
5. **Cost Optimization:** Azure resource tuning
6. **Documentation:** Final deployment summary

**Phase 4 Success Criteria:**
- System handles 50 concurrent users
- No security vulnerabilities found
- 99% availability SLA maintained
- All alerts configured and tested
- Performance meets requirements

---

## 9. Quick Reference

### Backend Deployment Monitoring
- **GitHub Actions:** https://github.com/Knotcreativ/kraftd/actions
- **Azure Portal:** https://portal.azure.com → Container Apps → kraftdintel-app
- **Container Logs:** `az containerapp logs show --name kraftdintel-app --resource-group kraftdintel-rg --follow`

### Service URLs
| Service | URL |
|---------|-----|
| Frontend | https://kraftd.io |
| Backend API | https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io |
| Backend Health | https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/health |
| GitHub Actions | https://github.com/Knotcreativ/kraftd/actions |
| Azure Portal | https://portal.azure.com |

### Testing Files to Create
1. ✓ PHASE_3_INTEGRATION_TESTING_PLAN.md (THIS FILE)
2. ⏳ PHASE_3_INTEGRATION_TEST_RESULTS.md (After testing)
3. ⏳ PHASE_3_INTEGRATION_POSTMAN_COLLECTION.json (API tests)
4. ⏳ PHASE_3_ISSUES_LOG.md (Any issues found)

---

## 10. Execution Checklist

### Before Testing
- [ ] Backend Container App deployment completed
- [ ] Health endpoint returns 200 OK
- [ ] Container logs show successful startup
- [ ] Environment variables loaded from Key Vault
- [ ] Cosmos DB connectivity verified
- [ ] Storage account access verified

### During Testing
- [ ] All Test Group 1 scenarios passed (Authentication)
- [ ] All Test Group 2 scenarios passed (Upload & Processing)
- [ ] All Test Group 3 scenarios passed (AI Features)
- [ ] All Test Group 4 scenarios passed (Data Integration)
- [ ] All Test Group 5 scenarios passed (API Endpoints)
- [ ] No critical errors found
- [ ] All issues documented

### After Testing
- [ ] Test results documented in PHASE_3_INTEGRATION_TEST_RESULTS.md
- [ ] All issues logged with severity and resolution
- [ ] Critical issues resolved
- [ ] Frontend and backend verified working together
- [ ] Ready to proceed to Phase 4

---

## Status
- 📋 Plan: READY FOR EXECUTION
- 🟢 Trigger: Backend deployment completion
- ⏱️ ETA: 30-45 minutes to complete
- 📊 Success Rate Target: 100% (all critical + high priority tests pass)
- 📅 Timeline: Phase 3 → Phase 4 (Production Validation) → PRODUCTION READY ✅

