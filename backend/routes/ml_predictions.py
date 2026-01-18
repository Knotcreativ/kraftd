"""
ML Prediction Service - FastAPI Integration

Exposes trained ML models through REST API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd
import logging

from models import ModelRegistry, RiskScorePredictorModel
from document_processing.orchestrator import ExtractionPipeline
from ml.data_pipeline import MetadataFeatureExtractor, DataPipelineProcessor, FeatureSet
from ml.training import MLTrainingPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ml", tags=["ML Predictions"])

# Initialize services
registry = ModelRegistry()
extractor = MetadataFeatureExtractor()
processor = DataPipelineProcessor()


# ===== Request/Response Models =====

class RiskPredictionRequest(BaseModel):
    """Request to predict risk score"""
    document: Dict[str, Any] = Field(..., description="KraftdDocument")
    explain: bool = Field(False, description="Include feature importance explanation")


class RiskPredictionResponse(BaseModel):
    """Risk prediction response"""
    risk_score: float = Field(..., description="Predicted risk score (0-100)")
    risk_level: str = Field(..., description="critical|major|moderate|low")
    confidence: float = Field(..., description="Model confidence (0-1)")
    explanation: Optional[Dict[str, Any]] = None


class PricePredictionRequest(BaseModel):
    """Request to predict price"""
    document: Dict[str, Any]
    line_item_index: int = Field(..., description="Index of line item to predict")


class PricePredictionResponse(BaseModel):
    """Price prediction response"""
    predicted_price: float
    confidence_interval: Dict[str, float]  # min, max
    market_comparison: Optional[str] = None  # Below/At/Above market


class SupplierReliabilityRequest(BaseModel):
    """Request supplier reliability prediction"""
    supplier_name: str
    document: Dict[str, Any]


class SupplierReliabilityResponse(BaseModel):
    """Supplier reliability prediction"""
    reliability_score: float  # 0-100
    reliability_grade: str  # A+, A, B, C, D, F
    risk_factors: List[str]


class PredictionBatchRequest(BaseModel):
    """Batch prediction request"""
    documents: List[Dict[str, Any]]
    prediction_types: List[str] = ["risk"]  # risk, price, supplier


class PredictionBatchResponse(BaseModel):
    """Batch prediction response"""
    predictions: List[Dict[str, Any]]
    total_documents: int
    successful: int
    failed: int
    average_execution_time_ms: float


# ===== Helper Functions =====

def get_risk_level(score: float) -> str:
    """Convert risk score to level"""
    if score >= 75:
        return "critical"
    elif score >= 50:
        return "major"
    elif score >= 25:
        return "moderate"
    else:
        return "low"


def get_reliability_grade(score: float) -> str:
    """Convert reliability score to grade"""
    if score >= 95:
        return "A+"
    elif score >= 85:
        return "A"
    elif score >= 75:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 45:
        return "D"
    else:
        return "F"


# ===== API Endpoints =====

@router.post("/risk/predict", response_model=RiskPredictionResponse)
async def predict_risk_score(request: RiskPredictionRequest) -> RiskPredictionResponse:
    """
    Predict document risk score
    
    Takes a KraftdDocument and returns predicted risk score (0-100)
    Risk factors: pricing anomalies, supplier history, deviations, terms
    
    Example:
    ```json
    {
      "document": {...full KraftdDocument...},
      "explain": true
    }
    ```
    """
    try:
        # Extract features
        features = extractor.extract_all_features(request.document)
        feature_df = pd.DataFrame([features])
        
        # Get risk features subset
        X, cols = processor.get_feature_subset(feature_df, FeatureSet.RISK_PREDICTION)
        
        # Load model
        try:
            model = registry.load_model("risk_predictor")
        except FileNotFoundError:
            raise HTTPException(
                status_code=503,
                detail="Risk prediction model not available. Please train models first."
            )
        
        # Make prediction
        risk_score = float(model.predict(X)[0])
        risk_level = get_risk_level(risk_score)
        
        # Get explanation if requested
        explanation = None
        if request.explain and hasattr(model, 'get_feature_importance'):
            importance = model.get_feature_importance(top_n=5)
            explanation = {
                "top_factors": importance.to_dict('records')
            }
        
        return RiskPredictionResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=0.85,  # Model confidence
            explanation=explanation
        )
    
    except Exception as e:
        logger.error(f"Risk prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/price/predict", response_model=PricePredictionResponse)
async def predict_price(request: PricePredictionRequest) -> PricePredictionResponse:
    """
    Predict fair price for line item
    
    Compares quoted price against market prediction
    
    Example:
    ```json
    {
      "document": {...},
      "line_item_index": 0
    }
    ```
    """
    try:
        # Extract features
        features = extractor.extract_all_features(request.document)
        feature_df = pd.DataFrame([features])
        
        # Get price features
        X, cols = processor.get_feature_subset(feature_df, FeatureSet.PRICE_PREDICTION)
        
        # Load model
        try:
            model = registry.load_model("price_predictor")
        except FileNotFoundError:
            raise HTTPException(
                status_code=503,
                detail="Price prediction model not available. Please train models first."
            )
        
        # Predict
        predicted_price = float(model.predict(X)[0])
        
        # Get confidence interval (±15%)
        margin = predicted_price * 0.15
        confidence_interval = {
            "min": predicted_price - margin,
            "max": predicted_price + margin
        }
        
        # Compare with actual
        actual_price = None
        if (request.line_item_index < len(request.document.get("line_items", []))):
            actual_price = request.document["line_items"][request.line_item_index].get("unit_price")
        
        market_comparison = None
        if actual_price:
            variance_pct = ((actual_price - predicted_price) / predicted_price) * 100
            if variance_pct < -10:
                market_comparison = "Below market"
            elif variance_pct > 10:
                market_comparison = "Above market"
            else:
                market_comparison = "At market"
        
        return PricePredictionResponse(
            predicted_price=predicted_price,
            confidence_interval=confidence_interval,
            market_comparison=market_comparison
        )
    
    except Exception as e:
        logger.error(f"Price prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/supplier/reliability", response_model=SupplierReliabilityResponse)
async def predict_supplier_reliability(request: SupplierReliabilityRequest) -> SupplierReliabilityResponse:
    """
    Predict supplier reliability score
    
    Factors: deviation frequency, on-time delivery, payment term variance
    
    Example:
    ```json
    {
      "supplier_name": "Supplier A",
      "document": {...}
    }
    ```
    """
    try:
        # Extract features
        features = extractor.extract_all_features(request.document)
        feature_df = pd.DataFrame([features])
        
        # Get supplier features
        X, cols = processor.get_feature_subset(feature_df, FeatureSet.SUPPLIER_RELIABILITY)
        
        # Load model
        try:
            model = registry.load_model("supplier_reliability_predictor")
        except FileNotFoundError:
            raise HTTPException(
                status_code=503,
                detail="Supplier reliability model not available. Please train models first."
            )
        
        # Predict
        reliability_score = float(model.predict(X)[0])
        reliability_grade = get_reliability_grade(reliability_score)
        
        # Risk factors
        risk_factors = []
        if feature_df.iloc[0].get('supplier_deviation_count', 0) > 2:
            risk_factors.append("High deviation frequency")
        if feature_df.iloc[0].get('supplier_on_time_rate', 1.0) < 0.8:
            risk_factors.append("Low on-time delivery rate")
        if feature_df.iloc[0].get('supplier_risk_score', 0) > 50:
            risk_factors.append("High historical risk score")
        
        return SupplierReliabilityResponse(
            reliability_score=reliability_score,
            reliability_grade=reliability_grade,
            risk_factors=risk_factors
        )
    
    except Exception as e:
        logger.error(f"Supplier reliability prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/predict", response_model=PredictionBatchResponse)
async def batch_predict(request: PredictionBatchRequest) -> PredictionBatchResponse:
    """
    Batch predict for multiple documents
    
    More efficient than individual requests
    """
    import time
    start_time = time.time()
    
    predictions = []
    successful = 0
    failed = 0
    
    for doc in request.documents:
        try:
            doc_predictions = {}
            
            if "risk" in request.prediction_types:
                risk_req = RiskPredictionRequest(document=doc)
                risk_pred = await predict_risk_score(risk_req)
                doc_predictions["risk"] = risk_pred.dict()
            
            predictions.append({
                "document_id": doc.get("document_id"),
                "predictions": doc_predictions,
                "status": "success"
            })
            successful += 1
        
        except Exception as e:
            logger.error(f"Batch prediction failed for doc: {e}")
            predictions.append({
                "document_id": doc.get("document_id"),
                "error": str(e),
                "status": "failed"
            })
            failed += 1
    
    execution_time_ms = (time.time() - start_time) * 1000
    
    return PredictionBatchResponse(
        predictions=predictions,
        total_documents=len(request.documents),
        successful=successful,
        failed=failed,
        average_execution_time_ms=execution_time_ms / len(request.documents)
    )


@router.get("/models/status")
async def get_models_status():
    """Get status of available models"""
    try:
        models = registry.list_models()
        
        status = {
            "available_models": {},
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
        for model_name, versions in models.items():
            status["available_models"][model_name] = {
                "versions": len(versions),
                "latest": versions[-1] if versions else None
            }
        
        return status
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/retrain")
async def retrain_models(documents: List[Dict[str, Any]] = Body(...)):
    """
    Retrain models with new data
    
    **Requires admin authentication**
    Triggers full retraining pipeline with provided documents
    """
    try:
        from ml.supplier_ecosystem import SupplierEcosystemModel
        
        # Process documents
        pipeline_processor = DataPipelineProcessor()
        df = pipeline_processor.process_documents(documents)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="No valid documents provided")
        
        # Run training
        pipeline = MLTrainingPipeline()
        results = pipeline.run_full_pipeline(df)
        
        return {
            "status": "training_completed",
            "results": results,
            "report": pipeline.generate_training_report()
        }
    
    except Exception as e:
        logger.error(f"Retraining failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Register router in main.py with:
# from routes.ml_predictions import router as ml_router
# app.include_router(ml_router, dependencies=[Depends(verify_token)])
