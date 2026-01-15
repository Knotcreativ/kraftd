# Kraftd Backend Pipeline Inspection Report

## Executive Summary

The Kraftd MVP has a **functional extraction layer** but **lacks an orchestrated intelligent pipeline**. The existing code has good building blocks (processors, extractors, schemas) but they operate in isolation without a coordinated flow for classification, mapping, inference, and completeness validation.

---

## Current State Assessment

### ✅ What ALREADY Exists

#### 1. **Document Processors** (Well-Implemented)
- `PDFProcessor` - Extracts text, tables, pages using pdfplumber
- `WordProcessor` - Extracts paragraphs, tables, styles from docx
- `ExcelProcessor` - Extracts sheet data, cell values
- `ImageProcessor` - OCR support via Azure Document Intelligence
- All inherit from `BaseProcessor` with consistent interface

**Status:** Production-ready, no changes needed

#### 2. **Azure Document Intelligence Integration**
- `AzureDocumentIntelligenceService` - Wrapper around Azure cognitive services
- Supports prebuilt models (layout, invoice, receipt)
- Extracts text, tables, form fields, paragraphs
- Conditional initialization based on environment configuration

**Status:** Working, can be leveraged for enhanced extraction

#### 3. **Extraction Logic** (`DocumentExtractor`)
- Maps parsed documents to `KraftdDocument` schema
- Implements document type detection (RFQ, BOQ, Quotation, PO, etc.)
- Extracts metadata, parties, project context, dates, commercial terms, line items
- Has inference for currencies, confidence calculation
- Supports both local parsing and Azure results

**Status:** Functional but monolithic, needs decomposition into reusable stages

#### 4. **Comprehensive Schema** (`schemas.py`)
- Complete data models for all document types (RFQ, BOQ, Quotation, PO, Contract, Invoice)
- Pydantic models with validation
- Enums for document types, risk levels, disciplines, currencies, units
- All party, line item, and commercial term structures defined

**Status:** Well-designed, ready for use

#### 5. **FastAPI Integration** (`main.py`)
- REST endpoints for upload, conversion, extraction, comparison
- Document ID-based workflow
- In-memory storage (MVP)
- Basic error handling

**Status:** Working but needs pipeline integration

#### 6. **AI Agent** (`kraft_agent.py`)
- Uses Microsoft Agent Framework with Azure OpenAI
- Defines tools for document processing, comparison, validation
- Has orchestration logic for multi-step workflows

**Status:** Scaffolding present, but tools are mostly placeholders

---

### ❌ What's MISSING or INCOMPLETE

#### 1. **Classifier Pipeline Stage**
- ❌ No dedicated `DocumentClassifier` component
- Current detection in `DocumentExtractor._detect_document_type()` uses regex only
- No confidence scoring or multi-modal classification
- Cannot handle edge cases (hybrid documents, unknown types)
- No classification error recovery

#### 2. **Mapper Pipeline Stage**
- ❌ No dedicated `DocumentMapper` component
- Mapping logic mixed into `DocumentExtractor`
- No separate input/output contracts
- Hard to test and reuse
- No handling of incomplete field mappings

#### 3. **Inferencer Pipeline Stage**
- ❌ No dedicated `DocumentInferencer` component
- Inference logic scattered in extractor
- No systematic approach to derived fields
- No handling of ambiguity or missing data relationships
- No business rule application framework

#### 4. **Completeness Validator Stage**
- ❌ No `CompletenessValidator` component
- Current confidence calculation is simplistic
- No field-level completeness assessment
- No remediation suggestions
- No critical vs. optional field classification

#### 5. **Pipeline Orchestration**
- ❌ No `ExtractionPipeline` orchestrator
- No stage chaining or state management
- No error recovery across stages
- No progress callbacks or monitoring
- No dependency injection

#### 6. **Error Handling & Resilience**
- Current code has basic try/catch blocks
- No circuit breakers for Azure calls
- No retry logic
- No fallback mechanisms (e.g., if Azure fails, use local)
- No detailed error reporting

#### 7. **Testing Infrastructure**
- `test_extractor.py` exists but is minimal
- No stage-level unit tests
- No integration tests for pipeline
- No edge case coverage
- No mock Azure services

#### 8. **Workflow Directory**
- `/backend/workflow/` folder is empty
- No pipeline definition, no orchestration classes

---

## Architecture Gaps

### Current Flow (Linear, Monolithic)
```
File → Processor (PDF/Word/Excel/Image) 
     → DocumentExtractor.extract_to_kraftd_document() 
     → Returns KraftdDocument
```

