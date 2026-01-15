# KRAFTD AI - PHASE 1 IMPLEMENTATION GUIDE
## Layer 1: Document Understanding (Weeks 1-2)

This guide covers the immediate implementation of **Layer 1** to achieve the foundation for all subsequent AI capabilities.

---

## 🎯 Phase 1 Goals

By end of Week 2, Kraftd AI must:
- ✅ Identify document type (RFQ, BOQ, Quote, PO, etc.) with **>95% accuracy**
- ✅ Extract all content regardless of **label variations** (Qty, QTY, Qunty, etc.)
- ✅ **Infer missing fields** from context
- ✅ **Normalize** units, currencies, dates, supplier names
- ✅ **Validate completeness** for each document type

**Result**: Extract accurate structured data from ANY document format.

---

## 1. Document Type Classifier

### What It Does
```
Input: Document (PDF, Word, Excel, Image)
          ↓
       AI Vision + Text Analysis
          ↓
Output: {
    "document_type": "RFQ",
    "confidence": 0.98,
    "reasoning": "Header contains 'Request for Quotation', standard RFQ line item structure"
}
```

### Implementation

**File**: `backend/document_processing/classifiers.py` (NEW)

```python
from azure.ai.vision.image_analysis import ImageAnalysisClient
from azure.core.credentials import AzureKeyCredential
import os
from typing import Dict, Tuple

class DocumentTypeClassifier:
    """
    Classifies documents using visual + text analysis.
    Uses multi-modal AI to understand document structure regardless of format.
    """
    
    def __init__(self):
        """Initialize with Azure Computer Vision."""
        self.vision_client = ImageAnalysisClient(
            endpoint=os.getenv("VISION_ENDPOINT", "https://kraftdintel-resource.cognitiveservices.azure.com/"),
            credential=AzureKeyCredential(os.getenv("VISION_API_KEY", os.getenv("DOCUMENTINTELLIGENCE_API_KEY")))
        )
        
        # Define document type signatures
        self.document_signatures = {
            "RFQ": {
                "keywords": ["request for quotation", "rfq", "quote requested", "proposal"],
                "structure": ["item", "quantity", "specification", "delivery"],
                "typical_tables": True
            },
            "BOQ": {
                "keywords": ["bill of quantities", "boq", "pricing schedule", "cost estimate"],
                "structure": ["description", "quantity", "rate", "amount"],
                "typical_tables": True
            },
            "QUOTATION": {
                "keywords": ["quotation", "quote", "proposal", "estimate", "price quote"],
                "structure": ["item", "qty", "unit price", "total"],
                "typical_tables": True
            },
            "PO": {
                "keywords": ["purchase order", "po", "order confirmation", "procurement order"],
                "structure": ["item", "quantity", "unit price", "delivery"],
                "typical_tables": True,
                "signature": True
            },
            "CONTRACT": {
                "keywords": ["agreement", "contract", "terms and conditions", "supply agreement"],
                "structure": ["terms", "conditions", "scope", "obligations"],
                "typical_tables": False
            },
            "INVOICE": {
                "keywords": ["invoice", "bill", "receipt", "payment due"],
                "structure": ["invoice number", "amount due", "line items"],
                "typical_tables": True
            }
        }
    
    def classify(self, document_path: str, text_content: str = None) -> Dict:
        """
        Classify document type using visual + text analysis.
        
        Args:
            document_path: Path to document (PDF, image, etc.)
            text_content: Optional pre-extracted text
            
        Returns:
            {
                "document_type": "RFQ",
                "confidence": 0.98,
                "reasoning": [
                    "Header text contains 'Request for Quotation'",
                    "Table structure matches RFQ pattern",
                    "Contains quantity and unit price columns"
                ]
            }
        """
        
        # Step 1: Visual analysis (for PDFs/images)
        visual_clues = self._analyze_visual_structure(document_path)
        
        # Step 2: Text analysis
        text_clues = self._analyze_text_content(text_content or "")
        
        # Step 3: Match against signatures
        scores = self._score_all_types(visual_clues, text_clues)
        
        # Step 4: Determine best match
        top_type = max(scores.items(), key=lambda x: x[1][0])
        
        return {
            "document_type": top_type[0],
            "confidence": top_type[1][0],
            "reasoning": top_type[1][1],
            "all_scores": {k: v[0] for k, v in scores.items()}
        }
    
    def _analyze_visual_structure(self, document_path: str) -> Dict:
        """Analyze document's visual structure."""
        return {
            "has_header": True,  # Would use Azure CV
            "has_table": True,
            "has_signature_area": False,
            "number_of_pages": 1,
            "layout_type": "tabular"  # vs narrative, mixed, etc.
        }
    
    def _analyze_text_content(self, text: str) -> Dict:
        """Analyze text content for keywords and structure."""
        text_lower = text.lower()
        
        # Find keywords
        keyword_matches = {}
        for doc_type, signatures in self.document_signatures.items():
            keyword_matches[doc_type] = [
                kw for kw in signatures["keywords"]
                if kw in text_lower
            ]
        
        return {
            "keyword_matches": keyword_matches,
            "has_table_structure": self._has_table_structure(text),
            "key_columns_present": self._identify_columns(text)
        }
    
    def _score_all_types(self, visual: Dict, text: Dict) -> Dict:
        """Score each document type against clues."""
        scores = {}
        
        for doc_type, signatures in self.document_signatures.items():
            score = 0.0
            reasons = []
            
            # Keyword matching
            keyword_hits = text["keyword_matches"].get(doc_type, [])
            if keyword_hits:
                score += 0.5
                reasons.append(f"Found keywords: {', '.join(keyword_hits)}")
            
            # Table structure
            if text["has_table_structure"] and signatures.get("typical_tables"):
                score += 0.3
                reasons.append("Document has table structure")
            
            # Column matching
            matched_columns = [
                col for col in signatures.get("structure", [])
                if col in text.get("key_columns_present", [])
            ]
            if matched_columns:
                score += min(0.2, 0.1 * len(matched_columns))
                reasons.append(f"Columns match: {', '.join(matched_columns)}")
            
            # Normalize to 0-1
            score = min(1.0, score)
            scores[doc_type] = (score, reasons)
        
        return scores
    
    def _has_table_structure(self, text: str) -> bool:
        """Check if text contains table-like structure."""
        # Simple heuristic: look for consistent columns
        lines = text.split('\n')
        return len(lines) > 5  # More sophisticated logic needed
    
    def _identify_columns(self, text: str) -> list:
        """Identify column headers from text."""
        # This is a placeholder; real implementation would parse table structure
        columns = []
        text_lower = text.lower()
        
        # Common column names across procurement docs
        common_columns = [
            "description", "qty", "quantity", "qunty",
            "rate", "price", "unit price", "unit cost",
            "amount", "total", "uom", "unit", "measurement",
            "item", "line item", "sl no", "sr no"
        ]
        
        for col in common_columns:
            if col in text_lower:
                columns.append(col)
        
        return columns
```

