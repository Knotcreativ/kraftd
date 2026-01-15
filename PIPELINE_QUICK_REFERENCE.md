# Kraftd Pipeline - Quick Reference Guide

## Visual Architecture

### High-Level Flow
```
┌─────────────────────────────────────────────────────────────────┐
│                        DOCUMENT INPUT                            │
│              (PDF, Word, Excel, Image, or Scanned)              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  AUTO-PARSE FILE     │
                  │─────────────────────│
                  │ Detect format        │
                  │ Run format processor │
                  │ Extract text, tables │
                  └──────────────┬───────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
         ┌────────────────────┐     ┌────────────────────┐
         │ LOCAL PARSING      │     │ AZURE DOC INTEL    │
         │────────────────────│     │────────────────────│
         │ text, tables       │     │ Layout analysis    │
         │ paragraphs         │     │ Form fields        │
         │ line items         │     │ High confidence    │
         └────────────┬───────┘     └────────────┬───────┘
                      │                          │
                      └──────────────┬───────────┘
                                     │
                                     ▼
                      ┌─────────────────────────┐
                      │ ① CLASSIFIER           │
                      │─────────────────────────│
                      │ What type of doc?       │
                      │ How confident?          │
                      │ Any alternatives?       │
                      │                         │
                      │ Confidence < 60%?       │
                      │ → Manual review         │
                      └──────────────┬──────────┘
                                     │
                                     ▼
                      ┌─────────────────────────┐
                      │ ② MAPPER               │
                      │─────────────────────────│
                      │ Extract all fields      │
                      │ Normalize to schema     │
                      │ Track mappings          │
                      │ Validate constraints    │
                      │                         │
                      │ Errors found?           │
                      │ → Log but continue       │
                      └──────────────┬──────────┘
                                     │
                                     ▼
                      ┌─────────────────────────┐
                      │ ③ INFERENCER           │
                      │─────────────────────────│
                      │ Fill missing fields     │
                      │ Calculate totals        │
                      │ Apply business rules    │
                      │ Resolve ambiguities     │
                      │                         │
                      │ Conflicts found?        │
                      │ → Flag for review       │
                      └──────────────┬──────────┘
                                     │
                                     ▼
                      ┌─────────────────────────┐
                      │ ④ VALIDATOR            │
                      │─────────────────────────│
                      │ Score completeness      │
                      │ Identify critical gaps  │
                      │ Suggest remediation     │
                      │ Make recommendation     │
                      │                         │
                      │ Ready? Review? Escalate?│
                      └──────────────┬──────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ENRICHED DOCUMENT OUTPUT                     │
│                                                                  │
│  KraftdDocument + Quality Metrics + Gaps + Recommendations     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stage Responsibilities

### Stage 1: Classifier
**Input:** Parsed document data
**Output:** Document type + confidence

**Does:**
- Runs regex patterns for document keywords
- Analyzes layout structure (if Azure available)
- Scores confidence (0-1)
- Suggests alternatives if ambiguous
- Flags for manual review if low confidence

**Example Output:**
```json
{
  "document_type": "RFQ",
  "confidence_score": 0.92,
  "method": "hybrid",
  "alternative_types": [
    {"type": "BOQ", "score": 0.35},
    {"type": "Quotation", "score": 0.08}
  ],
  "is_hybrid": false,
  "requires_manual_review": false
}
```

---

### Stage 2: Mapper
**Input:** Classification result + raw extracted data
**Output:** Partially filled KraftdDocument

**Does:**
- Extracts document metadata (number, date, parties)
- Normalizes party information
- Parses line items from tables
- Extracts commercial terms
- Handles null/missing defaults
- Validates field constraints
- Tracks what was mapped where

**Example Output:**
```json
{
  "kraftd_document": {
    "document_id": "doc-123",
    "metadata": {
      "document_type": "RFQ",
      "document_number": "RFQ-2024-001",
      "issue_date": "2024-01-15"
    },
    "parties": {
      "issuer": {
        "name": "ACME Corp",
        "legal_entity": "ACME LLC",
        "trn_vat_number": "VAT123456"
      }
    },
    "line_items": [
      {
        "line_number": 1,
        "description": "Steel Pipes",
        "quantity": 1000,
        "unit_of_measure": "kg",
        "unit_price": 50.0
      }
    ]
  },
  "field_mappings": {
    "issuer_name": {
      "source_field": "From: ACME Corp",
      "target_field": "parties.issuer.name",
      "confidence": 0.95,
      "method": "regex"
    }
  },
  "unmapped_fields": ["supplier_address"],
  "extraction_errors": []
}
```

---

### Stage 3: Inferencer
**Input:** Mapped document
**Output:** Enriched document with inferred fields

**Does:**
- Calculates totals: total_price = qty × unit_price × (1 - discount%)
- Infers missing parties from context
- Resolves currency (if mixed)
- Normalizes dates and payment terms
- Applies domain business rules
- Handles conflicting information
- Enriches from related fields

**Example:**
```
Input:  quantity=1000, unit_price=50, discount=0
Output: total_price=50000
Method: calculation
Confidence: 1.0

