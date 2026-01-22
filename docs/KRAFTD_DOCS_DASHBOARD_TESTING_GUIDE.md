# 🧪 Kraftd Docs User Dashboard - Testing Guide

**Version:** 1.0  
**Created:** January 20, 2025  
**Purpose:** Comprehensive testing procedures for the enhanced user dashboard

---

## Quick Links
- [Component Tests](#1-component-tests)
- [Integration Tests](#2-integration-tests)  
- [Responsive Tests](#3-responsive-design-tests)
- [Performance Tests](#4-performance-tests)
- [Accessibility Tests](#5-accessibility-tests)
- [Security Tests](#6-security-tests)

---

## 1. Component Tests

### 1.1 Dashboard Component

**Test ID:** COMP-DASH-001  
**Component:** `Dashboard.tsx`

| # | Scenario | Expected Result | Status |
|---|----------|-----------------|--------|
| 1 | Component renders without errors | No console errors | ⬜ |
| 2 | Header displays with title "📊 Kraftd Docs" | Title visible | ⬜ |
| 3 | User welcome message shows email prefix | "Welcome back, john!" | ⬜ |
| 4 | Logout button is clickable | Button visible and interactive | ⬜ |
| 5 | Tabs navigation displays "Overview" and "Documents" | Both tabs visible | ⬜ |
| 6 | Overview tab is selected by default | Overview tab highlighted | ⬜ |

### 1.2 Statistics Cards Component

**Test ID:** COMP-STAT-001  
**Component:** `StatCard.tsx`

| # | Scenario | Expected Result | Status |
|---|----------|-----------------|--------|
| 1 | Four stat cards render | All 4 cards visible | ⬜ |
| 2 | Total Documents card shows count | Shows: "📁 Total Documents" | ⬜ |
| 3 | Processed card shows percentage | Shows: "✅ Processed" + "87% complete" | ⬜ |
| 4 | Processing card shows pending count | Shows: "⏳ Processing" + number | ⬜ |
| 5 | Exported card shows export count | Shows: "📥 Exported" + number | ⬜ |
| 6 | Correct color gradient applied | Each card has unique color | ⬜ |
| 7 | Hover effect works | Card elevates on hover | ⬜ |

### 1.3 Activity Feed Component

**Test ID:** COMP-FEED-001  
**Component:** `ActivityFeed.tsx`

| # | Scenario | Expected Result | Status |
|---|----------|-----------------|--------|
| 1 | Activity feed renders | "Recent Activity" header visible | ⬜ |
| 2 | Shows last 5 activities | Max 5 items in feed | ⬜ |
| 3 | Activity icons display correctly | Upload (📤), Process (⚙️), Export (📥) | ⬜ |
| 4 | Status badges show correct icon | Success (✓), Processing (⟳), Error (!) | ⬜ |
| 5 | Empty state shows message | "No recent activity" for new users | ⬜ |
| 6 | Timestamps display correctly | Format: "January 20, 2025" | ⬜ |

### 1.4 Quick Actions Component

**Test ID:** COMP-ACT-001  
**Component:** `quick-actions` section

| # | Scenario | Expected Result | Status |
|---|----------|-----------------|--------|
| 1 | Four action buttons render | All buttons visible | ⬜ |
| 2 | "Upload Document" button works | Switches to Documents tab on click | ⬜ |
| 3 | "View Analytics" button visible | Button clickable (no action yet) | ⬜ |
| 4 | "Settings" button visible | Button clickable (no action yet) | ⬜ |
| 5 | "Help & Guides" button visible | Button clickable (no action yet) | ⬜ |
| 6 | Buttons have correct icons | Icons display correctly | ⬜ |

---

## 2. Integration Tests

### 2.1 Tab Navigation

**Test ID:** INT-TAB-001  
**Purpose:** Test tab switching functionality

```
Test Steps:
1. Load Dashboard
2. Click "Overview" tab
3. Verify Overview section visible
4. Click "Documents" tab
5. Verify Documents section visible
6. Click back to "Overview"
7. Verify Overview section visible again

Expected: Tab switches smoothly, content changes correctly
Status: ⬜
```

### 2.2 Data Loading

**Test ID:** INT-DATA-001  
**Purpose:** Test API data loading

```
Test Steps:
1. Load Dashboard (authenticated)
2. Observe loading spinner
3. Wait for data to load
4. Verify documents appear
5. Check statistics calculate correctly

Expected: 
- Loading spinner shows
- Data loads within 2 seconds
- Statistics match document count
- No console errors

Status: ⬜
```

### 2.3 Document Upload Integration

**Test ID:** INT-UPLOAD-001  
**Purpose:** Test document upload from dashboard

```
Test Steps:
1. Click "Upload Document" button
2. Select Documents tab
3. Drag & drop a PDF file
4. Observe upload progress
5. Verify success message
6. Check document appears in list
7. Verify stats update

Expected:
- Success message: "✓ 'filename.pdf' uploaded successfully!"
- Document appears with "Pending" status
- Total Documents count increases by 1
- Upload area resets

Status: ⬜
```

### 2.4 Document Review Integration

**Test ID:** INT-REVIEW-001  
**Purpose:** Test document review/analysis workflow

```
Test Steps:
1. Upload a test document
2. Verify document shows in list
3. Click "Review" button
4. Observe status change to "Processing"
5. Check activity feed updates
6. Verify success message

Expected:
- Success message shows processing ID
- Document status: "Processing"
- Activity feed shows new entry
- Processing badge animated

Status: ⬜
```

### 2.5 Document Deletion

**Test ID:** INT-DELETE-001  
**Purpose:** Test document deletion

```
Test Steps:
1. Upload a test document
2. Click delete/trash icon
3. Confirm deletion in dialog
4. Verify success message
5. Check document removed from list
6. Verify stats update

Expected:
- Confirmation dialog appears
- Success message: "✓ Document deleted successfully"
- Document removed from list
- Total Documents count decreases by 1

Status: ⬜
```

### 2.6 Authentication Integration

**Test ID:** INT-AUTH-001  
**Purpose:** Test authentication with dashboard

```
Test Steps:
1. Access dashboard without login
2. Should redirect to /login
3. Login with credentials
4. Redirect to dashboard
5. Verify welcome message shows user email
6. Click logout
7. Verify redirect to login page

Expected:
- Unauthenticated users redirected to login
- Welcome message shows user email prefix
- Logout clears auth and redirects

Status: ⬜
```

---

## 3. Responsive Design Tests

### 3.1 Mobile (375px - iPhone SE)

**Test ID:** RESP-MOB-001

| # | Component | Expected Behavior | Status |
|---|-----------|-------------------|--------|
| 1 | Header | Single column, centered | ⬜ |
| 2 | Logout button | Full width | ⬜ |
| 3 | Tabs | Full width, stacked horizontally | ⬜ |
| 4 | Stat cards | Single column layout | ⬜ |
| 5 | Actions grid | 2 columns (2x2 layout) | ⬜ |
| 6 | Activity items | Vertical layout, no wrapping | ⬜ |
| 7 | Upload area | Full width, no overflow | ⬜ |
| 8 | Document list | Full width cards | ⬜ |

**Test Method:**
```bash
# Chrome DevTools
1. Press F12
2. Click toggle device toolbar
3. Select iPhone SE (375x667)
4. Test all interactions
5. Verify no horizontal scroll
6. Check touch targets (44px+ recommended)
```

### 3.2 Tablet (768px - iPad)

**Test ID:** RESP-TAB-001

| # | Component | Expected Behavior | Status |
|---|-----------|-------------------|--------|
| 1 | Header | Flexbox layout, space-between | ⬜ |
| 2 | Stat cards | 2x2 grid layout | ⬜ |
| 3 | Actions grid | 2 columns | ⬜ |
| 4 | Activity feed | Single column, wider cards | ⬜ |

### 3.3 Desktop (1200px)

**Test ID:** RESP-DES-001

| # | Component | Expected Behavior | Status |
|---|-----------|-------------------|--------|
| 1 | Stat cards | 4 columns in one row | ⬜ |
| 2 | Actions grid | 4 columns in one row | ⬜ |
| 3 | Content | Centered with max-width 1400px | ⬜ |

### 3.4 Orientation Changes

**Test ID:** RESP-ORI-001

```
Test Steps:
1. Open Dashboard on tablet
2. Portrait orientation (768x1024)
   - Stat cards: 2x2 grid
   - Actions: 2 columns
3. Rotate to landscape (1024x768)
   - Stat cards: 4 columns
   - Actions: 4 columns
4. Verify smooth transition
5. No content cutoff

Status: ⬜
```

---

## 4. Performance Tests

### 4.1 Page Load Performance

**Test ID:** PERF-LOAD-001

```
Test Steps:
1. Open Chrome DevTools
2. Go to Network tab
3. Load dashboard page
4. Record metrics:
   - DOMContentLoaded
   - Load event
   - First Contentful Paint (FCP)
   - Largest Contentful Paint (LCP)
5. Check Lighthouse score

Benchmarks:
- Page Load: < 2.0s ✓
- FCP: < 1.5s ✓
- LCP: < 2.5s ✓
- Lighthouse: > 90 ✓

Status: ⬜
```

### 4.2 JavaScript Performance

**Test ID:** PERF-JS-001

```
Test Steps:
1. Open Performance tab in DevTools
2. Click Record
3. Perform interactions:
   - Switch tabs (5 times)
   - Hover over stat cards
   - Scroll activity feed
4. Stop recording
5. Review Scripting time

Benchmark:
- Main thread blocking: < 100ms ✓
- Tab switch: < 50ms ✓
- Scroll smoothness: 60fps ✓

Status: ⬜
```

### 4.3 Memory Usage

**Test ID:** PERF-MEM-001

```
Test Steps:
1. Open Memory tab in DevTools
2. Take heap snapshot (baseline)
3. Upload 5 documents
4. Switch tabs 10 times
5. Take heap snapshot (current)
6. Compare memory usage

Benchmark:
- Baseline: < 20MB
- After actions: < 30MB
- No memory leaks ✓

Status: ⬜
```

### 4.4 API Response Performance

**Test ID:** PERF-API-001

```
Test Steps:
1. Open Network tab
2. Reload dashboard
3. Check API requests:
   - GET /api/v1/documents: < 500ms
   - POST /api/v1/documents/upload: < 2000ms
   - DELETE /api/v1/documents/{id}: < 500ms

Benchmark:
- List documents: < 500ms ✓
- Upload: < 2s ✓
- Delete: < 500ms ✓

Status: ⬜
```

---

## 5. Accessibility Tests

### 5.1 Keyboard Navigation

**Test ID:** A11Y-KB-001

```
Test Steps:
1. Close mouse/trackpad
2. Use only Tab/Shift+Tab/Enter keys
3. Navigate through:
   - Logout button
   - Tab buttons
   - Action buttons
   - Form inputs
4. Verify focus indicators visible
5. Verify semantic order logical

Expected:
- All interactive elements keyboard accessible
- Focus indicator visible (blue outline)
- Tab order logical top-to-bottom
- No keyboard traps

Status: ⬜
```

### 5.2 Screen Reader Test (NVDA/JAWS)

**Test ID:** A11Y-SR-001

```
Test Steps:
1. Enable screen reader (NVDA on Windows)
2. Navigate dashboard
3. Verify announcements:
   - Page title
   - Headings (h1, h2, h3)
   - Button labels
   - Form labels
   - Status messages
4. Check image alt text

Expected:
- All content readable by screen reader
- Proper heading hierarchy
- Clear button labels
- Alert announcements

Status: ⬜
```

### 5.3 Color Contrast

**Test ID:** A11Y-COL-001

```
Tools: WAVE Browser Extension

Test Steps:
1. Install WAVE extension
2. Open dashboard
3. Run WAVE analysis
4. Check contrast ratios:
   - Text on background: 4.5:1 ✓
   - UI components: 3:1 ✓
5. Verify no red/yellow errors

Benchmark:
- AA compliance: All pass ✓
- AAA compliance: Preferred ✓

Status: ⬜
```

---

## 6. Security Tests

### 6.1 Authentication

**Test ID:** SEC-AUTH-001

```
Test Steps:
1. Try accessing /dashboard without token
   - Should redirect to /login ✓
2. Login with valid credentials
   - Should show dashboard ✓
3. Token expires (simulate)
   - Should redirect to /login ✓
4. Try manipulating JWT token
   - Should redirect to /login ✓

Status: ⬜
```

### 6.2 XSS Prevention

**Test ID:** SEC-XSS-001

```
Test Steps:
1. Upload document with XSS in filename:
   <img src=x onerror="alert('XSS')">
2. Verify in document list:
   - Script NOT executed
   - Text rendered as-is
3. Check activity feed:
   - No script execution
   - Text properly escaped

Expected:
- No alert boxes
- XSS payload displayed as text
- No console errors

Status: ⬜
```

### 6.3 CSRF Protection

**Test ID:** SEC-CSRF-001

```
Test Steps:
1. Logout and clear cookies
2. Create form on external site:
   - POST to /api/v1/documents/upload
3. Try submitting from external site
4. Verify request blocked:
   - CORS error ✓
   - 403 Forbidden ✓

Expected:
- Request rejected
- No unauthorized action

Status: ⬜
```

---

## 7. Browser Compatibility Tests

### 7.1 Chrome/Edge (Chromium-based)

**Test ID:** COMPAT-CHR-001

| Feature | Expected | Status |
|---------|----------|--------|
| Gradient backgrounds | ✓ Works | ⬜ |
| CSS Grid | ✓ Works | ⬜ |
| Flexbox | ✓ Works | ⬜ |
| CSS animations | ✓ Smooth | ⬜ |
| Fetch API | ✓ Works | ⬜ |

### 7.2 Firefox

**Test ID:** COMPAT-FF-001

| Feature | Expected | Status |
|---------|----------|--------|
| Layout | ✓ Correct | ⬜ |
| Styling | ✓ Matches | ⬜ |
| JavaScript | ✓ Functional | ⬜ |
| Form inputs | ✓ Accessible | ⬜ |

### 7.3 Safari

**Test ID:** COMPAT-SAF-001

| Feature | Expected | Status |
|---------|----------|--------|
| Gradient backgrounds | ✓ Works | ⬜ |
| CSS Grid | ✓ Works | ⬜ |
| Webkit prefixes | ✓ Applied | ⬜ |
| Mobile scroll | ✓ Smooth | ⬜ |

---

## 8. Error Handling Tests

### 8.1 Network Errors

**Test ID:** ERR-NET-001

```
Test Steps:
1. Open DevTools Network tab
2. Enable "Offline" mode
3. Try loading dashboard
4. Verify error message:
   "Failed to load documents"
5. Check retry mechanism

Expected:
- User-friendly error message
- No cryptic console errors
- Retry option available

Status: ⬜
```

### 8.2 API Errors (500)

**Test ID:** ERR-API-001

```
Test Steps:
1. Mock API to return 500 error
2. Try uploading document
3. Verify error message:
   "Failed to review document"
4. Allow user to retry

Expected:
- Error message displayed
- User can close alert
- User can retry action

Status: ⬜
```

### 8.3 Invalid Data

**Test ID:** ERR-DAT-001

```
Test Steps:
1. API returns invalid data (missing fields)
2. Verify graceful handling:
   - No component crashes
   - Error logged to console
   - User sees friendly message

Expected:
- App doesn't crash
- Console shows error details
- User informed of issue

Status: ⬜
```

---

## Test Summary Report

### Completion Checklist

| Category | Tests | Pass | Fail | Status |
|----------|-------|------|------|--------|
| Component Tests | 15 | ⬜ | ⬜ | 🔄 |
| Integration Tests | 20 | ⬜ | ⬜ | 🔄 |
| Responsive Tests | 12 | ⬜ | ⬜ | 🔄 |
| Performance Tests | 10 | ⬜ | ⬜ | 🔄 |
| Accessibility Tests | 8 | ⬜ | ⬜ | 🔄 |
| Security Tests | 5 | ⬜ | ⬜ | 🔄 |
| Compatibility Tests | 15 | ⬜ | ⬜ | 🔄 |
| Error Handling Tests | 5 | ⬜ | ⬜ | 🔄 |
| **TOTAL** | **90** | ⬜ | ⬜ | 🔄 |

### Pass Rate Target
- **Minimum Required:** 85% (76/90 tests)
- **Production Ready:** 95% (85.5/90 tests)
- **Target:** 100% (90/90 tests)

---

## How to Run Tests

### Manual Testing
```bash
1. npm run dev
2. Open http://localhost:5173
3. Follow test steps in each test ID
4. Mark results (Pass/Fail/Blocked)
5. Document findings
```

### Automated Testing (Future)
```bash
1. npm run test:unit
2. npm run test:integration
3. npm run test:e2e
4. Generate coverage report
```

### Performance Testing
```bash
1. npm run build
2. npm run preview
3. Open Chrome DevTools
4. Record Lighthouse metrics
5. Compare against benchmarks
```

---

## Test Reporting

### Template for Failed Tests

```markdown
**Test ID:** INT-UPLOAD-001
**Component:** DocumentUpload
**Severity:** High
**Status:** ❌ FAILED

**Steps to Reproduce:**
1. Click Upload button
2. Select file > 10MB
3. Observe behavior

**Expected Result:**
Error message: "File too large. Maximum 10MB."

**Actual Result:**
File upload proceeds without validation.

**Proposed Fix:**
Add size validation check before upload.
```

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| QA Lead | __________ | __________ | __________ |
| Dev Lead | __________ | __________ | __________ |
| Product Manager | __________ | __________ | __________ |

---

**Document Version:** 1.0  
**Last Updated:** January 20, 2025  
**Next Review:** After UAT completion

