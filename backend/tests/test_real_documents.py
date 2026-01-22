"""
Test classifier with real documents from test_documents folder.
"""

import os
from pathlib import Path
from document_processing.classifier import classify_document, DocumentTypeEnum
from document_processing.pdf_processor import PDFProcessor
from document_processing.word_processor import WordProcessor
from document_processing.excel_processor import ExcelProcessor


def extract_text(file_path):
    """Extract text from document based on file extension"""
    ext = Path(file_path).suffix.lower()
    
    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    if ext == '.pdf':
        processor = PDFProcessor(file_path)
        result = processor.parse()
        return result.get('text', '')
    
    if ext in ['.docx', '.doc']:
        processor = WordProcessor(file_path)
        result = processor.parse()
        return result.get('text', '')
    
    if ext in ['.xlsx', '.xls']:
        processor = ExcelProcessor(file_path)
        result = processor.parse()
        return result.get('text', '')
    
    return None


def test_documents():
    """Test all documents in test_documents folder"""
    test_dir = Path("test_documents")
    
    if not test_dir.exists():
        print(f"❌ Directory not found: {test_dir.absolute()}")
        return
    
    documents = list(test_dir.glob("*.*"))
    
    if not documents:
        print("❌ No documents found in test_documents folder")
        return
    
    print("\n" + "="*80)
    print(f"TESTING {len(documents)} REAL DOCUMENT(S)")
    print("="*80)
    
    for doc_path in documents:
        print(f"\n📄 File: {doc_path.name}")
        print("-" * 80)
        
        # Extract text
        text = extract_text(str(doc_path))
        
        if not text:
            print(f"❌ Could not extract text from {doc_path.suffix}")
            continue
        
        # Show preview
        preview = text[:300].replace('\n', ' ').strip()
        print(f"Preview: {preview}...")
        print(f"Total Characters: {len(text)}")
        
        # Classify
        result = classify_document(text, file_name=doc_path.name)
        
        # Results
        print(f"\n✅ CLASSIFICATION RESULTS")
        print(f"   Document Type: {result.document_type}")
        print(f"   Confidence: {result.confidence:.0%}")
        print(f"   Requires Review: {result.requires_review}")
        print(f"   Method: {result.method}")
        
        # Show matched signals
        matched_signals = [s for s in result.signals if s.matched]
        if matched_signals:
            print(f"\n✓ Matched Signals ({len(matched_signals)}):")
            for signal in matched_signals[:5]:  # Top 5
                print(f"   • {signal.signal_name} (confidence: {signal.confidence:.0%})")
                if signal.evidence:
                    print(f"     Evidence: {signal.evidence[0][:60]}")
        
        # Show alternatives
        if result.alternatives:
            print(f"\n📊 Alternative Classifications:")
            for alt_type, alt_conf in result.alternatives[:3]:
                print(f"   • {alt_type}: {alt_conf:.0%}")
        
        # Reasoning
        if result.reasoning:
            print(f"\n💭 Reasoning:")
            for reason in result.reasoning[:2]:
                print(f"   • {reason}")


if __name__ == "__main__":
    test_documents()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")
