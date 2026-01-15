# Orchestrated Extraction Pipeline Architecture

## Overview

This document defines the technical architecture for the **four-stage orchestrated pipeline** that will power intelligent document extraction in Kraftd. The pipeline decomposes extraction into reusable, testable stages with clear contracts and error handling.

---

## Stage Architecture

### Stage 1: DocumentClassifier
**Purpose:** Identify document type and characteristics

```
Input: 
  - file_path: str
  - parsed_data: Dict (from processor)
  - azure_result: Optional[AnalyzeResult]

Output:
  - ClassificationResult:
    - document_type: DocumentType (RFQ, BOQ, Quotation, PO, Contract, Invoice)
    - confidence_score: float (0-1)
    - classification_method: 'regex' | 'layout' | 'hybrid' | 'manual'
    - alternative_types: List[Tuple[DocumentType, float]]  # ranked alternatives
    - error: Optional[ClassificationError]
    
Responsibilities:
  - Detect primary document type
  - Provide confidence scores
  - Identify alternative types (for ambiguous cases)
  - Handle multi-modal inputs (text, layout, user hint)
  - Fallback if classification uncertain
```

**Implementation Details:**
```python
class ClassificationResult(BaseModel):
    document_type: DocumentType
    confidence_score: float  # 0-1
    classification_method: str
    alternative_types: List[Tuple[DocumentType, float]]
    metadata: Dict[str, Any]  # layout features, keyword counts, etc.
    error: Optional[str]
    is_hybrid: bool  # e.g., RFQ + BOQ combined
    requires_manual_review: bool  # confidence < 0.7

class DocumentClassifier:
    def __init__(self):
        self.patterns: Dict[DocumentType, List[Pattern]]
        self.confidence_weights: Dict[str, float]
    
    def classify(
        self, 
        parsed_data: Dict[str, Any],
        azure_result: Optional[AnalyzeResult] = None,
        user_hint: Optional[DocumentType] = None
    ) -> ClassificationResult:
        """Classify document with confidence scoring."""
        
    def _apply_regex_rules(self, text: str) -> ClassificationResult:
        """Pattern-based classification."""
        
    def _apply_layout_rules(self, azure_result: AnalyzeResult) -> ClassificationResult:
        """Azure Document Intelligence layout analysis."""
        
    def _fuse_results(self, regex_result, layout_result) -> ClassificationResult:
        """Combine multiple classification approaches."""
```

**Classification Rules:**
```
RFQ:
  - Keywords: "RFQ", "Request for Quotation", "Inquiry", "Tender"
  - Layout: Structured table with "Item", "Qty", "Delivery", "Specifications"
  - Tables: Present, well-structured
  - Parties: Issuer clear, Recipients unclear (open call)
  - Confidence factors:
    * Keywords found: +0.3
    * Table structure detected: +0.2
    * Submission instructions: +0.2
    * Evaluation criteria: +0.1
    * Issuer clearly identified: +0.1

BOQ (Bill of Quantities):
  - Keywords: "BOQ", "Bill of Quantities", "Schedule"
  - Layout: Tabular with quantities and unit prices
  - Tables: Yes, line-item focused
  - Parties: Usually internal, issuer only
  - Confidence factors: Similar to RFQ but no submission instructions

Quotation:
  - Keywords: "Quotation", "Quote", "Proposal", "Offer"
  - Layout: Supplier response format
  - Parties: Supplier clearly named, buyer generic
  - Dates: Validity date usually present
  - Confidence factors:
    * Keywords: +0.3
    * Supplier signature block: +0.2
    * Validity date: +0.15
    * Total quoted value: +0.15

PO (Purchase Order):
  - Keywords: "PO", "Purchase Order", "Order"
  - Layout: Formal document with PO number
  - Parties: Clear buyer and supplier
  - Data: Line items, delivery dates, payment terms
  - Confidence factors:
    * "PO" keyword: +0.4
    * PO number pattern: +0.2
    * Linked quotation reference: +0.1
    * Tax/VAT mention: +0.1

Contract:
  - Keywords: "Agreement", "Contract", "Terms & Conditions"
  - Layout: Narrative with clauses and sections
  - Tables: May have schedules
  - Parties: Clearly defined
  - Confidence factors:
    * Contract type keyword: +0.3
    * Signature blocks: +0.2
    * Legal clause keywords: +0.2
    * Effective date: +0.1

Invoice:
  - Keywords: "Invoice", "Bill", "Tax Invoice"
  - Layout: Formal invoice format
  - Parties: Supplier issues to buyer
  - Data: Line items, amounts, payment terms
  - Confidence factors:
    * Invoice number: +0.3
    * Invoice date: +0.2
    * Total amount and tax: +0.2
    * Payment terms: +0.1
```

