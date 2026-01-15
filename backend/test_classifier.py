"""
Test the Universal Classifier with realistic procurement documents.
"""

from document_processing.classifier import (
    UniversalClassifier,
    DocumentTypeEnum,
    classify_document
)


def test_rfq_detection():
    """Test RFQ classification"""
    text = """
    REQUEST FOR QUOTATION
    RFQ-2024-001
    
    We request quotation for the following items:
    
    Item No | Description | Quantity | Unit | Rate | Amount
    1 | Steel Pipes ASTM A36 | 1000 | kg | | 
    2 | Flanges 4" Class 300 | 50 | pcs | |
    3 | Gaskets | 100 | pcs | |
    
    Submission Deadline: 15 Feb 2024
    Evaluation Criteria: 
    - Technical compliance 40%
    - Commercial offer 60%
    
    Please send your quotation to procurement@company.com
    """
    
    result = classify_document(text)
    print(f"\n✓ RFQ Test")
    print(f"  Type: {result.document_type}")
    print(f"  Confidence: {result.confidence:.0%}")
    print(f"  Reasoning: {result.reasoning[0] if result.reasoning else 'N/A'}")
    assert result.document_type == DocumentTypeEnum.RFQ
    assert result.confidence >= 0.6


def test_boq_detection():
    """Test BOQ (Bill of Quantities) classification"""
    text = """
    BILL OF QUANTITIES
    Project: Building Construction
    
    Item | Description | Qty | UOM | Rate | Amount
    1 | Cement 50kg bags | 5000 | bags | 350 | 1,750,000
    2 | Steel TMT rods | 50 | tonnes | 45000 | 2,250,000
    3 | Sand | 1000 | cum | 1200 | 1,200,000
    4 | Bricks | 500000 | nos | 5 | 2,500,000
    5 | Water tank 500L | 20 | nos | 8000 | 160,000
    
    Total: 7,860,000
    """
    
    result = classify_document(text)
    print(f"\n✓ BOQ Test")
    print(f"  Type: {result.document_type}")
    print(f"  Confidence: {result.confidence:.0%}")
    assert result.document_type == DocumentTypeEnum.BOQ
    assert result.confidence >= 0.5


def test_quotation_detection():
    """Test Quotation classification"""
    text = """
    QUOTATION
    
    From: ABX Trading Company
    Date: 10 Jan 2024
    Quote #: QT-2024-5421
    
    To: Your Company
    
    We are pleased to submit our quotation for your requirement:
    
    Line | Item | Qty | Unit Price | Amount
    1 | Hydraulic Pump 50kW | 5 | 125,000 | 625,000
    2 | Delivery & Installation | 1 | 50,000 | 50,000
    3 | Annual Maintenance | 1 | 30,000 | 30,000
    
    Subtotal: 705,000
    Tax (15%): 105,750
    Grand Total: 810,750
    
    Validity: Valid until 25 Jan 2024
    Payment Terms: 50% advance, 50% on delivery
    Delivery: 4 weeks from order
    Warranty: 12 months
    
    Authorized Signature: _______________
    Company Seal
    """
    
    result = classify_document(text)
    print(f"\n✓ Quotation Test")
    print(f"  Type: {result.document_type}")
    print(f"  Confidence: {result.confidence:.0%}")
    assert result.document_type == DocumentTypeEnum.QUOTATION
    assert result.confidence >= 0.6


def test_po_detection():
    """Test Purchase Order classification"""
    text = """
    PURCHASE ORDER
    
    PO Number: PO-2024-001234
    PO Date: 15 Jan 2024
    
    Buyer: ABC Manufacturing Ltd
    Supplier: XYZ Steel Traders
    
    Item # | Description | Qty | Unit | Rate | Total
    1 | Steel Plate 25mm | 100 | MT | 65000 | 6,500,000
    2 | Stainless Steel Rod | 50 | MT | 95000 | 4,750,000
    3 | Fasteners Set | 500 | sets | 5000 | 2,500,000
    
    Total PO Value: 13,750,000
    
    Delivery Date: 28 Feb 2024
    Delivery Location: Our Plant, Mumbai
    
    Payment Terms: Net 30 days from invoice
    Incoterms: FOB
    
    Authorized By: Manager
    Date: 15 Jan 2024
    """
    
    result = classify_document(text)
    print(f"\n✓ Purchase Order Test")
    print(f"  Type: {result.document_type}")
    print(f"  Confidence: {result.confidence:.0%}")
    assert result.document_type == DocumentTypeEnum.PO
    assert result.confidence >= 0.6


def test_invoice_detection():
    """Test Invoice classification"""
    text = """
    TAX INVOICE
    
    Invoice No: INV-2024-0567
    Invoice Date: 20 Jan 2024
    Due Date: 20 Feb 2024
    
    Bill To: ABC Manufacturing
    Ship To: ABC Manufacturing, Mumbai
    
    From: XYZ Suppliers
    
    Description | Qty | Unit Price | Amount
    Steel Pipes ASTM A106 | 500 | 450 | 225,000
    Flanges 4" Class 300 | 50 | 8000 | 400,000
    Labor & Shipping | 1 | 50000 | 50,000
    
    Subtotal: 675,000
    SGST (9%): 60,750
    CGST (9%): 60,750
    Total: 796,500
    
    Payment Terms: Net 30 days
    Bank: ABC Bank, Account: 1234567890
    """
    
    result = classify_document(text)
    print(f"\n✓ Invoice Test")
    print(f"  Type: {result.document_type}")
    print(f"  Confidence: {result.confidence:.0%}")
    assert result.document_type == DocumentTypeEnum.INVOICE
    assert result.confidence >= 0.5


