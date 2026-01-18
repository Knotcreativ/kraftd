"""Signals-Broadcaster Bridge Service

Integrates Phase 5 (Signals Intelligence) with Phase 7 (Real-Time Streaming).
Emits real-time events when signals are detected, enabling live updates to connected WebSocket clients.

Provides:
- Event emission for price updates
- Risk alert broadcasting
- Anomaly detection events
- Trend change notifications
- Supplier signal events
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime
from models.signals import (
    RiskSignal, RiskLevel, AlertType, PriceTrend, TrendDirection,
    SupplierMetric, AnomalyDetection
)
from models.streaming import (
    RiskAlert, PriceUpdate, AnomalyDetected, TrendChange, SupplierSignal,
    AlertLevel, AnomalyType, TrendDirection as StreamTrendDirection, SignalType
)

logger = logging.getLogger(__name__)

# Import broadcaster - will be initialized at module load
try:
    from services.event_broadcaster import broadcaster
    BROADCASTER_AVAILABLE = True
except Exception as e:
    logger.warning(f"EventBroadcaster not available: {e}")
    BROADCASTER_AVAILABLE = False


class SignalsBroadcasterBridge:
    """Bridge between Signals Intelligence and Real-Time Streaming
    
    Converts signal detection events into streaming events and broadcasts them
    to connected WebSocket clients in real-time.
    """
    
    @staticmethod
    async def broadcast_price_update(
        item_id: str,
        current_price: float,
        previous_price: float,
        trend: PriceTrend,
        volatility: float,
        moving_avg_30: Optional[float] = None,
        moving_avg_90: Optional[float] = None
    ) -> bool:
        """Broadcast real-time price update to connected clients
        
        Args:
            item_id: Item/product ID
            current_price: Current price point
            previous_price: Previous price for comparison
            trend: PriceTrend object with direction and change info
            volatility: Price volatility (standard deviation)
            moving_avg_30: 30-day moving average (optional)
            moving_avg_90: 90-day moving average (optional)
            
        Returns:
            True if broadcast successful, False otherwise
        """
        if not BROADCASTER_AVAILABLE:
            logger.warning("Broadcaster not available - price update not sent")
            return False
        
        try:
            price_update = PriceUpdate(
                item_id=item_id,
                current_price=current_price,
                previous_price=previous_price,
                price_change=current_price - previous_price,
                price_change_percent=trend.price_change_percent,
                volatility=volatility,
                trend_direction=trend.direction.value,
                moving_avg_30=moving_avg_30,
                moving_avg_90=moving_avg_90,
                timestamp=datetime.utcnow()
            )
            
            messages_sent = await broadcaster.broadcast_event(
                price_update,
                topic="prices"
            )
            
            logger.info(f"Price update broadcast for {item_id} to {messages_sent} clients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to broadcast price update: {e}")
            return False
    
    @staticmethod
    async def broadcast_risk_alert(
        item_id: str,
        signal: RiskSignal,
        supplier_id: Optional[str] = None
    ) -> bool:
        """Broadcast risk alert to connected clients
        
        Args:
            item_id: Item/product ID
            signal: RiskSignal detected
            supplier_id: Supplier ID (optional)
            
        Returns:
            True if broadcast successful, False otherwise
        """
        if not BROADCASTER_AVAILABLE:
            logger.warning("Broadcaster not available - risk alert not sent")
            return False
        
        try:
            # Map RiskLevel to AlertLevel
            alert_level_map = {
                RiskLevel.CRITICAL: AlertLevel.CRITICAL,
                RiskLevel.HIGH: AlertLevel.HIGH,
                RiskLevel.MEDIUM: AlertLevel.MEDIUM,
                RiskLevel.LOW: AlertLevel.LOW
            }
            
            alert_level = alert_level_map.get(signal.severity, AlertLevel.MEDIUM)
            
            risk_alert = RiskAlert(
                item_id=item_id,
                supplier_id=supplier_id,
                risk_level=alert_level,
                alert_type=signal.signal_type.value,
                message=signal.title,
                description=signal.description,
                impact=signal.impact,
                recommendation=signal.recommendation,
                risk_score=signal.score,
                timestamp=datetime.utcnow(),
                details={
                    "severity": signal.severity.value,
                    "impact": signal.impact,
                    "recommendation": signal.recommendation
                }
            )
            
            messages_sent = await broadcaster.broadcast_event(
                risk_alert,
                topic="alerts"
            )
            
            logger.info(f"Risk alert broadcast for {item_id} ({signal.signal_type.value}) to {messages_sent} clients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to broadcast risk alert: {e}")
            return False
    
    @staticmethod
    async def broadcast_anomaly_detected(
        item_id: str,
        anomaly_type: str,
        current_value: float,
        expected_value: float,
        deviation_percent: float,
        z_score: float,
        severity: str = "MEDIUM"
    ) -> bool:
        """Broadcast anomaly detection event to connected clients
        
        Args:
            item_id: Item/product ID
            anomaly_type: Type of anomaly (PRICE_SPIKE, VOLUME_ANOMALY, etc)
            current_value: Current anomalous value
            expected_value: Expected/baseline value
            deviation_percent: Percentage deviation from expected
            z_score: Z-score for statistical significance
            severity: Anomaly severity (LOW, MEDIUM, HIGH, CRITICAL)
            
        Returns:
            True if broadcast successful, False otherwise
        """
        if not BROADCASTER_AVAILABLE:
            logger.warning("Broadcaster not available - anomaly event not sent")
            return False
        
        try:
            # Map anomaly type string to AnomalyType enum
            anomaly_type_map = {
                "PRICE_SPIKE": AnomalyType.PRICE_SPIKE,
                "VOLUME_ANOMALY": AnomalyType.VOLUME_ANOMALY,
                "TREND_BREAK": AnomalyType.TREND_BREAK,
                "UNUSUAL_PATTERN": AnomalyType.UNUSUAL_PATTERN
            }
            
            anom_type = anomaly_type_map.get(anomaly_type, AnomalyType.UNUSUAL_PATTERN)
            
            anomaly = AnomalyDetected(
                item_id=item_id,
                anomaly_type=anom_type,
                current_value=current_value,
                expected_value=expected_value,
                deviation_percent=deviation_percent,
                z_score=z_score,
                severity=severity,
                timestamp=datetime.utcnow(),
                details={
                    "z_score": z_score,
                    "deviation_percent": deviation_percent,
                    "analysis_method": "statistical"
                }
            )
            
            messages_sent = await broadcaster.broadcast_event(
                anomaly,
                topic="anomalies"
            )
            
            logger.info(f"Anomaly event broadcast for {item_id} ({anomaly_type}) to {messages_sent} clients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to broadcast anomaly detection: {e}")
            return False
    
    @staticmethod
    async def broadcast_trend_change(
        item_id: str,
        previous_direction: TrendDirection,
        new_direction: TrendDirection,
        change_details: Optional[Dict] = None
    ) -> bool:
        """Broadcast trend change event to connected clients
        
        Args:
            item_id: Item/product ID
            previous_direction: Previous trend direction
            new_direction: New trend direction
            change_details: Optional dict with additional context
            
        Returns:
            True if broadcast successful, False otherwise
        """
        if not BROADCASTER_AVAILABLE:
            logger.warning("Broadcaster not available - trend change not sent")
            return False
        
        try:
            # Map TrendDirection to streaming TrendDirection
            trend_map = {
                TrendDirection.UPWARD: StreamTrendDirection.UPTREND,
                TrendDirection.DOWNWARD: StreamTrendDirection.DOWNTREND,
                TrendDirection.STABLE: StreamTrendDirection.STABLE,
                TrendDirection.VOLATILE: StreamTrendDirection.VOLATILE
            }
            
            trend_change = TrendChange(
                item_id=item_id,
                previous_trend=trend_map.get(previous_direction, StreamTrendDirection.STABLE),
                new_trend=trend_map.get(new_direction, StreamTrendDirection.STABLE),
                change_magnitude=0.0,  # Would be calculated if needed
                confidence=0.95,  # Default confidence
                forecast_value=None,
                timestamp=datetime.utcnow(),
                details=change_details or {
                    "previous": previous_direction.value,
                    "new": new_direction.value
                }
            )
            
            messages_sent = await broadcaster.broadcast_event(
                trend_change,
                topic="trends"
            )
            
            logger.info(f"Trend change broadcast for {item_id} ({previous_direction.value} → {new_direction.value}) to {messages_sent} clients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to broadcast trend change: {e}")
            return False
    
    @staticmethod
    async def broadcast_supplier_signal(
        supplier_id: str,
        signal_type: str,
        health_status: Optional[str] = None,
        performance_score: Optional[float] = None,
        message: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> bool:
        """Broadcast supplier signal event to connected clients
        
        Args:
            supplier_id: Supplier ID
            signal_type: Type of supplier signal (HEALTH_CHANGE, PERFORMANCE_ALERT, etc)
            health_status: Current health status (HEALTHY, RISK, CRITICAL)
            performance_score: Performance score (0-100)
            message: Human-readable message
            details: Additional details dict
            
        Returns:
            True if broadcast successful, False otherwise
        """
        if not BROADCASTER_AVAILABLE:
            logger.warning("Broadcaster not available - supplier signal not sent")
            return False
        
        try:
            supplier_signal = SupplierSignal(
                supplier_id=supplier_id,
                signal_type=signal_type,
                health_status=health_status,
                performance_score=performance_score,
                message=message or f"Supplier {supplier_id} signal: {signal_type}",
                risk_factors=[],
                timestamp=datetime.utcnow(),
                details=details or {}
            )
            
            messages_sent = await broadcaster.broadcast_event(
                supplier_signal,
                topic="signals"
            )
            
            logger.info(f"Supplier signal broadcast for {supplier_id} ({signal_type}) to {messages_sent} clients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to broadcast supplier signal: {e}")
            return False
