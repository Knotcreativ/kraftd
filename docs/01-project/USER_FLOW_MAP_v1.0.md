# User Flow & Journey Map

**Version:** 1.0  
**Status:** APPROVED  
**Last Updated:** 2026-01-17  
**Maintained In:** `/docs/01-project/USER_FLOW_MAP_v1.0.md`

---

## User Journeys Overview

### Journey 1: Procurement Officer - Process RFQ

```
LOGIN
  ↓
DASHBOARD
  ├─ View all documents
  ├─ See recent uploads
  ├─ Check workflow status
  ↓
UPLOAD DOCUMENT
  ├─ Select PDF/Word/Excel
  ├─ File validation
  ├─ Upload progress
  ↓
DOCUMENT DETAIL
  ├─ View extracted content
  ├─ Review line items
  ├─ Verify extraction accuracy
  ├─ Edit fields if needed
  ├─ Confirm extraction complete
  ↓
START WORKFLOW
  ├─ Create estimation
  ├─ Add specifications
  ├─ Assign to manager
  ↓
VIEW WORKFLOW STATUS
  ├─ See workflow steps
  ├─ Track progress
  ├─ Monitor timelines
  ↓
LOGOUT
```

**Time per flow:** 2-5 minutes  
**Key screens:** Dashboard → Upload → Detail → Workflow  
**Decision points:** Edit extracted data? Start workflow? Download?

---

### Journey 2: Procurement Manager - Compare & Approve Quotes

```
LOGIN
  ↓
DASHBOARD
  ├─ View assigned quotations
  ├─ See pending approvals
  ├─ Check comparison requests
  ↓
QUOTATION UPLOAD (Alternate: Receive uploaded quotes)
  ├─ Upload quotation 1
  ├─ Upload quotation 2
  ├─ Upload quotation 3 (optional)
  ↓
COMPARISON VIEW
  ├─ System extracts pricing from each
  ├─ Display side-by-side table
  ├─ Show normalized costs
  ├─ Show scoring/recommendation
  ├─ Review supplier details
  ↓
APPROVE/REJECT QUOTES
  ├─ Select winning quotation
  ├─ Add approval notes
  ├─ Route to procurement officer
  ↓
CREATE PO (Optional - if approved)
  ├─ System pre-fills from quotation
  ├─ Review PO details
  ├─ Add special terms
  ├─ Download PO (PDF/Excel)
  ↓
EXPORT RESULTS
  ├─ Download comparison summary
  ├─ Download recommendation report
  ↓
LOGOUT
```

**Time per flow:** 5-15 minutes  
**Key screens:** Dashboard → Upload → Comparison → Approval → Export  
**Decision points:** Which quotation wins? Generate PO? Export?

---

### Journey 3: Finance Director - Audit & Compliance

```
LOGIN
  ↓
DASHBOARD
  ├─ View all workflows
  ├─ See completed POs
  ├─ Check audit trail
  ↓
SEARCH DOCUMENT
  ├─ Search by date range
  ├─ Filter by document type
  ├─ Filter by status
  ├─ Filter by vendor
  ↓
DOCUMENT DETAIL (Read-only)
  ├─ View extracted data
  ├─ Review workflow history
  ├─ Check approval chain
  ├─ View edit history
  ↓
EXPORT FOR AUDIT
  ├─ Export document + metadata
  ├─ Export workflow history
  ├─ Export approval records
  ↓
LOGOUT
```

**Time per flow:** 5-10 minutes  
**Key screens:** Dashboard → Search → Detail → Export  
**Decision points:** Which documents to audit? Export format?

---

## Screen-by-Screen Flow

### Screen 1: Login
```
┌─────────────────────────────────┐
│         KRAFTDINTEL LOGIN       │
│                                 │
│  Email: [_______________]       │
│  Password: [_______________]    │
│                                 │
│  [LOGIN]  [FORGOT PASSWORD]     │
│                                 │
└─────────────────────────────────┘
         ↓
    Validate credentials
         ↓
    Create session
         ↓
    Redirect to Dashboard
```

**Error Handling:**
- Invalid email → "Invalid email format"
- Invalid credentials → "Email or password incorrect"
- Account locked → "Too many login attempts"

---

