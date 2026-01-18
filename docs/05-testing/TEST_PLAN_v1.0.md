# Test Plan Document

**Version:** 1.0  
**Status:** APPROVED  
**Created:** 2026-01-17  
**Target Coverage:** 85%+

---

## Testing Strategy

**Pyramid Model:**
```
          /\
         /  \  End-to-End Tests (5%)
        /    \
       /______\
      /        \
     /          \  Integration Tests (15%)
    /            \
   /              \
  /________________\
 /                  \
/                    \  Unit Tests (80%)
/____________________\
```

---

## Testing Scope

### Unit Tests (80% coverage target)
**Focus:** Individual functions, services, components

**Examples:**
- Service method logic (extraction, comparison scoring)
- Validation functions
- Utility helpers
- React component behavior (in isolation)

**Tools:** pytest (backend), Jest (frontend)

### Integration Tests (15% coverage target)
**Focus:** Component interactions, API endpoints

**Examples:**
- API endpoint request/response flow
- Database CRUD operations
- Service-to-service communication
- Multi-component workflows

**Tools:** pytest + FastAPI TestClient, React Testing Library

### End-to-End Tests (5% coverage target)
**Focus:** Complete user flows

**Examples:**
- Login → Upload → Extract → Workflow flow
- Quote comparison → PO generation flow
- Full procurement process

**Tools:** Playwright, Cypress

---

## Backend Testing Plan

### Authentication Tests
```
✓ Login with valid credentials → returns JWT token
✓ Login with invalid credentials → returns 401
✓ Login with non-existent user → returns 401
✓ Logout invalidates token → subsequent requests fail
✓ Token refresh → returns new valid token
✓ Expired token → returns 401
✓ Malformed token → returns 401
```

### Document Management Tests
```
✓ Upload valid PDF file → document created
✓ Upload file > 5MB → returns 413 error
✓ Upload unsupported format → returns 400 error
✓ List documents → returns user's documents
✓ Get document by ID → returns full details
✓ Get non-existent document → returns 404
✓ Update extracted data → data persisted
✓ Delete document → document removed
✓ Unauthorized access to document → returns 403
```

### Extraction Service Tests
```
✓ Extract valid RFQ document → returns structured data
✓ Extract valid Quotation → returns line items
✓ Extract with low confidence → marks as needs_review
✓ Handle corrupted PDF → returns error
✓ Handle extraction timeout → returns timeout error
✓ Multiple simultaneous extractions → all succeed
✓ Confidence scores accurate → validates against known samples
```

### Workflow Tests
```
✓ Create workflow → initializes step 1
✓ Advance step → updates current_step
✓ Cannot skip steps → validates sequence
✓ Complete workflow → status = completed
✓ Get workflow progress → returns correct state
✓ Deadline validation → alerts if overdue
```

### Comparison Service Tests
```
✓ Score quotations → applies weights correctly
✓ Price-based sorting → lowest cost first
✓ Timeline scoring → shortest timeline highest
✓ Generate recommendation → selects best option
✓ Tie-breaking → consistent results
✓ Empty quotation list → returns empty result
```

### PO Generation Tests
```
✓ Generate PO → creates valid document
✓ PO contains all line items → complete data
✓ PO total calculation → correct math
✓ Tax calculation → correct rate applied
✓ PO approval workflow → routes to approvers
✓ Send to vendor → email formatted correctly
```

---

## Frontend Testing Plan

### Login Component
```
✓ Render login form → email & password inputs visible
✓ Submit invalid email → shows validation error
✓ Submit valid credentials → calls API
✓ API returns token → stores in localStorage
✓ Redirect to dashboard → navigation works
✓ Error message displays → on failed login
✓ Remember me → persists session
```

### Dashboard Component
```
✓ Load documents → displays list
✓ Pagination → shows 20 per page
✓ Search filter → filters documents
✓ Sort by date → recent first
✓ Document card → shows metadata
✓ Click document → navigates to detail
✓ Upload button → opens upload modal
✓ Empty state → message when no docs
```

### DocumentDetail Component
```
✓ Load document → displays all fields
✓ Show extracted data → displays structured fields
✓ Edit mode → allows field updates
✓ Save changes → calls API to update
✓ Delete button → removes document
✓ Workflow indicator → shows progress
✓ Actions available → based on status
```

### Upload Component
```
✓ Drag & drop file → accepts upload
✓ Click to upload → file picker opens
✓ File validation → prevents invalid files
✓ Progress indicator → shows upload progress
✓ Extraction polling → shows status updates
✓ Redirect on completion → to document detail
✓ Error handling → displays upload errors
```

### API Service
```
✓ Authentication header → JWT included
✓ Timeout handling → handles slow requests
✓ Error responses → parsed correctly
✓ 401 response → redirects to login
✓ Retry logic → retries on network error
✓ Token refresh → automatic re-auth
```

