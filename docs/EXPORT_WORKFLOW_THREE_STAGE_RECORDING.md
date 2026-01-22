# AI Export Workflow Recording System
## Three-Stage Tracking: Initial Summary → User Modifications → Final Deliverable

**Status:** ✅ DESIGN DOCUMENT - Ready for Implementation  
**Date:** January 18, 2026  
**Purpose:** Record complete audit trail of AI-generated content, user modifications, and final outputs

---

## Overview

Your system needs to track **three distinct stages** of the export workflow:

```
Stage 1: Initial AI Summary
  ↓ (User reviews & edits data)
Stage 2: User Modifications & Preferences
  ↓ (AI processes final version)
Stage 3: Final Summary & Deliverable
```

Each stage must be recorded in Cosmos DB for:
- ✅ Audit trail (who did what, when)
- ✅ User history (view past versions)
- ✅ AI learning (learn from user preferences)
- ✅ Quality tracking (measure improvements)
- ✅ Compliance (document processing chain)

---

## Stage 1: Initial AI Summary Recording

### What Gets Recorded

When user clicks "Review" and AI analyzes document intelligence data:

```python
{
    "id": "export_stage1_doc123_20240118",
    "document_id": "doc123",
    "owner_email": "user@example.com",
    "stage": "initial_ai_summary",
    "timestamp": "2024-01-18T10:30:45.123Z",
    
    # Source data
    "source": {
        "document_type": "invoice",
        "extraction_method": "AZURE_DI",
        "di_confidence": 0.92,
        "extraction_fields_count": 25,
        "line_items_count": 5
    },
    
    # Initial extracted data (before user editing)
    "initial_extracted_data": {
        "invoice_number": "INV-2024-001",
        "date": "2024-01-15",
        "supplier": "ABC Trading",
        "total": 1050.00,
        ...  // All extracted fields
    },
    
    # AI-generated initial summary
    "ai_initial_summary": {
        "executive_summary": "Invoice from ABC Trading for professional services...",
        "key_findings": [
            "Standard Net 30 payment terms",
            "All required fields present",
            "Single line item invoice"
        ],
        "recommendations": [
            "Approve for processing",
            "Standard supplier profile"
        ],
        "risk_factors": [],
        "action_items": [
            "Route to accounts payable",
            "Schedule payment for 2024-02-14"
        ]
    },
    
    # Metadata about initial summary generation
    "initial_summary_metadata": {
        "ai_model": "gpt-4o-mini",
        "processing_time_ms": 2150,
        "tokens_used": 450,
        "confidence_score": 0.94,
        "generated_at": "2024-01-18T10:30:45.123Z"
    },
    
    # System metadata
    "status": "awaiting_user_review",
    "_ts": 1705590645
}
```

### Recording Implementation

In `export_document()` endpoint:

```python
# After Phase 1 AI summary generation
if ai_summary and AGENT_AVAILABLE:
    stage1_record = {
        "id": f"export_stage1_{document_id}_{int(datetime.now().timestamp())}",
        "document_id": document_id,
        "owner_email": owner_email,
        "stage": "initial_ai_summary",
        "timestamp": datetime.now().isoformat(),
        
        "source": {
            "document_type": doc_record.get("document", {}).get("metadata", {}).get("document_type"),
            "extraction_method": doc_record.get("document", {}).get("metadata", {}).get("extraction_method"),
            "di_confidence": doc_record.get("document", {}).get("metadata", {}).get("di_confidence"),
            "extraction_fields_count": len(flat_data),
            "line_items_count": len(flat_data.get("line_items", []))
        },
        
        "initial_extracted_data": flat_data.copy(),
        
        "ai_initial_summary": ai_summary,
        
        "initial_summary_metadata": {
            "ai_model": agent.model_deployment,
            "processing_time_ms": ai_processing_time,
            "tokens_used": ai_tokens_used,
            "confidence_score": ai_summary.get("confidence", 0.0),
            "generated_at": datetime.now().isoformat()
        },
        
        "status": "awaiting_user_review"
    }
    
    # Save to Cosmos DB
    try:
        export_tracking_container = cosmos_database.get_container_client("export_tracking")
        await export_tracking_container.create_item(stage1_record)
        logger.info(f"Recorded Stage 1: Initial AI summary for {document_id}")
    except Exception as e:
        logger.error(f"Failed to record Stage 1: {e}")
```

