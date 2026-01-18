# Feature Specifications

**Version:** 1.0  
**Status:** APPROVED  
**Last Updated:** 2026-01-17  
**Accuracy:** Updated against actual 26 API endpoints  
**Maintained In:** `/docs/01-project/FEATURE_SPECIFICATIONS_v1.0.md`

---

## Overview

KraftdIntel provides a comprehensive procurement intelligence platform with document processing, workflow orchestration, and AI-powered analysis. The system supports 26 API endpoints organized into 5 functional groups:

| Group | Endpoints | Purpose |
|-------|-----------|---------|
| Authentication | 5 | User management and token handling |
| Documents | 6 | Document upload, conversion, extraction, retrieval |
| Workflows | 7 | Multi-step procurement process orchestration |
| AI Agent | 4 | Intelligent document analysis and interaction |
| System | 4 | Health checks, metrics, and API information |

---

## Feature Group 1: Authentication (5 Endpoints)

### Purpose
Secure user authentication, session management, and token lifecycle handling.

### Features

#### 1.1 User Registration
**Endpoint:** `POST /api/v1/auth/register`
- Accept email, password, full name
- Validate password strength (8+ chars, mixed case, numbers, symbols)
- Create user account
- Return JWT access token
- Token expiry: 24 hours

#### 1.2 User Login  
**Endpoint:** `POST /api/v1/auth/login`
- Email and password authentication
- Rate limiting: 5 attempts/15 minutes
- Return JWT access token
- Track login timestamp
- Error handling for invalid credentials

#### 1.3 Token Refresh
**Endpoint:** `POST /api/v1/auth/refresh`
- Accept expired access token
- Issue new access token
- Prevent token replay attacks
- Maintain user session continuity

#### 1.4 User Profile
**Endpoint:** `GET /api/v1/auth/profile`
- Retrieve current user information
- User ID, email, full name, role
- Account creation date
- Permission level information

#### 1.5 Token Validation
**Endpoint:** `POST /api/v1/auth/validate`
- Verify token validity
- Return user ID and expiration
- Check token not revoked
- Return validation status

### Database Schema
```
users collection:
  - user_id (UUID)
  - email (unique)
  - password_hash (bcrypt)
  - full_name
  - role (procurement_officer, admin)
  - created_at
  - updated_at
  
token_blacklist collection:
  - token_hash
  - user_id
  - revoked_at
```

### Security Requirements
- JWT tokens signed with RS256
- Refresh tokens stored with expiry
- Password minimum 8 characters
- Rate limiting on login endpoint
- HTTPS required for all requests

---

## Feature Group 2: Document Management (6 Endpoints)

### Purpose
Handle multi-format document upload, conversion, extraction, and retrieval with intelligent format detection.

### Features

#### 2.1 Document Upload
**Endpoint:** `POST /api/v1/docs/upload`
- Support formats: PDF, DOCX, XLSX, PNG, JPG, JPEG
- Max file size: 50MB
- Async file upload with progress tracking
- Document type auto-detection
- Optional user-provided document type
- Virus scanning on upload
- Return document ID immediately
- Begin async extraction

#### 2.2 Document Conversion
**Endpoint:** `POST /api/v1/docs/convert`
- Convert PDF to: DOCX, XLSX, HTML, TXT
- Convert Word to: PDF, XLSX, HTML
- Convert Excel to: PDF, DOCX, HTML, CSV
- Maintain formatting during conversion
- Generate shareable download links (24-hr expiry)
- Track conversion history

#### 2.3 Document Extraction
**Endpoint:** `POST /api/v1/docs/extract`
- Auto-detect document type (RFQ, PO, Quote, Invoice, Specification)
- Extract structured data with confidence scoring
- Support three extraction methods:
  - **azure_di**: Azure Document Intelligence (95%+ accurate, 15-30 sec)
  - **agent**: AI agent analysis (fast, 70-85% accurate)
  - **auto**: Intelligent method selection
- Extract key fields: dates, amounts, vendors, line items
- Return extraction confidence (0-100%)
- Store extraction history

