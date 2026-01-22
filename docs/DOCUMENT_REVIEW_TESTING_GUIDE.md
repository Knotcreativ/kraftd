# Document Review Dashboard - Testing Guide

**Date**: January 18, 2026
**Feature**: Document Review with Editable Data & Export
**Version**: 1.0
**Test Duration**: ~15 minutes

---

## Pre-Test Setup

### 1. Start Backend Server

```powershell
# Open PowerShell Terminal
cd "c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel\backend"

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install optional export packages (if not already installed)
pip install pandas openpyxl reportlab

# Start the server
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Expected Output**:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Start Frontend Server

```powershell
# Open another PowerShell Terminal
cd "c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel\frontend"

# Install dependencies (if first run)
npm install

# Start dev server
npm run dev
```

**Expected Output**:
```
Local:   http://localhost:3000/
```

### 3. Open Browser

Visit: `http://localhost:3000`

---

## Test Scenario 1: Navigation to Review Dashboard

### Prerequisites
- Both servers running
- User logged in

### Steps
1. Click "Dashboard" in navigation
2. Scroll to "Uploaded Documents" section
3. Verify document list displays
4. Find a document with status "✓ completed" or "⏳ processing"

### Expected Results
- ✅ Dashboard page loads
- ✅ Document list visible with status badges
- ✅ "View Details" button visible on each card

---

## Test Scenario 2: View Document Details

### Prerequisites
- Document list visible
- At least one completed/processed document

### Steps
1. Click "👁️ View Details" on a document card
2. Wait for page to load

### Expected Results
- ✅ URL changes to `/dashboard/review/{documentId}`
- ✅ Page title: "📋 Document Review"
- ✅ Back button visible
- ✅ Loading spinner briefly shows then disappears

---

## Test Scenario 3: Verify Dashboard Display

### Prerequisites
- Review dashboard loaded
- Document details visible

### Steps
1. Scroll down the page
2. Verify each section displays

### Expected Results

**Header Section** ✅
- Back button (works)
- Document Review title
- Status badge

**Summary Section** ✅
- Document Type field
- Processing Time (in ms)
- Completeness Score (with progress bar)
- Quality Score (with progress bar)

**Metrics Section** ✅
- Fields Mapped count
- Inferences Made count
- Line Items count
- Parties Found count

**Extracted Data Section** ✅
- "✏️ Extracted Data (Editable)" heading
- List of editable fields
- Each field has a textarea or input
- All extracted data values visible

**Export/Transform Section** ✅
- Format dropdown (4 options: JSON, CSV, Excel, PDF)
- Transformation Instructions textarea
- "📥 Export Document" button

---

## Test Scenario 4: Edit Extracted Data

### Prerequisites
- Review dashboard loaded
- Extracted data section visible

### Steps
1. Find a text field in the data section (e.g., invoice_number)
2. Click in the field
3. Modify the value (add "TEST" to the value)
4. Click another field to defocus
5. Verify the change is retained

### Expected Results
- ✅ Field shows blue focus outline when clicked
- ✅ Text can be entered/modified
- ✅ Change persists when focus moves away
- ✅ No error messages shown

---

## Test Scenario 5: Export as JSON

### Prerequisites
- Review dashboard loaded
- Data visible

### Steps
1. Format dropdown default shows "JSON"
2. Click "📥 Export Document" button
3. Wait for download to complete
4. Check browser downloads folder

### Expected Results
- ✅ Button shows "⏳ Exporting..." during processing
- ✅ Success message shows: "✓ Document exported as JSON"
- ✅ File downloads with name pattern: `document_XXXXXXXX.json`
- ✅ File size > 0 bytes
- ✅ Message auto-dismisses after ~4 seconds

### Verification
```powershell
# Check file was downloaded
Get-ChildItem "$env:USERPROFILE\Downloads" -Filter "document_*.json" -ErrorAction SilentlyContinue | 
  Select-Object Name, Length | 
  Sort-Object -Property CreationTime -Descending | 
  Select-Object -First 1
```

---

## Test Scenario 6: Export as CSV

### Prerequisites
- Review dashboard loaded
- Format dropdown available

### Steps
1. Click format dropdown
2. Select "CSV"
3. Click "📥 Export Document"
4. Wait for download

### Expected Results
- ✅ Dropdown shows "CSV" selected
- ✅ Button shows loading state
- ✅ File downloads: `document_XXXXXXXX.csv`
- ✅ File is comma-separated text
- ✅ Can open in Excel or text editor

### File Verification
```powershell
# Open CSV file to verify content
$lastCsv = Get-ChildItem "$env:USERPROFILE\Downloads" -Filter "document_*.csv" -ErrorAction SilentlyContinue | Sort-Object CreationTime -Descending | Select-Object -First 1
if ($lastCsv) {
  Get-Content $lastCsv.FullName | Select-Object -First 5
}
```

---

## Test Scenario 7: Export as Excel

### Prerequisites
- Review dashboard loaded
- pandas/openpyxl installed on backend

### Steps
1. Click format dropdown
2. Select "Excel (XLSX)"
3. Click "📥 Export Document"
4. Wait for download

