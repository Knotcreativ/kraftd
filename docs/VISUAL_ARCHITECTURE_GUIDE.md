# KRAFTD AI - VISUAL ARCHITECTURE GUIDE
## Understanding the Complete System

---

## 🎯 THE BIG PICTURE

### From Documents to Decisions
```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  SUPPLIER A          SUPPLIER B          SUPPLIER C                 │
│  ┌─────────┐        ┌─────────┐         ┌─────────┐                │
│  │ RFQ 001 │        │ RFQ 001 │         │ RFQ 001 │                │
│  │         │        │         │         │         │                │
│  │ Quote   │        │ Quote   │         │ Quote   │                │
│  │ 200K    │        │ 180K    │         │ 190K    │                │
│  └─────────┘        └─────────┘         └─────────┘                │
│        │                   │                   │                    │
│        └───────────────────┼───────────────────┘                    │
│                            │                                        │
│                            ▼                                        │
│                  📤 UPLOAD TO KRAFTD                               │
│                            │                                        │
└──────────────────────────────────────────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
          
    📄            💡           🤖
  EXTRACTION    INTELLIGENCE   AGENT
  
    Extract       Analyze      Recommend
    Structure     Risks        Action
    Data          Anomalies
    
                ▼
          
     ✅ RECOMMENDATION
     
     "Award to SUPPLIER B
      - 10% cost savings
      - 95% reliability
      - Zero deviations
      
      Risk: None
      
      Next: Send PO"
```

---

## 🏗️ SYSTEM LAYERS (Deep Dive)

### Layer 1: Document Understanding

```
INPUT: 10 RFQs (different formats, suppliers, languages)
       ┌──────────────┐
       │   PDF        │
       │   DOCX       │
       │   XLSX       │
       │   Image      │
       │   Mixed      │
       └──────────────┘
                │
        ┌───────┴──────────────────┐
        │                          │
        ▼                          ▼
    CLASSIFY               EXTRACT
    ┌─────────────┐       ┌─────────────────┐
    │ RFQ         │       │ Tables          │
    │ BOQ    ✓    │       │ Text            │
    │ Quote  ✓    │       │ Paragraphs ✓    │
    │ PO     ✓    │       │ Headers/Footers │
    │ etc.   ✓    │       │ Handwriting     │
    └─────────────┘       └─────────────────┘
        97% conf              90% accuracy
        
        └─────────────┬──────────────┘
                      │
                      ▼
            MAP FIELDS (Semantic)
            ┌────────────────────┐
            │ "Qty" → quantity   │
            │ "Rate" → unit_price│
            │ "Desc" → description│
            │ "UOM" → unit   ✓   │
            │ etc.               │
            └────────────────────┘
             98% confidence
             
                      │
                      ▼
            INFER MISSING FIELDS
            ┌────────────────────┐
            │ Missing: Unit      │
            │ Context: 100 pcs   │
            │ Infer: PCS ✓       │
            │ Confidence: 92%    │
            └────────────────────┘
                      │
                      ▼
OUTPUT: Structured data (95%+ accuracy)
        Complete with inferred fields
```

### Layer 2: Procurement Intelligence

```
NORMALIZED DATA
┌──────────────────────────────────────┐
│ Item 1:                              │
│   - Qty: 100 PCS (standardized)      │
│   - Rate: $50 USD (normalized)       │
│   - Total: $5,000 (calculated)       │
│   - Lead: 30 days (parsed)           │
│   - Status: ✓ Valid                  │
│                                      │
│ Item 2:                              │
│   - Qty: 200 PIECES (standardized)   │
│   - Rate: 10,000 INR → $120 USD      │
│   - Total: $24,000 (converted)       │
│   - Lead: Q2 2026 (normalized)       │
│   - Status: ✓ Valid                  │
│                                      │
│ Supplier: ACME Mfg Ltd (canonical)   │
│ PO: 18 items, $450K, 45-day lead     │
└──────────────────────────────────────┘
        │
        ▼
VALIDATION
┌──────────────────────────────────────┐
│ ✓ All quantities present             │
│ ✓ All prices valid                   │
│ ✓ Calculations correct               │
│ ✓ Totals match                       │
│ ✓ 92% completeness                   │
│ ⚠ Missing: Payment terms             │
│ ⚠ Missing: Warranty details          │
│ ⚠ Missing: Delivery address          │
└──────────────────────────────────────┘
        │
        ▼
RESULT: Clean, normalized, validated data ready for analysis
```

### Layer 3: Document Intelligence