Input:  document_total=49,000, calculated_total=50,000
Output: Flag as conflict, variance=2%
Resolution: Use extracted (likely includes discount)
```

---

### Stage 4: Validator
**Input:** Inferred enriched document
**Output:** Quality assessment + recommendations

**Does:**
- Classifies fields as Critical/Important/Optional
- Scores completeness: critical (60%) + important (30%) + optional (10%)
- Identifies missing critical fields
- Calculates quality score from confidence
- Suggests remediation for each gap
- Makes recommendation: ready/review/escalate

**Example Output:**
```json
{
  "overall_completeness": 0.88,
  "quality_score": 0.85,
  "field_completeness": {
    "document_number": 1.0,
    "issue_date": 1.0,
    "issuer_name": 0.95,
    "line_items": 0.80,
    "submission_deadline": 0.0
  },
  "critical_gaps": [
    {
      "field": "submission_deadline",
      "reason": "Required for RFQ to solicit responses",
      "remediation": "Extract from document or ask issuer",
      "severity": "critical"
    }
  ],
  "recommendation": "review_needed",
  "ready_for_next_step": false
}
```

---

## Decision Flow

```
                    START
                     │
                     ▼
          Is file valid & readable?
          /                          \
        YES                           NO
         │                            │
         ▼                            ▼
      Parse file               ERROR: Invalid file
         │                      Return error
         │
         ▼
    [CLASSIFIER]
         │
         ▼
    confidence >= 0.6?
    /                    \
  YES                     NO
   │                       │
   ▼                       ▼
[MAPPER]            Manual review needed
   │                Return low confidence
   ▼
Any extraction
 errors?
 /         \
YES         NO
│           │
▼           ▼
Log        [INFERENCER]
 │           │
 └─► [INFERENCER]
         │
         ▼
    Any conflicts?
    /         \
  YES         NO
   │           │
   ▼           ▼
Flag       [VALIDATOR]
 │           │
 └─► [VALIDATOR]
         │
         ▼
     Ready?
    / | | \
   /  │ │  \
YES REV ESC ...
│   │   │
└───┴───┴─► Return result
            with recommendation
```

---

## Document Type Classification Rules

### RFQ (Request for Quotation)
**Keywords:** RFQ, Request for Quotation, Inquiry, Tender, Bidding
**Layout:** Table with Items, Qty, Delivery, Specifications
**Confidence Factors:**
- Contains "RFQ" keyword: +30%
- Has structured table: +20%
- Has submission instructions: +20%
- Has evaluation criteria: +10%
- Issuer info present: +10%
- Has submission deadline: +10%

**Minimum Confidence:** 60% for automated processing

---

### Quotation
**Keywords:** Quotation, Quote, Proposal, Offer, Estimate
**Layout:** Supplier response with total value and validity date
**Confidence Factors:**
- Contains "Quote/Quotation" keyword: +30%
- Supplier signature/stamp: +20%
- Validity date present: +15%
- Total quoted value: +15%
- Has supplier contact: +10%
- Has terms and conditions: +10%

---

### PO (Purchase Order)
**Keywords:** PO, Purchase Order, Order Confirmation
**Layout:** Formal order with clear PO number and dates
**Confidence Factors:**
- Contains "PO" keyword: +40%
- PO number matches pattern: +20%
- Supplier and buyer clear: +15%
- Line items with prices: +15%
- Delivery date present: +10%

---

### Invoice
**Keywords:** Invoice, Bill, Tax Invoice, Receipt
**Layout:** Formal invoice with invoice number and date
**Confidence Factors:**
- Contains "Invoice" keyword: +30%
- Invoice number present: +20%
- Invoice date present: +20%
- Supplier and buyer clear: +15%
- Total amount and tax: +15%

---

## Inference Rules Applied

| Rule | Input | Output | Confidence |
|------|-------|--------|------------|
| **Total Calculation** | qty, unit_price, discount | total = qty × price × (1 - disc) | 1.0 |
| **Document Total** | line item totals, tax | doc_total = Σ items + tax | 0.95 |
| **Currency** | mixed currencies | flag conflict | 0.5 |
| **Delivery Date** | deadline, order date | must be >= order_date | 0.9 |
| **Party Inference** | missing recipient | assume open market | 0.6 |
| **VAT Amount** | total, vat_rate | vat = total × rate | 0.95 |
| **Payment Terms** | raw text | normalize format | 0.8 |

---

## Completeness Scoring

### By Document Type

**RFQ - Critical Fields (60%)**
- document_number
- issue_date  
- issuer info
- line_items (≥1)
- submission_deadline
- evaluation_criteria

**RFQ - Important Fields (30%)**
- project_context
- incoterms
- payment_terms
- submission_method
- required_documents

**RFQ - Optional Fields (10%)**
- revision_number
- warranty_period
- insurance_requirements

**Scoring Formula:**
```
completeness = 
  (critical_present / total_critical) × 0.60 +
  (important_present / total_important) × 0.30 +
  (optional_present / total_optional) × 0.10
