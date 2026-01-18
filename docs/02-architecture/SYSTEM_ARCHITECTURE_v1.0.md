# System Architecture Overview

**Version:** 1.0  
**Status:** APPROVED  
**Last Updated:** 2026-01-17  

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    KRAFTDINTEL ARCHITECTURE                 │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   CLIENT LAYER   │
│                  │
│  React SPA       │
│  TypeScript      │
│  Vite Build      │
└────────┬─────────┘
         │ HTTPS
         ↓
┌──────────────────────────────┐
│  PRESENTATION LAYER          │
│                              │
│  Azure Static Web App        │
│  - Frontend hosting          │
│  - CDN distribution          │
│  - CORS configuration        │
└────────┬─────────────────────┘
         │ HTTP/REST
         ↓
┌──────────────────────────────────────────────────┐
│          API GATEWAY / LOAD BALANCER             │
│  (Azure Container Apps - Ingress)                │
└────────┬─────────────────────────────────────────┘
         │
         ↓
┌──────────────────────────────────────────────────┐
│         APPLICATION LAYER (Backend)              │
│                                                  │
│  FastAPI Microservices (Container Apps)          │
│  ├─ Auth Service (JWT tokens)                    │
│  ├─ Document Service (upload, metadata)          │
│  ├─ Extraction Service (local + Azure DI)        │
│  ├─ Workflow Service (orchestration)             │
│  └─ Export Service (PDF, Excel generation)       │
│                                                  │
│  Languages: Python 3.13                          │
│  Framework: FastAPI                              │
│  Container: Docker (Azure Container Apps)        │
└────────┬──────────────────────────────────────────┘
         │
    ┌────┴─────┬─────────────┬──────────────┐
    │           │             │              │
    ↓           ↓             ↓              ↓
┌──────┐ ┌──────────┐ ┌─────────┐ ┌──────────────┐
│Cosmos│ │ Azure DI │ │Blob Str │ │ Key Vault    │
│  DB  │ │Document  │ │ Storage │ │(Secrets)     │
│(Data)│ │Intell    │ │(Files)  │ │(API Keys)    │
└──────┘ └──────────┘ └─────────┘ └──────────────┘

Supporting Services:
├─ Application Insights (Monitoring)
├─ Log Analytics (Logs)
└─ Azure Identity (Authentication)
```

---

## Core Components

### 1. Frontend (React + TypeScript)
- **Technology:** React 18, Vite, TypeScript
- **Hosting:** Azure Static Web App
- **Features:**
  - Dashboard component
  - Document upload component
  - Document detail view
  - Workflow status display
  - Quote comparison view
  - PO creation form
  - Export functionality
- **State:** React Context API
- **API Client:** Fetch API + error handling

### 2. Backend (FastAPI)
- **Technology:** FastAPI, Python 3.13
- **Hosting:** Azure Container Apps
- **Features:**
  - RESTful API endpoints (26+)
  - JWT authentication
  - Request validation (Pydantic)
  - Error handling & logging
  - Document processing orchestration
  - Workflow state management
- **Database:** Cosmos DB (MongoDB API)
- **Async:** asyncio + httpx for concurrent operations

### 3. Data Layer (Cosmos DB)
- **Database:** MongoDB API (Cosmos DB)
- **Collections:**
  - `users` - User accounts and credentials
  - `documents` - Document metadata
  - `extracted_data` - Extracted fields and content
  - `workflows` - Workflow status and history
  - `comparisons` - Quote comparison results
  - `pos` - Purchase order records
  - `audit_log` - Change history for compliance

### 4. Storage Layer (Azure Blob)
- **Purpose:** Store original document files
- **Organization:** `{user_id}/{document_id}/{filename}`
- **Access:** SAS tokens for secure download
- **Lifecycle:** Auto-delete after 90 days (configurable)

### 5. Intelligence Layer (Azure Document Intelligence)
- **Purpose:** Extract structured data from documents
- **Models:** Pre-trained models for business documents
- **Fallback:** Local extraction if Azure DI unavailable
- **Confidence Score:** Returned with each extraction
- **Supported Formats:** PDF, Word, Excel, Images

### 6. Security Layer (Azure Key Vault)
- **Stores:** Database connection strings, API keys
- **Access:** Managed Identity (no credential storage)
- **Rotation:** Automatic key rotation
- **Audit:** Complete access logging

---

## Data Flow

### Document Upload Flow
```
1. User uploads file (Frontend)
2. File sent to Backend (multipart/form-data)
3. Backend validates file (type, size)
4. Stored in Azure Blob Storage
5. Metadata saved to Cosmos DB
6. Extraction job queued
7. Return document ID to Frontend
```

### Document Extraction Flow
```
1. Extraction service receives document ID
2. Retrieve file from Blob Storage
3. Attempt local extraction (fast)
4. If confidence <80%:
   - Use Azure Document Intelligence
   - Higher accuracy (95%+)
   - Takes 5-10 seconds longer
