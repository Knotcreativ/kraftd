"""
ML Models for Procurement Intelligence

Three production-ready models:
1. Risk Score Prediction - Predict overall risk (0-100)
2. Price Prediction - Predict fair pricing for line items
3. Supplier Reliability - Predict supplier performance
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, List
import pickle
import logging
from datetime import datetime
from pathlib import Path

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

logger = logging.getLogger(__name__)


class RiskScorePredictorModel:
    """
    Predict overall document risk score (0-100)
    
    Predicts: overall_risk_score
    Target audience: Procurement managers, risk assessors
    """
    
    def __init__(self, model_type: str = "gradient_boosting"):
        """
        Initialize risk score predictor
        
        Args:
            model_type: 'gradient_boosting', 'random_forest'
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        self.is_trained = False
    
    def build_model(self):
        """Build the ML model"""
        if self.model_type == "gradient_boosting":
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                verbose=0
            )
        else:
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                n_jobs=-1,
                random_state=42
            )
    
    def train(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2) -> Dict[str, float]:
        """
        Train the risk prediction model
        
        Args:
            X: Feature matrix (already processed)
            y: Target variable (overall_risk_score)
            test_size: Proportion for test set
            
        Returns:
            Dictionary of metrics
        """
        # Build model
        self.build_model()
        
        # Handle categorical features
        for col in X.select_dtypes(include=['object']).columns:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                X[col] = self.label_encoders[col].fit_transform(X[col].astype(str))
            else:
                X[col] = self.label_encoders[col].transform(X[col].astype(str))
        
        # Store feature columns
        self.feature_columns = X.columns.tolist()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        logger.info(f"Training Risk Score Predictor ({self.model_type})...")
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)
        
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        
        self.is_trained = True
        
        metrics = {
            "train_rmse": train_rmse,
            "test_rmse": test_rmse,
            "train_mae": train_mae,
            "test_mae": test_mae,
            "train_r2": train_r2,
            "test_r2": test_r2,
            "samples": len(X)
        }
        
        logger.info(f"Risk Predictor Metrics: Test R² = {test_r2:.4f}, Test RMSE = {test_rmse:.2f}")
        return metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict risk scores
        
        Args:
            X: Feature matrix
            
        Returns:
            Predicted risk scores (0-100)
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        # Process categorical features
        for col in X.select_dtypes(include=['object']).columns:
            if col in self.label_encoders:
                X[col] = self.label_encoders[col].transform(X[col].astype(str))
        
        # Scale and predict
        X_scaled = self.scaler.transform(X[self.feature_columns])
        predictions = self.model.predict(X_scaled)
        
        # Clip to 0-100 range
        return np.clip(predictions, 0, 100)
    
    def get_feature_importance(self, top_n: int = 10) -> pd.DataFrame:
        """Get top important features"""
        if not hasattr(self.model, 'feature_importances_'):
            return pd.DataFrame()
        
        importances = self.model.feature_importances_
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        return feature_importance.head(top_n)


