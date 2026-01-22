# AI Export Feature - Testing Guide

## Prerequisites

### Software Running
- ✅ Backend server on `127.0.0.1:8000`
- ✅ Frontend server on `localhost:3000`
- ✅ Azure Cosmos DB (local emulator or cloud)
- ✅ Azure OpenAI credentials configured

### Test Data Available
- ✅ At least one document uploaded and extracted
- ✅ Document has extracted data ready for review

## Pre-Testing Checklist

```
[ ] Both servers running and accessible
[ ] No console errors in browser DevTools
[ ] No errors in backend terminal
[ ] Document uploaded and extracted successfully
[ ] Can see document in review dashboard
[ ] Backend logs show no critical errors
```

## Test Scenarios

### Scenario 1: Basic AI Review & Export (JSON)

**Objective:** Verify AI processing and JSON export works

**Steps:**
1. Open browser: `http://localhost:3000/login`
2. Login with test account
3. Navigate to document review dashboard (or upload new document)
4. Click "View Details" on a document
5. Verify page loads with extracted data
6. Make one small edit to a field (e.g., change a name)
7. Leave transformation instructions empty
8. Click "🤖 Export with AI Review" button

**Expected Results:**
```
Timing:
⏱️ 0-2s: Shows "AI Processing..." spinner

⏱️ 2-8s: Button disabled, processing continues
        (Check backend logs for AI agent initialization)

⏱️ 8-10s: AI summary section appears with animation
          (Slides in from below)

Content:
✓ Executive Summary populated
✓ Key Findings list appears (with → bullets)
✓ Recommendations list appears (with ✓ bullets)
✓ At least one other section visible
✓ Download format selector shows "json"
✓ "⬇️ Download Report" button visible

Messages:
✓ "✓ AI Review Complete - Ready to Download" message shows
✓ Message auto-dismisses after 4 seconds
```

**Validation:**
```javascript
// Check browser console (F12 → Console)
- No red error messages
- No "undefined" references
- No network errors (status 200)
```

**File Download:**
1. Click "⬇️ Download Report"
2. File downloads: `document_xxxxxxxx_reviewed.json`
3. Open file in text editor
4. Verify structure:
```json
{
  "data": { /* your edited data */ },
  "transformation_instructions": null,
  "ai_review_summary": {
    "executive_summary": "...",
    "key_findings": [...],
    "recommendations": [...],
    "risk_factors": [...],
    "action_items": [...]
  }
}
```

**Pass Criteria:** ✅ AI processes, summary displays, JSON downloads successfully

---

### Scenario 2: Edit Data Before Export

**Objective:** Verify edited data is included in AI review

**Steps:**
1. From Document Review page (from Scenario 1)
2. Scroll to "✏️ Extracted Data (Editable)" section
3. Find a field with text value (e.g., vendor name, description)
4. Click into textarea
5. Make significant change (e.g., "Acme Corp" → "Acme Corp - Updated")
6. Scroll down to "📤 Export & Transform"
7. In "Transformation Instructions" add:
   ```
   Convert all currency amounts to USD using current exchange rates
   ```
8. Click "🤖 Export with AI Review"

**Expected Results:**
```
Before Export:
✓ Data field shows your edit
✓ Transformation instructions text visible
✓ "json" format selected

After Processing:
✓ AI Summary appears
✓ Executive Summary mentions your edit
✓ Recommendations may reference transformation request
✓ Data preserved in export

Downloaded JSON:
✓ "data" field contains your edits
✓ "transformation_instructions" field populated
✓ "ai_review_summary" includes relevant analysis
```

**Pass Criteria:** ✅ Edits and preferences reflected in AI analysis

---

### Scenario 3: Multi-Format Export

**Objective:** Verify all export formats work

**Steps:**
1. From Document Review page with AI summary showing
2. Change format dropdown to "CSV"
3. Click "⬇️ Download Report"
4. Verify `document_xxxxxxxx_reviewed.csv` downloads
5. Repeat with "Excel" (should download `.xlsx`)
6. Repeat with "PDF" (should download `.pdf`)

**Expected Results:**

| Format | Downloaded As | Opens In | Contains |
|--------|---|---|---|
| **JSON** | `.json` | Text editor | Full AI summary + data |
| **CSV** | `.csv` | Excel/Sheets | Flattened data |
| **Excel** | `.xlsx` | Excel | Formatted data |
| **PDF** | `.pdf` | PDF reader | Professional report |

**PDF Specific:**
```
Expected PDF Content:
1. Title: "Document Review Report - [ID]"
2. AI Review Summary section
   - Executive Summary heading + text
   - Key Findings with bullets
   - Recommendations with bullets
   - Risk Factors (if any)
   - Action Items
3. Page break
4. Extracted Data section
   - All key-value pairs listed
   - Formatted readably
```

**Pass Criteria:** ✅ All 4 formats download successfully with correct content

---

### Scenario 4: Error Handling - No AI Credentials

**Objective:** Verify graceful degradation if AI unavailable

