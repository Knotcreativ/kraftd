import pdfplumber
from typing import List, Dict, Any
from .base_processor import BaseProcessor

class PDFProcessor(BaseProcessor):
    """Process PDF documents and extract text, tables, and structured data."""
    
    def parse(self) -> Dict[str, Any]:
        """Parse PDF and return structured data."""
        try:
            with pdfplumber.open(self.file_path) as pdf:
                result = {
                    "total_pages": len(pdf.pages),
                    "text": "",
                    "tables": [],
                    "pages": []
                }
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text
                    text = page.extract_text()
                    result["text"] += text + "\n"
                    
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        result["tables"].extend(tables)
                    
                    result["pages"].append({
                        "page_number": page_num,
                        "text": text,
                        "tables_count": len(tables) if tables else 0
                    })
                
                return result
        except Exception as e:
            return {"error": f"Failed to parse PDF: {str(e)}"}
    
    def extract_tables(self) -> List[List[Dict]]:
        """Extract all tables from the PDF."""
        tables = []
        try:
            with pdfplumber.open(self.file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table in page_tables:
                            tables.append({
                                "page": page_num,
                                "data": table
                            })
        except Exception as e:
            return [{"error": f"Failed to extract tables: {str(e)}"}]
        return tables
    
    def extract_text(self) -> str:
        """Extract all text from the PDF."""
        text = ""
        try:
            with pdfplumber.open(self.file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            text = f"Error extracting text: {str(e)}"
        return text