**Problems:**
- All intelligence in one method
- Hard to test individual stages
- Hard to reuse components
- Hard to extend with new logic
- No feedback loop for correction

### Proposed Flow (Orchestrated, Composable)
```
File 
  ↓
DocumentClassifier 
  ├─ Detect type (RFQ/BOQ/Quote/PO/Contract/Invoice)
  ├─ Confidence scoring
  └─ Error handling
  ↓
DocumentMapper
  ├─ Extract metadata
  ├─ Normalize fields
  ├─ Handle null/missing values
  └─ Cross-field validation
  ↓
DocumentInferencer
  ├─ Infer missing fields (e.g., total = qty × price)
  ├─ Apply business rules
  ├─ Resolve ambiguities
  └─ Enrich with context
  ↓
CompletenessValidator
  ├─ Assess completeness %
  ├─ Identify critical gaps
  ├─ Suggest remediation
  └─ Flag risky extractions
  ↓
KraftdDocument (final enriched output)
```

---

## Key Observations

### What Works Well
1. **Processors** are clean, modular, and handle file format variations
2. **Schemas** are comprehensive and well-structured
3. **Azure integration** is present and functional
4. **API structure** is simple and clear
5. **Agent framework** skeleton exists

### What Needs Improvement
1. **Separation of concerns** - extraction logic mixed together
2. **Testability** - hard to unit test individual stages
3. **Reusability** - stages cannot be used independently
4. **Error recovery** - no fallback paths
5. **Configurability** - hardcoded patterns and logic
6. **Observability** - minimal logging and progress tracking
7. **Documentation** - no pipeline documentation

### Risks If Not Addressed
1. **Maintainability** - Adding new document types becomes exponentially harder
2. **Quality** - Incomplete extraction not caught until late in workflow
3. **Reliability** - Single point of failure in monolithic extractor
4. **Debugging** - Hard to isolate where extraction failed
5. **Performance** - All extraction happens synchronously, no parallelization

---

## Reusable Assets (Don't Rewrite)

1. ✅ All file processors (`pdf_processor.py`, `word_processor.py`, etc.)
2. ✅ Azure service integration (`azure_service.py`)
3. ✅ All Pydantic schemas (`schemas.py`)
4. ✅ Basic FastAPI structure in `main.py`
5. ✅ Agent framework scaffolding in `kraft_agent.py`

---

## Integration Approach

The new pipeline should:
1. **Wrap existing extractors** - Use processors as-is
2. **Decompose extraction** - Into classifier, mapper, inferencer, validator stages
3. **Preserve schema** - Reuse all existing Pydantic models
4. **Extend not replace** - Add to existing codebase, don't delete working code
5. **Backwards compatible** - Existing API endpoints continue to work
6. **Configurable** - Allow swapping stages or adding custom logic

---

## Recommended Next Steps

1. ✅ **Design Phase** (This inspection)
2. 📋 **Stage 1: Classifier** - Implement `DocumentClassifier` with confidence scoring
3. 📋 **Stage 2: Mapper** - Extract mapping logic into dedicated `DocumentMapper`
4. 📋 **Stage 3: Inferencer** - Build inference engine for derived/implicit data
5. 📋 **Stage 4: Completeness** - Create `CompletenessValidator` with suggestions
6. 📋 **Stage 5: Orchestration** - Build `ExtractionPipeline` to chain stages
7. 📋 **Stage 6: Integration** - Wire into FastAPI and agent tools
8. 📋 **Stage 7: Testing** - Full test coverage
9. 📋 **Stage 8: Documentation** - Architecture guides and runbooks

---

## Estimated Effort

- **Classifier**: 2-3 hours
- **Mapper**: 3-4 hours
- **Inferencer**: 3-4 hours (most complex)
- **Completeness Validator**: 2-3 hours
- **Orchestration**: 2-3 hours
- **Integration**: 2-3 hours
- **Testing**: 3-4 hours
- **Documentation**: 1-2 hours

**Total**: ~18-26 hours of focused development

---

## Conclusion

The Kraftd backend has solid fundamentals but needs a **structured pipeline orchestration** to scale intelligent extraction. The proposed four-stage pipeline (Classify → Map → Infer → Validate) will:

- ✅ Improve code modularity and testability
- ✅ Enable intelligent field inference and completeness detection
- ✅ Provide better error handling and recovery
- ✅ Support new document types without rewriting core logic
- ✅ Create observability into extraction quality
- ✅ Prepare for future ML-based classification

All recommended changes are **additive** - no existing working code needs to be removed.
