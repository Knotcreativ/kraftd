# KraftdIntel API Documentation

**Version:** 1.0.0-MVP  
**Last Updated:** 2026-01-15  
**Base URL:** `http://localhost:7071/api` (local) | `https://kraftdocs.azurewebsites.net/api` (production)

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base Endpoints](#base-endpoints)
4. [Document Management](#document-management)
5. [Workflow Operations](#workflow-operations)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)

---

## Overview

The Kraftd Intelligence Backend API provides document processing and procurement workflow automation. All endpoints follow RESTful conventions and return JSON responses.

### API Features

- **Document Upload & Processing** - Upload PDFs and extract structured data
- **Format Conversion** - Convert between document formats
- **Intelligent Extraction** - AI-powered data extraction with validation
- **Workflow Automation** - Multi-step procurement workflow (inquiry → pro forma invoice)
- **Multi-Tenant Support** - Owner-based data isolation
- **Async Processing** - Non-blocking document processing

### Base Information

| Attribute | Value |
|-----------|-------|
| **API Version** | v1 |
| **Response Format** | JSON |
| **Authentication** | JWT Bearer Token |
| **Rate Limit** | 100 requests/minute |
| **Timeout** | 30 seconds |

---

## Authentication

All endpoints (except `/health` and root) require JWT Bearer token authentication.

### Authentication Flow

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

HTTP/1.1 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Using the Token

Include the token in all requests:

```http
GET /api/v1/documents
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Token Refresh

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}

HTTP/1.1 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Base Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-15T10:30:00.000000",
  "version": "1.0.0-MVP"
}
```

**Status Codes:**
- `200` - API is healthy
- `503` - API unavailable

---

### 2. Root Endpoint

**Endpoint:** `GET /`

Get API overview and available endpoints.

**Response:**
```json
{
  "message": "Kraftd Docs Backend is running.",
  "version": "1.0.0-MVP",
  "endpoints": {
    "document_ingestion": "/api/v1/docs/upload",
    "document_intelligence": "/api/v1/extract",
    "workflow": "/api/v1/workflow",
    "output": "/api/v1/generate-output",
    "health": "/health",
    "metrics": "/metrics"
  }
}
```

---

### 3. Metrics

**Endpoint:** `GET /metrics`

Get API usage metrics.

**Response:**
```json
{
  "total_requests": 1250,
  "total_errors": 15,
  "average_response_time_ms": 245,
  "error_rate": 1.2,
  "uptime_minutes": 480,
  "documents_processed": 320,
  "active_workflows": 15
}
```

---

## Document Management

### 1. Upload Document

**Endpoint:** `POST /api/v1/docs/upload`

Upload a PDF document for processing.

**Request:**
```
Content-Type: multipart/form-data

Parameters:
  file: <binary PDF file>
  doc_type: string (optional) - Document type (INVOICE, QUOTE, RFQUOTATION, etc.)
```

**Example:**
```bash
curl -X POST http://localhost:7071/api/v1/docs/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@invoice.pdf" \
  -F "doc_type=INVOICE"
```

**Response:**
```json
{
  "document_id": "doc-abc123",
  "filename": "invoice.pdf",
  "status": "uploaded",
  "file_size_bytes": 256432,
  "message": "Document uploaded successfully. Ready for processing."
}
```

**Status Codes:**
- `200` - Document uploaded
- `400` - Invalid file type
- `413` - File too large
- `500` - Server error

---

### 2. Extract Document Data

**Endpoint:** `POST /api/v1/extract`

Extract structured data from uploaded document.

**Request:**
```json
{
  "document_id": "doc-abc123",
  "extraction_type": "full"
}
```

**Example:**
```bash
curl -X POST http://localhost:7071/api/v1/extract \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc-abc123",
    "extraction_type": "full"
  }'
```

**Response:**
```json
{
  "document_id": "doc-abc123",
  "status": "extracted",
  "document_type": "INVOICE",
  "processing_time_ms": 5234,
  "extraction_metrics": {
    "fields_mapped": 18,
    "inferences_made": 7,
    "line_items": 12,
    "parties_found": 2
  },
  "validation": {
    "completeness_score": 94,
    "quality_score": 91,
    "overall_score": 92.5,
    "ready_for_processing": true,
    "requires_manual_review": false
  },
  "extracted_data": {
    "invoice_number": "INV-2026-001",
    "date": "2026-01-15",
    "total_amount": 15000,
    "currency": "SAR",
    "supplier": {
      "name": "Global Supplies Inc",
      "email": "contact@globalsupplies.com",
      "tax_id": "1234567890"
    },
    "line_items": [
      {
        "description": "Item 1",
        "quantity": 10,
        "unit_price": 1000,
        "total": 10000
      }
    ]
  }
}
```

**Status Codes:**
- `200` - Extraction successful
- `404` - Document not found
- `408` - Processing timeout
- `500` - Server error

---

### 3. Convert Document Format

**Endpoint:** `POST /api/v1/convert`

Convert document to different format.

**Request:**
```json
{
  "document_id": "doc-abc123",
  "target_format": "csv"
}
```

**Response:**
```json
{
  "document_id": "doc-abc123",
  "source_format": "pdf",
  "target_format": "csv",
  "status": "converted",
  "file_url": "https://storage.example.com/doc-abc123.csv",
  "message": "Document converted to CSV format"
}
```

---

### 4. Get Document

**Endpoint:** `GET /api/v1/documents/{id}`

Retrieve document details and status.

**Example:**
```bash
curl -X GET http://localhost:7071/api/v1/documents/doc-abc123 \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "document_id": "doc-abc123",
  "filename": "invoice.pdf",
  "status": "extracted",
  "owner_email": "buyer@company.com",
  "created_at": "2026-01-15T10:00:00.000000",
  "updated_at": "2026-01-15T10:05:30.000000",
  "file_size_bytes": 256432,
  "document_type": "INVOICE",
  "extraction_status": "complete",
  "workflow_stage": "estimation_in_progress"
}
```

---

### 5. Get Document Status

**Endpoint:** `GET /api/v1/documents/{id}/status`

Get current document processing status.

**Response:**
```json
{
  "document_id": "doc-abc123",
  "status": "extraction_in_progress",
  "progress": 65,
  "current_step": "field_mapping",
  "estimated_time_remaining_seconds": 15,
  "errors": []
}
```

---

## Workflow Operations

### 1. Inquiry Review

**Endpoint:** `POST /api/v1/workflow/inquiry`

Review and validate initial inquiry/RFQ.

**Request:**
```json
{
  "document_id": "doc-abc123"
}
```

**Response:**
```json
{
  "document_id": "doc-abc123",
  "step": "inquiry",
  "status": "REVIEW_PENDING",
  "timestamp": "2026-01-15T10:30:00.000000",
  "validation": {
    "scope_clarity": "complete",
    "requirements_extracted": true,
    "total_value": 50000,
    "currency": "SAR"
  },
  "message": "Inquiry reviewed and scope dissected."
}
```

---

### 2. Assessment

**Endpoint:** `POST /api/v1/workflow/assessment`

Assess document complexity and requirements.

**Response:**
```json
{
  "document_id": "doc-abc123",
  "step": "assessment",
  "status": "ASSESSMENT_COMPLETE",
  "assessment": {
    "complexity_level": "medium",
    "estimated_suppliers": 5,
    "estimated_quotes": 8,
    "special_requirements": ["rush_delivery", "technical_support"]
  }
}
```

---

### 3. Request Estimation

**Endpoint:** `POST /api/v1/workflow/estimation`

Request supplier quotations.

**Response:**
```json
{
  "document_id": "doc-abc123",
  "step": "estimation",
  "status": "ESTIMATION_IN_PROGRESS",
  "quotes_requested": 5,
  "expected_responses": "48 hours",
  "timestamp": "2026-01-15T10:35:00.000000"
}
```

---

### 4. Normalize Quotes

**Endpoint:** `POST /api/v1/workflow/normalize-quotes`

Normalize and standardize supplier quotes.

**Response:**
```json
{
  "document_id": "doc-abc123",
  "step": "normalize_quotes",
  "normalized_quotes": [
    {
      "supplier_id": "sup-001",
      "supplier_name": "Global Supplies Inc",
      "original_price": 48000,
      "normalized_price": 48000,
      "currency": "SAR",
      "delivery_days": 15,
      "payment_terms": "Net 30"
    },
    {
      "supplier_id": "sup-002",
      "supplier_name": "Fast Delivery Ltd",
      "original_price": 52000,
      "normalized_price": 52000,
      "currency": "SAR",
      "delivery_days": 7,
      "payment_terms": "Net 15"
    }
  ],
  "timestamp": "2026-01-15T11:00:00.000000"
}
```

---

### 5. Compare Quotes

**Endpoint:** `POST /api/v1/workflow/comparison`

Analyze and compare supplier quotes.

**Response:**
```json
{
  "document_id": "doc-abc123",
  "step": "comparison",
  "status": "COMPARISON_DONE",
  "analysis": {
    "lowest_price_supplier": "Global Supplies Inc",
    "lowest_price": 48000,
    "best_value_supplier": "Fast Delivery Ltd",
    "best_value_score": 92,
    "savings_potential": "4000 SAR",
    "recommendation": "sup-002"
  },
  "comparison_matrix": [
    {
      "supplier": "Global Supplies Inc",
      "price_score": 95,
      "delivery_score": 70,
      "reliability_score": 85,
      "overall_score": 83
    }
  ],
  "timestamp": "2026-01-15T11:30:00.000000"
}
```

---

### 6. Approve for PO

**Endpoint:** `POST /api/v1/workflow/approval`

Approve selected supplier for purchase order.

**Request:**
```json
{
  "document_id": "doc-abc123",
  "approved_supplier_id": "sup-002"
}
```

**Response:**
```json
{
  "document_id": "doc-abc123",
  "step": "approval",
  "status": "APPROVED_FOR_PO",
  "approved_supplier_id": "sup-002",
  "approved_supplier_name": "Fast Delivery Ltd",
  "po_number": "PO-2026-00001",
  "timestamp": "2026-01-15T12:00:00.000000"
}
```

---

### 7. Generate Pro Forma Invoice

**Endpoint:** `POST /api/v1/workflow/proforma-invoice`

Generate pro forma invoice for approved supplier.

**Response:**
```json
{
  "document_id": "doc-abc123",
  "step": "proforma_invoice",
  "status": "PROFORMA_GENERATED",
  "proforma_invoice": {
    "invoice_number": "PROFORMA-2026-001",
    "supplier_id": "sup-002",
    "supplier_name": "Fast Delivery Ltd",
    "total_amount": 52000,
    "currency": "SAR",
    "due_date": "2026-02-15",
    "payment_terms": "Net 15",
    "items": [
      {
        "description": "Item 1",
        "quantity": 10,
        "unit_price": 5200,
        "total": 52000
      }
    ]
  },
  "document_url": "https://storage.example.com/PROFORMA-2026-001.pdf",
  "timestamp": "2026-01-15T12:30:00.000000"
}
```

---

### 8. Generate Output Document

**Endpoint:** `POST /api/v1/generate-output`

Generate final formatted output document.

**Request:**
```json
{
  "document_id": "doc-abc123",
  "output_format": "pdf"
}
```

**Response:**
```json
{
  "document_id": "doc-abc123",
  "status": "output_generated",
  "output_format": "pdf",
  "file_url": "https://storage.example.com/doc-abc123-output.pdf",
  "file_size_bytes": 156232,
  "generation_time_ms": 2345,
  "timestamp": "2026-01-15T12:35:00.000000"
}
```

---

## Error Handling

### Error Response Format

All errors return consistent JSON structure:

```json
{
  "status_code": 404,
  "error": "not_found",
  "detail": "Document not found",
  "request_id": "req-abc123",
  "timestamp": "2026-01-15T10:30:00.000000"
}
```

### Common Error Codes

| Code | Error | Description |
|------|-------|-------------|
| 400 | `bad_request` | Invalid request parameters |
| 401 | `unauthorized` | Missing or invalid authentication token |
| 403 | `forbidden` | Insufficient permissions |
| 404 | `not_found` | Resource not found |
| 408 | `request_timeout` | Processing timeout (>30s) |
| 413 | `payload_too_large` | File size exceeds limit |
| 429 | `rate_limit_exceeded` | Too many requests |
| 500 | `internal_error` | Server error |
| 503 | `service_unavailable` | API temporarily unavailable |

### Error Examples

**404 - Document Not Found:**
```json
{
  "status_code": 404,
  "error": "not_found",
  "detail": "Document doc-xyz789 not found",
  "request_id": "req-abc123"
}
```

**400 - Invalid File Type:**
```json
{
  "status_code": 400,
  "error": "bad_request",
  "detail": "Unsupported file type: docx. Supported types: pdf",
  "request_id": "req-def456"
}
```

**408 - Processing Timeout:**
```json
{
  "status_code": 408,
  "error": "request_timeout",
  "detail": "Document extraction exceeded 30 second timeout",
  "request_id": "req-ghi789"
}
```

---

## Rate Limiting

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642246800
```

### Rate Limit Exceeded

When rate limit is exceeded:

```json
{
  "status_code": 429,
  "error": "rate_limit_exceeded",
  "detail": "Rate limit exceeded: 100 requests per minute",
  "retry_after_seconds": 45,
  "request_id": "req-xyz123"
}
```

---

## Examples

### Complete Workflow Example

**Step 1: Upload Document**
```bash
curl -X POST http://localhost:7071/api/v1/docs/upload \
  -H "Authorization: Bearer eyJhbGc..." \
  -F "file=@rfq.pdf" \
  -F "doc_type=RFQUOTATION"
```

**Step 2: Extract Data**
```bash
curl -X POST http://localhost:7071/api/v1/extract \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"document_id": "doc-abc123", "extraction_type": "full"}'
```

**Step 3: Start Workflow**
```bash
curl -X POST http://localhost:7071/api/v1/workflow/inquiry \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"document_id": "doc-abc123"}'
```

**Step 4: Request Estimation**
```bash
curl -X POST http://localhost:7071/api/v1/workflow/estimation \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"document_id": "doc-abc123"}'
```

**Step 5: Generate Output**
```bash
curl -X POST http://localhost:7071/api/v1/generate-output \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"document_id": "doc-abc123", "output_format": "pdf"}'
```

---

## Response Time SLAs

| Endpoint | Average | P95 | P99 |
|----------|---------|-----|-----|
| Health Check | 10ms | 20ms | 50ms |
| Upload | 100ms | 300ms | 500ms |
| Extract | 5000ms | 15000ms | 20000ms |
| Workflow Steps | 500ms | 1000ms | 2000ms |
| Output Generation | 2000ms | 5000ms | 10000ms |

---

## Authentication Errors

### Invalid Token

```
HTTP/1.1 401 Unauthorized
{
  "status_code": 401,
  "error": "invalid_token",
  "detail": "Invalid or expired authentication token"
}
```

### Missing Token

```
HTTP/1.1 401 Unauthorized
{
  "status_code": 401,
  "error": "missing_auth",
  "detail": "Authorization header missing. Use: Authorization: Bearer <token>"
}
```

---

## Pagination

Endpoints returning lists support pagination:

```
GET /api/v1/documents?page=1&limit=20
```

**Response:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

---

## Filtering

Document list endpoints support filtering:

```
GET /api/v1/documents?status=extracted&doc_type=INVOICE&owner_email=buyer@company.com
```

---

## Support

For API support or issues:
- **Email:** support@kraftdintel.com
- **Documentation:** https://docs.kraftdintel.com
- **Status Page:** https://status.kraftdintel.com

**API Version:** 1.0.0-MVP  
**Last Updated:** 2026-01-15