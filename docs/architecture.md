# Kraftd Docs — System Architecture

## Overview
Kraftd Docs is a global B2C document-intelligence platform that performs semantic document transformations using AI, OCR, and schema-driven intelligence. It does NOT perform file-type conversions (PDF → Word). Instead, it intelligently extracts, analyzes, and restructures document content based on user intent.

A **"conversion"** is the core unit of work. Each conversion encompasses:
- Document upload to Azure Blob Storage
- OCR + Azure Document Intelligence extraction
- AI analysis of document content + user intent
- AI-generated recommended schema
- User-edited schema with version tracking
- Output file generation in user-selected format
- Feedback collection and storage

All data is stored under a single `conversion_id` for complete traceability.

The system enforces user quota limits based on number of conversions per billing tier.

---

## High-Level Flow

```
1. User registers/logs in
   ↓
2. User uploads documents (1 or more)
   ├─ Files stored in Azure Blob Storage
   ├─ Conversion ID created
   ├─ Quota checked
   └─ Returns upload URLs + conversion_id
   ↓
3. Azure Document Intelligence processes files
   ├─ Extracts text, tables, fields
   ├─ Returns structured OCR data
   └─ Stored under ocr_id
   ↓
4. User enters free-text prompt (no categories)
   ├─ Prompt stored under prompt_id
   └─ Linked to conversion_id
   ↓
5. AI analyzes OCR + prompt
   ├─ Generates intelligence summary
   ├─ Identifies key data + gaps
   └─ Stored under summary_id
   ↓
6. AI generates recommended schema
   ├─ Maps extracted fields to schema
   ├─ Identifies missing fields
   ├─ Flags data conflicts
   └─ Stored under schema_id
   ↓
7. User edits schema
   ├─ All edits versioned
   ├─ Final schema stored under schema_final_id
   └─ Revision history maintained
   ↓
8. User selects output format
   └─ Supported: Word, Excel, JSON, PDF, CSV, Markdown, HTML
   ↓
9. AI generates final output
   ├─ Transforms data per user's schema
   ├─ File stored in Blob Storage
   └─ Linked to output_id
   ↓
10. User downloads file
    └─ Download tracked
    ↓
11. Feedback modal appears
    ├─ User provides feedback (optional)
    └─ Feedback stored under feedback_id
    ↓
12. Dashboard shows completed conversion
    └─ "New Conversion" resets workflow
```

---

## System Architecture

### **Technology Stack**

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend API** | Python 3.13 + FastAPI 0.128 | REST API, request handling, orchestration |
| **Frontend** | React 18.3 + TypeScript 5.9 + Vite 5.0 | Web interface, user interactions |
| **OCR Engine** | Azure Document Intelligence | Document extraction, field recognition |
| **AI Processing** | Azure OpenAI (GPT-4o, GPT-4o-mini) | Summary generation, schema creation, output generation |
| **Database** | Azure Cosmos DB (SQL API) | All structured data, multi-region capable |
| **File Storage** | Azure Blob Storage | Uploaded files, generated outputs, documents |
| **Authentication** | Custom JWT (RS256) | Stateless, secure token-based auth |
| **Message Queue** | (Optional: Azure Service Bus) | Async processing, long-running tasks |
| **Deployment** | Azure App Service / Container Apps | Scalable hosting |
| **CI/CD** | GitHub Actions | Automated build, test, deploy pipeline |
| **Infrastructure** | Azure Bicep | Infrastructure-as-Code |

---

## Backend Architecture

### **API Endpoints (67 total routes)**

#### **Authentication (Phase 1)**
```
POST   /api/v1/auth/register          - Create account
POST   /api/v1/auth/login             - Login user
POST   /api/v1/auth/refresh           - Refresh access token
POST   /api/v1/auth/verify-email      - Verify email address
GET    /api/v1/auth/profile           - Get current user profile
GET    /api/v1/auth/validate          - Validate current token
```

#### **Document Upload (Phase 2)**
```
POST   /api/v1/docs/upload            - Upload single document
POST   /api/v1/docs/upload/batch      - Upload multiple documents
GET    /api/v1/documents/{id}         - Get document details
DELETE /api/v1/documents/{id}         - Delete document
```

#### **User Profiles (Phase 3)**
```
GET    /api/v1/users/profile          - Get user profile
PUT    /api/v1/users/profile          - Update user profile
GET    /api/v1/users/settings         - Get user settings
PUT    /api/v1/users/settings         - Update user settings
```