class PricePredictorModel:
    """
    Predict fair pricing for line items
    
    Predicts: unit_price or total_price
    Target audience: Finance teams, procurement managers
    """
    
    def __init__(self, model_type: str = "gradient_boosting"):
        """Initialize price predictor"""
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        self.is_trained = False
    
    def build_model(self):
        """Build the ML model"""
        if self.model_type == "gradient_boosting":
            self.model = GradientBoostingRegressor(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=6,
                min_samples_split=4,
                min_samples_leaf=2,
                random_state=42
            )
        else:
            self.model = RandomForestRegressor(
                n_estimators=150,
                max_depth=12,
                min_samples_split=4,
                min_samples_leaf=2,
                n_jobs=-1,
                random_state=42
            )
    
    def train(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2) -> Dict[str, float]:
        """Train price prediction model"""
        self.build_model()
        
        # Handle categorical
        for col in X.select_dtypes(include=['object']).columns:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                X[col] = self.label_encoders[col].fit_transform(X[col].astype(str))
        
        self.feature_columns = X.columns.tolist()
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Scale
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train
        logger.info(f"Training Price Predictor ({self.model_type})...")
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)
        
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        train_mape = np.mean(np.abs((y_train - y_pred_train) / y_train)) * 100
        test_mape = np.mean(np.abs((y_test - y_pred_test) / y_test)) * 100
        test_r2 = r2_score(y_test, y_pred_test)
        
        self.is_trained = True
        
        metrics = {
            "train_rmse": train_rmse,
            "test_rmse": test_rmse,
            "train_mape": train_mape,
            "test_mape": test_mape,
            "test_r2": test_r2,
            "samples": len(X)
        }
        
        logger.info(f"Price Predictor Metrics: Test R² = {test_r2:.4f}, Test MAPE = {test_mape:.2f}%")
        return metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict prices"""
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        for col in X.select_dtypes(include=['object']).columns:
            if col in self.label_encoders:
                X[col] = self.label_encoders[col].transform(X[col].astype(str))
        
        X_scaled = self.scaler.transform(X[self.feature_columns])
        predictions = self.model.predict(X_scaled)
        
        # Ensure non-negative prices
        return np.maximum(predictions, 0)


class SupplierReliabilityModel:
    """
    Predict supplier reliability score
    
    Predicts: supplier_reliability_score (0-100)
    Target audience: Supplier management, risk teams
    """
    
    def __init__(self, model_type: str = "gradient_boosting"):
        """Initialize supplier reliability predictor"""
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        self.is_trained = False
    
    def build_model(self):
        """Build the ML model"""
        if self.model_type == "gradient_boosting":
            self.model = GradientBoostingRegressor(
                n_estimators=120,
                learning_rate=0.12,
                max_depth=5,
                min_samples_split=5,
                random_state=42
            )
        else:
            self.model = RandomForestRegressor(
                n_estimators=120,
                max_depth=10,
                min_samples_split=5,
                n_jobs=-1,
                random_state=42
            )
    
    def train(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2) -> Dict[str, float]:
        """Train supplier reliability model"""
        self.build_model()
        
        for col in X.select_dtypes(include=['object']).columns:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                X[col] = self.label_encoders[col].fit_transform(X[col].astype(str))
        
        self.feature_columns = X.columns.tolist()
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        logger.info(f"Training Supplier Reliability Model ({self.model_type})...")
        self.model.fit(X_train_scaled, y_train)
        
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)
        
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        
        self.is_trained = True
        
        metrics = {
            "train_rmse": train_rmse,
            "test_rmse": test_rmse,
            "train_r2": train_r2,
            "test_r2": test_r2,
            "samples": len(X)
        }
        
        logger.info(f"Supplier Reliability Metrics: Test R² = {test_r2:.4f}")
        return metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict supplier reliability score"""
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        for col in X.select_dtypes(include=['object']).columns:
            if col in self.label_encoders:
                X[col] = self.label_encoders[col].transform(X[col].astype(str))
        
        X_scaled = self.scaler.transform(X[self.feature_columns])
        predictions = self.model.predict(X_scaled)
        
        return np.clip(predictions, 0, 100)


class ModelRegistry:
    """Manage trained models - save, load, version control"""
    
    def __init__(self, model_dir: str = "backend/ml/models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
    
    def save_model(self, model: Any, model_name: str, metadata: Dict = None):
        """Save trained model with metadata"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.model_dir / f"{model_name}_{timestamp}.pkl"
        
        with open(filepath, 'wb') as f:
            pickle.dump(model, f)
        
        # Save metadata
        if metadata:
            meta_filepath = self.model_dir / f"{model_name}_{timestamp}_meta.json"
            import json
            with open(meta_filepath, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved model to {filepath}")
        return str(filepath)
    
    def load_model(self, model_name: str) -> Any:
        """Load latest version of model"""
        models = sorted(self.model_dir.glob(f"{model_name}_*.pkl"))
        if not models:
            raise FileNotFoundError(f"No models found for {model_name}")
        
        latest = models[-1]
        with open(latest, 'rb') as f:
            model = pickle.load(f)
        
        logger.info(f"Loaded model from {latest}")
        return model
    
    def list_models(self) -> Dict[str, List[str]]:
        """List all available models"""
        models = {}
        for pkl in self.model_dir.glob("*.pkl"):
            model_name = pkl.stem.rsplit('_', 1)[0]
            if model_name not in models:
                models[model_name] = []
            models[model_name].append(pkl.name)
        
        return models
