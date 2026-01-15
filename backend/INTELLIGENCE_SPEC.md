# Kraftd Docs — Document Intelligence Specification v1.0

## Overview
This specification defines what Kraftd should "see," extract, normalize, and surface when processing RFQs, BOQs, quotations, POs, contracts, and invoices. It serves as the foundation for document intelligence and the future Signals layer.

---

## 1. Global Document Metadata

### Document Identification
```
document_type: RFQ | BOQ | Quotation | PO | Contract | Addendum | Invoice
document_number: string (e.g., RFQ-2024-001, PO-SAP-12345)
revision_number: string (e.g., "Rev 1", "v2")
issue_date: date
page_count: int
pages_present: "X of Y"
user_intent: sell | buy | estimate | consult | inquire
```

### Parties
```
issuer:
  name: string (company/department)
  legal_entity: string
  trn_vat_number: string
  contact_person: name, email, phone
  registered_address: full address
  project_address: (if different)
  billing_address: (if different)

recipient:
  name: string (supplier, contractor, buyer)
  legal_entity: string
  trn_vat_number: string
  contact_person: name, email, phone
  addresses: [registered, project, delivery]
```

### Project Context
```
project_name: string
project_code: string
client_name: string
end_user: string
location: string (site, city, region)
discipline: civil | mechanical | electrical | instrumentation | mixed
package: string (e.g., "Piping Package A", "HVAC Supply")
```

### Dates
```
issue_date: date
submission_deadline: date (RFQ/quotations)
validity_date: date (quotations)
contract_start_date: date
contract_end_date: date
delivery_date: date
```

### Commercial Terms
```
currency: SAR | USD | AED | EUR | (other)
tax_vat_mentioned: boolean
vat_rate: float (%)
incoterms: FOB | CIF | DAP | DDP | Ex Works | (other)
payment_terms: string (e.g., "30 days from invoice", "50% advance, 50% on delivery")
performance_guarantee: boolean
retention_percentage: float (%)
warranty_period: string (e.g., "12 months")
```

---

## 2. Line Item–Level Data (Core Table)

This is the heart of RFQs, BOQs, and quotations. All line items normalize to:

```
line_number: int
item_code: string (material code, part number)
drawing_reference: string (if present)
wbs_code: string (if present)
description: string (often multi-line; normalize to single sentence)
technical_spec: string (e.g., ASTM A36, ISO 9001)
model_brand: string (e.g., "Grundfos pump", "ASME Class 300")

quantity: float
unit_of_measure: m | m2 | m3 | kg | ton | liter | piece | set | lot | hour | day | each
min_quantity: float (if framework)
max_quantity: float (if blanket)

unit_price: float
total_price: float (quantity * unit_price)
currency: SAR | USD | (same as document or mixed)
discount_percentage: float (%)
discount_amount: float

delivery_time: string (e.g., "4 weeks", "45 days")
delivery_location: string (site, warehouse, port)
packaging_notes: string (if present)

status_flags: optional | mandatory | alternative | equivalent | excluded | revised
notes: string (any additional line-level notes)
```

---

## 3. RFQ and Inquiry Documents

### Scope Definition
```
packages_included: [string] (e.g., ["Supply", "Installation", "Testing"])
packages_excluded: [string]
work_type: supply_only | supply_and_install | turnkey | design_build
```

### Submission Instructions
```
submission_method: email | portal | sealed_envelope | other
submission_address: string (email, portal URL, physical address)
required_documents: [string] (e.g., ["Technical Offer", "Commercial Offer", "Compliance Sheet"])
number_of_copies: int
required_formats: [string] (e.g., ["PDF", "Excel"])
```

### Evaluation Criteria
```
technical_score_weight: float (%)
commercial_score_weight: float (%)
mandatory_compliance_points: [string]
prequalification_requirements: [string]
scoring_method: best_price | best_value | technical_first | other
```

### Conditions and Constraints
```
liquidated_damages: float (%) per day
performance_penalties: [string]
mandatory_guarantees: [string]
retention_percentage: float (%)
bond_requirement: boolean
insurance_requirement: string (if present)
```

---

## 4. Supplier Quotations

### Quotation Metadata
```
quotation_number: string
quotation_date: date
supplier_name: string
supplier_legal_entity: string
supplier_trn_vat: string
supplier_contact: name, email, phone, bank_account
offer_validity: date
```

### Offer Structure
```
linked_rfq_number: string (if responding to specific RFQ)
delivery_terms: string (FOB, CIF, DAP, etc.)
payment_terms: string
discount_structure: [line_level | overall | tiered]
overall_discount: float (%)
```

### Deviations and Conditions
```
deviations_from_rfq: [
  {
    item_line: int,
    deviation_type: price | delivery | spec | payment | warranty | other,
    deviation_description: string,
    impact: critical | major | minor,
    reason: string
  }
]
exclusions: [string] (items not quoted)
clarifications: [string] (supplier's notes)
warranty_terms: string
after_sales_support: string
```

### Quotation Summary
```
total_quoted_value: float
currency: SAR | USD | (other)
vat_amount: float
final_amount: float (including VAT)
```

---

## 5. Purchase Orders (POs)