---

### Stage 2: DocumentMapper
**Purpose:** Extract and normalize fields to KraftdDocument schema

```
Input:
  - classification_result: ClassificationResult
  - parsed_data: Dict
  - azure_result: Optional[AnalyzeResult]

Output:
  - MappingResult:
    - kraftd_document: KraftdDocument (partially filled)
    - field_mappings: Dict[str, FieldMapping]  # what mapped where
    - unmapped_fields: List[str]  # raw data not mapped
    - extraction_errors: List[ExtractionError]
    - warnings: List[str]

Responsibilities:
  - Extract metadata (document number, date, parties)
  - Normalize parties (issuer, recipient, others)
  - Extract line items and normalize to standard format
  - Extract commercial terms (currency, payment, delivery)
  - Handle null/missing field defaults
  - Validate field constraints
```

**Implementation Details:**
```python
class FieldMapping(BaseModel):
    source_field: str
    target_field: str
    mapped_value: Any
    confidence: float
    method: str  # 'azure', 'regex', 'table_parse', 'direct'
    
class MappingResult(BaseModel):
    kraftd_document: KraftdDocument
    field_mappings: Dict[str, FieldMapping]
    unmapped_fields: List[str]
    extraction_errors: List[str]
    warnings: List[str]
    completeness_estimate: float  # 0-1, will be refined later

class DocumentMapper:
    def __init__(self, document_type: DocumentType):
        self.document_type = document_type
        self.field_schema: Dict = self._get_field_schema(document_type)
    
    def map(
        self,
        parsed_data: Dict[str, Any],
        azure_result: Optional[AnalyzeResult] = None,
        classification_metadata: Optional[Dict] = None
    ) -> MappingResult:
        """Map extracted data to KraftdDocument schema."""
    
    def _extract_metadata(self) -> DocumentMetadata:
        """Extract document ID, number, date, revision."""
        
    def _extract_parties(self) -> Dict[str, Party]:
        """Extract and normalize parties."""
        
    def _extract_line_items(self) -> List[LineItem]:
        """Parse and normalize line items from tables."""
        
    def _normalize_party(self, raw_data: Dict) -> Party:
        """Normalize party information."""
        
    def _normalize_line_item(self, row: List[str], line_num: int) -> LineItem:
        """Normalize a single line item."""
```

**Mapping Strategy:**
```
1. Try Azure Document Intelligence first (highest confidence)
   - For structured documents with clear fields
   - Use form field extraction for prebuilt models

2. Fall back to regex patterns
   - Date patterns, phone, email, amounts
   - Standard field keywords

3. Extract from tables
   - Line items, deliveries, payment milestones
   - Structured tabular data

4. User-provided hints
   - If classification has metadata (e.g., "contains invoice")
   - Use this to guide field extraction

5. Cross-field validation
   - Check totals = sum of items
   - Validate date sequences
   - Check party consistency
```

---

### Stage 3: DocumentInferencer
**Purpose:** Intelligently derive missing/implicit fields and apply business rules

```
Input:
  - mapping_result: MappingResult
  - document_type: DocumentType

Output:
  - InferenceResult:
    - kraftd_document: KraftdDocument (enriched)
    - inferred_fields: Dict[str, InferredField]
    - applied_rules: List[str]
    - conflicts: List[Conflict]
    
Responsibilities:
  - Infer missing fields from context
  - Calculate derived fields (totals, discounts)
  - Apply business rules and constraints
  - Resolve ambiguities
  - Handle field dependencies
  - Enrich with external data (if available)
```