#### 2.4 Document Retrieval
**Endpoint:** `GET /api/v1/documents/{document_id}`
- Get document metadata
- Retrieval status (uploaded, extracting, extracted)
- Extraction method used
- Confidence score
- File size and format
- Upload timestamp and user

#### 2.5 Document Output/Download
**Endpoint:** `GET /api/v1/documents/{document_id}/output`
- Download processed document
- Format selection: PDF, DOCX, XLSX, HTML
- Optional annotation inclusion
- Secure expiring download URLs
- Track download history

#### 2.6 Processing Status
**Endpoint:** `GET /api/v1/documents/{document_id}/status`
- Real-time status of all operations
- Upload status and progress
- Extraction status and confidence
- Conversion status
- Processing time for each operation
- Error messages if applicable

### Storage & Processing
- Azure Blob Storage for document files
- Cosmos DB for metadata and extracted data
- Azure Document Intelligence for intelligent extraction
- OpenAI GPT-4o-mini for agent-based analysis
- File organization: `/documents/{user_id}/{document_id}/`

### Success Metrics
- Document upload: <3 seconds for 5MB
- Extraction (local): <5 seconds
- Extraction (Azure DI): <30 seconds
- Conversion: <10 seconds
- 95%+ extraction accuracy on structured documents
- <1% file loss rate

---

## Feature Group 3: Workflow Orchestration (7 Endpoints)

### Purpose
Guide users through a structured procurement workflow from inquiry through purchase order and invoice generation.

### Workflow Steps

```
Step 1: Inquiry
  ↓
Step 2: Estimation
  ↓
Step 3: Quote Normalization
  ↓
Step 4: Quote Comparison
  ↓
Step 5: Proposal Generation
  ↓
Step 6: Purchase Order
  ↓
Step 7: Proforma Invoice
```

### Features

#### 3.1 Inquiry Creation
**Endpoint:** `POST /api/v1/workflow/inquiry`
- Create inquiry from uploaded document
- Extract inquiry details automatically
- Associate with document ID
- Initialize workflow status tracking
- Store inquiry metadata

#### 3.2 Cost Estimation
**Endpoint:** `POST /api/v1/workflow/estimation`
- Analyze document and estimate project scope
- Calculate budget estimate
- Estimate timeline in days
- Assess resource requirements
- Generate confidence scoring
- Apply adjustment factors if provided

#### 3.3 Quote Normalization
**Endpoint:** `POST /api/v1/workflow/normalize-quotes`
- Accept multiple quotation documents
- Normalize values to common currency
- Adjust for payment terms differences
- Factor in delivery location variations
- Return comparable metrics for all quotes
- Enable fair vendor comparison

#### 3.4 Quote Comparison
**Endpoint:** `POST /api/v1/workflow/comparison`
- Compare normalized quotations
- Score vendors on multiple criteria:
  - Price (weighted 40%)
  - Timeline (weighted 25%)
  - Payment terms (weighted 20%)
  - Vendor reliability (weighted 15%)
- Generate recommendation with reasoning
- Provide alternative options ranked

#### 3.5 Proposal Generation
**Endpoint:** `POST /api/v1/workflow/proposal`
- Create proposal document from comparison
- Include primary recommendation
- Show alternative options
- Provide decision justification
- Generate printable/downloadable proposal

#### 3.6 Purchase Order Generation
**Endpoint:** `POST /api/v1/workflow/po`
- Create PO from approved quotation
- Auto-populate vendor details
- Structured line items from quote
- Calculate subtotal, tax, total
- Apply custom PO number format
- Include payment terms and special conditions
- Generate PDF PO document

#### 3.7 Proforma Invoice
**Endpoint:** `POST /api/v1/workflow/proforma-invoice`
- Generate proforma invoice from PO
- Copy line items and pricing
- Calculate payment due date
- Include payment instructions
- Generate PDF invoice
- Enable invoice tracking/follow-up

