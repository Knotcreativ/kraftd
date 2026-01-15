# Phase 2 Implementation Roadmap

## Overview
This document provides a step-by-step implementation plan for building the orchestrated extraction pipeline based on the completed design.

---

## Implementation Phases

### Phase 2A: Foundation (4-5 hours)
**Objective:** Build base infrastructure and utilities

#### Tasks
1. **Create pipeline module structure**
   - `backend/pipeline/__init__.py`
   - `backend/pipeline/types.py` (shared types)
   - `backend/pipeline/errors.py` (custom exceptions)
   - `backend/pipeline/utils.py` (helpers)

2. **Define shared types**
   ```python
   - ClassificationResult
   - MappingResult
   - InferenceResult
   - CompletenessResult
   - ExtractionResult
   - PipelineConfig
   ```

3. **Implement base classes**
   ```python
   - BasePipelineStage
   - ErrorHandler
   - ProgressTracker
   ```

4. **Setup test infrastructure**
   ```python
   - `backend/tests/test_pipeline/`
   - Test fixtures and mocks
   - Sample documents for testing
   ```

**Deliverables:**
- Core module structure
- Type definitions
- Utility functions
- Test framework

---

### Phase 2B: Classifier (2-3 hours)
**Objective:** Implement Stage 1 - Document Type Detection

#### File: `backend/pipeline/classifier.py`

**Components:**
```python
class DocumentClassifier:
    def __init__(self, config: ClassifierConfig)
    def classify(parsed_data, azure_result, user_hint) → ClassificationResult
    
    # Private methods
    def _apply_regex_rules(text) → Dict[DocumentType, float]
    def _apply_layout_rules(azure_result) → Dict[DocumentType, float]
    def _fuse_results(regex_scores, layout_scores) → ClassificationResult
    def _get_classification_patterns() → Dict[DocumentType, List[Pattern]]
```

**Implementation Steps:**
1. Define regex patterns for each document type
2. Implement regex-based classification
3. Implement layout-based classification (using Azure)
4. Implement result fusion/scoring
5. Add fallback logic for low confidence
6. Unit tests for each classification rule

**Test Cases:**
- ✓ RFQ with clear keywords
- ✓ RFQ without keywords (layout-based)
- ✓ Ambiguous documents (hybrid scoring)
- ✓ Low confidence (< 60%)
- ✓ With user hint (improve confidence)

**Expected Output:**
```json
{
  "document_type": "RFQ",
  "confidence_score": 0.92,
  "classification_method": "hybrid",
  "alternative_types": [
    ["BOQ", 0.35]
  ],
  "requires_manual_review": false
}
```

---

### Phase 2C: Mapper (3-4 hours)
**Objective:** Implement Stage 2 - Field Extraction & Normalization

#### File: `backend/pipeline/mapper.py`

**Components:**
```python
class DocumentMapper:
    def __init__(document_type: DocumentType, config: MapperConfig)
    def map(parsed_data, azure_result, classification_metadata) → MappingResult
    
    # Extraction methods
    def _extract_metadata() → DocumentMetadata
    def _extract_parties() → Dict[str, Party]
    def _extract_line_items() → List[LineItem]
    def _extract_commercial_terms() → CommercialTerms
    
    # Normalization methods
    def _normalize_party(raw_party) → Party
    def _normalize_line_item(row, line_number) → LineItem
    def _normalize_currency(text) → Optional[str]
    def _normalize_date(text) → Optional[date]
    
    # Validation methods
    def _validate_constraints() → List[ValidationError]
    def _cross_validate_fields() → List[str]
```

**Implementation Steps:**
1. Implement metadata extraction (document number, date, parties)
2. Implement party extraction and normalization
3. Implement line item parsing from tables
4. Implement commercial terms extraction
5. Add field validation
6. Cross-field validation
7. Unit tests for each extraction method

**Test Cases:**
- ✓ Metadata extraction
- ✓ Party name variations (abbreviations, legal entities)
- ✓ Line items with various formats
- ✓ Mixed currencies
- ✓ Date format variations
- ✓ Missing fields (defaults)
- ✓ Validation errors (constraints)