```
VALIDATE → DETECT ISSUES

Input: 3 Quotations
┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
│ SUPPLIER A         │    │ SUPPLIER B         │    │ SUPPLIER C         │
│ Quote: $450,000    │    │ Quote: $500,000    │    │ Quote: $50,000     │
│ Lead: 45 days      │    │ Lead: 60 days      │    │ Lead: 10 days      │
│ (from RFQ: 30d)    │    │ (from RFQ: 30d)    │    │ (from RFQ: 30d)    │
└────────────────────┘    └────────────────────┘    └────────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
   Deviation: +15d         Deviation: +30d         Anomaly: -80%
   Status: ⚠ Acceptable    Status: 🔴 ISSUE       Status: 🔴 ALERT
              Risk: Medium             Risk: High           Risk: Critical


ANOMALY DETECTION
┌──────────────────────────────────────────────┐
│ Supplier C Price Anomaly                     │
│                                              │
│ RFQ avg: $200,000                            │
│ C offered: $50,000                           │
│ Z-score: -3.8 (far from normal)              │
│                                              │
│ ⚠ RISK FLAGS:                                │
│   • Unusually low price                      │
│   • Possible quality issue                   │
│   • Verify supplier stability                │
│   • Request production sample                │
│                                              │
│ ✓ Recommendation: VERIFY BEFORE AWARD        │
└──────────────────────────────────────────────┘

INCONSISTENCY DETECTION
┌──────────────────────────────────────────────┐
│ Quote Item 5: Calculation Error              │
│                                              │
│ Qty: 100                                     │
│ Rate: $50                                    │
│ Expected Total: $5,000                       │
│ Quote shows: $4,000                          │
│                                              │
│ 🔴 ERROR: $1,000 discrepancy                 │
│ Request correction from supplier             │
└──────────────────────────────────────────────┘

OUTPUT: Issues flagged, risks identified, action recommended
```

### Layer 4: Workflow Intelligence

```
INTELLIGENT ROUTING

Quote Received → Analysis Complete → Route Decision

                    ┌──────────────────────┐
                    │ Supplier B           │
                    │ $500K                │
                    │ Lead: 60 days        │
                    │ Quality: Verified    │
                    │ Reliability: 95%     │
                    └──────────────────────┘
                            │
                    ┌───────┴────────┐
                    │                │
              Check value?      Check compliance?
                    │                │
                   YES              YES
                    │                │
            Value: $500K?      Approved vendor?
                    │                │
                YES (>$100K)    NO (first time)
                    │                │
                    │                ├─→ 🔵 Send to Compliance
                    │                │
                    ├────────────────┤
                    │                │
                    ▼                ▼
              🟢 Route to CFO    🟢 Route to Procurement
              Due: 1 day         Due: 2 days
                    │                │
                    └────────────────┘
                            │
                    Auto-send emails
                    Track approvals
                    Escalate if overdue


AUTO-COMPARISON MATRIX

Criteria        Weight    A Score    B Score    C Score
─────────────────────────────────────────────────────
Price           40%       85        75         30
Quality         30%       80        90         70
Delivery        20%       85        60         95
Reliability     10%       90        95         50
─────────────────────────────────────────────────────
OVERALL         100%      84.5      80.5       54.5
─────────────────────────────────────────────────────
Rank:                     🥇 1st     🥈 2nd     🥉 3rd

Output: Recommendation → Award to A, Alternative: B
```

### Layer 5: Signals Intelligence

```
PREDICTIVE ALERTS

Price Signals:
    Historical: $100 → $110 → $120 → $130
    Trend: +10% per quarter
    Forecast: Will reach $160 by Q2 2026
    💡 Action: Negotiate annual contract NOW before increases
    
    Savings: 20% × 4 orders = $8,000/quarter

Supplier Signals:
    ACME: 12 interactions
    On-time: 92%
    Quality: 5 issues (2.5%)
    Deviations: Always +5 days lead time
    💡 Action: Factor in +7 day buffer for future orders

Project Signals:
    Budget: $500K
    Committed: $420K
    Forecasted: $530K
    Risk: 6% overrun
    💡 Action: Negotiate $20K in savings OR reduce scope

Risk Signals:
    Document: Missing warranty, payment terms unclear
    Completeness: 68%
    💡 Action: Request clarifications before signing
```

### Layer 6: Learning & Adaptation

```
FEEDBACK LOOP

┌─────────────────┐
│ AI Extracts:    │
│ Supplier: ABC   │
│ Amount: $100K   │
│ Lead: 30 days   │
└─────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ User Reviews: "Actually XYZ not ABC" │
│ Corrects: Supplier: XYZ             │
│ Reason: "Full legal name"           │
└─────────────────────────────────────┘
         │
         ▼
┌───────────────────────────────────────┐
│ System Learns:                        │
│ "ABC Ltd" = "XYZ Manufacturing Ltd"   │
│ Confidence: 95%                       │
│ Next time similar: Auto-correct       │
└───────────────────────────────────────┘
         │
         ▼
Pattern Detection:
    Supplier always deviates lead time by +7 days
    → Factor this in future quotes
    
    RFQ format: Always has column 3 = quantity
    → Use this as heuristic for new formats
    
    Currency: Projects in India always INR
    → Auto-convert to company currency

Self-Improvement: Accuracy increases 2-3% per month
```