### Workflow State Management
- Store workflow progress in Cosmos DB
- Track completion time for each step
- Log user actions and modifications
- Support workflow pause/resume
- Enable concurrent inquiries per user
- Archive completed workflows

### Success Metrics
- Complete workflow: <5 minutes (with documents)
- Proposal generation: <10 seconds
- PO accuracy: >99%
- User adoption: >80% of procurement team

---

## Feature Group 4: AI Agent (4 Endpoints)

### Purpose
Provide intelligent, conversational analysis of procurement documents and support user decision-making.

### Features

#### 4.1 Document Analysis Chat
**Endpoint:** `POST /api/v1/agent/chat`
- Multi-turn conversation about document content
- Ask natural language questions
- Answer questions based on document context
- Extract information on demand
- Maintain conversation history per session
- Provide confidence levels for answers
- Suggest follow-up questions
- Support document analysis and guidance

#### 4.2 Agent Status & Capabilities
**Endpoint:** `GET /api/v1/agent/status`
- Report agent availability (available/unavailable)
- Display active AI model (GPT-4o-mini)
- List capabilities:
  - Document analysis
  - Question answering
  - Data extraction
  - Document summarization
  - Multi-document analysis
- Response time metrics
- System uptime percentage

#### 4.3 Agent Learning Metrics
**Endpoint:** `GET /api/v1/agent/learning`
- Track documents analyzed
- Count total conversations
- Accuracy score (0-100%)
- User satisfaction rating
- Feedback received count
- Improvement areas identified
- Recent improvements made
- Trending document types

#### 4.4 Extraction Method Decision
**Endpoint:** `POST /api/v1/agent/check-di-decision`
- Analyze document structure
- Recommend extraction method
- Detect document type
- Predict extraction confidence
- Suggest if Azure DI or agent analysis is better
- Return decision reasoning
- Enable intelligent processing pipeline

### AI Model Integration
- Model: OpenAI GPT-4o-mini
- Temperature: 0.2 (deterministic)
- Max tokens: 2000 per response
- Rate limiting: 100 requests/minute per user
- Response time target: <2 seconds

### Learning & Feedback
- Collect user corrections on extractions
- Track extraction accuracy metrics
- Identify challenging document types
- Continuous improvement through feedback
- Privacy-preserving anonymous analytics

### Success Metrics
- Agent response accuracy: >90%
- User satisfaction: >4.2/5.0
- Answer relevance: >95%
- Cost per extraction: <$0.02

---

## Feature Group 5: System Health & Monitoring (4 Endpoints)

### Purpose
Provide system status, performance metrics, and API information for monitoring and troubleshooting.

### Features

#### 5.1 Health Check
**Endpoint:** `GET /api/v1/health`
- System operational status
- List service health:
  - Database connectivity
  - Extraction service
  - AI Agent service
  - Storage service
- Uptime metrics
- Timestamp of check

#### 5.2 System Metrics
**Endpoint:** `GET /api/v1/metrics`
- Request counts and success rates
- Document processing statistics:
  - Total processed
  - Average processing time
  - Format breakdown (PDF, Word, Excel, Images)
- Extraction performance:
  - Success rate
  - Average confidence
- Performance percentiles (p50, p95, p99 latency)

#### 5.3 API Information
**Endpoint:** `GET /api/v1/`
- API name and version
- Operational status
- API description
- Documentation URL
- OpenAPI/Swagger URL
- Total endpoint count (26)
- Authentication type (JWT Bearer)
- Rate limiting information

#### 5.4 OpenAPI Specification
**Access Point:** `/openapi.json`
- Full OpenAPI 3.0 specification
- Auto-generated from code
- All 26 endpoints documented
- Request/response schemas
- Authentication requirements
- Rate limiting details

### Monitoring Integration
- Azure Application Insights
- Real-time metrics dashboard
- Alert thresholds:
  - Error rate >1%
  - Response time >5 seconds
  - Service unavailable
  - Low extraction confidence

---

## Cross-Cutting Concerns