**Implementation Details:**
```python
class InferredField(BaseModel):
    field_name: str
    inferred_value: Any
    method: str  # 'calculation', 'rule', 'context', 'default'
    confidence: float  # 0-1
    explanation: str
    
class Conflict(BaseModel):
    field: str
    extracted_value: Any
    inferred_value: Any
    resolution: str  # 'extracted', 'inferred', 'manual_review'

class DocumentInferencer:
    def infer(self, mapping_result: MappingResult) -> InferenceResult:
        """Apply inference rules and enrich document."""
    
    def _infer_missing_parties(self, doc: KraftdDocument) -> Dict[str, Party]:
        """Infer recipient from context if missing."""
        
    def _infer_totals(self, line_items: List[LineItem]) -> Dict[str, float]:
        """Calculate totals from line items."""
        
    def _resolve_currency(self, doc: KraftdDocument) -> Optional[str]:
        """Infer currency if mixed or missing."""
        
    def _infer_dates(self, doc: KraftdDocument) -> Dict[str, date]:
        """Infer missing dates from context."""
        
    def _apply_business_rules(self, doc: KraftdDocument) -> List[str]:
        """Apply domain-specific rules."""
```

**Inference Rules:**

```
1. Party Inference
   - If recipient missing in RFQ: Assume open market call
   - If supplier not identified: Flag for manual review
   - Resolve party name aliases (SAP codes, abbreviations)
   
2. Total Calculation
   - total_price = quantity × unit_price × (1 - discount%)
   - document_total = sum(line item totals) + tax
   - Check: (quoted total - calculated total) < threshold
   
3. Currency Resolution
   - If mixed currencies: Flag as risk
   - If missing: Infer from issuer country/context
   - If ambiguous: Suggest most common in region
   
4. Date Inference
   - If issue_date missing: Use document created date
   - If validity_date missing: RFQ default 30 days, Quote default 14 days
   - If delivery_date missing: Use submission_deadline or validate if in past
   
5. Payment Terms Normalization
   - "30 net" → "30 days from invoice"
   - "2/10 net 30" → advanced discount handling
   - "On delivery" → payment_type = "on_completion"
   
6. Delivery Term Inference
   - If location missing: Use project location
   - If incoterms missing: Default based on document type
   - Validate delivery_date >= order_date
   
7. Line Item Reconciliation
   - Check all items have required fields
   - Validate unit_of_measure against item type
   - Infer uom if missing (e.g., kg for "raw material")
   - Cross-check qty: if range given, use midpoint
   
8. Tax/VAT Inference
   - If vat_rate in metadata but not document: Apply document-level default
   - Calculate vat_amount from total if rate given
   - Validate vat_amount = total × vat_rate ± threshold
   
9. Supplier Details Enrichment
   - Attempt to enrich supplier from internal database
   - Match by company name, TRN, email domain
   - Flag if supplier not in system (new vendor)
   
10. Cross-Field Validation
    - If quotation references RFQ: Validate all items present
    - If PO references quotation: Check prices match ±threshold
    - If invoice references PO: Validate items and amounts align
```

**Conflict Resolution Strategy:**
```
HIGH CONFIDENCE extracted > INFERRED
  - If extracted value has confidence > 0.9: use extracted
  - If inferred value more logically consistent: negotiate

CALCULATED vs EXTRACTED
  - If calculated total ≠ extracted total: check both
  - If variance < 1%: use extracted (likely rounding)
  - If variance > 1%: flag as conflict, suggest review

CONTRADICTORY INFERENCES
  - If two rules suggest different values: apply priority order
  - Log conflict with explanation
  - Mark document for manual review if critical field
```

---

### Stage 4: CompletenessValidator
**Purpose:** Assess extraction completeness and quality

```
Input:
  - inference_result: InferenceResult
  - document_type: DocumentType

Output:
  - CompletenessResult:
    - overall_completeness: float (0-1)
    - field_completeness: Dict[str, float]
    - critical_gaps: List[CriticalGap]
    - remediation_suggestions: List[str]
    - quality_score: float (0-1)
    - extraction_warnings: List[str]
    - recommendation: 'ready' | 'review_needed' | 'escalate'

Responsibilities:
  - Classify fields as critical, important, optional
  - Calculate completeness % for each category
  - Identify missing critical fields
  - Suggest remediation actions
  - Flag quality issues
  - Provide final recommendation
```

