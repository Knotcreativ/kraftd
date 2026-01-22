# KRAFTD AI INTELLIGENCE SPECIFICATION
## Complete 7-Layer AI Responsibility Map

**Vision**: AI evolves from extracting documents → understanding procurement → predicting risk → guiding decisions.

---

## 🎯 Executive Summary

Kraftd requires a **layered intelligence system** that progressively deepens AI capability:

```
Layer 7: System Intelligence    (Endgame: Strategic guidance)
Layer 6: Learning & Adaptation  (Self-improving from feedback)
Layer 5: Signals Intelligence   (Predictive alerts & recommendations)
Layer 4: Workflow Intelligence  (Auto-routing, validation, generation)
Layer 3: Document Intelligence  (Reasoning & anomaly detection)
Layer 2: Procurement Intelligence (Schema mapping & normalization)
Layer 1: Document Understanding  (Extraction & semantic interpretation)
```

---

## LAYER 1: Document Understanding ✅ (30% Complete)

### Goal
AI understands ANY document structure and extracts content with semantic intelligence.

### Current Status
- ✅ **Type Detection**: PDFProcessor, WordProcessor, ExcelProcessor, ImageProcessor ready
- ✅ **Content Extraction**: Tables, text, paragraphs extracted via local + Azure DI
- ⚠️ **Semantic Understanding**: Basic keyword matching, needs enhancement
- ❌ **Flexible Mapping**: Hardcoded field mapping, needs fuzzy matching
- ❌ **Inferential Extraction**: No inference capability for missing labels

### What Exists
**File**: `backend/document_processing/`
- `base_processor.py` - Abstract processor pattern
- `pdf_processor.py` - PDF handling (pdfplumber)
- `word_processor.py` - DOCX handling (python-docx)
- `excel_processor.py` - XLSX handling (openpyxl)
- `image_processor.py` - OCR via pytesseract
- `extractor.py` - Structured data extraction
- `azure_service.py` - Azure Document Intelligence integration

### Requirements to Implement

#### A. Document Type Recognition ❌
```python
# Current: Hardcoded by file extension
# Needed: AI-based document classification

document_classifier = DocumentTypeClassifier(
    model="gpt-4-turbo",  # Visual understanding
    confidence_threshold=0.95
)

detected_type = document_classifier.identify(
    image_of_first_page,
    text_content,
    table_structure
)
# Returns: DocumentType.RFQ, confidence=0.98
```

**Implementation Plan**:
1. Create `DocumentTypeClassifier` class
2. Train on Kraftd document samples
3. Use multi-modal LLM (vision + text)
4. Return confidence scores

#### B. Flexible Label Mapping ❌
```python
# Current: "Quantity", "QTY" → quantity (hardcoded)
# Needed: Semantic similarity matching

label_mapper = SemanticLabelMapper()

mapped_field = label_mapper.map(
    found_label="Qunty",
    document_context="procurement RFQ",
    nearby_values=[100, 50, 75]  # numeric context
)
# Returns: (field="quantity", confidence=0.99, reason="semantic match + numeric context")
```

**Implementation Plan**:
1. Create `SemanticLabelMapper` using embeddings (e.g., OpenAI embeddings)
2. Build label dictionary with semantic variants
3. Use contextual clues (document type, nearby values)
4. Return confidence + reasoning

#### C. Inferential Extraction ❌
```python
# Current: Missing label = missing data
# Needed: Infer from context

inferencer = ContextInferencer(
    document_type="RFQ",
    extracted_fields={...}
)

inferred_quantity = inferencer.infer_missing(
    target_field="quantity",
    nearby_values={"100", "units", "qty"},
    row_position=2,
    context="procurement document"
)
# Returns: (value=100, confidence=0.85, source="inferred from context")
```

**Implementation Plan**:
1. Create `ContextInferencer` class
2. Build inference rules based on document type
3. Analyze position, neighboring values, document structure
4. Assign confidence scores

---

## LAYER 2: Procurement Intelligence ✅ (50% Complete)

### Goal
Map extracted data into Kraftd schema with normalization.

### Current Status
- ✅ **Schema Defined**: `document_processing/schemas.py` (500+ lines)
- ✅ **Basic Mapping**: Extractor maps to KraftdDocument
- ⚠️ **Normalization**: Partial (units, currency, dates)
- ⚠️ **Validation**: Basic checks exist
- ❌ **Deviations Tracking**: Not implemented

### What Exists
**File**: `backend/document_processing/schemas.py`
- `LineItem` - Individual procurable items
- `DocumentMetadata` - Doc info (number, date, supplier, etc.)
- `CommercialTerms` - Warranty, penalties, retention, etc.
- `KraftdDocument` - Complete normalized document

