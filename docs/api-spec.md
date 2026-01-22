# Kraftd Docs — Backend REST API Specification

**Version**: 1.0  
**Last Updated**: January 22, 2026  
**Base URL**: `https://api.kraftd.com/api/v1`  
**Framework**: FastAPI (Python 3.13)  
**Database**: Azure Cosmos DB  
**Authentication**: JWT (RS256 algorithm, bcrypt passwords)  

---

## Overview

The Kraftd API provides a complete document intelligence and processing pipeline. The core unit of work is an **ExtractionRecord** — a single document upload that flows through classification, extraction, AI analysis, user review, and export stages.

### API Capabilities

- 🔐 User authentication (register, login, verify email, refresh tokens)
- 📄 Document upload and batch processing
- 🤖 AI-powered document classification and field extraction
- 🧠 Intelligent schema generation and user-guided refinement
- 💾 Multi-format export (PDF, JSON, CSV, XLSX)
- 💬 AI agent for interactive document Q&A
- 📊 Workflow automation (RFQ → PO → Invoice processing)
- ✅ Health monitoring and metrics

---

## Table of Contents

1. [Authentication](#authentication)
2. [Health & System](#health--system)
3. [Document Operations](#document-operations)
4. [Extraction & Processing](#extraction--processing)
5. [AI Workflows](#ai-workflows)
6. [Export & Download](#export--download)
7. [Agent Interface](#agent-interface)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [Examples](#examples)

---

# Authentication

All endpoints except `/api/v1/auth/register` and `/api/v1/auth/login` require a valid JWT token in the `Authorization` header:

```
Authorization: Bearer <token>
```

Tokens are RS256-signed JWTs with 1-hour expiration. Use `/api/v1/auth/refresh` to obtain new tokens.

---

## POST /api/v1/auth/register

Register a new user account.

### Request

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "firstName": "John",
  "lastName": "Doe",
  "company": "Acme Corp",
  "acceptTerms": true,
  "acceptPrivacy": true
}
```

### Response (201 Created)

```json
{
  "message": "Registration successful. Please verify your email.",
  "user_id": "usr-abc123",
  "email": "user@example.com",
  "status": "pending_verification"
}
```

### Errors

- `400 EMAIL_INVALID` — Invalid email format
- `400 PASSWORD_TOO_WEAK` — Password < 8 chars or contains email
- `400 TERMS_NOT_ACCEPTED` — Legal terms not accepted
- `409 USER_EXISTS` — Email already registered

---

## POST /api/v1/auth/login

Login and receive JWT tokens.

### Request

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

### Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user_id": "usr-abc123",
  "email": "user@example.com",
  "plan_type": "pro"
}
```

### Errors

- `401 INVALID_CREDENTIALS` — Email or password incorrect
- `403 EMAIL_NOT_VERIFIED` — Must verify email first
- `404 USER_NOT_FOUND` — User does not exist

---

## POST /api/v1/auth/verify-email

Verify user email with OTP token.

### Request

```json
{
  "email": "user@example.com",
  "otp_token": "123456"
}
```

### Response (200 OK)

```json
{
  "message": "Email verified successfully",
  "verified_at": "2026-01-22T10:30:00Z"
}
```

### Errors

- `400 INVALID_OTP` — OTP token incorrect or expired
- `404 USER_NOT_FOUND` — User does not exist

---

## POST /api/v1/auth/refresh

Refresh expired access token.

### Request (no body)

```
Authorization: Bearer <refresh_token>
```

### Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Errors

- `401 INVALID_TOKEN` — Token invalid or expired
- `401 UNAUTHORIZED` — No token provided

---

## GET /api/v1/auth/profile

Get current authenticated user profile.

### Request (no parameters)

```
Authorization: Bearer <token>
```

### Response (200 OK)

```json
{
  "user_id": "usr-abc123",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company": "Acme Corp",
  "plan_type": "pro",
  "quota_limit": 5000,
  "quota_used": 1250,
  "created_at": "2026-01-15T10:00:00Z",
  "verified_at": "2026-01-15T10:15:00Z"
}
```

---

## GET /api/v1/auth/validate

Validate current JWT token.

### Request (no parameters)

```
Authorization: Bearer <token>
```

### Response (200 OK)

```json
{
  "valid": true,
  "user_id": "usr-abc123",
  "email": "user@example.com",
  "expires_at": "2026-01-22T11:30:00Z"
}
```

---

# Health & System

## GET /api/v1/health

System health check (no authentication required).

### Response (200 OK)

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-22T10:30:00Z",
  "uptime_seconds": 86400,
  "database": "connected",
  "blob_storage": "connected"
}
```

---

## GET /api/v1/metrics

System metrics and performance data.

### Request

```
Authorization: Bearer <token>
```

### Response (200 OK)

```json
{
  "documents_processed_today": 245,
  "avg_processing_time_ms": 3200,
  "ai_api_latency_ms": 1850,
  "database_latency_ms": 45,
  "error_rate_percent": 0.2,
  "active_extractions": 12,
  "queue_depth": 3
}
```

---

## GET /api/v1/

API status and route listing.

### Response (200 OK)

```json
{
  "name": "Kraftd Docs API",
  "version": "1.0.0",
  "status": "operational",
  "routes": 67,
  "endpoints": [
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/docs/upload",
    ...
  ]
}
```

---

# Document Operations

## POST /api/v1/docs/upload

Upload a single document to Cosmos DB and Azure Blob Storage.

### Request

```
Content-Type: multipart/form-data
Authorization: Bearer <token>

Parameters:
  - file (required): PDF, DOCX, XLSX, or image file (max 50 MB)
  - document_type (optional): RFQ | BOQ | QUOTATION | INVOICE | PO | CONTRACT | AUTO
```

### Response (201 Created)

```json
{
  "success": true,
  "document": {
    "document_id": "doc-xyz789",
    "owner_email": "user@example.com",
    "filename": "quotation.pdf",
    "file_type": "PDF",
    "file_size_bytes": 2048576,
    "blob_url": "https://kraftdstorage.blob.core.windows.net/documents/doc-xyz789.pdf",
    "uploaded_at": "2026-01-22T10:30:00Z",
    "status": "uploaded"
  }
}
```

### Errors

- `400 FILE_TOO_LARGE` — File exceeds 50 MB limit
- `400 INVALID_FILE_TYPE` — Unsupported file format
- `413 PAYLOAD_TOO_LARGE` — Request body too large
- `429 QUOTA_EXCEEDED` — User quota limit reached

---

## POST /api/v1/docs/upload/batch

Upload multiple documents in a single request.

### Request

```
Content-Type: multipart/form-data
Authorization: Bearer <token>

Parameters:
  - files (required): Array of files (max 10 files, max 50 MB each)
  - batch_name (optional): Name for batch tracking
```

### Response (201 Created)

```json
{
  "success": true,
  "batch_id": "batch-001",
  "uploaded_count": 5,
  "failed_count": 1,
  "documents": [
    {
      "document_id": "doc-xyz789",
      "filename": "quotation.pdf",
      "status": "uploaded"
    },
    ...
  ],
  "errors": [
    {
      "filename": "corrupt.pdf",
      "error": "FILE_CORRUPTED"
    }
  ]
}
```

---

## GET /api/v1/documents/{document_id}

Get document metadata and extraction status.

### Request

```
Authorization: Bearer <token>
```

### Response (200 OK)

```json
{
  "document_id": "doc-xyz789",
  "owner_email": "user@example.com",
  "filename": "quotation.pdf",
  "file_type": "PDF",
  "status": "extracted",
  "uploaded_at": "2026-01-22T10:30:00Z",
  "processing_completed_at": "2026-01-22T10:35:00Z",
  "blob_url": "https://...",
  "extraction_record": {
    "document_type": "QUOTATION",
    "parties": {
      "issuer": {
        "name": "Tech Solutions Inc",
        "contact_person": { "name": "John Smith", "email": "john@tech.com" }
      },
      "recipient": { "name": "Acme Corp" }
    },
    "dates": {
      "issue_date": "2026-01-20",
      "validity_date": "2026-02-20"
    },
    "line_items": [
      {
        "line_number": 1,
        "description": "Development Services",
        "quantity": 100,
        "unit_of_measure": "HR",
        "unit_price": 150.00,
        "total_price": 15000.00,
        "currency": "USD"
      }
    ],
    "commercial_terms": {
      "currency": "USD",
      "payment_terms": "Net 30",
      "tax_vat_mentioned": true,
      "vat_rate": 5.0
    },
    "extraction_confidence": {
      "overall_confidence": 0.94,
      "field_confidence": {
        "parties": 0.98,
        "dates": 0.92,
        "line_items": 0.87,
        "commercial_terms": 0.91
      }
    }
  }
}
```

### Errors

- `404 DOCUMENT_NOT_FOUND` — Document does not exist
- `403 FORBIDDEN` — Document owned by different user

---

## GET /api/v1/documents/{document_id}/status

Get document processing status only.

### Response (200 OK)

```json
{
  "document_id": "doc-xyz789",
  "status": "extracted",
  "processing_stage": "transformation",
  "progress_percent": 75,
  "estimated_completion_seconds": 120,
  "extraction_metrics": {
    "completeness_score": 0.92,
    "quality_score": 0.88,
    "overall_score": 0.90,
    "ready_for_processing": true,
    "requires_manual_review": false
  }
}
```

---

# Extraction & Processing

## POST /api/v1/docs/extract

Process a document through the complete intelligent extraction pipeline.

Stages:
1. **Classify** — Identify document type (RFQ, BOQ, Invoice, etc.)
2. **Map** — Extract structured fields into KraftdDocument schema
3. **Infer** — Apply business logic rules (calculate totals, infer currency, etc.)
4. **Validate** — Score completeness and quality

### Request

```json
{
  "document_id": "doc-xyz789",
  "force_reprocessing": false
}
```

### Response (200 OK)

```json
{
  "success": true,
  "document_id": "doc-xyz789",
  "status": "extracted",
  "processing_time_ms": 3200,
  
  "extraction_result": {
    "document_type": "QUOTATION",
    "metadata": {
      "document_number": "QUOT-2026-001",
      "issue_date": "2026-01-20",
      "revision_number": "1"
    },
    
    "parties": {
      "issuer": {
        "name": "Tech Solutions Inc",
        "legal_entity": "Tech Solutions Inc (LLC)",
        "trn_vat_number": "100123456789",
        "contact_person": {
          "name": "John Smith",
          "email": "john@tech.com",
          "phone": "+1-555-0100",
          "department": "Sales"
        },
        "registered_address": {
          "address_line1": "123 Tech Park",
          "city": "San Francisco",
          "region": "CA",
          "postal_code": "94105",
          "country": "USA"
        }
      },
      "recipient": {
        "name": "Acme Corp",
        "legal_entity": "Acme Corporation"
      }
    },
    
    "project_context": {
      "project_name": "Website Redesign 2026",
      "project_code": "WR-2026-01",
      "client_name": "Acme Corp",
      "location": "New York, USA",
      "discipline": "IT"
    },
    
    "dates": {
      "issue_date": "2026-01-20",
      "submission_deadline": "2026-02-03",
      "validity_date": "2026-02-20",
      "delivery_date": "2026-03-15"
    },
    
    "commercial_terms": {
      "currency": "USD",
      "tax_vat_mentioned": true,
      "vat_rate": 5.0,
      "incoterms": "DDP",
      "payment_terms": "Net 30",
      "performance_guarantee": true,
      "warranty_period": "12 months",
      "advance_payment_percentage": 30.0,
      "milestone_based_payment": true
    },
    
    "line_items": [
      {
        "line_number": 1,
        "item_code": "IT-DEV-100",
        "description": "Frontend Development",
        "quantity": 100,
        "unit_of_measure": "HOURS",
        "unit_price": 150.00,
        "total_price": 15000.00,
        "currency": "USD",
        "delivery_time": "8 weeks",
        "status_flags": ["requires_review"],
        "data_quality": "high",
        "requires_clarification": false
      },
      {
        "line_number": 2,
        "item_code": "IT-DEV-200",
        "description": "Backend API Development",
        "quantity": 80,
        "unit_of_measure": "HOURS",
        "unit_price": 175.00,
        "total_price": 14000.00,
        "currency": "USD",
        "data_quality": "high"
      }
    ],
    
    "signals": {
      "categorization": {
        "commodity_category": "IT Services",
        "supplier_tier": "Tier 1",
        "spend_category": "Professional Services"
      },
      "risk_indicators": {
        "validity_days": 31,
        "price_confidence": "high",
        "aggressive_discount": false,
        "heavy_deviations": false
      },
      "phase": "BIDDING"
    },
    
    "extraction_confidence": {
      "overall_confidence": 0.94,
      "field_confidence": {
        "parties": 0.98,
        "line_items": 0.87,
        "dates": 0.92,
        "commercial_terms": 0.91
      },
      "missing_fields": ["warranty_period"],
      "flags": ["high_confidence_extraction"]
    }
  },
  
  "validation_result": {
    "completeness_score": 92,
    "quality_score": 88,
    "overall_score": 90,
    "ready_for_processing": true,
    "requires_manual_review": false
  }
}
```

### Errors

- `400 INVALID_DOCUMENT` — Document could not be read
- `409 ALREADY_PROCESSING` — Document currently being processed
- `404 DOCUMENT_NOT_FOUND` — Document does not exist

---

## POST /api/v1/docs/convert

Convert extracted document to a target output format.

### Request

```json
{
  "document_id": "doc-xyz789",
  "output_format": "json",
  "include_ai_summary": true,
  "include_original_extraction": false
}
```

### Response (200 OK)

```json
{
  "success": true,
  "output_id": "output-001",
  "document_id": "doc-xyz789",
  "file_url": "https://kraftdstorage.blob.core.windows.net/exports/output-001.json",
  "file_type": "JSON",
  "file_size_bytes": 45623,
  "created_at": "2026-01-22T10:36:00Z",
  "expires_at": "2026-01-29T10:36:00Z"
}
```

---

# AI Workflows

## POST /api/v1/workflow/inquiry

Process procurement inquiry (RFQ analysis and supplier insights).

### Request

```json
{
  "document_id": "doc-xyz789",
  "analysis_depth": "detailed"
}
```

### Response (200 OK)

```json
{
  "success": true,
  "workflow_id": "wf-inquiry-001",
  "phase": "inquiry_analysis",
  "ai_analysis": {
    "key_insights": "RFQ for IT services with 12-week delivery requirement...",
    "supplier_recommendations": [
      {
        "recommended_supplier": "Tech Solutions Inc",
        "strength": "Excellent track record with similar projects",
        "risk": "Long lead time may impact timeline",
        "confidence": 0.92
      }
    ],
    "budget_analysis": {
      "estimated_budget": "AED 100,000 - 150,000",
      "budget_risk": "Within acceptable range",
      "cost_optimization_tips": ["Request volume discount for hours over 500"]
    }
  }
}
```

---

## POST /api/v1/workflow/estimation

Generate cost estimation from quotations.

### Request

```json
{
  "document_ids": ["doc-001", "doc-002", "doc-003"],
  "markup_percentage": 15
}
```

### Response (200 OK)

```json
{
  "success": true,
  "workflow_id": "wf-estimation-001",
  "estimated_cost": 115000,
  "cost_breakdown": {
    "labor": 65000,
    "materials": 35000,
    "overhead": 15000
  },
  "recommendation": "Quotation from Tech Solutions Inc offers best value"
}
```

---

## POST /api/v1/workflow/normalize-quotes

Normalize and compare multiple supplier quotations.

### Request

```json
{
  "document_ids": ["quote-001", "quote-002", "quote-003"],
  "normalize_currency": "USD",
  "comparison_basis": "unit_price"
}
```

### Response (200 OK)

```json
{
  "success": true,
  "workflow_id": "wf-normalize-001",
  "normalized_quotes": [
    {
      "supplier": "Tech Solutions Inc",
      "total_price": 29000,
      "currency": "USD",
      "unit_price": 162.50,
      "delivery_days": 56,
      "price_per_delivery_day": 517.86,
      "ranking": 1
    }
  ],
  "winner": "Tech Solutions Inc (best unit price)"
}
```

---

## POST /api/v1/workflow/comparison

Create detailed supplier comparison matrix.

### Request

```json
{
  "document_ids": ["quote-001", "quote-002"],
  "comparison_factors": ["price", "delivery", "warranty", "terms"]
}
```

### Response (200 OK)

```json
{
  "success": true,
  "workflow_id": "wf-comparison-001",
  "comparison_matrix": [
    {
      "factor": "Total Price",
      "supplier_1": "USD 29000",
      "supplier_2": "USD 31500",
      "winner": "Supplier 1"
    },
    {
      "factor": "Delivery Time",
      "supplier_1": "8 weeks",
      "supplier_2": "6 weeks",
      "winner": "Supplier 2"
    }
  ]
}
```

---

## POST /api/v1/workflow/proposal

Generate proposal document from extracted data.

### Request

```json
{
  "document_id": "doc-xyz789",
  "proposal_type": "technical",
  "include_commercial": true
}
```

### Response (200 OK)

```json
{
  "success": true,
  "workflow_id": "wf-proposal-001",
  "document_id": "doc-xyz789",
  "proposal_url": "https://kraftdstorage.blob.core.windows.net/exports/proposal-001.pdf",
  "status": "ready_for_download"
}
```

---

## POST /api/v1/workflow/po

Generate Purchase Order from quotation/proposal.

### Request

```json
{
  "quotation_document_id": "quote-001",
  "buyer_company": "Acme Corp",
  "po_terms": {
    "payment_terms": "Net 45",
    "delivery_address": "123 Main St, Dubai",
    "special_conditions": []
  }
}
```

### Response (200 OK)

```json
{
  "success": true,
  "workflow_id": "wf-po-001",
  "po_number": "PO-2026-00123",
  "po_document_url": "https://kraftdstorage.blob.core.windows.net/exports/po-2026-00123.pdf",
  "created_at": "2026-01-22T10:40:00Z"
}
```

---

## POST /api/v1/workflow/proforma-invoice

Generate Pro-Forma Invoice.

### Request

```json
{
  "po_document_id": "po-001",
  "invoice_terms": {
    "payment_due_date": "2026-02-22",
    "bank_details": { "account": "...", "iban": "..." }
  }
}
```

### Response (200 OK)

```json
{
  "success": true,
  "invoice_number": "PINV-2026-001",
  "invoice_url": "https://kraftdstorage.blob.core.windows.net/exports/pinv-2026-001.pdf"
}
```

---

# Agent Interface

## POST /api/v1/agent/chat

Interactive AI agent for document Q&A and guidance.

### Request

```json
{
  "message": "What is the total cost of this quotation?",
  "document_id": "doc-xyz789",
  "conversation_id": "conv-001"
}
```

### Response (200 OK)

```json
{
  "success": true,
  "conversation_id": "conv-001",
  "response": "The total cost of the quotation is USD 29,000 for 180 hours of development work (Frontend: 100 hours @ USD 150/hr = USD 15,000, Backend: 80 hours @ USD 175/hr = USD 14,000). This includes 5% VAT (USD 1,450).",
  "confidence": 0.96,
  "sources": ["line_items", "commercial_terms"]
}
```

---

## GET /api/v1/agent/status

Get agent operational status and capabilities.

### Response (200 OK)

```json
{
  "status": "operational",
  "model": "gpt-4o-mini",
  "capabilities": [
    "document_qa",
    "data_extraction",
    "cost_analysis",
    "supplier_evaluation",
    "workflow_automation"
  ],
  "max_conversation_length": 50,
  "response_time_ms_avg": 1200
}
```

---

## GET /api/v1/agent/learning

Get agent learning metrics (document understanding improvement).

### Response (200 OK)

```json
{
  "documents_analyzed": 1245,
  "accuracy_improvement": {
    "week_1": "85.2%",
    "week_2": "87.8%",
    "week_3": "89.3%"
  },
  "most_improved_categories": ["quotations", "line_items"],
  "model_version": "gpt-4o-mini:v1.2"
}
```

---

## POST /api/v1/agent/check-di-decision

Get AI recommendation on whether to use Azure Document Intelligence for extraction.

### Request

```json
{
  "document_id": "doc-xyz789"
}
```

### Response (200 OK)

```json
{
  "should_use_di": true,
  "recommendation": "Document is scanned/image-based. Azure Document Intelligence will improve extraction accuracy by 15-20%.",
  "confidence": 0.92,
  "reason_codes": ["image_based", "complex_tables", "handwritten_elements"]
}
```

---

# Export & Download

## GET /api/v1/documents/{document_id}/output

Get generated output files for a document.

### Request

```
Authorization: Bearer <token>
```

### Response (200 OK)

```json
{
  "document_id": "doc-xyz789",
  "outputs": [
    {
      "output_id": "output-001",
      "format": "json",
      "file_size_bytes": 45623,
      "created_at": "2026-01-22T10:36:00Z",
      "expires_at": "2026-01-29T10:36:00Z",
      "download_url": "https://kraftdstorage.blob.core.windows.net/exports/output-001.json",
      "download_count": 2
    },
    {
      "output_id": "output-002",
      "format": "pdf",
      "file_size_bytes": 512000,
      "created_at": "2026-01-22T10:37:00Z",
      "expires_at": "2026-01-29T10:37:00Z",
      "download_url": "https://kraftdstorage.blob.core.windows.net/exports/output-002.pdf",
      "download_count": 1
    }
  ]
}
```

---

## POST /api/v1/exports/{export_workflow_id}/feedback

Submit feedback on export quality and accuracy.

### Request

```json
{
  "quality_rating": 5,
  "accuracy_rating": 4,
  "completeness_rating": 5,
  "comments": "Excellent extraction, data was complete and accurate.",
  "feedback_type": "positive",
  "issues_found": []
}
```

### Response (200 OK)

```json
{
  "feedback_id": "fb-001",
  "message": "Thank you for your feedback. This helps us improve accuracy.",
  "recorded_at": "2026-01-22T10:45:00Z"
}
```

---

# Error Handling

All errors follow this standard format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": {
      "field": "optional field that caused error",
      "hint": "optional suggestion to fix"
    }
  }
}
```

### Common HTTP Status Codes

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | Success | Document extracted successfully |
| 201 | Created | Document uploaded |
| 400 | Bad Request | Invalid email format |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | User cannot access document |
| 404 | Not Found | Document does not exist |
| 409 | Conflict | Document already being processed |
| 413 | Payload Too Large | File exceeds size limit |
| 429 | Too Many Requests | Rate limit exceeded or quota exceeded |
| 500 | Server Error | Unexpected internal error |
| 503 | Service Unavailable | Database or AI service down |

---

# Rate Limiting

Requests are rate-limited per user and API key:

- **Free Plan**: 100 requests/hour, 10 documents/day
- **Pro Plan**: 1000 requests/hour, 100 documents/day
- **Enterprise Plan**: Unlimited (custom SLA)

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1642779600
```

---

# Examples

## Complete Document Processing Flow

### 1. Register

```bash
curl -X POST https://api.kraftd.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "firstName": "John",
    "lastName": "Doe",
    "acceptTerms": true,
    "acceptPrivacy": true
  }'
```

### 2. Verify Email

```bash
curl -X POST https://api.kraftd.com/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "otp_token": "123456"
  }'
```

### 3. Login

```bash
curl -X POST https://api.kraftd.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Response contains**: `access_token`

### 4. Upload Document

```bash
curl -X POST https://api.kraftd.com/api/v1/docs/upload \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@quotation.pdf"
```

**Response contains**: `document_id`

### 5. Extract Data

```bash
curl -X POST https://api.kraftd.com/api/v1/docs/extract \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc-xyz789"
  }'
```

**Response contains**: Fully extracted KraftdDocument with all fields

### 6. Generate Export

```bash
curl -X POST https://api.kraftd.com/api/v1/docs/convert \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc-xyz789",
    "output_format": "json"
  }'
```

**Response contains**: `file_url` for download

### 7. Submit Feedback

```bash
curl -X POST https://api.kraftd.com/api/v1/exports/export-001/feedback \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "quality_rating": 5,
    "accuracy_rating": 4,
    "comments": "Excellent work!"
  }'
```

---

## Implementation Notes

- **Base URL**: `https://api.kraftd.com/api/v1`
- **Timeout**: 60 seconds per request
- **Connection Pool**: Keep-alive enabled
- **Retry Policy**: Exponential backoff with jitter (max 3 retries)
- **Logging**: All requests logged for debugging and analytics
- **API Documentation**: OpenAPI/Swagger available at `/docs`
- **Status Page**: https://status.kraftd.com

---

**Last Updated**: January 22, 2026  
**API Version**: 1.0.0  
**Python Version**: 3.13  
**Framework**: FastAPI 0.128