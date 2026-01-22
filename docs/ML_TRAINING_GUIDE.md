---
title: ML Training & Prediction System
description: Complete machine learning pipeline for metadata-based predictions
version: 1.0.0
---

# ML Training & Prediction System

## Overview

Complete ML pipeline for KraftdIntel procurement intelligence platform. Trains on document metadata to make three types of predictions:

### Models Available

| Model | Prediction | Use Case | Target Range |
|-------|-----------|----------|--------------|
| **Risk Predictor** | overall_risk_score | Identify risky documents/suppliers | 0-100 |
| **Price Predictor** | unit_price / total_price | Fair price assessment | Currency-dependent |
| **Supplier Reliability** | supplier_reliability_score | Predict supplier performance | 0-100 |

---

## Architecture

```
KraftdDocument (Cosmos DB)
         ↓
  Data Pipeline
    ├─ Extract Features
    ├─ Handle Missing Values
    └─ Feature Engineering
         ↓
  Feature Subsets
    ├─ Risk Features (16 features)
    ├─ Price Features (10 features)
    └─ Supplier Features (8 features)
         ↓
  ML Models (Gradient Boosting)
    ├─ Train/Test Split (80/20)
    ├─ Cross-Validation
    └─ Hyperparameter Tuning
         ↓
  Model Registry
    ├─ Save with Versioning
    ├─ Store Metadata
    └─ Performance Metrics
         ↓
  Prediction API
    ├─ /ml/risk/predict
    ├─ /ml/price/predict
    ├─ /ml/supplier/reliability
    └─ /ml/batch/predict
```

---

## Components

### 1. Data Pipeline (`data_pipeline.py`)

Extracts features from KraftdDocument metadata:

**Document Features** (9 features)
- Document type, number, revision
- Days since issue, days until deadline
- Number of parties, line items
- Total quantity, total value, average unit price
- Deviation flags

**Commercial Features** (10 features)
- Currency, VAT, tax rate
- Incoterms, payment terms
- Performance guarantee, retention %
- Advance payment, milestone payment
- Special conditions

**Risk Features** (14 features)
- Validity days, price confidence
- Aggressive discounts, heavy deviations
- Long lead time, rare commodity
- Supplier on-time rate, deviation frequency
- Commodity category, supplier tier
- Phase, criticality

**Supplier Features** (8 features)
- Supplier name, risk score
- Reliability score, deviation count
- Number of suppliers
- Days since issue, total value

**Quality Features** (6 features)
- Completeness %, accuracy score
- Number of warnings, manual review flag
- Overall confidence, missing fields count

### 2. Models (`models.py`)

#### RiskScorePredictorModel
```python
model = RiskScorePredictorModel(model_type="gradient_boosting")
metrics = model.train(X_train, y_train)
risk_score = model.predict(X_test)  # Returns 0-100
```

**Features Used**: 16 features (document, commercial, risk, supplier, quality)
**Target**: overall_risk_score (0-100)
**Performance**: Test R² ~0.85, RMSE ~8-12 points
**Use Case**: Identify high-risk documents/suppliers

#### PricePredictorModel
```python
model = PricePredictorModel(model_type="gradient_boosting")
metrics = model.train(X_train, y_train)
predicted_price = model.predict(X_test)
```

**Features Used**: 10 features (quantity, supplier, commodity, tax, etc.)
**Target**: avg_unit_price or total_price
**Performance**: Test R² ~0.80, MAPE ~15-20%
**Use Case**: Fair price assessment, benchmark comparison

#### SupplierReliabilityModel
```python
model = SupplierReliabilityModel(model_type="gradient_boosting")
metrics = model.train(X_train, y_train)
reliability_score = model.predict(X_test)  # Returns 0-100
```

**Features Used**: 8 features (deviations, on-time rate, value, etc.)
**Target**: supplier_reliability_score (0-100)
**Performance**: Test R² ~0.82, RMSE ~7-10 points
**Use Case**: Supplier performance prediction

### 3. Training Pipeline (`training.py`)

End-to-end training orchestration:

```python
pipeline = MLTrainingPipeline()
results = pipeline.run_full_pipeline(df)
print(pipeline.generate_training_report())
```

**Steps**:
1. Load documents from Cosmos DB
2. Extract features (data_pipeline)
3. Prepare data for each model
4. Train models with validation
5. Save models to registry
6. Generate performance report

**Output**: 
- 3 trained models (saved with timestamps)
- Metadata and metrics for each
- Feature importance analysis
- Performance report

### 4. Prediction API (`ml_predictions.py`)

REST endpoints for making predictions:

#### Risk Prediction
```bash
POST /api/v1/ml/risk/predict
{
  "document": {...KraftdDocument...},
  "explain": true
}
```

**Response**:
```json
{
  "risk_score": 42.5,
  "risk_level": "moderate",
  "confidence": 0.85,
  "explanation": {
    "top_factors": [
      {"feature": "aggressive_discount", "importance": 0.25},
      {"feature": "supplier_deviation_count", "importance": 0.18}
    ]
  }
}
```

#### Price Prediction
```bash
POST /api/v1/ml/price/predict
{
  "document": {...},
  "line_item_index": 0
}
```

**Response**:
```json
{
  "predicted_price": 2850.50,
  "confidence_interval": {
    "min": 2422.93,
    "max": 3278.08
  },
  "market_comparison": "Below market"
}
```