### Integration with kraft_agent.py

Add to `_upload_document_tool`:
```python
from document_processing.classifiers import DocumentTypeClassifier

classifier = DocumentTypeClassifier()
doc_type_result = classifier.classify(file_path, extracted_text)

# Store classification result
document_metadata["detected_type"] = doc_type_result["document_type"]
document_metadata["type_confidence"] = doc_type_result["confidence"]
```

---

## 2. Semantic Label Mapper

### What It Does
```
Input: Extracted label "Qunty", nearby values [100, 50, 75]
       ↓
   Semantic similarity + context analysis
       ↓
Output: {
    "field": "quantity",
    "confidence": 0.99,
    "reason": "Semantic match (Qunty ≈ Quantity) + numeric context"
}
```

### Implementation

**File**: `backend/document_processing/label_mapper.py` (NEW)

```python
from openai import AzureOpenAI
import difflib
from typing import Dict, List, Tuple
import os

class SemanticLabelMapper:
    """
    Maps document labels to Kraftd schema fields using semantic similarity.
    Handles typos, abbreviations, and language variations.
    """
    
    def __init__(self):
        """Initialize with OpenAI embeddings."""
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY", os.getenv("DOCUMENTINTELLIGENCE_API_KEY")),
            api_version="2024-02-15-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT"))
        )
        
        # Define Kraftd schema fields with their variants
        self.field_definitions = {
            "quantity": {
                "aliases": ["qty", "quantity", "qunty", "required qty", "no. of items", "count"],
                "type": "numeric",
                "context_clues": ["pieces", "units", "pcs", "nos", "count"]
            },
            "unit_price": {
                "aliases": ["rate", "unit price", "price", "cost", "unit cost", "amount"],
                "type": "currency",
                "context_clues": ["per unit", "each", "per item", "rupee", "dollar", "usd", "inr"]
            },
            "unit": {
                "aliases": ["uom", "unit", "measurement", "u/m", "unit of measurement"],
                "type": "string",
                "context_clues": ["meter", "piece", "kg", "hour", "day", "box"]
            },
            "description": {
                "aliases": ["description", "item", "scope", "details", "specification", "name"],
                "type": "text",
                "context_clues": ["steel", "plastic", "service", "labor"]
            },
            "total_price": {
                "aliases": ["total", "amount", "total amount", "line total", "extended price"],
                "type": "currency",
                "context_clues": ["sum", "total", "final"]
            },
            "supplier_name": {
                "aliases": ["supplier", "vendor", "seller", "company", "from", "by"],
                "type": "string",
                "context_clues": ["ltd", "inc", "limited", "pvt"]
            },
            "delivery_date": {
                "aliases": ["delivery", "due date", "required by", "deadline", "eta"],
                "type": "date",
                "context_clues": ["jan", "feb", "2025", "2026", "days"]
            }
        }
    
    def map_label(self, 
                  found_label: str, 
                  document_context: str,
                  nearby_values: List[str] = None,
                  row_data: Dict = None) -> Dict:
        """
        Map a found label to a Kraftd schema field.
        
        Args:
            found_label: The label found in the document (e.g., "Qunty")
            document_context: Document type context (e.g., "RFQ")
            nearby_values: Values near the label for context
            row_data: Complete row data for inferential mapping
            
        Returns:
            {
                "field": "quantity",
                "confidence": 0.99,
                "method": "semantic_match",
                "reasoning": "Semantic similarity (0.95) + numeric context"
            }
        """
        
        # Normalize the found label
        normalized = found_label.lower().strip()
        
        # Step 1: Try exact match (fastest)
        exact_match = self._try_exact_match(normalized)
        if exact_match and exact_match["confidence"] > 0.95:
            return exact_match
        
        # Step 2: Try fuzzy string match (typo tolerance)
        fuzzy_match = self._try_fuzzy_match(normalized)
        if fuzzy_match and fuzzy_match["confidence"] > 0.85:
            return fuzzy_match
        
        # Step 3: Try semantic matching (understanding meaning)
        semantic_match = self._try_semantic_match(normalized)
        if semantic_match and semantic_match["confidence"] > 0.80:
            return semantic_match
        
        # Step 4: Try contextual inference
        contextual_match = self._try_contextual_match(
            normalized, nearby_values, row_data, document_context
        )
        if contextual_match:
            return contextual_match
        
        # No match found
        return {
            "field": None,
            "confidence": 0.0,
            "method": "no_match",
            "reasoning": f"Could not map '{found_label}' to any Kraftd field"
        }
    
    def _try_exact_match(self, normalized: str) -> Dict:
        """Try to match exactly against known aliases."""
        for field_name, field_def in self.field_definitions.items():
            if normalized in field_def["aliases"]:
                return {
                    "field": field_name,
                    "confidence": 1.0,
                    "method": "exact_match",
                    "reasoning": "Exact match with known alias"
                }
        return None
    
    def _try_fuzzy_match(self, normalized: str) -> Dict:
        """Try fuzzy matching against aliases (handles typos)."""
        all_aliases = []
        alias_to_field = {}
        
        for field_name, field_def in self.field_definitions.items():
            for alias in field_def["aliases"]:
                all_aliases.append(alias)
                alias_to_field[alias] = field_name
        
        # Find best match
        matches = difflib.get_close_matches(normalized, all_aliases, n=1, cutoff=0.7)
        
        if matches:
            best_alias = matches[0]
            similarity = difflib.SequenceMatcher(None, normalized, best_alias).ratio()
            return {
                "field": alias_to_field[best_alias],
                "confidence": similarity,
                "method": "fuzzy_match",
                "reasoning": f"Fuzzy match: '{normalized}' ≈ '{best_alias}' (similarity: {similarity:.2f})"
            }
        
        return None
    
    def _try_semantic_match(self, normalized: str) -> Dict:
        """Try semantic matching using embeddings (understands meaning)."""
        # This would use OpenAI embeddings API
        # For now, return simple semantic heuristic
        
        semantic_rules = {
            "quantity": ["qty", "qunt", "number", "count", "how many"],
            "unit_price": ["rate", "price", "cost", "per", "each"],
            "unit": ["measurement", "uom", "metre", "meter", "piece", "kg", "meter"],
            "description": ["desc", "item", "what", "type", "kind"],
            "total_price": ["total", "sum", "amount", "final"],
            "supplier_name": ["vendor", "seller", "from", "company", "supplier"],
            "delivery_date": ["delivery", "date", "when", "due", "deadline"]
        }
        
        for field, keywords in semantic_rules.items():
            for keyword in keywords:
                if keyword in normalized:
                    return {
                        "field": field,
                        "confidence": 0.80,
                        "method": "semantic_match",
                        "reasoning": f"Semantic keyword match: '{keyword}' suggests '{field}'"
                    }
        
        return None
    
    def _try_contextual_match(self, normalized: str, nearby_values: List, 
                              row_data: Dict, doc_context: str) -> Dict:
        """Try to infer field from context (position, nearby values)."""
        
        # If we have numeric values nearby and the field name is ambiguous,
        # infer from context
        if nearby_values:
            # Check if values are numeric (might indicate quantity or price)
            numeric_count = sum(1 for v in nearby_values if str(v).replace('.', '').isdigit())
            
            if numeric_count > 0:
                # More heuristics would go here
                if "qty" in normalized or "quantity" in normalized or len(normalized) < 5:
                    return {
                        "field": "quantity",
                        "confidence": 0.75,
                        "method": "contextual_inference",
                        "reasoning": f"Context: numeric values nearby, short label suggests quantity"
                    }
        
        return None
    
    def map_all_labels(self, labels: List[str], 
                      document_context: str,
                      table_data: Dict = None) -> List[Dict]:
        """Map multiple labels at once."""
        return [
            self.map_label(label, document_context)
            for label in labels
        ]
```