#### **Document Intelligence (Phases 5-7)**
```
POST   /api/v1/docs/extract           - Extract text/fields from document
POST   /api/v1/docs/convert           - Convert document to target format
POST   /api/v1/workflow/inquiry       - User prompt submission
POST   /api/v1/workflow/estimation    - AI-generated schema recommendation
POST   /api/v1/workflow/normalize-quotes - Normalize field data
POST   /api/v1/workflow/comparison    - Compare extracted vs. user schema
POST   /api/v1/workflow/proposal      - Generate output proposal
POST   /api/v1/workflow/po            - (Custom: Purchase Order format)
POST   /api/v1/workflow/proforma-invoice - (Custom: Invoice format)
```

#### **Export & Download**
```
GET    /api/v1/documents/{id}/output  - Download generated file
POST   /api/v1/export/feedback        - Submit feedback on conversion
```

#### **System Health**
```
GET    /api/v1/health                 - Health check endpoint
GET    /api/v1/metrics                - Performance metrics
GET    /api/v1/                       - API root info
```

### **Backend Modules**

```
backend/
├── src/
│   ├── api/
│   │   ├── routes/           # API route handlers
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── documents.py  # Document management
│   │   │   ├── workflows.py  # Intelligence workflows
│   │   │   └── ...
│   │   ├── services/         # Business logic
│   │   │   ├── auth_service.py       # JWT token creation/validation
│   │   │   ├── cosmos_service.py     # Database access
│   │   │   ├── document_intelligence.py # Azure DI integration
│   │   │   ├── export_tracking.py    # Conversion tracking
│   │   │   └── ...
│   │   ├── models/           # Data schemas (Pydantic)
│   │   │   ├── user.py       # User, token models
│   │   │   ├── document.py   # Document models
│   │   │   ├── extraction.py # OCR extraction models
│   │   │   └── ...
│   │   ├── repositories/     # Data access layer
│   │   │   ├── user_repository.py
│   │   │   ├── document_repository.py
│   │   │   ├── extraction_repository.py
│   │   │   └── ...
│   │   ├── middleware/       # Request/response middleware
│   │   │   ├── rbac.py       # Role-based access control
│   │   │   ├── error_handler.py
│   │   │   └── ...
│   │   └── utils/            # Helper functions
│   ├── config.py             # Configuration management
│   ├── metrics.py            # Metrics collection
│   ├── rate_limit.py         # Rate limiting middleware
│   └── monitoring.py         # Performance monitoring
├── main.py                   # FastAPI application entry point
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container image
└── tests/                    # Test suite
```

### **Key Services**

#### **AuthService**
- JWT token creation (RS256 signing)
- Token validation and refresh
- Password hashing (bcrypt)
- Session management

#### **CosmosService**
- Database connection pooling
- Query execution with retry logic
- Transaction support
- Change feed processing (optional)

#### **DocumentIntelligenceService**
- Azure Document Intelligence API integration
- OCR extraction (text, tables, form fields)
- Result caching
- Error handling and retries

#### **ExportTrackingService**
- Three-stage recording: Upload → Processing → Completion
- Conversion lifecycle tracking
- Quota enforcement
- Usage analytics

#### **ProfileService**
- User profile management
- Subscription tier tracking
- Quota calculation
- Settings persistence

---

## Data Model

### **Core Collections (Cosmos DB)**

#### **Users Collection**
```json
{
  "id": "user_123",
  "email": "user@example.com",
  "name": "John Doe",
  "passwordHash": "bcrypt_hash",
  "subscriptionTier": "pro",  // free, pro, enterprise
  "quotaLimit": 1000,          // conversions per month
  "quotaUsed": 247,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-22T14:20:00Z",
  "isActive": true,
  "owner_email": "user@example.com"  // Partition key
}
```

#### **Conversions Collection**
```json
{
  "id": "conv_abc123",
  "userId": "user_123",
  "status": "completed",  // pending, processing, completed, failed
  "documentIds": ["doc_1", "doc_2"],
  "ocrId": "ocr_xyz",
  "promptId": "prompt_xyz",
  "summaryId": "summary_xyz",
  "schemaId": "schema_v1",
  "schemaFinalId": "schema_final_v3",
  "outputIds": {
    "docx": "output_docx_1",
    "json": "output_json_1"
  },
  "feedbackId": "feedback_1",
  "createdAt": "2024-01-22T10:00:00Z",
  "completedAt": "2024-01-22T10:45:00Z",
  "owner_email": "user@example.com"  // Partition key
}
```

#### **Documents Collection**
```json
{
  "id": "doc_1",
  "conversionId": "conv_abc123",
  "userId": "user_123",
  "fileName": "invoice.pdf",
  "blobUrl": "https://storage.blob.core.windows.net/uploads/...",
  "fileSize": 250000,
  "mimeType": "application/pdf",
  "uploadedAt": "2024-01-22T10:00:00Z",
  "owner_email": "user@example.com"  // Partition key
}
```

