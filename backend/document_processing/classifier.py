"""
Universal Document Classifier for Kraftd

Classifies ANY document (any format, any structure) into procurement document types.
Format-agnostic, content-aware, multi-signal scoring.

Handles:
- PDFs, Word, Excel, Images, Text, Scanned, Screenshots
- RFQ, BOQ, Quotation, PO, Invoice, SOW, Item List, Technical Spec
- Structured tables, paragraphs, bullet lists, mixed, handwritten
- Unknown and mixed document types
- Confidence scoring (0-1)
"""

import re
from enum import Enum
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime


class DocumentTypeEnum(str, Enum):
    """All possible document types"""
    RFQ = "RFQ"
    BOQ = "BOQ"
    QUOTATION = "Quotation"
    PO = "PO"
    INVOICE = "Invoice"
    CONTRACT = "Contract"
    SOW = "SOW"  # Scope of Work
    ITEM_LIST = "ItemList"
    TECHNICAL_SPEC = "TechnicalSpec"
    UNKNOWN = "Unknown"
    MIXED = "Mixed"


@dataclass
class ClassificationSignal:
    """A single signal that contributes to classification"""
    signal_name: str
    matched: bool
    weight: float  # How much this signal matters (0-1)
    confidence: float  # How sure we are about this signal (0-1)
    evidence: List[str]  # What we found


