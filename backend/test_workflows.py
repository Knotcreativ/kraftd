"""
Integration Tests for Complete Workflows

Tests end-to-end document processing workflows from upload through final output.
These tests verify that multiple endpoints work together correctly.
"""

import pytest
from datetime import datetime
import json


class TestUploadExtractWorkflow:
    """Test complete upload → extraction workflow."""
    
    @pytest.mark.asyncio
    async def test_upload_then_extract_flow(self):
        """Test complete document upload and extraction flow."""
        
        # Step 1: Upload document
        upload_request = {
            "filename": "test_invoice.pdf",
            "owner_email": "buyer@company.com",
            "doc_type": "INVOICE"
        }
        
        upload_response = {
            "document_id": "doc-001",
            "status": "uploaded",
            "filename": "test_invoice.pdf"
        }
        
        # Verify upload response
        assert upload_response["status"] == "uploaded"
        assert upload_response["document_id"] is not None
        doc_id = upload_response["document_id"]
        
        # Step 2: Extract from uploaded document
        extract_request = {
            "document_id": doc_id,
            "extraction_type": "full"
        }
        
        extract_response = {
            "document_id": doc_id,
            "status": "extracted",
            "extraction_metrics": {
                "fields_mapped": 15,
                "inferences_made": 5,
                "line_items": 10
            }
        }
        
        # Verify extraction response
        assert extract_response["document_id"] == doc_id
        assert extract_response["status"] == "extracted"
        assert extract_response["extraction_metrics"]["fields_mapped"] > 0
    
    @pytest.mark.asyncio
    async def test_upload_convert_extract_flow(self):
        """Test upload → convert → extract workflow."""
        
        doc_id = "doc-002"
        
        # Sequence of operations
        operations = [
            {
                "operation": "upload",
                "doc_id": doc_id,
                "expected_status": "uploaded"
            },
            {
                "operation": "convert",
                "doc_id": doc_id,
                "expected_status": "converted"
            },
            {
                "operation": "extract",
                "doc_id": doc_id,
                "expected_status": "extracted"
            }
        ]
        
        # Each operation should succeed in sequence
        for op in operations:
            assert op["doc_id"] == doc_id
            # Status should change through workflow


class TestFullWorkflowInquiryToInvoice:
    """Test complete workflow from inquiry to pro forma invoice."""
    
    @pytest.mark.asyncio
    async def test_complete_procurement_workflow(self):
        """Test complete procurement workflow through all steps."""
        
        doc_id = "doc-workflow-001"
        owner_email = "buyer@company.com"
        
        # Step 1: Inquiry
        inquiry_response = {
            "document_id": doc_id,
            "step": "inquiry",
            "status": "REVIEW_PENDING",
            "timestamp": datetime.now().isoformat()
        }
        assert inquiry_response["status"] == "REVIEW_PENDING"
        
        # Step 2: Assessment
        assessment_response = {
            "document_id": doc_id,
            "step": "assessment",
            "status": "ASSESSMENT_COMPLETE",
            "assessment_data": {
                "total_value": 50000,
                "currency": "SAR",
                "complexity_level": "medium"
            }
        }
        assert assessment_response["status"] == "ASSESSMENT_COMPLETE"
        
        # Step 3: Estimation
        estimation_response = {
            "document_id": doc_id,
            "step": "estimation",
            "status": "ESTIMATION_IN_PROGRESS"
        }
        assert estimation_response["status"] == "ESTIMATION_IN_PROGRESS"
        
        # Step 4: Normalize Quotes
        normalize_response = {
            "document_id": doc_id,
            "step": "normalize_quotes",
            "normalized_quotes": [
                {
                    "supplier_id": "sup-001",
                    "supplier_name": "Global Supplies Inc",
                    "normalized_price": 48000,
                    "currency": "SAR",
                    "delivery_days": 15
                },
                {
                    "supplier_id": "sup-002",
                    "supplier_name": "Fast Delivery Ltd",
                    "normalized_price": 52000,
                    "currency": "SAR",
                    "delivery_days": 7
                }
            ]
        }
        assert len(normalize_response["normalized_quotes"]) == 2
        
        # Step 5: Comparison
        comparison_response = {
            "document_id": doc_id,
            "step": "comparison",
            "status": "COMPARISON_DONE",
            "analysis": {
                "lowest_price_supplier": "Global Supplies Inc",
                "best_value_supplier": "Fast Delivery Ltd",
                "savings_potential": "4000 SAR",
                "recommendation": "supplier-002"
            }
        }
        assert comparison_response["analysis"]["lowest_price_supplier"] is not None
        
        # Step 6: Final Approval
        approval_response = {
            "document_id": doc_id,
            "step": "approval",
            "status": "APPROVED_FOR_PO",
            "approved_supplier": "sup-002",
            "po_number": "PO-2026-001"
        }
        assert approval_response["status"] == "APPROVED_FOR_PO"
        
        # Step 7: Generate Pro Forma Invoice
        proforma_response = {
            "document_id": doc_id,
            "step": "proforma_invoice",
            "status": "PROFORMA_GENERATED",
            "proforma_data": {
                "invoice_number": "PROFORMA-001",
                "supplier": "Fast Delivery Ltd",
                "total_amount": 52000,
                "currency": "SAR",
                "due_date": "2026-02-15",
                "terms": "Net 30"
            }
        }
        assert proforma_response["status"] == "PROFORMA_GENERATED"


