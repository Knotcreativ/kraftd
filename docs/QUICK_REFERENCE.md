# Kraftd MVP — Quick Reference Guide

**Date:** January 17, 2026  
**Status:** Production Ready ✅

---

## 🎯 What is Kraftd?

**Kraftd** is an intelligent document processing and workflow management platform for enterprise procurement.

**Core Capability:** Upload an RFQ, BOQ, PO, Invoice, or Quotation → Kraftd extracts structured data automatically → Use in workflows.

---

## 📱 User Journey (10-Step Overview)

```
1. USER ACCESSES APP
   └─→ Browser opens: https://kraftdintel-web.azurestaticapps.net
   └─→ App loads React frontend from Azure Static Web Apps

2. USER AUTHENTICATES
   └─→ Register: Email + Password → Cosmos DB
   └─→ Login: Get JWT tokens (60 min access, 7 day refresh)

3. DASHBOARD LOADS
   └─→ List documents (pending/processing/completed/failed)
   └─→ Upload new documents
   └─→ Access workflows

4. UPLOAD DOCUMENT
   └─→ Select PDF/Image/Excel file
   └─→ Upload to Azure Blob Storage
   └─→ Create record in Cosmos DB (status: pending)

5. PROCESS DOCUMENT
   └─→ Classification: Detect document type (RFQ, BOQ, etc.)
   └─→ Extraction: Get headers, line items, totals
   └─→ Inference: Fill gaps with business logic
   └─→ Completeness: Score data quality (0-100%)

6. VIEW RESULTS
   └─→ See extracted data (structured)
   └─→ View completeness score
   └─→ See recommendations for missing fields

7. START WORKFLOW
   └─→ Choose workflow type (rfq_to_boq, approval_flow, etc.)
   └─→ Follow step-by-step process
   └─→ Approve/reject at each step

8. TRACK WORKFLOW
   └─→ See progress (step 2 of 4)
   └─→ Update step status
   └─→ View completion timeline

9. EXPORT/CONVERT
   └─→ Generate Excel
   └─→ Create PDF report
   └─→ Download formatted output

10. COMPLETE
    └─→ Archive document
    └─→ Use data in business system
    └─→ Repeat with next document
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────┐
│  USER BROWSER                               │
│  Opens: https://kraftdintel-web...          │
└─────────────────┬───────────────────────────┘
                  │ HTTPS (Encrypted)
                  ↓
┌─────────────────────────────────────────────────────────┐
│  FRONTEND (Azure Static Web Apps - West Europe)         │
│  • React 18 + TypeScript                                │
│  • Dashboard, Upload, Results, Workflows                │
│  • State management, Routing, UI Components             │
└─────────────────┬───────────────────────────────────────┘
                  │ REST API + JWT
                  ↓
┌──────────────────────────────────────────────────────────┐
│  BACKEND (Azure Container Apps - UAE North)             │
│  • FastAPI (26 endpoints)                               │
│  • Authentication, Documents, Workflows, AI              │
│  • Processing Pipeline, Validation, Business Logic      │
└──┬───────────────────────────────────┬────────────┬─────┘
   │                                   │            │
   ↓                                   ↓            ↓
 COSMOS DB                        BLOB STORAGE  APP INSIGHTS
 (User Data,                      (PDF, Image,  (Logs,
  Documents,                       Excel Files) Telemetry)
  Workflows)
```

---

## 📊 Data Flow Example: Upload & Process RFQ