---

## Stage 2: User Modifications & Preferences Recording

### What Gets Recorded

When user edits data and enters preferences in text box:

```python
{
    "id": "export_stage2_doc123_20240118",
    "document_id": "doc123",
    "owner_email": "user@example.com",
    "stage": "user_modifications",
    "timestamp": "2024-01-18T10:35:20.456Z",
    
    # Link to Stage 1
    "stage1_id": "export_stage1_doc123_20240118",
    
    # Original data (from Stage 1)
    "original_data": {
        "invoice_number": "INV-2024-001",
        "date": "2024-01-15",
        "supplier": "ABC Trading",
        "total": 1050.00,
        ...
    },
    
    # User's edited data
    "modified_data": {
        "invoice_number": "INV-2024-001",  // Changed from INV-2024-001
        "date": "2024-01-15",
        "supplier": "ABC Trading Ltd.",    // User corrected name
        "total": 1050.00,
        "notes": "Added notes from user review",
        ...  // Other fields user edited
    },
    
    # User preferences and instructions
    "user_preferences": {
        "transformation_instructions": "Highlight all totals in red, merge supplier name with contact person",
        "export_format": "pdf",
        "document_template": "executive_summary",
        "template_customization": "Focus on financial metrics and risk assessment",
        "priority_fields": ["supplier", "total", "payment_terms"]
    },
    
    # Diff between original and modified
    "changes": [
        {
            "field": "supplier",
            "original_value": "ABC Trading",
            "modified_value": "ABC Trading Ltd.",
            "change_type": "correction",
            "user_reason": "Corrected full legal name"
        },
        {
            "field": "notes",
            "original_value": null,
            "modified_value": "Added notes from user review",
            "change_type": "addition",
            "user_reason": "Adding internal notes"
        }
    ],
    
    # User metadata
    "user_actions": {
        "fields_edited_count": 2,
        "fields_added_count": 1,
        "total_modifications": 3,
        "editing_time_seconds": 285,  // Time user spent editing
        "edits_per_minute": 0.63,
        "data_confidence_before_edit": 0.92,
        "user_confidence_after_edit": 0.98  // Estimated from user input
    },
    
    # System metadata
    "status": "awaiting_final_processing",
    "created_at": "2024-01-18T10:35:20.456Z"
}
```

### Recording Implementation

When user submits edited data:

```python
# In frontend, before sending export request
const stage2Data = {
    stage1_id: stage1Record.id,
    original_data: stage1Record.initial_extracted_data,
    modified_data: editedData,
    user_preferences: {
        transformation_instructions: userInstructions,
        export_format: selectedFormat,
        document_template: documentTemplate,
        template_customization: templateCustomization,
        priority_fields: highlightedFields
    },
    editing_time_seconds: (Date.now() - reviewStartTime) / 1000,
    changes: calculateDiff(original, edited)
};

// Send with export request
const response = await apiClient.downloadExportedFile(
    documentId,
    exportFormat,
    editedData,
    userInstructions,
    templateOptions,
    stage2Data  // Include tracking data
);
```

Backend recording:

```python
@app.post("/api/v1/docs/{document_id}/export")
async def export_document(...):
    # ... previous code ...
    
    stage1_id = export_request.get("stage1_id")
    editing_time_seconds = export_request.get("editing_time_seconds", 0)
    user_changes = export_request.get("changes", [])
    
    if stage1_id:
        stage2_record = {
            "id": f"export_stage2_{document_id}_{int(datetime.now().timestamp())}",
            "document_id": document_id,
            "owner_email": owner_email,
            "stage": "user_modifications",
            "timestamp": datetime.now().isoformat(),
            
            "stage1_id": stage1_id,
            
            "original_data": previous_extracted_data,  # From Stage 1
            "modified_data": flat_data,  # User's edited version
            
            "user_preferences": {
                "transformation_instructions": transformation_instructions,
                "export_format": format_type,
                "document_template": document_template,
                "template_customization": template_customization,
                "priority_fields": list(flat_data.keys())[:5]  # Top 5 fields
            },
            
            "changes": calculate_changes(previous_extracted_data, flat_data),
            
            "user_actions": {
                "fields_edited_count": len(calculate_changes(...)),
                "editing_time_seconds": editing_time_seconds,
                "edits_per_minute": len(user_changes) / (editing_time_seconds / 60) if editing_time_seconds > 0 else 0,
                "data_confidence_before_edit": doc_record.get("extraction_confidence", 0.0),
                "user_confidence_after_edit": 0.95  # Could be from user feedback
            },
            
            "status": "awaiting_final_processing"
        }
        
        # Save to Cosmos DB
        try:
            export_tracking_container = cosmos_database.get_container_client("export_tracking")
            await export_tracking_container.create_item(stage2_record)
            logger.info(f"Recorded Stage 2: User modifications for {document_id}")
        except Exception as e:
            logger.error(f"Failed to record Stage 2: {e}")
```