**Implementation Details:**
```python
class CriticalGap(BaseModel):
    field: str
    reason: str
    remediation: str
    severity: 'critical' | 'high' | 'medium' | 'low'

class FieldCompleteness(BaseModel):
    present: bool
    confidence: float  # 0-1
    inferred: bool
    quality_score: float  # 0-1

class CompletenessResult(BaseModel):
    overall_completeness: float
    field_completeness: Dict[str, FieldCompleteness]
    critical_gaps: List[CriticalGap]
    remediation_suggestions: List[str]
    quality_score: float
    extraction_warnings: List[str]
    ready_for_next_step: bool
    recommendation: str  # 'ready', 'review_needed', 'escalate'

class CompletenessValidator:
    def validate(self, inference_result: InferenceResult) -> CompletenessResult:
        """Assess completeness and quality of extracted document."""
        
    def _get_field_criticality(self, document_type: DocumentType) -> Dict[str, str]:
        """Define which fields are critical for each doc type."""
        
    def _calculate_completeness(self) -> float:
        """Calculate overall completeness score."""
        
    def _identify_gaps(self) -> List[CriticalGap]:
        """Identify missing critical fields."""
        
    def _suggest_remediation(self, gaps: List[CriticalGap]) -> List[str]:
        """Suggest how to remediate gaps."""
        
    def _calculate_quality_score(self) -> float:
        """Score extraction quality (confidence, consistency, etc.)."""
```

**Field Criticality Matrix:**

```
RFQ:
  CRITICAL:
    - document_number
    - issue_date
    - issuer (name, contact)
    - line_items (at least one)
    - submission_deadline
    - evaluation_criteria or scoring_method
  
  IMPORTANT:
    - project_context
    - incoterms
    - payment_terms
    - required_documents list
    - submission_method
    - submission_address
  
  OPTIONAL:
    - revision_number
    - warranty_period
    - performance_guarantee
    - insurance_requirements

Quotation:
  CRITICAL:
    - quotation_number
    - quotation_date
    - supplier_name
    - line_items
    - total_quoted_value
    - validity_date
  
  IMPORTANT:
    - supplier_contact
    - delivery_terms
    - payment_terms
    - warranty_terms
    - linked_rfq_number (if responding to RFQ)
  
  OPTIONAL:
    - supplier_legal_entity
    - after_sales_support
    - clarifications
    - deviations

PO:
  CRITICAL:
    - po_number
    - po_date
    - supplier_name
    - buyer_name
    - line_items
    - po_value
    - delivery_date(s)
  
  IMPORTANT:
    - payment_terms
    - incoterms
    - linked_quotation_number
    - linked_rfq_number
    - contact persons
    - delivery_location
  
  OPTIONAL:
    - split_deliveries
    - change_order_procedure
    - performance_guarantee

Invoice:
  CRITICAL:
    - invoice_number
    - invoice_date
    - supplier_name
    - buyer_name
    - line_items
    - invoice_total
    - payment_terms
    - due_date
  
  IMPORTANT:
    - supplier_tax_number
    - linked_po_number
    - tax_amount
    - payment_reference
    - bank_details
  
  OPTIONAL:
    - project_reference
    - delivery_note_number
    - warranty_information

Contract:
  CRITICAL:
    - contract_number
    - parties (both)
    - scope_summary
    - effective_date
    - duration or end_date
    - total_contract_value
    - payment_structure
  
  IMPORTANT:
    - deliverables list
    - termination_conditions
    - dispute_resolution
    - liability_cap
    - insurance_requirements
  
  OPTIONAL:
    - force_majeure clause
    - indemnity_clause
    - change_order_procedure
```

**Completeness Scoring:**
```
overall_completeness = 
  (critical_fields_present / total_critical) * 0.6 +
  (important_fields_present / total_important) * 0.3 +
  (optional_fields_present / total_optional) * 0.1

quality_score =
  (avg_field_confidence) * 0.4 +
  (consistency_score) * 0.3 +
  (validation_passed_ratio) * 0.2 +
  (no_warnings_bonus) * 0.1

Thresholds:
  >= 0.95: Ready (no review needed)
  >= 0.85: Ready with caution (document slightly incomplete)
  >= 0.70: Review needed (user should verify)
  < 0.70: Escalate (manual review required)
```

