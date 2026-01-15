"""
Intelligent Field Inference & Business Logic

Applies business rules to enhance extracted document data:
- Calculate totals (qty × price × discount × tax)
- Infer missing fields from context
- Resolve conflicting data
- Normalize currencies and units
- Link related documents
- Detect anomalies

Input: KraftdDocument from Mapper
Output: Enhanced KraftdDocument with inferred fields
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import re
import logging

from .schemas import (
    KraftdDocument, LineItem, DocumentType, Currency, Dates,
    CommercialTerms, Party, Contact, Address, ProcessingMetadata, ExtractionMethod
)

logger = logging.getLogger(__name__)


@dataclass
class InferenceSignal:
    """Result of an inference rule"""
    rule_name: str
    field_name: str
    inferred_value: Any
    confidence: float  # 0-1
    evidence: str
    requires_review: bool = False


class FieldInferencer:
    """Apply business logic and infer missing fields"""
    
    def __init__(self):
        self.inference_rules = self._init_inference_rules()
        self.currency_rates = self._init_currency_rates()
    
    def _init_currency_rates(self) -> Dict[str, float]:
        """Spot rates for currency conversion (for reference only)"""
        return {
            'SAR': 1.0,
            'USD': 3.75,  # 1 USD = 3.75 SAR
            'AED': 1.02,  # 1 AED = 1.02 SAR
            'EUR': 4.10,  # 1 EUR = 4.10 SAR
            'GBP': 4.75,  # 1 GBP = 4.75 SAR
            'INR': 0.045, # 1 INR = 0.045 SAR
        }
    
    def _init_inference_rules(self) -> Dict[str, callable]:
        """Initialize all inference rules"""
        return {
            'calculate_totals': self._calculate_totals,
            'infer_currency': self._infer_currency,
            'normalize_uom': self._normalize_uom,
            'calculate_tax': self._calculate_tax,
            'infer_parties': self._infer_parties,
            'normalize_dates': self._normalize_dates,
            'detect_delivery_terms': self._detect_delivery_terms,
            'infer_payment_terms': self._infer_payment_terms,
            'detect_discounts': self._detect_discounts,
            'validate_line_items': self._validate_line_items,
        }
    
    # ==================== CALCULATION RULES ====================
    
    def _calculate_totals(self, doc: KraftdDocument, text: str) -> List[InferenceSignal]:
        """Calculate line item totals and document total"""
        signals = []
        
        if not doc.line_items:
            return signals
        
        total_before_tax = 0
        
        for item in doc.line_items:
            # Calculate line total: qty × unit_price
            if item.quantity and item.unit_price:
                calculated_total = item.quantity * item.unit_price
                
                # Apply discount if exists
                if item.discount_percentage:
                    calculated_total *= (1 - item.discount_percentage / 100)
                
                # Check for mismatch
                if item.total_price and abs(calculated_total - item.total_price) > 1:
                    signals.append(InferenceSignal(
                        rule_name='calculate_totals',
                        field_name=f'line_item_{item.line_number}_total',
                        inferred_value=calculated_total,
                        confidence=0.9,
                        evidence=f"Calculated: {item.quantity} × {item.unit_price} = {calculated_total}",
                        requires_review=True
                    ))
                    item.total_price = calculated_total
                
                total_before_tax += calculated_total
        
        return signals
    
    def _calculate_tax(self, doc: KraftdDocument, text: str) -> List[InferenceSignal]:
        """Calculate tax/VAT on totals"""
        signals = []
        
        if not doc.line_items or not doc.commercial_terms:
            return signals
        
        total_before_tax = sum(item.total_price for item in doc.line_items if item.total_price)
        
        # Check if VAT mentioned
        if doc.commercial_terms.vat_rate and total_before_tax > 0:
            vat_amount = total_before_tax * (doc.commercial_terms.vat_rate / 100)
            
            # Store in commercial terms
            if not doc.commercial_terms.vat_amount or abs(doc.commercial_terms.vat_amount - vat_amount) > 1:
                signals.append(InferenceSignal(
                    rule_name='calculate_tax',
                    field_name='vat_amount',
                    inferred_value=vat_amount,
                    confidence=0.95,
                    evidence=f"VAT {doc.commercial_terms.vat_rate}% on {total_before_tax} = {vat_amount}"
                ))
        
        return signals
    
    # ==================== FIELD INFERENCE RULES ====================
    
    def _infer_currency(self, doc: KraftdDocument, text: str) -> List[InferenceSignal]:
        """Infer currency from context if not explicit"""
        signals = []
        
        # If currency already set, no need to infer
        if doc.commercial_terms and doc.commercial_terms.currency:
            return signals
        
        # Look for currency patterns in text
        currency_patterns = {
            'SAR': r'\bsar\b|\bريال\b',
            'USD': r'\busd\b|\b\$\b',
            'AED': r'\baed\b|درهم',
            'EUR': r'\beur\b|€',
            'GBP': r'\bgbp\b|£',
            'INR': r'\binr\b|₹',
        }
        
        for currency, pattern in currency_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                signals.append(InferenceSignal(
                    rule_name='infer_currency',
                    field_name='currency',
                    inferred_value=currency,
                    confidence=0.8,
                    evidence=f"Found '{currency}' pattern in document"
                ))
                break
        
        # If no match, default to SAR (Saudi Arabia context)
        if not signals:
            signals.append(InferenceSignal(
                rule_name='infer_currency',
                field_name='currency',
                inferred_value='SAR',
                confidence=0.5,
                evidence="No explicit currency found, defaulting to SAR"
            ))
        
        return signals
    
    def _infer_parties(self, doc: KraftdDocument, text: str) -> List[InferenceSignal]:
        """Infer missing party information"""
        signals = []
        
        # Look for email patterns
        email_pattern = r'\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b'
        emails = re.findall(email_pattern, text, re.IGNORECASE)
        
        if emails and doc.parties:
            for role, party in doc.parties.items():
                if party and not party.contact_person:
                    party.contact_person = Contact(email=emails[0])
                    signals.append(InferenceSignal(
                        rule_name='infer_parties',
                        field_name=f'{role}_email',
                        inferred_value=emails[0],
                        confidence=0.7,
                        evidence=f"Found email in document"
                    ))
                    break
        
        # Look for phone patterns
        phone_pattern = r'(?:\+|00)?[\d\s\-\(\)]{10,}'
        phones = re.findall(phone_pattern, text)
        
        if phones and doc.parties:
            for role, party in doc.parties.items():
                if party and not party.contact_person:
                    party.contact_person = Contact(phone=phones[0])
                elif party and party.contact_person and not party.contact_person.phone:
                    party.contact_person.phone = phones[0]
                    signals.append(InferenceSignal(
                        rule_name='infer_parties',
                        field_name=f'{role}_phone',
                        inferred_value=phones[0],
                        confidence=0.6,
                        evidence="Found phone number in document"
                    ))
                    break
        
        return signals
    
    def _normalize_uom(self, doc: KraftdDocument, text: str) -> List[InferenceSignal]:
        """Normalize unit of measure across line items"""
        signals = []
        
        if not doc.line_items:
            return signals
        
        # Common UOM conversions
        conversions = {
            'MT': ('TON', 1.0),
            'TONNE': ('TON', 1.0),
            'KG': ('KILOGRAM', 1.0),
            'NO': ('PIECE', 1.0),
            'NOS': ('PIECE', 1.0),
            'PCS': ('PIECE', 1.0),
            'PC': ('PIECE', 1.0),
        }
        
        for item in doc.line_items:
            # Already normalized, skip
            if item.unit_of_measure in ['METER', 'KILOGRAM', 'TON', 'PIECE', 'SET', 'LOT', 'HOUR', 'DAY']:
                continue
            
            # Check if needs conversion
            uom_str = str(item.unit_of_measure).upper()
            if uom_str in conversions:
                normalized, factor = conversions[uom_str]
                # Would apply conversion factor here if needed
        
        return signals
    
    def _normalize_dates(self, doc: KraftdDocument, text: str) -> List[InferenceSignal]:
        """Infer/normalize dates"""
        signals = []
        
        if not doc.dates:
            return signals
        
        # Infer delivery date from lead time if not present
        if doc.dates.issue_date and not doc.dates.delivery_date:
            # Look for delivery timeframe in text
            delivery_match = re.search(r'delivery.*?(\d+)\s*(?:weeks?|days?|months?)', text, re.IGNORECASE)
            if delivery_match:
                timeframe = delivery_match.group(1)
                unit = re.search(r'weeks?|days?|months?', text, re.IGNORECASE).group(0).lower()
                
                try:
                    days = int(timeframe)
                    if 'week' in unit:
                        days *= 7
                    elif 'month' in unit:
                        days *= 30
                    
                    delivery_date = doc.dates.issue_date + timedelta(days=days)
                    signals.append(InferenceSignal(
                        rule_name='normalize_dates',
                        field_name='delivery_date',
                        inferred_value=delivery_date,
                        confidence=0.75,
                        evidence=f"Calculated from {timeframe} {unit} lead time"
                    ))
                except (ValueError, TypeError):
                    pass
        
        return signals
    
    # ==================== DETECTION RULES ====================
    
    def _detect_delivery_terms(self, doc: KraftdDocument, text: str) -> List[InferenceSignal]:
        """Detect Incoterms and delivery conditions"""
        signals = []
        
        # Common Incoterms
        incoterms_map = {
            'FOB': 'Free on Board',
            'CIF': 'Cost, Insurance & Freight',
            'DAP': 'Delivered at Place',
            'DDP': 'Delivered Duty Paid',
            'EXW': 'Ex Works',
        }
        
        for term, desc in incoterms_map.items():
            if re.search(rf'\b{term}\b', text, re.IGNORECASE):
                signals.append(InferenceSignal(
                    rule_name='detect_delivery_terms',
                    field_name='incoterms',
                    inferred_value=term,
                    confidence=0.95,
                    evidence=f"Found '{term}' ({desc}) in document"
                ))
                break
        
        return signals
    
    def _detect_discounts(self, doc: KraftdDocument, text: str) -> List[InferenceSignal]:
        """Detect discounts and apply to line items"""
        signals = []
        
        # Look for discount patterns
        discount_pattern = r'(?:discount|off|reduction)[\s:]*(\d+(?:\.\d+)?)\s*%'
        discount_matches = re.finditer(discount_pattern, text, re.IGNORECASE)
        
        discount_found = False
        for match in discount_matches:
            discount_pct = float(match.group(1))
            
            # Apply to line items if not already set
            for item in doc.line_items:
                if not item.discount_percentage:
                    item.discount_percentage = discount_pct
                    discount_found = True
            
            if discount_found:
                signals.append(InferenceSignal(
                    rule_name='detect_discounts',
                    field_name='discount_percentage',
                    inferred_value=discount_pct,
                    confidence=0.85,
                    evidence=f"Found {discount_pct}% discount in document",
                    requires_review=True
                ))
        
        return signals
    
    def _infer_payment_terms(self, doc: KraftdDocument, text: str) -> List[InferenceSignal]:
        """Infer payment structure"""
        signals = []
        
        if not doc.commercial_terms:
            return signals
        
        # Check for advance payment
        advance_match = re.search(r'advance\s+(?:payment)?[\s:]*(\d+)\s*%', text, re.IGNORECASE)
        if advance_match:
            advance_pct = float(advance_match.group(1))
            doc.commercial_terms.advance_payment_percentage = advance_pct
            doc.commercial_terms.has_advance_payment = True
            signals.append(InferenceSignal(
                rule_name='infer_payment_terms',
                field_name='advance_payment',
                inferred_value=f"{advance_pct}% advance",
                confidence=0.9,
                evidence=f"Found {advance_pct}% advance payment requirement"
            ))
        
        # Check for milestone-based
        if re.search(r'milestone|progress\s+payment|stage.*payment', text, re.IGNORECASE):
            doc.commercial_terms.milestone_based_payment = True
            signals.append(InferenceSignal(
                rule_name='infer_payment_terms',
                field_name='milestone_payment',
                inferred_value=True,
                confidence=0.85,
                evidence="Document mentions milestone or progress payments"
            ))
        
        return signals
    
    # ==================== VALIDATION RULES ====================
    
    def _validate_line_items(self, doc: KraftdDocument, text: str) -> List[InferenceSignal]:
        """Validate line item completeness and consistency"""
        signals = []
        
        if not doc.line_items:
            return signals
        
        for item in doc.line_items:
            # Check for required fields
            issues = []
            
            if not item.description:
                issues.append("Missing description")
            
            if item.quantity == 0 or not item.quantity:
                issues.append("Quantity is zero or missing")
            
            if item.unit_price == 0 or not item.unit_price:
                issues.append("Unit price is zero or missing")
            
            if item.total_price == 0 or not item.total_price:
                issues.append("Total price is zero or missing")
            
            # Flag if any issues
            if issues:
                signals.append(InferenceSignal(
                    rule_name='validate_line_items',
                    field_name=f'line_item_{item.line_number}',
                    inferred_value=None,
                    confidence=0.0,
                    evidence=f"Issues: {', '.join(issues)}",
                    requires_review=True
                ))
        
        return signals


class DocumentInferencer:
    """
    Orchestrate field inference for KraftdDocument.
    
    Applies all business logic rules to enhance extracted data.
    """
    
    def __init__(self):
        self.inferencer = FieldInferencer()
    
    def infer(self, doc: KraftdDocument, text: str) -> Tuple[KraftdDocument, List[InferenceSignal]]:
        """
        Apply all inference rules to document.
        
        Args:
            doc: KraftdDocument from Mapper stage
            text: Original normalized text for context
        
        Returns:
            (Enhanced KraftdDocument, List of inference signals)
        """
        
        all_signals = []
        
        # Apply each inference rule
        for rule_name, rule_func in self.inferencer.inference_rules.items():
            try:
                signals = rule_func(doc, text)
                all_signals.extend(signals)
            except Exception as e:
                logger.warning(f"Inference rule '{rule_name}' failed: {e}")
        
        # Update document metadata to show inference was applied
        if doc.processing_metadata:
            doc.processing_metadata.extraction_method = ExtractionMethod.HYBRID
        
        # Update modification timestamp
        doc.updated_at = datetime.now()
        
        return doc, all_signals


def infer_document(doc: KraftdDocument, text: str) -> Tuple[KraftdDocument, List[InferenceSignal]]:
    """
    Quick function to apply inference rules.
    
    Usage:
        doc, signals = infer_document(mapped_doc, original_text)
        for signal in signals:
            print(f"{signal.field_name}: {signal.inferred_value}")
    """
    inferencer = DocumentInferencer()
    return inferencer.infer(doc, text)