@dataclass
class ClassificationResult:
    """Structured classification output"""
    document_type: DocumentTypeEnum
    confidence: float  # Overall confidence 0-1
    method: str  # "keyword", "structure", "hybrid", "user_hint"
    signals: List[ClassificationSignal]  # All signals evaluated
    reasoning: List[str]  # Human-readable explanation
    alternatives: List[Tuple[DocumentTypeEnum, float]]  # Other candidates
    requires_review: bool  # Manual review needed?
    suggested_conversion: Optional[DocumentTypeEnum] = None  # Convert to this type?
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class UniversalClassifier:
    """
    Format-agnostic, content-aware document classifier.
    
    Works on normalized text from any source:
    - PDFs, Word, Excel, Images, Text, Scanned, etc.
    
    Returns confident classification or UNKNOWN/MIXED.
    """

    def __init__(self):
        """Initialize classifier with patterns and weights"""
        self.signals = self._init_signals()
        self.confidence_threshold = 0.60  # Below this = UNKNOWN

    def classify(
        self,
        text: str,
        user_hint: Optional[str] = None,
        file_name: Optional[str] = None
    ) -> ClassificationResult:
        """
        Classify document from normalized text.

        Args:
            text: Normalized text from any document (no file format bias)
            user_hint: User's suggestion ("RFQ", "Quote", etc.) for validation
            file_name: Original filename (for metadata only, NOT used for classification)

        Returns:
            ClassificationResult with type, confidence, signals, reasoning
        """
        # Normalize text for consistent matching
        normalized_text = self._normalize_text(text)

        # Evaluate all signals
        signal_results = self._evaluate_signals(normalized_text)

        # Score each document type
        type_scores = self._score_document_types(signal_results)

        # Determine primary type
        primary_type, primary_confidence = self._select_primary_type(type_scores)

        # Validate against user hint if provided
        if user_hint:
            hint_type = self._parse_user_hint(user_hint)
            if hint_type and hint_type != primary_type:
                # User hint contradicts classification
                if primary_confidence < 0.70:
                    # Low confidence, trust user hint
                    primary_type = hint_type
                    primary_confidence = 0.85  # Boost confidence
                else:
                    # High confidence, flag conflict
                    signal_results.append(
                        ClassificationSignal(
                            signal_name="user_hint_conflict",
                            matched=True,
                            weight=0.1,
                            confidence=0.5,
                            evidence=[f"User suggested {hint_type} but text suggests {primary_type}"]
                        )
                    )

        # Get alternatives (other possible types with scores)
        alternatives = self._get_alternatives(type_scores, primary_type)

        # Detect mixed documents (multiple strong signals)
        is_mixed = self._detect_mixed(type_scores)
        if is_mixed:
            primary_type = DocumentTypeEnum.MIXED
            primary_confidence *= 0.8  # Reduce confidence for mixed

        # Build reasoning
        reasoning = self._build_reasoning(signal_results, primary_type)

        # Determine if review needed
        requires_review = (
            primary_confidence < self.confidence_threshold or
            is_mixed or
            primary_type == DocumentTypeEnum.UNKNOWN
        )

        result = ClassificationResult(
            document_type=primary_type,
            confidence=primary_confidence,
            method=self._determine_method(signal_results),
            signals=signal_results,
            reasoning=reasoning,
            alternatives=alternatives,
            requires_review=requires_review
        )

        return result

    # ==================== TEXT NORMALIZATION ====================

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for consistent pattern matching.
        
        - Lowercase
        - Remove extra whitespace
        - Standardize line breaks
        """
        if not text:
            return ""

        # Lowercase for keyword matching
        text = text.lower()

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove extra punctuation that interferes with matching
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)

        return text.strip()

    # ==================== SIGNAL EVALUATION ====================

    def _init_signals(self) -> Dict:
        """Initialize all classification signals"""
        return {
            # RFQ signals
            "rfq_keywords": {
                "patterns": [
                    r"\brfq\b",
                    r"request for quotation",
                    r"request for quote",
                    r"call for quotation",
                    r"invitation to quote",
                    r"tender inquiry"
                ],
                "weight": 0.6,
                "target_type": DocumentTypeEnum.RFQ
            },
            "rfq_structure": {
                "patterns": [
                    r"submission deadline",
                    r"evaluation criteria",
                    r"required documents",
                    r"submission method",
                    r"supplier qualifications"
                ],
                "weight": 0.3,
                "target_type": DocumentTypeEnum.RFQ
            },

            # BOQ signals
            "boq_keywords": {
                "patterns": [
                    r"\bboq\b",
                    r"bill of quantities",
                    r"bill of quantity",
                    r"quantity schedule",
                    r"itemized list"
                ],
                "weight": 0.6,
                "target_type": DocumentTypeEnum.BOQ
            },
            "boq_structure": {
                "patterns": [
                    r"(qty|quantity|qnt|nos|pieces|units?)",
                    r"(unit price|rate|price per|amount)",
                    r"(description|item|material|specification)"
                ],
                "weight": 0.2,
                "target_type": DocumentTypeEnum.BOQ
            },
            "table_with_numbers": {
                "patterns": [
                    r"\d+\s+[a-z\s]+\s+\d+\s*\.?\d*",  # Row with qty, description, amount
                ],
                "weight": 0.2,
                "target_type": DocumentTypeEnum.BOQ
            },

            # Quotation signals
            "quote_keywords": {
                "patterns": [
                    r"\bquotation\b",
                    r"\bquote\b",
                    r"supplier quote",
                    r"offer price",
                    r"price offer",
                    r"commercial proposal"
                ],
                "weight": 0.6,
                "target_type": DocumentTypeEnum.QUOTATION
            },
            "quote_structure": {
                "patterns": [
                    r"validity (period|date|until|of offer)",
                    r"terms of payment",
                    r"delivery terms",
                    r"warranty",
                    r"after sales support"
                ],
                "weight": 0.3,
                "target_type": DocumentTypeEnum.QUOTATION
            },
            "supplier_signature": {
                "patterns": [
                    r"authorized signature",
                    r"company seal",
                    r"approved by",
                    r"signature:",
                    r"___.*company.*___"
                ],
                "weight": 0.15,
                "target_type": DocumentTypeEnum.QUOTATION
            },

            # PO signals
            "po_keywords": {
                "patterns": [
                    r"\bpo\b",
                    r"\bpo\s*#",
                    r"purchase order",
                    r"order confirmation",
                    r"order number"
                ],
                "weight": 0.7,
                "target_type": DocumentTypeEnum.PO
            },
            "po_structure": {
                "patterns": [
                    r"po\s*(number|date|#).*:\s*\d+",
                    r"(buyer|customer).*:\s*[a-z]",
                    r"(vendor|supplier).*:\s*[a-z]",
                    r"delivery date",
                    r"total order value"
                ],
                "weight": 0.25,
                "target_type": DocumentTypeEnum.PO
            },

            # Invoice signals
            "invoice_keywords": {
                "patterns": [
                    r"\binvoice\b",
                    r"\bbill\b",
                    r"tax invoice",
                    r"proforma invoice",
                    r"receipt"
                ],
                "weight": 0.6,
                "target_type": DocumentTypeEnum.INVOICE
            },
            "invoice_structure": {
                "patterns": [
                    r"invoice\s*(number|#|date).*:\s*\d+",
                    r"amount due",
                    r"total amount",
                    r"tax/gst/vat",
                    r"payment due date",
                    r"bank details"
                ],
                "weight": 0.3,
                "target_type": DocumentTypeEnum.INVOICE
            },
            "invoice_parties": {
                "patterns": [
                    r"bill to.*:",
                    r"ship to.*:",
                    r"from:.*\n",
                    r"sold by:.*purchased by:"
                ],
                "weight": 0.1,
                "target_type": DocumentTypeEnum.INVOICE
            },

            # Contract signals
            "contract_keywords": {
                "patterns": [
                    r"\bagreement\b",
                    r"\bcontract\b",
                    r"terms and conditions",
                    r"scope of work",
                    r"service agreement"
                ],
                "weight": 0.5,
                "target_type": DocumentTypeEnum.CONTRACT
            },
            "contract_structure": {
                "patterns": [
                    r"(1\.|section|clause)\s+[a-z]",
                    r"(hereby|whereas|party|parties)",
                    r"(liability|indemnity|insurance|termination)",
                    r"signature.*date"
                ],
                "weight": 0.3,
                "target_type": DocumentTypeEnum.CONTRACT
            },

            # SOW signals
            "sow_keywords": {
                "patterns": [
                    r"\bsow\b",
                    r"scope of work",
                    r"statement of work",
                    r"work plan",
                    r"deliverables"
                ],
                "weight": 0.6,
                "target_type": DocumentTypeEnum.SOW
            },

            # Technical Spec signals
            "techspec_keywords": {
                "patterns": [
                    r"technical specification",
                    r"technical spec",
                    r"spec sheet",
                    r"specification",
                    r"(astm|iso|din|api|astm)\s+[a-z0-9]"
                ],
                "weight": 0.5,
                "target_type": DocumentTypeEnum.TECHNICAL_SPEC
            },

            # Item List signals
            "item_list_keywords": {
                "patterns": [
                    r"item list",
                    r"parts list",
                    r"material list",
                    r"equipment list"
                ],
                "weight": 0.4,
                "target_type": DocumentTypeEnum.ITEM_LIST
            }
        }

    def _evaluate_signals(self, text: str) -> List[ClassificationSignal]:
        """
        Evaluate all signals against the text.
        
        Returns list of all signal results.
        """
        results = []

        for signal_name, signal_def in self.signals.items():
            matched = False
            evidence = []
            max_confidence = 0

            # Try all patterns in this signal
            for pattern in signal_def["patterns"]:
                matches = re.findall(pattern, text)
                if matches:
                    matched = True
                    evidence.extend(matches[:3])  # Keep first 3 matches
                    max_confidence = max(max_confidence, 0.8)

            # Create signal result
            signal_result = ClassificationSignal(
                signal_name=signal_name,
                matched=matched,
                weight=signal_def["weight"],
                confidence=max_confidence if matched else 0,
                evidence=evidence
            )

            results.append(signal_result)

        return results

    # ==================== SCORING ====================

    def _score_document_types(self, signals: List[ClassificationSignal]) -> Dict[DocumentTypeEnum, float]:
        """
        Score each document type based on matched signals.
        
        Returns: {DocumentType: confidence_score}
        """
        scores = {}

        # Initialize all types with 0 score
        for doc_type in DocumentTypeEnum:
            if doc_type != DocumentTypeEnum.UNKNOWN and doc_type != DocumentTypeEnum.MIXED:
                scores[doc_type] = 0.0

        # Accumulate scores from signals
        for signal in signals:
            if signal.matched:
                # Find what type this signal targets
                target_type = None
                for sig_name, sig_def in self.signals.items():
                    if sig_name == signal.signal_name:
                        target_type = sig_def["target_type"]
                        break

                if target_type and target_type in scores:
                    # Add weighted contribution
                    score_contribution = signal.weight * signal.confidence
                    scores[target_type] += score_contribution

        # Normalize scores to 0-1 range
        max_score = max(scores.values()) if scores.values() else 0
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}

        return scores

    def _select_primary_type(
        self, 
        scores: Dict[DocumentTypeEnum, float]
    ) -> Tuple[DocumentTypeEnum, float]:
        """
        Select primary document type from scores.
        
        If no type has confidence >= threshold, return UNKNOWN.
        """
        if not scores:
            return DocumentTypeEnum.UNKNOWN, 0.0

        # Find highest scoring type
        primary_type = max(scores, key=scores.get)
        primary_score = scores[primary_type]

        # If score too low, mark as UNKNOWN
        if primary_score < self.confidence_threshold:
            return DocumentTypeEnum.UNKNOWN, primary_score

        return primary_type, primary_score

    def _detect_mixed(self, scores: Dict[DocumentTypeEnum, float]) -> bool:
        """
        Detect if document is MIXED (multiple equally strong signals).
        
        Only mark MIXED if multiple document types have VERY strong signals (0.7+).
        This prevents false MIXED detection when one signal dominates.
        E.g., RFQ (0.85) + BOQ (0.3) should be RFQ, not MIXED.
        But RFQ (0.80) + Quotation (0.75) should be MIXED.
        """
        very_strong_signals = [s for s in scores.values() if s >= 0.70]
        
        # Only MIXED if 2+ types have very strong signals AND they're close in score
        if len(very_strong_signals) >= 2:
            # Check if top 2 are within 15 percentage points
            sorted_scores = sorted(scores.values(), reverse=True)
            if len(sorted_scores) >= 2:
                diff = sorted_scores[0] - sorted_scores[1]
                return diff < 0.15  # Scores too close - ambiguous
        
        return False

    def _get_alternatives(
        self,
        scores: Dict[DocumentTypeEnum, float],
        primary_type: DocumentTypeEnum
    ) -> List[Tuple[DocumentTypeEnum, float]]:
        """Get ranked list of alternative document types"""
        alternatives = [
            (doc_type, score)
            for doc_type, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)
            if doc_type != primary_type and score > 0.2
        ]
        return alternatives[:5]  # Top 5 alternatives

    # ==================== USER HINT HANDLING ====================

    def _parse_user_hint(self, user_hint: str) -> Optional[DocumentTypeEnum]:
        """Parse user hint string into DocumentTypeEnum"""
        hint_lower = user_hint.lower().strip()

        # Map various user inputs to enum values
        mapping = {
            "rfq": DocumentTypeEnum.RFQ,
            "request": DocumentTypeEnum.RFQ,
            "inquiry": DocumentTypeEnum.RFQ,
            "tender": DocumentTypeEnum.RFQ,

            "boq": DocumentTypeEnum.BOQ,
            "bill of quantities": DocumentTypeEnum.BOQ,
            "quantities": DocumentTypeEnum.BOQ,

            "quotation": DocumentTypeEnum.QUOTATION,
            "quote": DocumentTypeEnum.QUOTATION,
            "proposal": DocumentTypeEnum.QUOTATION,
            "offer": DocumentTypeEnum.QUOTATION,

            "po": DocumentTypeEnum.PO,
            "purchase order": DocumentTypeEnum.PO,
            "order": DocumentTypeEnum.PO,

            "invoice": DocumentTypeEnum.INVOICE,
            "bill": DocumentTypeEnum.INVOICE,

            "contract": DocumentTypeEnum.CONTRACT,
            "agreement": DocumentTypeEnum.CONTRACT,

            "sow": DocumentTypeEnum.SOW,
            "scope": DocumentTypeEnum.SOW,

            "itemlist": DocumentTypeEnum.ITEM_LIST,
            "item list": DocumentTypeEnum.ITEM_LIST,
            "list": DocumentTypeEnum.ITEM_LIST,

            "techspec": DocumentTypeEnum.TECHNICAL_SPEC,
            "specification": DocumentTypeEnum.TECHNICAL_SPEC,
        }

        return mapping.get(hint_lower)

    # ==================== REASONING ====================

    def _determine_method(self, signals: List[ClassificationSignal]) -> str:
        """Determine classification method used"""
        matched_signals = [s for s in signals if s.matched]
        
        if not matched_signals:
            return "none"
        
        # Check if mostly keyword-based
        keyword_signals = [s for s in matched_signals if "keyword" in s.signal_name]
        structure_signals = [s for s in matched_signals if "structure" in s.signal_name or "table" in s.signal_name]

        if keyword_signals and not structure_signals:
            return "keyword"
        elif structure_signals and not keyword_signals:
            return "structure"
        else:
            return "hybrid"

    def _build_reasoning(self, signals: List[ClassificationSignal], doc_type: DocumentTypeEnum) -> List[str]:
        """Build human-readable reasoning"""
        reasoning = []

        if doc_type == DocumentTypeEnum.UNKNOWN:
            reasoning.append("No strong document type signature found")
            return reasoning

        if doc_type == DocumentTypeEnum.MIXED:
            reasoning.append("Multiple document types detected in same file")
            return reasoning

        # Find signals that matched for this type
        relevant_signals = [
            s for s in signals
            if s.matched and self._signal_targets_type(s.signal_name, doc_type)
        ]

        if not relevant_signals:
            return ["Unable to determine reasoning"]

        # Add specific findings
        for signal in relevant_signals[:3]:  # Top 3 signals
            if signal.evidence:
                evidence_str = ", ".join(signal.evidence[:2])
                reasoning.append(f"Detected {signal.signal_name}: {evidence_str}")
            else:
                reasoning.append(f"Detected {signal.signal_name}")

        return reasoning

    def _signal_targets_type(self, signal_name: str, doc_type: DocumentTypeEnum) -> bool:
        """Check if a signal targets a specific document type"""
        if signal_name not in self.signals:
            return False
        return self.signals[signal_name]["target_type"] == doc_type


# ==================== STANDALONE FUNCTIONS ====================

def classify_document(
    text: str,
    user_hint: Optional[str] = None,
    file_name: Optional[str] = None
) -> ClassificationResult:
    """
    Convenience function for quick classification.
    
    Usage:
        result = classify_document(normalized_text, user_hint="RFQ")
        print(f"{result.document_type} ({result.confidence:.0%})")
    """
    classifier = UniversalClassifier()
    return classifier.classify(text, user_hint, file_name)