---

## Stage Orchestration

### ExtractionPipeline Orchestrator

**Purpose:** Chain stages, manage state, handle errors, provide callbacks

```python
class ExtractionPipeline:
    """Orchestrates document extraction through all stages."""
    
    def __init__(
        self,
        classifier: DocumentClassifier = None,
        mappers: Dict[DocumentType, DocumentMapper] = None,
        inferencer: DocumentInferencer = None,
        validator: CompletenessValidator = None,
        error_handler: ErrorHandler = None
    ):
        """Initialize pipeline with optional dependency injection."""
        self.classifier = classifier or DocumentClassifier()
        self.mappers = mappers or self._default_mappers()
        self.inferencer = inferencer or DocumentInferencer()
        self.validator = validator or CompletenessValidator()
        self.error_handler = error_handler or ErrorHandler()
        
    async def extract(
        self,
        file_path: str,
        parsed_data: Optional[Dict] = None,
        azure_result: Optional[AnalyzeResult] = None,
        user_hint: Optional[DocumentType] = None,
        on_progress: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ) -> ExtractionResult:
        """
        Execute full pipeline with error handling and progress callbacks.
        
        Args:
            file_path: Path to document
            parsed_data: Pre-parsed data (optional, will auto-parse if missing)
            azure_result: Azure Document Intelligence result (optional)
            user_hint: Suggested document type (optional)
            on_progress: Callback(stage, progress, metadata)
            on_error: Callback(stage, error, recovery_action)
        
        Returns:
            ExtractionResult with all stages' results
        """
        result = ExtractionResult()
        
        try:
            # Stage 1: Classification
            on_progress and on_progress("classification", 0.1)
            
            # Parse file if needed
            if not parsed_data:
                parsed_data = await self._parse_file(file_path)
            
            classification_result = self.classifier.classify(
                parsed_data, azure_result, user_hint
            )
            result.classification = classification_result
            
            if classification_result.confidence_score < 0.6:
                raise ClassificationError(f"Low confidence ({classification_result.confidence_score:.2f}) - {classification_result.error}")
            
            on_progress and on_progress("classification", 0.25)
            
            # Stage 2: Mapping
            on_progress and on_progress("mapping", 0.25)
            
            mapper = self.mappers.get(
                classification_result.document_type,
                DocumentMapper(classification_result.document_type)
            )
            mapping_result = mapper.map(
                parsed_data,
                azure_result,
                classification_result.metadata
            )
            result.mapping = mapping_result
            
            if mapping_result.extraction_errors:
                on_error and on_error(
                    "mapping", 
                    mapping_result.extraction_errors, 
                    "continuing_with_partial_extraction"
                )
            
            on_progress and on_progress("mapping", 0.50)
            
            # Stage 3: Inference
            on_progress and on_progress("inference", 0.50)
            
            inference_result = self.inferencer.infer(mapping_result)
            result.inference = inference_result
            
            if inference_result.conflicts:
                on_error and on_error(
                    "inference",
                    inference_result.conflicts,
                    "flagged_for_review"
                )
            
            on_progress and on_progress("inference", 0.75)
            
            # Stage 4: Completeness
            on_progress and on_progress("completeness", 0.75)
            
            completeness_result = self.validator.validate(inference_result)
            result.completeness = completeness_result
            result.kraftd_document = inference_result.kraftd_document
            
            on_progress and on_progress("completeness", 1.0)
            
            result.status = "success"
            return result
            
        except Exception as e:
            result.status = "error"
            result.error = str(e)
            recovery = self.error_handler.handle(e)
            on_error and on_error("pipeline", e, recovery)
            raise

class ExtractionResult(BaseModel):
    status: str  # 'success', 'partial', 'error'
    kraftd_document: Optional[KraftdDocument] = None
    classification: Optional[ClassificationResult] = None
    mapping: Optional[MappingResult] = None
    inference: Optional[InferenceResult] = None
    completeness: Optional[CompletenessResult] = None
    error: Optional[str] = None
    execution_time_ms: float = 0
```

