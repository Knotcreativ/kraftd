# Kraftd Docs — Document Processing Pipeline

This document defines the **actual** end-to-end backend pipeline for document intelligence processing.

The core unit of work is a single **document extraction** — one uploaded file flowing through intelligent processing stages and stored as a unified **ExtractionRecord** in Azure Cosmos DB.

---

# Pipeline Architecture

```
UPLOAD
   ↓
[1] CLASSIFY      (Identify document type)
   ↓
[2] MAP           (Extract structured fields)
   ↓
[3] INFER         (Apply business logic)
   ↓
[4] VALIDATE      (Score quality & completeness)
   ↓
[5] TRANSFORM     (Apply user edits + preferences)
   ↓
[6] EXPORT        (Generate output files)
   ↓
[7] FEEDBACK      (Collect user ratings)
   ↓
COMPLETE
```

---

# Stage 0: Document Upload

## Trigger
- User calls `POST /api/v1/docs/upload` (single)
- Or `POST /api/v1/docs/upload/batch` (multiple)

## Input
- File: PDF, DOCX, XLSX, or image (max 50 MB)
- Optional: document_type hint (RFQ, BOQ, QUOTATION, INVOICE, PO, CONTRACT, or AUTO)
- Partition key: `owner_email` (from JWT token)

## Processing
1. **Validate** — Check file type, size, and user quota
2. **Store Blob** — Upload file to Azure Blob Storage
3. **Create Record** — Initialize ExtractionRecord in Cosmos DB:
   ```python
   {
     "id": "{document_id}:direct_parse",
     "owner_email": "user@example.com",
     "document_id": "doc-xyz789",
     "source": "direct_parse",
     "document": {
       "file_name": "quotation.pdf",
       "file_type": "PDF",
       "file_size_bytes": 2048576,
       "uploaded_at": "2026-01-22T10:30:00Z"
     },
     "status": "uploaded"
   }
   ```
4. **Extract Text** — Read file contents (PDF text, OCR for images)
5. **Update Quota** — Increment `user.quota_used`

## Output
```json
{
  "document_id": "doc-xyz789",
  "status": "uploaded",
  "blob_url": "https://kraftdstorage.blob.core.windows.net/documents/doc-xyz789.pdf",
  "processing_ready": true
}
```

## Error Handling
- `400 FILE_TOO_LARGE` — File > 50 MB
- `400 INVALID_FILE_TYPE` — Unsupported format
- `429 QUOTA_EXCEEDED` — User at quota limit
- `507 STORAGE_ERROR` — Blob upload failed

---

# Stage 1: Classify

## Trigger
- Automatic (triggered during extraction)
- Or manual: `POST /api/v1/docs/extract` with `force_reprocessing: true`

## Input
- Raw text extracted from document
- Optional document_type hint from user

## Processing
**UniversalClassifier** (machine learning model):
1. Analyze document structure, keywords, patterns
2. Identify document type with confidence score
3. Return classification with reasoning

### Supported Document Types
- **RFQ** — Request for Quotation
- **BOQ** — Bill of Quantities
- **QUOTATION** — Supplier quotation
- **INVOICE** — Invoice
- **PO** — Purchase Order
- **CONTRACT** — Contract
- **OTHER** — Unable to classify

## Output
```json
{
  "document_type": "QUOTATION",
  "confidence": 0.96,
  "reasoning": "Contains 'quotation', date, supplier info, line items, and pricing"
}
```

## Latency
- Typically: **100-500 ms**
- Data: Analyzed locally (no Azure calls)

---

# Stage 2: Map (Field Extraction)

## Trigger
- Automatic after Stage 1

## Input
- Raw text from document
- Classification result (document_type)
- Document metadata (filename, size, upload time)

## Processing
**DocumentMapper** uses pattern matching, regex, and heuristics:

1. **Extract Metadata**
   - Document number (e.g., "QUOT-2026-001")
   - Issue date, revision, page count
   - Document-specific fields (RFQ scope, PO terms, etc.)

2. **Extract Parties**
   - Issuer/Supplier (company, contact, address)
   - Recipient/Buyer (company, contact, address)
   - Additional parties if present

3. **Extract Key Dates**
   - Issue date, submission deadline, validity, delivery, contract dates

