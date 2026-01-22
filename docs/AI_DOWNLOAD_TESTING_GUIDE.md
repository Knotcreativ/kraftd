# Testing Guide - AI-Powered Download Feature

## Quick Start

### Start the Servers

**Terminal 1 - Backend:**
```bash
cd c:\Users\1R6\OneDrive\Project\ Catalyst\KraftdIntel\backend
.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd c:\Users\1R6\OneDrive\Project\ Catalyst\KraftdIntel\frontend
npm run dev
```

Backend: `http://127.0.0.1:8000`
Frontend: `http://localhost:3000`

---

## Test Scenario 1: Standard Template Export

### Steps
1. Open `http://localhost:3000/login`
2. Create a test account:
   - Email: `test@example.com`
   - Password: `SecurePass123`
   - Name: Test User
   - Accept terms/privacy
3. Click "Create Account"
4. Login with credentials
5. Upload a PDF document
6. View document details
7. Edit some fields (optional)
8. Click **"🤖 Export with AI Review"** button
9. Wait 8-12 seconds for AI to process
10. See AI summary appear with sections:
    - Executive Summary
    - Key Findings
    - Recommendations
    - Risk Factors
    - Action Items
11. In "Document Template" section:
    - **Standard** option should be pre-selected (blue highlight)
12. In "Download Format" dropdown:
    - Select **"PDF"**
13. Click **"⬇️ Download Report"** button
14. Wait 5-8 seconds for file generation
15. See success message: `✓ File downloaded as PDF (standard template)`

### Expected Results
- ✅ File downloads to browser
- ✅ Filename: `{docid}_standard_{date}.pdf`
- ✅ File opens in PDF reader
- ✅ Contains title, AI summary, and data sections
- ✅ Professional formatting applied

---

## Test Scenario 2: Executive Summary Template Export

### Steps
1. Same document from Scenario 1 already open
2. In "Document Template" section:
   - Select **"👔 Executive Summary"** radio button
   - Should show blue border and gradient background
3. Keep format as **"PDF"**
4. Click **"⬇️ Download Report"**
5. Wait for processing

### Expected Results
- ✅ File downloads with name: `{docid}_executive_summary_{date}.pdf`
- ✅ PDF is 1-2 pages (concise)
- ✅ Contains high-level overview only
- ✅ AI formatted for executives

---

## Test Scenario 3: Custom Template Export

### Steps
1. Same document still open
2. In "Document Template" section:
   - Select **"✨ Custom"** radio button
3. Custom textarea appears with placeholder:
   - `"e.g., 'Create a single-page summary with key metrics in table format, followed by action items'"`
4. Enter custom instructions:
   ```
   Create a single-page summary focusing on key metrics and risks, 
   presented in a table format. Include only critical action items at the end.
   ```
5. Format: Select **"PDF"**
6. Click **"⬇️ Download Report"**
7. Wait for AI to process and apply custom template

### Expected Results
- ✅ File downloads: `{docid}_custom_{date}.pdf`
- ✅ Follows custom formatting instructions
- ✅ Single page with table format
- ✅ Only action items included

---

## Test Scenario 4: JSON Format Export

### Steps
1. Same document still open
2. Template: Select **"Standard"** (or any)
3. Format: Select **"JSON"** from dropdown
4. Click **"⬇️ Download Report"**
5. File downloads

### Expected Results
- ✅ File: `{docid}_standard_{date}.json`
- ✅ Contains structured metadata:
  ```json
  {
    "metadata": {
      "document_id": "...",
      "template": "standard",
      "timestamp": "2024-01-18T...",
      "format": "json"
    },
    "data": { ... },
    "ai_review_summary": { ... }
  }
  ```
- ✅ Can be parsed and imported

---

## Test Scenario 5: Excel Format Export

### Steps
1. Same document still open
2. Template: **"Financial Report"**
3. Format: **"Excel"**
4. Click download
5. Open downloaded file in Excel

### Expected Results
- ✅ File: `{docid}_financial_report_{date}.xlsx`
- ✅ Opens in Excel/Sheets
- ✅ Data formatted in rows/columns
- ✅ Ready for analysis

---

## Test Scenario 6: CSV Format Export

