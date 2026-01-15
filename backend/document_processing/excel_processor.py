import pandas as pd
import openpyxl
from typing import List, Dict, Any
from .base_processor import BaseProcessor

class ExcelProcessor(BaseProcessor):
    """Process Excel (.xlsx) documents and extract tables, structured data."""
    
    def parse(self) -> Dict[str, Any]:
        """Parse Excel document and return structured data."""
        try:
            xl_file = pd.ExcelFile(self.file_path)
            result = {
                "sheet_names": xl_file.sheet_names,
                "sheets": []
            }
            
            for sheet_name in xl_file.sheet_names:
                df = pd.read_excel(self.file_path, sheet_name=sheet_name)
                result["sheets"].append({
                    "sheet_name": sheet_name,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "data": df.to_dict(orient="records")
                })
            
            return result
        except Exception as e:
            return {"error": f"Failed to parse Excel document: {str(e)}"}
    
    def extract_tables(self) -> List[List[Dict]]:
        """Extract all tables (sheets) from the Excel document."""
        tables = []
        try:
            xl_file = pd.ExcelFile(self.file_path)
            for sheet_name in xl_file.sheet_names:
                df = pd.read_excel(self.file_path, sheet_name=sheet_name)
                tables.append({
                    "sheet_name": sheet_name,
                    "data": df.to_dict(orient="records"),
                    "columns": list(df.columns)
                })
        except Exception as e:
            return [{"error": f"Failed to extract tables: {str(e)}"}]
        return tables
    
    def extract_text(self) -> str:
        """Extract all text from the Excel document."""
        text = ""
        try:
            xl_file = pd.ExcelFile(self.file_path)
            for sheet_name in xl_file.sheet_names:
                df = pd.read_excel(self.file_path, sheet_name=sheet_name)
                text += f"Sheet: {sheet_name}\n"
                text += df.to_string() + "\n\n"
        except Exception as e:
            text = f"Error extracting text: {str(e)}"
        return text
    
    def get_sheet_data(self, sheet_name: str) -> Dict[str, Any]:
        """Get data from a specific sheet."""
        try:
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)
            return {
                "sheet_name": sheet_name,
                "rows": len(df),
                "columns": list(df.columns),
                "data": df.to_dict(orient="records")
            }
        except Exception as e:
            return {"error": f"Failed to get sheet data: {str(e)}"}