### PO Metadata
```
po_number: string
po_date: date
buyer_name: string
supplier_name: string
linked_rfq_number: string
linked_quotation_number: string
```

### Scope
```
line_items: [normalized line item schema above]
split_deliveries: [
  {
    delivery_number: int,
    delivery_date: date,
    items: [line_numbers],
    location: string,
    quantity_portion: float (%)
  }
]
```

### Commercial Terms
```
po_value: float
currency: SAR | USD | (other)
vat_rate: float (%)
total_po_value: float
agreed_prices_vs_quoted: [
  {
    line: int,
    quoted_price: float,
    po_price: float,
    variance: float (%)
  }
]
payment_milestone: [
  {
    milestone: int,
    description: string,
    payment_percentage: float (%),
    trigger_condition: string
  }
]
```

### Risk and Performance Terms
```
liquidated_damages: float (%) per day
performance_guarantee: boolean
retention_percentage: float (%)
termination_clause: string (if present)
change_order_procedure: string (if present)
```

---

## 6. Contracts and Frameworks

### Contract Metadata
```
contract_number: string
contract_type: service | supply | construction | framework | other
effective_date: date
duration: string (e.g., "12 months", "24 months from effective date")
parties: [issuer, recipient as defined above]
```

### Scope of Work
```
scope_summary: string (high-level)
deliverables: [string]
locations: [string]
disciplines: [civil, mechanical, electrical, etc.]
```

### Payment Structure
```
payment_basis: lump_sum | unit_rate | cost_plus | milestone_based | hybrid
milestones: [
  {
    milestone_number: int,
    description: string,
    condition: string,
    payment_percentage: float (%),
    due_date: date
  }
]
total_contract_value: float
currency: SAR | USD | (other)
```

### Risk and Legal Clauses
```
indemnity_clause: present (boolean)
liability_cap: float (if present)
force_majeure: present (boolean)
insurance_required: string (if present)
dispute_resolution: arbitration | litigation | negotiation | other
termination_conditions: [string]
change_management: present (boolean)
```

---

## 7. Signals-Oriented Fields

These fields support future Kraftd Signals layer and predictive analytics:

### Categorization
```
commodity_category: steel | concrete | valves | cables | labor | services | equipment | other
subcategory: string (more specific)
supplier_tier: tier1 | tier2 | tier3 | unrated
spend_category: capex | opex | strategic | tactical
```

### Risk Indicators
```
validity_days: int (days between quotation date and expiry)
price_confidence: high | medium | low (based on deviations, alternatives)
aggressive_discount: boolean (discount > 20%)
heavy_deviations: boolean (count > 3)
long_lead_time: boolean (> 12 weeks)
rare_commodity: boolean (only 1 supplier available)
```

### Behavioral Patterns (built over time)
```
supplier_on_time_rate: float (%)
supplier_deviation_frequency: int
supplier_price_consistency: high | medium | low
supplier_payment_term_variance: boolean
supplier_warranty_reliability: high | medium | low
item_variation_frequency: int (how often re-quoted/changed)
item_availability_risk: low | medium | high
```

### Project Phase
```
phase: tender | execution | variation | close_out | framework | standing_order
criticality: critical_path | on_path | buffer | non_critical
```

---

## 8. Normalized Output Format

All extracted intelligence flows into this unified structure:

```json
{
  "document_id": "uuid",
  "document_type": "RFQ | BOQ | Quotation | PO | Contract | Invoice",
  "metadata": { ... },
  "parties": { ... },
  "project_context": { ... },
  "dates": { ... },
  "commercial_terms": { ... },
  "line_items": [ ... ],
  "document_specific": {
    "rfq_data": { ... } | null,
    "quotation_data": { ... } | null,
    "po_data": { ... } | null,
    "contract_data": { ... } | null
  },
  "signals": {
    "categorization": { ... },
    "risk_indicators": { ... },
    "behavioral_patterns": { ... },
    "phase": string
  },
  "extraction_confidence": {
    "overall_confidence": float (0-1),
    "field_confidence": {
      "parties": float,
      "line_items": float,
      "dates": float,
      "commercial_terms": float
    },
    "missing_fields": [string],
    "flags": [string] (warnings, inconsistencies)
  }
}
```

---

## 9. Implementation Notes

### Extraction Priority
1. **Always extract:** document type, parties, dates, line items
2. **Extract when present:** project context, commercial terms, deviations
3. **Best-effort:** specific RFQ/quotation/contract clauses
4. **Signals:** categorize and flag for future analysis

### Confidence Scoring
- **High (0.9+):** Direct table/structured extraction
- **Medium (0.6-0.9):** Regex/pattern matching, some manual validation needed
- **Low (<0.6):** NLP/model-based, requires human review

### Future Enhancements
- Integrate Azure Form Recognizer for high-fidelity extraction
- Add OpenAI GPT-4/5 for contract clause interpretation
- Build behavioral analytics into Signals layer
- Enable ML-based anomaly detection for risk flagging

---

## 10. Success Metrics for Intelligence Layer

- **Accuracy:** 90%+ accuracy on line items, quantities, prices
- **Completeness:** 85%+ of extractable fields populated
- **Speed:** < 2 seconds to extract and normalize per document
- **Traceability:** Full audit trail of extracted vs. original data