### Steps
1. Same document open
2. Template: **"Detailed Analysis"**
3. Format: **"CSV"**
4. Click download
5. Open in text editor or Excel

### Expected Results
- ✅ File: `{docid}_detailed_analysis_{date}.csv`
- ✅ Contains properly formatted CSV data
- ✅ Headers and values separated
- ✅ Importable to any spreadsheet tool

---

## Test Scenario 7: Mobile Responsiveness

### Steps
1. Open browser DevTools (F12)
2. Toggle device toolbar (mobile view)
3. Test on different sizes:
   - iPhone 12 (390px)
   - iPad (768px)
   - Large desktop (1200px+)
4. Verify layout adjustments:
   - Template grid stacks properly
   - Buttons are full width on mobile
   - Text is readable
   - No horizontal scroll

### Expected Results
- ✅ Template grid responsive
- ✅ Dropdown works on mobile
- ✅ Download button accessible
- ✅ Text size appropriate for device

---

## Test Scenario 8: Error Handling - Invalid Data

### Steps
1. Upload document with very limited/corrupt data
2. Click export
3. Try to download anyway

### Expected Results
- ✅ System handles gracefully
- ✅ Error message displays
- ✅ No browser crash
- ✅ User can retry

---

## Test Scenario 9: Error Handling - AI Unavailable

### Steps
1. (Simulate by temporarily disabling AI service)
2. Click export with AI review
3. Wait for response

### Expected Results
- ✅ System falls back to basic export
- ✅ Shows message about AI being unavailable
- ✅ File still downloads
- ✅ No critical errors

---

## Test Scenario 10: Large Document

### Steps
1. Upload large document (10+ pages)
2. Extract and review
3. Click export
4. Select template and format
5. Monitor processing time

### Expected Results
- ✅ Processing takes 15-20 seconds total
- ✅ Loading state shows progress
- ✅ File generates successfully
- ✅ Output quality maintained

---

## Test Scenario 11: Multiple Downloads

### Steps
1. Same document open
2. Download as PDF (Standard)
   - Wait for file
3. Download as Excel (Executive Summary)
   - Wait for file
4. Download as JSON (Custom)
   - Wait for file
5. Check all 3 files in downloads folder

### Expected Results
- ✅ All 3 files present
- ✅ Different names with templates
- ✅ Different formats correct
- ✅ No conflicts or overwrites

---

## Test Scenario 12: Different Document Types

### Steps
1. Upload different document types:
   - Procurement document
   - Invoice
   - Contract
   - Report
2. For each, test export with different templates
3. Verify AI adapts to document type

### Expected Results
- ✅ Each document type handled
- ✅ AI summary reflects content type
- ✅ Template formatting appropriate
- ✅ Output quality consistent

---

## Test Scenario 13: UI Interaction

### Steps
1. Hover over template options
   - Should show hover effect
   - Border highlights
   - Background slightly changes
2. Click radio button
   - Should select (blue highlight)
   - If Custom, textarea appears
   - If not Custom, textarea disappears
3. Edit custom instructions
   - Text updates
   - No validation issues
4. Select format dropdown
   - All 4 options visible
   - Selection works
   - Current selection shows

### Expected Results
- ✅ All hover effects work
- ✅ Radio buttons toggle correctly
- ✅ Custom textarea shows/hides properly
- ✅ Dropdown functional
- ✅ Button states correct (enabled/disabled)

---

## Test Scenario 14: Data Privacy

### Steps
1. Export document with sensitive data
2. Check downloaded file
3. Verify no unintended copies made
4. Check browser storage
5. Verify no cached sensitive data

### Expected Results
- ✅ File contains only intended data
- ✅ No temporary files left
- ✅ localStorage clean
- ✅ Session data cleared
- ✅ No sensitive info exposed

---

## Visual Checklist

### On Screen Elements
- [ ] AI Summary section displays all 5 cards
- [ ] Executive Summary card visible
- [ ] Key Findings card with bullet points
- [ ] Recommendations card with bullet points
- [ ] Risk Factors card in red (⚠️)
- [ ] Action Items card in green (✅)
- [ ] "Document Template" heading visible
- [ ] 6 template options showing
- [ ] Templates have icons (📄👔🔬💰⚙️✨)
- [ ] Template descriptions visible
- [ ] Format dropdown shows 4 options
- [ ] Download button visible
- [ ] Loading state works