### Error Handling Strategy

```python
class PipelineError(Exception):
    """Base pipeline error."""
    def __init__(self, stage: str, message: str, recoverable: bool = False):
        self.stage = stage
        self.message = message
        self.recoverable = recoverable

class ClassificationError(PipelineError):
    """Classification stage failed."""
    pass

class MappingError(PipelineError):
    """Mapping stage failed."""
    pass

class InferenceError(PipelineError):
    """Inference stage failed."""
    pass

class ValidationError(PipelineError):
    """Validation failed."""
    pass

class ErrorHandler:
    """Handle pipeline errors with recovery strategies."""
    
    def handle(self, error: Exception) -> str:
        """Return recovery action string."""
        if isinstance(error, ClassificationError):
            if error.recoverable:
                return "retry_with_user_hint"
            return "escalate_to_manual_review"
        elif isinstance(error, MappingError):
            return "continue_with_partial_data"
        elif isinstance(error, InferenceError):
            return "skip_inference_use_extracted"
        elif isinstance(error, ValidationError):
            return "flag_for_review_include_warnings"
        else:
            return "escalate_to_manual_review"
```

---

## Data Flow Diagram

```
┌─ File Input ─────────────────────────────────────────┐
│                                                      │
│  file_path                                           │
│  parsed_data (optional)                              │
│  azure_result (optional)                             │
│  user_hint (optional)                                │
└─────────────────────────────────┬────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  DocumentClassifier      │
                    │─────────────────────────│
                    │ classify()               │
                    │ Apply regex rules       │
                    │ Apply layout rules      │
                    │ Fuse results            │
                    │ Score confidence        │
                    └──────────────┬───────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  ClassificationResult    │
                    │─────────────────────────│
                    │ document_type            │
                    │ confidence_score         │
                    │ alternative_types       │
                    │ classification_method   │
                    └──────────────┬───────────┘
                                  │
                                  ▼ (decision point)
                        confidence < 0.6?
                                  │
                ┌─────────────────┴─────────────────┐
                │ NO                               YES
                │                                  │
                ▼                          ┌────────▼────────┐
    ┌──────────────────────────┐          │ Manual Review   │
    │  DocumentMapper          │          │ or Escalation   │
    │─────────────────────────│          └─────────────────┘
    │ map()                    │
    │ Extract metadata         │
    │ Normalize parties        │
    │ Extract line items       │
    │ Normalize commercial     │
    │ terms                    │
    └──────────────┬───────────┘
                   │
                   ▼
    ┌──────────────────────────┐
    │  MappingResult           │
    │─────────────────────────│
    │ kraftd_document          │
    │ field_mappings           │
    │ unmapped_fields          │
    │ extraction_errors        │
    │ warnings                 │
    └──────────────┬───────────┘
                   │
                   ▼
    ┌──────────────────────────┐
    │  DocumentInferencer      │
    │─────────────────────────│
    │ infer()                  │
    │ Infer missing fields     │
    │ Calculate derived fields │
    │ Apply business rules     │
    │ Resolve ambiguities      │
    │ Enrich from context      │
    └──────────────┬───────────┘
                   │
                   ▼
    ┌──────────────────────────┐
    │  InferenceResult         │
    │─────────────────────────│
    │ kraftd_document          │
    │ inferred_fields          │
    │ applied_rules            │
    │ conflicts                │
    └──────────────┬───────────┘
                   │
                   ▼
    ┌──────────────────────────┐
    │ CompletenessValidator    │
    │─────────────────────────│
    │ validate()               │
    │ Score completeness       │
    │ Identify gaps            │
    │ Suggest remediation      │
    │ Calculate quality score  │
    │ Make recommendation      │
    └──────────────┬───────────┘
                   │
                   ▼
    ┌──────────────────────────┐
    │  CompletenessResult      │
    │─────────────────────────│
    │ overall_completeness     │
    │ field_completeness       │
    │ critical_gaps            │
    │ remediation_suggestions  │
    │ quality_score            │
    │ recommendation           │
    └──────────────┬───────────┘
                   │
                   ▼
    ┌──────────────────────────┐
    │  ExtractionResult        │
    │─────────────────────────│
    │ status                   │
    │ kraftd_document          │
    │ classification           │
    │ mapping                  │
    │ inference                │
    │ completeness             │
    │ error (if any)           │
    └──────────────────────────┘
```

