"""Signals Intelligence Data Models

Pydantic models for KraftdIntel signals intelligence layer (Phase 5).
Covers price trends, risk alerts, supplier performance, and predictions.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS FOR SIGNALS LAYER
# ============================================================================

class TrendDirection(str, Enum):
    """Price trend direction enumeration"""
    UPWARD = "upward"
    DOWNWARD = "downward"
    STABLE = "stable"
    VOLATILE = "volatile"


class RiskLevel(str, Enum):
    """Risk severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of alerts that can be generated"""
    PRICE_SPIKE = "price_spike"
    PRICE_DROP = "price_drop"
    VOLATILITY_WARNING = "volatility_warning"
    SUPPLIER_ISSUE = "supplier_issue"
    ANOMALY = "anomaly_detected"
    TREND_CHANGE = "trend_change"
    FORECAST = "forecast_warning"


class SupplierHealthStatus(str, Enum):
    """Supplier performance health status"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class AnalysisPeriod(str, Enum):
    """Time periods for analysis"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


# ============================================================================
# PRICE TREND MODELS
# ============================================================================

class PricePoint(BaseModel):
    """Individual price data point"""
    timestamp: datetime = Field(..., description="Timestamp of price")
    price: float = Field(..., description="Price value", gt=0)
    quantity: Optional[float] = Field(None, description="Quantity purchased", ge=0)
    supplier_id: Optional[str] = Field(None, description="Supplier ID")
    document_id: Optional[str] = Field(None, description="Source document ID")
    confidence: float = Field(default=1.0, ge=0, le=1, description="Confidence score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-01-18T14:00:00Z",
                "price": 150.50,
                "quantity": 100,
                "supplier_id": "supp-001",
                "document_id": "doc-001",
                "confidence": 0.95
            }
        }


class PriceTrend(BaseModel):
    """Price trend analysis for a specific item"""
    item_id: str = Field(..., description="Item/SKU identifier")
    item_name: str = Field(..., description="Item name")
    period: AnalysisPeriod = Field(default=AnalysisPeriod.MONTHLY, description="Analysis period")
    
    # Trend metrics
    direction: TrendDirection = Field(..., description="Overall trend direction")
    current_price: float = Field(..., description="Current price", gt=0)
    previous_price: float = Field(..., description="Previous period price", gt=0)
    price_change_percent: float = Field(..., description="Percentage change")
    
    # Statistical metrics
    moving_average_7d: Optional[float] = Field(None, description="7-day moving average")
    moving_average_30d: Optional[float] = Field(None, description="30-day moving average")
    volatility: float = Field(..., description="Price volatility (std dev)", ge=0)
    min_price: float = Field(..., description="Minimum price in period", gt=0)
    max_price: float = Field(..., description="Maximum price in period", gt=0)
    
    # Forecast
    forecasted_price: Optional[float] = Field(None, description="Predicted next price")
    forecast_confidence: Optional[float] = Field(None, ge=0, le=1, description="Forecast confidence")
    
    # Metadata
    data_points: int = Field(..., description="Number of price points analyzed", ge=1)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "SKU-001",
                "item_name": "Widget A",
                "period": "monthly",
                "direction": "upward",
                "current_price": 155.00,
                "previous_price": 150.00,
                "price_change_percent": 3.33,
                "volatility": 2.5,
                "min_price": 148.0,
                "max_price": 160.0,
                "forecasted_price": 157.50,
                "data_points": 30,
                "last_updated": "2026-01-18T14:00:00Z"
            }
        }


class TrendListResponse(BaseModel):
    """Response for trend list queries"""
    total_count: int = Field(..., description="Total trends found")
    trends: List[PriceTrend] = Field(..., description="Array of trends")
    period: AnalysisPeriod = Field(..., description="Analysis period used")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# RISK ALERT MODELS
# ============================================================================

class RiskSignal(BaseModel):
    """Individual risk signal"""
    signal_type: AlertType = Field(..., description="Type of alert")
    severity: RiskLevel = Field(..., description="Risk severity level")
    score: float = Field(..., ge=0, le=100, description="Risk score (0-100)")
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Detailed description")
    impact: str = Field(..., description="Business impact of this risk")
    recommendation: str = Field(..., description="Recommended action")
    
    class Config:
        json_schema_extra = {
            "example": {
                "signal_type": "price_spike",
                "severity": "high",
                "score": 75,
                "title": "Significant Price Increase Detected",
                "description": "Widget A price increased 15% in last week",
                "impact": "Budget impact of $2,500 if purchased at current rates",
                "recommendation": "Negotiate with supplier or find alternatives"
            }
        }


class RiskAlert(BaseModel):
    """Comprehensive risk alert for an item"""
    alert_id: str = Field(..., description="Unique alert identifier")
    item_id: str = Field(..., description="Item/SKU identifier")
    item_name: str = Field(..., description="Item name")
    
    # Overall risk
    overall_risk_level: RiskLevel = Field(..., description="Overall risk level")
    overall_risk_score: float = Field(..., ge=0, le=100, description="Overall risk score")
    
    # Individual signals
    signals: List[RiskSignal] = Field(..., description="Individual risk signals")
    
    # Thresholds
    price_threshold_breach: Optional[bool] = Field(None, description="Price threshold breached")
    volatility_threshold_breach: Optional[bool] = Field(None, description="Volatility threshold breached")
    supplier_issue_detected: Optional[bool] = Field(None, description="Supplier problem detected")
    
    # Escalation
    escalation_required: bool = Field(default=False, description="Escalation needed")
    escalation_reason: Optional[str] = Field(None, description="Why escalation needed")
    escalation_to: Optional[str] = Field(None, description="Escalate to this role/person")
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="When alert expires")
    acknowledged: bool = Field(default=False)
    acknowledged_at: Optional[datetime] = Field(None)
    acknowledged_by: Optional[str] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "alert-001",
                "item_id": "SKU-001",
                "item_name": "Widget A",
                "overall_risk_level": "high",
                "overall_risk_score": 78,
                "signals": [
                    {
                        "signal_type": "price_spike",
                        "severity": "high",
                        "score": 85,
                        "title": "Price increase detected",
                        "description": "Widget A up 15% YoY",
                        "impact": "$2,500 budget impact",
                        "recommendation": "Negotiate or source alternative"
                    }
                ],
                "escalation_required": True,
                "escalation_to": "procurement_manager",
                "created_at": "2026-01-18T14:00:00Z"
            }
        }


class AlertListResponse(BaseModel):
    """Response for alert list queries"""
    total_count: int = Field(..., description="Total alerts")
    alerts: List[RiskAlert] = Field(..., description="Alert list")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Applied filters")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# SUPPLIER PERFORMANCE MODELS
# ============================================================================

class SupplierMetric(BaseModel):
    """Individual supplier performance metric"""
    metric_name: str = Field(..., description="Metric name")
    current_value: float = Field(..., description="Current value")
    target_value: Optional[float] = Field(None, description="Target/goal value")
    benchmark: Optional[float] = Field(None, description="Industry benchmark")
    trend: TrendDirection = Field(default=TrendDirection.STABLE, description="Metric trend")
    status: str = Field(..., description="Pass/Fail status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metric_name": "on_time_delivery",
                "current_value": 94.5,
                "target_value": 95.0,
                "benchmark": 92.0,
                "trend": "stable",
                "status": "good"
            }
        }


class SupplierPerformance(BaseModel):
    """Comprehensive supplier performance analysis"""
    supplier_id: str = Field(..., description="Supplier identifier")
    supplier_name: str = Field(..., description="Supplier name")
    
    # Overall health
    health_status: SupplierHealthStatus = Field(..., description="Overall health status")
    overall_score: float = Field(..., ge=0, le=100, description="Overall score (0-100)")
    
    # Key metrics
    on_time_delivery: float = Field(..., ge=0, le=100, description="On-time delivery %")
    quality_score: float = Field(..., ge=0, le=100, description="Quality score")
    price_competitiveness: float = Field(..., ge=0, le=100, description="Price score")
    responsiveness: float = Field(..., ge=0, le=100, description="Responsiveness score")
    
    # Detailed metrics
    metrics: List[SupplierMetric] = Field(default_factory=list, description="Detailed metrics")
    
    # Risk factors
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    
    # Historical tracking
    previous_score: Optional[float] = Field(None, ge=0, le=100, description="Previous score")
    score_trend: TrendDirection = Field(default=TrendDirection.STABLE, description="Score trend")
    
    # Comparison
    rank_in_category: Optional[int] = Field(None, description="Rank among similar suppliers")
    total_in_category: Optional[int] = Field(None, description="Total suppliers in category")
    
    # Timing
    evaluation_period: AnalysisPeriod = Field(default=AnalysisPeriod.MONTHLY)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "supplier_id": "supp-001",
                "supplier_name": "ABC Manufacturing",
                "health_status": "good",
                "overall_score": 87.5,
                "on_time_delivery": 94.5,
                "quality_score": 89.0,
                "price_competitiveness": 85.0,
                "responsiveness": 86.5,
                "rank_in_category": 3,
                "total_in_category": 12,
                "score_trend": "upward",
                "last_updated": "2026-01-18T14:00:00Z"
            }
        }


class SupplierListResponse(BaseModel):
    """Response for supplier performance list queries"""
    total_count: int = Field(..., description="Total suppliers")
    suppliers: List[SupplierPerformance] = Field(..., description="Supplier list")
    category: Optional[str] = Field(None, description="Filter category if applied")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# PREDICTION MODELS
# ============================================================================

class PricePrediction(BaseModel):
    """Price prediction for future periods"""
    item_id: str = Field(..., description="Item identifier")
    item_name: str = Field(..., description="Item name")
    prediction_date: datetime = Field(..., description="Date of prediction")
    
    # Predictions
    predicted_price: float = Field(..., description="Predicted price", gt=0)
    confidence_interval_lower: float = Field(..., description="Lower 95% CI", gt=0)
    confidence_interval_upper: float = Field(..., description="Upper 95% CI", gt=0)
    confidence_level: float = Field(..., ge=0, le=1, description="Model confidence")
    
    # Model info
    model_type: str = Field(..., description="Type of forecasting model used")
    factors: List[str] = Field(default_factory=list, description="Factors influencing prediction")
    
    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "SKU-001",
                "item_name": "Widget A",
                "prediction_date": "2026-02-01",
                "predicted_price": 158.75,
                "confidence_interval_lower": 155.20,
                "confidence_interval_upper": 162.30,
                "confidence_level": 0.92,
                "model_type": "ARIMA",
                "factors": ["seasonal_trend", "supplier_capacity", "market_demand"]
            }
        }


class AnomalyDetection(BaseModel):
    """Anomaly detection result"""
    item_id: str = Field(..., description="Item identifier")
    anomaly_type: str = Field(..., description="Type of anomaly")
    severity: RiskLevel = Field(..., description="Anomaly severity")
    description: str = Field(..., description="What is anomalous")
    expected_value: float = Field(..., description="Expected value")
    actual_value: float = Field(..., description="Actual/observed value")
    deviation_percent: float = Field(..., description="Deviation percentage")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")
    
    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "SKU-001",
                "anomaly_type": "sudden_price_change",
                "severity": "high",
                "description": "Price jumped 25% with no explanation",
                "expected_value": 150.0,
                "actual_value": 187.50,
                "deviation_percent": 25.0,
                "confidence": 0.88
            }
        }


# ============================================================================
# REQUEST MODELS
# ============================================================================

class TrendQueryRequest(BaseModel):
    """Request for trend analysis"""
    item_id: Optional[str] = Field(None, description="Filter by item ID")
    item_ids: Optional[List[str]] = Field(None, description="Filter by multiple items")
    period: AnalysisPeriod = Field(default=AnalysisPeriod.MONTHLY, description="Analysis period")
    supplier_id: Optional[str] = Field(None, description="Filter by supplier")
    days_back: int = Field(default=90, ge=1, description="Days of data to analyze")
    
    class Config:
        json_schema_extra = {
            "example": {
                "item_ids": ["SKU-001", "SKU-002"],
                "period": "monthly",
                "days_back": 90
            }
        }


class AlertQueryRequest(BaseModel):
    """Request for alert filtering"""
    risk_level: Optional[RiskLevel] = Field(None, description="Filter by risk level")
    item_id: Optional[str] = Field(None, description="Filter by item")
    acknowledged: Optional[bool] = Field(None, description="Filter by acknowledgment status")
    days_back: int = Field(default=30, ge=1, description="Days to look back")
    
    class Config:
        json_schema_extra = {
            "example": {
                "risk_level": "high",
                "acknowledged": False,
                "days_back": 30
            }
        }


class SupplierQueryRequest(BaseModel):
    """Request for supplier analysis"""
    supplier_id: Optional[str] = Field(None, description="Specific supplier")
    health_status: Optional[SupplierHealthStatus] = Field(None, description="Filter by status")
    category: Optional[str] = Field(None, description="Supplier category")
    min_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum score filter")
    
    class Config:
        json_schema_extra = {
            "example": {
                "health_status": "fair",
                "category": "raw_materials",
                "min_score": 80
            }
        }


class PredictionRequest(BaseModel):
    """Request for price predictions"""
    item_id: str = Field(..., description="Item to predict")
    periods_ahead: int = Field(default=3, ge=1, le=12, description="Periods to forecast")
    confidence_level: float = Field(default=0.95, ge=0.80, le=0.99, description="Confidence level")
    
    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "SKU-001",
                "periods_ahead": 3,
                "confidence_level": 0.95
            }
        }


# ============================================================================
# ERROR RESPONSE MODELS
# ============================================================================

class SignalsErrorResponse(BaseModel):
    """Error response for signals endpoints"""
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "ITEM_NOT_FOUND",
                "message": "No price data found for item SKU-001",
                "details": {"item_id": "SKU-001", "data_points": 0},
                "timestamp": "2026-01-18T14:00:00Z"
            }
        }