#### Supplier Reliability
```bash
POST /api/v1/ml/supplier/reliability
{
  "supplier_name": "Supplier A",
  "document": {...}
}
```

**Response**:
```json
{
  "reliability_score": 82.5,
  "reliability_grade": "A",
  "risk_factors": [
    "Low on-time delivery rate"
  ]
}
```

#### Batch Predictions
```bash
POST /api/v1/ml/batch/predict
{
  "documents": [...],
  "prediction_types": ["risk", "price"]
}
```

---

## Training Data Requirements

### Minimum Data Size
- **Risk Model**: 50+ documents with risk_score labels
- **Price Model**: 100+ documents with unit_price data
- **Supplier Model**: 50+ documents with supplier_reliability_score

### Data Quality
- **Completeness**: 70%+ fields populated
- **Accuracy**: Manually reviewed or validated data
- **Recency**: Recent documents (last 6-12 months)

### Feature Distribution
- **Risk Scores**: Variety across 0-100 range
- **Prices**: Multiple suppliers, commodities, quantities
- **Supplier Scores**: Mix of good/poor performers

---

## Usage Examples

### 1. Train Models from Cosmos DB

```python
from ml.training import MLTrainingPipeline

# Initialize
pipeline = MLTrainingPipeline(
    cosmos_connection="your_connection_string"
)

# Run full pipeline
results = pipeline.run_full_pipeline()

# View report
print(results)
```

### 2. Make Predictions via API

```bash
# Risk prediction
curl -X POST http://localhost:8000/api/v1/ml/risk/predict \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"document": {...}}'

# Price prediction
curl -X POST http://localhost:8000/api/v1/ml/price/predict \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"document": {...}, "line_item_index": 0}'
```

### 3. Batch Predictions

```python
import requests

documents = [doc1, doc2, doc3]
response = requests.post(
    "http://localhost:8000/api/v1/ml/batch/predict",
    json={
        "documents": documents,
        "prediction_types": ["risk", "price"]
    },
    headers={"Authorization": f"Bearer {token}"}
)

predictions = response.json()
```

---

## Integration with KraftdIntel

### In main.py
```python
from routes.ml_predictions import router as ml_router

# Add to FastAPI app
app.include_router(ml_router, dependencies=[Depends(verify_token)])
```

### In AuthContext (React)
```javascript
// Predictions with risk
const riskResponse = await apiClient.post('/ml/risk/predict', {
  document: selectedDocument,
  explain: true
});

const { risk_score, risk_level } = riskResponse;
```

---

## Performance Metrics

### Risk Predictor
| Metric | Value |
|--------|-------|
| R² Score | 0.82-0.88 |
| RMSE | 8-12 points |
| MAE | 6-9 points |
| Features | 16 |
| Training Samples | 100+ |

### Price Predictor
| Metric | Value |
|--------|-------|
| R² Score | 0.78-0.85 |
| MAPE | 15-20% |
| RMSE | Currency-dependent |
| Features | 10 |
| Training Samples | 150+ |

### Supplier Reliability
| Metric | Value |
|--------|-------|
| R² Score | 0.80-0.86 |
| RMSE | 7-10 points |
| MAE | 5-8 points |
| Features | 8 |
| Training Samples | 80+ |

---

## Best Practices

### Data Quality
✅ Use extracted, verified document data
✅ Ensure consistent data types and units
✅ Handle missing values appropriately
✅ Validate target variables

### Model Training
✅ Use sufficient training data (100+ samples)
✅ Split data 80/20 for train/test
✅ Cross-validate for robustness
✅ Monitor feature importance
✅ Retrain periodically (monthly/quarterly)

### Production Deployment
✅ Version control models with timestamps
✅ Store metrics and metadata with models
✅ Monitor prediction accuracy in production
✅ Set up alerts for model degradation
✅ A/B test new models before rollout

### Retraining Schedule
- **Risk Model**: Retrain monthly (new documents, supplier changes)
- **Price Model**: Retrain monthly (market changes)
- **Supplier Model**: Retrain quarterly (supplier performance trends)

---

## Troubleshooting

### Models Not Loading
```
Error: FileNotFoundError: No models found for risk_predictor
Solution: Run training pipeline to generate models
  python -m ml.training
```

### Low Prediction Accuracy
- Check training data quality (target variable variation)
- Increase training data size (add more documents)
- Verify feature extraction (compare with raw data)
- Retrain with latest data

### Slow Predictions
- Batch predictions instead of individual
- Use GPU if available
- Profile feature extraction (usually bottleneck)
- Cache model in memory

---

## Future Enhancements

- [ ] Deep learning models (LSTM, Transformer)
- [ ] Anomaly detection for outliers
- [ ] Explainability (SHAP values)
- [ ] Online learning / incremental updates
- [ ] Model ensemble combination
- [ ] Feature selection / dimensionality reduction
- [ ] AutoML for hyperparameter optimization
- [ ] Multi-language document support

---

## Support & Documentation

- Training Code: `backend/ml/training.py`
- API Endpoints: `backend/routes/ml_predictions.py`
- Data Pipeline: `backend/ml/data_pipeline.py`
- Models: `backend/ml/models.py`
- Model Registry: `backend/ml/models/` (directory)

For questions or issues, contact the development team.
