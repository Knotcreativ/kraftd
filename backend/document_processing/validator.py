"""
Validator Stage - Completeness & Quality Assessment

Evaluates document completeness and data quality:
- Critical field checking
- Completeness scoring per document type
- Data quality metrics
- Gap identification
- Remediation suggestions
- Risk assessment

Input: Enhanced KraftdDocument from Inferencer
Output: ValidationResult with scores and gaps
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from .schemas import KraftdDocument, DocumentType, LineItem


class CriticalityLevel(str, Enum):
    """Field criticality for each document type"""
    REQUIRED = "required"      # Must have
    IMPORTANT = "important"    # Should have
    OPTIONAL = "optional"      # Nice to have


@dataclass
class FieldGap:
    """A missing or incomplete field"""
    field_name: str
    criticality: CriticalityLevel
    description: str
    remediation: str


@dataclass
class ValidationResult:
    """Validation assessment of a document"""
    document_id: str
    document_type: DocumentType
    
    # Scores
    completeness_score: float  # 0-100% of critical fields present
    data_quality_score: float  # 0-100% based on anomalies
    overall_score: float       # Weighted average
    
    # Gaps
    critical_gaps: List[FieldGap]
    important_gaps: List[FieldGap]
    optional_gaps: List[FieldGap]
    
    # Issues
    warnings: List[str]
    anomalies: List[str]
    
    # Assessment
    ready_for_processing: bool  # Can auto-process?
    requires_manual_review: bool  # Needs human review?
    validation_timestamp: datetime = None
    
    def __post_init__(self):
        if self.validation_timestamp is None:
            self.validation_timestamp = datetime.now()


class CriticalityChecker:
    """Define critical fields per document type"""
    
    def __init__(self):
        self.critical_fields = self._init_critical_fields()
    
    def _init_critical_fields(self) -> Dict[DocumentType, Dict[str, CriticalityLevel]]:
        """Define which fields are critical for each document type"""
        return {
            DocumentType.RFQ: {
                'parties.issuer': CriticalityLevel.REQUIRED,
                'parties.recipient': CriticalityLevel.REQUIRED,
                'metadata.document_number': CriticalityLevel.REQUIRED,
                'dates.issue_date': CriticalityLevel.IMPORTANT,
                'dates.submission_deadline': CriticalityLevel.REQUIRED,
                'line_items': CriticalityLevel.REQUIRED,
                'commercial_terms.currency': CriticalityLevel.IMPORTANT,
            },
            
            DocumentType.BOQ: {
                'parties.issuer': CriticalityLevel.IMPORTANT,
                'metadata.document_number': CriticalityLevel.IMPORTANT,
                'line_items': CriticalityLevel.REQUIRED,
                'line_items.description': CriticalityLevel.REQUIRED,
                'line_items.quantity': CriticalityLevel.REQUIRED,
                'line_items.unit_price': CriticalityLevel.REQUIRED,
                'commercial_terms.currency': CriticalityLevel.IMPORTANT,
            },
            
            DocumentType.QUOTATION: {
                'parties.issuer': CriticalityLevel.REQUIRED,
                'parties.recipient': CriticalityLevel.IMPORTANT,
                'metadata.document_number': CriticalityLevel.REQUIRED,
                'dates.issue_date': CriticalityLevel.IMPORTANT,
                'dates.validity_date': CriticalityLevel.IMPORTANT,
                'line_items': CriticalityLevel.REQUIRED,
                'commercial_terms.currency': CriticalityLevel.REQUIRED,
                'commercial_terms.payment_terms': CriticalityLevel.IMPORTANT,
            },
            
            DocumentType.PO: {
                'parties.issuer': CriticalityLevel.REQUIRED,
                'parties.recipient': CriticalityLevel.REQUIRED,
                'metadata.document_number': CriticalityLevel.REQUIRED,
                'dates.issue_date': CriticalityLevel.REQUIRED,
                'dates.delivery_date': CriticalityLevel.IMPORTANT,
                'line_items': CriticalityLevel.REQUIRED,
                'commercial_terms.currency': CriticalityLevel.REQUIRED,
                'commercial_terms.payment_terms': CriticalityLevel.IMPORTANT,
            },
            
            DocumentType.INVOICE: {
                'parties.issuer': CriticalityLevel.REQUIRED,
                'parties.recipient': CriticalityLevel.REQUIRED,
                'metadata.document_number': CriticalityLevel.REQUIRED,
                'dates.issue_date': CriticalityLevel.REQUIRED,
                'line_items': CriticalityLevel.REQUIRED,
                'commercial_terms.currency': CriticalityLevel.REQUIRED,
            },
            
            DocumentType.CONTRACT: {
                'parties.issuer': CriticalityLevel.REQUIRED,
                'parties.recipient': CriticalityLevel.REQUIRED,
                'metadata.document_number': CriticalityLevel.IMPORTANT,
                'dates.issue_date': CriticalityLevel.IMPORTANT,
                'commercial_terms.currency': CriticalityLevel.IMPORTANT,
            },
        }
    
    def get_critical_fields(self, doc_type: DocumentType) -> Dict[str, CriticalityLevel]:
        """Get critical fields for document type"""
        return self.critical_fields.get(doc_type, {})


class DocumentValidator:
    """
    Validate document completeness and quality.
    
    Checks for:
    - Critical fields present
    - Data consistency
    - Anomalies
    - Completeness score
    """
    
    def __init__(self):
        self.criticality_checker = CriticalityChecker()
    
    def validate(self, doc: KraftdDocument) -> ValidationResult:
        """
        Validate document completeness and quality.
        
        Args:
            doc: KraftdDocument from Inferencer stage
        
        Returns:
            ValidationResult with scores and gaps
        """
        
        critical_gaps = []
        important_gaps = []
        optional_gaps = []
        warnings = []
        anomalies = []
        
        # Get critical fields for this document type
        critical_fields = self.criticality_checker.get_critical_fields(doc.metadata.document_type)
        
        # Check each critical field
        for field_path, criticality in critical_fields.items():
            if not self._field_exists(doc, field_path):
                gap = FieldGap(
                    field_name=field_path,
                    criticality=criticality,
                    description=f"Missing {field_path}",
                    remediation=f"Extract or manually provide {field_path}"
                )
                
                if criticality == CriticalityLevel.REQUIRED:
                    critical_gaps.append(gap)
                elif criticality == CriticalityLevel.IMPORTANT:
                    important_gaps.append(gap)
                else:
                    optional_gaps.append(gap)
        
        # Check for anomalies
        anomalies.extend(self._check_line_item_anomalies(doc))
        anomalies.extend(self._check_party_anomalies(doc))
        anomalies.extend(self._check_date_anomalies(doc))
        
        # Generate warnings
        warnings.extend(self._check_warnings(doc))
        
        # Calculate completeness score
        total_critical = len(critical_gaps) + len([f for f in critical_fields.keys() if self._field_exists(doc, f)])
        completeness_score = 0
        if total_critical > 0:
            completeness_score = (total_critical - len(critical_gaps)) / total_critical * 100
        
        # Calculate data quality score (inverse of anomalies)
        anomaly_count = len(anomalies)
        data_quality_score = max(0, 100 - (anomaly_count * 5))  # 5 points per anomaly
        
        # Overall score (weighted)
        overall_score = (completeness_score * 0.6) + (data_quality_score * 0.4)
        
        # Determine if ready for processing
        ready_for_processing = (
            len(critical_gaps) == 0 and
            anomaly_count < 3 and
            completeness_score >= 80
        )
        
        # Determine if requires review
        requires_review = (
            len(critical_gaps) > 0 or
            anomaly_count >= 2 or
            completeness_score < 90
        )
        
        result = ValidationResult(
            document_id=doc.document_id,
            document_type=doc.metadata.document_type,
            completeness_score=completeness_score,
            data_quality_score=data_quality_score,
            overall_score=overall_score,
            critical_gaps=critical_gaps,
            important_gaps=important_gaps,
            optional_gaps=optional_gaps,
            warnings=warnings,
            anomalies=anomalies,
            ready_for_processing=ready_for_processing,
            requires_manual_review=requires_review
        )
        
        return result
    
    # ==================== FIELD CHECKING ====================
    
    def _field_exists(self, doc: KraftdDocument, field_path: str) -> bool:
        """Check if a field exists and has value"""
        parts = field_path.split('.')
        
        obj = doc
        for part in parts:
            if obj is None:
                return False
            
            # Handle special cases
            if part == 'line_items':
                return bool(obj.line_items)  # Check if list is not empty
            elif part == 'parties':
                return bool(obj.parties and len(obj.parties) > 0)
            elif part == 'description' and isinstance(obj, LineItem):
                return bool(obj.description and len(obj.description.strip()) > 0)
            elif part == 'quantity' and isinstance(obj, LineItem):
                return bool(obj.quantity and obj.quantity > 0)
            elif part == 'unit_price' and isinstance(obj, LineItem):
                return bool(obj.unit_price and obj.unit_price > 0)
            else:
                # Generic attribute access
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                else:
                    return False
        
        # Check final value
        return obj is not None and (not isinstance(obj, str) or len(obj.strip()) > 0)
    
    # ==================== ANOMALY DETECTION ====================
    
    def _check_line_item_anomalies(self, doc: KraftdDocument) -> List[str]:
        """Check for line item anomalies"""
        anomalies = []
        
        if not doc.line_items:
            return anomalies
        
        for i, item in enumerate(doc.line_items):
            # Zero or negative quantity
            if item.quantity <= 0:
                anomalies.append(f"Line item {item.line_number}: Quantity is {item.quantity}")
            
            # Zero or negative price
            if item.unit_price <= 0:
                anomalies.append(f"Line item {item.line_number}: Unit price is {item.unit_price}")
            
            # Missing description
            if not item.description or len(item.description.strip()) == 0:
                anomalies.append(f"Line item {item.line_number}: Missing description")
            
            # Total doesn't match calculation
            if item.total_price:
                expected = item.quantity * item.unit_price
                if abs(expected - item.total_price) > 1:
                    anomalies.append(
                        f"Line item {item.line_number}: Total mismatch "
                        f"(expected {expected}, got {item.total_price})"
                    )
            
            # Very large discount
            if item.discount_percentage and item.discount_percentage > 50:
                anomalies.append(
                    f"Line item {item.line_number}: Unusually high discount "
                    f"({item.discount_percentage}%)"
                )
        
        return anomalies
    
    def _check_party_anomalies(self, doc: KraftdDocument) -> List[str]:
        """Check for party/supplier anomalies"""
        anomalies = []
        
        if not doc.parties:
            anomalies.append("No parties (buyer/supplier) identified")
            return anomalies
        
        # Check if both parties present
        if len(doc.parties) < 2:
            anomalies.append("Missing one of buyer or supplier")
        
        # Check for valid party names
        for role, party in doc.parties.items():
            if not party or not party.name:
                anomalies.append(f"Missing {role} name")
            elif len(party.name) < 3:
                anomalies.append(f"Suspiciously short {role} name: '{party.name}'")
        
        return anomalies
    
    def _check_date_anomalies(self, doc: KraftdDocument) -> List[str]:
        """Check for date anomalies"""
        anomalies = []
        
        if not doc.dates:
            return anomalies
        
        # Check if submission deadline is after issue date
        if doc.dates.issue_date and doc.dates.submission_deadline:
            if doc.dates.submission_deadline <= doc.dates.issue_date:
                anomalies.append(
                    "Submission deadline is not after issue date"
                )
        
        # Check if delivery date is in future
        if doc.dates.delivery_date:
            from datetime import datetime as dt
            if doc.dates.delivery_date < dt.now().date():
                anomalies.append(
                    f"Delivery date {doc.dates.delivery_date} is in the past"
                )
        
        return anomalies
    
    # ==================== WARNINGS ====================
    
    def _check_warnings(self, doc: KraftdDocument) -> List[str]:
        """Generate non-critical warnings"""
        warnings = []
        
        # Check if line items have descriptions that are too short
        if doc.line_items:
            for item in doc.line_items:
                if item.description and len(item.description) < 5:
                    warnings.append(
                        f"Line {item.line_number}: Description too short "
                        f"('{item.description}')"
                    )
        
        # Check for very high prices that might be errors
        if doc.line_items:
            prices = [item.unit_price for item in doc.line_items if item.unit_price]
            if prices:
                avg_price = sum(prices) / len(prices)
                for item in doc.line_items:
                    if item.unit_price > avg_price * 10:
                        warnings.append(
                            f"Line {item.line_number}: Price {item.unit_price} "
                            f"is 10x average ({avg_price})"
                        )
        
        # Check for missing currency
        if not doc.commercial_terms or not doc.commercial_terms.currency:
            warnings.append("Currency not specified")
        
        # Check for missing payment terms
        if not doc.commercial_terms or not doc.commercial_terms.payment_terms:
            warnings.append("Payment terms not specified")
        
        return warnings


def validate_document(doc: KraftdDocument) -> ValidationResult:
    """
    Quick function to validate document.
    
    Usage:
        result = validate_document(enhanced_doc)
        print(f"Completeness: {result.completeness_score:.0f}%")
        print(f"Ready to process: {result.ready_for_processing}")
        for gap in result.critical_gaps:
            print(f"  Missing: {gap.field_name}")
    """
    validator = DocumentValidator()
    return validator.validate(doc)