**Setup:**
1. Temporarily unset Azure OpenAI env vars:
   ```powershell
   $env:AZURE_OPENAI_ENDPOINT = ""
   $env:AZURE_OPENAI_API_KEY = ""
   ```
2. Restart backend server

**Steps:**
1. Open document review page
2. Click "🤖 Export with AI Review"

**Expected Results:**
```
Option A: AI skipped gracefully
✓ Summary section appears (may be minimal)
✓ Download button works
✓ File downloads successfully
✓ No crash or 500 error

Option B: Error message shown (acceptable)
✓ "AI Agent is not available" message
✓ User can still download without AI summary
✓ Fallback to basic export
```

**Pass Criteria:** ✅ No crash, user can still export

---

### Scenario 5: Network Timeout / Slow AI

**Objective:** Verify timeout handling and loading state

**Steps:**
1. Open DevTools Network tab (F12 → Network)
2. Throttle to "Slow 3G" or offline
3. Click "🤖 Export with AI Review"

**Expected Results:**
```
Immediate:
✓ Shows "⏳ AI Processing..." 
✓ Button disabled

After 5 seconds:
✓ Still shows processing state
✓ No spinner freeze
✓ User can see it's still working

After 15 seconds (timeout):
✓ Either completes with partial summary
✓ Or shows timeout error
✓ But doesn't hang indefinitely
```

**Pass Criteria:** ✅ Handles slow/missing connections gracefully

---

### Scenario 6: Large Document with Complex Data

**Objective:** Verify performance with larger datasets

**Steps:**
1. Upload a document with:
   - 50+ extracted fields
   - Multiple line items (10+)
   - Complex nested data
2. Edit several fields
3. Click "🤖 Export with AI Review"

**Expected Results:**
```
Performance:
⏱️ AI processing: 8-15 seconds (acceptable)
⏱️ UI responsive during processing
⏱️ Download: 1-3 seconds

Results:
✓ All fields shown in summary
✓ No truncation of data
✓ AI handles complexity
✓ File exports completely
✓ No memory issues (check DevTools)
```

**Validation:**
```javascript
// DevTools → Memory tab
- No memory spike > 100MB
- Memory released after export complete
```

**Pass Criteria:** ✅ Handles large datasets without performance degradation

---

### Scenario 7: Mobile Responsive (iPad/Tablet)

**Objective:** Verify mobile layout works

**Setup:**
1. Open DevTools (F12)
2. Click "Toggle device toolbar" (Ctrl+Shift+M)
3. Select "iPad" (768px width)

**Steps:**
1. Navigate to document review page
2. Scroll through all sections
3. Verify layout readable on tablet
4. Click "🤖 Export with AI Review"
5. When summary appears, scroll and verify all sections visible
6. Try download format selector - ensure dropdown works
7. Click "⬇️ Download Report"

**Expected Results:**
```
Layout (Tablet 768px):
✓ All sections readable
✓ No horizontal scrolling
✓ Buttons full width
✓ Text readable without zooming
✓ Form inputs properly sized

Summary Section:
✓ Cards stack vertically
✓ Lists format nicely
✓ Download section clear and functional
✓ Buttons full width

Functionality:
✓ Format selector works
✓ Download triggers correctly
✓ No visual glitches
```

**Pass Criteria:** ✅ Tablet layout responsive and functional

---

### Scenario 8: Mobile Responsive (Phone)

**Objective:** Verify mobile phone layout works

**Setup:**
1. Open DevTools (F12)
2. Select "iPhone 12" (390px width)

**Steps:**
1. Navigate to document review page
2. Scroll through carefully
3. Verify each section readable
4. Test export and download

**Expected Results:**
```
Layout (Mobile 390px):
✓ No horizontal scrolling
✓ Comfortable reading width
✓ Buttons easily tappable (>44px height)
✓ Spacing appropriate
✓ Font sizes readable

Summary on Mobile:
✓ Executive summary visible
✓ Lists scroll-through (not cut off)
✓ Download section accessible
✓ Buttons full width
✓ Format dropdown opens fully

Pass/Fail:
✓ No layout breaks
✓ All content accessible without pinch-zoom
```

**Pass Criteria:** ✅ Mobile layout responsive and usable

---

### Scenario 9: Browser Compatibility

**Objective:** Verify feature works across browsers

