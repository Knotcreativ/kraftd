# Per-Document Extraction Storage Architecture

## Problem
When a user uploads **multiple documents** (e.g., quotations from two different suppliers), the OCR and Document Intelligence extraction results should be stored **separately per document**, not merged into a single record. This prevents data confusion and allows independent processing of each document's intelligence.

## Solution
Added a dedicated **ExtractionRepository** alongside DocumentRepository to handle per-document extraction payloads.

### Architecture

#### 1. DocumentRepository (existing)
- **Container**: `documents`
- **Partition Key**: `/owner_email`
- **Item ID**: `document_id` (UUID)
- **Content**: Document metadata, file path, document type, status
- **Purpose**: Track uploaded document metadata and processing status

#### 2. ExtractionRepository (new)
- **Container**: `extractions`
- **Partition Key**: `/owner_email`
- **Item ID**: `{document_id}:{source}` (e.g., `abc-123:direct_parse`)
- **Content**: Extracted structured data, validation scores, confidence
- **Purpose**: Store extraction results **per document per source method**

### Data Flow

#### Multi-Document Upload
```
POST /api/v1/docs/upload/batch
├─ File 1 (Supplier A Quotation)
│  └─ create_document() → documents container
│     └─ document_id: "doc-001"
│        filename: "supplier_a_quote.pdf"
│        file_type: "pdf"
│        status: "uploaded"
│
└─ File 2 (Supplier B Quotation)
   └─ create_document() → documents container
      └─ document_id: "doc-002"
         filename: "supplier_b_quote.pdf"
         file_type: "pdf"
         status: "uploaded"
```

#### Per-Document Extraction
```
POST /api/v1/docs/extract?document_id=doc-001
├─ Parse file
├─ Run ExtractionPipeline (Classifier → Mapper → Inferencer → Validator)
└─ Store extraction results separately:
   ├─ Update DocumentRepository (status: extracted, validation summary)
   └─ Create ExtractionRepository item:
      └─ extraction_repo.create_extraction(
         document_id="doc-001",
         source="direct_parse",
         data={extracted_document, validation, confidence_scores},
         metadata={extraction_method, stages_completed, processing_time_ms}
      )
      └─ Cosmos DB item: {"id": "doc-001:direct_parse", ...}
```

### Multi-Source Extraction (Future)
When a document can be extracted by multiple methods (OCR, Azure Document Intelligence, direct parse):

```
extractions container:
├─ "doc-001:ocr"          → OCR extraction results
├─ "doc-001:direct_parse" → Classifier + pipeline results
└─ "doc-001:azure_di"     → Azure Document Intelligence results

All three stored independently, no merging or overwriting.
```

### Benefits

1. **Per-Document Isolation**: Each document's extraction is stored as a separate item. Multiple documents don't share data.
2. **Multi-Source Capability**: Same document can be extracted via OCR, direct parsing, and Azure DI independently, each stored with source metadata.
3. **Scalability**: Extraction payloads don't bloat the main document record; queries remain fast.
4. **Auditability**: Each extraction method leaves a separate audit trail.
5. **Comparison & Learning**: AI can compare extraction quality across methods for the same document.

### Code Integration

#### When Uploading Multiple Documents
```python
# Batch upload endpoint
@app.post("/api/v1/docs/upload/batch")
async def upload_documents(files: List[UploadFile] = File(...)):
    # For each file:
    repo.create_document(...)  # Store metadata in documents container
    # Extraction happens later when user clicks "Review"
```

#### When Extracting a Single Document
```python
# Extract endpoint
@app.post("/api/v1/docs/extract?document_id=doc-001")
async def extract_intelligence(document_id: str):
    # ... run pipeline ...
    
    # Store main document status
    await update_document_record(document_id, {
        "document": kraftd_document.dict(),
        "validation": validation_data
    })
    
    # Store extraction results separately
    extraction_repo = await get_extraction_repository()
    await extraction_repo.create_extraction(
        document_id=document_id,
        source="direct_parse",
        data={extracted_document, validation, confidence_scores}
    )
```

#### When Retrieving Extractions for a Document
```python
# Get all extraction methods for a document
extraction_repo = await get_extraction_repository()
extractions = await extraction_repo.get_extractions_for_document(
    owner_email="user@company.com",
    document_id="doc-001"
)
# Returns: [ocr_result, direct_parse_result, azure_di_result, ...]
```

### File Changes

- **Created**: `backend/repositories/extraction_repository.py`
  - `ExtractionRepository` class with CRUD methods
  - `create_extraction()`, `get_extractions_for_document()`, `delete_extraction()`
  
- **Updated**: `backend/main.py`
  - Added `get_extraction_repository()` helper
  - Updated `/upload/batch` endpoint to note extraction separation
  - Updated `/extract` endpoint to store results in ExtractionRepository after processing

### Cosmos DB Schema

#### documents container
```json
{
  "id": "doc-001",
  "owner_email": "user@company.com",
  "filename": "supplier_a_quote.pdf",
  "document_type": "Quotation",
  "file_path": "/uploads/doc-001.pdf",
  "file_type": "pdf",
  "status": "extracted",
  "created_at": "2024-01-19T10:00:00Z",
  "updated_at": "2024-01-19T10:05:00Z"
}
```

#### extractions container
```json
{
  "id": "doc-001:direct_parse",
  "document_id": "doc-001",
  "owner_email": "user@company.com",
  "source": "direct_parse",
  "confidence": 0.95,
  "payload": {
    "extracted_document": {...KraftdDocument...},
    "validation": {
      "completeness_score": 85.5,
      "quality_score": 92.0,
      "ready_for_processing": true
    },
    "confidence_scores": {
      "classifier": 0.98,
      "mapping": 0.87,
      "inference": 0.91
    }
  },
  "metadata": {
    "extraction_method": "direct_parse",
    "stages_completed": ["classifier", "mapper", "inferencer", "validator"],
    "processing_time_ms": 2345
  },
  "created_at": "2024-01-19T10:05:00Z",
  "updated_at": "2024-01-19T10:05:00Z"
}
```

### Migration & Deployment

1. Create `extractions` container in Cosmos DB (partition key: `/owner_email`)
2. Deploy `extraction_repository.py`
3. Deploy updated `main.py` with extraction storage logic
4. Existing documents continue to work; new extractions stored separately
5. Optional: Backfill historical extractions to new container

### Testing

```bash
# Test batch upload
curl -X POST http://localhost:8000/api/v1/docs/upload/batch \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.pdf"
# Returns: [{"document_id": "doc-001", ...}, {"document_id": "doc-002", ...}]

# Extract doc-001
curl -X POST "http://localhost:8000/api/v1/docs/extract?document_id=doc-001"
# Stores in extractions: {"id": "doc-001:direct_parse", ...}

# Extract doc-002
curl -X POST "http://localhost:8000/api/v1/docs/extract?document_id=doc-002"
# Stores in extractions: {"id": "doc-002:direct_parse", ...}

# Verify isolation: extractions are separate items per document
```

---

**Status**: Ready for deployment. ExtractionRepository fully integrated into upload/extract pipeline.