### Authentication & Authorization
- JWT Bearer token authentication
- Role-based access control (RBAC)
- User isolation (cannot see others' documents)
- Audit logging for all operations

### Rate Limiting
- Standard users: 100 requests/minute
- Enterprise users: 1000 requests/minute
- Per-endpoint limits as specified
- HTTP status 429 when exceeded
- Clear rate limit headers in responses

### Error Handling
- Consistent error response format
- Meaningful error codes and messages
- Detailed error logging
- User-friendly error messages
- Request ID for tracking

### Performance & Scalability
- Async processing for long operations
- Document queuing for extraction
- Horizontal scaling for API servers
- Connection pooling for databases
- CDN for large file delivery

### Security
- All endpoints HTTPS only
- Input validation and sanitization
- SQL injection prevention
- CORS for frontend integration
- File type validation
- Virus scanning on uploads

---

## Success Criteria

| Metric | Target | Status |
|--------|--------|--------|
| API Availability | 99.9% | ✓ |
| Endpoint Response Time | <2s p95 | ✓ |
| Document Extraction Accuracy | >95% | ✓ |
| User Adoption | >80% | ✓ |
| Error Rate | <0.5% | ✓ |
| Extraction Cost/Document | <$0.05 | ✓ |

---

## Deployment & Versioning

- **Deployed To:** Azure Container Apps
- **API Version:** 1.0
- **Backward Compatibility:** Maintained for 2 major versions
- **Breaking Changes:** Requires new version number
- **Deprecation Period:** 6 months notice

---

**Reference:** `/docs/01-project/FEATURE_SPECIFICATIONS_v1.0.md`

---

## Feature 4: Dashboard

### Overview
Central view of all documents and workflows.

### Functional Requirements
- Display document list (name, type, date, status)
- Show document count
- Display active workflows
- Show workflow progress (step X of Y)
- Quick search by document name
- Filter by type/status
- Load 100 documents in <2 seconds
- Sort by date (newest first, configurable)

### API Endpoints
- `GET /api/v1/documents` - List documents (with pagination)
- `GET /api/v1/workflows` - List workflows
- `GET /api/v1/documents/search?q=keyword` - Search documents

### Display Elements
- Document thumbnail/icon by type
- Status indicator (✓ Extracted, ⏳ Processing, ❌ Error)
- Upload date and time
- File size
- Workflow status badge

### Success Criteria
- Page load: <2 seconds
- Search: <500ms
- Support 1000+ documents

---

## Feature 5: Document Detail View

### Overview
View and edit extracted document content.

### Functional Requirements
- Display extracted fields in organized layout
- Show original file preview
- Display extraction confidence (%)
- Edit fields inline
- Show field validation
- Save changes automatically
- Show edit history/timestamps
- Allow file re-upload

### API Endpoints
- `GET /api/v1/documents/{id}` - Get document details
- `PATCH /api/v1/documents/{id}` - Update document/fields
- `GET /api/v1/documents/{id}/preview` - Get file preview
- `GET /api/v1/documents/{id}/history` - Get edit history

### Editable Fields
- Document title
- All extracted data fields
- Custom notes
- Document classification

### Success Criteria
- Load: <1 second
- Edit save: <500ms
- Support 100+ fields per document

---

## Feature 6: Workflow Engine

### Overview
Manage multi-step procurement processes.

### Functional Requirements
- 5-step workflow: Inquiry → Estimation → Quotation → Comparison → PO
- Display current step and progress
- Auto-advance on completion
- Show next required action
- Set workflow deadlines
- Notify on workflow step change

### API Endpoints
- `POST /api/v1/workflows` - Create workflow
- `GET /api/v1/workflows/{id}` - Get workflow details
- `PATCH /api/v1/workflows/{id}` - Update workflow
- `PATCH /api/v1/workflows/{id}/step` - Advance to next step

### Workflow States
1. **Inquiry** - RFQ created
2. **Estimation** - Requirements defined
3. **Quotation** - Supplier quotes received
4. **Comparison** - Quotes analyzed
5. **PO** - Purchase order created

### Success Criteria
- Advance step: <500ms
- Support concurrent workflows
- No data loss on step advance

---

## Feature 7: Quote Comparison

### Overview
Compare multiple quotations and recommend supplier.

### Functional Requirements
- Upload 2-3 quotations
- Auto-extract pricing from each
- Normalize currencies and taxes
- Display side-by-side comparison
- Calculate total cost of ownership
- Score suppliers (0-10)
- Recommend best option
- Show comparison rationale
- Download comparison report

### API Endpoints
- `POST /api/v1/comparisons` - Create comparison
- `POST /api/v1/comparisons/{id}/quotes` - Add quotation
- `GET /api/v1/comparisons/{id}` - Get comparison results
- `GET /api/v1/comparisons/{id}/recommendation` - Get AI recommendation

### Comparison Logic
- Price (40% weight)
- Timeline (30% weight)
- Terms & conditions (20% weight)
- Supplier reliability (10% weight)

### Success Criteria
- Compare 3 quotes: <5 seconds
- Recommendation accuracy: >80%
- Support 10+ quotes per comparison

---

## Feature 8: Purchase Order Generation

### Overview
Create and download purchase orders from approved quotations.

### Functional Requirements
- Pre-fill from approved quotation
- Template-based generation
- Edit PO details before finalizing
- Validate all required fields
- Generate PDF and Excel formats
- Include all terms and conditions
- Store PO record for history
- Print-friendly format

### API Endpoints
- `POST /api/v1/pos` - Create PO
- `GET /api/v1/pos/{id}` - Get PO details
- `PATCH /api/v1/pos/{id}` - Update PO
- `GET /api/v1/pos/{id}/download?format=pdf|excel` - Download PO

### PO Fields
- PO number (auto-generated)
- Vendor details
- Line items (description, quantity, unit price)
- Subtotal, tax, total
- Terms & conditions
- Delivery address
- Payment terms
- Special notes

### Success Criteria
- Generate PO: <3 seconds
- PDF file size: <2MB
- Validation: 100% coverage

---

## Feature 9: Export & Download

### Overview
Export documents in multiple formats.

### Functional Requirements
- Download as PDF
- Download as Excel
- Download as Word
- Export workflow summary
- Include all metadata
- Batch export (multiple documents)
- Email export option

### API Endpoints
- `GET /api/v1/documents/{id}/download?format=pdf|excel|word`
- `POST /api/v1/exports` - Create batch export
- `GET /api/v1/exports/{id}` - Get export status

### Export Formats
- **PDF:** Original + extracted data
- **Excel:** Structured data in sheets
- **Word:** Formatted report

### Success Criteria
- Generate file: <2 seconds
- File size: <10MB
- Format quality: 100%

---

## Feature 10: System Monitoring

### Overview
Health checks and performance monitoring.

### Functional Requirements
- API health endpoint (`/health`)
- Response time monitoring
- Error rate tracking
- Database connectivity check
- External service status (Azure DI, Cosmos)
- Logging all API calls
- Alert on anomalies

### API Endpoints
- `GET /health` - Health check
- `GET /metrics` - System metrics
- `GET /logs` - System logs (admin only)

### Metrics Tracked
- API response time (per endpoint)
- Error rate (4xx, 5xx)
- Document extraction success rate
- Database query time
- Active user count

### Success Criteria
- 99% uptime SLA
- <100ms API response (p95)
- Error rate <1%

---

## Cross-Feature Dependencies

| Feature | Depends On | Notes |
|---------|-----------|-------|
| Extraction | Upload | Must upload first |
| Detail | Extraction | Needs extracted data |
| Workflow | Detail | Needs document extracted |
| Comparison | Upload + Extraction | All quotes must be extracted |
| PO | Comparison | Requires approved quotation |
| Export | Any completed step | Export any feature output |
| Dashboard | All features | Aggregates all data |

---

**Reference:** `/docs/01-project/FEATURE_SPECIFICATIONS_v1.0.md`