### Requirements to Implement

#### A. Enhanced Normalization ⚠️
```python
# Current: Basic string replacement
# Needed: Intelligent normalization

normalizer = ProcurementNormalizer(
    project_context={
        "currency": "USD",
        "expected_units": ["pieces", "meters", "hours"],
        "supplier_list": [...]
    }
)

normalized = normalizer.normalize_quantity(
    value="100 pcs",
    item_context={"description": "steel sheets"}
)
# Returns: (quantity=100, unit="pieces", standardized_unit="PCS")

normalized_price = normalizer.normalize_currency(
    value="10,000.50 INR",
    document_currency="INR",
    target_currency="USD"
)
# Returns: (amount=120.50, currency="USD", exchange_rate=0.012, as_of_date="2026-01-15")

normalized_date = normalizer.normalize_date(
    value="15/01/2026 OR 2026-01-15 OR Jan 15 2026",
    document_context="RFQ issued"
)
# Returns: (date="2026-01-15", format="ISO8601", confidence=0.99)
```

**Implementation Plan**:
1. Create `ProcurementNormalizer` class
2. Add currency conversion via API (XE.com, OANDA)
3. Build unit conversion library
4. Date format unification

#### B. Deviation Tracking ❌
```python
# Deviations from RFQ specifications

deviation_tracker = DeviationTracker(
    rfq_document=rfq,
    quotation_document=quote
)

deviations = deviation_tracker.find_all()
# Returns: [
#     {
#         "type": "quantity_variation",
#         "rfq_value": 100,
#         "quoted_value": 95,
#         "variance_percent": -5.0,
#         "severity": "low"
#     },
#     {
#         "type": "price_variance",
#         "rfq_unit_price": 50,
#         "quoted_unit_price": 55,
#         "variance_percent": 10.0,
#         "severity": "medium"
#     },
#     {
#         "type": "lead_time_extension",
#         "rfq_days": 30,
#         "quoted_days": 45,
#         "variance_days": 15,
#         "severity": "high"
#     }
# ]
```

**Implementation Plan**:
1. Create `DeviationTracker` class
2. Compare RFQ items with quotation items (fuzzy matching)
3. Calculate variances (percentage, absolute)
4. Assign severity levels

#### C. Supplier Normalization ⚠️
```python
# Current: Raw supplier name from document
# Needed: Fuzzy matching against supplier registry

supplier_normalizer = SupplierNormalizer(
    supplier_registry=supplier_db  # Database of known suppliers
)

normalized = supplier_normalizer.normalize(
    raw_name="ACME Manufacturing Ltd.",
    aliases=["ACME Mfg", "ACME MFG Ltd", "Acme manufacturing"]
)
# Returns: {
#     "canonical_name": "ACME Manufacturing Ltd",
#     "vendor_id": "SUPP-12345",
#     "confidence": 0.98,
#     "alternate_names": ["ACME Mfg", "ACME MFG Ltd"]
# }
```

**Implementation Plan**:
1. Create `SupplierNormalizer` class
2. Use fuzzy string matching (fuzzywuzzy, difflib)
3. Build supplier registry (manually or from historical data)
4. Return canonical name + vendor ID

---

## LAYER 3: Document Intelligence ✅ (20% Complete)

### Goal
AI reasons about completeness, consistency, anomalies, and patterns.

### Current Status
- ❌ **Missing Field Detection**: Not implemented
- ❌ **Inconsistency Detection**: Not implemented
- ❌ **Anomaly Detection**: Not implemented
- ❌ **Supplier Behavior Tracking**: Not implemented

### Requirements to Implement

#### A. Missing Field Detection ❌
```python
# Check for required and recommended fields

completeness_checker = CompletenessChecker(
    document_type="quotation",  # Different rules per type
    mandatory_fields=[
        "supplier_name", "document_number", "issue_date",
        "items", "unit_prices", "total_price"
    ],
    recommended_fields=[
        "delivery_date", "payment_terms", "validity_period",
        "warranty", "technical_specs"
    ]
)

report = completeness_checker.check(document)
# Returns: {
#     "completeness_score": 0.78,  # 78% complete
#     "missing_mandatory": [
#         {"field": "payment_terms", "severity": "high"},
#         {"field": "warranty", "severity": "medium"}
#     ],
#     "missing_recommended": [
#         {"field": "validity_period", "severity": "low"}
#     ],
#     "recommendations": [
#         "Request payment terms from supplier",
#         "Clarify warranty conditions"
#     ]
# }
```

