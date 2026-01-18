# Security Checklist Document

**Version:** 1.0  
**Status:** APPROVED  
**Compliance:** SOC2-Ready  
**Last Reviewed:** 2026-01-17

---

## Authentication & Authorization

### ✓ Password Security
- [x] Minimum 12 characters required
- [x] Must contain: uppercase, lowercase, number, special char
- [x] Passwords hashed with bcrypt (cost factor 12)
- [x] No password stored in plain text
- [x] No password reset links valid > 24 hours
- [x] Failed login attempt lockout after 5 tries (15 min cooldown)

**Implementation:**
```python
# backend/services/auth_service.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### ✓ JWT Token Management
- [x] Tokens expire after 24 hours
- [x] Refresh tokens only extend by 24 hours
- [x] Token signature verified on every request
- [x] Tokens include user_id and role
- [x] Revoked tokens cannot be reused
- [x] Refresh tokens stored server-side

**Configuration:**
```
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
JWT_SECRET_KEY=<32+ char random string from Key Vault>
```

### ✓ Role-Based Access Control (RBAC)
- [x] Three roles defined: officer, approver, admin
- [x] Each endpoint validates required role
- [x] Users can only access own documents
- [x] Approvers can only approve assigned items
- [x] Admins have full system access

**Permission Matrix:**
| Action | Officer | Approver | Admin |
|--------|---------|----------|-------|
| Upload document | ✓ | ✓ | ✓ |
| Create workflow | ✓ | ✗ | ✓ |
| Approve PO | ✗ | ✓ | ✓ |
| Manage users | ✗ | ✗ | ✓ |
| View reports | ✓ | ✓ | ✓ |

### ✓ Multi-Tenancy Isolation
- [x] Data isolated by company_id
- [x] No cross-tenant data access possible
- [x] Tenant ID validated on every request
- [x] Cosmos DB partitioned by tenant

---

## API Security

### ✓ CORS Configuration
- [x] CORS enabled only for frontend domain
- [x] Credentials allowed (cookies, auth headers)
- [x] Preflight requests handled properly
- [x] No wildcard (*) allowed in production

**Configuration:**
```python
# backend/middleware.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://jolly-coast-03a4f4d03.4.azurestaticapps.net"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=86400
)
```

### ✓ Rate Limiting
- [x] 100 requests per minute per user
- [x] 1000 requests per minute per IP
- [x] Exponential backoff on 429 errors
- [x] Rate limits returned in response headers

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1642416000
```

### ✓ HTTPS/TLS
- [x] All traffic encrypted in transit
- [x] TLS 1.2 minimum
- [x] HSTS header enabled
- [x] Certificate pinning for critical endpoints
- [x] No mixed HTTP/HTTPS

**Headers:**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### ✓ Input Validation
- [x] All inputs validated server-side
- [x] Pydantic schema enforcement
- [x] File type whitelist (PDF only)
- [x] File size limit 5 MB
- [x] Email format validation
- [x] Injection prevention (parameterized queries)

**Validation Example:**
```python
class DocumentUploadRequest(BaseModel):
    filename: str = Field(..., max_length=255)
    document_type: str = Field(..., regex="^(RFQ|Quote|PO|Invoice)$")
    
    @field_validator('filename')
    def validate_filename(cls, v):
        if not v.endswith(('.pdf', '.PDF')):
            raise ValueError('Only PDF files allowed')
        return v
```

### ✓ Output Encoding
- [x] All user input HTML-escaped
- [x] JSON responses properly encoded
- [x] No raw HTML in API responses
- [x] Content-Type headers correct

---

## Data Security

### ✓ Encryption at Rest
- [x] Database encrypted with Azure-managed keys
- [x] Blob storage encrypted with AES-256
- [x] Backups encrypted
- [x] No plaintext secrets in code

**Azure Configuration:**
```
- Cosmos DB: Encryption at rest enabled
- Blob Storage: Storage Service Encryption enabled
- Key Vault: All secrets encrypted
```

### ✓ Encryption in Transit
- [x] TLS 1.2+ for all connections
- [x] Certificate validation enabled
- [x] No downgrade attacks possible
- [x] Perfect Forward Secrecy enabled

### ✓ Secrets Management
- [x] All secrets in Azure Key Vault
- [x] No secrets in environment files (git)
- [x] No secrets in logs or error messages
- [x] Automatic secret rotation enabled
- [x] Access logs maintained

**Secrets Stored:**
```
- JWT_SECRET_KEY
- COSMOS_CONNECTION_STRING
- AZURE_STORAGE_CONNECTION_STRING
- DOCUMENT_INTELLIGENCE_KEY
- Email service credentials
```

### ✓ Sensitive Data Handling
- [x] No SSN, credit cards, or PII logged
- [x] Passwords never logged
- [x] API keys never logged
- [x] Tokens truncated in logs (show last 4 chars only)
- [x] PII redacted in error messages

**Logging Policy:**
```
DO log: User ID, timestamp, action, status code
DO NOT log: passwords, tokens, API keys, file contents
```

### ✓ Data Retention
- [x] Audit logs retained 2 years
- [x] Draft documents auto-deleted after 90 days
- [x] Soft deletes used (recovery period 30 days)
- [x] Data deletion completes within 24 hours
- [x] Right to be forgotten (GDPR) supported

---

## File Upload Security