---

## Stage 3: Final Summary & Deliverable Recording

### What Gets Recorded

When AI generates final version and produces downloadable file:

```python
{
    "id": "export_stage3_doc123_20240118",
    "document_id": "doc123",
    "owner_email": "user@example.com",
    "stage": "final_summary_and_deliverable",
    "timestamp": "2024-01-18T10:36:15.789Z",
    
    # Link to previous stages
    "stage1_id": "export_stage1_doc123_20240118",
    "stage2_id": "export_stage2_doc123_20240118",
    
    # Final AI-generated summary
    "ai_final_summary": {
        "executive_summary": "Executive summary based on user's final edits and preferences...",
        "key_findings": [
            "After user corrections: Complete and verified data",
            "All supplier information validated",
            "Financial metrics confirmed by user"
        ],
        "recommendations": [
            "Ready for approval",
            "High confidence after user validation"
        ],
        "risk_factors": [],
        "action_items": [
            "Route to finance for final approval",
            "Create purchase order if approved"
        ],
        "learning_insights": {
            "user_corrected_fields": ["supplier_name"],
            "confidence_improvement": 0.06,  // From 0.92 to 0.98
            "user_focus_areas": ["financial_metrics", "supplier_info"]
        }
    },
    
    # Metadata about final summary generation
    "final_summary_metadata": {
        "ai_model": "gpt-4o-mini",
        "processing_time_ms": 1890,
        "tokens_used": 380,
        "template_used": "executive_summary",
        "export_format": "pdf",
        "confidence_score": 0.98,
        "generated_at": "2024-01-18T10:36:15.789Z"
    },
    
    # Generated file information
    "deliverable": {
        "filename": "doc123_executive_summary_20240118.pdf",
        "file_size_bytes": 245632,
        "file_format": "pdf",
        "mime_type": "application/pdf",
        "pages": 3,
        "content_hash": "sha256:abc123def456...",
        "generated_at": "2024-01-18T10:36:15.789Z"
    },
    
    # Complete workflow summary
    "workflow_summary": {
        "total_time_seconds": 125,  // From review start to download
        "stage1_time_seconds": 45,  // AI analysis
        "stage2_time_seconds": 40,  // User editing
        "stage3_time_seconds": 40,  // Final AI processing + file generation
        
        "total_modifications": 3,
        "user_input_quality": 0.98,
        "ai_processing_accuracy": 0.96,
        "final_output_quality": 0.97,
        
        "ai_learning_recorded": true,
        "user_patterns_learned": [
            "User focuses on supplier information",
            "Tends to correct names and addresses",
            "Prefers executive_summary template",
            "Uses transformation_instructions effectively"
        ]
    },
    
    # Traceability
    "traceability": {
        "document_history": [
            {
                "timestamp": "2024-01-18T10:25:00Z",
                "action": "document_uploaded",
                "details": "Original PDF uploaded"
            },
            {
                "timestamp": "2024-01-18T10:28:00Z",
                "action": "extracted_by_adi",
                "details": "Azure Document Intelligence extraction"
            },
            {
                "timestamp": "2024-01-18T10:30:45Z",
                "action": "stage1_ai_summary",
                "details": "Initial AI summary generated"
            },
            {
                "timestamp": "2024-01-18T10:35:20Z",
                "action": "user_modifications",
                "details": "User edited data and added preferences"
            },
            {
                "timestamp": "2024-01-18T10:36:15Z",
                "action": "stage3_final_summary",
                "details": "Final AI summary and PDF generated"
            },
            {
                "timestamp": "2024-01-18T10:36:16Z",
                "action": "downloaded_by_user",
                "details": "User downloaded PDF file"
            }
        ]
    },
    
    # Status and next actions
    "status": "completed",
    "download_status": "ready",
    "expiration_date": "2024-02-18T10:36:15Z"  // 30 days retention
}
```