```
STEP 1: USER UPLOADS FILE
┌─────────────┐
│ RFQ.pdf     │
└────────┬────┘
         │
         ↓
    ┌─────────────────────────────┐
    │ Frontend Upload Component   │
    │ • Validate file type/size   │
    │ • Show progress bar         │
    └────┬────────────────────────┘
         │
         ↓
    POST /documents/upload
    Content-Type: multipart/form-data
    Authorization: Bearer {jwt_token}
    Body: [binary file data]
         │
         ↓
    ┌─────────────────────────────────┐
    │ Backend Upload Handler          │
    │ • Validate                      │
    │ • Upload to Blob Storage        │
    │ • Create DB record              │
    │ • Return documentId             │
    └────┬────────────────────────────┘
         │
         ├─→ Azure Blob Storage
         │   Location: /documents/doc_123/RFQ.pdf
         │
         └─→ Cosmos DB
             {
               "id": "doc_123",
               "name": "RFQ.pdf",
               "status": "pending",
               "blob_url": "https://...",
               "owner_email": "user@..."
             }

STEP 2: USER CLICKS "PROCESS"
┌──────────────────────────────────┐
│ Frontend: User clicks button      │
│ POST /documents/doc_123/process   │
└────┬─────────────────────────────┘
     │
     ↓
  ┌──────────────────────────────────────────┐
  │ STAGE 1: CLASSIFICATION                 │
  │                                          │
  │ Input: RFQ.pdf                          │
  │ Process: Analyze layout, text, structure│
  │ Output: {                               │
  │   "documentType": "RFQ",               │
  │   "confidence": 0.94                   │
  │ }                                       │
  └────┬─────────────────────────────────────┘
       │
       ↓
  ┌──────────────────────────────────────────┐
  │ STAGE 2: EXTRACTION                     │
  │                                          │
  │ Input: RFQ.pdf + documentType           │
  │ Process: OCR + Document Intelligence    │
  │ Output: {                               │
  │   "header": {                           │
  │     "date": "2026-01-15",              │
  │     "number": "RFQ-001",               │
  │     "from": {...},                     │
  │     "to": {...}                        │
  │   },                                    │
  │   "lineItems": [...],                  │
  │   "totals": {...}                      │
  │ }                                       │
  └────┬─────────────────────────────────────┘
       │
       ↓
  ┌──────────────────────────────────────────┐
  │ STAGE 3: INFERENCE                      │
  │                                          │
  │ Input: Extracted data with gaps         │
  │ Process: Apply business rules           │
  │ Logic:                                  │
  │  • Missing date? Use "today"           │
  │  • Missing currency? Use "AED"         │
  │  • Missing totals? Calculate           │
  │  • Missing VAT? Apply 5% rule          │
  │ Output: Complete data set              │
  └────┬─────────────────────────────────────┘
       │
       ↓
  ┌──────────────────────────────────────────┐
  │ STAGE 4: COMPLETENESS                   │
  │                                          │
  │ Input: Complete extracted data          │
  │ Scoring:                                │
  │  • Critical fields: 5/5 (100%) × 60%   │
  │  • Important fields: 3/3 (100%) × 30%  │
  │  • Optional fields: 2/3 (67%) × 10%    │
  │ Total Score: 96%                       │
  │                                         │
  │ Output: {                               │
  │   "completenessScore": 96,             │
  │   "missingFields": ["incoTerms"],     │
  │   "recommendations": [...]             │
  │ }                                       │
  └────┬─────────────────────────────────────┘
       │
       ↓
  ┌────────────────────────────────────────────┐
  │ Update Cosmos DB                          │
  │                                            │
  │ {                                         │
  │   "id": "doc_123",                       │
  │   "status": "completed",                │
  │   "classificationResult": {...},        │
  │   "extractedData": {...},               │
  │   "completenessScore": 96,              │
  │   "processedAt": "2026-01-17T11:00:00Z"│
  │ }                                        │
  └────┬──────────────────────────────────────┘
       │
       ↓
  ┌──────────────────────────────────────────┐
  │ Frontend: Update Dashboard               │
  │                                          │
  │ Document status: pending → completed    │
  │ Show: Completeness badge (96%)          │
  │ Show: "View Results" button             │
  │ Show: "Start Workflow" button           │
  └──────────────────────────────────────────┘

STEP 3: USER VIEWS RESULTS
┌──────────────────────────────┐
│ User clicks "View Results"   │
└────┬─────────────────────────┘
     │
     ↓
  GET /documents/doc_123
     │
     ↓
  ┌──────────────────────────────┐
  │ Backend Returns:             │
  │ • Document metadata          │
  │ • Extracted data             │
  │ • Completeness score         │
  │ • Missing fields             │
  │ • Recommendations            │
  └────┬─────────────────────────┘
       │
       ↓
  ┌────────────────────────────────────────┐
  │ Frontend Displays:                     │
  │                                        │
  │ TAB 1: Summary                        │
  │  - Document type: RFQ                 │
  │  - Completeness: 96%                  │
  │  - Total items: 2                     │
  │  - Total amount: 9,450 AED            │
  │                                        │
  │ TAB 2: Extracted Data                 │
  │  - Header (Date, Number, From, To)   │
  │  - Line items (table)                 │
  │  - Totals                             │
  │  - Metadata                           │
  │                                        │
  │ TAB 3: Recommendations               │
  │  - Missing: incoTerms                 │
  │  - Suggestions                        │
  │                                        │
  │ ACTIONS:                              │
  │  - Start Workflow                     │
  │  - Export Excel                       │
  │  - Download PDF                       │
  │  - Delete                             │
  └────────────────────────────────────────┘
```

---

## 🔑 Key Endpoints (26 Total)

### Authentication (5)
```
POST   /auth/register       Create account
POST   /auth/login          Get JWT tokens
POST   /auth/refresh        Refresh access token
POST   /auth/logout         Invalidate tokens
GET    /auth/me             Current user info
```

### Documents (6)
```
POST   /documents/upload    Upload file
GET    /documents           List user's documents
GET    /documents/{id}      Get document details
POST   /documents/{id}/process   Start processing
DELETE /documents/{id}      Delete document
GET    /documents/{id}/export/{format}  Export data
```

### Workflows (7)
```
POST   /workflows           Create workflow
GET    /workflows           List workflows
GET    /workflows/{id}      Get workflow details
PUT    /workflows/{id}/steps/{num}   Update step status
POST   /workflows/{id}/steps/{num}/approve   Approve step
POST   /workflows/{id}/complete   Mark complete
DELETE /workflows/{id}      Delete workflow
```

