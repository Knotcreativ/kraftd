import pytesseract
from PIL import Image
import pdfplumber
from typing import List, Dict, Any
from .base_processor import BaseProcessor

class ImageProcessor(BaseProcessor):
    """Process scanned images and PDFs using OCR to extract text and data."""
    
    def parse(self) -> Dict[str, Any]:
        """Parse image/scanned PDF and return structured data using OCR."""
        try:
            if self.file_path.lower().endswith('.pdf'):
                return self._parse_scanned_pdf()
            else:
                return self._parse_image()
        except Exception as e:
            return {"error": f"Failed to parse image: {str(e)}"}
    
    def _parse_image(self) -> Dict[str, Any]:
        """Parse a single image file."""
        try:
            image = Image.open(self.file_path)
            text = pytesseract.image_to_string(image)
            
            return {
                "file_type": "image",
                "text": text,
                "image_size": image.size,
                "image_format": image.format
            }
        except Exception as e:
            return {"error": f"Failed to parse image: {str(e)}"}
    
    def _parse_scanned_pdf(self) -> Dict[str, Any]:
        """Parse a scanned PDF using OCR."""
        try:
            result = {
                "file_type": "scanned_pdf",
                "pages": [],
                "full_text": ""
            }
            
            with pdfplumber.open(self.file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Try to extract text directly first
                    text = page.extract_text()
                    
                    # If minimal text extracted, use OCR on page image
                    if not text or len(text.strip()) < 50:
                        try:
                            image = page.to_image()
                            text = pytesseract.image_to_string(image.original)
                        except:
                            text = "Failed to OCR page"
                    
                    result["pages"].append({
                        "page_number": page_num,
                        "text": text
                    })
                    result["full_text"] += text + "\n"
            
            return result
        except Exception as e:
            return {"error": f"Failed to parse scanned PDF: {str(e)}"}
    
    def extract_tables(self) -> List[List[Dict]]:
        """Extract tables from OCR'd text (limited capability)."""
        # OCR-based table extraction is limited; recommend pre-processing
        return [{"note": "Table extraction from OCR'd images is limited. Consider pre-processing or manual review."}]
    
    def extract_text(self) -> str:
        """Extract all text from the image using OCR."""
        text = ""
        try:
            if self.file_path.lower().endswith('.pdf'):
                with pdfplumber.open(self.file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if not page_text or len(page_text.strip()) < 50:
                            try:
                                image = page.to_image()
                                page_text = pytesseract.image_to_string(image.original)
                            except:
                                pass
                        text += page_text + "\n"
            else:
                image = Image.open(self.file_path)
                text = pytesseract.image_to_string(image)
        except Exception as e:
            text = f"Error extracting text with OCR: {str(e)}"
        return text