**Implementation Plan**:
1. Create `CompletenessChecker` class
2. Define mandatory/recommended fields per document type
3. Score completeness (0-100%)
4. Generate recommendations

#### B. Inconsistency Detection ❌
```python
# Find calculation errors, mismatches

consistency_checker = ConsistencyChecker()

issues = consistency_checker.check_line_items(
    line_items=[
        {
            "quantity": 100,
            "unit_price": 50,
            "total": 4000  # Should be 5000
        },
        {
            "quantity": 200,
            "unit_price": 25,
            "total": 5000  # Correct
        }
    ]
)
# Returns: [
#     {
#         "line": 0,
#         "type": "calculation_error",
#         "expected": 5000,
#         "found": 4000,
#         "error_amount": 1000,
#         "severity": "high"
#     }
# ]

currency_issues = consistency_checker.check_currencies(
    document_currency="USD",
    items_currency="INR",
    # ... more checks
)

term_issues = consistency_checker.check_conflicting_terms(
    terms=document.commercial_terms
)
```

**Implementation Plan**:
1. Create `ConsistencyChecker` class
2. Validate calculations (qty × unit_price = total)
3. Check currency consistency
4. Check date logic (issue < delivery < validity)
5. Find duplicate items

#### C. Anomaly Detection ❌
```python
# Flag unusual patterns

anomaly_detector = AnomalyDetector(
    project_context={
        "avg_price_per_unit": 50,
        "typical_lead_days": 30,
        "supplier_count": 5,
    }
)

anomalies = anomaly_detector.detect_all(document)
# Returns: [
#     {
#         "type": "price_outlier",
#         "field": "unit_price",
#         "value": 5,  # Expected ~50
#         "z_score": -3.2,  # Far from normal
#         "severity": "critical",
#         "flag": "UNUSUALLY_LOW_PRICE - possible quality issue or error"
#     },
#     {
#         "type": "lead_time_outlier",
#         "value": 90,  # Expected ~30
#         "severity": "high",
#         "flag": "EXTENDED_DELIVERY - review feasibility"
#     },
#     {
#         "type": "discount_anomaly",
#         "discount_percent": 40,
#         "typical_discount": 5,
#         "severity": "high",
#         "flag": "SUSPICIOUS_DISCOUNT - verify supplier stability"
#     }
# ]
```

**Implementation Plan**:
1. Create `AnomalyDetector` class
2. Use statistical methods (z-score, IQR)
3. Compare against project/supplier baselines
4. Flag prices, lead times, discounts, volumes
5. Provide contextual warnings

#### D. Supplier Behavior Profiling ❌
```python
# Track supplier patterns over time

behavior_profiler = SupplierBehaviorProfiler(
    supplier_name="ACME Manufacturing Ltd",
    history_db=supplier_historical_data
)

profile = behavior_profiler.analyze()
# Returns: {
#     "supplier_id": "SUPP-12345",
#     "total_interactions": 12,
#     "on_time_delivery_rate": 0.92,  # 92%
#     "price_consistency": {
#         "std_deviation": 5.2,  # 5.2% variation
#         "trend": "stable",
#         "avg_deviation_from_rfq": 3.1
#     },
#     "quality_issues": 1,  # 1 documented issue
#     "deviations": {
#         "always_deviates": False,
#         "deviation_frequency": 0.25,  # 25% of quotes deviate
#         "typical_deviation": "lead_time +5 days"
#     },
#     "reliability_score": 0.88,
#     "risk_flags": [
#         "Occasional delays (8% of orders)",
#         "Price volatility within 5%"
#     ]
# }
```

**Implementation Plan**:
1. Create `SupplierBehaviorProfiler` class
2. Query historical supplier data
3. Calculate metrics: on-time %, price variance, quality issues
4. Generate risk profile
5. Track changes over time

---

## LAYER 4: Workflow Intelligence ❌ (10% Complete)

### Goal
AI automates routing, validation, comparison, and generation.

### Current Status
- ❌ **Auto-Routing**: Not implemented
- ⚠️ **Auto-Validation**: Basic endpoint exists, needs enhancement
- ❌ **Auto-Comparison**: Draft code exists, needs completion
- ⚠️ **Auto-Generation**: Basic BOQ export, needs enhancement

### Requirements to Implement

