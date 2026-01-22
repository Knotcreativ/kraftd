#!/usr/bin/env python3
"""Test the FastAPI endpoints."""
import requests
import json
from pathlib import Path
import time

BASE_URL = "http://localhost:8000"

def test_root():
    """Test the root endpoint."""
    print("[TEST] Root Endpoint")
    response = requests.get(f"{BASE_URL}/")
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Response: {json.dumps(data, indent=2)}")
        return True
    else:
        print(f"  Error: {response.text}")
        return False

def test_upload(file_path: str):
    """Test document upload."""
    print(f"\n[TEST] Upload Document: {file_path}")
    
    if not Path(file_path).exists():
        print(f"  ERROR: File not found: {file_path}")
        return None
    
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{BASE_URL}/docs/upload", files=files)
    
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Document ID: {data['document_id']}")
        print(f"  Message: {data['message']}")
        return data['document_id']
    else:
        print(f"  Error: {response.text}")
        return None

def test_extract(document_id: str):
    """Test extraction."""
    print(f"\n[TEST] Extract Document: {document_id}")
    
    params = {"document_id": document_id}
    response = requests.post(f"{BASE_URL}/extract", params=params)
    
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Status: {data['status']}")
        print(f"  Document Type: {data.get('document_type', 'UNKNOWN')}")
        print(f"  Processing Time: {data['processing_time_ms']}ms")
        
        if 'validation' in data:
            validation = data['validation']
            print(f"  Validation:")
            print(f"    - Completeness: {validation['completeness_score']}%")
            print(f"    - Quality: {validation['quality_score']}%")
            print(f"    - Overall: {validation['overall_score']}%")
            print(f"    - Ready: {validation['ready_for_processing']}")
            print(f"    - Needs Review: {validation['requires_manual_review']}")
        
        if 'extraction_metrics' in data:
            metrics = data['extraction_metrics']
            print(f"  Metrics:")
            print(f"    - Fields Mapped: {metrics['fields_mapped']}")
            print(f"    - Inferences: {metrics['inferences_made']}")
            print(f"    - Line Items: {metrics['line_items']}")
            print(f"    - Parties Found: {metrics['parties_found']}")
        
        return True
    else:
        print(f"  Error: {response.text}")
        return False

def test_get_status(document_id: str):
    """Test getting document status."""
    print(f"\n[TEST] Get Document Status: {document_id}")
    
    response = requests.get(f"{BASE_URL}/documents/{document_id}/status")
    
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Document Status: {data['status']}")
        print(f"  File Type: {data['file_type']}")
        
        if data.get('data_quality'):
            quality = data['data_quality']
            print(f"  Data Quality:")
            print(f"    - Completeness: {quality.get('completeness_percentage', 'N/A')}%")
            print(f"    - Accuracy: {quality.get('accuracy_score', 'N/A')}")
        
        return True
    else:
        print(f"  Error: {response.text}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Kraftd Docs API")
    print("=" * 60)
    
    # Find a test PDF
    test_file = Path("../test_pdfs/sample.pdf")
    if not test_file.exists():
        # Try to find any PDF
        from glob import glob
        pdfs = glob("../test_pdfs/*.pdf")
        if pdfs:
            test_file = pdfs[0]
            print(f"Using test file: {test_file}")
        else:
            print("No test PDFs found. Skipping upload test.")
            return
    
    # Test root endpoint
    if not test_root():
        print("ERROR: Could not connect to server!")
        return
    
    # Test upload
    doc_id = test_upload(str(test_file))
    if not doc_id:
        print("ERROR: Upload failed!")
        return
    
    # Give it a moment
    time.sleep(0.5)
    
    # Test extraction
    if test_extract(doc_id):
        print("\n✓ Extraction successful!")
    else:
        print("\n✗ Extraction failed!")
    
    # Test status
    if test_get_status(doc_id):
        print("\n✓ Status retrieval successful!")
    else:
        print("\n✗ Status retrieval failed!")
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