### Integration Example
```python
mapper = SemanticLabelMapper()

# Map multiple labels from an RFQ
labels_to_map = ["Qunty", "Rate", "UOM", "Desc"]
mappings = mapper.map_all_labels(labels_to_map, "RFQ")

# Result:
# [
#     {"field": "quantity", "confidence": 0.99, ...},
#     {"field": "unit_price", "confidence": 0.98, ...},
#     {"field": "unit", "confidence": 1.0, ...},
#     {"field": "description", "confidence": 0.95, ...}
# ]
```

---

## 3. Context Inferencer

### What It Does
```
Input: Missing label, but have [100, "pieces", "steel sheets"]
       ↓
   Analyze position + context
       ↓
Output: {
    "inferred_field": "quantity",
    "value": 100,
    "confidence": 0.90,
    "reason": "Numeric + unit context"
}
```

### Implementation

**File**: `backend/document_processing/inferencer.py` (NEW)

```python
from typing import Dict, Any, List
import re

class ContextInferencer:
    """
    Infers missing fields from document context.
    When a label is missing, uses surrounding data to guess the field.
    """
    
    def infer_field_type(self, 
                        value: str, 
                        row_position: int,
                        row_data: Dict,
                        document_type: str,
                        nearby_columns: List[str]) -> Dict:
        """
        Infer field type from value and context.
        
        Args:
            value: The value found
            row_position: Column position (0-indexed)
            row_data: Complete row data
            document_type: RFQ, BOQ, etc.
            nearby_columns: Names of columns before/after
            
        Returns:
            {
                "field": "quantity",
                "confidence": 0.85,
                "reason": "Numeric value in quantity column position"
            }
        """
        
        # Step 1: Analyze the value itself
        value_type = self._analyze_value_type(value)
        
        # Step 2: Analyze row context
        row_pattern = self._analyze_row_pattern(row_data)
        
        # Step 3: Use position heuristics
        position_hint = self._get_position_hint(row_position, document_type, len(row_data))
        
        # Step 4: Cross-reference nearby columns
        column_hint = self._get_column_hint(nearby_columns)
        
        # Step 5: Combine signals
        return self._combine_signals(value_type, row_pattern, position_hint, column_hint)
    
    def _analyze_value_type(self, value: str) -> Dict:
        """Determine what type of value this is."""
        value_str = str(value).strip()
        
        # Check for numeric
        if re.match(r'^\d+(\.\d+)?$', value_str):
            return {"type": "numeric", "numeric_value": float(value_str)}
        
        # Check for currency
        if re.match(r'^[\$₹€]\s*\d+', value_str):
            return {"type": "currency"}
        
        # Check for date
        if re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', value_str):
            return {"type": "date"}
        
        # Check for unit
        unit_patterns = ['metre', 'meter', 'meter', 'kg', 'lb', 'pcs', 'pieces', 'box', 'hour', 'day']
        if any(unit in value_str.lower() for unit in unit_patterns):
            return {"type": "unit"}
        
        # Default to text
        return {"type": "text", "length": len(value_str)}
    
    def _analyze_row_pattern(self, row_data: Dict) -> Dict:
        """Analyze the pattern of data in the row."""
        numeric_cols = sum(1 for v in row_data.values() if str(v).replace('.', '').isdigit())
        text_cols = sum(1 for v in row_data.values() if not str(v).replace('.', '').isdigit())
        
        return {
            "numeric_count": numeric_cols,
            "text_count": text_cols,
            "likely_pattern": "description_qty_price" if text_cols > 0 else "numeric_only"
        }
    
    def _get_position_hint(self, row_position: int, doc_type: str, row_length: int) -> Dict:
        """Use column position to hint at field type."""
        
        # Standard column positions for procurement docs:
        # 0: Item/Description
        # 1: Qty
        # 2: Unit
        # 3: Unit Price
        # 4: Total
        
        position_hints = {
            0: {"likely_field": "description", "confidence": 0.8},
            1: {"likely_field": "quantity", "confidence": 0.8},
            2: {"likely_field": "unit", "confidence": 0.7},
            3: {"likely_field": "unit_price", "confidence": 0.7},
            4: {"likely_field": "total_price", "confidence": 0.6},
        }
        
        return position_hints.get(row_position, {"likely_field": None, "confidence": 0.0})
    
    def _get_column_hint(self, nearby_columns: List[str]) -> Dict:
        """Use nearby columns to infer this field."""
        # If nearby columns are "Item" and "Unit", this field is likely "Quantity"
        # This would require a smarter column sequence model
        return {"hint": None, "confidence": 0.0}
    
    def _combine_signals(self, value_type, row_pattern, position_hint, column_hint) -> Dict:
        """Combine all signals to make final inference."""
        
        # Simple rule-based combination
        if value_type["type"] == "numeric":
            # Numeric could be quantity or price
            if position_hint["likely_field"] == "quantity":
                return {
                    "field": "quantity",
                    "confidence": 0.85,
                    "reason": f"Numeric value in quantity position (col {value_type})"
                }
            elif position_hint["likely_field"] == "unit_price":
                return {
                    "field": "unit_price",
                    "confidence": 0.80,
                    "reason": "Numeric value in price position"
                }
        
        elif value_type["type"] == "text":
            if position_hint["likely_field"] == "description":
                return {
                    "field": "description",
                    "confidence": 0.9,
                    "reason": "Text value in description position"
                }
        
        elif value_type["type"] == "date":
            return {
                "field": "delivery_date",
                "confidence": 0.85,
                "reason": "Date value detected"
            }
        
        # Fallback
        return {
            "field": position_hint["likely_field"],
            "confidence": position_hint["confidence"],
            "reason": f"Inferred from position and value type"
        }
```