#### A. Auto-Routing ❌
```python
# Route document to appropriate person/team

router = WorkflowRouter(
    organization_structure={
        "procurement_head": "john@company.com",
        "finance_head": "jane@company.com",
        "cfo": "boss@company.com"
    },
    business_rules={
        "high_value": {"amount_threshold": 100000, "route_to": "cfo"},
        "standard": {"route_to": "procurement_head"},
        "international": {"route_to": "compliance_team"},
    }
)

routing = router.route(
    document=quotation,
    business_context={
        "value": 250000,
        "supplier_country": "India",
        "risk_level": "high"
    }
)
# Returns: {
#     "primary_approver": "jane@company.com",  # Finance head
#     "secondary_approver": "boss@company.com",  # CFO
#     "cc_list": ["compliance@company.com"],
#     "reason": "High value quote (>100k) requires CFO approval",
#     "priority": "urgent",
#     "due_date": "2026-01-16"
# }
```

**Implementation Plan**:
1. Create `WorkflowRouter` class
2. Build routing rules engine
3. Define business rules (value thresholds, supplier types, etc.)
4. Integrate with email/notification system
5. Track routing history

#### B. Enhanced Auto-Validation ⚠️
```python
# Already has basic structure, needs enhancement

validator = ProcurementValidator(
    rfq_document=rfq,
    quotation=quote,
    business_rules={...}
)

validation_result = validator.validate_complete()
# Returns: {
#     "passed": False,
#     "completeness": {"score": 0.78, "grade": "B"},
#     "compliance": {"score": 0.95, "grade": "A"},
#     "quality": {"score": 0.65, "grade": "C"},
#     "risks": [
#         {
#             "category": "commercial",
#             "issue": "Missing payment terms",
#             "severity": "high",
#             "recommended_action": "Request clarification"
#         }
#     ],
#     "overall_score": 0.79,
#     "recommendation": "CONDITIONAL APPROVAL - address highlighted issues"
# }
```

**Implementation Plan**:
1. Enhance existing `/workflow/comparison` endpoint
2. Add rule-based scoring
3. Return structured validation report
4. Provide actionable recommendations

#### C. Advanced Auto-Comparison ❌
```python
# Already drafted, needs completion

comparator = SupplierComparator(
    rfq=rfq_document,
    quotations=[quote1, quote2, quote3],
    evaluation_criteria={
        "price_weight": 0.40,
        "quality_weight": 0.30,
        "delivery_weight": 0.20,
        "supplier_reliability_weight": 0.10
    },
    constraints={
        "must_be_domestic": False,
        "must_have_warranty": True,
        "max_lead_days": 60,
        "budget_limit": 500000
    }
)

analysis = comparator.analyze()
# Returns: {
#     "suppliers": [
#         {
#             "name": "ACME Manufacturing",
#             "price_score": 0.95,
#             "quality_score": 0.80,
#             "delivery_score": 0.85,
#             "reliability_score": 0.90,
#             "overall_score": 0.88,
#             "rank": 1,
#             "recommendation": "RECOMMENDED",
#             "strengths": ["Best price", "Proven reliability"],
#             "weaknesses": ["Longer lead time"],
#             "risk_level": "low"
#         },
#         {
#             "name": "XYZ Supplies",
#             "overall_score": 0.75,
#             "rank": 2,
#             "recommendation": "ACCEPTABLE - 12% more expensive but faster delivery",
#             "risk_level": "medium"
#         }
#     ],
#     "recommendation": "Award to ACME Manufacturing - best value",
#     "savings_opportunity": "15% below budget",
#     "risk_mitigation": "Require 5% performance bond"
# }
```

**Implementation Plan**:
1. Complete `SupplierComparator` class
2. Build scoring algorithm
3. Implement weighted evaluation
4. Add constraint checking
5. Generate comparison matrix (Excel)

#### D. Auto-Generation Templates ⚠️
```python
# Generate various documents

generator = ProcurementDocumentGenerator(
    template_dir="templates/",
    company_info=company_context
)

comparison_sheet = generator.generate_comparison(
    quotations=[quote1, quote2, quote3],
    format="excel"
)
# Generates: Comparison_RFQ-001_2026-01-15.xlsx

scorecard = generator.generate_scorecard(
    supplier="ACME Manufacturing",
    history=supplier_history,
    format="excel"
)
# Generates: Scorecard_ACME_2026-01-15.xlsx

summary_report = generator.generate_summary(
    documents=[rfq, quote1, quote2],
    format="pdf"
)
# Generates: Summary_RFQ-001_2026-01-15.pdf
```

**Implementation Plan**:
1. Create `ProcurementDocumentGenerator` class
2. Build template system (Jinja2)
3. Support Excel, PDF, Word output
4. Auto-populate with extracted data

---

## LAYER 5: Signals Intelligence ❌ (Not Started)

### Goal
AI generates predictive alerts and recommendations.

