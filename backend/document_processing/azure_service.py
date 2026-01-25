"""
Azure Document Intelligence Service Integration

Provides intelligent document extraction using Azure's pre-trained models
for procurement documents (RFQs, quotations, POs, etc.)
"""

import os
from typing import Dict, Any, Optional, List
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient, AnalyzeResult


class AzureDocumentIntelligenceService:
    """Service wrapper for Azure Document Intelligence API."""
    
    def __init__(self):
        """Initialize Azure Document Intelligence client."""
        # Get credentials from environment variables
        self.endpoint = os.environ.get("DOCUMENTINTELLIGENCE_ENDPOINT")
        self.key = os.environ.get("DOCUMENTINTELLIGENCE_API_KEY")
        
        if not self.endpoint or not self.key:
            raise ValueError(
                "Azure Document Intelligence credentials not configured. "
                "Set DOCUMENTINTELLIGENCE_ENDPOINT and DOCUMENTINTELLIGENCE_API_KEY environment variables."
            )
        
        self.client = DocumentAnalysisClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )
    
    def analyze_document(self, file_path: str, model_type: str = "prebuilt-layout") -> AnalyzeResult:
        """
        Analyze a document using Azure Document Intelligence.
        
        Args:
            file_path: Path to the document file
            model_type: The model to use (e.g., "prebuilt-layout", "prebuilt-invoice", "prebuilt-receipt")
        
        Returns:
            AnalyzeResult containing extracted document data
        """
        try:
            # Read file and send for analysis
            with open(file_path, "rb") as f:
                poller = self.client.begin_analyze_document(
                    model_type,
                    body=f
                )
            
            # Wait for analysis to complete
            result: AnalyzeResult = poller.result()
            return result
        except Exception as e:
            raise Exception(f"Azure Document Intelligence analysis failed: {str(e)}")
    
    def extract_tables(self, result: AnalyzeResult) -> List[List[Dict[str, str]]]:
        """
        Extract tables from analysis result.
        
        Args:
            result: AnalyzeResult from analyze_document
        
        Returns:
            List of tables, each table is a list of row dictionaries
        """
        tables = []
        
        if not result.tables:
            return tables
        
        for table in result.tables:
            table_data = []
            row_dict = {}
            
            # Build table data from cells
            for cell in table.cells:
                row_idx = cell.row_index
                col_idx = cell.column_index
                
                # Initialize row if needed
                if row_idx not in row_dict:
                    row_dict[row_idx] = {}
                
                row_dict[row_idx][col_idx] = cell.content
            
            # Convert to list of dicts (columns as keys)
            if row_dict:
                max_rows = max(row_dict.keys()) + 1
                max_cols = max(max(row.keys()) for row in row_dict.values()) + 1
                
                for row_idx in range(max_rows):
                    if row_idx in row_dict:
                        table_data.append(row_dict[row_idx])
                    else:
                        table_data.append({col: "" for col in range(max_cols)})
            
            tables.append(table_data)
        
        return tables
    
    def extract_text_by_lines(self, result: AnalyzeResult) -> List[str]:
        """
        Extract text lines from analysis result.
        
        Args:
            result: AnalyzeResult from analyze_document
        
        Returns:
            List of text lines
        """
        lines = []
        
        for page in result.pages:
            if page.lines:
                for line in page.lines:
                    lines.append(line.content)
        
        return lines
    
    def extract_paragraphs(self, result: AnalyzeResult) -> List[str]:
        """
        Extract paragraphs from analysis result.
        
        Args:
            result: AnalyzeResult from analyze_document
        
        Returns:
            List of paragraphs
        """
        paragraphs = []
        
        if result.paragraphs:
            for paragraph in result.paragraphs:
                paragraphs.append(paragraph.content)
        
        return paragraphs
    
    def get_document_text(self, result: AnalyzeResult) -> str:
        """
        Get full document text from analysis result.
        
        Args:
            result: AnalyzeResult from analyze_document
        
        Returns:
            Full document text
        """
        return result.content if result.content else ""
    
    def extract_form_fields(self, result: AnalyzeResult) -> Dict[str, Any]:
        """
        Extract form fields from analysis result (if using prebuilt models like invoice, receipt).
        
        Args:
            result: AnalyzeResult from analyze_document
        
        Returns:
            Dictionary of extracted form fields
        """
        fields = {}
        
        if result.documents:
            for doc in result.documents:
                if doc.fields:
                    for field_name, field_value in doc.fields.items():
                        # Extract value based on type
                        if hasattr(field_value, 'value_string'):
                            fields[field_name] = {
                                "value": field_value.value_string,
                                "confidence": field_value.confidence
                            }
                        elif hasattr(field_value, 'value_date'):
                            fields[field_name] = {
                                "value": field_value.value_date,
                                "confidence": field_value.confidence
                            }
                        elif hasattr(field_value, 'value_currency'):
                            fields[field_name] = {
                                "value": field_value.value_currency,
                                "confidence": field_value.confidence
                            }
                        elif hasattr(field_value, 'value_number'):
                            fields[field_name] = {
                                "value": field_value.value_number,
                                "confidence": field_value.confidence
                            }
                        elif hasattr(field_value, 'value_array'):
                            fields[field_name] = {
                                "value": field_value.value_array,
                                "confidence": field_value.confidence
                            }
                        else:
                            fields[field_name] = {
                                "value": str(field_value),
                                "confidence": getattr(field_value, 'confidence', None)
                            }
        
        return fields


def is_azure_configured() -> bool:
    """Check if Azure Document Intelligence is configured."""
    return bool(
        os.environ.get("DOCUMENTINTELLIGENCE_ENDPOINT") and
        os.environ.get("DOCUMENTINTELLIGENCE_API_KEY")
    )


def get_azure_service() -> Optional[AzureDocumentIntelligenceService]:
    """Get Azure Document Intelligence service instance if configured."""
    try:
        if is_azure_configured():
            return AzureDocumentIntelligenceService()
    except Exception:
        pass
    return None