**Expected Output:**
```python
MappingResult(
    kraftd_document=KraftdDocument(...),
    field_mappings={
        "issuer_name": FieldMapping(
            source_field="From: ACME Corp",
            target_field="parties.issuer.name",
            mapped_value="ACME Corp",
            confidence=0.95,
            method="regex"
        )
    },
    unmapped_fields=["supplier_address"],
    extraction_errors=[],
    warnings=["Issuer address not found"]
)
```

---

### Phase 2D: Inferencer (3-4 hours)
**Objective:** Implement Stage 3 - Intelligent Field Inference

#### File: `backend/pipeline/inferencer.py`

**Components:**
```python
class DocumentInferencer:
    def infer(mapping_result: MappingResult) → InferenceResult
    
    # Inference methods
    def _infer_missing_parties() → Dict[str, Party]
    def _infer_totals() → Dict[str, float]
    def _resolve_currency() → Optional[str]
    def _infer_dates() → Dict[str, date]
    def _apply_business_rules() → Dict[str, Any]
    
    # Conflict resolution
    def _detect_conflicts() → List[Conflict]
    def _resolve_conflict(field, extracted, inferred) → Resolution
```

**Implementation Steps:**
1. Implement total calculation inference
2. Implement party inference (from context)
3. Implement currency resolution
4. Implement date inference and validation
5. Implement business rules (10+ rules)
6. Implement conflict detection
7. Implement conflict resolution strategy
8. Unit tests for each rule

**Business Rules to Implement:**
```
1. total_price = qty × unit_price × (1 - discount%)
2. document_total = Σ line_items + tax
3. If vat_rate and total exist: calculate vat_amount
4. If delivery_date < order_date: flag as error
5. If recipient missing (RFQ): assume open market
6. If currency mixed: flag as conflict
7. Normalize payment terms (e.g., "30 net" → "30 days from invoice")
8. Infer delivery location from context
9. Validate party consistency across document
10. Cross-reference line items (totals must match)
```

**Test Cases:**
- ✓ Calculate total from line items
- ✓ Party inference from context
- ✓ Currency resolution
- ✓ Date validation and inference
- ✓ Payment term normalization
- ✓ Conflict detection
- ✓ Conflict resolution

**Expected Output:**
```python
InferenceResult(
    kraftd_document=KraftdDocument(...),  # enriched
    inferred_fields={
        "total_value": InferredField(
            field_name="total_value",
            inferred_value=50000.0,
            method="calculation",
            confidence=1.0,
            explanation="Sum of all line items"
        )
    },
    applied_rules=["total_calculation", "date_validation"],
    conflicts=[]
)
```

---

### Phase 2E: Completeness Validator (2-3 hours)
**Objective:** Implement Stage 4 - Quality Assessment

#### File: `backend/pipeline/validator.py`

**Components:**
```python
class CompletenessValidator:
    def validate(inference_result: InferenceResult) → CompletenessResult
    
    # Assessment methods
    def _classify_field_importance() → Dict[str, str]
    def _calculate_completeness() → float
    def _identify_critical_gaps() → List[CriticalGap]
    def _calculate_quality_score() → float
    def _suggest_remediation(gaps) → List[str]
    def _make_recommendation() → str
```

**Implementation Steps:**
1. Define field criticality for each document type
2. Implement completeness scoring
3. Implement gap identification
4. Implement quality scoring
5. Implement remediation suggestions
6. Implement recommendation logic
7. Unit tests for scoring and recommendations

**Field Criticality Data:**
```python
FIELD_CRITICALITY = {
    DocumentType.RFQ: {
        "critical": ["document_number", "issue_date", "issuer", "line_items", "submission_deadline"],
        "important": ["project_context", "incoterms", "payment_terms"],
        "optional": ["revision_number", "warranty_period"]
    },
    # ... other document types
}
```

**Test Cases:**
- ✓ Completeness scoring (critical/important/optional)
- ✓ Gap identification
- ✓ Quality score calculation
- ✓ Remediation suggestions
- ✓ Recommendation logic (ready/review/escalate)

**Expected Output:**
```python
CompletenessResult(
    overall_completeness=0.88,
    quality_score=0.85,
    field_completeness={
        "document_number": FieldCompleteness(present=True, confidence=1.0),
        "submission_deadline": FieldCompleteness(present=False, confidence=0.0)
    },
    critical_gaps=[
        CriticalGap(
            field="submission_deadline",
            reason="Required for RFQ",
            remediation="Extract from document or contact issuer",
            severity="critical"
        )
    ],
    recommendation="review_needed"
)
```