### Requirements to Implement

#### A. Price Signals ❌
```python
# Monitor price patterns

price_analyzer = PriceSignalAnalyzer(
    supplier="ACME Manufacturing",
    commodity="Steel Sheets",
    history_days=365
)

signals = price_analyzer.detect_signals()
# Returns: [
#     {
#         "signal_type": "price_trend",
#         "trend": "increasing",
#         "rate_of_change": 0.05,  # 5% per month
#         "confidence": 0.92,
#         "recommendation": "Negotiate now before further increases",
#         "potential_impact": "Could add $10k to annual spend"
#     },
#     {
#         "signal_type": "seasonal_pattern",
#         "pattern": "Q4 prices typically 10% lower",
#         "next_opportunity": "2026-10-01",
#         "recommendation": "Defer purchase to Q4 if possible"
#     },
#     {
#         "signal_type": "benchmark_gap",
#         "your_price": 50,
#         "market_avg": 45,
#         "gap_percent": 11.1,
#         "recommendation": "ACME is 11% above market - negotiate or source alternatives",
#         "savings_opportunity": "$5.5k/year"
#     }
# ]
```

**Implementation Plan**:
1. Create `PriceSignalAnalyzer` class
2. Build price history database
3. Implement trend detection (moving average, regression)
4. Find seasonal patterns
5. Compare against market benchmarks

#### B. Supplier Signals ❌
```python
# Monitor supplier health

supplier_monitor = SupplierSignalMonitor(
    supplier="ACME Manufacturing",
    data_sources=["quote_history", "delivery_history", "quality_reports"]
)

signals = supplier_monitor.detect_signals()
# Returns: [
#     {
#         "signal_type": "reliability_trend",
#         "current_on_time_rate": 0.85,  # Down from 0.95
#         "trend": "declining",
#         "severity": "warning",
#         "recommendation": "Monitor closely; consider diversifying"
#     },
#     {
#         "signal_type": "quality_issue",
#         "recent_issues": 3,
#         "defect_rate": 0.02,
#         "trend": "increasing",
#         "recommendation": "Implement additional QA checks"
#     },
#     {
#         "signal_type": "market_behavior",
#         "observation": "Always deviates from RFQ specs",
#         "pattern": "lead_time extension (avg +10 days)",
#         "recommendation": "Factor in 15-day buffer for future orders"
#     }
# ]
```

**Implementation Plan**:
1. Create `SupplierSignalMonitor` class
2. Track delivery performance, quality, behavior
3. Identify declining trends
4. Alert on pattern changes

#### C. Project Signals ❌
```python
# Predict project risks

project_predictor = ProjectSignalPredictor(
    project_id="PROJECT-2026-001",
    baseline={
        "budget": 500000,
        "planned_start": "2026-02-01",
        "planned_end": "2026-12-31"
    }
)

signals = project_predictor.predict_risks()
# Returns: [
#     {
#         "signal_type": "cost_overrun_risk",
#         "current_committed": 420000,
#         "predicted_final": 530000,
#         "overrun_percent": 6.0,
#         "confidence": 0.78,
#         "recommendation": "Negotiate with suppliers or reduce scope",
#         "time_to_action": "urgent"
#     },
#     {
#         "signal_type": "delay_risk",
#         "current_lead_days": 45,
#         "planned_buffer": 30,
#         "delay_probability": 0.35,  # 35% chance of delay
#         "recommendation": "Start procurement immediately"
#     },
#     {
#         "signal_type": "scope_drift",
#         "new_items": 5,
#         "removed_items": 2,
#         "net_cost_impact": 15000,
#         "recommendation": "Review scope changes with stakeholders"
#     }
# ]
```

**Implementation Plan**:
1. Create `ProjectSignalPredictor` class
2. Track project budgets and timelines
3. Analyze committed vs. forecasted costs
4. Predict delay risks
5. Monitor scope changes

#### D. Document Signals ❌
```python
# Flag risky documents

doc_risk_analyzer = DocumentRiskAnalyzer()

signals = doc_risk_analyzer.analyze(quotation)
# Returns: [
#     {
#         "signal_type": "missing_data_risk",
#         "missing_fields": ["payment_terms", "warranty"],
#         "completeness_score": 0.68,
#         "risk_level": "high",
#         "recommendation": "Request complete quote before evaluation"
#     },
#     {
#         "signal_type": "contractual_risk",
#         "issue": "Unlimited liability clause",
#         "language": "Supplier holds no liability for delays exceeding 30 days",
#         "risk_level": "medium",
#         "recommendation": "Negotiate cap on liability"
#     },
#     {
#         "signal_type": "commercial_risk",
#         "issue": "Non-standard payment terms",
#         "terms": "50% advance, 50% on delivery",
#         "risk_level": "low",
#         "recommendation": "Acceptable but check supplier credit"
#     }
# ]
```