### ✓ File Validation
- [x] File type whitelist: PDF only
- [x] Magic number validation (not just extension)
- [x] File size limit: 5 MB
- [x] No executable files allowed
- [x] Virus scanning enabled

**Validation Code:**
```python
def validate_upload_file(file: UploadFile):
    # Check extension
    if not file.filename.endswith('.pdf'):
        raise ValueError("Only PDF files allowed")
    
    # Check MIME type
    if file.content_type != 'application/pdf':
        raise ValueError("Invalid file type")
    
    # Check file size
    file_size = await get_file_size(file)
    if file_size > 5_000_000:  # 5 MB
        raise ValueError("File too large")
    
    # Check magic number
    header = await file.read(4)
    if header[:4] != b'%PDF':
        raise ValueError("Not a valid PDF file")
```

### ✓ Storage Security
- [x] Files stored in Azure Blob Storage
- [x] Unique filenames (GUID-based)
- [x] No direct file access URLs in client
- [x] Signed URLs expire after 1 hour
- [x] Separate container per document type

---

## API Endpoint Security

### ✓ Endpoint-Level Authorization
```python
@router.get("/api/v1/documents/{doc_id}")
async def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_user)
):
    document = await DocumentRepository.get(doc_id)
    
    # Verify ownership
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403)
    
    return document
```

### ✓ Request Validation
- [x] Content-Type header checked
- [x] Request body schema validated
- [x] Path parameters validated
- [x] Query parameters sanitized
- [x] Request size limit: 10 MB

### ✓ Response Security
- [x] No sensitive data in error messages
- [x] No stack traces to users
- [x] No system information leaked
- [x] Consistent error responses
- [x] No timing attacks

**Error Response Example:**
```json
{
  "error": "unauthorized",
  "message": "You don't have permission to access this resource"
}
```

---

## Infrastructure Security

### ✓ Azure Security
- [x] Virtual Network configured
- [x] Network Security Groups restrict traffic
- [x] Managed identity authentication used
- [x] Firewall rules configured
- [x] DDoS protection enabled

**NSG Rules:**
```
- Allow HTTPS (443) from frontend domain
- Allow backend API only from static web app
- Deny all other inbound traffic
```

### ✓ Container Security
- [x] Images from trusted registry
- [x] No hardcoded credentials in images
- [x] Security scanning enabled
- [x] Latest patches applied
- [x] Non-root user for container

**Dockerfile Security:**
```dockerfile
FROM python:3.13-slim
RUN useradd -m -u 1000 appuser
USER appuser
COPY --chown=appuser:appuser . /app
```

### ✓ Logging & Monitoring
- [x] All API calls logged
- [x] Failed auth attempts logged
- [x] Admin actions logged
- [x] Data access logged
- [x] Application Insights configured
- [x] Alerts for suspicious activity

**Alert Conditions:**
```
- 10+ failed login attempts in 5 min
- Unauthorized access attempts
- Large data exports
- Configuration changes
- API rate limit exceeded
```

---

## Compliance & Auditing

### ✓ Audit Trail
- [x] Every action logged with timestamp
- [x] User ID recorded for each action
- [x] Action details stored
- [x] IP address logged
- [x] 2-year retention period
- [x] Immutable audit logs (no deletion)

**Audit Log Entry:**
```json
{
  "log_id": "audit_123",
  "timestamp": "2026-01-17T10:30:00Z",
  "user_id": "usr_abc123",
  "action": "document_deleted",
  "resource_id": "doc_xyz789",
  "ip_address": "192.168.1.100",
  "status": "success"
}
```

### ✓ Compliance Standards
- [x] GDPR compliance (data privacy)
- [x] SOC2 Type II controls
- [x] OWASP Top 10 mitigations
- [x] PCI DSS for payment data (if applicable)
- [x] HIPAA ready (if handling health data)

### ✓ Security Testing
- [x] OWASP ZAP scanning monthly
- [x] Dependency vulnerability scanning
- [x] Penetration testing annually
- [x] Code security review on PRs
- [x] Secure code training required

---

## Incident Response

### ✓ Security Incident Plan
- [x] Incident detection enabled
- [x] Alert routing configured
- [x] Escalation procedures defined
- [x] Communication templates ready
- [x] Recovery procedures documented
- [x] Post-incident review process

**Response Timeline:**
```
- P0 (Critical): Response in 1 hour
- P1 (High): Response in 4 hours
- P2 (Medium): Response in 24 hours
- P3 (Low): Response in 5 days
```

### ✓ Backup & Disaster Recovery
- [x] Daily automated backups
- [x] Backups encrypted and tested
- [x] RTO: 4 hours
- [x] RPO: 1 hour
- [x] Backup located in different region
- [x] Restore procedures documented

---

## Security Checklist for Deployment

Before deploying to production, verify:

- [ ] All secrets in Key Vault (not in code)
- [ ] CORS configured for correct domain only
- [ ] JWT expiration set to 24 hours
- [ ] Rate limiting enabled
- [ ] Audit logging enabled
- [ ] TLS 1.2+ configured
- [ ] HSTS headers enabled
- [ ] Security headers present
- [ ] Firewall rules restrictive
- [ ] Database encrypted at rest
- [ ] Backups automated and tested
- [ ] Monitoring and alerts configured
- [ ] Security group reviewed
- [ ] Secrets rotation scheduled
- [ ] Incident response plan ready

---

**Reference:** `/docs/02-architecture/SECURITY_CHECKLIST_v1.0.md`
