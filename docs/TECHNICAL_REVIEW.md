# KraftdIntel Backend - Technical Review
## Correctness, Stability, and Testability Analysis

---

## 1. API ROUTES & RESPONSIBILITIES

### Route Modules (11 files)

| Route | Responsibility | Endpoints Count |
|-------|--------------|-----------------|
| **auth.py** | JWT authentication, email verification, password reset | ~8 |
| **user_profile.py** | User profiles, preferences, avatars, data export | ~8 |
| **templates.py** | Document templates (CRUD), generation, validation | ~8 |
| **signals.py** | Price trends, alerts, supplier analytics, predictions | ~13 |
| **streaming.py** | WebSocket channels (alerts, prices, signals, trends, health) | 6 WS + 3 HTTP |
| **events.py** | Event history queries (price, alert, anomaly, signal, trend events) | ~8 |
| **ml_predictions.py** | ML models (risk, price, supplier reliability, batch prediction) | ~7 |
| **advanced_ml.py** | Advanced analytics (mobility, pricing index, supplier ecosystem) | ~6 |
| **agent.py** | Document analysis, chat, agent status | ~4 |
| **admin.py** | User management, role management, audit logs, system stats | ~8 |
| **__init__.py** | Route registration | - |

**Issues Identified:**
- ✅ **Good**: Clear separation of concerns, stable endpoint organization
- ⚠️ **Moderate**: `agent.py` lacks detailed validation for document_id uniqueness
- ⚠️ **Moderate**: `streaming.py` has 6 WebSocket endpoints with token verification — potential for denial-of-service if many clients connect without proper backpressure handling

---

## 2. CORE SERVICES ANALYSIS

### Authentication & Authorization (3 services)

**auth_service.py**
- JWT token generation (HS256)
- Password hashing (bcrypt)
- Email verification flow
- ✅ Follows industry standard practices
- ⚠️ No token blacklist/revocation mechanism (logout = client-side deletion only)

**token_service.py**
- Token creation and validation
- Token rotation support
- Expiration handling with refresh token logic
- ✅ Proper exception handling (ExpiredSignatureError, InvalidTokenError)
- ⚠️ No configurable secret rotation strategy

**rbac_service.py**
- Role-based access control (USER, ADMIN, MANAGER)
- Permission enforcement
- ✅ Clean enum-based role system
- ⚠️ No fine-grained resource-level permissions beyond ownership checks

### Multi-Tenancy (1 service)

**tenant_service.py**
- Tenant context isolation
- Cross-tenant access prevention
- Partition key enforcement
- ✅ **Critical fix applied**: Ownership keys now include tenant_id
- ✅ Context validation on every request
- ⚠️ Context stored in thread-local/request context — verify async safety

### Resource Ownership (1 service)

**ownership_service.py** [RECENTLY FIXED]
- Resource ownership validation
- Access control with sharing support
- Multi-tenant key format: `{tenant_id}:{type}:{id}`
- ✅ **Fix verified**: 230/230 tests passing
- ✅ In-memory dictionary for dev; production-ready for Cosmos DB migration
- ⚠️ No audit trail for ownership transfers or access grants
- ⚠️ No expiration on shared resource access

### Document Processing (2 main classes)

**orchestrator.py** - ExtractionPipeline
- 4-stage pipeline: Classify → Map → Infer → Validate
- Handles PDFs, Word, Excel, Images
- Returns PipelineResult with completeness scores
- ✅ Clean stage architecture
- ✅ Proper error handling at each stage
- ⚠️ **Timeout**: DOCUMENT_PROCESSING_TIMEOUT = 25s — may fail for large documents
- ⚠️ **No rate limiting** per user on document uploads

**azure_service.py** - Azure Document Intelligence
- Optional integration for advanced OCR/extraction
- Fallback to pdfplumber/python-docx if unavailable
- ✅ Graceful degradation if Azure credentials missing
- ⚠️ No caching of extraction results; every re-upload re-processes

### Database & Persistence (3 services)

**cosmos_service.py** - Azure Cosmos DB Client
- Singleton pattern with lazy initialization
- Supports connection retries
- ✅ Best practices: Microsoft-documented patterns
- ✅ Proper initialization/shutdown hooks
- ⚠️ No connection pooling configuration exposed
- ⚠️ No retry policy with exponential backoff configurable

**document_repository.py** - Document CRUD
- Partition key: `owner_email` (single-user queries efficient)
- Status tracking: PENDING → PROCESSING → COMPLETED/FAILED
- TTL-based cleanup (90 days default)
- ✅ Clear document status enum
- ⚠️ **Cross-partition queries not optimized**: Listing all documents requires full scan
- ⚠️ No pagination for large result sets
- ⚠️ Missing indexes for status, document_type, created_at queries