5. Store results in Cosmos DB
6. Notify Frontend via API poll/WebSocket
```

### Quote Comparison Flow
```
1. User uploads 2-3 quotations
2. Each automatically extracted
3. Comparison service loads extracted data
4. Normalizes pricing (currencies, taxes)
5. Calculates scoring:
   - Price weight: 40%
   - Timeline weight: 30%
   - Terms weight: 20%
   - Reliability weight: 10%
6. Generates recommendation
7. Display to user for approval
```

---

## External Service Integrations

| Service | Purpose | Fallback |
|---------|---------|----------|
| Azure Document Intelligence | Extract document data | Local extraction (lower accuracy) |
| Azure Blob Storage | Store files | (N/A - critical) |
| Cosmos DB | Store application data | (N/A - critical) |
| Azure Container Apps | Host backend | (N/A - critical) |
| Azure Static Web App | Host frontend | (N/A - critical) |
| Key Vault | Manage secrets | (N/A - critical) |
| Application Insights | Monitor system | (N/A - optional) |

---

## Scaling Strategy

### Horizontal Scaling
- **Frontend:** CDN automatically scales (Static Web App)
- **Backend:** Container Apps auto-scales 0-10 instances based on CPU
- **Database:** Cosmos DB provisions RU/s as needed

### Rate Limiting
- Per-user API rate limit: 100 requests/minute
- Per-endpoint rate limit: Varies by operation
- Queue long-running jobs (extraction)

### Caching
- Frontend: Browser cache + service worker
- Backend: Redis cache layer (future enhancement)
- Static assets: CDN cache (30 days)

---

## Security Architecture

```
┌─────────────────────────────────────┐
│   USER AUTHENTICATION (JWT)         │
│   ├─ Email/password login           │
│   ├─ Session token (24h expiry)     │
│   └─ Secure cookie storage          │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   AUTHORIZATION (Role-based)        │
│   ├─ Admin: Full access             │
│   ├─ Manager: Approve quotes        │
│   └─ Officer: Upload/process docs   │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   ENCRYPTION (TLS 1.3)              │
│   ├─ All data in transit encrypted  │
│   ├─ HTTPS-only endpoints           │
│   └─ No insecure fallbacks          │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   DATA PROTECTION                   │
│   ├─ Secrets in Key Vault           │
│   ├─ No hardcoded credentials       │
│   ├─ Database encryption at rest    │
│   └─ File-level access control      │
└─────────────────────────────────────┘
```

---

## Deployment Architecture

```
GitHub Repository (Knotcreativ/kraftd)
         │
         ├─ Frontend/ (React)
         │  └─→ GitHub Actions build
         │      └─→ Azure Static Web App
         │
         └─ Backend/ (FastAPI)
            └─→ Docker build
               └─→ Azure Container Registry
                  └─→ Container Apps
```

---

## Performance Targets

| Component | Target | Actual |
|-----------|--------|--------|
| Frontend load | <2s | <1.5s |
| API response | <500ms | <200ms |
| Document extraction | <10s | <5s (local), <30s (Azure) |
| Quote comparison | <5s | <3s |
| PO generation | <3s | <2s |
| Database query | <100ms | <50ms |
| Overall uptime | 99% | 99.5% |

---

## Disaster Recovery

- **Backup:** Daily snapshots of Cosmos DB
- **Recovery Time Objective (RTO):** 1 hour
- **Recovery Point Objective (RPO):** 24 hours
- **Failover:** Automatic to secondary region (future)

---

**Reference:** `/docs/02-architecture/SYSTEM_ARCHITECTURE_v1.0.md`
