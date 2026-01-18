# API Contract Document

**Version:** 1.0  
**Status:** APPROVED  
**Last Updated:** 2026-01-17  
**Accuracy:** Updated against actual FastAPI implementation (26 endpoints)

---

## Overview

This document defines the complete API contract for KraftdIntel, a procurement intelligence platform with document processing, workflow orchestration, and AI-powered analysis capabilities.

**Base URL:** `https://api.kraftdintel.com/api/v1`  
**Authentication:** Bearer token (JWT)  
**Rate Limiting:** 100 requests/minute per user  
**Response Format:** JSON  

---

## Authentication Endpoints (5 endpoints)

### POST /api/v1/auth/register
**Register new user**

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Errors:**
- `400`: Invalid input (email format, weak password)
- `409`: Email already registered

---

### POST /api/v1/auth/login
**Login to system**

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Errors:**
- `400`: Invalid email format
- `401`: Email or password incorrect
- `429`: Too many login attempts (account locked for 15 min)

---

### POST /api/v1/auth/refresh
**Refresh authentication token**

**Headers:**
```
Authorization: Bearer {expired_token}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Errors:**
- `401`: Token invalid or expired
- `400`: Invalid token format

---

### GET /api/v1/auth/profile
**Get current user profile**

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "user_id": "user_123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "procurement_officer",
  "created_at": "2026-01-15T09:00:00Z"
}
```

**Errors:**
- `401`: Unauthorized
- `404`: User not found

---

### POST /api/v1/auth/validate
**Validate current token**

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "valid": true,
  "user_id": "user_123",
  "email": "user@example.com",
  "expires_at": "2026-01-18T09:00:00Z"
}
```

**Errors:**
- `401`: Token invalid or expired
- `400`: Invalid token format

---

## Document Endpoints (6 endpoints)

### POST /api/v1/docs/upload
**Upload new document for processing**

**Headers:**
```
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

**Request:**
```
file: <binary file data>
document_type: "RFQ|Quote|Specification|Image|Excel|Word" (optional)
```

**Supported Formats:**
- PDF (.pdf)
- Microsoft Word (.docx, .doc)
- Microsoft Excel (.xlsx, .xls)
- Images (.png, .jpg, .jpeg)

**Response (201 Created):**
```json
{
  "document_id": "doc_abc123",
  "filename": "RFQ_2026_001.pdf",
  "size_bytes": 1048576,
  "status": "extracting",
  "uploaded_at": "2026-01-17T10:30:00Z",
  "extraction_method": "pending"
}
```

**Errors:**
- `400`: File too large (>50MB limit)
- `400`: Unsupported file type
- `401`: Unauthorized
- `413`: Payload too large
- `422`: Invalid document structure

---

### POST /api/v1/docs/convert
**Convert document to different format**

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
  "document_id": "doc_abc123",
  "target_format": "docx|xlsx|html|txt"
}
```

**Response (200 OK):**
```json
{
  "document_id": "doc_abc123",
  "original_format": "pdf",
  "target_format": "docx",
  "download_url": "https://storage.kraftdintel.com/converted/doc_abc123.docx",
  "size_bytes": 2048576,
  "conversion_time_ms": 3210,
  "expires_at": "2026-01-18T10:30:00Z"
}
```

**Errors:**
- `400`: Unsupported format
- `404`: Document not found
- `500`: Conversion failed
- `503`: Conversion service temporarily unavailable

---

### POST /api/v1/docs/extract
**Extract data from document (multiple formats supported)**

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
  "document_id": "doc_abc123",
  "extraction_method": "azure_di|agent|auto"
}
```

**Response (200 OK):**
```json
{
  "document_id": "doc_abc123",
  "extraction_id": "extr_xyz789",
  "status": "extracted",
  "method_used": "azure_di",
  "extracted_data": {
    "document_type": "RFQ",
    "vendor": "Acme Corp",
    "total_amount": 45000,
    "payment_terms": "Net 30",
    "delivery_date": "2026-03-15"
  },
  "confidence": 0.96,
  "extraction_time_ms": 2345,
  "extracted_at": "2026-01-17T10:35:00Z"
}
```

**Errors:**
- `400`: Invalid extraction method
- `404`: Document not found
- `500`: Extraction failed
- `503`: Extraction service unavailable

---