**Test Browsers:**
- [ ] Chrome/Chromium (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

**Steps for Each Browser:**
1. Login and navigate to document review
2. Export with AI review
3. Verify summary displays correctly
4. Download in each format
5. Check DevTools console for errors

**Expected Results:**
```
All Browsers:
✓ AI processing works
✓ Summary displays with animations
✓ Download format selector works
✓ Files download correctly
✓ No console errors
✓ Styling looks correct
```

**Known Issues:** (If any)
```
- Safari: May need 10+ seconds for AI (known lag)
- Firefox: Perfect performance
- Chrome: Baseline performance
- Edge: Identical to Chrome
```

**Pass Criteria:** ✅ Works across all major browsers

---

### Scenario 10: Complete User Journey

**Objective:** Full end-to-end workflow test

**Steps:**
```
1. Fresh login
   ↓
2. Upload new document (PDF/Word/Excel)
   ↓
3. Wait for document processing
   ↓
4. Click "View Details"
   ↓
5. See extracted data
   ↓
6. Edit 3-4 fields
   ↓
7. Add transformation instruction
   ↓
8. Click "🤖 Export with AI Review"
   ↓
9. Wait for AI processing (watch loading spinner)
   ↓
10. Review AI summary
    - Read executive summary
    - Check key findings
    - Note recommendations
    - Review risks
    ↓
11. Select PDF format
    ↓
12. Click "⬇️ Download Report"
    ↓
13. Open PDF file
    ↓
14. Verify content matches
    - Document title
    - Your edits included
    - AI summary present
    - Professional formatting
```

**Pass Criteria:** ✅ Entire journey smooth and intuitive

---

## Performance Benchmarks

### Acceptable Timings

```
Operation                           Time        Status
─────────────────────────────────────────────────────
Page load (review dashboard)        <2s         ✓
Load document details               <1s         ✓
AI processing                       3-10s       ✓ (first might be slower)
Summary appears on page             <1s         ✓
Format change & preview             <500ms      ✓
Download trigger                    <500ms      ✓
File download                       1-3s        ✓
─────────────────────────────────────────────────────
```

### Load Testing

```
Test: Simulate 10 concurrent exports
Expected: 
  - No 503 errors
  - No timeouts
  - Response within 15 seconds
  - Backend handles queue gracefully
```

---

## Quality Checklist

### Functionality
- [ ] AI processes document and returns summary
- [ ] All 5 summary sections populate (when applicable)
- [ ] Edit data affects AI analysis
- [ ] Transformation instructions processed
- [ ] All 4 export formats work
- [ ] Files download with correct names
- [ ] No data loss during processing

### User Experience
- [ ] Loading states clear ("AI Processing...")
- [ ] Summary appears with smooth animation
- [ ] UI remains responsive during export
- [ ] Error messages helpful and actionable
- [ ] Mobile layout responsive
- [ ] Buttons clearly labeled with emoji/icons
- [ ] Download button obvious and accessible

### Performance
- [ ] AI processing < 15 seconds
- [ ] No memory leaks
- [ ] Smooth animations (60 FPS)
- [ ] No lag during typing
- [ ] Responsive to user input

### Data Integrity
- [ ] User edits preserved
- [ ] AI summary accurate
- [ ] File content matches expectations
- [ ] No data corruption in export
- [ ] No PII exposed unnecessarily

### Browser Quality
- [ ] No JavaScript errors
- [ ] No console warnings
- [ ] Accessible (keyboard navigation)
- [ ] ARIA labels present
- [ ] Works with screen readers

### Accessibility
- [ ] Keyboard nav works (Tab, Enter, Space)
- [ ] Color not only indicator of status
- [ ] Sufficient contrast ratios
- [ ] Focus states visible
- [ ] Form labels associated

---

## Test Report Template

```markdown
## AI Export Feature - Test Report

**Date:** YYYY-MM-DD
**Tester:** [Name]
**Environment:** Chrome 119 / Windows 11

### Test Results Summary
- **Passed:** X/10 scenarios
- **Failed:** Y/10 scenarios  
- **Blocked:** Z/10 scenarios
- **Overall:** ✅ PASS / ⚠️ PARTIAL / ❌ FAIL

### Scenario Results

#### ✅ Scenario 1: Basic AI Review
- Status: PASS
- Notes: Works as expected
- Time: 8.2 seconds

#### ✅ Scenario 2: Edit Data Before Export  
- Status: PASS
- Notes: Edits reflected in AI summary
- Time: 9.1 seconds

...

### Issues Found
1. [Priority] Description
   - Steps: How to reproduce
   - Expected: What should happen
   - Actual: What happened instead
   
### Recommendations
- Consider adding X feature
- Improve Y performance
- Fix Z bug

### Sign-off
- Tester: [Name]
- Date: YYYY-MM-DD
- Status: Ready for production / Needs fixes
```

---

## Debugging Tips

### Check Backend Logs
```powershell
# Look for:
"Exporting document"
"Processing document with AI"
"AI review completed"
"Export failed"
```

### Check Frontend Console
```javascript
F12 → Console
- Look for red errors
- Check network tab for 500/401 errors
- Verify API calls in Network tab
```

### Test Endpoint Directly
```bash
# Use curl or Postman
POST http://127.0.0.1:8000/api/v1/docs/{id}/export
Content-Type: application/json

{
  "format": "json",
  "data": {"test": "data"},
  "transformation_instructions": "",
  "use_ai_review": true
}
```

### Enable Debug Logging
```python
# In backend main.py
logging.getLogger().setLevel(logging.DEBUG)
```

---

## Sign-Off

```
Feature: AI Export with Intelligent Document Review
Version: 1.0.0
Test Date: [Date]
Tester: [Name]
Status: ✅ Ready for Production

Signature: _______________________
Date: _______________________
```