### AI Agent (4)
```
POST   /agent/chat          Chat with AI
POST   /agent/extract       Extract from unstructured text
POST   /agent/infer         Infer missing data
GET    /agent/rules         Get business rules
```

### System (4)
```
GET    /health             System health check
GET    /metrics            Performance metrics
POST   /logs               Query logs
GET    /config             System configuration
```

---

## 💾 Database Schema (Cosmos DB)

### Users Collection
```json
{
  "id": "user_uuid",
  "email": "user@example.com",
  "password_hash": "bcrypt_hash",
  "created_at": "2026-01-17T10:00:00Z",
  "owner_email": "user@example.com"
}
```

### Documents Collection
```json
{
  "id": "doc_123",
  "name": "RFQ.pdf",
  "owner_email": "user@example.com",
  "status": "completed",
  "uploadedAt": "2026-01-17T10:30:00Z",
  "processedAt": "2026-01-17T10:45:00Z",
  "documentType": "RFQ",
  "completenessScore": 96,
  "extractedData": {...},
  "blob_url": "https://..."
}
```

### Workflows Collection
```json
{
  "id": "wf_456",
  "documentId": "doc_123",
  "workflowType": "rfq_to_boq",
  "status": "in_progress",
  "currentStep": 2,
  "steps": [
    {
      "stepNumber": 1,
      "name": "Review RFQ Data",
      "status": "completed"
    },
    {
      "stepNumber": 2,
      "name": "Generate BOQ",
      "status": "in_progress"
    }
  ],
  "createdAt": "2026-01-17T10:50:00Z"
}
```

---

## 🔐 Security Features

| Feature | Implementation |
|---------|-----------------|
| **Authentication** | JWT tokens (60 min access, 7 day refresh) |
| **Password** | Bcrypt hashing (never stored in plain text) |
| **Transport** | HTTPS encrypted, TLS 1.3+ |
| **API Access** | Bearer token required on all endpoints |
| **Token Expiry** | Auto-refresh on 401 responses |
| **Rate Limiting** | 100 requests/min on auth endpoints |
| **Secrets** | Never in logs or responses |
| **CORS** | Frontend domain only |

---

## ⏱️ Performance Targets

| Operation | Target | Status |
|-----------|--------|--------|
| Upload document (50MB) | <30 seconds | ✅ Target |
| Process RFQ | <5 minutes | ✅ Target |
| API response | <500ms | ✅ Target |
| Dashboard load | <2 seconds | ✅ Target |

---

## 📋 Deployment Status

| Component | Status | Region | URL |
|-----------|--------|--------|-----|
| **Frontend** | ✅ Live | West Europe | https://kraftdintel-web.azurestaticapps.net |
| **Backend** | ✅ Live | UAE North | https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io |
| **Database** | ✅ Ready | UAE North | Cosmos DB (provisioned) |
| **Monitoring** | ✅ Active | UAE North | Application Insights |
| **CI/CD** | ✅ Active | — | GitHub Actions |

---

## 🚀 Getting Started (Team Members)

### 1. Read Documentation
- [ ] START_HERE.txt (5 min)
- [ ] USER_FLOW.md (20 min)
- [ ] API_CONTRACT_v1.0.md (15 min)

### 2. Local Development Setup
```bash
# Clone repository
git clone https://github.com/Knotcreativ/kraftd.git
cd kraftd

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m pytest

# Frontend setup
cd ../frontend
npm install
npm run dev

# Visit: http://localhost:5173
```

### 3. Connect to Development API
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

### 4. Run Integration Tests
```bash
cd backend
python -m pytest test_integration.py -v
```

---

## 📞 Support & Resources

### Documentation
- **Complete Flow:** `/docs/USER_FLOW.md`
- **API Details:** `/docs/02-architecture/API_CONTRACT_v1.0.md`
- **Setup Guide:** `/docs/03-development/SETUP_GUIDE_v1.0.md`
- **Deployment:** `/docs/04-deployment/DEPLOYMENT_GUIDE_v1.0.md`

### Quick Links
- **Frontend Code:** `/frontend/` (React 18 + TypeScript)
- **Backend Code:** `/backend/` (FastAPI)
- **Infrastructure:** `/infrastructure/` (Bicep templates)
- **Tests:** `/backend/tests/`

### Troubleshooting
- Check: `/docs/04-deployment/TROUBLESHOOTING_RUNBOOK_v1.0.md`
- Logs: Azure Application Insights
- API Status: GET /health endpoint

---

## 🎓 Development Roadmap

**MVP (Current)** ✅
- Document upload & processing
- Basic workflows
- Extraction pipeline

**Phase 2**
- Real-time notifications
- Team collaboration
- Advanced search

**Phase 3**
- ERP integrations
- Mobile app
- Custom workflows
- Webhooks

---

## 📄 Version Info

| Component | Version | Status |
|-----------|---------|--------|
| API | v1.0 | Production |
| Frontend | 1.0.0 | Production |
| Documentation | 1.0 | Current |
| Database Schema | 1.0 | Current |

**Last Updated:** January 17, 2026  
**Next Review:** February 2026

---

**Questions?** Check `/docs/INDEX.md` for full documentation index.