### GET /api/v1/documents/{document_id}
**Get document details and metadata**

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "document_id": "doc_abc123",
  "filename": "RFQ_2026_001.pdf",
  "size_bytes": 1048576,
  "document_type": "RFQ",
  "status": "extracted",
  "uploaded_by": "user_123",
  "uploaded_at": "2026-01-17T10:30:00Z",
  "extraction_status": "completed",
  "extraction_method": "azure_di",
  "confidence": 0.96,
  "extracted_at": "2026-01-17T10:35:00Z"
}
```

**Errors:**
- `404`: Document not found
- `401`: Unauthorized

---

### GET /api/v1/documents/{document_id}/output
**Get processed document output (download in various formats)**

**Headers:**
```
Authorization: Bearer {token}
```

**Query Parameters:**
```
?format=pdf|docx|xlsx|html&include_annotations=true|false
```

**Response (200 OK):**
- Binary file data
- Content-Type: application/pdf (or application/vnd.openxmlformats-officedocument.wordprocessingml.document, etc.)

**Errors:**
- `400`: Unsupported format
- `404`: Document not found
- `500`: Processing failed

---

### GET /api/v1/documents/{document_id}/status
**Get real-time document processing status**

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "document_id": "doc_abc123",
  "overall_status": "extracted",
  "upload_status": "completed",
  "upload_time_ms": 450,
  "extraction_status": "completed",
  "extraction_method": "azure_di",
  "extraction_time_ms": 2345,
  "confidence_score": 0.96,
  "last_updated": "2026-01-17T10:36:00Z"
}
```

**Errors:**
- `404`: Document not found
- `401`: Unauthorized

---

## Workflow Endpoints (7 endpoints)

### POST /api/v1/workflow/inquiry
**Create inquiry from uploaded document**

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
  "document_id": "doc_abc123"
}
```

**Response (200 OK):**
```json
{
  "inquiry_id": "inq_xyz789",
  "document_id": "doc_abc123",
  "status": "created",
  "workflow_step": 1,
  "timestamp": "2026-01-17T10:30:00Z"
}
```

**Errors:**
- `400`: Invalid document
- `404`: Document not found

---

### POST /api/v1/workflow/estimation
**Create cost and timeline estimation from document**

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
  "document_id": "doc_abc123",
  "scope_adjustment": 0.0
}
```

**Response (200 OK):**
```json
{
  "estimation_id": "est_xyz789",
  "document_id": "doc_abc123",
  "budget_estimate": 50000,
  "currency": "USD",
  "timeline_estimate_days": 56,
  "confidence": 0.89
}
```

**Errors:**
- `400`: Invalid document
- `404`: Document not found

---

### POST /api/v1/workflow/normalize-quotes
**Normalize multiple quotations for fair comparison**

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
  "quote_document_ids": ["doc_quote1", "doc_quote2", "doc_quote3"]
}
```

**Response (200 OK):**
```json
{
  "normalization_id": "norm_xyz789",
  "normalized_quotes": [
    {
      "document_id": "doc_quote1",
      "vendor_name": "Vendor A",
      "normalized_amount": 34000,
      "normalized_timeline_days": 45
    }
  ]
}
```

**Errors:**
- `400`: Insufficient documents
- `404`: Document not found

---

### POST /api/v1/workflow/comparison
**Compare normalized quotations and generate recommendations**

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
  "quote_document_ids": ["doc_quote1", "doc_quote2", "doc_quote3"]
}
```

**Response (200 OK):**
```json
{
  "comparison_id": "comp_xyz789",
  "ranking": [
    {
      "rank": 1,
      "vendor": "Vendor A",
      "overall_score": 9.2,
      "scores": {
        "price": 9.5,
        "timeline": 9.0
      }
    }
  ],
  "recommendation": {
    "vendor": "Vendor A",
    "reasoning": ["Best overall value", "Shortest timeline"]
  }
}
```

**Errors:**
- `400`: Invalid quote IDs
- `404`: Quote not found

---

### POST /api/v1/workflow/proposal
**Generate proposal based on comparison results**

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
  "comparison_id": "comp_xyz789",
  "selected_vendor": "Vendor A"
}
```

**Response (200 OK):**
```json
{
  "proposal_id": "prop_xyz789",
  "comparison_id": "comp_xyz789",
  "selected_vendor": "Vendor A",
  "status": "created",
  "created_at": "2026-01-17T14:00:00Z"
}
```

**Errors:**
- `400`: Invalid comparison
- `404`: Comparison not found

---

### POST /api/v1/workflow/po
**Generate purchase order from approved quote**

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
  "quote_document_id": "doc_quote1",
  "purchase_order_number": "PO-2026-001"
}
```

**Response (200 OK):**
```json
{
  "po_id": "po_xyz789",
  "po_number": "PO-2026-001",
  "vendor_name": "Vendor A",
  "amount": 34560,
  "currency": "USD",
  "status": "generated",
  "generated_at": "2026-01-17T14:15:00Z"
}
```

**Errors:**
- `400`: Invalid quote
- `404`: Quote not found

---

### POST /api/v1/workflow/proforma-invoice
**Generate proforma invoice from purchase order**

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
  "po_id": "po_xyz789",
  "invoice_date": "2026-01-17"
}
```

**Response (200 OK):**
```json
{
  "invoice_id": "inv_xyz789",
  "po_id": "po_xyz789",
  "po_number": "PO-2026-001",
  "vendor_name": "Vendor A",
  "amount": 34560,
  "currency": "USD",
  "status": "generated",
  "generated_at": "2026-01-17T14:20:00Z"
}
**Errors:**
- `400`: Invalid PO
- `404`: PO not found