### Layer 7: System Intelligence

```
STRATEGIC GUIDANCE

Input: Year's procurement history + Market data + Project pipeline

Analysis:
┌────────────────────────────────────────────────────┐
│ 1. Cost Reduction Opportunities:                  │
│    - Consolidate fastener suppliers: -10%         │
│    - Volume discount negotiations: -5%            │
│    - Identified savings: $75K/year                │
│                                                    │
│ 2. Supplier Risk Assessment:                      │
│    - ACME: Low risk, high reliability             │
│    - XYZ: Medium risk (new vendor)                │
│    - ABC: High risk (quality issues)              │
│    → Recommendation: Diversify suppliers          │
│                                                    │
│ 3. Market Trends:                                 │
│    - Steel prices: +15% YoY                       │
│    - Lead times: Lengthening (36 → 45 days)      │
│    - Action: Lock in prices Q1 2026               │
│                                                    │
│ 4. Strategic Initiatives:                         │
│    - Sustainability: 20% of suppliers ISO14001    │
│    - Resilience: Multi-source critical items      │
│    - Partnership: Invest in top 3 suppliers       │
└────────────────────────────────────────────────────┘
         │
         ▼
Recommendations:
┌────────────────────────────────────────────────────┐
│ ✓ Award annual contract to ACME (3 years)         │
│   - Locks in prices before market increase         │
│   - Saves $75K over period                         │
│   - Reduces admin overhead                         │
│                                                    │
│ ✓ Negotiate volume discount with XYZ              │
│   - Current: $50/unit → Target: $47/unit          │
│   - Annual savings: $30K                           │
│   - Improves backup capacity                       │
│                                                    │
│ ✓ Transition away from ABC                        │
│   - Quality issues not acceptable                  │
│   - Phase out over 6 months                        │
│   - Transfer volumes to ACME & XYZ                 │
│                                                    │
│ ✓ Develop 2 new ISO14001 suppliers                │
│   - Sustainability initiative                      │
│   - Reduce single-supplier risk                    │
│   - Timeline: 3 months                             │
│                                                    │
│ Expected Impact:                                   │
│ • $100K+ annual savings                            │
│ • 50% reduction in supply risk                     │
│ • Sustainable supply chain                        │
│ • Predictable pricing                              │
└────────────────────────────────────────────────────┘
```

---

## 📊 DATA FLOW DIAGRAM

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         KRAFTD AI SYSTEM DATA FLOW                        │
└──────────────────────────────────────────────────────────────────────────┘

STAGE 1: INGESTION
────────────────────
User uploads documents
    │
    ├─→ PDF Processor
    ├─→ Word Processor
    ├─→ Excel Processor
    └─→ Image Processor (OCR)
    
    ▼
Raw extracted content

STAGE 2: UNDERSTANDING (Layer 1)
────────────────────────────────
Document Classifier
    ├─→ Type: RFQ/BOQ/Quote/PO?
    └─→ Confidence: 98%
    
Semantic Label Mapper
    ├─→ "Qty" → quantity
    ├─→ "Rate" → unit_price
    └─→ Map unknown labels
    
Context Inferencer
    ├─→ Missing fields?
    ├─→ Infer from context
    └─→ Add confidence scores
    
Completeness Checker
    ├─→ 92% complete
    ├─→ Missing: Payment terms
    └─→ Recommendations: Request from supplier
    
    ▼
Normalized, validated, structured data

STAGE 3: INTELLIGENCE (Layers 3-4)
──────────────────────────────────
Document Intelligence
    ├─→ Inconsistency checker
    ├─→ Anomaly detector
    ├─→ Issue flagging
    └─→ Risk assessment
    
Workflow Router
    ├─→ Rule evaluation
    ├─→ Routing decision
    └─→ Notification/assignment
    
Supplier Comparison
    ├─→ Score normalization
    ├─→ Weighted analysis
    ├─→ Recommendation
    └─→ Ranking
    
    ▼
Actionable intelligence

STAGE 4: PREDICTION (Layer 5)
─────────────────────────────
Signal Analysis
    ├─→ Price trends
    ├─→ Supplier health
    ├─→ Project risks
    └─→ Alerts generated
    
    ▼
Predictive alerts & recommendations

STAGE 5: LEARNING (Layer 6)
───────────────────────────
User Feedback
    ├─→ Correction captured
    ├─→ Pattern extracted
    └─→ Model updated
    
    ▼