**Implementation Plan**:
1. Create `DocumentRiskAnalyzer` class
2. Flag missing critical fields
3. Detect non-standard terms
4. Alert on contractual risks
5. Score overall document risk

---

## LAYER 6: Learning & Adaptation ❌ (Not Started)

### Goal
AI improves from user corrections and patterns.

### Requirements to Implement

#### A. Feedback Loop ❌
```python
# User corrects AI extractions

feedback_system = FeedbackLearner()

# User corrects an extraction
feedback_system.record_correction(
    document_id="DOC-12345",
    field="supplier_name",
    ai_value="ACME Mfg Ltd",
    user_corrected_value="ACME Manufacturing Limited",
    reason="More complete legal name"
)

# System learns
feedback_system.update_model()

# Next time similar pattern is found, AI improves
next_extraction = feedback_system.infer(
    similar_supplier_name="Acme Manufacturing Ltd."
)
# Now returns: "ACME Manufacturing Limited" (learned from feedback)
```

**Implementation Plan**:
1. Create `FeedbackLearner` class
2. Store user corrections in database
3. Analyze correction patterns
4. Fine-tune extraction logic
5. Track improvement metrics

#### B. Pattern Learning ❌
```python
# Learn supplier patterns

pattern_learner = SupplierPatternLearner()

# From past interactions
patterns = pattern_learner.extract_patterns(
    supplier="ACME Manufacturing",
    min_interactions=5
)
# Returns: {
#     "always_deviates_lead_time": True,
#     "typical_deviation": "+7 days",
#     "price_discount_range": "3-8%",
#     "typical_deviations": ["lead_time", "packaging"],
#     "reliability_pattern": "stable for orders < $50k, issues for larger orders"
# }

# Use patterns for predictions
prediction = pattern_learner.predict_next_quote(
    supplier="ACME Manufacturing",
    rfq_price=100,
    rfq_lead_days=30
)
# Returns: {
#     "predicted_price": 103,  # Expected 3% discount
#     "predicted_lead_days": 37,  # Expected +7 days
#     "confidence": 0.88
# }
```

**Implementation Plan**:
1. Create `SupplierPatternLearner` class
2. Extract patterns from historical data
3. Build predictive models per supplier
4. Validate predictions
5. Auto-update as new data arrives

#### C. Document Structure Learning ❌
```python
# Learn new document formats

structure_learner = DocumentStructureLearner(
    industry="construction_procurement",
    company="Kraftd"
)

# User provides sample documents
structure_learner.learn_from_sample(
    document_type="RFQ",
    samples=[doc1, doc2, doc3]
)

# System now recognizes new RFQ formats
new_document = structure_learner.extract(new_rfq)
# Better extraction because it learned company-specific patterns
```

**Implementation Plan**:
1. Create `DocumentStructureLearner` class
2. Build document layout classifiers
3. Learn field positions
4. Adapt to company-specific formats
5. Improve extraction accuracy

---

## LAYER 7: System Intelligence ❌ (Not Started)

### Goal
AI becomes the strategic brain of procurement.

### Requirements to Implement

#### A. Supplier Recommendation ❌
```python
# Recommend best supplier

recommender = SupplierRecommender(
    rfq=rfq_document,
    quotations=[quote1, quote2, quote3],
    company_strategy={
        "prefer_domestic": True,
        "sustainability_focus": True,
        "quality_over_cost": False,
        "long_term_partnerships": True
    }
)

recommendation = recommender.recommend()
# Returns: {
#     "recommended_supplier": "ACME Manufacturing",
#     "rationale": [
#         "Best price (5% below budget)",
#         "Proven reliability (92% on-time)",
#         "Domestic supplier",
#         "Long-term partnership potential"
#     ],
#     "alternative_suppliers": [
#         {
#             "name": "XYZ Supplies",
#             "why_second_choice": "15% more expensive but faster delivery",
#             "when_to_use": "If timeline becomes critical"
#         }
#     ],
#     "risk_mitigation": [
#         "Require 5% performance bond",
#         "Negotiate penalty for delays > 5 days"
#     ],
#     "negotiation_strategy": {
#         "opening_offer": "Accept at 95% of quoted price",
#         "targets": ["2% additional discount", "5-day lead time reduction"],
#         "walk_away_point": "3% above quoted price"
#     }
# }
```

