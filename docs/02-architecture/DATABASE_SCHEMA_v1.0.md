# Database Schema Document

**Version:** 1.0  
**Status:** APPROVED  
**Database:** MongoDB (Azure Cosmos DB)  
**Last Updated:** 2026-01-17

---

## Collections Overview

| Collection | Purpose | Est. Records | Primary Key |
|-----------|---------|-------------|------------|
| users | User accounts & auth | ~1,000 | user_id |
| documents | Uploaded documents | ~50,000 | document_id |
| extracted_data | OCR/AI extraction results | ~50,000 | extraction_id |
| workflows | Document workflows | ~10,000 | workflow_id |
| quotations | Vendor quotations | ~30,000 | quotation_id |
| comparisons | Price comparisons | ~10,000 | comparison_id |
| purchase_orders | Generated POs | ~15,000 | po_id |
| audit_log | System audit trail | ~200,000 | log_id |

---

## Collection: users

**Purpose:** User accounts, authentication, roles

**Fields:**

```json
{
  "user_id": "usr_abc123",
  "email": "john.doe@company.com",
  "full_name": "John Doe",
  "password_hash": "bcrypt_hash_...",
  "role": "procurement_officer",
  "department": "Procurement",
  "company": "ACME Corp",
  "status": "active",
  "last_login": "2026-01-17T10:30:00Z",
  "created_at": "2025-10-01T08:00:00Z",
  "updated_at": "2026-01-17T10:30:00Z",
  "preferences": {
    "timezone": "UTC-5",
    "language": "en",
    "notification_email": true
  },
  "permissions": [
    "upload_documents",
    "view_documents",
    "create_workflows",
    "generate_pos"
  ]
}
```

**Indexes:**
- `email` (unique)
- `company` (for multi-tenant isolation)
- `status` (for active user queries)

---

## Collection: documents

**Purpose:** Track uploaded documents

**Fields:**

```json
{
  "document_id": "doc_xyz789",
  "user_id": "usr_abc123",
  "company_id": "comp_123",
  "filename": "RFQ_2026_001.pdf",
  "document_type": "RFQ",
  "file_size": 1048576,
  "content_type": "application/pdf",
  "storage_path": "blob://documents/2026-01/doc_xyz789.pdf",
  "status": "extracted",
  "extraction_status": {
    "overall_confidence": 96,
    "field_confidence": {
      "project_name": 98,
      "budget": 94,
      "deadline": 92
    }
  },
  "metadata": {
    "pages": 5,
    "document_date": "2026-01-15",
    "vendor_name": "ACME Solutions"
  },
  "extracted_data_id": "ext_789abc",
  "workflow_ids": ["wf_001", "wf_002"],
  "tags": ["procurement", "rfq", "january"],
  "created_at": "2026-01-17T09:00:00Z",
  "processing_time_ms": 2345,
  "uploaded_at": "2026-01-17T09:00:00Z",
  "updated_at": "2026-01-17T10:30:00Z"
}
```

**Indexes:**
- `user_id` + `created_at` (for document list queries)
- `status` (for filtering)
- `document_type` (for type-specific queries)
- `workflow_ids` (for finding docs in specific workflows)

---

## Collection: extracted_data

**Purpose:** Store AI-extracted structured data

**Fields:**

```json
{
  "extraction_id": "ext_789abc",
  "document_id": "doc_xyz789",
  "extraction_method": "azure_document_intelligence",
  "extraction_timestamp": "2026-01-17T09:05:00Z",
  "raw_text": "Project: Website Redesign...",
  "structured_fields": {
    "project_name": {
      "value": "Website Redesign",
      "confidence": 98,
      "source_text": "Project: Website Redesign"
    },
    "budget": {
      "value": 50000,
      "currency": "USD",
      "confidence": 94,
      "source_text": "$50,000"
    },
    "required_by": {
      "value": "2026-02-15",
      "confidence": 92,
      "source_text": "Needed by Feb 15, 2026"
    },
    "line_items": [
      {
        "item": "Frontend Development",
        "hours": 100,
        "rate": 150,
        "amount": 15000,
        "confidence": 90
      },
      {
        "item": "Backend API Development",
        "hours": 80,
        "rate": 175,
        "amount": 14000,
        "confidence": 88
      }
    ]
  },
  "extraction_errors": [],
  "manual_corrections": {
    "corrected_fields": ["budget"],
    "corrected_at": "2026-01-17T10:00:00Z",
    "corrected_by": "usr_abc123"
  },
  "validation_status": "approved"
}
```

