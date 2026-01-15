"""
Quick test to verify Azure Document Intelligence is working
"""

import requests
import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Create a sample RFQ PDF for testing
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

# Test the API
def test_azure_extraction():
    base_url = "http://127.0.0.1:8001"  # Changed to port 8001
    
    # Save test document
    print("Creating test PDF...")
    pdf_buffer = create_sample_pdf()
    pdf_path = Path("azure_test_document.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_buffer.getvalue())
    print(f"✓ Test PDF created: {pdf_path}\n")
    
    # Upload document
    print("=== STEP 1: Upload Document ===")
    with open(pdf_path, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{base_url}/docs/upload", files=files)
    
    if response.status_code != 200:
        print(f"✗ Upload failed: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    upload_result = response.json()
    document_id = upload_result.get("document_id")
    print(f"✓ Upload successful!")
    print(f"  Document ID: {document_id}\n")
    
    # Extract intelligence
    print("=== STEP 2: Extract with Azure Document Intelligence ===")
    response = requests.post(f"{base_url}/extract?document_id={document_id}")
    
    if response.status_code != 200:
        print(f"✗ Extraction failed: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    extracted_data = response.json()
    
    print(f"✓ Extraction successful!")
    
    # Show key results
    print(f"\n  Extraction Method: {extracted_data.get('extraction_method')}")
    print(f"  Processing Time: {extracted_data.get('processing_metadata', {}).get('processing_duration_ms')}ms")
    
    metadata = extracted_data.get("metadata", {})
    print(f"\n  METADATA:")
    print(f"    Document Type: {metadata.get('document_type')}")
    print(f"    Document #: {metadata.get('document_number')}")
    print(f"    Issue Date: {metadata.get('issue_date')}")
    
    parties = extracted_data.get("parties", {})
    if parties.get("issuer"):
        issuer = parties["issuer"]
        print(f"\n  ISSUER:")
        print(f"    Name: {issuer.get('name')}")
        print(f"    Phone: {issuer.get('contact', {}).get('phone')}")
        print(f"    Email: {issuer.get('contact', {}).get('email')}")
    
    project = extracted_data.get("project_context", {})
    if project:
        print(f"\n  PROJECT:")
        print(f"    Name: {project.get('project_name')}")
        print(f"    Location: {project.get('location')}")
    
    line_items = extracted_data.get("line_items")
    if line_items:
        print(f"\n  LINE ITEMS ({len(line_items)}):")
        for i, item in enumerate(line_items[:3], 1):  # Show first 3
            print(f"    {i}. {item.get('description')}")
            print(f"       Qty: {item.get('quantity')} {item.get('unit')}")
            print(f"       Price: {item.get('unit_price')} {item.get('currency')}")
    else:
        print(f"\n  LINE ITEMS: Not extracted")
    
    quality = extracted_data.get("data_quality", {})
    print(f"\n  DATA QUALITY:")
    print(f"    Completeness: {quality.get('completeness_percentage', 0):.0f}%")
    print(f"    Accuracy: {quality.get('accuracy_score', 0)*100:.0f}%")
    
    print("\n" + "="*60)
    print("✓ AZURE EXTRACTION TEST COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    try:
        test_azure_extraction()
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