**Implementation Plan**:
1. Create `SupplierRecommender` class
2. Integrate all previous layers
3. Build company strategy engine
4. Generate negotiation strategies
5. Provide business context

#### B. Predictive Analytics ❌
```python
# Predict future needs

predictor = ProcurementPredictor(
    company_history=company_spending_data,
    project_pipeline=upcoming_projects,
    market_trends=market_data
)

forecast = predictor.forecast_6_months()
# Returns: {
#     "predicted_demand": {
#         "steel_sheets": {"quantity": 5000, "cost": 250000},
#         "fasteners": {"quantity": 100000, "cost": 50000},
#         # ...
#     },
#     "cost_forecast": {
#         "total_spend": 1200000,
#         "trend": "increasing 3% YoY",
#         "seasonal_peaks": ["Q4", "Q1"]
#     },
#     "supplier_capacity_concerns": [
#         {
#             "supplier": "ACME",
#             "capacity_utilization": 0.95,
#             "risk": "May not meet surge demand in Q4"
#         }
#     ],
#     "recommendations": [
#         "Secure long-term contracts with top 3 suppliers",
#         "Diversify supplier base for fasteners",
#         "Negotiate volume discounts now for Q4"
#     ]
# }
```

**Implementation Plan**:
1. Create `ProcurementPredictor` class
2. Build demand forecasting
3. Analyze spending trends
4. Predict supplier constraints
5. Recommend procurement strategies

#### C. Contract Intelligence ❌
```python
# Extract and understand contracts

contract_analyzer = ContractAnalyzer()

analysis = contract_analyzer.analyze(contract_document)
# Returns: {
#     "document_type": "Purchase Agreement",
#     "key_terms": {
#         "validity": "2026-01-15 to 2027-01-14",
#         "payment_terms": "Net 30 from invoice",
#         "delivery": "FOB Destination",
#         "warranty": "12 months"
#     },
#     "risks": [
#         {
#             "clause": "Limitation of Liability",
#             "text": "Supplier liability capped at 25% of order value",
#             "risk_level": "medium",
#             "market_standard": "50-100%",
#             "recommendation": "Negotiate increase to 50% minimum"
#         }
#     ],
#     "unusual_terms": [
#         {
#             "term": "Price adjustment clause",
#             "detail": "Prices increase if raw material costs increase by >5%",
#             "risk": "Exposure to commodity volatility",
#             "recommendation": "Negotiate cap at 3% or add CPI adjustment mechanism"
#         }
#     ]
# }
```

**Implementation Plan**:
1. Create `ContractAnalyzer` class
2. Extract key contract terms
3. Flag unusual/risky clauses
4. Compare against market standards
5. Provide negotiation talking points

#### D. Strategic Guidance ❌
```python
# Provide strategic procurement recommendations

strategist = ProcurementStrategist(
    company=company_context,
    market_data=market_insights,
    supplier_network=supplier_database
)

strategy = strategist.generate_strategy(
    planning_horizon="12 months",
    focus_areas=["cost_reduction", "supplier_diversity", "sustainability"]
)
# Returns: {
#     "cost_reduction_opportunities": [
#         {
#             "opportunity": "Consolidate fasteners to 2 suppliers",
#             "current_spend": 500000,
#             "potential_savings": 50000,  # 10% reduction
#             "implementation_timeline": "3 months",
#             "action_plan": [
#                 "RFQ to top 5 suppliers for annual contract",
#                 "Negotiate volume discounts",
#                 "Implement supply agreement"
#             ]
#         }
#     ],
#     "supplier_diversity_goals": {
#         "target_female_owned_suppliers": 0.15,
#         "target_small_businesses": 0.20,
#         "current_percentage": 0.08,
#         "gap": "Find 5-7 additional diverse suppliers"
#     },
#     "sustainability_initiatives": {
#         "carbon_reduction_target": "15% by 2027",
#         "supplier_criteria": ["ISO14001", "carbon_reporting"],
#         "action": "Pre-qualify suppliers on sustainability"
#     }
# }
```

**Implementation Plan**:
1. Create `ProcurementStrategist` class
2. Analyze company strategy
3. Identify opportunities
4. Generate action plans
5. Track progress

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
**Focus**: Layers 1-2 completeness

- [ ] Document type classification (Layer 1)
- [ ] Semantic label mapping (Layer 1)
- [ ] Inferential extraction (Layer 1)
- [ ] Enhanced normalization (Layer 2)
- [ ] Supplier normalization (Layer 2)
- **Deliverable**: Accurate extraction regardless of document format

### Phase 2: Intelligence (Weeks 3-4)
**Focus**: Layers 3-4 implementation