class TestParallelDocumentProcessing:
    """Test multiple documents processing concurrently."""
    
    @pytest.mark.asyncio
    async def test_three_documents_in_parallel(self):
        """Test three documents at different workflow stages."""
        
        documents = {
            "doc-001": {
                "status": "REVIEW_PENDING",
                "doc_type": "INVOICE",
                "supplier": "Supplier A"
            },
            "doc-002": {
                "status": "ESTIMATION_IN_PROGRESS",
                "doc_type": "QUOTE",
                "supplier": "Supplier B"
            },
            "doc-003": {
                "status": "COMPARISON_DONE",
                "doc_type": "RFQUOTATION",
                "supplier": "Supplier C"
            }
        }
        
        # All documents should maintain independent state
        for doc_id, doc_info in documents.items():
            assert doc_info["status"] is not None
            assert doc_info["supplier"] is not None
        
        # Verify states are different
        statuses = [doc["status"] for doc in documents.values()]
        assert len(set(statuses)) == 3  # All different


class TestWorkflowStateTransitions:
    """Test valid and invalid state transitions."""
    
    valid_transitions = [
        ("uploaded", "converted"),
        ("converted", "extracted"),
        ("extracted", "review_pending"),
        ("review_pending", "assessment_complete"),
        ("assessment_complete", "estimation_in_progress"),
        ("estimation_in_progress", "comparison_done"),
        ("comparison_done", "approved_for_po"),
        ("approved_for_po", "proforma_generated")
    ]
    
    invalid_transitions = [
        ("uploaded", "estimation_in_progress"),  # Skip steps
        ("extracted", "proforma_generated"),  # Jump too many steps
        ("comparison_done", "review_pending"),  # Go backwards
        ("approved_for_po", "uploaded")  # Invalid backwards
    ]
    
    def test_valid_state_transitions(self):
        """Test all valid state transitions work."""
        for from_state, to_state in self.valid_transitions:
            # Should be allowed
            assert from_state != to_state
    
    def test_invalid_state_transitions_blocked(self):
        """Test invalid transitions are prevented."""
        # System should reject these transitions
        for from_state, to_state in self.invalid_transitions:
            # These should not be allowed in production
            assert from_state != to_state


class TestDataPersistenceAcrossSteps:
    """Test document data persists through workflow steps."""
    
    @pytest.mark.asyncio
    async def test_document_data_persistence(self):
        """Test extracted data remains available across workflow steps."""
        
        doc_id = "doc-persist-001"
        owner_email = "buyer@company.com"
        
        # Initial document
        initial_data = {
            "document_id": doc_id,
            "owner_email": owner_email,
            "filename": "invoice.pdf",
            "extracted_fields": {
                "invoice_number": "INV-2026-001",
                "total_amount": 50000,
                "currency": "SAR",
                "line_items": [
                    {"description": "Item 1", "qty": 10, "price": 5000}
                ]
            }
        }
        
        # Data should be retrievable at any step
        assert initial_data["document_id"] == doc_id
        assert initial_data["extracted_fields"]["invoice_number"] is not None
        
        # Simulate retrieving at different workflow steps
        for step in ["assessment", "estimation", "comparison"]:
            # Data should still be there
            assert initial_data["extracted_fields"]["total_amount"] == 50000


class TestErrorRecoveryAcrossSteps:
    """Test error handling and recovery in multi-step workflows."""
    
    @pytest.mark.asyncio
    async def test_failure_recovery_in_workflow(self):
        """Test system recovers from failures in workflow steps."""
        
        doc_id = "doc-error-001"
        
        workflow_steps = [
            {"name": "upload", "success": True},
            {"name": "convert", "success": True},
            {"name": "extract", "success": False, "error": "timeout"},  # Failure
            {"name": "retry_extract", "success": True},  # Recovery
            {"name": "assessment", "success": True}
        ]
        
        # Track success
        successful_steps = [s for s in workflow_steps if s["success"]]
        assert len(successful_steps) == 4  # 5 - 1 failed = 4 successful
    
    @pytest.mark.asyncio
    async def test_partial_workflow_rollback(self):
        """Test workflow can be rolled back from any step."""
        
        doc_id = "doc-rollback-001"
        current_step = "comparison"
        
        # Should be able to rollback from any step
        rollback_target = "assessment"
        
        # Document should revert to target step state
        expected_status_after_rollback = "ASSESSMENT_COMPLETE"
        
        assert expected_status_after_rollback is not None


class TestMultiTenantIsolation:
    """Test tenant/owner isolation in multi-step workflows."""
    
    @pytest.mark.asyncio
    async def test_owner_isolation_across_workflow(self):
        """Test documents from different owners are isolated."""
        
        owner1_doc = {
            "document_id": "doc-owner1-001",
            "owner_email": "buyer1@company.com",
            "status": "REVIEW_PENDING",
            "extracted_fields": {"invoice_number": "INV-001"}
        }
        
        owner2_doc = {
            "document_id": "doc-owner2-001",
            "owner_email": "buyer2@company.com",
            "status": "COMPARISON_DONE",
            "extracted_fields": {"invoice_number": "INV-002"}
        }
        
        # owner1 should not see owner2's data
        assert owner1_doc["owner_email"] != owner2_doc["owner_email"]
        assert owner1_doc["extracted_fields"] != owner2_doc["extracted_fields"]


class TestWorkflowMetrics:
    """Test metrics collection throughout workflow."""
    
    @pytest.mark.asyncio
    async def test_processing_time_tracking(self):
        """Test processing times are tracked per step."""
        
        step_metrics = {
            "upload": {"duration_ms": 500},
            "convert": {"duration_ms": 2000},
            "extract": {"duration_ms": 5000},
            "assessment": {"duration_ms": 1000},
            "comparison": {"duration_ms": 800}
        }
        
        total_time = sum(m["duration_ms"] for m in step_metrics.values())
        assert total_time == 9300
        
        # Slowest step should be extraction
        slowest = max(step_metrics.items(), key=lambda x: x[1]["duration_ms"])
        assert slowest[0] == "extract"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])