4. **Extract Line Items**
   - Item number, description, quantity, UOM, unit price, total price
   - Technical specs, discounts, packaging notes
   - Quality flags (requires_clarification, data_quality)

5. **Extract Commercial Terms**
   - Currency, payment terms, incoterms
   - Tax/VAT rates, advance payment, payment milestones
   - Warranty, guarantee, retention, insurance

6. **Extract Project Context**
   - Project name, code, client, location, discipline, package

7. **Normalize & Validate**
   - Fill missing fields with defaults
   - Validate constraints (qty > 0, dates make sense, etc.)
   - Calculate field confidence scores

## Output
**KraftdDocument** (fully structured):

```python
{
  "document_id": "doc-xyz789",
  "metadata": {
    "document_type": "QUOTATION",
    "document_number": "QUOT-2026-001",
    "issue_date": "2026-01-20",
    "revision_number": "1",
    "page_count": 5
  },
  
  "parties": {
    "issuer": {
      "name": "Tech Solutions Inc",
      "legal_entity": "Tech Solutions Inc (LLC)",
      "trn_vat_number": "100123456789",
      "contact_person": {
        "name": "John Smith",
        "email": "john@tech.com",
        "phone": "+1-555-0100"
      },
      "registered_address": {
        "address_line1": "123 Tech Park",
        "city": "San Francisco",
        "country": "USA"
      }
    },
    "recipient": {
      "name": "Acme Corp"
    }
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
    "payment_terms": "Net 30",
    "advance_payment_percentage": 30.0
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
      "data_quality": "high",
      "requires_clarification": false
    },
    {
      "line_number": 2,
      "description": "Backend API Development",
      "quantity": 80,
      "unit_of_measure": "HOURS",
      "unit_price": 175.00,
      "total_price": 14000.00,
      "currency": "USD"
    }
  ],
  
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
}
```

## Latency
- Typically: **800-1500 ms** (pattern matching + validation)
- Data: Processed locally (no Azure calls)

## Error Handling
- `400 INVALID_DOCUMENT` — Text could not be parsed
- `400 MISSING_CRITICAL_FIELDS` — No parties or line items found

---

# Stage 3: Infer (Business Logic)

## Trigger
- Automatic after Stage 2

## Input
- KraftdDocument from Stage 2

## Processing
**DocumentInferencer** applies business rules:

1. **Infer Totals**
   - Sum line_item prices → subtotal
   - Calculate VAT → tax
   - Sum → total

2. **Infer Currency**
   - Use detected currency from document
   - Fall back to country of issuer
   - Validate all line items use consistent currency

3. **Infer Payment Structure**
   - Detect payment milestones
   - Identify advance payment requirements
   - Calculate payment schedule

4. **Infer Delivery Schedule**
   - Extract delivery dates from line items
   - Identify critical path / longest lead time
   - Flag split deliveries

5. **Classify Risk Indicators**
   - Price trends (aggressive discounts? outliers?)
   - Long lead times
   - Unusual payment terms
   - Supplier history signals (if available)

6. **Populate Signals**
   - Categorization (commodity, supplier tier, spend category)
   - Risk indicators (validity days, price confidence, etc.)
   - Behavioral patterns (supplier on-time rate, etc.)
   - Phase (Planning, Bidding, Contracting, Execution)
   - Criticality (Low, Medium, High)

## Output
**Enhanced KraftdDocument** with:
- Calculated totals, tax, payment schedule
- Inferred signals for risk/procurement analysis
- Supplier recommendation flags

## Latency
- Typically: **200-400 ms** (rule evaluation)
- Data: Processed locally

---

# Stage 4: Validate (Quality Scoring)

## Trigger
- Automatic after Stage 3

## Input
- Enhanced KraftdDocument from Stage 3

## Processing
**DocumentValidator** scores completeness and quality:

1. **Calculate Field Presence Score**
   - Count extracted vs. required fields
   - Weight by importance (parties > 10%, line_items > 30%)
   - Result: 0-100

2. **Calculate Data Quality Score**
   - Confidence scores per field
   - Data type matches (dates are dates, numbers are numbers)
   - Outlier detection
   - Result: 0-100

3. **Determine Readiness**
   - `ready_for_processing = true` if score > 70
   - `requires_manual_review = true` if score < 60