#### **Extractions Collection**
```json
{
  "id": "ocr_xyz",
  "conversionId": "conv_abc123",
  "documentId": "doc_1",
  "extractedText": "Lorem ipsum dolor sit...",
  "extractedFields": {
    "invoiceNumber": "INV-2024-001",
    "date": "2024-01-20",
    "amount": "1250.00"
  },
  "extractedTables": [
    {
      "name": "LineItems",
      "rows": [...]
    }
  ],
  "confidence": 0.92,
  "processingTime": 2500,  // ms
  "processedAt": "2024-01-22T10:02:00Z",
  "owner_email": "user@example.com"  // Partition key
}
```

#### **Prompts Collection**
```json
{
  "id": "prompt_xyz",
  "conversionId": "conv_abc123",
  "userId": "user_123",
  "promptText": "Extract invoice details and organize into a standard template",
  "createdAt": "2024-01-22T10:05:00Z",
  "owner_email": "user@example.com"  // Partition key
}
```

#### **Schemas Collection**
```json
{
  "id": "schema_final_v3",
  "conversionId": "conv_abc123",
  "version": 3,
  "schemaJson": {
    "type": "object",
    "properties": {
      "invoiceNumber": { "type": "string" },
      "date": { "type": "string", "format": "date" },
      "amount": { "type": "number" },
      "lineItems": {
        "type": "array",
        "items": { "type": "object" }
      }
    }
  },
  "sourceSchema": "schema_v1",  // AI-recommended
  "userEdits": [...],           // Array of edits
  "finalizedAt": "2024-01-22T10:30:00Z",
  "owner_email": "user@example.com"  // Partition key
}
```

#### **Outputs Collection**
```json
{
  "id": "output_docx_1",
  "conversionId": "conv_abc123",
  "userId": "user_123",
  "fileFormat": "docx",  // word, excel, json, pdf, csv, markdown
  "blobUrl": "https://storage.blob.core.windows.net/outputs/...",
  "fileSize": 500000,
  "downloadCount": 1,
  "generatedAt": "2024-01-22T10:35:00Z",
  "owner_email": "user@example.com"  // Partition key
}
```

#### **Feedback Collection**
```json
{
  "id": "feedback_1",
  "conversionId": "conv_abc123",
  "userId": "user_123",
  "feedbackText": "Good extraction, but missed some field details",
  "rating": 4,  // 1-5 stars
  "submittedAt": "2024-01-22T10:50:00Z",
  "owner_email": "user@example.com"  // Partition key
}
```

### **Partition Strategy**
- **Partition Key**: `owner_email` (for all user-specific data)
- **Reasoning**: Ensures data isolation per user, enables efficient queries by user, supports multi-tenancy
- **Indexing**: Automatic for all properties

---

## Frontend Architecture

### **Technology Stack**
- **Framework**: React 18.3 with TypeScript 5.9
- **Build Tool**: Vite 5.0
- **UI Framework**: (Material-UI or custom components)
- **State Management**: React Context API or Redux
- **HTTP Client**: Axios or Fetch API
- **Hosting**: Azure Static Web Apps

### **Project Structure**
```
frontend/
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── FileUploader.tsx
│   │   ├── SchemaEditor.tsx
│   │   ├── OutputPreview.tsx
│   │   ├── FeedbackModal.tsx
│   │   └── ...
│   ├── pages/              # Page components
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── ConversionPage.tsx
│   │   ├── SettingsPage.tsx
│   │   └── ...
│   ├── hooks/              # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useConversion.ts
│   │   └── ...
│   ├── context/            # React Context
│   │   └── AuthContext.tsx
│   ├── services/           # API communication
│   │   ├── api.ts          # Axios instance
│   │   └── endpoints.ts    # API routes
│   ├── utils/              # Helper functions
│   └── App.tsx             # Root component
├── public/                 # Static assets
├── index.html              # HTML entry point
├── vite.config.ts
└── tsconfig.json
```

### **Key Pages**

1. **Login/Register** - Authentication UI
2. **Dashboard** - Show previous conversions, quotas, settings
3. **Conversion Workflow**
   - Upload documents
   - Enter prompt
   - Review AI summary
   - Edit schema
   - Select output format
   - Download results
   - Provide feedback

---

## Security Architecture

### **Authentication Flow**
```
User Login
    ↓
Backend validates credentials
    ↓
Generate JWT (RS256 signed)
    ↓
Return access_token + refresh_token
    ↓
Frontend stores in sessionStorage/memory (not localStorage)
    ↓
Subsequent requests include Authorization: Bearer <token>
    ↓
Backend validates JWT signature + expiration
```

