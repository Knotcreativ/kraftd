# Backend Architecture Document

**Version:** 1.0  
**Status:** APPROVED  
**Framework:** FastAPI (Python 3.13)  
**Last Updated:** 2026-01-17

---

## Backend Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Client (Frontend)                      │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Application Server                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               API Routes Layer                        │   │
│  │  /auth  /documents  /workflows  /comparisons  /pos   │   │
│  └────────────┬──────────────────────────────────────┬──┘   │
│               │                                        │      │
│  ┌────────────▼──────────────────────────────────────▼──┐   │
│  │          Business Logic Layer (Services)            │   │
│  │  AuthService  DocumentService  WorkflowService      │   │
│  └────────────┬──────────────────────────────────────┬──┘   │
│               │                                        │      │
│  ┌────────────▼──────────────────────────────────────▼──┐   │
│  │           Data Access Layer (Repositories)         │   │
│  │  UserRepository  DocumentRepository  etc.          │   │
│  └────────────┬──────────────────────────────────────┬──┘   │
│               │                                        │      │
└───────────────┼────────────────────────────────────────┼──────┘
                │                                        │
        ┌───────▼────────────┐              ┌──────────▼────┐
        │   Cosmos DB        │              │  Azure Blob   │
        │   (MongoDB API)    │              │   Storage     │
        └────────────────────┘              └───────────────┘
```

---

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration management
├── dependencies.py         # Dependency injection
├── schemas.py              # Pydantic models (data validation)
├── middleware.py           # Auth, logging, error handling
├── requirements.txt        # Python dependencies
│
├── routes/
│   ├── auth.py            # Authentication endpoints
│   ├── documents.py       # Document management endpoints
│   ├── workflows.py       # Workflow endpoints
│   ├── comparisons.py     # Comparison endpoints
│   └── purchase_orders.py # PO generation endpoints
│
├── services/
│   ├── auth_service.py        # JWT, password management
│   ├── document_service.py    # Upload, extraction orchestration
│   ├── extraction_service.py  # Azure Document Intelligence
│   ├── workflow_service.py    # Workflow state machine
│   ├── comparison_service.py  # Quote comparison logic
│   └── po_service.py          # PO generation
│
├── repositories/
│   ├── base_repository.py     # Generic CRUD operations
│   ├── user_repository.py     # User data access
│   ├── document_repository.py # Document persistence
│   ├── workflow_repository.py # Workflow state
│   └── po_repository.py       # PO data access
│
├── models/
│   ├── user.py        # User domain model
│   ├── document.py    # Document domain model
│   └── workflow.py    # Workflow domain model
│
├── external/
│   ├── document_intelligence.py  # Azure DI integration
│   ├── blob_storage.py           # Azure Blob Storage
│   ├── cosmos_db.py              # Cosmos DB driver
│   └── email_service.py          # Email notifications
│
└── utils/
    ├── logger.py       # Logging configuration
    ├── exceptions.py   # Custom exceptions
    ├── validators.py   # Input validation
    └── helpers.py      # Utility functions
```

---

## Core Components

### 1. API Routes Layer
**File:** `routes/*.py`

**Responsibilities:**
- HTTP request/response handling
- Input validation (Pydantic schemas)
- Response formatting
- Error handling & status codes

**Example (documents.py):**
```python
@router.post("/documents/upload")
async def upload_document(
    file: UploadFile,
    document_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    # Validate file
    # Call DocumentService
    # Return response
```

**26 Endpoints Across Routes:**
- Auth: login, logout, refresh_token (3)
- Documents: upload, list, get, update, delete (5)
- Workflows: create, get, list, update_step (4)
- Comparisons: create, get, list (3)
- POs: create, get, list, update_status, finalize (5)
- Export: download_pdf, download_excel (2)
- Health: health_check (1)

### 2. Business Logic Layer
**File:** `services/*.py`

**Components:**

#### AuthService
```python
class AuthService:
    - login(email, password) -> access_token
    - validate_token(token) -> User
    - hash_password(password) -> hash
    - verify_password(password, hash) -> bool
    - refresh_token(token) -> new_token
```

#### DocumentService
```python
class DocumentService:
    - upload_document(file, user_id) -> Document
    - extract_data(document_id) -> extraction_result
    - get_document(document_id, user_id) -> Document
    - update_extraction(document_id, data) -> Document
    - delete_document(document_id, user_id) -> bool
    - orchestrate_extraction() # coordinates extraction pipeline
```

#### WorkflowService
```python
class WorkflowService:
    - create_workflow(document_id, type) -> Workflow
    - get_workflow(workflow_id) -> Workflow
    - advance_step(workflow_id) -> Workflow
    - validate_step_completion(workflow_id, step) -> bool
```

#### ComparisonService
```python
class ComparisonService:
    - create_comparison(workflow_id, quotations) -> Comparison
    - score_quotations(quotations, criteria) -> Scores
    - recommend_best(scores) -> Recommendation
```

#### POService
```python
class POService:
    - generate_po(comparison_id, selected_quote) -> PurchaseOrder
    - update_po(po_id, changes) -> PurchaseOrder
    - finalize_po(po_id) -> PurchaseOrder
    - send_to_vendor(po_id) -> bool
```

### 3. Data Access Layer
**File:** `repositories/*.py`

**Pattern:** Repository Pattern for data abstraction