---

### Phase 2F: Pipeline Orchestrator (2-3 hours)
**Objective:** Implement Stage Orchestration & Integration

#### File: `backend/pipeline/orchestrator.py`

**Components:**
```python
class ExtractionPipeline:
    def __init__(classifier, mappers, inferencer, validator, error_handler)
    async def extract(file_path, parsed_data, azure_result, user_hint, 
                     on_progress, on_error) → ExtractionResult
    
    # Stage methods
    async def _run_classifier() → ClassificationResult
    async def _run_mapper() → MappingResult
    async def _run_inferencer() → InferenceResult
    async def _run_validator() → CompletenessResult
    
    # Helper methods
    async def _parse_file() → Dict[str, Any]
    def _handle_error(stage, error) → str
    def _invoke_callbacks() → None
```

**Implementation Steps:**
1. Implement stage chaining logic
2. Implement state management
3. Implement error handling and recovery
4. Implement progress callbacks
5. Implement dependency injection
6. Implement file parsing logic
7. Integration tests

**Test Cases:**
- ✓ Full pipeline execution
- ✓ Error recovery at each stage
- ✓ Progress callbacks
- ✓ Custom stage injection
- ✓ File parsing fallback

**Expected Output:**
```python
ExtractionResult(
    status="success",
    kraftd_document=KraftdDocument(...),
    classification=ClassificationResult(...),
    mapping=MappingResult(...),
    inference=InferenceResult(...),
    completeness=CompletenessResult(...)
)
```

---

### Phase 2G: API Integration (2-3 hours)
**Objective:** Wire Pipeline into FastAPI and Agent

#### Changes to `backend/main.py`

**New Endpoint:**
```python
@app.post("/extract-intelligent")
async def extract_with_pipeline(file: UploadFile):
    """Full orchestrated pipeline extraction."""
    # Save file
    # Run pipeline
    # Store result
    # Return response
```

**Integration with existing endpoints:**
```python
# Update /extract to use pipeline
# Update /validate to use validator stage
# Update /workflow to use pipeline internally
```

**Changes to `backend/agent/kraft_agent.py`:**
```python
class KraftdAIAgent:
    def __init__(self):
        self.pipeline = ExtractionPipeline()
    
    async def _extract_intelligence_tool(self, document_id):
        # Use pipeline internally
        result = await self.pipeline.extract(...)
        return result
```

**Implementation Steps:**
1. Instantiate pipeline in main.py
2. Add new `/extract-intelligent` endpoint
3. Update existing endpoints to use pipeline
4. Update Agent tools to use pipeline
5. Maintain backward compatibility
6. Integration tests with FastAPI

**Expected Behavior:**
- New `/extract-intelligent` endpoint provides full pipeline
- Existing endpoints continue to work
- Agent uses pipeline for better extraction
- Gradual migration from old to new endpoints

---

### Phase 2H: Testing & Documentation (3-4 hours)
**Objective:** Complete test coverage and documentation

#### Testing

**Unit Tests:**
- `tests/test_pipeline/test_classifier.py`
- `tests/test_pipeline/test_mapper.py`
- `tests/test_pipeline/test_inferencer.py`
- `tests/test_pipeline/test_validator.py`

**Integration Tests:**
- `tests/test_pipeline/test_orchestrator.py`
- `tests/test_pipeline/test_full_pipeline.py`

**Test Coverage Goals:**
- Stage-level: >95%
- Pipeline: >90%
- Overall: >85%

**Test Strategy:**
```python
# Unit tests: Mock dependencies, test stage in isolation
test_classifier.py:
  - test_classify_rfq()
  - test_classify_quotation()
  - test_low_confidence()
  - test_with_user_hint()
  - test_hybrid_classification()

# Integration tests: Real dependencies, test full flow
test_full_pipeline.py:
  - test_complete_rq_extraction()
  - test_error_recovery()
  - test_progress_callbacks()
  - test_custom_stages()
```

#### Documentation

**Files to create:**
1. `PIPELINE_USAGE_GUIDE.md` - How to use the pipeline
2. `PIPELINE_EXTENSION_GUIDE.md` - How to extend with custom stages
3. `PIPELINE_TROUBLESHOOTING.md` - Common issues and solutions
4. Code comments for all stages and methods