---

## Test Case Examples

### Test Case: Successful Document Upload and Extraction

**ID:** TC-DOC-001
**Priority:** Critical
**Category:** Document Management

**Preconditions:**
- User logged in
- Sample RFQ PDF available
- Azure Document Intelligence configured

**Steps:**
1. Navigate to upload page
2. Drag & drop RFQ_Sample.pdf
3. Select document type: "RFQ"
4. Click "Upload"
5. Wait for extraction

**Expected Result:**
- ✓ Document uploaded successfully
- ✓ Status changes to "extracting"
- ✓ Extraction completes within 30 seconds
- ✓ Extracted data displayed
- ✓ Confidence score > 90%
- ✓ Line items extracted correctly

---

### Test Case: Quote Comparison Scoring

**ID:** TC-COMP-001
**Priority:** High
**Category:** Quote Comparison

**Preconditions:**
- Workflow with 3 quotations created
- Scoring weights configured (Price 40%, Timeline 30%, Terms 20%, Rating 10%)

**Steps:**
1. Navigate to comparison view
2. Verify all 3 quotations loaded
3. Check scoring criteria displayed
4. Verify best option highlighted

**Expected Result:**
- ✓ All quotations scored
- ✓ Recommendation shown
- ✓ Top choice accurate
- ✓ Score breakdown visible
- ✓ "Select Best" button works

---

### Test Case: PO Generation and Approval

**ID:** TC-PO-001
**Priority:** Critical
**Category:** Purchase Order

**Preconditions:**
- Comparison completed
- Best quote selected
- Approver role configured

**Steps:**
1. Create PO from comparison
2. Review PO details
3. Submit for approval
4. As approver, review PO
5. Approve PO
6. PO sent to vendor

**Expected Result:**
- ✓ PO generated with correct data
- ✓ Sent to approver email
- ✓ Approver can view and approve
- ✓ Vendor receives PO email
- ✓ PO status = "approved"

---

## Performance Test Targets

| Metric | Target |
|--------|--------|
| Page load time | < 2 seconds |
| API response time | < 500ms (p95) |
| Search results | < 1 second |
| Document extraction | < 60 seconds |
| Database query | < 100ms |
| Build time | < 2 minutes |
| Bundle size | < 500KB (gzipped) |

---

## Security Testing

| Test | Verification |
|------|--------------|
| SQL Injection | Parameterized queries only |
| XSS Prevention | Input sanitization, output encoding |
| CSRF Protection | CORS tokens, same-origin checks |
| Sensitive Data | No passwords in logs, API responses |
| JWT Validation | Token signature verified, expiry checked |
| Rate Limiting | Max 100 requests/min per user |
| File Upload | Type validation, size limits, scan for malware |

---

## Test Data

### Sample Documents

**RFQ Sample:**
```
File: test_data/RFQ_Sample.pdf
Type: Request for Quote
Size: 250 KB
Expected Extraction:
  - Project: Website Redesign
  - Budget: $50,000
  - Due Date: 2026-02-15
  - Line Items: 3
```

**Quotation Sample:**
```
File: test_data/Quote_Sample_1.pdf
Vendor: ACME Solutions
Amount: $34,000
Timeline: 8 weeks
Expected Extraction:
  - All line items extracted
  - Confidence > 95%
```

---

## Testing Tools & Setup

### Backend
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio httpx

# Run tests
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_auth.py::test_login_success -v
```

### Frontend
```bash
# Install test dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom jest

# Run tests
npm run test

# Run with coverage
npm run test:coverage

# Run specific test file
npm run test -- DocumentDetail.test.tsx
```

### E2E Testing (Optional)
```bash
# Install Playwright
npm install --save-dev @playwright/test

# Run E2E tests
npx playwright test

# Run with UI
npx playwright test --ui
```

---

## Test Execution Schedule

| Phase | When | Duration | Coverage |
|-------|------|----------|----------|
| Unit | Every commit | Continuous | 80%+ |
| Integration | Daily | ~30 min | 15%+ |
| E2E | Before release | ~1 hour | 5%+ |
| Performance | Weekly | ~1 hour | Key flows |
| Security | Monthly | ~2 hours | Full scan |

---

## CI/CD Integration

**GitHub Actions Workflow:**

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ --cov=.

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install --prefix frontend
      - run: npm run test --prefix frontend
```

---

## Test Success Criteria

- ✓ 85%+ code coverage
- ✓ All critical tests passing
- ✓ No regressions from previous release
- ✓ Performance targets met
- ✓ Security scans clean
- ✓ Zero unresolved bugs (P0/P1)

---

**Reference:** `/docs/05-testing/TEST_PLAN_v1.0.md`