**Indexes:**
- `document_id` (foreign key lookup)
- `validation_status` (for finding unreviewed extractions)

---

## Collection: workflows

**Purpose:** Track document workflow/process state

**Fields:**

```json
{
  "workflow_id": "wf_001",
  "document_id": "doc_xyz789",
  "user_id": "usr_abc123",
  "workflow_type": "procurement",
  "workflow_template": "standard_rfq",
  "current_step": 3,
  "total_steps": 5,
  "status": "in_progress",
  "started_at": "2026-01-17T09:30:00Z",
  "deadline": "2026-02-15",
  "days_remaining": 29,
  "steps": [
    {
      "step_number": 1,
      "name": "Inquiry",
      "description": "Initial requirement gathering",
      "status": "completed",
      "completed_at": "2026-01-17T09:35:00Z"
    },
    {
      "step_number": 2,
      "name": "Estimation",
      "description": "Get vendor estimates",
      "status": "completed",
      "completed_at": "2026-01-17T10:00:00Z"
    },
    {
      "step_number": 3,
      "name": "Quotation",
      "description": "Collect formal quotations",
      "status": "in_progress",
      "started_at": "2026-01-17T10:05:00Z"
    },
    {
      "step_number": 4,
      "name": "Comparison",
      "status": "pending"
    },
    {
      "step_number": 5,
      "name": "Purchase Order",
      "status": "pending"
    }
  ],
  "assigned_to": ["usr_abc123", "usr_def456"],
  "notifications_sent": 2,
  "updated_at": "2026-01-17T10:30:00Z"
}
```