### **Key Security Measures**
- ✅ **Passwords**: Hashed with bcrypt (10 rounds)
- ✅ **Tokens**: RS256 JWT with 1-hour expiration
- ✅ **Refresh Tokens**: 7-day expiration, rotated on use
- ✅ **CORS**: Restricted to allowed origins
- ✅ **HTTPS Only**: TLS 1.2+ enforced
- ✅ **Rate Limiting**: 100 requests/minute per IP
- ✅ **Input Validation**: Pydantic models for all inputs
- ✅ **SQL Injection**: Parameterized queries via ORM
- ✅ **Secrets Management**: Azure Key Vault for API keys
- ✅ **Audit Logging**: All user actions logged to Cosmos DB

---

## Quota Enforcement

### **Quota Checking Points**
1. **Conversion Creation** - Check if user has remaining quota
2. **Document Upload** - Verify quota before OCR
3. **Output Generation** - Deduct quota on successful completion

### **Quota Tiers**
```
Free:       50 conversions/month
Pro:        1,000 conversions/month
Enterprise: Unlimited
```

### **Quota Reset**
- Monthly reset on subscription anniversary
- Pro-rata refunds for plan downgrades

---

## Azure Infrastructure

### **Resources**
- **App Service** - Backend API hosting (Linux, Python 3.13)
- **Static Web Apps** - Frontend hosting (auto-deploy from GitHub)
- **Cosmos DB** - Primary database (multi-region capable)
- **Blob Storage** - Document + output file storage
- **Document Intelligence** - OCR extraction
- **Azure OpenAI** - AI processing (gpt-4o, gpt-4o-mini)
- **Key Vault** - Secrets management
- **Container Registry** - Docker image storage (optional)
- **Log Analytics** - Centralized logging
- **Application Insights** - Application performance monitoring
- **Azure AD B2C** - Identity provider (optional, currently using custom JWT)

### **Deployment Architecture**
```
GitHub Repository
    ↓
GitHub Actions CI/CD Pipeline
    ↓
Build Docker Image (Python + FastAPI)
    ↓
Push to Azure Container Registry
    ↓
Deploy to App Service / Container Apps
    ↓
Static Web Apps auto-deploys frontend
```

---

## Performance Characteristics

### **Typical Latencies**
- User login: **200-500ms**
- Document upload: **1-5s** (depends on file size)
- OCR extraction: **2-10s** (depends on document complexity)
- AI summary generation: **3-8s**
- Schema recommendation: **2-5s**
- Output generation: **5-15s**
- Full conversion (end-to-end): **15-45s**

### **Scalability**
- **Horizontal**: App Service auto-scales based on load (1-10 instances)
- **Database**: Cosmos DB handles 100,000+ RU/s throughput
- **Storage**: Azure Blob Storage scales to petabytes
- **Concurrency**: Supports 1,000+ concurrent users per region

---

## Monitoring & Observability

### **Metrics Tracked**
- Request latency (by endpoint)
- Error rates (by type)
- Conversion success/failure rates
- AI processing times
- Database query performance
- Storage usage
- User quota utilization

### **Alerting**
- API error rate > 5%
- Response time > 5 seconds
- Database throttling events
- Storage quota approaching limit
- Deployment failures

### **Logging**
- Structured logging (JSON format)
- Correlation IDs for request tracing
- User action audit trail
- Error stack traces with context
- Performance timing for all operations

---

## Deployment Pipeline

### **GitHub Actions Workflow**
```yaml
Trigger: Push to main
    ↓
Run Tests (pytest)
    ↓
Build Docker Image
    ↓
Push to ACR
    ↓
Deploy to Staging (Container Apps)
    ↓
Run Integration Tests
    ↓
Deploy to Production
    ↓
Smoke Tests
```

### **Deployment Frequency**
- Main branch deploys to production automatically
- Staging environment for testing before production
- Rollback capability within 5 minutes

---

## Cost Optimization

### **Current Monthly Costs** (estimated)
- App Service (B2 instance): $50-75
- Cosmos DB (14,400 RU/s): $700-900
- Blob Storage (1TB): $20-30
- Document Intelligence (requests): $1-5 per request
- Azure OpenAI (tokens): Variable, ~$0.001-0.01 per request
- **Total**: ~$800-1000/month at launch

### **Cost Reduction Strategies**
1. Scale Cosmos DB RU/s down during off-peak
2. Use spot instances for app service
3. Implement caching to reduce AI API calls
4. Archive old conversions to cheaper storage tier
5. Implement batch processing for background tasks

---

## Guiding Principles for Development

1. **Modularity** - Each service has a single responsibility
2. **Statelesness** - Backend can be horizontally scaled
3. **Traceability** - Every action linked to `conversion_id`
4. **Durability** - No file-type conversion logic (AI-driven instead)
5. **User-Centric** - Free-text prompts, no rigid categories
6. **Quota Enforcement** - Strict limits by subscription tier
7. **Versioning** - All schema edits are versioned
8. **Scalability** - Cosmos DB partitioning, Blob Storage tiers
9. **Security** - Zero-trust architecture, encrypted data
10. **Observability** - Complete tracing of all operations