4. **Generate Recommendations**
   - Suggest manual review of low-confidence fields
   - Identify missing critical data
   - Flag potential data entry errors

## Output
```json
{
  "completeness_score": 92,
  "quality_score": 88,
  "overall_score": 90,
  "ready_for_processing": true,
  "requires_manual_review": false,
  "missing_fields": [],
  "low_confidence_fields": ["warranty_period"],
  "recommendations": []
}
```

## Latency
- Typically: **100-200 ms** (scoring)
- Data: Processed locally

---

# Stage 5: Transform (User Edits + Preferences)

## Trigger
- Optional: User submits schema edits
- Automatic: Before export if user has made modifications

## Input
- Original KraftdDocument
- User modifications (list of field edits with timestamps, reason, user)
- Conversion preferences (output format, include_ai_summary, etc.)

## Processing
**DocumentTransformer**:

1. **Apply User Modifications**
   - For each modification: original → modified value
   - Track who changed it, when, and why
   - Maintain version history

2. **Merge AI Summary** (if user requested)
   - Integrate AI insights into document
   - Flag fields that AI added

3. **Apply Preferences**
   - Include/exclude original extraction data
   - Include/exclude AI analysis
   - Format selections

4. **Generate Transformed Document**
   - Clean, normalized data ready for export
   - Audit trail of all changes

## Output
```json
{
  "transformation_id": "transform-001",
  "user_modifications_applied": true,
  "document_data": { ... normalized fields ... },
  "ai_summary_integrated": { ... },
  "audit_trail": [
    {
      "field": "delivery_date",
      "original": "2026-02-28",
      "modified": "2026-02-15",
      "modified_by": "user@example.com",
      "reason": "Client requires earlier delivery"
    }
  ]
}
```

## Latency
- Typically: **150-300 ms**

---

# Stage 6: Export (Output Generation)

## Trigger
- User calls `POST /api/v1/docs/convert` with output_format

## Input
- Transformed document
- Output format (json, pdf, csv, xlsx)
- Optional: template selection

## Processing
**ExportGenerator**:

1. **Format Data** — Convert KraftdDocument to target format
2. **Generate Template** — Apply formatting, layout, branding
3. **Create File** — Write to disk or buffer
4. **Upload to Blob** — Store in Azure Blob Storage
5. **Create Download Link** — Generate SAS URL (7-day expiry)
6. **Track Download** — Record in ExtractionRecord.download_info

### Supported Formats
- **JSON** — Structured data export (fastest, smallest)
- **CSV** — Line items + metadata (for spreadsheet import)
- **XLSX** — Excel with multiple sheets (prettified)
- **PDF** — Formatted document with branding (slowest)

## Output
```json
{
  "output_id": "output-001",
  "format": "json",
  "file_url": "https://kraftdstorage.blob.core.windows.net/exports/output-001.json",
  "file_size_bytes": 45623,
  "created_at": "2026-01-22T10:36:00Z",
  "expires_at": "2026-01-29T10:36:00Z"
}
```

## Latency
- **JSON**: 200-300 ms
- **CSV**: 300-500 ms
- **XLSX**: 500-800 ms
- **PDF**: 2000-3000 ms (includes formatting)

---

# Stage 7: Feedback (Quality Improvement)

## Trigger
- User downloads file → feedback modal appears
- User calls `POST /api/v1/exports/{export_id}/feedback`

## Input
```json
{
  "quality_rating": 5,           // 1-5
  "accuracy_rating": 4,
  "completeness_rating": 5,
  "comments": "Excellent extraction",
  "feedback_type": "positive",   // positive | negative | neutral | suggestion
  "issues_found": []
}
```

## Processing
1. **Store Feedback** — Save to ExtractionRecord.feedback
2. **Update Metrics** — Aggregate for user + system-wide
3. **Trigger Improvements** — Flag low-rated documents for model training
4. **Send Thank You** — User receives thank you message

## Output
```json
{
  "feedback_id": "fb-001",
  "recorded_at": "2026-01-22T10:45:00Z",
  "impact": "Your feedback helps us improve accuracy"
}
```

---

# Complete ExtractionRecord Structure

After all stages, the ExtractionRecord in Cosmos DB contains:

