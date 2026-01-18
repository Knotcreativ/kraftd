# Kraftd MVP — Complete User Flow

**Version**: 1.0  
**Last Updated**: January 2026  
**Status**: Production Ready

---

## Overview

Kraftd is an intelligent document processing and workflow management system. This document describes the complete end-to-end user journey from initial access through document completion.

**Key Components:**
- **Frontend**: React 18 + TypeScript, hosted on Azure Static Web Apps
- **Backend**: FastAPI with 26 production endpoints
- **Database**: Cosmos DB for document and user data
- **Processing**: Multi-stage intelligent extraction pipeline
- **Monitoring**: Application Insights + OpenTelemetry

---

## Table of Contents

1. [User Accesses the Application](#1-user-accesses-the-application)
2. [Authentication Flow](#2-authentication-flow)
3. [Dashboard Loads](#3-dashboard-loads)
4. [Document Upload](#4-user-uploads-a-document)
5. [Processing Pipeline](#5-document-processing-pipeline)
6. [View Results](#6-user-views-processed-document)
7. [Workflows](#7-user-starts-a-workflow)
8. [Conversion & Download](#9-conversion-optional-mvp-feature)

---

## 1. User Accesses the Application

### 1.1 Landing on Frontend

When user opens the Kraftd web application:

```
Browser Request
    ↓
Azure Static Web Apps (westeurope)
    ↓
Load index.html
    ↓
Load React bundle (from dist/)
    ↓
Global styles + routing config
    ↓
Application ready
```

**Resources Loaded:**
- `index.html` - Entry point
- React 18 bundle with TypeScript
- CSS modules and Tailwind styles
- React Router configuration
- Context/Redux state initialization

### 1.2 Initial State Check

The app checks localStorage for authentication state:

```javascript
// On mount:
const accessToken = localStorage.getItem('accessToken');
const refreshToken = localStorage.getItem('refreshToken');

if (accessToken && isTokenValid(accessToken)) {
  // User is authenticated → Load dashboard
  navigate('/dashboard');
} else if (refreshToken) {
  // Attempt silent authentication (future feature)
  refreshAccessToken();
} else {
  // No tokens → Redirect to login
  navigate('/login');
}
```

**Outcome:**
- Authenticated user → Dashboard loads
- Unauthenticated user → Login page shows

---

## 2. Authentication Flow

Authentication is the gateway to all user functionality.

### 2.1 Registration

**User Action:**
```
Email: user@example.com
Password: [secure password]
Click: "Create Account"
```

**Frontend Validation:**
- Email format validation
- Password strength check (optional)
- Non-empty field validation

**Frontend → Backend:**
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Backend Processing:**

1. **Validation**
   ```python
   # Check if user exists
   existing_user = db.query("SELECT * FROM users WHERE email = ?")
   if existing_user:
       return {"error": "User already exists"}
   ```

2. **Password Hashing**
   ```python
   password_hash = bcrypt.hash(password)
   ```

3. **Store in Cosmos DB**
   ```json
   {
     "id": "user_uuid",
     "email": "user@example.com",
     "password_hash": "bcrypt_hash_here",
     "created_at": "2026-01-17T10:30:00Z",
     "owner_email": "user@example.com",
     "documents_count": 0,
     "last_login": null
   }
   ```

4. **Response**
   ```json
   {
     "success": true,
     "message": "Registration successful"
   }
   ```

**Frontend Result:**
- Success notification
- Redirect to login page

---

### 2.2 Login

**User Action:**
```
Email: user@example.com
Password: [password]
Click: "Login"
```

**Frontend → Backend:**
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Backend Processing:**

1. **User Lookup**
   ```python
   user = db.query("SELECT * FROM users WHERE email = ?")
   if not user:
       return {"error": "Invalid credentials"}
   ```

2. **Password Verification**
   ```python
   if not bcrypt.verify(password, user.password_hash):
       return {"error": "Invalid credentials"}
   ```

3. **Token Generation**
   ```python
   access_token = create_access_token(
       subject=user.email,
       expires_delta=timedelta(minutes=60)
   )
   refresh_token = create_refresh_token(
       subject=user.email,
       expires_delta=timedelta(days=7)
   )
   ```

4. **Response**
   ```json
   {
     "accessToken": "eyJhbGciOiJIUzI1NiIs...",
     "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
     "expiresIn": 3600,
     "user": {
       "email": "user@example.com"
     }
   }
   ```

**Frontend Result:**
- Store tokens in localStorage/memory
- Redirect to dashboard
- User is authenticated

**Token Management:**
- **Access Token**: Valid 60 minutes (API calls)
- **Refresh Token**: Valid 7 days (get new access token)
- **Token Refresh Endpoint**: `POST /auth/refresh`

---

## 3. Dashboard Loads

### 3.1 API Calls on Dashboard Load

Once authenticated, frontend makes parallel requests:

```http
GET /documents
Authorization: Bearer {accessToken}

Response:
{
  "documents": [
    {
      "id": "doc_123",
      "name": "RFQ_Jan2026.pdf",
      "status": "completed",
      "uploadedAt": "2026-01-17T09:00:00Z",
      "completeness": 95,
      "documentType": "RFQ"
    },
    {
      "id": "doc_124",
      "name": "BOQ_draft.xlsx",
      "status": "processing",
      "uploadedAt": "2026-01-17T10:00:00Z"
    }
  ]
}
```

### 3.2 Dashboard UI Components

**Primary Elements:**
1. **Document List**
   - Document name
   - Status badge (pending/processing/completed/failed)
   - Upload date
   - Completeness score
   - Quick actions (view, delete, process)

2. **Upload Section**
   - Drag-and-drop zone
   - File picker button
   - Supported formats: PDF, PNG, JPEG, XLSX, DOCX

3. **Workflow List** (optional for MVP)
   - Active workflows
   - Status indicators
   - Next step indicators

4. **Empty State**
   - Message: "No documents yet"
   - CTA: "Upload your first document"

### 3.3 Document Status States

| Status | Meaning | User Can | Next Step |
|--------|---------|----------|-----------|
| `pending` | Uploaded, waiting to process | Click "Process" | Move to processing |
| `processing` | Pipeline running | Wait or view logs | Auto → completed/failed |
| `completed` | Extraction finished | View results, download | Export or workflow |
| `failed` | Pipeline error | Delete, retry, contact support | Retry or delete |

---

## 4. User Uploads a Document

### 4.1 Upload Initiation

**User Action:**
```
1. Click "Upload Document"
2. Select file (e.g., RFQ_Jan2026.pdf)
3. Click "Open"
```

### 4.2 Frontend Behavior

```javascript
// File validation
if (file.size > 50 * 1024 * 1024) {
  showError("File too large (max 50MB)");
  return;
}

const supportedTypes = ['application/pdf', 'image/png', 'image/jpeg', ...];
if (!supportedTypes.includes(file.type)) {
  showError("Unsupported file type");
  return;
}

// Show progress
showProgressBar();
disableUI();

// Upload with FormData
const formData = new FormData();
formData.append('file', file);

fetch('POST /documents/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData,
  onProgress: (e) => updateProgressBar(e.loaded / e.total)
});
```

### 4.3 Backend Processing

```http
POST /documents/upload
Content-Type: multipart/form-data
Authorization: Bearer {accessToken}

Body: [binary file data]
```

**Backend Steps:**

1. **File Validation**
   ```python
   # Check file type
   if file.content_type not in SUPPORTED_TYPES:
       return {"error": "Unsupported file type"}
   
   # Check file size
   if file.size > 50 * 1024 * 1024:
       return {"error": "File too large"}
   ```

2. **Upload to Azure Blob Storage**
   ```python
   blob_client = blob_container_client.get_blob_client(file.filename)
   blob_client.upload_blob(file.file, overwrite=True)
   blob_url = blob_client.url
   ```

3. **Create Document Record in Cosmos DB**
   ```json
   {
     "id": "doc_123",
     "name": "RFQ_Jan2026.pdf",
     "owner_email": "user@example.com",
     "blob_url": "https://storage.blob.core.windows.net/...",
     "status": "pending",
     "uploadedAt": "2026-01-17T10:30:00Z",
     "fileSize": 2048576,
     "fileType": "application/pdf",
     "documentType": null,
     "extractedData": null,
     "completeness": null,
     "failureReason": null
   }
   ```

4. **Response**
   ```json
   {
     "documentId": "doc_123",
     "status": "pending",
     "message": "Document uploaded successfully. Click 'Process' to extract data."
   }
   ```

### 4.4 Frontend Updates

- Document appears in list with status = `pending`
- Progress bar closes
- UI re-enabled
- Notification: "Document uploaded successfully"
- Button: "Process Now" or user can process later

---

## 5. Document Processing Pipeline

This is the core intelligence engine. When user clicks "Process" or auto-processing triggers:

```http
POST /documents/{documentId}/process
Authorization: Bearer {accessToken}
```

### 5.1 Stage 1 — Classification

**Purpose:** Identify document type

**Process:**
```python
# Load document from Blob
document_content = blob_client.download_blob().readall()

# Stage 1: Classification
classifier = DocumentClassifier()
classification_result = classifier.classify(document_content)

# Result
{
  "document_type": "RFQ",  # RFQ, BOQ, Quotation, Invoice, PO, Contract
  "confidence_score": 0.94,
  "alternatives": [
    {"type": "BOQ", "confidence": 0.04},
    {"type": "Quotation", "confidence": 0.02}
  ]
}
```

**Uses:**
- Regex pattern matching
- Layout analysis
- DI (Document Intelligence) classification
- OCR text analysis

**Output:** Document type with confidence score

### 5.2 Stage 2 — Extraction

**Purpose:** Extract structured data from document

**Process:**
```python
# Stage 2: Extraction
extractor = DocumentExtractor(document_type="RFQ")
extraction_result = extractor.extract(document_content)

# Result
{
  "header": {
    "date": "2026-01-15",
    "number": "RFQ-2026-001",
    "from": {
      "name": "Acme Corp",
      "address": "123 Main St, Dubai"
    },
    "to": {
      "name": "Supplier Ltd",
      "address": "456 Park Ave, Abu Dhabi"
    }
  },
  "lineItems": [
    {
      "description": "Widget A",
      "quantity": 100,
      "unit": "pcs",
      "unitPrice": 50,
      "totalPrice": 5000,
      "currency": "AED"
    },
    {
      "description": "Widget B",
      "quantity": 50,
      "unit": "pcs",
      "unitPrice": 75,
      "totalPrice": 3750,
      "currency": "AED"
    }
  ],
  "totals": {
    "subtotal": 8750,
    "tax": 700,
    "total": 9450,
    "currency": "AED"
  },
  "metadata": {
    "paymentTerms": "Net 30",
    "deliveryDate": "2026-02-15",
    "notes": "Please confirm availability"
  }
}
```

**Uses:**
- Azure Document Intelligence SDK
- Table extraction
- OCR with layout analysis
- Fallback regex rules

**Output:** Structured extraction with all fields

### 5.3 Stage 3 — Inference

**Purpose:** Fill gaps using business logic

**Process:**
```python
# Stage 3: Inference
inferencer = DataInferencer()

# Rules applied:
inference_result = inferencer.infer(extraction_result)

# Examples of inferences:
- Missing totals → Calculate from line items
- Missing currency → Infer from company location/standard
- Missing VAT rate → Use standard (5% for UAE)
- Missing payment terms → Use default ("Net 30")
- Missing delivery date → Calculate from terms
- Missing parties → Match against known vendors

# Result includes confidence scores for each inferred field
```

**Output:** Complete data with inferred missing values

### 5.4 Stage 4 — Completeness Scoring

**Purpose:** Score data quality

**Process:**
```python
# Stage 4: Completeness Check
completeness_checker = CompletenessChecker()

scoring = {
  "critical": {           # 60% weight
    "fields": [
      "date", "from", "to", "lineItems", "total"
    ],
    "completed": 5,
    "total": 5,
    "score": 1.0
  },
  "important": {          # 30% weight
    "fields": [
      "documentNumber", "paymentTerms", "currency"
    ],
    "completed": 3,
    "total": 3,
    "score": 1.0
  },
  "optional": {           # 10% weight
    "fields": [
      "notes", "incoTerms", "deliveryLocation"
    ],
    "completed": 1,
    "total": 3,
    "score": 0.33
  }
}

# Overall calculation:
overall_score = (1.0 * 0.6) + (1.0 * 0.3) + (0.33 * 0.1) = 0.963 → 96%

# Response
{
  "completenessScore": 96,
  "missingFields": ["incoTerms", "deliveryLocation"],
  "recommendations": [
    "Add Inco Terms for international shipment",
    "Specify delivery location for freight cost calculation"
  ]
}
```

### 5.5 Save Results to Cosmos DB

```json
{
  "id": "doc_123",
  "status": "completed",
  "classificationResult": {
    "documentType": "RFQ",
    "confidence": 0.94
  },
  "extractedData": {
    "header": {...},
    "lineItems": [...],
    "totals": {...},
    "metadata": {...}
  },
  "inferenceData": {
    "inferredFields": {...},
    "confidenceScores": {...}
  },
  "completenessScore": 96,
  "missingFields": ["incoTerms"],
  "recommendations": [...],
  "processedAt": "2026-01-17T10:45:00Z",
  "processingDurationMs": 3240
}
```

### 5.6 Frontend Updates

- Status changes from `processing` → `completed`
- Completeness badge shows "96%"
- "View Results" button becomes active
- Optional notification: "Document ready for review"

---

## 6. User Views Processed Document

### 6.1 User Action

User clicks on completed document in dashboard

### 6.2 Frontend Request

```http
GET /documents/{documentId}
Authorization: Bearer {accessToken}
```

### 6.3 Backend Response

```json
{
  "id": "doc_123",
  "name": "RFQ_Jan2026.pdf",
  "status": "completed",
  "uploadedAt": "2026-01-17T10:30:00Z",
  "processedAt": "2026-01-17T10:45:00Z",
  
  "classification": {
    "documentType": "RFQ",
    "confidence": 0.94
  },
  
  "extractedData": {
    "header": {
      "date": "2026-01-15",
      "number": "RFQ-2026-001",
      "from": {...},
      "to": {...}
    },
    "lineItems": [...],
    "totals": {...}
  },
  
  "completeness": {
    "score": 96,
    "missingFields": ["incoTerms"],
    "recommendations": [...]
  }
}
```

### 6.4 Frontend Display

**Tabs/Sections:**

1. **Summary Tab**
   - Document type badge
   - Completeness score with visual indicator
   - Key figures (total amount, item count)
   - Quick stats

2. **Extracted Data Tab**
   - Header info (date, number, parties)
   - Line items in table format
   - Totals section
   - Editable fields for corrections

3. **Recommendations Tab**
   - Missing fields listed
   - Suggestions for improvement
   - Action items

4. **Actions Panel**
   - "Start Workflow" button
   - "Download Data" (JSON/CSV/Excel)
   - "Export as PDF"
   - "Delete" option

---

## 7. User Starts a Workflow

### 7.1 Workflow Types

**Available Workflows:**
- `rfq_to_boq` - Convert RFQ to BOQ
- `approval_flow` - Get approvals
- `quote_generation` - Create quotation
- `po_matching` - Match with PO

### 7.2 Frontend Action

```javascript
// User clicks "Start Workflow"
POST /workflows

{
  "documentId": "doc_123",
  "workflowType": "rfq_to_boq",
  "parameters": {
    "targetFormat": "excel"
  }
}
```

### 7.3 Backend Processing

```python
# Create workflow record
workflow = {
  "id": "wf_456",
  "documentId": "doc_123",
  "workflowType": "rfq_to_boq",
  "status": "initiated",
  "currentStep": 1,
  "steps": [
    {
      "stepNumber": 1,
      "name": "Review RFQ Data",
      "status": "completed",
      "completedAt": "2026-01-17T10:50:00Z"
    },
    {
      "stepNumber": 2,
      "name": "Generate BOQ Template",
      "status": "in_progress",
      "startedAt": "2026-01-17T10:51:00Z"
    },
    {
      "stepNumber": 3,
      "name": "Review Generated BOQ",
      "status": "pending"
    },
    {
      "stepNumber": 4,
      "name": "Export & Finalize",
      "status": "pending"
    }
  ],
  "createdAt": "2026-01-17T10:50:00Z",
  "estimatedCompletionTime": "2026-01-17T11:00:00Z"
}
```

### 7.4 Frontend Updates

**Workflow View Shows:**
- Progress bar (step 2 of 4)
- Current step details
- Pending actions
- Timeline view
- "Mark Complete" button for current step

---

## 8. Workflow Progress

### 8.1 User Updates Workflow

```http
PUT /workflows/{workflowId}/steps/{stepNumber}
Content-Type: application/json

{
  "status": "completed",
  "notes": "BOQ reviewed and approved",
  "approvalRequired": false
}
```

### 8.2 Backend Updates

- Marks step as completed
- Moves to next step automatically
- Updates workflow status
- Logs timestamps
- Triggers notifications (if configured)

### 8.3 Approval Flows

**For workflows requiring approval:**

```http
PUT /workflows/{workflowId}/steps/{stepNumber}/approve

{
  "approved": true,
  "comments": "Approved for export"
}
```

---

## 9. Conversion (Optional MVP Feature)

### 9.1 Conversion Options

**User can generate:**

1. **Excel Export**
   ```http
   POST /documents/{documentId}/export/excel
   
   Response: Download link to .xlsx file
   ```

2. **PDF Report**
   ```http
   POST /documents/{documentId}/export/pdf
   
   Response: Download link to formatted PDF
   ```

3. **BOQ Template**
   ```http
   POST /documents/{documentId}/convert/boq
   
   Response: New document with BOQ format
   ```

### 9.2 Backend Processing

```python
# Generate file
generator = ExportGenerator()

if format == "excel":
    excel_bytes = generator.to_excel(extracted_data)
elif format == "pdf":
    pdf_bytes = generator.to_pdf(extracted_data)

# Upload to Blob Storage
blob_name = f"{document_id}_export_{timestamp}.{extension}"
blob_client.upload_blob(excel_bytes)

# Return download link
return {
  "downloadUrl": blob_url,
  "filename": "RFQ_Jan2026_export.xlsx",
  "expiresIn": 3600  # Link valid 1 hour
}
```

### 9.3 Frontend

- Shows download button
- Initiates download when clicked
- Tracks download success
- Optional: Save to OneDrive/SharePoint

---

## 10. Completion

### 10.1 Final State

User can now:
- ✅ Access structured document data
- ✅ View completeness score
- ✅ Download in multiple formats
- ✅ Access workflow progress
- ✅ Export to external systems
- ✅ Archive or delete document

### 10.2 Data Retention

- Documents stored in Cosmos DB indefinitely
- Files stored in Azure Blob for 90 days
- Workflow history retained for audit
- User can request deletion (GDPR)

### 10.3 Next Actions

- Upload another document
- Create new workflow
- Export data to business system
- Share with team (future feature)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Static Web Apps                     │
│                  (Frontend - React 18 + TS)                  │
│                    westeurope region                         │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Azure Container Apps                            │
│         (Backend - FastAPI 26 endpoints)                     │
│              uaenorth region                                 │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Auth        │  │  Documents   │  │  Workflows   │       │
│  │  Endpoints   │  │  Endpoints   │  │  Endpoints   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────────┬───────────────┬───────────────┬─────────────┘
                 │               │               │
                 ↓               ↓               ↓
        ┌────────────┐   ┌────────────┐   ┌──────────┐
        │ Cosmos DB  │   │ Blob Store │   │ App      │
        │ (Data)     │   │ (Files)    │   │ Insights │
        │            │   │            │   │ (Logs)   │
        └────────────┘   └────────────┘   └──────────┘
```

---

## Error Handling

### Common Scenarios

| Scenario | Status Code | Frontend Action |
|----------|-------------|-----------------|
| Invalid token | 401 | Refresh or redirect to login |
| File too large | 413 | Show error, prompt user |
| Processing failed | 500 | Show error, offer retry |
| Network timeout | 0 | Retry with exponential backoff |
| Invalid file type | 400 | Show supported types |

---

## Performance Targets

- **Upload**: <30s for 50MB file
- **Processing**: <5 min for typical RFQ
- **API Response**: <500ms for most endpoints
- **Dashboard Load**: <2s

---

## Security

- ✅ All API calls require valid JWT
- ✅ Passwords hashed with bcrypt
- ✅ Tokens auto-expire
- ✅ No secrets in responses
- ✅ HTTPS everywhere
- ✅ CORS properly configured
- ✅ Rate limiting on auth endpoints

---

## Next Steps (Post-MVP)

- [ ] Real-time notifications for workflow progress
- [ ] Team collaboration (shared documents)
- [ ] Advanced search and filtering
- [ ] Integration with ERP systems
- [ ] Mobile app support
- [ ] Webhooks for external systems
- [ ] Batch processing
- [ ] Custom workflow builder