- [ ] Missing field detection (Layer 3)
- [ ] Inconsistency detection (Layer 3)
- [ ] Anomaly detection (Layer 3)
- [ ] Auto-routing (Layer 4)
- [ ] Advanced comparison (Layer 4)
- **Deliverable**: Document validation and workflow automation

### Phase 3: Signals (Weeks 5-6)
**Focus**: Layer 5 implementation

- [ ] Price signal analysis (Layer 5)
- [ ] Supplier signal monitoring (Layer 5)
- [ ] Project signal prediction (Layer 5)
- [ ] Document risk signals (Layer 5)
- **Deliverable**: Predictive alerts and recommendations

### Phase 4: Adaptation (Weeks 7-8)
**Focus**: Layer 6 implementation

- [ ] Feedback loop system (Layer 6)
- [ ] Pattern learning (Layer 6)
- [ ] Document structure learning (Layer 6)
- **Deliverable**: Self-improving AI

### Phase 5: Strategic Intelligence (Weeks 9-12)
**Focus**: Layer 7 implementation

- [ ] Supplier recommendation engine (Layer 7)
- [ ] Procurement forecasting (Layer 7)
- [ ] Contract intelligence (Layer 7)
- [ ] Strategic guidance (Layer 7)
- **Deliverable**: AI as strategic procurement partner

---

## Technology Stack

| Layer | Technologies |
|-------|---|
| **LLM & Reasoning** | Azure OpenAI GPT-4, Agent Framework |
| **Document Processing** | Azure Document Intelligence, pdfplumber, pytesseract |
| **Data Storage** | PostgreSQL (future), Azure Cosmos DB (analytics) |
| **Embeddings** | OpenAI embeddings, sentence-transformers |
| **NLP** | NLTK, spaCy, fuzzywuzzy |
| **Analytics** | pandas, numpy, scikit-learn |
| **Visualization** | matplotlib, plotly (for reports) |
| **API** | FastAPI, Pydantic |

---

## Success Metrics

### Layer 1: Document Understanding
- Extraction accuracy: **>95%** (vs current 85%)
- Label mapping confidence: **>98%**
- Inferred field accuracy: **>90%**

### Layer 2: Procurement Intelligence
- Normalization correctness: **99%**
- Deviation detection rate: **>95%**
- False positive rate: **<5%**

### Layer 3: Document Intelligence
- Missing field detection: **100% recall**
- Inconsistency detection: **>90%**
- Anomaly precision: **>85%**

### Layer 4: Workflow Intelligence
- Routing accuracy: **98%**
- Comparison time: **<5 seconds**
- User adoption: **>80%**

### Layer 5: Signals Intelligence
- Signal precision: **>90%**
- Prediction accuracy: **>75%**
- Actionable recommendations: **>80%**

### Layer 6: Learning & Adaptation
- Correction incorporation: **<1 day**
- Pattern accuracy: **>80%**
- Continuous improvement: **+2% accuracy per month**

### Layer 7: System Intelligence
- User satisfaction: **>85%**
- Cost savings identified: **>15% of spend**
- Strategic recommendation adoption: **>70%**

---

## Integration Points

### With Existing Backend
- All layers integrate through FastAPI endpoints
- Leverage existing document processing
- Extend `/workflow`, `/extract`, `/generate-output` endpoints

### With Frontend (Future)
- Real-time document analysis
- Interactive comparison dashboard
- Alert notifications
- Feedback collection

### With External Systems (Future)
- Supplier database integration
- Market data feeds
- Historical spend data
- Financial systems (for approval)

---

## Next Immediate Action

**Start with Layer 1, Phase 1:**
1. Implement `DocumentTypeClassifier` - AI-based document type detection
2. Implement `SemanticLabelMapper` - Fuzzy field matching
3. Enhance completeness checker with scoring

**Success Criteria**:
- Can accurately identify RFQ vs BOQ vs Quotation vs PO
- Can extract fields regardless of label variations
- Completeness score for each document

**Timeline**: 1 week

---

## Summary

The **Kraftd AI Specification** defines a 7-layer intelligence stack that evolves the AI from basic extraction to strategic procurement guidance. The roadmap prioritizes foundation (extraction quality), then intelligence (reasoning), then prediction (signals), then adaptation (learning), and finally strategy (business guidance).

**Current Status**: Layers 1-2 are 30-50% complete. Layers 3-7 are not yet implemented.

**Vision**: By Phase 5 (Week 12), Kraftd will have an AI that doesn't just extract documents—it understands procurement, predicts risks, guides decisions, and continuously improves.