```python
{
  # Identity
  "id": "doc-xyz789:direct_parse",
  "owner_email": "user@example.com",
  "document_id": "doc-xyz789",
  "source": "direct_parse",
  
  # Timestamps
  "created_at": "2026-01-22T10:30:00Z",
  "updated_at": "2026-01-22T10:45:00Z",
  
  # Stage 0: Upload
  "document": { file_name, file_type, uploaded_at, ... },
  "extraction_data": { raw text, tables, images, ... },
  
  # Stages 1-4: Processing
  "extracted_document": {
    # Stage 1: Classification
    # Stage 2: Field extraction (parties, dates, line_items, etc.)
    # Stage 3: Inferred signals (risk, categorization, phase)
    # Stage 4: Validation scores
  },
  
  # Stage 5: User interactions
  "ai_summary": { key_insights, recommendations, ... },
  "user_modifications": { list of edits with timestamps },
  "conversion_preferences": { output_format, include_ai_summary, ... },
  
  # Stage 6: Export
  "transformed_data": { final document + audit trail },
  "download_info": { urls, download_count, expiry },
  
  # Stage 7: Feedback
  "feedback": { ratings, comments, feedback_type },
  
  # Status
  "status": "exported",  // uploaded | extracted | reviewed | transformed | exported | archived
  "tags": ["urgent", "supplier_comparison"],
  "custom_metadata": {}
}
```

---

# Quota Enforcement

Quota is checked at critical stages:

| Stage | Check | Cost | Quota Hit Response |
|-------|-------|------|-------------------|
| Upload | Before file storage | 1 unit/doc | 429 QUOTA_EXCEEDED |
| Classify | Before ML inference | 0.5 units | 429 QUOTA_EXCEEDED |
| Extract | Before field mapping | 1 unit | 429 QUOTA_EXCEEDED |
| Infer | Before business logic | 0.5 units | 429 QUOTA_EXCEEDED |
| Export | Before file generation | 1 unit | 429 QUOTA_EXCEEDED |

**Quota Plans:**
- Free: 100 units/month
- Pro: 5000 units/month
- Enterprise: Unlimited

---

# Error Recovery

Each stage has error recovery:

1. **Validation Failure** → Return error, don't advance stage
2. **AI Service Timeout** → Retry with exponential backoff (max 3x)
3. **Storage Failure** → Queue for retry, notify user
4. **Partial Extraction** → Return best-effort results with confidence scores
5. **Critical Error** → Mark document as `failed`, don't process further

---

# Pipeline Monitoring

System logs:
- **Per-stage latency** (track performance regressions)
- **Success/failure rate** (detect bugs)
- **Quota usage** (capacity planning)
- **AI token usage** (cost optimization)
- **User feedback ratings** (quality metrics)

Metrics endpoint: `GET /api/v1/metrics`

---

# Pipeline Scalability

The pipeline is designed for:
- ✅ Batch processing (10+ documents concurrently)
- ✅ High-throughput (100s docs/hour per tenant)
- ✅ Low-latency (< 10 seconds end-to-end for typical documents)
- ✅ High availability (database replication, blob redundancy)
- 🔄 Async job queues (future enhancement)
- 🔄 Distributed processing (future enhancement)

---

# Example: Complete Flow Timing

**Typical 3-page quotation (PDF, 2 MB):**

```
Stage 0 (Upload):        500 ms    →  total: 500 ms
Stage 1 (Classify):      300 ms    →  total: 800 ms
Stage 2 (Map):          1200 ms    →  total: 2000 ms
Stage 3 (Infer):         250 ms    →  total: 2250 ms
Stage 4 (Validate):      150 ms    →  total: 2400 ms
────────────────────────────────────────────────
Total extraction:       2400 ms (2.4 seconds)

User edits:            variable
Stage 5 (Transform):     200 ms
Stage 6 (Export JSON):   250 ms    →  total: 3100 ms
Stage 7 (Feedback):      100 ms    →  total: 3200 ms
────────────────────────────────────────────────
Full end-to-end:      ~3-5 seconds (depending on user actions)
```

---

**Last Updated**: January 22, 2026  
**Pipeline Version**: 1.0  
**Database**: Azure Cosmos DB  
**Processing Framework**: FastAPI + Python 3.13