### Recording Implementation

After AI generates final version:

```python
# After Phase 2 template generation
if use_ai_template_generation and ai_summary:
    # Generate final file (JSON/CSV/Excel/PDF)
    content = generate_file(format_type, ai_formatted_data, ...)
    
    stage3_record = {
        "id": f"export_stage3_{document_id}_{int(datetime.now().timestamp())}",
        "document_id": document_id,
        "owner_email": owner_email,
        "stage": "final_summary_and_deliverable",
        "timestamp": datetime.now().isoformat(),
        
        "stage1_id": stage1_id,
        "stage2_id": stage2_id,
        
        "ai_final_summary": ai_summary,  # Final AI-generated summary
        
        "final_summary_metadata": {
            "ai_model": agent.model_deployment,
            "processing_time_ms": final_processing_time,
            "tokens_used": final_tokens_used,
            "template_used": document_template,
            "export_format": format_type,
            "confidence_score": 0.98,
            "generated_at": datetime.now().isoformat()
        },
        
        "deliverable": {
            "filename": f"{document_id}_{document_template}_{datetime.now().strftime('%Y%m%d')}.{format_type}",
            "file_size_bytes": len(content),
            "file_format": format_type,
            "mime_type": get_mime_type(format_type),
            "content_hash": hashlib.sha256(content).hexdigest(),
            "generated_at": datetime.now().isoformat()
        },
        
        "workflow_summary": {
            "total_time_seconds": (datetime.now() - stage1_timestamp).total_seconds(),
            "stage1_time_seconds": stage1_duration,
            "stage2_time_seconds": stage2_duration,
            "stage3_time_seconds": stage3_duration,
            "total_modifications": len(calculate_changes(...)),
            "ai_processing_accuracy": 0.96,
            "final_output_quality": 0.97
        },
        
        "traceability": {
            "document_history": build_document_history(...)
        },
        
        "status": "completed",
        "download_status": "ready",
        "expiration_date": (datetime.now() + timedelta(days=30)).isoformat()
    }
    
    # Save to Cosmos DB
    try:
        export_tracking_container = cosmos_database.get_container_client("export_tracking")
        await export_tracking_container.create_item(stage3_record)
        logger.info(f"Recorded Stage 3: Final summary for {document_id}")
        
        # Also record for AI learning
        await record_for_learning(stage3_record)
        
    except Exception as e:
        logger.error(f"Failed to record Stage 3: {e}")
```

---

## Cosmos DB Schema

### Container: `export_tracking`

```json
{
    "name": "export_tracking",
    "partitionKeyPath": "/owner_email",
    "uniqueKeyPolicy": {
        "uniqueKeys": [
            {
                "paths": ["/id"]
            }
        ]
    },
    "indexingPolicy": {
        "indexingMode": "consistent",
        "includedPaths": [
            {
                "path": "/owner_email",
                "indexes": [{"kind": "Range", "dataType": "String"}]
            },
            {
                "path": "/document_id",
                "indexes": [{"kind": "Range", "dataType": "String"}]
            },
            {
                "path": "/stage",
                "indexes": [{"kind": "Range", "dataType": "String"}]
            },
            {
                "path": "/timestamp",
                "indexes": [{"kind": "Range", "dataType": "String"}]
            }
        ]
    }
}
```

---

## Query Patterns

### Get All Stages for a Document
```python
query = "SELECT * FROM export_tracking WHERE c.document_id = @doc_id ORDER BY c.timestamp ASC"
parameters = [{"name": "@doc_id", "value": document_id}]

# Returns: Stage 1, Stage 2, Stage 3 in chronological order
```

### Get User's Export History
```python
query = "SELECT c.document_id, c.stage, c.timestamp, c.status FROM export_tracking WHERE c.owner_email = @email ORDER BY c.timestamp DESC"
parameters = [{"name": "@email", "value": user_email}]

# Returns: All exports by user
```

