from typing import List, Dict, Any, Optional
import re
from datetime import datetime, date
from .schemas import (
    DocumentType, LineItem, Party, Contact, Address, DocumentMetadata,
    ProjectContext, Dates, CommercialTerms, RFQData, QuotationData,
    POData, ContractData, Signals, Categorization, RiskIndicators,
    BehavioralPatterns, ExtractionConfidence, FieldConfidence,
    UnitOfMeasure, Currency, KraftdDocument
)

class DocumentExtractor:
    """Enhanced extractor that maps parsed documents to KraftdDocument schema.
    
    Supports both local extraction (regex/pattern-based) and Azure Document Intelligence
    for higher accuracy on structured documents.
    """
    
    def __init__(self, parsed_data: Dict[str, Any] = None, document_type: Optional[str] = None, azure_result: Any = None):
        """
        Initialize extractor.
        
        Args:
            parsed_data: Parsed document data from local processors (pdf, word, etc.)
            document_type: Optional document type hint
            azure_result: Optional Azure Document Intelligence AnalyzeResult
        """
        self.parsed_data = parsed_data or {}
        self.document_type = document_type
        self.azure_result = azure_result
        
        # Extract text from either local parsing or Azure result
        if azure_result:
            self.text = azure_result.content if hasattr(azure_result, 'content') else ""
            self.tables = self._extract_tables_from_azure(azure_result)
        else:
            self.text = parsed_data.get("text", "") or parsed_data.get("full_text", "")
            self.tables = parsed_data.get("tables", []) or parsed_data.get("sheets", [])
    
    def _extract_tables_from_azure(self, azure_result: Any) -> List[List[Dict]]:
        """Extract tables from Azure Document Intelligence result."""
        tables = []
        
        if not hasattr(azure_result, 'tables') or not azure_result.tables:
            return tables
        
        for table in azure_result.tables:
            table_data = {}
            
            # Build table from cells
            for cell in table.cells:
                row_idx = cell.row_index
                col_idx = cell.column_index
                
                if row_idx not in table_data:
                    table_data[row_idx] = {}
                
                table_data[row_idx][col_idx] = cell.content
            
            # Convert to list format
            if table_data:
                rows = []
                for row_idx in sorted(table_data.keys()):
                    row = [table_data[row_idx].get(col_idx, "") 
                           for col_idx in sorted(table_data[row_idx].keys())]
                    rows.append(row)
                tables.append(rows)
        
        return tables
    
    def extract_to_kraftd_document(self, document_id: str) -> KraftdDocument:
        """Extract all intelligence and map to KraftdDocument schema."""
        # Detect document type if not provided
        doc_type = self._detect_document_type()
        
        # Extract core components
        metadata = self._extract_metadata(doc_type)
        parties = self._extract_parties()
        project_context = self._extract_project_context()
        dates = self._extract_dates()
        commercial_terms = self._extract_commercial_terms()
        line_items = self._extract_line_items()
        
        # Extract document-specific data
        document_specific = self._extract_document_specific(doc_type)
        
        # Extract signals
        signals = self._extract_signals(line_items)
        
        # Calculate confidence
        extraction_confidence = self._calculate_confidence()
        
        return KraftdDocument(
            document_id=document_id,
            metadata=metadata,
            parties=parties,
            project_context=project_context,
            dates=dates,
            commercial_terms=commercial_terms,
            line_items=line_items,
            document_specific=document_specific,
            signals=signals,
            extraction_confidence=extraction_confidence
        )
    
    # ===== Core Extraction Methods =====
    
    def _detect_document_type(self) -> DocumentType:
        """Detect document type from content."""
        if self.document_type:
            return DocumentType(self.document_type)
        
        text_lower = self.text.lower()
        doc_type_keywords = {
            DocumentType.RFQ: ["request for quotation", "rfq", "inquiry"],
            DocumentType.BOQ: ["bill of quantities", "boq", "schedule of quantities"],
            DocumentType.QUOTATION: ["quotation", "quote", "offer"],
            DocumentType.PO: ["purchase order", "po number", "order"],
            DocumentType.CONTRACT: ["contract", "agreement", "service agreement"],
            DocumentType.INVOICE: ["invoice", "bill"]
        }
        
        for doc_type, keywords in doc_type_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return doc_type
        
        return DocumentType.BOQ  # Default
    
    def _extract_metadata(self, doc_type: DocumentType) -> DocumentMetadata:
        """Extract document metadata."""
        document_number = self._extract_field_value(
            r"(RFQ|PO|INV|DOC|REF)[\s-]*(\d+[-\w]*)",
            self.text
        )
        
        issue_date = self._extract_date(
            r"(?:issue|date|dated?)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            self.text
        )
        
        return DocumentMetadata(
            document_type=doc_type,
            document_number=document_number or "Unknown",
            issue_date=issue_date
        )
    
    def _extract_parties(self) -> Dict[str, Party]:
        """Extract issuer and recipient parties."""
        issuer = self._extract_party("issuer")
        recipient = self._extract_party("recipient")
        
        return {
            "issuer": issuer,
            "recipient": recipient
        }
    
    def _extract_party(self, party_type: str) -> Party:
        """Extract individual party details."""
        # Placeholder: Would integrate with NER or document structure
        keywords = {
            "issuer": ["from", "issued by", "supplier", "company"],
            "recipient": ["to", "recipient", "buyer", "client"]
        }
        
        contact_name = self._extract_field_value(r"(Mr\.|Ms\.|Dr\.)?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)", self.text)
        email = self._extract_field_value(r"[\w\.-]+@[\w\.-]+\.\w+", self.text)
        phone = self._extract_field_value(r"\+?\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}", self.text)
        
        return Party(
            name=f"Unknown {party_type.capitalize()}",
            contact_person=Contact(name=contact_name, email=email, phone=phone) if any([contact_name, email, phone]) else None
        )
    
    def _extract_project_context(self) -> Optional[ProjectContext]:
        """Extract project context."""
        project_name = self._extract_field_value(r"(?:project|site)[\s:]*([^\n]+)", self.text)
        location = self._extract_field_value(r"(?:location|address)[\s:]*([^\n]+)", self.text)
        
        return ProjectContext(
            project_name=project_name,
            location=location
        )
    
    def _extract_dates(self) -> Optional[Dates]:
        """Extract all dates from document."""
        issue_date = self._extract_date(r"(?:issue|date|dated?)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", self.text)
        deadline = self._extract_date(r"(?:deadline|due|submission)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", self.text)
        delivery_date = self._extract_date(r"(?:delivery|deliver)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", self.text)
        
        return Dates(
            issue_date=issue_date,
            submission_deadline=deadline,
            delivery_date=delivery_date
        )
    
    def _extract_commercial_terms(self) -> Optional[CommercialTerms]:
        """Extract commercial terms."""
        currency = self._extract_currency()
        # Extract VAT rate from text
        vat_match = re.search(r"(?:vat|tax)[\s:]*(\d+(?:\.\d+)?)\s*%", self.text, re.IGNORECASE)
        vat_rate = float(vat_match.group(1)) if vat_match else None
        incoterms = self._extract_field_value(r"(FOB|CIF|DAP|DDP|EXW)", self.text)
        payment_terms = self._extract_field_value(r"(?:payment|terms?)[\s:]*([^\n]+)", self.text)
        
        return CommercialTerms(
            currency=Currency(currency) if currency else None,
            vat_rate=vat_rate,
            incoterms=incoterms,
            payment_terms=payment_terms
        )
    
    def _extract_line_items(self) -> Optional[List[LineItem]]:
        """Extract line items from tables."""
        line_items = []
        
        if not self.tables:
            return None
        
        for table_idx, table in enumerate(self.tables):
            table_data = table.get("data", []) if isinstance(table, dict) else table
            
            for row_idx, row in enumerate(table_data):
                if row_idx == 0:  # Skip header row
                    continue
                
                line_item = self._parse_row_to_line_item(row, row_idx)
                if line_item:
                    line_items.append(line_item)
        
        return line_items if line_items else None
    
    def _parse_row_to_line_item(self, row: tuple, line_number: int) -> Optional[LineItem]:
        """Convert table row to LineItem."""
        if not row or len(row) < 2:
            return None
        
        try:
            description = str(row[0]).strip() if row[0] else "Unknown"
            quantity = self._extract_number(str(row[1])) if len(row) > 1 else 1.0
            unit = self._normalize_unit(str(row[2]).strip()) if len(row) > 2 else UnitOfMeasure.EACH
            unit_price = self._extract_number(str(row[3])) if len(row) > 3 else 0.0
            total_price = quantity * unit_price
            
            return LineItem(
                line_number=line_number,
                description=description,
                quantity=quantity,
                unit_of_measure=unit,
                unit_price=unit_price,
                total_price=total_price,
                currency=self._extract_currency() or Currency.SAR
            )
        except Exception:
            return None
    
    def _extract_document_specific(self, doc_type: DocumentType) -> Dict[str, Optional[Any]]:
        """Extract document-type-specific data."""
        data = {
            "rfq_data": None,
            "quotation_data": None,
            "po_data": None,
            "contract_data": None
        }
        
        if doc_type == DocumentType.RFQ:
            data["rfq_data"] = RFQData()  # Placeholder
        elif doc_type == DocumentType.QUOTATION:
            data["quotation_data"] = QuotationData()  # Placeholder
        elif doc_type == DocumentType.PO:
            data["po_data"] = POData(po_number=self._extract_field_value(r"PO[\s-]*(\d+)", self.text) or "Unknown")
        elif doc_type == DocumentType.CONTRACT:
            data["contract_data"] = ContractData()  # Placeholder
        
        return data
    
    def _extract_signals(self, line_items: Optional[List[LineItem]]) -> Optional[Signals]:
        """Extract signals for future analytics."""
        categorization = self._extract_categorization()
        risk_indicators = self._extract_risk_indicators(line_items)
        
        return Signals(
            categorization=categorization,
            risk_indicators=risk_indicators
        )
    
    def _extract_categorization(self) -> Categorization:
        """Categorize commodities and spend."""
        commodity_keywords = {
            "steel": ["steel", "rebar", "angle", "channel"],
            "concrete": ["concrete", "cement", "aggregate"],
            "valves": ["valve", "gate", "check"],
            "cables": ["cable", "wire", "conductor"],
            "labor": ["labor", "manpower", "installation"],
            "services": ["service", "transport", "delivery", "inspection"]
        }
        
        text_lower = self.text.lower()
        detected_category = None
        
        for category, keywords in commodity_keywords.items():
            if any(kw in text_lower for kw in keywords):
                detected_category = category
                break
        
        return Categorization(
            commodity_category=detected_category or "miscellaneous",
            spend_category="opex" if "service" in text_lower else "capex"
        )
    
    def _extract_risk_indicators(self, line_items: Optional[List[LineItem]]) -> RiskIndicators:
        """Flag risk indicators."""
        aggressive_discount = False
        long_lead_time = False
        
        if line_items:
            for item in line_items:
                if item.discount_percentage and item.discount_percentage > 20:
                    aggressive_discount = True
                if item.delivery_time and "week" in item.delivery_time.lower():
                    lead_weeks = int(re.search(r"(\d+)\s*week", item.delivery_time.lower()).group(1))
                    if lead_weeks > 12:
                        long_lead_time = True
        
        return RiskIndicators(
            aggressive_discount=aggressive_discount,
            long_lead_time=long_lead_time
        )
    
    def _calculate_confidence(self) -> ExtractionConfidence:
        """Calculate extraction confidence scores."""
        # Weighted scoring based on extracted fields
        scores = {
            "parties": 0.8 if self.text else 0.0,
            "line_items": 0.9 if self.tables else 0.3,
            "dates": 0.85 if self._extract_date(r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", self.text) else 0.2,
            "commercial_terms": 0.75,
            "project_context": 0.7
        }
        
        overall = sum(scores.values()) / len(scores)
        
        return ExtractionConfidence(
            overall_confidence=overall,
            field_confidence=FieldConfidence(**scores)
        )
    
    # ===== Helper Methods =====
    
    def _extract_currency(self) -> Optional[str]:
        """Extract currency from text."""
        currencies = ["SAR", "USD", "AED", "EUR", "GBP", "INR"]
        for curr in currencies:
            if curr in self.text.upper():
                return curr
        return "SAR"  # Default
    
    def _extract_date(self, pattern: str, text: str) -> Optional[date]:
        """Extract and parse date from text."""
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Try common date formats
                for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"]:
                    try:
                        return datetime.strptime(date_str, fmt).date()
                    except:
                        pass
        except:
            pass
        return None
    
    def _extract_field_value(self, pattern: str, text: str) -> Optional[str]:
        """Extract field value using regex."""
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1) if match.lastindex and match.lastindex >= 1 else match.group(0)
        except:
            pass
        return None
    
    def _extract_number(self, text: str) -> float:
        """Extract numeric value from text."""
        try:
            text = str(text).replace(",", "")
            match = re.search(r"\d+(?:\.\d+)?", text)
            return float(match.group()) if match else 0.0
        except:
            return 0.0
    
    def _normalize_unit(self, unit_str: str) -> UnitOfMeasure:
        """Normalize unit string to UnitOfMeasure enum."""
        unit_map = {
            "m": UnitOfMeasure.METER,
            "meter": UnitOfMeasure.METER,
            "m2": UnitOfMeasure.SQUARE_METER,
            "m3": UnitOfMeasure.CUBIC_METER,
            "kg": UnitOfMeasure.KILOGRAM,
            "ton": UnitOfMeasure.TON,
            "piece": UnitOfMeasure.PIECE,
            "each": UnitOfMeasure.EACH,
            "set": UnitOfMeasure.SET,
            "hour": UnitOfMeasure.HOUR,
            "day": UnitOfMeasure.DAY
        }
        
        return unit_map.get(unit_str.lower(), UnitOfMeasure.EACH)
