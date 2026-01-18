"""
ML Training Pipeline - Complete Workflow

Steps:
1. Load documents from Cosmos DB
2. Extract features using data_pipeline
3. Train multiple models on different targets
4. Evaluate and compare models
5. Save best models to registry
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple
import json
from datetime import datetime

from data_pipeline import (
    MetadataFeatureExtractor,
    DataPipelineProcessor,
    FeatureSet
)
from models import (
    RiskScorePredictorModel,
    PricePredictorModel,
    SupplierReliabilityModel,
    ModelRegistry
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MLTrainingPipeline:
    """End-to-end ML training pipeline"""
    
    def __init__(self, cosmos_connection: str = None):
        """
        Initialize training pipeline
        
        Args:
            cosmos_connection: Cosmos DB connection string
        """
        self.cosmos_connection = cosmos_connection
        self.processor = DataPipelineProcessor()
        self.registry = ModelRegistry()
        self.results = {}
    
    def load_documents_from_cosmos(self) -> pd.DataFrame:
        """
        Load documents from Cosmos DB
        
        In production, implement actual Cosmos DB connection
        For now, returns sample data structure
        """
        logger.info("Loading documents from Cosmos DB...")
        
        # TODO: Implement actual Cosmos DB connection
        # Example:
        # from azure.cosmos import CosmosClient
        # client = CosmosClient.from_connection_string(self.cosmos_connection)
        # db = client.get_database_client("kraftd")
        # container = db.get_container_client("documents")
        # documents = list(container.query_items(query="SELECT * FROM c"))
        
        # For demo, return empty DataFrame
        logger.warning("Using mock data - implement Cosmos DB connection in production")
        return pd.DataFrame()
    
    def prepare_risk_prediction_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for risk prediction"""
        logger.info("Preparing risk prediction data...")
        
        # Get risk features
        X, cols = self.processor.get_feature_subset(df, FeatureSet.RISK_PREDICTION)
        y = df['overall_risk_score'] if 'overall_risk_score' in df.columns else pd.Series()
        
        if len(y) == 0:
            logger.warning("No target variable for risk prediction")
            return None, None
        
        # Remove rows with missing target
        mask = y.notna()
        X = X[mask]
        y = y[mask]
        
        logger.info(f"Risk prediction: {len(X)} samples, {len(cols)} features")
        return X, y
    
    def prepare_price_prediction_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for price prediction"""
        logger.info("Preparing price prediction data...")
        
        # Get price features
        X, cols = self.processor.get_feature_subset(df, FeatureSet.PRICE_PREDICTION)
        y = df['avg_unit_price'] if 'avg_unit_price' in df.columns else pd.Series()
        
        if len(y) == 0:
            logger.warning("No target variable for price prediction")
            return None, None
        
        # Remove rows with missing/invalid target
        mask = (y.notna()) & (y > 0)
        X = X[mask]
        y = y[mask]
        
        logger.info(f"Price prediction: {len(X)} samples, {len(cols)} features")
        return X, y
    
    def prepare_supplier_reliability_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for supplier reliability prediction"""
        logger.info("Preparing supplier reliability data...")
        
        # Get supplier features
        X, cols = self.processor.get_feature_subset(df, FeatureSet.SUPPLIER_RELIABILITY)
        y = df['supplier_reliability_score'] if 'supplier_reliability_score' in df.columns else pd.Series()
        
        if len(y) == 0:
            logger.warning("No target variable for supplier reliability")
            return None, None
        
        # Remove rows with missing target
        mask = y.notna()
        X = X[mask]
        y = y[mask]
        
        logger.info(f"Supplier reliability: {len(X)} samples, {len(cols)} features")
        return X, y
    
    def train_risk_model(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Train risk score prediction model"""
        if X is None or len(X) < 10:
            logger.warning("Insufficient data for risk model training")
            return {"status": "skipped", "reason": "insufficient_data"}
        
        logger.info("=" * 60)
        logger.info("TRAINING RISK SCORE PREDICTION MODEL")
        logger.info("=" * 60)
        
        model = RiskScorePredictorModel(model_type="gradient_boosting")
        metrics = model.train(X, y, test_size=0.2)
        
        # Save model
        self.registry.save_model(
            model,
            "risk_predictor",
            metadata={
                "model_type": "RiskScorePredictorModel",
                "metrics": metrics,
                "training_date": datetime.now().isoformat(),
                "feature_count": len(model.feature_columns)
            }
        )
        
        # Feature importance
        importance = model.get_feature_importance(top_n=10)
        logger.info("\nTop 10 Important Features:")
        logger.info(importance.to_string())
        
        self.results["risk_model"] = {
            "status": "trained",
            "metrics": metrics,
            "model": model
        }
        
        return metrics
    
    def train_price_model(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Train price prediction model"""
        if X is None or len(X) < 10:
            logger.warning("Insufficient data for price model training")
            return {"status": "skipped", "reason": "insufficient_data"}
        
        logger.info("=" * 60)
        logger.info("TRAINING PRICE PREDICTION MODEL")
        logger.info("=" * 60)
        
        model = PricePredictorModel(model_type="gradient_boosting")
        metrics = model.train(X, y, test_size=0.2)
        
        # Save model
        self.registry.save_model(
            model,
            "price_predictor",
            metadata={
                "model_type": "PricePredictorModel",
                "metrics": metrics,
                "training_date": datetime.now().isoformat(),
                "feature_count": len(model.feature_columns)
            }
        )
        
        # Feature importance
        importance = model.get_feature_importance(top_n=10)
        logger.info("\nTop 10 Important Features:")
        logger.info(importance.to_string())
        
        self.results["price_model"] = {
            "status": "trained",
            "metrics": metrics,
            "model": model
        }
        
        return metrics
    
    def train_supplier_reliability_model(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Train supplier reliability prediction model"""
        if X is None or len(X) < 10:
            logger.warning("Insufficient data for supplier reliability model training")
            return {"status": "skipped", "reason": "insufficient_data"}
        
        logger.info("=" * 60)
        logger.info("TRAINING SUPPLIER RELIABILITY PREDICTION MODEL")
        logger.info("=" * 60)
        
        model = SupplierReliabilityModel(model_type="gradient_boosting")
        metrics = model.train(X, y, test_size=0.2)
        
        # Save model
        self.registry.save_model(
            model,
            "supplier_reliability_predictor",
            metadata={
                "model_type": "SupplierReliabilityModel",
                "metrics": metrics,
                "training_date": datetime.now().isoformat(),
                "feature_count": len(model.feature_columns)
            }
        )
        
        # Feature importance
        importance = model.get_feature_importance(top_n=10)
        logger.info("\nTop 10 Important Features:")
        logger.info(importance.to_string())
        
        self.results["supplier_reliability_model"] = {
            "status": "trained",
            "metrics": metrics,
            "model": model
        }
        
        return metrics
    
    def run_full_pipeline(self, df: pd.DataFrame = None) -> Dict:
        """
        Run complete training pipeline
        
        Args:
            df: Feature DataFrame (if None, loads from Cosmos DB)
            
        Returns:
            Dictionary with training results
        """
        logger.info("\n" + "=" * 60)
        logger.info("STARTING ML TRAINING PIPELINE")
        logger.info("=" * 60)
        
        # Load data if not provided
        if df is None:
            df = self.load_documents_from_cosmos()
            if df.empty:
                logger.error("Failed to load documents")
                return {"status": "failed", "reason": "no_data"}
        
        logger.info(f"Loaded {len(df)} documents with {len(df.columns)} features")
        
        # Train models
        try:
            # Risk Prediction
            X_risk, y_risk = self.prepare_risk_prediction_data(df)
            self.train_risk_model(X_risk, y_risk)
        except Exception as e:
            logger.error(f"Risk model training failed: {e}")
        
        try:
            # Price Prediction
            X_price, y_price = self.prepare_price_prediction_data(df)
            self.train_price_model(X_price, y_price)
        except Exception as e:
            logger.error(f"Price model training failed: {e}")
        
        try:
            # Supplier Reliability
            X_supplier, y_supplier = self.prepare_supplier_reliability_data(df)
            self.train_supplier_reliability_model(X_supplier, y_supplier)
        except Exception as e:
            logger.error(f"Supplier reliability model training failed: {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info("ML TRAINING PIPELINE COMPLETED")
        logger.info("=" * 60)
        
        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "results": self.results,
            "registry_location": str(self.registry.model_dir)
        }
    
    def generate_training_report(self) -> str:
        """Generate human-readable training report"""
        report = "\n" + "=" * 70 + "\n"
        report += "ML TRAINING REPORT\n"
        report += "=" * 70 + "\n\n"
        
        for model_name, result in self.results.items():
            report += f"\n{model_name.upper()}\n"
            report += "-" * 50 + "\n"
            
            if result.get("status") == "trained":
                metrics = result.get("metrics", {})
                for key, value in metrics.items():
                    if isinstance(value, float):
                        report += f"  {key}: {value:.4f}\n"
                    else:
                        report += f"  {key}: {value}\n"
            else:
                report += f"  Status: {result.get('status')}\n"
                if 'reason' in result:
                    report += f"  Reason: {result.get('reason')}\n"
        
        report += "\n" + "=" * 70 + "\n"
        
        return report


# Example usage
def main():
    """Example: Run training pipeline"""
    
    pipeline = MLTrainingPipeline()
    
    # For demo, create sample data
    from data_pipeline import DataPipelineProcessor
    processor = DataPipelineProcessor()
    
    # Mock documents (in production: load from Cosmos DB)
    sample_docs = [
        {
            "document_id": f"doc-{i:03d}",
            "metadata": {"document_type": "RFQ", "document_number": f"RFQ-{i}"},
            "dates": {"issue_date": "2024-01-01T00:00:00"},
            "parties": {"issuer": {}, "recipient": {}},
            "project_context": {"project_code": "P001", "discipline": "civil"},
            "line_items": [{"quantity": 100, "unit_price": 50 + i, "total_price": 5000 + i*100}],
            "commercial_terms": {"currency": "USD", "tax_vat_mentioned": True},
            "signals": {
                "risk_indicators": {"validity_days": 30, "aggressive_discount": False},
                "behavioral_patterns": {"supplier_on_time_rate": 0.85 + i*0.01}
            },
            "supplier_signals": [{"supplier_name": f"Supplier {i}", "risk_score": 25 + i}],
            "data_quality": {"completeness_percentage": 0.90 + i*0.01},
            "extraction_confidence": {"overall_confidence": 0.85 + i*0.01},
            "overall_risk_score": 25 + i*2,
            "supplier_reliability_score": 75 - i,
            "avg_unit_price": 50 + i,
            "status": "approved"
        }
        for i in range(100)  # 100 sample documents
    ]
    
    # Process documents
    df = processor.process_documents(sample_docs)
    
    # Run pipeline
    results = pipeline.run_full_pipeline(df)
    
    # Print report
    print(pipeline.generate_training_report())
    
    # Print available models
    print("\nAvailable Models:")
    for model_name, versions in pipeline.registry.list_models().items():
        print(f"  {model_name}: {len(versions)} versions")


if __name__ == "__main__":
    main()