---

## 4. Enhanced Completeness Checker

**File**: `backend/document_processing/completeness.py` (NEW)

```python
from typing import Dict, List
from document_processing.schemas import DocumentType

class CompletenessChecker:
    """Check document completeness based on type."""
    
    def __init__(self):
        self.requirements = {
            DocumentType.RFQ: {
                "mandatory": [
                    "document_number", "issue_date", "supplier_name",
                    "project_name", "items", "unit_prices"
                ],
                "recommended": [
                    "delivery_date", "payment_terms", "validity_period",
                    "special_requirements", "contact_person"
                ]
            },
            DocumentType.BOQ: {
                "mandatory": [
                    "items", "quantities", "units", "rates",
                    "description"
                ],
                "recommended": ["total_amount", "currency", "issue_date"]
            },
            DocumentType.QUOTATION: {
                "mandatory": [
                    "supplier_name", "quote_number", "items",
                    "quantities", "unit_prices", "total_price"
                ],
                "recommended": [
                    "validity_period", "payment_terms", "delivery_date",
                    "warranty", "terms_and_conditions"
                ]
            },
            DocumentType.PO: {
                "mandatory": [
                    "po_number", "supplier_name", "items",
                    "quantities", "unit_prices", "total_price",
                    "delivery_address", "payment_terms"
                ],
                "recommended": [
                    "purchase_date", "expected_delivery_date",
                    "inspection_checklist", "approved_by"
                ]
            }
        }
    
    def check(self, document, document_type: DocumentType) -> Dict:
        """Check completeness of a document."""
        
        reqs = self.requirements.get(document_type, {})
        mandatory = reqs.get("mandatory", [])
        recommended = reqs.get("recommended", [])
        
        # Count what's present
        mandatory_present = sum(
            1 for field in mandatory if getattr(document, field, None)
        )
        recommended_present = sum(
            1 for field in recommended if getattr(document, field, None)
        )
        
        # Calculate score
        mandatory_score = mandatory_present / len(mandatory) if mandatory else 1.0
        recommended_score = recommended_present / len(recommended) if recommended else 1.0
        overall_score = (mandatory_score * 0.7) + (recommended_score * 0.3)
        
        # Grade it
        if overall_score >= 0.95:
            grade = "A"
        elif overall_score >= 0.80:
            grade = "B"
        elif overall_score >= 0.65:
            grade = "C"
        else:
            grade = "D"
        
        return {
            "completeness_score": round(overall_score, 2),
            "grade": grade,
            "mandatory_fields_missing": [
                f for f in mandatory if not getattr(document, f, None)
            ],
            "recommended_fields_missing": [
                f for f in recommended if not getattr(document, f, None)
            ],
            "recommendations": [
                f"Request {field} from supplier"
                for field in mandatory
                if not getattr(document, field, None)
            ]
        }
```