```

### Thresholds
- **≥ 0.95:** Ready to process (no review)
- **≥ 0.85:** Ready with caution (slight gaps)
- **≥ 0.70:** Review needed (user should verify)
- **< 0.70:** Escalate (manual review required)

---

## Integration Points

### 1. FastAPI Endpoint
```python
POST /extract-intelligent
├─ Accept file upload
├─ Run pipeline (4 stages)
├─ Return KraftdDocument + metrics
└─ Store in database
```

### 2. Agent Framework
```python
Agent Tools:
├─ _extract_intelligence_tool()
│  └─ Use pipeline internally
├─ _validate_document_tool()
│  └─ Use completeness validator
└─ _detect_risks_tool()
   └─ Use inference results
```

### 3. Existing Endpoints
```python
/docs/upload       → Stage 0 (Parse)
/extract           → Stages 1-4 (Full pipeline)
/validate          → Stage 4 (Completeness only)
/workflow          → Use pipeline internally
```

---

## Error Handling

| Error | Stage | Recovery | Outcome |
|-------|-------|----------|---------|
| Low confidence | Classifier | Ask for user hint | Manual review |
| Parse error | Mapper | Log, continue | Partial extraction |
| Conflict | Inferencer | Flag for review | Document marked |
| Missing critical | Validator | List gaps | Escalate |
| Azure timeout | Any | Fallback to local | Lower confidence |

---

## Configuration Options

```python
config = {
    # Classifier
    "classifier": {
        "use_azure": True,
        "confidence_threshold": 0.60,
        "fallback_to_hint": True
    },
    
    # Mapper
    "mapper": {
        "use_azure_first": True,
        "strict_validation": False,
        "infer_parties": True
    },
    
    # Inferencer
    "inferencer": {
        "apply_rules": True,
        "auto_resolve": False,
        "enrichment": True
    },
    
    # Validator
    "validator": {
        "strictness": "medium",  # low|medium|high
        "auto_flag": True
    }
}
```

---

## Sample Usage (Once Implemented)

```python
from pipeline import ExtractionPipeline

# Initialize
pipeline = ExtractionPipeline()

# Extract with callbacks
async def process_document(file_path):
    def on_progress(stage, progress, meta):
        print(f"{stage}: {progress:.0%}")
    
    result = await pipeline.extract(
        file_path,
        on_progress=on_progress
    )
    
    # Check result
    print(f"Type: {result.classification.document_type}")
    print(f"Confidence: {result.classification.confidence_score:.0%}")
    print(f"Completeness: {result.completeness.overall_completeness:.0%}")
    print(f"Recommendation: {result.completeness.recommendation}")
    
    # Access document
    doc = result.kraftd_document
    print(f"Document ID: {doc.document_id}")
    print(f"Issuer: {doc.parties.issuer.name}")
    print(f"Line Items: {len(doc.line_items)}")
    
    return result
```

---

## Success Metrics

Once implemented, measure:

✅ **Accuracy**
- Classification accuracy: target 90%+
- Field extraction accuracy: target 95%+
- Inference accuracy: target 85%+

✅ **Completeness**
- Average completeness score: 85%+
- Critical field capture: 98%+
- Manual review rate: <20%

✅ **Performance**
- Processing time: <2 seconds per document
- Azure success rate: 95%+
- Fallback handling: graceful, <1% error rate

✅ **Quality**
- Test coverage: >90%
- Edge case handling: robust
- Error messages: clear and actionable

---

## Next Steps

Phase 2 Implementation:
1. Create `/backend/pipeline/` module
2. Implement each stage in separate files
3. Create shared types and utilities
4. Wire into FastAPI and Agent
5. Add comprehensive tests
6. Document usage and extend with domain rules

**Estimated effort:** 18-26 development hours
**Recommended timeline:** 1-2 weeks with testing

---

**Questions? See detailed design in PIPELINE_ARCHITECTURE_DESIGN.md**
