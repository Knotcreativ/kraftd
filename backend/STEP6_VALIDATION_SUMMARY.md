# STEP 6 SCENARIO MAPPING - EXECUTIVE SUMMARY

## ✅ VALIDATION RESULT: APPROACH IS VIABLE (90%+ CONFIDENCE)

---

## OVERVIEW

**Objective**: Migrate 10 document and workflow endpoints from in-memory storage to Cosmos DB via DocumentRepository

**Status**: All scenarios analyzed, all issues identified as resolvable

**Confidence**: HIGH - Pattern matches Step 5 (auth endpoints), all repository methods exist

---

## KEY FINDINGS

### 1. ✅ Repository Methods Are Available
All 10 endpoints can be supported by existing DocumentRepository methods:
- ✅ `create_document()` - for upload
- ✅ `get_document()` - for retrieval and updates
- ✅ `update_document()` - for field updates
- ✅ `update_document_status()` - for status transitions
- ✅ `exists()` - for existence checks

### 2. ✅ Current Data Model Maps Cleanly

**Current Structure**:
```python
documents_db = {
  "doc-id": {
    "file_path": "...",
    "file_type": "pdf",
    "document": {...},  # KraftdDocument.dict()
    "validation": {...}  # Optional
  }
}
```

**Maps to Cosmos** via DocumentRepository schema - NO BREAKING CHANGES

### 3. ⚠️ 6 Identified Issues (ALL RESOLVABLE)

| Issue | Problem | Solution | Impact | Status |
|-------|---------|----------|--------|--------|
| File Storage | Not in Cosmos DB | Keep in UPLOAD_DIR, store path in metadata | LOW | ✅ |
| Owner Email | Partition key required | Extract from JWT token | MEDIUM | ✅ |
| Serialization | KraftdDocument.dict() | Store as JSON nested field | LOW | ✅ |
| Status Enum | Arbitrary status strings | Extend DocumentStatus enum | MEDIUM | ✅ |
| File Paths | Could break in cluster | Reconstruct from doc_id + UPLOAD_DIR | LOW | ✅ |
| Validation Results | Need schema | Add to document fields | LOW | ✅ |

---

## ENDPOINT MIGRATION PLAN

### Phase 1: Preparation ✓
- Extend DocumentStatus enum with workflow statuses
- Create `get_document_repository()` helper
- Test with sample data

### Phase 2: Core Operations (3 endpoints)
- `POST /api/v1/docs/upload` → `create_document()`
- `POST /api/v1/docs/convert` → `get_document()` + update
- `POST /api/v1/docs/extract` → `get_document()` + `update_document()`

### Phase 3: Read Operations (3 endpoints)
- `GET /api/v1/documents/{id}` → `get_document()`
- `GET /api/v1/documents/{id}/status` → `get_document()` + extract status
- `GET /api/v1/documents/{id}/output` → `get_document()` + extract document

### Phase 4: Workflow Integration (4 endpoints)
- `POST /api/v1/workflow/inquiry` → `update_document_status()`
- `POST /api/v1/workflow/estimation` → `get_document()` + update
- `POST /api/v1/workflow/normalize-quotes` → `update_document()`
- `POST /api/v1/workflow/comparison` → `update_document()`

---

## DESIGN DECISIONS CONFIRMED

✅ **File Storage**: Remains in UPLOAD_DIR (not Cosmos DB)
- Files are large, mutable, and accessed frequently
- Cosmos DB better for metadata and state tracking
- File path stored in document record

✅ **Owner Verification**: Extract from JWT token
- Current endpoints lack owner context (security issue)
- JWT validation provides secure ownership
- Partition key (/owner_email) ensures data isolation

✅ **Fallback Mode**: All endpoints support in-memory fallback
- Same pattern as Step 5
- Zero-downtime migration strategy
- Easy rollback if needed

✅ **Status Management**: Extend DocumentStatus enum
- Add workflow statuses: REVIEW_PENDING, ESTIMATION_IN_PROGRESS, etc.
- Unified status tracking across repository

✅ **Schema Design**: Flat structure with nested document field
```
{
  id, owner_email, filename, document_type, status,
  file_path, file_type,
  document: { ... KraftdDocument ... },
  validation: { ... scores ... },
  created_at, updated_at, ttl
}
```

---

## RISK MITIGATION

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Owner email unavailable | LOW | HIGH | JWT validation required |
| File paths break | LOW | MEDIUM | Reconstruct from doc_id |
| Cosmos connection issues | MEDIUM | LOW | Fallback to in-memory |
| Status enum mismatch | LOW | MEDIUM | Extend enum upfront |
| Query performance issues | MEDIUM | MEDIUM | Use partition key |

---

## VALIDATION CHECKLIST (Ready to Implement)

```
Phase 1 Checks:
□ DocumentStatus enum extended with workflow statuses
□ get_document_repository() helper created
□ Repository tested with sample data

Phase 2-4 Checks:
□ Repository imports added
□ All 10 endpoints updated with repository calls
□ Fallback to documents_db in all endpoints
□ Error handling with proper logging
□ JWT owner extraction implemented

Validation Script:
□ 12/12 validation checks created
□ All endpoints verified to use repository
□ All error handlers verified
□ All logging statements verified
```

---

## CONFIDENCE ASSESSMENT

**Overall Confidence**: ⭐⭐⭐⭐⭐ HIGH (90%+)

**Why High Confidence**:
1. ✅ Step 5 proved repository pattern works
2. ✅ All required methods exist in DocumentRepository
3. ✅ Current data model maps cleanly to repository schema
4. ✅ All identified issues have clear solutions
5. ✅ Fallback strategy ensures safety
6. ✅ Partition key strategy optimizes performance
7. ✅ Zero breaking changes to API contracts

**Why Not 100%**:
- Owner email extraction depends on JWT validation (medium risk, easily mitigated)
- Cosmos DB connection (handled by fallback)
- Query performance (optimized via partition key, but untested at scale)

---

## RECOMMENDATION

### ✅ PROCEED WITH IMPLEMENTATION

**Next Steps**:
1. Review this scenario mapping document
2. Approve design decisions
3. Authorize implementation phase
4. Begin Phase 1 (preparation)
5. Execute Phases 2-4 (migrations)
6. Run validation tests (12 checks)

---

## SUCCESS CRITERIA

- ✅ All 10 endpoints migrated to repository pattern
- ✅ All validation checks passing (12/12)
- ✅ Fallback mode working (tested with Cosmos offline)
- ✅ Error handling comprehensive (try/except/finally)
- ✅ Logging comprehensive (DEBUG, INFO, ERROR, WARNING)
- ✅ No breaking changes to API contracts
- ✅ Performance maintained (partition key optimization)

---

**Status**: Ready for implementation approval
**Confidence**: 90%+ HIGH
**Risk Level**: LOW (with mitigations in place)
**Estimated Timeline**: 3-4 hours for full implementation + validation