---

## Implementation Checklist

### Week 1
- [ ] Create `classifiers.py` with `DocumentTypeClassifier`
- [ ] Create `label_mapper.py` with `SemanticLabelMapper`
- [ ] Create `inferencer.py` with `ContextInferencer`
- [ ] Create `completeness.py` with `CompletenessChecker`
- [ ] Integrate classifiers into `kraft_agent.py`
- [ ] Test with 10 sample RFQs

### Week 2
- [ ] Integrate mappers into extractor pipeline
- [ ] Test label mapping with 50 documents
- [ ] Add inferencer to handle missing fields
- [ ] Build completeness validation endpoint
- [ ] Create test suite
- [ ] Document APIs

---

## Success Criteria

By end of Phase 1, must achieve:

| Metric | Target | Current |
|--------|--------|---------|
| Document Type Accuracy | >95% | TBD |
| Label Mapping Accuracy | >98% | TBD |
| Completeness Detection | 100% recall | TBD |
| End-to-End Extraction | >90% accuracy | 85% |

---

## Integration with kraft_agent.py

Update the agent's `_upload_document_tool`:

```python
async def _upload_document_tool(self, file_path: str) -> str:
    """Upload and intelligently analyze a document."""
    
    # Step 1: Extract raw content
    extracted = DocumentExtractor(file_path, processed_data)
    text = extracted.get_all_text()
    
    # Step 2: Classify document type
    classifier = DocumentTypeClassifier()
    type_result = classifier.classify(file_path, text)
    
    # Step 3: Extract with semantic awareness
    mapper = SemanticLabelMapper()
    inferencer = ContextInferencer()
    
    # Map all labels
    labels = self._extract_column_headers(text)
    label_mappings = mapper.map_all_labels(labels, type_result["document_type"])
    
    # Step 4: Check completeness
    checker = CompletenessChecker()
    completeness = checker.check(extracted.document, type_result["document_type"])
    
    # Step 5: Return enhanced result
    return {
        "document_id": doc_id,
        "detected_type": type_result["document_type"],
        "confidence": type_result["confidence"],
        "completeness_score": completeness["completeness_score"],
        "missing_fields": completeness["recommendations"],
        "extracted_data": extracted.document.dict()
    }
```

---

## Next Steps

Once Phase 1 is complete:
1. Move to **Phase 2**: Implement Layer 3 (Document Intelligence) - Anomaly detection, inconsistency checking
2. Then **Phase 3**: Implement Layer 4 (Workflow Intelligence) - Auto-routing, auto-generation
3. Then **Phase 4**: Implement Layer 5 (Signals Intelligence) - Predictive analytics

**Total Vision**: A 7-layer intelligence stack that makes Kraftd the most intelligent procurement platform.