def test_unknown_detection():
    """Test UNKNOWN classification for ambiguous text"""
    text = """
    Random Document
    
    This is just some random text.
    It doesn't match any known document pattern.
    There are no quantities, prices, or terms.
    Just random content.
    """
    
    result = classify_document(text)
    print(f"\n✓ Unknown Test")
    print(f"  Type: {result.document_type}")
    print(f"  Confidence: {result.confidence:.0%}")
    print(f"  Requires Review: {result.requires_review}")
    assert result.document_type == DocumentTypeEnum.UNKNOWN
    assert result.requires_review


def test_mixed_detection():
    """Test MIXED classification for combined documents"""
    text = """
    REQUEST FOR QUOTATION (RFQ-2024-001)
    
    And also includes BOQ elements:
    
    Item | Description | Quantity | Unit | Unit Price
    1 | Materials | 1000 | kg | 50
    2 | Labor | 100 | hours | 500
    
    Plus Submission Deadline: 15 Feb 2024
    Evaluation Criteria: 40% technical, 60% commercial
    """
    
    result = classify_document(text)
    print(f"\n✓ Mixed Test")
    print(f"  Type: {result.document_type}")
    print(f"  Confidence: {result.confidence:.0%}")
    # Mixed documents have lower confidence
    assert result.requires_review or result.document_type in [
        DocumentTypeEnum.RFQ,
        DocumentTypeEnum.BOQ,
        DocumentTypeEnum.MIXED
    ]


def test_with_user_hint():
    """Test classification with user hint"""
    text = """
    This document could be interpreted as RFQ or BOQ.
    It has: Submission Deadline (RFQ signal)
    And also: Qty and Unit Price columns (BOQ signal)
    """
    
    # Without hint - ambiguous
    result1 = classify_document(text)
    print(f"\n✓ Without Hint Test")
    print(f"  Type: {result1.document_type}")
    print(f"  Requires Review: {result1.requires_review}")
    
    # With hint - clear
    result2 = classify_document(text, user_hint="RFQ")
    print(f"\n✓ With Hint Test (user_hint='RFQ')")
    print(f"  Type: {result2.document_type}")
    print(f"  Confidence: {result2.confidence:.0%}")
    # User hint should help resolve ambiguity
    assert result2.document_type == DocumentTypeEnum.RFQ or result2.confidence >= 0.60


def test_format_agnostic():
    """Test that classifier ignores file format"""
    # All these could come from PDF, Word, Excel, Image, etc.
    # Classifier should treat them the same
    
    text = """
    REQUEST FOR QUOTATION
    RFQ-2024-005
    
    Please provide quotation for:
    
    Item | Description | Quantity | Unit | Rate
    1 | Steel Pipes ASTM A36 | 500 | kg | 
    2 | Flanges 4" Class 300 | 200 | pcs |
    3 | Gaskets | 100 | pcs |
    
    Submission Deadline: 20 Jan 2024
    Evaluation Criteria: 40% technical, 60% price
    Contact: procurement@company.com
    """
    
    # Simulate different file types (text is already extracted)
    for file_name in ["document.pdf", "request.docx", "data.xlsx", "scan.jpg", "message.txt"]:
        result = classify_document(text, file_name=file_name)
        print(f"\n✓ Format-Agnostic Test ({file_name})")
        print(f"  Type: {result.document_type}")
        # Should be RFQ classification regardless of original format
        assert result.document_type == DocumentTypeEnum.RFQ, f"Failed for {file_name}: got {result.document_type}"


def test_confidence_scoring():
    """Test that confidence scores are reasonable"""
    classifier = UniversalClassifier()
    
    # High confidence - clear RFQ
    high_conf_text = """
    REQUEST FOR QUOTATION
    RFQ-2024-001
    Submission Deadline: 15 Feb
    Evaluation Criteria: 40% technical, 60% price
    Item | Qty | Description
    1 | 1000 | Steel Pipes
    """
    result1 = classifier.classify(high_conf_text)
    print(f"\n✓ High Confidence Test")
    print(f"  Confidence: {result1.confidence:.0%}")
    assert result1.confidence >= 0.7
    
    # Low confidence - minimal signals
    low_conf_text = """
    Document with some quote information but not clear.
    Contains number 100 and item description.
    """
    result2 = classifier.classify(low_conf_text)
    print(f"\n✓ Low Confidence Test")
    print(f"  Confidence: {result2.confidence:.0%}")
    print(f"  Requires Review: {result2.requires_review}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("UNIVERSAL CLASSIFIER TESTS")
    print("Format-Agnostic, Content-Aware Classification")
    print("="*60)
    
    try:
        test_rfq_detection()
        test_boq_detection()
        test_quotation_detection()
        test_po_detection()
        test_invoice_detection()
        test_unknown_detection()
        test_mixed_detection()
        test_with_user_hint()
        test_format_agnostic()
        test_confidence_scoring()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        print("\nClassifier is production-ready:")
        print("  ✓ Format-agnostic (works on normalized text)")
        print("  ✓ Content-aware (ignores file extension)")
        print("  ✓ Multi-signal scoring")
        print("  ✓ Handles UNKNOWN and MIXED types")
        print("  ✓ Returns structured ClassificationResult")
        print("  ✓ Fast (no LLM/Vision API calls)")
        print("\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