### Expected Results
- ✅ Dropdown shows "Excel (XLSX)" selected
- ✅ Export takes ~500ms (slightly longer than JSON/CSV)
- ✅ File downloads: `document_XXXXXXXX.xlsx`
- ✅ File can open in Excel/Sheets
- ✅ Data displays in cells

### File Verification
```powershell
# Verify Excel file exists
$lastXlsx = Get-ChildItem "$env:USERPROFILE\Downloads" -Filter "document_*.xlsx" -ErrorAction SilentlyContinue | 
  Sort-Object CreationTime -Descending | 
  Select-Object -First 1
if ($lastXlsx) {
  Write-Host "Excel file: $($lastXlsx.Name) - Size: $($lastXlsx.Length) bytes"
}
```

---

## Test Scenario 8: Export as PDF

### Prerequisites
- Review dashboard loaded
- reportlab installed on backend

### Steps
1. Click format dropdown
2. Select "PDF"
3. Click "📥 Export Document"
4. Wait for download

### Expected Results
- ✅ Dropdown shows "PDF" selected
- ✅ Export takes ~1000ms (longest format)
- ✅ File downloads: `document_XXXXXXXX.pdf`
- ✅ File can open in PDF reader
- ✅ Contains document title and data

---

## Test Scenario 9: Transformation Instructions

### Prerequisites
- Review dashboard loaded
- Export section visible

### Steps
1. Click "Transformation Instructions" textarea
2. Type: "Convert amounts to USD"
3. Select JSON format
4. Click Export

### Expected Results
- ✅ Text enters the textarea
- ✅ Export proceeds normally
- ✅ Backend receives transformation instruction
- ✅ File exports (transformation applies in backend)

---

## Test Scenario 10: Error Handling - Invalid Document

### Prerequisites
- Browser at dashboard

### Steps
1. Manually enter URL: `http://localhost:3000/dashboard/review/invalid-id-123`
2. Wait for page load

### Expected Results
- ✅ Error state displays
- ✅ Message: "Error Loading Document"
- ✅ Error detail: "Document not found"
- ✅ "← Back to Dashboard" button visible and working

---

## Test Scenario 11: Mobile Responsiveness - Tablet

### Prerequisites
- Browser DevTools open
- Review dashboard loaded

### Steps
1. Open DevTools (F12)
2. Click "Toggle Device Toolbar" (mobile icon)
3. Select "iPad" (768px width)
4. Reload page (Ctrl+R)
5. Scroll and verify layout

### Expected Results
- ✅ Header adapts to tablet width
- ✅ Summary grid shows 2 columns
- ✅ Buttons remain clickable
- ✅ No horizontal scroll needed
- ✅ Text readable without zoom

---

## Test Scenario 12: Mobile Responsiveness - Phone

### Prerequisites
- Browser DevTools open
- Review dashboard loaded

### Steps
1. DevTools still open
2. Select "iPhone 12" (390px width)
3. Reload page
4. Scroll and verify layout

### Expected Results
- ✅ Header stacks vertically
- ✅ Summary grid shows 1 column
- ✅ Buttons full width
- ✅ Font size readable
- ✅ Tap targets >= 48px
- ✅ No content cut off

---

## Test Scenario 13: Back Button Navigation

### Prerequisites
- Review dashboard loaded

### Steps
1. Click "← Back" button in header
2. Wait for navigation

### Expected Results
- ✅ URL changes back to `/dashboard`
- ✅ Document list visible
- ✅ Document still in list with updated status
- ✅ History works (browser back button)

---

## Test Scenario 14: Data Persistence Across Edits

### Prerequisites
- Review dashboard loaded
- Multiple editable fields visible

### Steps
1. Edit field A: Change "Invoice" to "Invoice-EDITED"
2. Edit field B: Change "Amount" to "999.99"
3. Scroll to bottom (export section)
4. Scroll back to data section
5. Verify changes still present

### Expected Results
- ✅ Field A still shows "Invoice-EDITED"
- ✅ Field B still shows "999.99"
- ✅ No data lost during scroll
- ✅ Component state maintained

---

## Test Scenario 15: Loading State Verification

### Prerequisites
- Browser Network tab open (DevTools)
- Review dashboard loaded

### Steps
1. Observe Network tab while page initially loads
2. Note API call to `/api/v1/docs/{id}`
3. Verify response headers and timing

### Expected Results
- ✅ GET request to correct endpoint
- ✅ Response status: 200 OK
- ✅ Response time: ~200-500ms
- ✅ Content-Type: application/json
- ✅ Response size: 10-50KB

---

## Test Scenario 16: Export API Call Verification

### Prerequisites
- Browser Network tab open
- Review dashboard loaded

### Steps
1. Click Export button (any format)
2. Check Network tab
3. Find the POST request to `/docs/{id}/export`

### Expected Results
- ✅ Method: POST
- ✅ URL: `/api/v1/docs/{documentId}/export`
- ✅ Request includes format, data, instructions
- ✅ Response Status: 200 OK
- ✅ Response Type: Depends on format
  - JSON: application/json
  - CSV: text/csv
  - XLSX: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
  - PDF: application/pdf

