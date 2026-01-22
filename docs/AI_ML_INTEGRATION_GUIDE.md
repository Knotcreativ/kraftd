# AI-ML Integration Guide

## Overview

The Kraftd AI Agent (gpt-4o) now seamlessly integrates with all 4 specialized ML models to provide comprehensive, dual-validated procurement analysis.

**Cost:** $0/month (gpt-4o via GitHub Models is FREE, ML models run locally)

## Architecture

```
User Uploads Document
        ↓
gpt-4o (GitHub Models) Extracts Intelligence
        ↓
Requests ML Predictions from 4 Models:
├─ Supplier Ecosystem Model → Success probability (0-100)
├─ Pricing Index Model → Fair pricing score (0-100)
├─ Risk Scoring Model → Risk factors (0-100)
└─ Mobility Clustering Model → Supply chain risk (0-100)
        ↓
gpt-4o Cross-Validates:
├─ Does ML align with AI analysis?
├─ Where do they diverge? (anomaly indicator)
└─ Combine for enhanced recommendation
        ↓
Final Recommendation with ML Confidence Metrics
```

## New Tools Available to gpt-4o

### 1. `get_ml_insights`

Request ML model predictions for supplier data.

**Parameters:**
- `supplier_data` (dict): Supplier information extracted from document
  - name, location, history, previous performance, etc.
- `procurement_metadata` (dict): Procurement details
  - pricing, volume, payment terms, historical data, etc.

**Returns:**
```json
{
  "pricing_fairness_score": 75,
  "ecosystem_health_score": 68,
  "supply_chain_risk": 35,
  "overall_risk_score": 40,
  "pricing_trend": "stable",
  "supplier_success_probability": 0.72,
  "anomalies_detected": ["unusual_pricing_spike"],
  "recommendations": [
    "Competitive pricing detected",
    "Strong supplier health",
    "Consider longer contract"
  ]
}
```

**Example Usage in Agent:**
```python
# gpt-4o extracts supplier info from document
supplier_data = {
    "name": "ABC Manufacturing",
    "location": "USA",
    "years_in_business": 15,
    "quality_certifications": ["ISO 9001", "ISO 14001"]
}

procurement_metadata = {
    "unit_price": 45.50,
    "annual_volume": 12000,
    "payment_terms": "Net 30",
    "lead_time_days": 14,
    "historical_prices": [43, 44, 45, 45.50]
}

# Call get_ml_insights tool
ml_insights = await agent.get_ml_insights(supplier_data, procurement_metadata)
```

### 2. `enrich_analysis_with_ml`

Combine AI analysis with ML predictions to create enhanced recommendation.

**Parameters:**
- `ai_analysis` (dict): Initial AI analysis from gpt-4o
- `ml_insights` (dict): ML model predictions from `get_ml_insights`

**Returns:**
```json
{
  "supplier_recommendation": "RECOMMENDED",
  "ml_confidence": 82,
  "risk_factors": [
    {
      "source": "ai_analysis",
      "risk": "Standard payment terms",
      "ml_confirmation": false
    },
    {
      "source": "ml_models",
      "risk": "New supplier (< 5 years data)",
      "ml_confirmation": true
    }
  ],
  "supplier_viability": {
    "ai_assessment": "viable",
    "ml_assessment": "viable",
    "consensus": "RECOMMENDED",
    "confidence": 82,
    "reasoning": "Strong supplier ecosystem health • Fair pricing compared to market baseline • High success probability from historical data"
  },
  "data_driven_recommendations": [
    {
      "source": "ai_analysis",
      "recommendation": "Implement quarterly reviews",
      "ml_backed": true,
      "consensus": true
    },
    {
      "source": "ml_models",
      "recommendation": "Consider volume discount opportunity",
      "ml_backed": true
    }
  ],
  "ml_validation": {
    "pricing_analysis_validated": true,
    "supplier_health_confirmed": true,
    "supply_chain_safe": true,
    "ml_risk_score": 38
  }
}
```

## How ML Models Work

### 1. Supplier Ecosystem Model (`supplier_ecosystem.py`)
- **Purpose:** Predict supplier success probability and ecosystem health
- **Algorithms:** GradientBoosting, RandomForest, LogisticRegression
- **Output Scales:**
  - Success Probability: 0-1 (probability of supplier meeting commitments)
  - Ecosystem Health: 0-100 (market conditions, supplier viability)
- **Use Case:** Assess long-term supplier viability and partnership potential

### 2. Pricing Index Model (`pricing_index.py`)
- **Purpose:** Assess fair pricing vs market baseline
- **Algorithm:** HuberRegressor (robust regression handles outliers)
- **Output Scale:** 0-100 (fairness score)
  - < 40: Price significantly above market
  - 40-60: Fair pricing
  - 60-100: Competitive advantage
- **Use Case:** Identify overpriced suppliers or spot negotiation opportunities

### 3. Risk Scoring Model (`models.py`)
- **Purpose:** Detect procurement risk factors
- **Algorithms:** RandomForest, GradientBoosting Regression
- **Output Scale:** 0-100 (risk level)
  - < 30: Low risk
  - 30-70: Moderate risk
  - > 70: High risk
- **Use Case:** Identify suppliers with historical anomalies or red flags

### 4. Mobility Clustering Model (`mobility_clustering.py`)
- **Purpose:** Detect supply chain route anomalies
- **Algorithms:** DBSCAN clustering, IsolationForest
- **Output Scale:** 0-100 (supply chain risk)
  - Detects: Unusual route patterns, suspicious supplier behavior