**Indexes:**
- `document_id` (link to document)
- `user_id` + `status` (for user's active workflows)
- `deadline` (for deadline tracking)

---

## Collection: quotations

**Purpose:** Store vendor quotations

**Fields:**

```json
{
  "quotation_id": "quot_abc123",
  "workflow_id": "wf_001",
  "document_id": "doc_xyz789",
  "vendor_name": "ACME Solutions",
  "vendor_email": "sales@acme.com",
  "vendor_contact": "John Smith",
  "quotation_date": "2026-01-16",
  "valid_until": "2026-02-16",
  "line_items": [
    {
      "description": "Frontend Development",
      "quantity": 1,
      "unit_price": 15000,
      "amount": 15000
    },
    {
      "description": "Backend API Development",
      "quantity": 1,
      "unit_price": 14000,
      "amount": 14000
    },
    {
      "description": "QA & Testing",
      "quantity": 1,
      "unit_price": 5000,
      "amount": 5000
    }
  ],
  "subtotal": 34000,
  "tax": 2720,
  "total_amount": 36720,
  "currency": "USD",
  "payment_terms": "Net 30",
  "delivery_timeline": "8 weeks",
  "special_terms": "Includes 12-month warranty",
  "attached_document_id": "doc_quote_source",
  "score": 8.7,
  "status": "received",
  "received_at": "2026-01-17T08:00:00Z"
}
```

**Indexes:**
- `workflow_id` (find quotes in workflow)
- `vendor_name` (for vendor history)
- `status` (for filtering)

---

## Collection: comparisons

**Purpose:** Compare multiple quotations

**Fields:**

```json
{
  "comparison_id": "comp_001",
  "workflow_id": "wf_001",
  "document_id": "doc_xyz789",
  "created_by": "usr_abc123",
  "quotation_ids": ["quot_abc123", "quot_def456", "quot_ghi789"],
  "comparison_criteria": {
    "price": { "weight": 40 },
    "timeline": { "weight": 30 },
    "payment_terms": { "weight": 20 },
    "vendor_rating": { "weight": 10 }
  },
  "scored_quotations": [
    {
      "quotation_id": "quot_abc123",
      "vendor_name": "ACME Solutions",
      "total_amount": 36720,
      "timeline": "8 weeks",
      "payment_terms": "Net 30",
      "scores": {
        "price": 35,
        "timeline": 28,
        "payment_terms": 20,
        "vendor_rating": 8
      },
      "final_score": 91
    }
  ],
  "recommendation": {
    "quotation_id": "quot_abc123",
    "vendor_name": "ACME Solutions",
    "final_score": 91,
    "savings": 2400,
    "reasoning": [
      "Best price point",
      "Fastest timeline",
      "Favorable payment terms"
    ]
  },
  "status": "completed",
  "created_at": "2026-01-17T11:00:00Z"
}
```

**Indexes:**
- `workflow_id` (find comparison for workflow)
- `created_by` (for user history)

---

## Collection: purchase_orders

**Purpose:** Generated purchase orders

**Fields:**

```json
{
  "po_id": "po_001",
  "po_number": "PO-2026-001",
  "workflow_id": "wf_001",
  "comparison_id": "comp_001",
  "selected_quotation_id": "quot_abc123",
  "created_by": "usr_abc123",
  "vendor_name": "ACME Solutions",
  "vendor_contact": "John Smith",
  "vendor_email": "sales@acme.com",
  "po_date": "2026-01-17",
  "po_effective_date": "2026-01-17",
  "delivery_address": "123 Business Ave, Suite 100, New York, NY 10001",
  "line_items": [
    {
      "po_line": 1,
      "description": "Frontend Development",
      "quantity": 1,
      "unit_price": 15000,
      "amount": 15000
    }
  ],
  "subtotal": 34000,
  "tax": 2720,
  "total_amount": 36720,
  "currency": "USD",
  "payment_terms": "Net 30",
  "delivery_terms": "FOB Shipping Point",
  "special_terms": "Includes 12-month warranty",
  "terms_and_conditions": "Standard T&Cs...",
  "status": "draft",
  "approval_chain": [
    {
      "approver": "usr_mgr123",
      "approval_level": "manager",
      "status": "pending",
      "due_date": "2026-01-18"
    }
  ],
  "created_at": "2026-01-17T12:00:00Z",
  "modified_at": "2026-01-17T12:00:00Z"
}
```

**Indexes:**
- `po_number` (unique lookup)
- `vendor_name` (for vendor history)
- `status` (for filtering)
- `created_by` (for user's POs)

---

## Collection: audit_log

**Purpose:** Track all system actions for compliance

**Fields:**

```json
{
  "log_id": "audit_xyz123",
  "timestamp": "2026-01-17T10:30:00Z",
  "user_id": "usr_abc123",
  "action": "document_uploaded",
  "resource_type": "document",
  "resource_id": "doc_xyz789",
  "details": {
    "filename": "RFQ_2026_001.pdf",
    "file_size": 1048576,
    "extraction_confidence": 96
  },
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "status": "success",
  "http_status": 200
}
```

**Indexes:**
- `user_id` + `timestamp` (for user activity)
- `resource_type` + `resource_id` (for resource audit trail)
- `timestamp` (for compliance queries)

---

## Data Integrity & Constraints

| Constraint | Implementation |
|-----------|-----------------|
| User references | Foreign key to users collection |
| Document consistency | Document must exist before workflow |
| Extraction validity | Extraction must match document extraction_id |
| Workflow transitions | Must follow predefined state machine |
| PO authorization | Requires approval from assigned approvers |
| Tax calculations | Always recalculated from line items |

---

## TTL (Time-to-Live) Settings

| Collection | TTL | Purpose |
|-----------|-----|---------|
| audit_log | 2 years | Compliance retention period |
| extraction_errors | 30 days | Cleanup temporary errors |
| draft_pos | 90 days | Auto-purge abandoned drafts |
| deleted_documents | 30 days | Soft delete recovery window |

---

## Partitioning Strategy

**Partition Key:** `user_id` + `company_id`
- Ensures data isolation per tenant
- Enables horizontal scaling
- Supports multi-tenancy

---

## Sample Query Patterns

### Get user's recent documents
```
db.documents.find(
  { user_id: "usr_abc123" },
  { sort: { created_at: -1 }, limit: 20 }
)
```

### Get workflow with all nested steps
```
db.workflows.findOne({ workflow_id: "wf_001" })
```

### Compare quotations for a workflow
```
db.comparisons.findOne({
  workflow_id: "wf_001"
})
```

---

**Reference:** `/docs/02-architecture/DATABASE_SCHEMA_v1.0.md`