Continuous improvement

STAGE 6: STRATEGY (Layer 7)
──────────────────────────
Strategic Analysis
    ├─→ Market trends
    ├─→ Supply chain optimization
    ├─→ Cost reduction opportunities
    └─→ Strategic recommendations
    
    ▼
Strategic guidance

OUTPUT
──────
✓ Structured data
✓ Validation results
✓ Issues & risks
✓ Recommendations
✓ Strategic guidance
✓ Next actions
```

---

## 🎬 EXAMPLE CONVERSATION FLOW

```
User: "Upload these 3 RFQs"

System: Processes all 3
    • Classifies as RFQ (97% confidence)
    • Extracts 54 line items
    • Maps all fields (98% confidence)
    • Validates 87% complete
    → "Ready for analysis"

User: "Compare quotes for item 5"

System: Analyzes
    • SUPPLIER A: $500 (lead: 30 days)
    • SUPPLIER B: $480 (lead: 45 days)
    • SUPPLIER C: $450 (lead: 20 days)
    
    Scores:
    • A: 85 points (price + speed)
    • B: 78 points (price good, slow delivery)
    • C: 92 points (best price, fastest)
    
    Evaluates Supplier C history:
    • 5 prior deals
    • 100% on-time delivery
    • Zero quality issues
    • Reliable
    
    → "RECOMMEND: SUPPLIER C
       Save $50 vs A, $30 vs B
       Fastest delivery
       Proven reliability"

User: "Create PO for Supplier C"

System: Generates
    • Creates PO document
    • Populates item details
    • Adds terms & conditions
    • Calculates totals
    • Formats for signature
    
    → "PO ready for approval"

User: "Send for approval"

System: Routes intelligently
    • Evaluates: Value $450K (>$100K threshold)
    • Routes to: CFO
    • Priority: High
    • Due: Tomorrow
    • Alert: "CFO approval needed"
    
    → "Routed to CFO - waiting for approval"

User: "Status?"

System: Provides update
    • PO-001 (Supplier C): Pending CFO
    • PO-002 (Supplier A): Approved CFO, sent to vendor
    • PO-003 (Supplier B): Acknowledged by vendor
    
    → "1 pending, 2 in flight, 0 completed"
```

---

## 🚀 THE TRANSFORMATION

### Before Kraftd AI
```
Manual Process:
1. Receive document (2-3 days delayed)
2. Manual data entry (2-3 hours per document)
3. Error checking (1 hour)
4. Forwarding for approval (1 day)
5. Supplier communication (2-3 days)

Total: 5-7 days per RFQ
Error rate: 5-10%
Cost: 30+ hours per month
```

### After Kraftd AI (Phase 1)
```
Automated Process:
1. Upload document (instant)
2. Auto-extract (10 seconds)
3. Validation (2 seconds)
4. Route to approver (instant)
5. Supplier follow-up (instant)

Total: 30 seconds per RFQ
Error rate: <1%
Cost: 2 hours per month
Savings: 28+ hours/month = $7K/month
```

### After Full Implementation (Phase 7)
```
Intelligent Process:
1. Upload document (instant)
2. Full AI analysis (5 seconds)
3. Automated comparison (2 seconds)
4. Intelligent recommendation (2 seconds)
5. Auto-route & schedule (instant)
6. Risk alert if needed (instant)
7. Predictive insights (instant)

Total: 10 seconds per RFQ
Error rate: 0.1%
Cost: <1 hour per month
Savings: $15K+ per month
Strategic value: $50K+ per month
```

---

## 📈 EVOLUTION PATH

```
           Strategic
            Guidance
              (7)
               ▲
              ╱│╲
            ╱  │  ╲
          ╱    │    ╲
    Learning  │   System
     (6)      │  Intelligence
       ▲      │      
       │      │    Signals
       │      │   (5)
       └──────┼────▲
              │   ╱│╲
              │ ╱  │  ╲
         Workflow  │  Document
        Intelligence Document
           (4)     │ Intelligence
              ▲    │    (3)
              │    │    ▲
              └────┼────┘
                   │
              Procurement
              Intelligence
                  (2)
                   ▲
                   │
            Document
           Understanding
               (1)

START HERE (Phase 1)
↓
ADD REASONING (Phase 2)
↓
ADD AUTOMATION (Phase 3)
↓
ADD PREDICTION (Phase 4)
↓
ADD LEARNING (Phase 5)
↓
ADD STRATEGY (Phase 6)
↓
INTELLIGENT PLATFORM
```

---

This visual guide shows:
- How data flows through the system
- How each layer builds on the previous
- Real-world examples of each capability
- The transformation from manual to intelligent
- The 7-phase evolution path

**Result**: Complete visual understanding of Kraftd AI architecture.