---

## Test Scenario 17: Complete Workflow Test

### Prerequisites
- Fresh browser session
- Clean downloads folder

### Steps
1. Open Dashboard
2. Upload a new PDF document
3. Wait for processing (Review button enabled)
4. Click Review button
5. Wait for processing to complete
6. Click View Details
7. Verify dashboard displays
8. Edit 2-3 fields
9. Select Excel format
10. Add transformation instruction
11. Click Export
12. Verify file downloads
13. Click Back button
14. Verify back on dashboard

### Expected Results
- ✅ All 14 steps complete without errors
- ✅ File downloaded successfully
- ✅ No error messages shown
- ✅ Navigation smooth and responsive

---

## Test Scenario 18: Concurrent Exports

### Prerequisites
- Review dashboard loaded
- Export button clickable

### Steps
1. Click Export (JSON) - wait 2 seconds
2. While downloading, click Export (CSV)
3. Verify both downloads complete

### Expected Results
- ✅ Both exports queue properly
- ✅ Both files download
- ✅ No race conditions
- ✅ No errors thrown

---

## Browser Console Testing

### Steps
1. Open DevTools Console (F12)
2. Go through test scenarios 1-17
3. Observe console for errors

### Expected Results
- ✅ No JavaScript errors
- ✅ No TypeScript type errors
- ✅ No network errors (unless intentional)
- ✅ No warning messages (except possibly vendor warnings)

### Commands to Test
```javascript
// Check if API client is available
typeof apiClient

// Check if routes work
window.location.pathname

// Check localStorage (should have token)
localStorage.getItem('accessToken')

// Verify component mounted
document.querySelector('.review-detail-container')
```

---

## Performance Testing

### Metrics to Monitor
1. **Initial Load Time**: Should be < 1 second
2. **Export JSON Time**: Should be < 200ms
3. **Export CSV Time**: Should be < 300ms
4. **Export Excel Time**: Should be < 700ms
5. **Export PDF Time**: Should be < 1500ms

### How to Measure
```powershell
# Using PowerShell to test backend response time
$uri = "http://127.0.0.1:8000/api/v1/docs/{documentId}"
$timer = [System.Diagnostics.Stopwatch]::StartNew()
$response = Invoke-WebRequest -Uri $uri -Headers @{"Authorization"="Bearer YOUR_TOKEN"}
$timer.Stop()
Write-Host "Response time: $($timer.ElapsedMilliseconds)ms"
```

---

## Test Results Template

```
TEST SCENARIO: [Name]
Date: [Date]
Tester: [Name]

✅ PASSED / ❌ FAILED / ⚠️ PARTIAL

Details:
- Step 1: ✅ PASS
- Step 2: ✅ PASS
- Step 3: ✅ PASS

Issues Found:
(None / List any)

Notes:
(Additional observations)
```

---

## Success Criteria

### All Tests Must Pass
- ✅ Navigation to review dashboard
- ✅ Display of all data sections
- ✅ Editing data fields
- ✅ Export in JSON format
- ✅ Export in CSV format
- ✅ Export in Excel format
- ✅ Export in PDF format
- ✅ Error handling for missing documents
- ✅ Mobile responsive on tablet
- ✅ Mobile responsive on phone
- ✅ Back button navigation
- ✅ Data persistence during scroll
- ✅ API calls correct
- ✅ No console errors
- ✅ Performance within limits

### Production Readiness
- ✅ All 18 test scenarios pass
- ✅ No TypeScript errors
- ✅ No runtime errors in console
- ✅ File exports complete successfully
- ✅ User can complete full workflow
- ✅ Mobile works without issues
- ✅ Backend responds correctly
- ✅ Documentation complete

---

## Troubleshooting During Testing

### Backend Won't Start
```powershell
# Check if port 8000 is in use
netstat -ano | Select-String ":8000"

# Kill process using port
taskkill /PID [PID] /F

# Restart backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Frontend Won't Start
```powershell
# Clear node_modules and reinstall
rm -r node_modules
npm install
npm run dev
```

### Exports Failing
```powershell
# Check if dependencies installed
.venv\Scripts\python.exe -m pip list | Select-String "pandas|openpyxl|reportlab"

# Install missing dependencies
pip install pandas openpyxl reportlab
```

### API Returns 404
- Verify document ID in URL
- Check document was processed
- Verify backend is running
- Check network tab for correct URL

### File Won't Download
- Check browser download settings
- Verify file size > 0
- Check Content-Disposition header
- Try different format

---

## Sign-Off

After completing all tests:

```
✅ Feature Testing Complete
✅ All 18 Test Scenarios: PASSED
✅ Mobile Responsive: VERIFIED
✅ No Critical Issues Found
✅ Production Ready

Tested By: [Your Name]
Date: [Date]
Duration: [Time]

Recommendation: ✅ READY FOR DEPLOYMENT
```

---

**Test Duration**: ~15 minutes (all scenarios)
**Success Rate**: Should be 100%
**Next Step**: Deploy to production after sign-off
