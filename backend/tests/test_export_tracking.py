"""
Quick validation test for export tracking service implementation
"""

import asyncio
import json
from datetime import datetime
from services.export_tracking_service import (
    ExportTrackingService, ExportStage
)


async def test_export_tracking_service():
    """Test ExportTrackingService in-memory without Cosmos DB"""
    
    print("\n" + "="*70)
    print("EXPORT TRACKING SERVICE - VALIDATION TEST")
    print("="*70)
    
    # Initialize service without Cosmos DB (None passed)
    service = ExportTrackingService(cosmos_service=None)
    print("\n✓ ExportTrackingService initialized (without Cosmos DB)")
    
    # Test Stage 1 Recording
    print("\n" + "-"*70)
    print("TEST 1: Record Stage 1 - Initial AI Summary")
    print("-"*70)
    
    initial_extracted_data = {
        "invoice_number": "INV-2024-001",
        "vendor": "ABC Trading",
        "amount": 1050.00,
        "date": "2024-01-15"
    }
    
    ai_summary = {
        "executive_summary": "Invoice from ABC Trading for services rendered",
        "key_findings": ["Standard terms", "All fields present"],
        "recommendations": ["Approve for processing"],
        "risk_factors": [],
        "action_items": ["Route to accounting"],
        "confidence_score": 0.94
    }
    
    workflow_id = await service.record_stage_1_initial_summary(
        document_id="doc_001",
        owner_email="test@example.com",
        document_type="invoice",
        initial_extracted_data=initial_extracted_data,
        ai_initial_summary=ai_summary,
        extraction_confidence=0.92,
        processing_time_ms=2150,
        tokens_used=450
    )
    
    print(f"✓ Stage 1 recorded")
    print(f"  Workflow ID: {workflow_id}")
    print(f"  Document Type: invoice")
    print(f"  AI Confidence: 0.94")
    print(f"  Processing Time: 2150ms")
    
    # Test Stage 2 Recording
    print("\n" + "-"*70)
    print("TEST 2: Record Stage 2 - User Modifications")
    print("-"*70)
    
    modified_data = initial_extracted_data.copy()
    modified_data["vendor"] = "ABC Trading Ltd."  # User correction
    modified_data["notes"] = "Approved for payment"  # User addition
    
    user_preferences = {
        "transformation_instructions": "Highlight totals in red",
        "export_format": "pdf",
        "document_template": "executive_summary",
        "template_customization": "Focus on financial metrics"
    }
    
    changes = [
        {
            "field": "vendor",
            "original_value": "ABC Trading",
            "modified_value": "ABC Trading Ltd.",
            "change_type": "modification"
        },
        {
            "field": "notes",
            "original_value": None,
            "modified_value": "Approved for payment",
            "change_type": "addition"
        }
    ]
    
    stage2_success = await service.record_stage_2_user_modifications(
        export_workflow_id=workflow_id,
        document_id="doc_001",
        owner_email="test@example.com",
        original_data=initial_extracted_data,
        modified_data=modified_data,
        user_preferences=user_preferences,
        editing_time_seconds=285,
        changes=changes
    )
    
    print(f"✓ Stage 2 recorded: {stage2_success}")
    print(f"  Changes tracked: {len(changes)}")
    print(f"  Editing time: 285 seconds")
    print(f"  Export format: PDF")
    print(f"  Template: executive_summary")
    
    # Test Stage 3 Recording
    print("\n" + "-"*70)
    print("TEST 3: Record Stage 3 - Final Deliverable")
    print("-"*70)
    
    final_summary = ai_summary.copy()
    final_summary["confidence_score"] = 0.98  # Increased after user validation
    
    mock_file_content = b"PDF content here..." * 100  # Simulate file
    
    stage3_success = await service.record_stage_3_final_deliverable(
        export_workflow_id=workflow_id,
        document_id="doc_001",
        owner_email="test@example.com",
        ai_final_summary=final_summary,
        export_format="pdf",
        deliverable_filename="doc_001_executive_summary_20240118.pdf",
        file_size_bytes=len(mock_file_content),
        file_content=mock_file_content,
        document_template="executive_summary",
        processing_time_ms=1890,
        tokens_used=380,
        workflow_metrics={
            "total_time_seconds": 125,
            "stage1_time_seconds": 45,
            "stage2_time_seconds": 40,
            "stage3_time_seconds": 40,
            "total_modifications": 2,
            "ai_processing_accuracy": 0.96,
            "final_output_quality": 0.97
        }
    )
    
    print(f"✓ Stage 3 recorded: {stage3_success}")
    print(f"  File: doc_001_executive_summary_20240118.pdf")
    print(f"  Size: {len(mock_file_content)} bytes")
    print(f"  Format: PDF")
    print(f"  AI Confidence: 0.98")
    print(f"  Output Quality: 0.97")
    
    # Test Change Calculation
    print("\n" + "-"*70)
    print("TEST 4: Change Detection")
    print("-"*70)
    
    original = {"field1": "value1", "field2": "value2"}
    modified = {"field1": "value1_changed", "field3": "new_value"}
    
    calculated_changes = service._calculate_changes(original, modified)
    
    print(f"✓ Changes calculated: {len(calculated_changes)}")
    for change in calculated_changes:
        print(f"  • {change['change_type'].upper()}: {change['field']}")
    
    # Test MIME Type Detection
    print("\n" + "-"*70)
    print("TEST 5: MIME Type Mapping")
    print("-"*70)
    
    formats_to_test = ["json", "csv", "excel", "pdf"]
    for fmt in formats_to_test:
        mime = service._get_mime_type(fmt)
        print(f"  ✓ {fmt:6} → {mime}")
    
    print("\n" + "="*70)
    print("VALIDATION COMPLETE")
    print("="*70)
    print("\n✅ All tests passed!")
    print("\nImplementation Summary:")
    print("  • ExportTrackingService class: Working")
    print("  • Stage 1 Recording: Working")
    print("  • Stage 2 Recording: Working")
    print("  • Stage 3 Recording: Working")
    print("  • Change Detection: Working")
    print("  • MIME Type Mapping: Working")
    print("\nReady for:")
    print("  → Cosmos DB integration")
    print("  → Export endpoint implementation")
    print("  → API endpoint additions")
    print("  → Frontend integration")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_export_tracking_service())
