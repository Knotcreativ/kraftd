"""
Test script to validate the local document extractor with a sample document.
"""

import json
import requests
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Create a sample RFQ/Quotation PDF for testing
def create_sample_pdf():
    """Generate a simple PDF with procurement content."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 750, "REQUEST FOR QUOTATION (RFQ)")
    
    # Metadata
    c.setFont("Helvetica", 10)
    c.drawString(50, 720, "Document #: RFQ-2026-001")
    c.drawString(50, 705, "Issue Date: January 15, 2026")
    c.drawString(50, 690, "Submission Deadline: January 22, 2026")
    
    # Issuer Info
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, 660, "ISSUER:")
    c.setFont("Helvetica", 10)
    c.drawString(50, 645, "Kraftd Engineering LLC")
    c.drawString(50, 630, "Phone: +966-12-123-4567")
    c.drawString(50, 615, "Email: procurement@kraftd.com")
    
    # Project Info
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, 585, "PROJECT:")
    c.setFont("Helvetica", 10)
    c.drawString(50, 570, "Dammam Industrial Expansion Project")
    c.drawString(50, 555, "Location: Dammam, Saudi Arabia")
    
    # Line Items Table
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, 525, "REQUIRED ITEMS:")
    
    # Table header
    c.setFont("Helvetica-Bold", 9)
    y = 510
    c.drawString(50, y, "Item #")
    c.drawString(100, y, "Description")
    c.drawString(300, y, "Qty")
    c.drawString(350, y, "Unit")
    c.drawString(400, y, "Unit Price (SAR)")
    
    # Line 1
    c.setFont("Helvetica", 9)
    y = 495
    c.drawString(50, y, "1")
    c.drawString(100, y, "Structural Steel Beams (Grade 50)")
    c.drawString(300, y, "500")
    c.drawString(350, y, "MT")
    c.drawString(400, y, "4,500.00")
    
    # Line 2
    y = 480
    c.drawString(50, y, "2")
    c.drawString(100, y, "Reinforced Concrete (Ready Mix)")
    c.drawString(300, y, "250")
    c.drawString(350, y, "M3")
    c.drawString(400, y, "850.00")
    
    # Line 3
    y = 465
    c.drawString(50, y, "3")
    c.drawString(100, y, "Installation Labor (20 Weeks)")
    c.drawString(300, y, "800")
    c.drawString(350, y, "Hours")
    c.drawString(400, y, "125.00")
    
    # Payment Terms
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, 435, "TERMS:")
    c.setFont("Helvetica", 9)
    c.drawString(50, 420, "Currency: SAR (Saudi Riyal)")
    c.drawString(50, 405, "Payment: 50% upon order, 50% upon delivery")
    c.drawString(50, 390, "Delivery: FOB Dammam")
    c.drawString(50, 375, "VAT: Applicable (15%)")
    
    c.save()
    buffer.seek(0)
    return buffer

# Save test PDF to file
def save_test_pdf():
    pdf_buffer = create_sample_pdf()
    pdf_path = Path("test_document.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_buffer.getvalue())
    return pdf_path

# Test the API
def test_api():
    base_url = "http://127.0.0.1:8000"
    
    # Save test document
    print("Creating test PDF...")
    pdf_path = save_test_pdf()
    print(f"✓ Test PDF created: {pdf_path}")
    
    # Test 1: Upload document
    print("\n=== TEST 1: Document Upload ===")
    with open(pdf_path, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{base_url}/docs/upload", files=files)
    
    if response.status_code == 200:
        upload_result = response.json()
        document_id = upload_result.get("document_id")
        print(f"✓ Upload successful!")
        print(f"  Document ID: {document_id}")
        print(f"  File path: {upload_result.get('file_path')}")
        print(f"  Status: {upload_result.get('status')}")
    else:
        print(f"✗ Upload failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return
    
    # Test 2: Extract intelligence
    print("\n=== TEST 2: Document Extraction ===")
    response = requests.post(f"{base_url}/extract?document_id={document_id}")
    
    if response.status_code == 200:
        extracted_data = response.json()
        print(f"✓ Extraction successful!")
        print(f"\n  Document Type: {extracted_data.get('document_type')}")
        print(f"  Extraction Method: {extracted_data.get('extraction_method')}")
        
        # Metadata
        metadata = extracted_data.get("metadata", {})
        print(f"\n  METADATA:")
        print(f"    Document #: {metadata.get('document_number')}")
        print(f"    Issue Date: {metadata.get('issue_date')}")
        
        # Parties
        parties = extracted_data.get("parties", {})
        if parties.get("issuer"):
            issuer = parties["issuer"]
            print(f"\n  ISSUER:")
            print(f"    Name: {issuer.get('name')}")
            print(f"    Phone: {issuer.get('contact', {}).get('phone')}")
            print(f"    Email: {issuer.get('contact', {}).get('email')}")
        
        # Project Context
        project = extracted_data.get("project_context", {})
        print(f"\n  PROJECT:")
        print(f"    Name: {project.get('project_name')}")
        print(f"    Location: {project.get('location')}")
        
        # Line Items
        line_items = extracted_data.get("line_items", [])
        if line_items:
            print(f"\n  LINE ITEMS ({len(line_items)}):")
            for i, item in enumerate(line_items, 1):
                print(f"    {i}. {item.get('description')}")
                print(f"       Qty: {item.get('quantity')} {item.get('unit')}")
                print(f"       Unit Price: {item.get('unit_price')} {item.get('currency')}")
                if item.get('data_quality'):
                    print(f"       Confidence: {item['data_quality'].get('accuracy_score', 0)*100:.0f}%")
        else:
            print(f"\n  LINE ITEMS: None extracted")
        
        # Commercial Terms
        terms = extracted_data.get("commercial_terms", {})
        print(f"\n  COMMERCIAL TERMS:")
        print(f"    Currency: {terms.get('currency')}")
        print(f"    VAT Rate: {terms.get('vat_rate')}%")
        print(f"    Incoterms: {terms.get('incoterms')}")
        print(f"    Payment Terms: {terms.get('payment_terms')}")
        
        # Data Quality
        quality = extracted_data.get("data_quality", {})
        print(f"\n  DATA QUALITY:")
        print(f"    Completeness: {quality.get('completeness_percentage', 0):.0f}%")
        print(f"    Accuracy: {quality.get('accuracy_score', 0)*100:.0f}%")
        print(f"    Issues: {quality.get('quality_issues', [])}")
        
    else:
        print(f"✗ Extraction failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return
    
    # Test 3: Get document details
    print("\n=== TEST 3: Get Document Details ===")
    response = requests.get(f"{base_url}/documents/{document_id}")
    
    if response.status_code == 200:
        doc = response.json()
        print(f"✓ Retrieved document successfully!")
        print(f"  Status: {doc.get('status')}")
        print(f"  Created: {doc.get('created_at')}")
        print(f"  Last Updated: {doc.get('updated_at')}")
    else:
        print(f"✗ Failed to get document: {response.status_code}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