---

## AI Agent Endpoints (4 endpoints)

### POST /api/v1/agent/chat
**Chat with AI agent for document analysis and questions**

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
  "document_id": "doc_abc123",
  "message": "What are the key requirements and delivery timeline?",
  "session_id": "sess_xyz123"
}
```

**Response (200 OK):**
```json
{
  "response": "Based on the RFQ, the key requirements include: 1) Frontend development 2) Backend with FastAPI 3) Database design. The delivery timeline is 45 days.",
  "confidence": 0.95,
  "extracted_facts": {
    "requirements": ["Frontend dev", "Backend dev", "Database"],
    "timeline": "45 days",
    "budget": 50000
  }
}
```

**Errors:**
- `400`: Invalid message format
- `404`: Document not found
- `429`: Rate limit exceeded
- `503`: Agent service unavailable

---

### GET /api/v1/agent/status
**Get AI agent availability and model information**

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "status": "available",
  "model": "gpt-4o-mini",
  "version": "1.0",
  "capabilities": [
    "document_analysis",
    "question_answering",
    "data_extraction",
    "document_summarization"
  ],
  "response_time_ms": 1200,
  "uptime_percent": 99.8
}
```

**Errors:**
- `503`: Agent service unavailable

---

### GET /api/v1/agent/learning
**Get agent learning and performance metrics**

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "documents_analyzed": 450,
  "total_conversations": 1200,
  "accuracy_score": 0.94,
  "user_satisfaction": 0.91,
  "feedback_received": 120
}
```

**Errors:**
- `401`: Unauthorized

---

### POST /api/v1/agent/check-di-decision
**Check if Azure Document Intelligence extraction should be used**

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
  "document_id": "doc_abc123"
}
```

**Response (200 OK):**
```json
{
  "use_azure_di": true,
  "confidence": 0.92,
  "reasoning": "Highly structured document with clear form fields",
  "document_type_detected": "Form",
  "expected_extraction_confidence": 0.95
}
```

**Errors:**
- `404`: Document not found

---

## Health & Status Endpoints (4 endpoints)

### GET /api/v1/health
**System health check**

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-17T15:30:00Z",
  "version": "1.0.0",
  "uptime_seconds": 864000,
  "services": {
    "database": "healthy",
    "extraction_service": "healthy",
    "agent_service": "healthy",
    "storage": "healthy"
  }
}
```

**Errors:**
- `503`: Service degraded

---

### GET /api/v1/metrics
**Get system and platform metrics**

**Response (200 OK):**
```json
{
  "timestamp": "2026-01-17T15:30:00Z",
  "requests": {
    "total": 15000,
    "per_minute": 25,
    "success_rate": 0.98
  },
  "documents": {
    "total_processed": 1250,
    "avg_processing_time_ms": 2150,
    "formats": {
      "pdf": 750,
      "docx": 300,
      "xlsx": 150,
      "images": 50
    }
  },
  "extraction": {
    "success_rate": 0.96,
    "avg_confidence": 0.93
  }
}
```

**Errors:**
- `401`: Unauthorized

---

### GET /api/v1/
**API root information and documentation**

**Response (200 OK):**
```json
{
  "name": "KraftdIntel API",
  "version": "1.0.0",
  "status": "operational",
  "description": "Procurement intelligence platform with document processing and AI-powered analysis",
  "documentation_url": "/docs",
  "openapi_url": "/openapi.json",
  "endpoints_count": 26,
  "auth_type": "JWT Bearer",
  "rate_limit": "100 requests/minute"
}
```

---

## Error Response Format

All errors follow this standard format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "field_name",
      "issue": "Detailed issue description"
    },
    "timestamp": "2026-01-17T15:30:00Z",
    "request_id": "req_xyz789"
  }
}
```

### Common HTTP Status Codes

| Status | Meaning | When Used |
|--------|---------|-----------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input or parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but no permission |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists (e.g., duplicate email) |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal server error |
| 503 | Service Unavailable | Service temporarily down |

---

## Authentication & Security

### Bearer Token Format
```
Authorization: Bearer {JWT_TOKEN}
```

### Token Claims
```json
{
  "sub": "user_123",
  "email": "user@example.com",
  "iat": 1673896800,
  "exp": 1673983200,
  "iss": "KraftdIntel",
  "aud": "api.kraftdintel.com"
}
```

### Token Expiration
- Access Token: 24 hours
- Refresh Token: 30 days

### Rate Limiting
- **Standard:** 100 requests/minute per user
- **Enterprise:** 1000 requests/minute per user
- **Headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## Changelog

### Version 1.0.0 - 2026-01-17
- Initial API contract with 26 endpoints
- Support for 5 authentication endpoints
- Document processing with multiple formats (PDF, Word, Excel, Image)
- Advanced workflow orchestration (7 workflow steps)
- AI agent integration (4 agent endpoints)
- System health and metrics endpoints
- Comprehensive error handling
- Rate limiting and security features

---