**template_storage.py** - Template Management
- In-memory template storage with persistence option
- Supports CRUD, duplication, validation
- ✅ Template syntax validation via Jinja2
- ⚠️ No template versioning
- ⚠️ Orphaned templates not auto-cleaned

### Business Logic Services (4 key services)

**signals_service.py** - Risk Analysis
- Price trend analysis (moving averages, volatility, forecasting)
- Anomaly detection
- Supplier performance scoring
- ✅ Statistical algorithms implemented correctly
- ⚠️ **No input validation**: accepts empty price lists (may divide by zero)
- ⚠️ **Simple forecasting**: Exponential smoothing (α=0.3) may be insufficient for procurement
- ⚠️ No confidence intervals on predictions

**email_service.py** - SendGrid Integration
- Verification, password reset, alert notifications
- ✅ Proper error handling with logging
- ✅ Graceful fallback if API unavailable
- ⚠️ **No rate limiting on email sends** (potential spam vector)
- ⚠️ **No template management** (hardcoded email content)

**alert_service.py** - Alert Generation
- Multi-channel alerts (email, in-app, WebSocket)
- Alert severity levels (LOW, MEDIUM, HIGH, CRITICAL)
- ✅ Proper alert handler pattern
- ⚠️ **Generic exception handling** (bare `except:` on line 304) hides errors
- ⚠️ No deduplication; same alert triggered multiple times

**export_tracking_service.py** - Export Workflow State Machine
- 4-stage tracking: Requested → Processing → Ready → Downloaded
- Supports PDF, JSON, CSV, Excel exports
- ✅ Comprehensive state management
- ✅ Proper error logging at each stage
- ⚠️ No concurrent export limits (potential resource exhaustion)
- ⚠️ No cleanup of stale export records

---

## 3. DOCUMENT UPLOAD → EXTRACTION → STORAGE → EXPORT FLOW

### End-to-End Process

```
1. User uploads file (Frontend: DocumentUpload.tsx)
   ↓
2. POST /documents/upload or /agent/analyze (Route handler)
   ↓
3. Determine document type (extension-based or ML classifier)
   ↓
4. Select processor (PDFProcessor, WordProcessor, ExcelProcessor, ImageProcessor)
   ↓
5. Extract content (pdfplumber, python-docx, openpyxl, pytesseract)
   ↓
6. Run ExtractionPipeline (Classify → Map → Infer → Validate)
   ↓
7. Optional: Call Azure Document Intelligence for advanced features
   ↓
8. Store KraftdDocument in Cosmos DB (documents collection)
   ↓
9. Trigger KraftdAIAgent (GPT-4o mini) for analysis
   ↓
10. Calculate risk signals (signals_service.py)
   ↓
11. Generate alerts (alert_service.py)
   ↓
12. Broadcast events via WebSocket (event_broadcaster.py)
   ↓
13. Export (PDF/JSON/CSV) via export_tracking_service.py
   ↓
14. User downloads results
```

### Critical Path Issues

| Step | Timeout | Issue | Recommendation |
|------|---------|-------|-----------------|
| 3-4 | 20s | File extraction may timeout on large PDFs (50+ pages) | Add streaming extraction |
| 5-6 | 25s | OCR on scanned images slow | Use Azure batch endpoint for images |
| 9 | N/A | GPT-4o mini API latency variable (no timeout defined) | Add 30s timeout + fallback to rule-based analysis |
| 12 | N/A | WebSocket broadcast blocking if client slow | Use async queue with backpressure |
| 13 | N/A | Export generation can timeout | Make async, return job ID instead |

### Validations Missing

- ❌ **File size validation**: 25 MB limit in config, but no pre-upload check
- ❌ **File type validation**: Extension-based only; MIME type not validated
- ❌ **Duplicate detection**: Same file uploaded twice = 2 separate records
- ❌ **Content validation**: No checks for malformed PDFs, corrupt files
- ❌ **Virus scanning**: No antivirus integration

---

## 4. COSMOS DB USAGE

### Collections & Partition Keys

| Collection | Partition Key | TTL | Purpose |
|-----------|---------------|----|---------|
| documents | /owner_email | 90 days | Document records with metadata |
| signals | /tenant_id | N/A | Risk signals and alerts |
| events | /tenant_id | 30 days | Event audit trail |
| templates | /tenant_id | N/A | Document templates |
| users | /email | N/A | User accounts and profiles |
| audit | /tenant_id | 2555 days | Compliance audit logs |

### Best Practices Assessment

✅ **Implemented:**
- Partition keys chosen for tenant/user isolation
- TTL configured for automatic cleanup
- Cosmos service singleton pattern
- Lazy initialization with error handling