### Screen 2: Dashboard
```
┌──────────────────────────────────────┐
│  DASHBOARD                  [Logout] │
├──────────────────────────────────────┤
│                                      │
│  Quick Stats:                        │
│  Documents: 12  |  Workflows: 5     │
│                                      │
│  [+ Upload New Document]             │
│                                      │
│  Recent Documents:                   │
│  ┌──────────────────────────────┐   │
│  │ RFQ_2026_001.pdf             │   │
│  │ Date: 2026-01-15 | Status: ✓ │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │ Quote_ABC_Corp.xlsx          │   │
│  │ Date: 2026-01-14 | Status: ⏳ │   │
│  └──────────────────────────────┘   │
│                                      │
│  Active Workflows:                   │
│  ┌──────────────────────────────┐   │
│  │ RFQ_2026_001: Quotation      │   │
│  │ Step 3 of 5 | Due: 2026-01-20│   │
│  └──────────────────────────────┘   │
│                                      │
└──────────────────────────────────────┘
         ↓
    [Click on document]
         ↓
    View Document Detail
```

**User Actions:**
- Click document → View detail
- Click [+Upload] → Upload modal
- Click workflow → Workflow detail
- Sort/filter → Update list

---

### Screen 3: Upload Document
```
┌──────────────────────────────────┐
│  UPLOAD DOCUMENT                 │
├──────────────────────────────────┤
│                                  │
│  [Drag file or click to browse]  │
│                                  │
│  Supported: PDF, Word, Excel     │
│  Max size: 5MB                   │
│                                  │
│  File: RFQ_2026_001.pdf [✓]     │
│  Size: 1.2MB                     │
│                                  │
│  Extracting... [████████░░] 80%  │
│                                  │
│  [CANCEL]  [EXTRACT & CONTINUE]  │
│                                  │
└──────────────────────────────────┘
         ↓
    Document uploaded
         ↓
    Auto-extract started
         ↓
    Redirect to Detail
```

**States:**
- Empty → "Drag to upload"
- Uploading → "Uploading... 50%"
- Extracting → "Extracting... 80%"
- Complete → "Extraction complete ✓"

---

### Screen 4: Document Detail
```
┌─────────────────────────────────────────┐
│  DOCUMENT: RFQ_2026_001.pdf             │
├─────────────────────────────────────────┤
│                                         │
│  Status: ✓ Extracted  Confidence: 96%  │
│                                         │
│  Original File: [View PDF]              │
│                                         │
│  EXTRACTED DATA:                        │
│  ┌─────────────────────────────────┐   │
│  │ Project: Website Redesign       │   │
│  │ [Edit]                          │   │
│  │                                 │   │
│  │ Required by: 2026-02-15         │   │
│  │ [Edit]                          │   │
│  │                                 │   │
│  │ Budget: $50,000                 │   │
│  │ [Edit]                          │   │
│  │                                 │   │
│  │ Line Items (3):                 │   │
│  │ 1. Frontend development (100h)  │   │
│  │ 2. Backend development (80h)    │   │
│  │ 3. Testing & QA (40h)           │   │
│  │ [Edit]                          │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ACTIONS:                               │
│  [Start Workflow] [Download] [Delete]  │
│                                         │
└─────────────────────────────────────────┘
```

**Interactions:**
- Click [Edit] → Edit field inline
- Click [Start Workflow] → Create workflow
- Click [Download] → Download PDF
- Change confidence → Update data quality

---

### Screen 5: Quote Comparison
```
┌───────────────────────────────────────────┐
│  QUOTATION COMPARISON                     │
├───────────────────────────────────────────┤
│                                           │
│  Comparing 3 quotations for Website Dev  │
│                                           │
│  ┌─────────────┬───────────┬───────────┐ │
│  │ Item        │ Vendor A  │ Vendor B  │ │
│  ├─────────────┼───────────┼───────────┤ │
│  │ Frontend    │ $15,000   │ $18,000   │ │
│  │ Backend     │ $12,000   │ $10,000   │ │
│  │ QA Testing  │ $5,000    │ $6,000    │ │
│  ├─────────────┼───────────┼───────────┤ │
│  │ TOTAL       │ $32,000   │ $34,000   │ │
│  │ Timeline    │ 8 weeks   │ 10 weeks  │ │
│  │ Support     │ 6 months  │ 12 months │ │
│  └─────────────┴───────────┴───────────┘ │
│                                           │
│  SCORING:                                 │
│  Vendor A: 9.2/10 ⭐ RECOMMENDED         │
│  Vendor B: 8.1/10                        │
│                                           │
│  ACTIONS:                                 │
│  [Approve A] [Approve B] [Request More]  │
│  [Download Comparison] [Export Report]   │
│                                           │
└───────────────────────────────────────────┘
```

