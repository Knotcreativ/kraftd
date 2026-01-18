"""Signals Intelligence Service

Core algorithms for price trend analysis, risk detection, and supplier analytics.
Implements Phase 5: Signals Intelligence layer for KraftdIntel.
"""

import logging
import statistics
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from models.signals import (
    PricePoint, PriceTrend, TrendDirection, AnalysisPeriod,
    RiskAlert, RiskSignal, AlertType, RiskLevel, SupplierMetric,
    SupplierPerformance, SupplierHealthStatus, PricePrediction,
    AnomalyDetection
)

logger = logging.getLogger(__name__)


class TrendAnalysisService:
    """Analyzes price trends and provides forecasting"""
    
    @staticmethod
    def calculate_moving_average(prices: List[float], window: int) -> Optional[float]:
        """Calculate moving average for given window size"""
        if len(prices) < window:
            return None
        return statistics.mean(prices[-window:])
    
    @staticmethod
    def calculate_volatility(prices: List[float]) -> float:
        """Calculate price volatility (standard deviation)"""
        if len(prices) < 2:
            return 0.0
        return statistics.stdev(prices)
    
    @staticmethod
    def calculate_price_change_percent(current: float, previous: float) -> float:
        """Calculate percentage change between two prices"""
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100
    
    @staticmethod
    def detect_trend_direction(prices: List[float]) -> TrendDirection:
        """Detect overall trend direction from prices"""
        if len(prices) < 2:
            return TrendDirection.STABLE
        
        # Calculate volatility
        volatility = TrendAnalysisService.calculate_volatility(prices)
        volatility_threshold = statistics.mean(prices) * 0.05  # 5% threshold
        
        if volatility > volatility_threshold:
            return TrendDirection.VOLATILE
        
        # Calculate simple trend
        first_half_avg = statistics.mean(prices[:len(prices)//2])
        second_half_avg = statistics.mean(prices[len(prices)//2:])
        
        change_percent = TrendAnalysisService.calculate_price_change_percent(
            second_half_avg, first_half_avg
        )
        
        if change_percent > 2:
            return TrendDirection.UPWARD
        elif change_percent < -2:
            return TrendDirection.DOWNWARD
        else:
            return TrendDirection.STABLE
    
    @staticmethod
    def simple_forecast(prices: List[float], periods: int = 1) -> Optional[float]:
        """Simple exponential smoothing forecast
        
        Args:
            prices: Historical price list
            periods: Number of periods to forecast ahead
            
        Returns:
            Forecasted price or None if insufficient data
        """
        if len(prices) < 3:
            return None
        
        # Simple exponential smoothing with alpha = 0.3
        alpha = 0.3
        forecast = prices[-1]
        
        for _ in range(periods):
            # Calculate next forecast
            forecast = alpha * prices[-1] + (1 - alpha) * forecast
        
        return round(forecast, 2)
    
    @staticmethod
    def analyze_trend(
        prices: List[float],
        timestamps: List[datetime],
        period: AnalysisPeriod = AnalysisPeriod.MONTHLY
    ) -> Dict:
        """Comprehensive trend analysis
        
        Args:
            prices: List of prices
            timestamps: Corresponding timestamps
            period: Analysis period
            
        Returns:
            Dictionary with trend metrics
        """
        if not prices:
            return {}
        
        current_price = prices[-1]
        previous_price = prices[0] if len(prices) > 1 else current_price
        
        trend_data = {
            "direction": TrendAnalysisService.detect_trend_direction(prices),
            "current_price": current_price,
            "previous_price": previous_price,
            "price_change_percent": TrendAnalysisService.calculate_price_change_percent(
                current_price, previous_price
            ),
            "moving_average_7d": TrendAnalysisService.calculate_moving_average(prices, 7),
            "moving_average_30d": TrendAnalysisService.calculate_moving_average(prices, 30),
            "volatility": TrendAnalysisService.calculate_volatility(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "forecasted_price": TrendAnalysisService.simple_forecast(prices, periods=1),
            "data_points": len(prices)
        }
        
        return trend_data


class RiskScoringService:
    """Calculates risk scores and generates alerts"""
    
    @staticmethod
    def calculate_price_risk(
        current_price: float,
        moving_avg: float,
        volatility: float,
        threshold_percent: float = 10.0
    ) -> Tuple[float, Optional[AlertType]]:
        """Calculate risk from price deviation
        
        Returns:
            (risk_score, alert_type)
        """
        if moving_avg == 0:
            return 0.0, None
        
        deviation_percent = abs((current_price - moving_avg) / moving_avg * 100)
        
        risk_score = min(100, deviation_percent * 2)  # 2x multiplier
        
        alert_type = None
        if deviation_percent > threshold_percent:
            if current_price > moving_avg:
                alert_type = AlertType.PRICE_SPIKE
            else:
                alert_type = AlertType.PRICE_DROP
        
        return risk_score, alert_type
    
    @staticmethod
    def calculate_volatility_risk(volatility: float, avg_price: float) -> float:
        """Calculate risk from price volatility
        
        High volatility indicates unpredictable pricing.
        """
        if avg_price == 0:
            return 0.0
        
        coefficient_of_variation = (volatility / avg_price) * 100
        
        # Risk increases exponentially with volatility
        # At 10% CV = 20 points, at 20% = 50 points, at 30% = 90 points
        risk_score = min(100, (coefficient_of_variation ** 1.5))
        
        return risk_score
    
    @staticmethod
    def calculate_supplier_risk(
        supplier_score: float,
        on_time_delivery: float,
        quality_score: float
    ) -> float:
        """Calculate risk from supplier performance"""
        
        weighted_risk = 0.0
        
        # Supplier score: 0-100 (100 is best, so invert for risk)
        weighted_risk += (100 - supplier_score) * 0.5
        
        # On-time delivery: <90% is risky
        if on_time_delivery < 90:
            weighted_risk += (90 - on_time_delivery) * 0.3
        
        # Quality: <85% is risky
        if quality_score < 85:
            weighted_risk += (85 - quality_score) * 0.2
        
        return min(100, weighted_risk)
    
    @staticmethod
    def score_to_risk_level(score: float) -> RiskLevel:
        """Convert numeric score to risk level"""
        if score < 25:
            return RiskLevel.LOW
        elif score < 50:
            return RiskLevel.MEDIUM
        elif score < 75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    @staticmethod
    def generate_risk_signals(
        item_id: str,
        price_trend: PriceTrend,
        supplier_score: Optional[float] = None
    ) -> List[RiskSignal]:
        """Generate individual risk signals for an item"""
        
        signals = []
        
        # Price spike/drop signal
        if abs(price_trend.price_change_percent) > 10:
            signals.append(RiskSignal(
                signal_type=AlertType.PRICE_SPIKE if price_trend.price_change_percent > 0 else AlertType.PRICE_DROP,
                severity=RiskLevel.HIGH if abs(price_trend.price_change_percent) > 20 else RiskLevel.MEDIUM,
                score=min(100, abs(price_trend.price_change_percent) * 1.5),
                title=f"{'Price Increase' if price_trend.price_change_percent > 0 else 'Price Decrease'} Detected",
                description=f"{item_id} price changed {price_trend.price_change_percent:.1f}% since last period",
                impact=f"Budget impact if trend continues",
                recommendation="Review supplier pricing or explore alternatives"
            ))
        
        # Volatility warning
        if price_trend.volatility > (price_trend.current_price * 0.10):
            signals.append(RiskSignal(
                signal_type=AlertType.VOLATILITY_WARNING,
                severity=RiskLevel.MEDIUM,
                score=min(100, (price_trend.volatility / price_trend.current_price) * 200),
                title="High Price Volatility",
                description=f"Price volatility (std dev: ${price_trend.volatility:.2f}) is elevated",
                impact="Difficult to forecast costs and budget accurately",
                recommendation="Increase safety stock or negotiate fixed-price contracts"
            ))
        
        # Trend change signal
        if price_trend.direction in [TrendDirection.VOLATILE]:
            signals.append(RiskSignal(
                signal_type=AlertType.TREND_CHANGE,
                severity=RiskLevel.MEDIUM,
                score=60,
                title="Unexpected Price Volatility",
                description=f"Price trend shows {price_trend.direction.value} pattern",
                impact="Difficulty in demand planning and budgeting",
                recommendation="Monitor closely and escalate if continues"
            ))
        
        return signals


class SupplierAnalyticsService:
    """Analyzes supplier performance metrics"""
    
    @staticmethod
    def calculate_overall_score(
        on_time_delivery: float,
        quality_score: float,
        price_competitiveness: float,
        responsiveness: float
    ) -> float:
        """Calculate weighted overall supplier score"""
        
        # Weights: delivery (40%), quality (30%), price (20%), responsiveness (10%)
        overall = (
            on_time_delivery * 0.40 +
            quality_score * 0.30 +
            price_competitiveness * 0.20 +
            responsiveness * 0.10
        )
        
        return round(overall, 1)
    
    @staticmethod
    def score_to_health_status(score: float) -> SupplierHealthStatus:
        """Convert score to health status"""
        if score >= 90:
            return SupplierHealthStatus.EXCELLENT
        elif score >= 80:
            return SupplierHealthStatus.GOOD
        elif score >= 70:
            return SupplierHealthStatus.FAIR
        elif score >= 50:
            return SupplierHealthStatus.POOR
        else:
            return SupplierHealthStatus.CRITICAL
    
    @staticmethod
    def identify_risk_factors(
        performance: Dict,
        benchmarks: Dict
    ) -> List[str]:
        """Identify specific risk factors for a supplier"""
        
        risk_factors = []
        
        # On-time delivery below benchmark
        if performance.get("on_time_delivery", 100) < benchmarks.get("on_time_delivery", 95):
            risk_factors.append("Below average on-time delivery")
        
        # Quality issues
        if performance.get("quality_score", 100) < 80:
            risk_factors.append("Quality concerns")
        
        # Price competitiveness
        if performance.get("price_competitiveness", 100) < benchmarks.get("price_competitiveness", 80):
            risk_factors.append("Higher than competitive prices")
        
        # Responsiveness issues
        if performance.get("responsiveness", 100) < 80:
            risk_factors.append("Poor responsiveness to inquiries")
        
        return risk_factors
    
    @staticmethod
    def analyze_supplier(
        supplier_id: str,
        supplier_name: str,
        metrics: Dict
    ) -> Dict:
        """Comprehensive supplier performance analysis"""
        
        # Calculate overall score
        overall_score = SupplierAnalyticsService.calculate_overall_score(
            metrics.get("on_time_delivery", 0),
            metrics.get("quality_score", 0),
            metrics.get("price_competitiveness", 0),
            metrics.get("responsiveness", 0)
        )
        
        # Determine health status
        health_status = SupplierAnalyticsService.score_to_health_status(overall_score)
        
        # Industry benchmarks (default values)
        benchmarks = {
            "on_time_delivery": 95,
            "quality_score": 90,
            "price_competitiveness": 80,
            "responsiveness": 85
        }
        
        # Identify risks
        risk_factors = SupplierAnalyticsService.identify_risk_factors(metrics, benchmarks)
        
        return {
            "overall_score": overall_score,
            "health_status": health_status,
            "risk_factors": risk_factors,
            "benchmarks": benchmarks
        }


class AnomalyDetectionService:
    """Detects unusual patterns in data"""
    
    @staticmethod
    def detect_price_anomalies(
        prices: List[float],
        threshold_std_dev: float = 2.5
    ) -> List[Tuple[int, float]]:
        """Detect price anomalies using statistical methods
        
        Returns:
            List of (index, deviation_percent) tuples for anomalies
        """
        if len(prices) < 3:
            return []
        
        mean = statistics.mean(prices)
        std_dev = statistics.stdev(prices)
        
        anomalies = []
        
        for i, price in enumerate(prices):
            # Z-score
            z_score = (price - mean) / std_dev if std_dev > 0 else 0
            
            if abs(z_score) > threshold_std_dev:
                deviation = abs((price - mean) / mean * 100)
                anomalies.append((i, deviation))
        
        return anomalies
    
    @staticmethod
    def detect_trend_breaks(
        prices: List[float],
        window: int = 10
    ) -> List[int]:
        """Detect sudden breaks or changes in trend"""
        if len(prices) < window * 2:
            return []
        
        breaks = []
        
        # Compare moving averages to detect breaks
        for i in range(window, len(prices) - window):
            before_avg = statistics.mean(prices[i-window:i])
            after_avg = statistics.mean(prices[i:i+window])
            
            change_percent = abs((after_avg - before_avg) / before_avg * 100) if before_avg > 0 else 0
            
            # Significant trend break (>15% change)
            if change_percent > 15:
                breaks.append(i)
        
        return breaks


class SignalsService:
    """Main service orchestrating all signals intelligence operations"""
    
    # In-memory storage
    _price_history: Dict[str, List[PricePoint]] = {}
    _risk_alerts: Dict[str, RiskAlert] = {}
    _supplier_metrics: Dict[str, Dict] = {}
    
    @staticmethod
    def add_price_point(item_id: str, price_point: PricePoint) -> None:
        """Add a price point to history"""
        if item_id not in SignalsService._price_history:
            SignalsService._price_history[item_id] = []
        
        SignalsService._price_history[item_id].append(price_point)
        logger.info(f"Price point added for {item_id}: ${price_point.price}")
    
    @staticmethod
    def get_price_trend(
        item_id: str,
        days_back: int = 90,
        period: AnalysisPeriod = AnalysisPeriod.MONTHLY
    ) -> Optional[PriceTrend]:
        """Get price trend for an item"""
        
        if item_id not in SignalsService._price_history:
            return None
        
        history = SignalsService._price_history[item_id]
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Filter by date range
        recent_prices = [
            p for p in history
            if p.timestamp >= cutoff_date
        ]
        
        if not recent_prices:
            return None
        
        prices = [p.price for p in recent_prices]
        timestamps = [p.timestamp for p in recent_prices]
        
        # Analyze trend
        trend_data = TrendAnalysisService.analyze_trend(prices, timestamps, period)
        
        return PriceTrend(
            item_id=item_id,
            item_name=item_id,  # Would come from catalog in production
            period=period,
            **trend_data,
            forecast_confidence=0.85  # Simple estimate
        )
    
    @staticmethod
    def create_risk_alert(
        item_id: str,
        risk_level: RiskLevel,
        signals: List[RiskSignal]
    ) -> str:
        """Create a new risk alert and store it"""
        
        alert_id = f"alert-{datetime.utcnow().timestamp()}"
        
        alert = RiskAlert(
            alert_id=alert_id,
            item_id=item_id,
            item_name=item_id,
            overall_risk_level=risk_level,
            overall_risk_score=sum(s.score for s in signals) / len(signals) if signals else 0,
            signals=signals
        )
        
        SignalsService._risk_alerts[alert_id] = alert
        logger.info(f"Risk alert created: {alert_id} for item {item_id}")
        
        return alert_id
    
    @staticmethod
    def get_risk_alerts(
        risk_level: Optional[RiskLevel] = None,
        days_back: int = 30
    ) -> List[RiskAlert]:
        """Get risk alerts with optional filtering"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        alerts = [
            a for a in SignalsService._risk_alerts.values()
            if a.created_at >= cutoff_date
        ]
        
        if risk_level:
            alerts = [a for a in alerts if a.overall_risk_level == risk_level]
        
        return sorted(alerts, key=lambda a: a.overall_risk_score, reverse=True)
    
    @staticmethod
    def add_supplier_metrics(supplier_id: str, metrics: Dict) -> None:
        """Add or update supplier metrics"""
        SignalsService._supplier_metrics[supplier_id] = metrics
        logger.info(f"Supplier metrics updated for {supplier_id}")
    
    @staticmethod
    def get_supplier_performance(supplier_id: str) -> Optional[SupplierPerformance]:
        """Get supplier performance analysis"""
        
        if supplier_id not in SignalsService._supplier_metrics:
            return None
        
        metrics = SignalsService._supplier_metrics[supplier_id]
        analysis = SupplierAnalyticsService.analyze_supplier(
            supplier_id,
            metrics.get("name", supplier_id),
            metrics
        )
        
        return SupplierPerformance(
            supplier_id=supplier_id,
            supplier_name=metrics.get("name", supplier_id),
            health_status=analysis["health_status"],
            overall_score=analysis["overall_score"],
            on_time_delivery=metrics.get("on_time_delivery", 0),
            quality_score=metrics.get("quality_score", 0),
            price_competitiveness=metrics.get("price_competitiveness", 0),
            responsiveness=metrics.get("responsiveness", 0),
            risk_factors=analysis["risk_factors"]
        )
    
    @staticmethod
    def clear_all() -> None:
        """Clear all stored data (for testing)"""
        SignalsService._price_history.clear()
        SignalsService._risk_alerts.clear()
        SignalsService._supplier_metrics.clear()
        logger.info("Signals service cleared")