```python
class BaseRepository:
    async def create(self, model: BaseModel)
    async def read(self, id: str)
    async def update(self, id: str, data: dict)
    async def delete(self, id: str)
    async def list(self, filters: dict, skip: int, limit: int)
```

**Implementations:**
- `UserRepository` - User authentication & profiles
- `DocumentRepository` - Document records & metadata
- `WorkflowRepository` - Workflow state management
- `ComparisonRepository` - Comparison results
- `PORepository` - Purchase order records

### 4. Schemas Layer
**File:** `schemas.py`

**Purpose:** Data validation & API contract definition

```python
class DocumentUploadRequest(BaseModel):
    filename: str
    document_type: Optional[str]
    file_size: int

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    uploaded_at: datetime
```

### 5. Middleware & Security
**File:** `middleware.py`

**Components:**
- JWT Authentication middleware
- CORS configuration
- Error handling middleware
- Request logging middleware
- Rate limiting

```python
# Dependency for protecting routes
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Validate token
    # Return authenticated user
```

### 6. External Integrations
**File:** `external/*.py`

#### Azure Document Intelligence Integration
```python
class AzureDocumentIntelligence:
    async def extract_from_file(file_path) -> ExtractionResult
    - Sends document to Azure DI
    - Parses response
    - Returns structured data
    - Handles confidence scores
```

#### Azure Blob Storage Integration
```python
class AzureBlobStorage:
    async def upload_file(file_content, path) -> url
    async def download_file(path) -> binary_data
    async def delete_file(path) -> bool
```

#### Cosmos DB Integration
```python
class CosmosDBClient:
    - Connection pooling
    - Database selection
    - Collection management
    - Query execution
```

---

## Data Flow: Document Upload & Extraction

```
1. User uploads file via POST /documents/upload
   ├─ Routes layer validates input
   ├─ DocumentService.upload_document() called
   │  ├─ Stores metadata in Cosmos DB
   │  └─ Uploads file to Blob Storage
   │
2. Extraction triggered (async)
   ├─ DocumentService.extract_data() called
   ├─ Sends document to Azure Document Intelligence
   │  └─ Azure DI returns structured extraction
   │
3. Store extraction results
   ├─ ExtractionService processes response
   ├─ Stores extracted_data in Cosmos DB
   └─ Updates document status to "extracted"
   
4. Return to user
   └─ Document available for workflow processing
```

---

## Data Flow: Workflow & Purchase Order Generation

```
1. Create workflow
   ├─ User initiates workflow on document
   ├─ WorkflowService creates workflow record
   └─ Sets initial step and status
   
2. Add quotations
   ├─ User uploads quotations from vendors
   ├─ Each quotation stored as document
   └─ Linked to workflow
   
3. Create comparison
   ├─ ComparisonService collects quotations
   ├─ Applies scoring criteria
   │  ├─ Price weight: 40%
   │  ├─ Timeline weight: 30%
   │  ├─ Terms weight: 20%
   │  └─ Rating weight: 10%
   └─ Generates recommendation
   
4. Generate PO
   ├─ User selects recommended quotation
   ├─ POService.generate_po() creates PO
   ├─ Populates all line items
   ├─ Stores in Cosmos DB
   └─ Ready for approval/sending
```

---

## Error Handling Strategy

**Custom Exceptions:**

```python
class KraftdIntelException(Exception):
    """Base exception"""

class AuthenticationException(KraftdIntelException):
    """JWT validation failed"""

class DocumentProcessingException(KraftdIntelException):
    """Azure DI extraction failed"""

class ValidationException(KraftdIntelException):
    """Input validation failed"""
```

**Error Response Format:**
```json
{
  "error": "validation_error",
  "message": "Invalid email format",
  "details": {"email": "must be valid email"},
  "timestamp": "2026-01-17T10:30:00Z"
}
```

---

## Performance Optimizations

| Strategy | Implementation |
|----------|-----------------|
| Async I/O | All database & external calls async |
| Connection pooling | Reuse DB/API connections |
| Caching | Cache user roles, company config |
| Background jobs | Extract documents asynchronously |
| Pagination | 20-item default page size |
| Indexes | Cosmos DB indexes on query fields |
| Compression | GZIP response compression |

---

## Security Measures

| Layer | Implementation |
|-------|-----------------|
| Authentication | JWT with expiring tokens |
| Authorization | Role-based access control |
| Encryption | TLS for all network traffic |
| Secrets | Azure Key Vault for credentials |
| Input validation | Pydantic schema validation |
| CORS | Configured for frontend domain |
| Rate limiting | 100 req/min per user |
| SQL Injection | Parameterized queries only |
| CSRF | CORS tokens for state-changing ops |

---

## Deployment Configuration

**Production Environment:**
- Language: Python 3.13
- Framework: FastAPI + Uvicorn
- Hosting: Azure Container Apps
- Database: Cosmos DB (MongoDB API)
- Storage: Azure Blob Storage
- Secrets: Azure Key Vault
- Monitoring: Application Insights

**Environment Variables:**
```
COSMOS_CONNECTION_STRING=<key_vault_reference>
COSMOS_DATABASE=kraftdintel
AZURE_STORAGE_CONNECTION_STRING=<key_vault_reference>
DOCUMENT_INTELLIGENCE_KEY=<key_vault_reference>
DOCUMENT_INTELLIGENCE_ENDPOINT=<endpoint>
JWT_SECRET_KEY=<key_vault_reference>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

---

**Reference:** `/docs/02-architecture/BACKEND_ARCHITECTURE_v1.0.md`