⚠️ **Not Implemented:**
- **No indexes defined** for common queries (status, document_type, created_at)
- **No composite indexes** for multi-column filters
- **No cross-partition optimization** (e.g., querying all docs by status requires full scan)
- **No RU budgeting strategy** (no monitoring of RU consumption)
- **No bulk insert optimization** (single inserts for batch operations)
- **No connection string rotation** (hardcoded in Key Vault, no refresh)

### Query Patterns (Performance Risk)

```python
# GOOD (partition-scoped)
GET /documents/{document_id}?owner_email=user@domain.com
→ Single partition query, O(1) RU cost

# BAD (cross-partition)
GET /documents/statistics?status=PENDING
→ Full collection scan, O(n) RU cost, scales poorly
```

---

## 5. SECRETS & CONFIG HANDLING

### Configuration Approach

**File: config.py**
- Environment variables with sensible defaults
- Validation function `validate_config()` on startup
- Timeouts, rate limits, logging levels configurable
- ✅ Clear separation of concerns
- ✅ Validation before app startup

**File: secrets_manager.py**
- Azure Key Vault integration
- Retrieves: DB connection, API keys, SendGrid tokens
- ✅ Secrets never logged
- ✅ Fallback to .env for local dev

### Issues Identified

❌ **Critical:**
- No secret rotation mechanism
- API keys visible in logs if exception occurs with context
- No expiration warnings for soon-to-rotate secrets
- Environment variables exposed in Docker if ENV printed to logs

⚠️ **Moderate:**
- .env files not in .gitignore (potential leaks in Git history)
- SendGrid API key passed as plain HTTP header (no encoding)
- Database credentials stored in Key Vault but no circuit breaker if Key Vault down

### Recommendations

1. Implement Key Vault secret rotation with automatic refresh
2. Add audit logging for secret access
3. Use managed identities instead of connection string keys
4. Implement circuit breaker pattern for Key Vault calls

---

## 6. POTENTIAL ISSUES & MISSING VALIDATIONS

### Critical Issues (Should Fix Before Production at Scale)

| Issue | Severity | Impact | Fix |
|-------|----------|--------|-----|
| No input validation on document_id, resource_id | High | Injection attacks, cross-tenant access | Add Pydantic validators |
| Timeout not set on GPT-4o mini API calls | High | Requests hang indefinitely | Add 30s timeout + fallback |
| No rate limiting per user/tenant | High | DoS attacks, quota exhaustion | Implement token bucket limiter |
| Concurrent export requests unlimited | High | Memory exhaustion, OOM crashes | Queue with max concurrency |
| WebSocket broadcast blocking | Medium | Slow clients block all clients | Use async queue + timeout |
| Bare `except:` in alert_service.py | Medium | Silent failures, hidden bugs | Replace with specific exception types |
| No duplicate document detection | Medium | Storage waste, confusion | Add hash-based dedup |
| Ownership keys migration incomplete | Low | Multitenancy violations if old format used | Migrate all old records |

### Missing Validations

```python
# Missing in routes
- Document ID format validation (UUID vs string?)
- File size limits enforced
- File MIME type checking
- Owner_email domain allowlist
- Supplier ID format validation
- Price value ranges (negative prices?)
- Alert threshold ranges (0-100?)

# Missing in services
- Empty price list handling in signals_service.py
- Null/None checks in orchestrator.py
- Connection failure retries (no exponential backoff)
- Email address format validation
```

### Performance Risks for High-Volume B2C

| Scenario | Risk | Mitigation |
|----------|------|-----------|
| 1000 concurrent uploads | Memory: PDF extraction buffered in RAM | Stream extraction, use temp disk |
| 100+ documents per user | Query perf: O(n) partition scan | Add indexes on status, date |
| Real-time signal calculation | CPU: Calculations blocking request thread | Move to background job queue |
| WebSocket broadcast to 10k+ users | Memory/Network: All messages buffered | Use pub/sub (Redis) instead |
| Cosmos DB spike (1M RU/s) | Throttling (429): Requests fail | Implement backoff + retry queue |

---

## 7. IMPROVEMENTS FOR HIGH-VOLUME B2C DOCUMENT CONVERSION

### Architecture Recommendations

**1. Async Processing Pipeline**
```
Current: Request → Extract → Analyze → Store → Response (blocking)
Proposed: Request → Queue → Return Job ID
          Background: Extract → Analyze → Store → Webhook
```
- **Benefit**: Non-blocking uploads, better UX for large files
- **Implementation**: Use Azure Service Bus or RabbitMQ

**2. Document Extraction Streaming**
```python
# Current: pdfplumber.load(file) → all pages loaded
# Proposed: Generator yielding pages one-at-a-time
for page in stream_pdf_pages(file):
    text = extract_page(page)
    store_partial_result()  # Early detection of issues
```