---

## Integration Points

### FastAPI Integration
```python
# In main.py, add pipeline endpoint

from pipeline import ExtractionPipeline

pipeline = ExtractionPipeline()

@app.post("/extract-intelligent")
async def extract_with_pipeline(file: UploadFile = File(...)):
    """Extract using full orchestrated pipeline."""
    
    # Save file
    file_path = save_upload(file)
    
    # Parse based on type
    parsed_data = await auto_parse(file_path)
    
    # Run pipeline
    def on_progress(stage, progress, metadata):
        print(f"{stage}: {progress:.0%}")
    
    def on_error(stage, error, recovery):
        print(f"{stage} error: {error}, recovery: {recovery}")
    
    try:
        result = await pipeline.extract(
            file_path,
            parsed_data=parsed_data,
            on_progress=on_progress,
            on_error=on_error
        )
        
        # Store in database
        documents_db[result.kraftd_document.document_id] = result
        
        return {
            "document_id": result.kraftd_document.document_id,
            "document_type": result.classification.document_type,
            "completeness": result.completeness.overall_completeness,
            "ready_for_next_step": result.completeness.ready_for_next_step,
            "recommendation": result.completeness.recommendation,
            "critical_gaps": result.completeness.critical_gaps,
            "execution_time_ms": result.execution_time_ms
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Agent Framework Integration
```python
# In kraft_agent.py, use pipeline in tools

class KraftdAIAgent:
    def __init__(self):
        self.pipeline = ExtractionPipeline()
    
    async def _extract_intelligence_tool(self, document_id: str) -> str:
        """Extract intelligence using pipeline."""
        doc_record = documents_db[document_id]
        file_path = doc_record["file_path"]
        parsed_data = doc_record.get("parsed_data")
        
        result = await self.pipeline.extract(file_path, parsed_data)
        
        # Update document with extraction result
        documents_db[document_id].update({
            "extraction_result": result,
            "document": result.kraftd_document.dict()
        })
        
        return f"""
        Extraction complete:
        - Type: {result.classification.document_type}
        - Completeness: {result.completeness.overall_completeness:.0%}
        - Status: {result.completeness.recommendation}
        - Gaps: {len(result.completeness.critical_gaps)}
        """
```

---

## Configuration & Extensibility

### Stage Configuration
```python
pipeline_config = {
    "classifier": {
        "use_azure": True,
        "confidence_threshold": 0.6,
        "fallback_to_user_hint": True
    },
    "mapper": {
        "use_azure_first": True,
        "strict_validation": False,
        "infer_missing_parties": True
    },
    "inferencer": {
        "apply_business_rules": True,
        "resolve_conflicts_auto": False,  # manual review if conflicts
        "enrichment_enabled": True
    },
    "validator": {
        "strictness": "medium",  # low, medium, high
        "auto_flag_for_review": True
    }
}

pipeline = ExtractionPipeline(**pipeline_config)
```

### Custom Stage Implementation
```python
class CustomClassifier(DocumentClassifier):
    """Custom classifier using domain-specific rules."""
    
    def classify(self, parsed_data, azure_result, user_hint):
        # Custom implementation
        pass

class CustomInferencer(DocumentInferencer):
    """Custom inferencer for specific business logic."""
    
    def infer(self, mapping_result):
        # Custom implementation
        pass

# Use custom stages
pipeline = ExtractionPipeline(
    classifier=CustomClassifier(),
    inferencer=CustomInferencer()
)
```

---

## Summary

This architecture provides:

✅ **Modularity** - Each stage is independent and testable
✅ **Reusability** - Stages can be used separately or recombined
✅ **Error Handling** - Clear error recovery strategies
✅ **Extensibility** - Custom stages can be injected
✅ **Observability** - Progress and error callbacks
✅ **Quality Assessment** - Built-in completeness validation
✅ **Configurability** - Flexible configuration options
✅ **Backward Compatibility** - Wraps existing extractors

Next phase: Implementation of each stage.