**Actions:**
- Click [Approve X] → Set winning quotation
- Click [Download] → Export comparison as PDF
- Click [Export Report] → Excel with all details

---

### Screen 6: Create PO
```
┌────────────────────────────────────────┐
│  CREATE PURCHASE ORDER                 │
├────────────────────────────────────────┤
│                                        │
│  Source: Quotation from Vendor A       │
│                                        │
│  PURCHASE ORDER DETAILS:               │
│  ┌──────────────────────────────────┐ │
│  │ PO Number: PO-2026-001           │ │
│  │ [Edit]                           │ │
│  │                                  │ │
│  │ Vendor: Vendor A                 │ │
│  │ Contact: john@vendora.com        │ │
│  │                                  │ │
│  │ Line Items:                      │ │
│  │ 1. Frontend dev: $15,000 (100h)  │ │
│  │ 2. Backend dev: $12,000 (80h)    │ │
│  │ 3. QA Testing: $5,000 (40h)      │ │
│  │                                  │ │
│  │ Total: $32,000                   │ │
│  │ Tax: $2,560 (8%)                 │ │
│  │ Grand Total: $34,560             │ │
│  │                                  │ │
│  │ Terms & Conditions:              │ │
│  │ [Standard terms from quotation]  │ │
│  │ [Edit]                           │ │
│  │                                  │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ACTIONS:                              │
│  [Download PDF] [Export Excel]         │
│  [Save & Send] [Cancel]                │
│                                        │
└────────────────────────────────────────┘
```

**Pre-filled from quotation:**
- Line items
- Pricing
- Terms
- Vendor details

**User can edit:**
- PO number
- Special terms
- Payment terms
- Delivery address

---

## Transitions & Decision Points

| From | To | Trigger | Condition |
|------|----|---------|-----------| 
| Login | Dashboard | Auth success | User credentials valid |
| Dashboard | Upload | Click [+Upload] | Any time |
| Upload | Detail | Extract complete | File uploaded successfully |
| Detail | Workflow | Click [Start] | User is manager/officer |
| Detail | Export | Click [Download] | Always available |
| Dashboard | Search | Click filter/search | Any filter selected |
| Detail | Edit | Click [Edit] | Editable field clicked |
| Workflow | Approval | Workflow step 3+ | Ready for approval |
| Approval | Comparison | Quotes loaded | 2+ quotes received |
| Comparison | PO | Click [Approve] | User has authority |
| PO | Export | Click [Download] | PO complete |
| Any | Login | Session expired | 24 hours elapsed |

---

## Error States & Recovery

### Upload Failed
```
❌ Upload failed: File too large (6.2MB, max 5MB)

[DISMISS] [RETRY] [CANCEL]
```

### Extraction Failed
```
⚠️ Extraction incomplete: Could not detect line items

Confidence: 45% (Below threshold)

[RETRY] [MANUAL ENTRY] [CANCEL]
```

### API Error
```
❌ Something went wrong

Connection to backend failed.

[RETRY] [GO TO DASHBOARD] [CONTACT SUPPORT]
```

---

## Accessibility & Performance

### Load Time Targets
- Login: <1 second
- Dashboard: <2 seconds
- Upload: <3 seconds (includes extraction)
- Detail: <1 second
- Comparison: <2 seconds
- PO: <1 second

### Responsive Design
- Desktop: 1920x1080+
- Tablet: 768x1024
- Mobile: 375x667 (limited features)

### Keyboard Navigation
- Tab through all interactive elements
- Enter to activate buttons
- Escape to close modals
- Arrow keys for list navigation

---

**Reference:** `/docs/01-project/USER_FLOW_MAP_v1.0.md`
