"""
Phase 7: Real-Time Streaming Event Models

This module defines all event types and messages for WebSocket streaming.
"""

from enum import Enum
from typing import Optional, Dict, Any, Union, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


# ============= ENUMERATIONS =============

class EventType(str, Enum):
    """Types of streaming events"""
    PRICE_UPDATE = "price_update"
    RISK_ALERT = "risk_alert"
    SUPPLIER_SIGNAL = "supplier_signal"
    ANOMALY_DETECTED = "anomaly_detected"
    TREND_CHANGE = "trend_change"
    HEALTH_CHECK = "health_check"


class AlertLevel(str, Enum):
    """Risk/alert severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TrendDirection(str, Enum):
    """Price trend direction"""
    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"
    STABLE = "STABLE"


class SignalType(str, Enum):
    """Types of supplier signals"""
    HEALTH_CHANGE = "HEALTH_CHANGE"
    PERFORMANCE_ALERT = "PERFORMANCE_ALERT"
    RISK_FACTOR = "RISK_FACTOR"


class AnomalyType(str, Enum):
    """Types of anomalies detected"""
    PRICE_ANOMALY = "PRICE_ANOMALY"
    TREND_BREAK = "TREND_BREAK"
    SUPPLIER_ANOMALY = "SUPPLIER_ANOMALY"
    VOLATILITY_SPIKE = "VOLATILITY_SPIKE"


# ============= CLIENT REQUESTS =============

class SubscriptionRequest(BaseModel):
    """Client request to subscribe to a WebSocket stream"""
    action: str = Field("subscribe", description="Action type")
    filters: Optional[Dict[str, Any]] = Field(
        None, 
        description="Optional filters for events (e.g., risk_level=['CRITICAL', 'HIGH'])"
    )
    items: Optional[List[str]] = Field(
        None,
        description="Item IDs to track (for prices, trends)"
    )
    suppliers: Optional[List[str]] = Field(
        None,
        description="Supplier IDs to track"
    )
    anomaly_types: Optional[List[str]] = Field(
        None,
        description="Types of anomalies to receive"
    )
    sensitivity: Optional[str] = Field(
        "MEDIUM",
        description="Sensitivity level: HIGH, MEDIUM, LOW"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "action": "subscribe",
                "items": ["COPPER", "STEEL"],
                "filters": {
                    "risk_level": ["CRITICAL", "HIGH"],
                    "trend_direction": ["UPTREND", "DOWNTREND"]
                }
            }
        }


class UnsubscriptionRequest(BaseModel):
    """Client request to unsubscribe from a stream"""
    action: str = Field("unsubscribe", description="Action type")
    topic: Optional[str] = Field(
        None,
        description="Topic to unsubscribe from"
    )


class AcknowledgeAlertRequest(BaseModel):
    """Client request to acknowledge a risk alert"""
    action: str = Field("acknowledge", description="Action type")
    alert_id: str = Field(..., description="Alert ID to acknowledge")
    notes: Optional[str] = Field(
        None,
        description="Optional notes about acknowledgment"
    )


# ============= EVENTS (Server -> Client) =============

class PriceUpdate(BaseModel):
    """Real-time price update event"""
    type: EventType = Field(EventType.PRICE_UPDATE)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    item_id: str = Field(..., description="Item/commodity ID")
    price: float = Field(..., description="Current price")
    previous_price: Optional[float] = Field(
        None,
        description="Previous price for comparison"
    )
    change_percent: float = Field(..., description="Price change percentage")
    trend_direction: TrendDirection = Field(..., description="Trend direction")
    volatility: float = Field(..., description="Volatility percentage")
    moving_average_7d: float = Field(..., description="7-day moving average")
    moving_average_30d: float = Field(..., description="30-day moving average")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "price_update",
                "timestamp": "2024-01-18T10:30:45.123Z",
                "item_id": "COPPER",
                "price": 8.95,
                "previous_price": 8.85,
                "change_percent": 1.13,
                "trend_direction": "UPTREND",
                "volatility": 15.3,
                "moving_average_7d": 8.72,
                "moving_average_30d": 8.45
            }
        }


class RiskAlert(BaseModel):
    """Risk alert event - sent when risk threshold exceeded"""
    type: EventType = Field(EventType.RISK_ALERT)
    alert_id: str = Field(
        default_factory=lambda: f"alert-{uuid.uuid4()}",
        description="Unique alert ID"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    risk_level: AlertLevel = Field(..., description="Alert severity")
    alert_type: str = Field(
        ...,
        description="Type of alert (e.g., PRICE_VOLATILITY, SUPPLIER_RISK)"
    )
    item_id: Optional[str] = Field(None, description="Item ID if applicable")
    supplier_id: Optional[str] = Field(None, description="Supplier ID if applicable")
    message: str = Field(..., description="Human-readable alert message")
    details: Dict[str, Any] = Field(..., description="Alert details")
    acknowledged: bool = Field(False, description="Whether alert was acknowledged")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "risk_alert",
                "alert_id": "alert-550e8400",
                "timestamp": "2024-01-18T10:30:45Z",
                "risk_level": "CRITICAL",
                "alert_type": "PRICE_VOLATILITY",
                "item_id": "COPPER",
                "message": "Price volatility exceeded 25% threshold",
                "details": {
                    "current_price": 8.95,
                    "previous_price": 7.50,
                    "volatility_percent": 26.3,
                    "recommended_action": "Review hedging strategy"
                },
                "acknowledged": False
            }
        }


class SupplierSignal(BaseModel):
    """Supplier performance signal event"""
    type: EventType = Field(EventType.SUPPLIER_SIGNAL)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    supplier_id: str = Field(..., description="Supplier ID")
    signal_type: SignalType = Field(..., description="Type of signal")
    old_value: Optional[Any] = Field(None, description="Previous value")
    new_value: Optional[Any] = Field(None, description="New value")
    message: str = Field(..., description="Signal message")
    details: Dict[str, Any] = Field(..., description="Signal details")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "supplier_signal",
                "timestamp": "2024-01-18T10:30:45Z",
                "supplier_id": "SUPPLIER_A",
                "signal_type": "HEALTH_CHANGE",
                "old_value": "GOOD",
                "new_value": "FAIR",
                "message": "Supplier health declined: on-time delivery rate dropped",
                "details": {
                    "on_time_percent": 92.5,
                    "quality_percent": 98.2,
                    "overall_score": 72
                }
            }
        }


class AnomalyDetected(BaseModel):
    """Anomaly detection event"""
    type: EventType = Field(EventType.ANOMALY_DETECTED)
    anomaly_id: str = Field(
        default_factory=lambda: f"anom-{uuid.uuid4()}",
        description="Unique anomaly ID"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    anomaly_type: AnomalyType = Field(..., description="Type of anomaly")
    item_id: Optional[str] = Field(None, description="Item ID if applicable")
    supplier_id: Optional[str] = Field(None, description="Supplier ID if applicable")
    severity: AlertLevel = Field(..., description="Anomaly severity")
    z_score: float = Field(..., description="Z-score deviation")
    message: str = Field(..., description="Anomaly message")
    details: Dict[str, Any] = Field(..., description="Anomaly details")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "anomaly_detected",
                "anomaly_id": "anom-550e8400",
                "timestamp": "2024-01-18T10:30:45Z",
                "anomaly_type": "PRICE_ANOMALY",
                "item_id": "COPPER",
                "severity": "HIGH",
                "z_score": 3.2,
                "message": "Price spike detected: 25% above normal",
                "details": {
                    "current_price": 9.50,
                    "expected_price": 7.60,
                    "std_dev_threshold": 2.5,
                    "likely_cause": "Supply disruption"
                }
            }
        }


class TrendChange(BaseModel):
    """Trend direction change event"""
    type: EventType = Field(EventType.TREND_CHANGE)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    item_id: str = Field(..., description="Item ID")
    old_trend: TrendDirection = Field(..., description="Previous trend")
    new_trend: TrendDirection = Field(..., description="New trend")
    message: str = Field(..., description="Trend change message")
    details: Dict[str, Any] = Field(..., description="Trend details")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "trend_change",
                "timestamp": "2024-01-18T10:30:45Z",
                "item_id": "COPPER",
                "old_trend": "UPTREND",
                "new_trend": "STABLE",
                "message": "Trend changed from UPTREND to STABLE",
                "details": {
                    "moving_average_7d": 8.72,
                    "moving_average_30d": 8.45,
                    "volatility": 15.3,
                    "forecast_next_7d": 8.80
                }
            }
        }


class HealthCheck(BaseModel):
    """Server health check event"""
    type: EventType = Field(EventType.HEALTH_CHECK)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field("HEALTHY", description="Server status")
    active_connections: int = Field(..., description="Number of active connections")
    messages_sent_total: int = Field(..., description="Total messages sent")
    errors_last_minute: int = Field(..., description="Errors in last minute")
    avg_latency_ms: float = Field(..., description="Average latency in milliseconds")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "health_check",
                "timestamp": "2024-01-18T10:30:45Z",
                "status": "HEALTHY",
                "active_connections": 127,
                "messages_sent_total": 5432,
                "errors_last_minute": 0,
                "avg_latency_ms": 45.2
            }
        }


# Union type for all possible streaming events
StreamingEvent = Union[
    PriceUpdate,
    RiskAlert,
    SupplierSignal,
    AnomalyDetected,
    TrendChange,
    HealthCheck
]
