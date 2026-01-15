"""
Field Extraction & Mapping for Kraftd Documents

Maps extracted text to KraftdDocument schema.
Handles all document types: RFQ, BOQ, Quotation, PO, Invoice, Contract.

Strategy:
1. Extract parties (buyer, supplier) via patterns and context
2. Extract dates (issue, submission, delivery, validity)
3. Extract line items (qty, price, description, UOM)
4. Extract commercial terms (currency, tax, payment, warranty)
5. Extract document-specific fields (RFQ conditions, PO terms, etc.)
6. Normalize and validate all extracted data
7. Return structured KraftdDocument with confidence scores
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from dataclasses import dataclass
import json
import uuid

from .schemas import (
    KraftdDocument, DocumentMetadata, DocumentType, Party, Contact, Address,
    LineItem, UnitOfMeasure, Currency, Dates, CommercialTerms, ProjectContext,
    ExtractionConfidence, FieldConfidence, ProcessingMetadata, ReviewState,
    DocumentStatus, ExtractionMethod, RFQData, QuotationData, POData, ContractData,
    RFQScope, SubmissionInstructions, EvaluationCriteria, RFQConditions
)
from .classifier import DocumentTypeEnum, classify_document


@dataclass
class ExtractionSignal:
    """A single extraction signal"""
    field_name: str
    value: Any
    confidence: float  # 0-1
    evidence: str
    method: str  # "regex", "table", "context", "ai"


class FieldExtractor:
    """Extract specific fields using various methods"""
    
    def __init__(self):
        """Initialize field extraction patterns"""
        self.patterns = self._init_patterns()
    
    def _init_patterns(self) -> Dict[str, List[str]]:
        """Initialize regex patterns for field extraction"""
        return {
            # Parties
            "supplier_name": [
                r"(?:supplier|vendor|contractor|from|company)[\s:]+([a-z\s\&\.,0-9]+?)(?:\n|address|email|contact)",
                r"(?:to|recipient)[\s:]+([a-z\s\&\.,0-9]+?)(?:\n|address)",
            ],
            "buyer_name": [
                r"(?:buyer|client|purchaser|requester|organization|department)[\s:]+([a-z\s\&\.,0-9]+?)(?:\n|address|email|contact)",
            ],
            
            # Document Numbers - more permissive
            "document_number": [
                r"(?:rfq|po|quote|quotation|inv(?:oice)?|contract|sow)[\s\-#:]+([a-z0-9\-/\.]+)",
                r"(?:doc\.?\s*no\.?|number|ref\.?)[\s:]+([a-z0-9\-/\.]+)",
            ],
            "revision_number": [
                r"(?:rev\.?|revision)[\s\.:\-]+([a-z0-9]+)",
            ],
            
            # Dates - more flexible
            "issue_date": [
                r"(?:date|issued?|issue date)[\s:]+([0-9]{1,2}\s+[a-z]{3,9}\s+[0-9]{4})",
                r"([0-9]{1,2}\s+[a-z]{3,9}\s+[0-9]{4})",
            ],
            "submission_deadline": [
                r"(?:submission deadline|deadline|due date)[\s:]+([0-9]{1,2}\s+[a-z]{3,9}\s+[0-9]{4})",
            ],
            "delivery_date": [
                r"(?:delivery date|delivery|expected delivery)[\s:]+([0-9]{1,2}\s+[a-z]{3,9}\s+[0-9]{4})",
            ],
            "validity_date": [
                r"(?:validity|valid until|offer valid|quote validity)[\s:]+([0-9]{1,2}\s+[a-z]{3,9}\s+[0-9]{4})",
            ],
            
            # Currency
            "currency": [
                r"(?:currency|price in|amount in)[\s:]+([a-z]{3})",
                r"\b([a-z]{3})\s+(?:[\d,]+\.?\d*|thousand|million)",
            ],
            
            # Tax/VAT
            "vat_rate": [
                r"(?:vat|tax|gst|sgst)[\s:]*\(?([0-9]+(?:\.[0-9]+)?)\s*%",
                r"([0-9]+(?:\.[0-9]+)?)\s*%\s*(?:vat|tax|gst)",
            ],
            
            # Payment Terms
            "payment_terms": [
                r"(?:payment terms?|payment condition)[\s:]+([^\n]+)",
                r"(?:net|advance|milestone)[\s\-]+([0-9]+)\s*(?:days|%|of)",
            ],
        }
    
    def extract_party(self, text: str, party_type: str) -> Optional[Party]:
        """Extract party (buyer/supplier) from text"""
        name_pattern = f"{party_type}_name"
        
        # Find name
        name = self._extract_single_field(text, name_pattern)
        if not name:
            return None
        
        # Extract contact info
        contact = Contact(
            name=name.split('\n')[0].strip(),
            email=self._extract_email(text),
            phone=self._extract_phone(text),
        )
        
        # Extract address
        address = self._extract_address(text)
        
        return Party(
            name=name.strip(),
            contact_person=contact,
            registered_address=address,
            project_address=address
        )
    
    def extract_dates(self, text: str) -> Dict[str, Optional[date]]:
        """Extract all date fields"""
        dates = {}
        
        for date_field in ["issue_date", "submission_deadline", "delivery_date", "validity_date"]:
            date_str = self._extract_single_field(text, date_field)
            if date_str:
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    dates[date_field] = parsed_date
        
        return dates
    
    def extract_line_items(self, text: str) -> List[LineItem]:
        """Extract line items from text"""
        line_items = []
        
        # Try to find structured tables first
        items_from_table = self._extract_from_table(text)
        if items_from_table:
            return items_from_table
        
        # Look for patterns like rows with line numbers
        # Split text by lines and find table-like sections
        lines = text.split('\n')
        
        for line in lines:
            # Skip empty or header lines
            if not line.strip() or any(x in line.lower() for x in ['item', 'description', 'qty', 'quantity', 'price', '---']):
                continue
            
            # Look for lines starting with numbers (line items)
            match = re.match(r'^\s*(\d+)\s*[\s\.|)]+', line)
            if match:
                try:
                    # Extract components
                    parts = re.split(r'\s*\|\s*|,\s+', line)
                    
                    if len(parts) >= 3:
                        # Find numeric values in the parts
                        numbers = []
                        for part in parts:
                            # Extract all numbers from part
                            nums = re.findall(r'[\d,]+\.?\d*', part)
                            if nums:
                                numbers.append(float(nums[0].replace(',', '')))
                        
                        if len(numbers) >= 2:
                            # We have at least qty and price
                            line_num = int(match.group(1))
                            desc = parts[1].strip() if len(parts) > 1 else f"Item {line_num}"
                            qty = numbers[0]
                            price = numbers[-1]  # Last number is price
                            
                            item = LineItem(
                                line_number=line_num,
                                description=desc,
                                quantity=qty,
                                unit_of_measure=UnitOfMeasure.EACH,
                                unit_price=price,
                                total_price=qty * price,
                                currency=Currency.SAR
                            )
                            line_items.append(item)
                except (ValueError, IndexError, AttributeError):
                    continue
        
        return line_items
    
    def extract_commercial_terms(self, text: str) -> CommercialTerms:
        """Extract payment, warranty, and other commercial terms"""
        currency_str = self._extract_single_field(text, "currency")
        currency = self._normalize_currency(currency_str) if currency_str else Currency.SAR
        
        vat_rate = None
        vat_str = self._extract_single_field(text, "vat_rate")
        if vat_str:
            try:
                vat_rate = float(vat_str)
            except ValueError:
                vat_rate = None
        
        payment_terms = self._extract_single_field(text, "payment_terms")
        
        # Check for advance payment
        has_advance = bool(re.search(r"advance\s+payment|upfront", text, re.IGNORECASE))
        advance_pct = None
        advance_match = re.search(r"advance.*?(\d+)\s*%", text, re.IGNORECASE)
        if advance_match:
            advance_pct = float(advance_match.group(1))
        
        # Check for milestone-based
        has_milestone = bool(re.search(r"milestone|progress payment", text, re.IGNORECASE))
        
        # Warranty
        warranty_match = re.search(r"warranty.*?(\d+)\s*(?:month|year|day)", text, re.IGNORECASE)
        warranty_period = warranty_match.group(0) if warranty_match else None
        
        return CommercialTerms(
            currency=currency,
            vat_rate=vat_rate,
            payment_terms=payment_terms,
            warranty_period=warranty_period,
            has_advance_payment=has_advance,
            advance_payment_percentage=advance_pct,
            milestone_based_payment=has_milestone
        )
    
    # ==================== HELPER METHODS ====================
    
    def _extract_single_field(self, text: str, field_name: str) -> Optional[str]:
        """Extract single field using regex patterns"""
        if field_name not in self.patterns:
            return None
        
        patterns = self.patterns[field_name]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip() if match.lastindex else match.group(0).strip()
        
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address"""
        match = re.search(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", text, re.IGNORECASE)
        return match.group(0) if match else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number"""
        match = re.search(r"(?:\+|00)?[\d\s\-\(\)]{10,}", text)
        return match.group(0).strip() if match else None
    
    def _extract_address(self, text: str) -> Optional[Address]:
        """Extract address components"""
        # Simplified address extraction
        lines = text.split('\n')
        address_lines = []
        
        for i, line in enumerate(lines):
            if any(x in line.lower() for x in ['address', 'city', 'country', 'postal']):
                # Capture this line and next few lines
                address_lines.extend(lines[i:min(i+3, len(lines))])
                break
        
        if not address_lines:
            return None
        
        address_text = ' '.join(address_lines)
        
        return Address(
            address_line1=address_text[:100] if address_text else None,
            city=None,  # Would need more sophisticated parsing
            country=None
        )
    
    def _extract_from_table(self, text: str) -> List[LineItem]:
        """Try to extract line items from table structure"""
        # Look for table patterns: item | qty | price
        items = []
        
        # Split by common table delimiters
        lines = text.split('\n')
        table_lines = []
        in_table = False
        
        for line in lines:
            if '|' in line or any(x in line.lower() for x in ['qty', 'quantity', 'price', 'amount', 'item']):
                in_table = True
                table_lines.append(line)
            elif in_table and (line.strip() == '' or not any(c.isdigit() for c in line)):
                break
        
        # Parse table rows
        for line in table_lines[1:]:  # Skip header
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                try:
                    # Try to extract: desc | qty | price
                    desc = parts[0]
                    
                    # Try to find qty in parts[1]
                    qty_match = re.search(r'[\d.]+', parts[1] or '0')
                    if not qty_match:
                        continue
                    qty = float(qty_match.group())
                    
                    # Try to find price in last part
                    price_match = re.search(r'[\d.]+', parts[-1] or '0')
                    if not price_match:
                        continue
                    price = float(price_match.group().replace(',', ''))
                    
                    item = LineItem(
                        line_number=len(items) + 1,
                        description=desc,
                        quantity=qty,
                        unit_of_measure=UnitOfMeasure.EACH,
                        unit_price=price,
                        total_price=qty * price,
                        currency=Currency.SAR
                    )
                    items.append(item)
                except (ValueError, IndexError, AttributeError):
                    continue
        
        return items
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string into date object"""
        if not date_str:
            return None
        
        # Try multiple date formats
        formats = [
            "%d %B %Y",  # 15 January 2024
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d %b %Y",   # 15 Jan 2024
            "%B %d, %Y",  # January 15, 2024
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _normalize_currency(self, currency_str: str) -> Currency:
        """Normalize currency string to enum"""
        if not currency_str:
            return Currency.SAR
        
        mapping = {
            'sar': Currency.SAR,
            'usd': Currency.USD,
            'aed': Currency.AED,
            'eur': Currency.EUR,
            'gbp': Currency.GBP,
            'inr': Currency.INR,
        }
        
        return mapping.get(currency_str.lower()[:3], Currency.SAR)
    
    def _normalize_uom(self, uom_str: str) -> UnitOfMeasure:
        """Normalize UOM string to enum"""
        if not uom_str:
            return UnitOfMeasure.EACH
        
        mapping = {
            'm': UnitOfMeasure.METER,
            'm2': UnitOfMeasure.SQUARE_METER,
            'm3': UnitOfMeasure.CUBIC_METER,
            'kg': UnitOfMeasure.KILOGRAM,
            'ton': UnitOfMeasure.TON,
            'l': UnitOfMeasure.LITER,
            'pc': UnitOfMeasure.PIECE,
            'pcs': UnitOfMeasure.PIECE,
            'set': UnitOfMeasure.SET,
            'lot': UnitOfMeasure.LOT,
            'h': UnitOfMeasure.HOUR,
            'day': UnitOfMeasure.DAY,
            'each': UnitOfMeasure.EACH,
        }
        
        return mapping.get(uom_str.lower(), UnitOfMeasure.EACH)


class DocumentMapper:
    """
    Map extracted fields to KraftdDocument schema.
    
    Orchestrates field extraction and builds final document.
    """
    
    def __init__(self):
        self.extractor = FieldExtractor()
    
    def map(
        self,
        text: str,
        classification_result: Optional[Dict] = None,
        document_file_name: Optional[str] = None
    ) -> KraftdDocument:
        """
        Map document text to KraftdDocument schema.
        
        Args:
            text: Normalized document text
            classification_result: Result from Classifier stage
            document_file_name: Original filename for metadata
        
        Returns:
            KraftdDocument with extracted fields
        """
        
        # Classify if not already done
        if not classification_result:
            from .classifier import classify_document
            classification_result = classify_document(text, file_name=document_file_name)
        
        # Map document type
        doc_type_map = {
            'RFQ': DocumentType.RFQ,
            'BOQ': DocumentType.BOQ,
            'Quotation': DocumentType.QUOTATION,
            'PO': DocumentType.PO,
            'Invoice': DocumentType.INVOICE,
            'Contract': DocumentType.CONTRACT,
            'SOW': DocumentType.CONTRACT,
        }
        
        mapped_type = doc_type_map.get(
            str(classification_result.document_type).split('.')[-1],
            DocumentType.RFQ
        )
        
        # Extract fields
        document_number = self.extractor._extract_single_field(text, "document_number") or "UNKNOWN"
        revision = self.extractor._extract_single_field(text, "revision_number")
        
        # Extract parties
        parties = {}
        issuer = self.extractor.extract_party(text, "supplier")
        recipient = self.extractor.extract_party(text, "buyer")
        
        if issuer:
            parties["issuer"] = issuer
        if recipient:
            parties["recipient"] = recipient
        
        # If missing, create placeholder
        if not parties:
            parties = {
                "issuer": Party(name="Unknown Supplier"),
                "recipient": Party(name="Unknown Buyer")
            }
        
        # Extract dates
        dates_dict = self.extractor.extract_dates(text)
        dates = Dates(
            issue_date=dates_dict.get("issue_date"),
            submission_deadline=dates_dict.get("submission_deadline"),
            delivery_date=dates_dict.get("delivery_date"),
            validity_date=dates_dict.get("validity_date")
        ) if dates_dict else None
        
        # Extract line items
        line_items = self.extractor.extract_line_items(text)
        
        # Extract commercial terms
        commercial_terms = self.extractor.extract_commercial_terms(text)
        
        # Update currency in line items
        for item in line_items:
            item.currency = commercial_terms.currency or Currency.SAR
        
        # Build metadata
        metadata = DocumentMetadata(
            document_type=mapped_type,
            document_number=document_number,
            revision_number=revision,
            issue_date=dates.issue_date if dates else None,
            page_count=None,
            user_intent=None
        )
        
        # Confidence scores
        field_confidence = FieldConfidence(
            parties=0.7 if parties else 0.0,
            line_items=0.8 if line_items else 0.3,
            dates=0.75 if dates else 0.3,
            commercial_terms=0.7,
            project_context=0.4
        )
        
        missing_fields = []
        if not line_items:
            missing_fields.append("line_items")
        if not dates:
            missing_fields.append("dates")
        if not parties:
            missing_fields.append("parties")
        
        extraction_confidence = ExtractionConfidence(
            overall_confidence=0.7,
            field_confidence=field_confidence,
            missing_fields=missing_fields if missing_fields else None
        )
        
        # Build document
        doc = KraftdDocument(
            document_id=str(uuid.uuid4()),
            metadata=metadata,
            parties=parties,
            dates=dates,
            commercial_terms=commercial_terms,
            line_items=line_items if line_items else None,
            status=DocumentStatus.EXTRACTED,
            extraction_confidence=extraction_confidence,
            processing_metadata=ProcessingMetadata(
                extraction_method=ExtractionMethod.DIRECT_PARSE,
                processing_duration_ms=0,
                processor_version="1.0.0",
                source_file_size_bytes=len(text)
            )
        )
        
        return doc


def map_document(
    text: str,
    classification_result: Optional[Dict] = None,
    document_file_name: Optional[str] = None
) -> KraftdDocument:
    """
    Quick function to map document.
    
    Usage:
        doc = map_document(normalized_text)
        print(doc.parties)
        print(doc.line_items)
    """
    mapper = DocumentMapper()
    return mapper.map(text, classification_result, document_file_name)