**3. Caching Layer**
- Cache extraction results (same file hash → reuse results)
- Cache ML predictions (price predictions, risk scores)
- Use Redis for hot data

**4. Request Isolation & Limits**
```python
# Add per-user limits
MAX_UPLOADS_PER_HOUR = 100
MAX_CONCURRENT_EXTRACTIONS = 5
MAX_EXPORT_JOBS = 10
```

**5. Database Optimization**
```sql
-- Add indexes
CREATE INDEX idx_status ON documents (owner_email, status)
CREATE INDEX idx_created ON documents (owner_email, created_at DESC)
CREATE COMPOSITE INDEX idx_search ON documents (owner_email, document_type, status)
```

**6. Monitoring & Observability**
- Add Application Insights for all operations
- Track: extraction time, API latency, error rates
- Set alerts for: timeout rate > 5%, Cosmos RU > 80%
- Log diagnostic info for failed extractions

**7. Circuit Breaker for External APIs**
```python
# GPT-4o mini, Azure Document Intelligence, SendGrid
# If failure rate > 30%, pause requests, return 503
# Exponential backoff: 1s → 2s → 4s → max 60s
```

**8. Batch Processing Optimization**
```python
# For bulk imports (>100 documents)
Batch → Parallel extraction (4 workers)
      → Batch insert to Cosmos DB
      → Batch signal calculation
      → Single webhook notification
```

### Code Quality Improvements

| Area | Current | Recommended |
|------|---------|-------------|
| Error handling | Mixed (try/except + logging) | Structured exceptions + Sentry/AppInsights |
| Logging | Per-file logging config | Centralized structured logging (JSON) |
| Testing | 230 tests, 100% pass rate ✅ | Add load tests (concurrent uploads), chaos tests |
| Type hints | Partial (Tuple, List, Dict) | Full typing with `mypy` strict mode |
| Documentation | Docstrings present | Add architecture decision records (ADRs) |
| CI/CD | GitHub Actions ✅ | Add integration tests, container security scan |

---

## 8. SECURITY ASSESSMENT

### Strengths ✅
- JWT tokens with expiration
- Password hashing (bcrypt)
- Multi-tenant isolation via partition keys
- RBAC with role-based permissions
- Audit logging (audit_service.py)
- Email verification before account activation
- CORS middleware configured

### Weaknesses ⚠️
- No token revocation (logout = client discard)
- No rate limiting on auth endpoints (brute force risk)
- No CSRF protection on state-changing endpoints
- WebSocket connections not rate-limited
- Secrets not rotated automatically
- No input sanitization (potential injection via document content)
- No DDoS protection (rate limits per IP/tenant only)

### Recommendations
1. Add OAuth2 token revocation (blacklist or JTI claim)
2. Implement rate limiting per IP + per user
3. Add request signing for document API calls
4. Use request ID correlation for audit trail
5. Regular security audit of uploaded document content
6. Add WAF (Web Application Firewall) in front of API

---

## SUMMARY SCORECARD

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Correctness** | 8/10 | Recent multitenancy fix verified; missing input validation |
| **Stability** | 7/10 | Good error handling; missing timeouts & backoff strategies |
| **Testability** | 9/10 | 230 tests passing; need load & chaos tests |
| **Performance** | 6/10 | No async queue; timeouts too tight; missing indexes |
| **Security** | 7/10 | Good RBAC; missing rate limits & token revocation |
| **Scalability** | 6/10 | Blocking architecture; no batch optimization; no caching |
| **Maintainability** | 8/10 | Clear structure; good separation of concerns |

**Overall: 7.3/10 — Production-ready for small-to-medium volume; needs optimization for high-volume B2C**

---

## ACTION ITEMS (Priority Order)

### Phase 1 (Must-Do Before Scale)
- [ ] Add timeouts to GPT-4o mini API calls (30s)
- [ ] Implement per-user rate limiting (upload/export jobs)
- [ ] Add input validation (UUID, email, price ranges)
- [ ] Fix bare `except:` clauses (alert_service.py)
- [ ] Add indexes to Cosmos DB (status, created_at)

### Phase 2 (High-Priority Improvements)
- [ ] Async extraction pipeline + job queue
- [ ] Document hash-based deduplication
- [ ] Cache extraction results (Redis)
- [ ] Circuit breaker for external APIs
- [ ] Structured logging with correlation IDs

### Phase 3 (Nice-to-Have Enhancements)
- [ ] Streaming PDF extraction
- [ ] Batch document processing
- [ ] Advanced ML predictions with confidence
- [ ] Secret rotation automation
- [ ] Load testing (1000 concurrent users)
