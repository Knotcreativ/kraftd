================================================================================
EXTRACTION DATA STRUCTURE - VISUAL REFERENCE GUIDE
================================================================================

Complete JSON structure of ExtractionRecord with all sections:

┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTRACTION RECORD                                   │
│                    (Cosmos DB Item Structure)                               │
└─────────────────────────────────────────────────────────────────────────────┘

{
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ SECTION 0: IDENTIFICATION & ISOLATION                                   │
  │ (Ensures per-document isolation with multi-tenant support)              │
  └─────────────────────────────────────────────────────────────────────────┘
  
  "_id": "doc-001:direct_parse",           ← Unique per document per source
  "owner_email": "user@example.com",       ← PARTITION KEY (multi-tenant)
  "document_id": "doc-001",                ← Document identifier
  "source": "direct_parse",                ← Extraction method
  
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ SECTION 1: TIMESTAMPS                                                   │
  │ (For audit trail and modification tracking)                             │
  └─────────────────────────────────────────────────────────────────────────┘
  
  "created_at": "2026-01-19T10:30:00Z",    ← When extracted
  "updated_at": "2026-01-19T10:35:00Z",    ← Last modification
  
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ SECTION 2: DOCUMENT METADATA                                            │
  │ (File information for uploaded document)                                │
  └─────────────────────────────────────────────────────────────────────────┘
  
  "document": {
    "file_name": "supplier_quotation.pdf",
    "file_type": "PDF",
    "file_size_bytes": 2048576,
    "uploaded_at": "2026-01-19T10:30:00Z",
    "file_hash": "abc123def456..."        ← For duplicate detection
  },
  
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ SECTION 3: RAW EXTRACTION DATA                                          │
  │ (Direct output from OCR/parsing, unchanged by user)                     │
  └─────────────────────────────────────────────────────────────────────────┘
  
  "extraction_data": {
    "text": "Complete extracted text content from document...",
    
    "tables": [
      {
        "table_id": "tbl-1",
        "rows": 10,
        "columns": 5,
        "data": [
          ["Col1", "Col2", "Col3", "Col4", "Col5"],
          ["Data1", "Data2", "Data3", "Data4", "Data5"],
          ...
        ]
      }
    ],
    
    "images": ["img-url-1", "img-url-2"],
    
    "key_value_pairs": {
      "supplier_name": "ABC Supplies Inc.",
      "quote_number": "QT-2026-001",
      "valid_until": "2026-02-19",
      "total_amount": "$15,250.00"
    },
    
    "metadata": {
      "document_type": "QUOTATION",
      "content_length": 15234,
      "language": "en",
      "pages": 3
    },
    
    "extraction_method": "direct_parse",
    "extraction_duration_ms": 2340
  },
  
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ SECTION 4: AI ANALYSIS SUMMARY                                          │
  │ (Generated after user review, enriches extraction with intelligence)     │
  └─────────────────────────────────────────────────────────────────────────┘
  
  "ai_summary": {
    "key_insights": "High-quality quotation from established supplier",
    
    "supplier_information": {
      "name": "ABC Supplies Inc.",
      "location": "USA",
      "established": 1995,
      "rating": 4.5,
      "reliability": "HIGH",
      "certifications": ["ISO 9001", "ISO 14001"]
    },
    
    "risk_factors": [
      {
        "risk_type": "pricing_volatility",
        "severity": "MEDIUM",        ← LOW | MEDIUM | HIGH | CRITICAL
        "description": "Price increased 15% from last quote",
        "mitigation": "Negotiate volume discounts"
      },
      {
        "risk_type": "supplier_concentration",
        "severity": "LOW",
        "description": "Single supplier for critical component",
        "mitigation": "Identify alternative suppliers"
      }
    ],
    
    "recommendations": [
      "Negotiate volume discounts for orders > $100K",
      "Verify compliance certifications are current",
      "Compare with at least 2 alternative suppliers",
      "Request extended payment terms"
    ],
    
    "confidence_scores": {
      "classifier": 0.98,    ← 0-1 (how confident in document type)
      "mapping": 0.95,       ← 0-1 (field extraction confidence)
      "inference": 0.92      ← 0-1 (business rule confidence)
    },
    
    "model_used": "gpt-4o-mini",
    "analysis_timestamp": "2026-01-19T10:33:00Z"
  },
  
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ SECTION 5: USER MODIFICATIONS                                           │
  │ (Corrections made by user, full audit trail)                            │
  └─────────────────────────────────────────────────────────────────────────┘
  
  "user_modifications": {
    "modifications": [
      {
        "original_field": "supplier_name",
        "original_value": "ABC Supplies Inc.",
        "modified_value": "ABC Supplies Incorporated",  ← User correction
        "modification_reason": "Correction for legal entity name",
        "modified_at": "2026-01-19T10:34:00Z",
        "modified_by": "user@example.com"
      },
      {
        "original_field": "total_amount",
        "original_value": "$15,250.00",
        "modified_value": "$15,250.00 (Confirmed with supplier)",
        "modification_reason": "Added verification note",
        "modified_at": "2026-01-19T10:34:30Z",
        "modified_by": "user@example.com"
      }
    ],
    "total_modifications": 2,
    "last_modified_at": "2026-01-19T10:34:30Z",
    "last_modified_by": "user@example.com"
  },
  
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ SECTION 6: CONVERSION PREFERENCES                                       │
  │ (User settings for export/download)                                     │
  └─────────────────────────────────────────────────────────────────────────┘
  
  "conversion_preferences": {
    "output_format": "pdf",           ← pdf | json | csv | xlsx
    "include_ai_summary": true,       ← Include risk analysis?
    "include_original_extraction": true,  ← Keep raw data?
    "include_user_modifications": true,   ← Include user edits?
    "timezone": "UTC",
    "language": "en",
    "custom_settings": {
      "logo_type": "full_color",
      "include_risk_matrix": true,
      "page_orientation": "portrait",
      "font_size": 11
    }
  },
  
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ SECTION 7: TRANSFORMED DOCUMENT DATA                                    │
  │ (Final output combining extraction + AI + user modifications)           │
  └─────────────────────────────────────────────────────────────────────────┘
  
  "transformed_data": {
    "document_data": {
      "supplier": {
        "name": "ABC Supplies Incorporated",  ← User-modified value
        "location": "USA",
        "email": "sales@abcsupplies.com",
        "certifications": ["ISO 9001", "ISO 14001"]
      },
      "quote": {
        "number": "QT-2026-001",
        "date": "2026-01-19",
        "valid_until": "2026-02-19",
        "items": [
          {
            "description": "Component A",
            "quantity": 1000,
            "unit_price": 12.50,
            "total": 12500.00
          },
          {
            "description": "Shipping & Handling",
            "quantity": 1,
            "unit_price": 750.00,
            "total": 750.00
          }
        ],
        "subtotal": 12500.00,
        "shipping": 750.00,
        "total": 13250.00
      }
    },
    
    "ai_summary_integrated": {
      "supplier_rating": 4.5,
      "reliability": "HIGH",
      "risk_summary": "MEDIUM - Pricing volatility",
      "key_recommendations": [
        "Negotiate volume discounts",
        "Compare with alternatives"
      ]
    },
    
    "user_modifications_applied": true,
    "transformation_id": "txf-001",
    "transformation_timestamp": "2026-01-19T10:34:30Z",
    "transformation_method": "direct_parse_with_ai_enrichment"
  },
  
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ SECTION 8: DOWNLOAD INFORMATION & TRACKING                              │
  │ (Usage analytics and export URLs)                                       │
  └─────────────────────────────────────────────────────────────────────────┘
  
  "download_info": {
    "download_count": 2,                    ← How many times downloaded
    "last_downloaded_at": "2026-01-19T14:20:00Z",
    "download_urls": {
      "pdf": "https://storage.example.com/export-001.pdf",
      "json": "https://storage.example.com/export-001.json",
      "xlsx": "https://storage.example.com/export-001.xlsx"
    },
    "export_status": "ready"                ← pending | processing | ready | failed
  },
  
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ SECTION 9: USER FEEDBACK                                                │
  │ (Quality assessment for continuous improvement)                         │
  └─────────────────────────────────────────────────────────────────────────┘
  
  "feedback": {
    "quality_rating": 5,                    ← 1-5 (overall quality)
    "accuracy_rating": 5,                   ← 1-5 (extraction accuracy)
    "completeness_rating": 4,               ← 1-5 (all data captured)
    "comments": "Excellent extraction quality, very accurate data.",
    "feedback_type": "positive",            ← positive | negative | neutral | suggestion
    "submitted_at": "2026-01-19T15:00:00Z",
    "submitted_by": "user@example.com"
  },
  
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ SECTION 10: STATUS & METADATA                                           │
  │ (Overall document state and custom tags)                                │
  └─────────────────────────────────────────────────────────────────────────┘
  
  "status": "extracted",                   ← extracted | reviewed | transformed | exported | archived
  "tags": [                                ← Searchable tags
    "supplier",
    "quotation",
    "high-value",
    "verified"
  ],
  "custom_metadata": {
    "department": "procurement",
    "project_id": "proj-2026-001",
    "approval_status": "pending"
  }
}

================================================================================
KEY POINTS
================================================================================

1. COMPLETE ISOLATION:
   Each document's extraction is stored separately by document_id
   Multiple documents uploaded together DON'T mix their data

2. MULTI-TENANT SAFETY:
   Partition key /owner_email ensures users can't see each other's data
   Queries automatically scoped to owner's partition

3. MULTIPLE EXTRACTION SOURCES:
   Same document can be processed multiple ways (direct_parse, ocr, azure_di)
   Compare results: doc-001:direct_parse vs doc-001:ocr vs doc-001:azure_di

4. AUDIT TRAIL:
   Every modification tracked with timestamp and user
   Can see exactly what changed and when

5. FLEXIBLE UPDATES:
   Update AI summary separately from user modifications
   Update feedback independently from preferences
   Each section updateable without touching others

6. FULL LIFECYCLE:
   Extraction → AI Summary → User Edits → Transformation → Download → Feedback
   Complete journey from upload to usage captured

================================================================================