**Documentation Content:**
```
USAGE_GUIDE:
- Quick start
- Basic usage
- Configuration options
- Error handling
- Examples

EXTENSION_GUIDE:
- Create custom classifier
- Create custom mapper
- Add business rules
- Custom types and validators

TROUBLESHOOTING:
- Classification fails
- Mapping errors
- Inference conflicts
- Low completeness scores
- Performance tuning
```

---

## Implementation Timeline

### Week 1
- **Day 1-2:** Foundation (types, base classes, test setup)
- **Day 3:** Classifier implementation
- **Day 4:** Mapper implementation
- **Day 5:** Inferencer implementation (start)

### Week 2
- **Day 1-2:** Inferencer implementation (complete, with business rules)
- **Day 3:** Validator implementation
- **Day 4:** Orchestrator + API integration
- **Day 5:** Testing, fixes, documentation

### Week 3
- **Day 1-3:** Edge case testing, performance tuning
- **Day 4-5:** Documentation, knowledge transfer

---

## Resource Requirements

### Development
- 1 senior developer: 18-26 hours
- 1 QA/tester: 6-8 hours (optional, can be integrated)

### Dependencies
- Existing processors (no changes)
- Existing schemas (no changes)
- Azure Document Intelligence SDK (already present)
- pytest for testing
- pydantic for validation

---

## Success Criteria

### By Phase 2 Completion

✅ **Functional Requirements**
- All 4 stages implemented and working
- Pipeline orchestrates all stages
- Error handling and recovery working
- FastAPI integration complete
- Agent integration complete

✅ **Quality Requirements**
- >85% test coverage
- All edge cases documented
- Performance <2 seconds per document
- Error messages clear and actionable

✅ **Documentation Requirements**
- Usage guide complete
- Extension guide complete
- Code well-commented
- Troubleshooting guide available

✅ **Performance Requirements**
- Classification: <100ms
- Mapping: <500ms
- Inference: <500ms
- Validation: <200ms
- **Total:** <2 seconds per document

---

## Risk Mitigation

### High-Risk Areas

**1. Inference Logic Complexity**
- Risk: Too many rules, hard to maintain
- Mitigation: Start with 10 core rules, allow extensibility
- Test: Heavy unit testing of each rule

**2. Performance Degradation**
- Risk: Too slow with all stages
- Mitigation: Profile and optimize early
- Test: Load testing with realistic documents

**3. Backward Compatibility**
- Risk: Break existing functionality
- Mitigation: Keep old endpoints, new `/extract-intelligent`
- Test: Full regression testing

**4. Azure Quota/Costs**
- Risk: Too many Document Intelligence calls
- Mitigation: Cache results, allow local fallback
- Test: Monitor usage, set quotas

---

## Rollout Strategy

### Phase 1: Internal Testing
- Run pipeline on internal sample documents
- Fix bugs and edge cases
- Get team feedback

### Phase 2: Beta Users
- Deploy to staging
- Test with real user documents
- Refine rules based on feedback

### Phase 3: Production Rollout
- Launch `/extract-intelligent` endpoint
- Keep old `/extract` for backward compatibility
- Migrate gradually to new pipeline
- Monitor quality metrics

### Phase 4: Deprecation
- After 3-6 months, deprecate old endpoint
- Complete migration to pipeline

---

## Estimated Effort Breakdown

| Task | Duration | Owner |
|------|----------|-------|
| Foundation | 4-5 hrs | Dev |
| Classifier | 2-3 hrs | Dev |
| Mapper | 3-4 hrs | Dev |
| Inferencer | 3-4 hrs | Dev |
| Validator | 2-3 hrs | Dev |
| Orchestrator | 2-3 hrs | Dev |
| API Integration | 2-3 hrs | Dev |
| Testing | 3-4 hrs | Dev |
| Documentation | 1-2 hrs | Dev |
| **TOTAL** | **23-31 hrs** | |

**Timeline:** 2-3 weeks with normal development pace

---

## Next Steps

1. **Review & Approve** - Team reviews this roadmap
2. **Setup** - Create repository structure
3. **Begin Phase 2A** - Start with foundation
4. **Iterate** - Complete each phase, get feedback
5. **Deploy** - Roll out to staging and production

---

**Ready to begin implementation? Start with Phase 2A: Foundation**