### Get Stage 3 Deliverables
```python
query = "SELECT c.deliverable, c.workflow_summary FROM export_tracking WHERE c.stage = 'final_summary_and_deliverable' AND c.owner_email = @email"
parameters = [{"name": "@email", "value": user_email}]

# Returns: Only final deliverables for download
```

### Track AI Learning Patterns
```python
query = "SELECT c.workflow_summary.user_patterns_learned FROM export_tracking WHERE c.stage = 'final_summary_and_deliverable' AND c.owner_email = @email"
parameters = [{"name": "@email", "value": user_email}]

# Returns: Patterns learned from this user's preferences
```

---

## Data Flow Diagram

```
Document Uploaded
      ↓
Azure Document Intelligence Extracts Data
      ↓
[STAGE 1: INITIAL AI SUMMARY]
├─ AI analyzes extracted data
├─ Generates initial summary
└─ Saves Stage 1 Record to Cosmos DB
      ↓
User Reviews Data & Summary
      ↓
User Edits Fields + Adds Preferences
      ↓
[STAGE 2: USER MODIFICATIONS]
├─ Records original data
├─ Records modified data
├─ Records user preferences
├─ Calculates diff/changes
└─ Saves Stage 2 Record to Cosmos DB
      ↓
User Selects Template & Format
      ↓
[STAGE 3: FINAL SUMMARY & DELIVERABLE]
├─ AI processes user's modified data
├─ Generates final summary
├─ Creates formatted file
├─ Records deliverable info
├─ Records workflow metrics
├─ Records learning patterns
├─ Saves Stage 3 Record to Cosmos DB
└─ Makes file available for download
      ↓
User Downloads File
      ↓
[SYSTEM]
├─ Updates download status
├─ Records download timestamp
└─ Archives for future reference
```

---

## Benefits

### For Audit Trail
- ✅ Complete history of document processing
- ✅ Who made what changes, when
- ✅ Full traceability from original to final
- ✅ Compliance with document retention policies

### For User Experience
- ✅ Users can see their export history
- ✅ Users can re-generate versions
- ✅ Users can compare versions
- ✅ Users can export previous versions

### For AI Learning
- ✅ AI learns user preferences from Stage 2
- ✅ AI learns what corrections users make
- ✅ AI learns which templates users prefer
- ✅ AI improves accuracy over time

### For System Improvement
- ✅ Track processing quality metrics
- ✅ Measure confidence improvements
- ✅ Monitor user patterns
- ✅ Identify common issues
- ✅ Optimize workflow performance

---

## Implementation Checklist

### Database Setup
- [ ] Create `export_tracking` container in Cosmos DB
- [ ] Set partition key to `/owner_email`
- [ ] Create indexes on: document_id, stage, timestamp, status
- [ ] Set TTL for data retention

### Stage 1 Implementation
- [ ] Add recording code after AI summary generation
- [ ] Test Stage 1 record creation
- [ ] Verify data completeness
- [ ] Test Cosmos DB persistence

### Stage 2 Implementation
- [ ] Add change detection logic
- [ ] Pass stage1_id to frontend
- [ ] Capture user editing time
- [ ] Record user preferences
- [ ] Calculate diffs

### Stage 3 Implementation
- [ ] Add final summary recording
- [ ] Record deliverable info
- [ ] Calculate workflow metrics
- [ ] Trigger AI learning
- [ ] Save traceability chain

### Testing
- [ ] Test complete workflow (all 3 stages)
- [ ] Verify Cosmos DB records created
- [ ] Test query patterns
- [ ] Test export history retrieval
- [ ] Test AI learning from data

### APIs to Add
- [ ] GET /api/v1/docs/{document_id}/export-history - Get all stages
- [ ] GET /api/v1/user/exports - List user's exports
- [ ] GET /api/v1/exports/{export_id}/stage/{stage_number} - Get specific stage
- [ ] GET /api/v1/exports/{export_id}/download - Download final file
- [ ] POST /api/v1/exports/{export_id}/regenerate - Regenerate with same settings

---

## Summary

This three-stage recording system provides:

1. **Stage 1 Recording** - Captures AI's initial analysis
2. **Stage 2 Recording** - Tracks user edits and preferences
3. **Stage 3 Recording** - Records final AI processing and deliverable

Together, they create a complete audit trail while enabling:
- User history and re-generation
- AI learning from user behavior
- Quality tracking and improvement
- Compliance and archival

---