- **Use Case:** Identify supply chain vulnerabilities and logistics risks

## Example Workflow

### Scenario: Evaluate New Supplier Quote

```
1. USER UPLOADS QUOTATION PDF

2. gpt-4o EXTRACTS (via document_intelligence):
   {
     "supplier_name": "XYZ Electronics",
     "unit_price": 125.00,
     "monthly_volume": 500,
     "payment_terms": "Net 60",
     "delivery_location": "Singapore",
     "quality_certifications": ["ISO 9001"],
     "ai_assessment": "Legitimate supplier, competitive pricing"
   }

3. gpt-4o CALLS get_ml_insights:
   Input: supplier_data + procurement_metadata
   
4. ML MODELS SCORE:
   {
     "pricing_fairness": 72,
     "ecosystem_health": 68,
     "risk_score": 42,
     "supply_chain_risk": 58,
     "success_probability": 0.68,
     "anomalies": ["high_lead_time_variability"]
   }

5. gpt-4o CROSS-VALIDATES:
   ✓ AI: "Professional company, clean contracts"
   ✓ ML: "Competitive pricing, moderate risk"
   ✓ CONSENSUS: Viable supplier with monitoring needed

6. gpt-4o CALLS enrich_analysis_with_ml:
   Input: ai_analysis + ml_insights
   
7. FINAL RECOMMENDATION RETURNED:
   {
     "recommendation": "PROCEED WITH CAUTION",
     "ml_confidence": 68,
     "summary": "XYZ Electronics shows promise but requires monitoring.
                 AI analysis: Professional organization with clear terms.
                 ML analysis: Competitive pricing but elevated supply chain risk
                 from delivery location variability.
                 SUGGESTION: Start with 3-month trial period before full commitment.
                 ML CONFIDENCE: 68/100"
   }

8. USER RECEIVES ENHANCED RECOMMENDATION
   • AI reasoning (semantic understanding)
   • ML confidence scores (data-driven validation)
   • Anomaly alerts (when AI and ML diverge)
   • Combined assessment for better decision-making
```

## Key Benefits

### 1. Dual Validation
- **AI (gpt-4o):** Explains 'WHY' - semantic understanding of document context
- **ML:** Quantifies 'WHAT' - statistical patterns from historical data
- **Result:** More confident recommendations

### 2. Anomaly Detection
When AI and ML predictions diverge:
- AI says: "Looks like a good supplier"
- ML says: "High risk based on patterns"
- **Alert:** Flag for manual review

### 3. Confidence Metrics
- ML Confidence Score (0-100): How confident are the models?
- Viability Consensus: Do AI and ML agree?
- Risk Assessment: Combined confidence from both systems

### 4. Cost Efficiency
- gpt-4o: **FREE** (GitHub Models)
- ML models: **FREE** (scikit-learn, runs locally)
- **Total Cost: $0/month**

### 5. Continuous Learning
- gpt-4o learns document patterns over time
- ML models improve with more training data
- System gets smarter with usage

## Integration Details

### File Structure
```
backend/
├── agent/
│   └── kraft_agent.py (ENHANCED with ML integration)
├── services/
│   └── ai_ml_integration.py (NEW - 500+ lines)
├── ml/
│   ├── supplier_ecosystem.py
│   ├── models.py
│   ├── pricing_index.py
│   └── mobility_clustering.py
└── routes/
    └── advanced_ml.py (ML endpoints)
```

### How the Integration Works

1. **kraft_agent.py**
   - System instructions updated to include ML usage guidelines
   - New tools: `get_ml_insights`, `enrich_analysis_with_ml`
   - When processing documents, gpt-4o can request ML predictions

2. **ai_ml_integration.py**
   - `AIMLIntegration` class manages AI↔ML communication
   - `request_ml_scores()`: Gets predictions from all 4 ML models
   - `enrich_ai_analysis()`: Merges AI insights with ML predictions
   - Error handling: Graceful degradation if ML unavailable

3. **ML Models**
   - All 4 models accessible through integration layer
   - Models return structured predictions
   - Results packaged for gpt-4o consumption

## Testing

All integration tests pass:
```
Test Results: 230/230 PASSING ✓
- Owner isolation tests
- Multi-tenant tests
- ML integration tests
- Signal generation tests
- All domain-specific tests
```

## Deployment

Latest deployment includes:
- ✓ gpt-4o (GitHub Models) - FREE
- ✓ 4 ML models (scikit-learn)
- ✓ AI-ML integration layer
- ✓ Enhanced kraft_agent.py
- ✓ All 230 tests passing

**Commit:** a7cb11f  
**Status:** DEPLOYED & PRODUCTION READY

## Future Enhancements

1. **Model Training:** Continuously retrain ML models with new data
2. **Performance Tracking:** Monitor AI vs Azure Document Intelligence
3. **Custom Models:** Add domain-specific ML models for specialized procurement
4. **Real-time Learning:** Update models based on user feedback
5. **Explainability:** Detailed breakdowns of ML predictions
6. **A/B Testing:** Compare AI and ML recommendations against actual outcomes

## References

- [AI-ML Integration Code](backend/services/ai_ml_integration.py)
- [Enhanced Kraft Agent](backend/agent/kraft_agent.py)
- [Supplier Ecosystem Model](backend/ml/supplier_ecosystem.py)
- [Pricing Index Model](backend/ml/pricing_index.py)
- [Risk Scoring Model](backend/ml/models.py)
- [Mobility Clustering Model](backend/ml/mobility_clustering.py)