### File Output Verification
- [ ] Filename includes doc ID
- [ ] Filename includes template name
- [ ] Filename includes date
- [ ] File extension correct (.pdf/.json/.csv/.xlsx)
- [ ] File size reasonable (not empty)
- [ ] File opens correctly
- [ ] Content readable
- [ ] Formatting applied

---

## Performance Benchmarks

### Expected Timing

| Phase | Operation | Duration |
|-------|-----------|----------|
| 1 | AI analysis | 8-12 sec |
| 2 | Template generation | 5-8 sec |
| 2 | File format conversion | 1-3 sec |
| 2 | Browser download | <1 sec |
| **Total** | Full flow | ~15-20 sec |

### Acceptable Performance
- ✅ AI response: <15 seconds
- ✅ File download: <20 seconds
- ✅ UI responsive throughout
- ✅ No timeout errors

---

## Browser Testing Matrix

Test on each browser combination:

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | Latest | Should work |
| Firefox | Latest | Should work |
| Safari | Latest | Should work |
| Edge | Latest | Should work |

### Test Actions Per Browser
- [ ] Export with AI Review
- [ ] Template selection works
- [ ] Format selection works
- [ ] Download file
- [ ] Open downloaded file
- [ ] Verify content

---

## Test Summary Form

Use this checklist to track testing:

```
Feature: AI-Powered Download & Template Generation
Date: _______________
Tester: _______________

Scenario 1 (Standard): [ ] PASS [ ] FAIL - Notes: ___________
Scenario 2 (Executive): [ ] PASS [ ] FAIL - Notes: ___________
Scenario 3 (Custom): [ ] PASS [ ] FAIL - Notes: ___________
Scenario 4 (JSON): [ ] PASS [ ] FAIL - Notes: ___________
Scenario 5 (Excel): [ ] PASS [ ] FAIL - Notes: ___________
Scenario 6 (CSV): [ ] PASS [ ] FAIL - Notes: ___________
Scenario 7 (Mobile): [ ] PASS [ ] FAIL - Notes: ___________
Scenario 8 (Errors): [ ] PASS [ ] FAIL - Notes: ___________
Scenario 9 (AI Down): [ ] PASS [ ] FAIL - Notes: ___________
Scenario 10 (Large): [ ] PASS [ ] FAIL - Notes: ___________
Scenario 11 (Multiple): [ ] PASS [ ] FAIL - Notes: ___________
Scenario 12 (Doc Types): [ ] PASS [ ] FAIL - Notes: ___________
Scenario 13 (UI): [ ] PASS [ ] FAIL - Notes: ___________
Scenario 14 (Privacy): [ ] PASS [ ] FAIL - Notes: ___________

Overall Result: [ ] PASS [ ] FAIL

Critical Issues: _______________
Minor Issues: _______________
Suggestions: _______________

Ready for Deployment: [ ] YES [ ] NO
```

---

## Troubleshooting During Tests

### Issue: AI Summary not appearing
**Solution:**
- Check backend logs for AI errors
- Verify KraftdAIAgent is initialized
- Check document has data to analyze

### Issue: Template selection not responding
**Solution:**
- Check browser console (F12) for errors
- Verify CSS loaded correctly
- Clear browser cache

### Issue: Download not starting
**Solution:**
- Check file generation in backend logs
- Verify format selection
- Check browser download settings

### Issue: Downloaded file empty
**Solution:**
- Check backend export logic
- Verify data was edited
- Check file format compatibility

### Issue: Mobile layout broken
**Solution:**
- Check viewport settings
- Verify CSS media queries
- Test on real device, not just DevTools

---

## Success Criteria

✅ **Feature is ready if:**
- All 14 test scenarios PASS
- All file formats work correctly
- All templates generate properly
- Mobile responsive works
- Error handling works
- Performance meets benchmarks
- No TypeScript errors (cache OK)
- No console errors
- User can complete flow easily

---

**Start testing!** 🚀

Use this guide to verify the AI-Powered Download feature works as expected.

Questions? Check the main documentation: `AI_POWERED_DOWNLOAD_FEATURE.md`
