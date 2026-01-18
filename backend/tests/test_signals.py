"""Signals Intelligence Tests

Comprehensive test suite for Phase 5: Signals Intelligence layer
Tests for all services, models, and REST endpoints
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from models.signals import (
    PricePoint, PriceTrend, TrendDirection, AnalysisPeriod,
    RiskAlert, RiskSignal, AlertType, RiskLevel, SupplierHealthStatus,
    SupplierPerformance
)
from services.signals_service import (
    TrendAnalysisService, RiskScoringService, SupplierAnalyticsService,
    AnomalyDetectionService, SignalsService
)


class TestTrendAnalysisService:
    """Tests for trend analysis algorithms"""
    
    def test_calculate_moving_average_basic(self):
        """Test basic moving average calculation"""
        prices = [100, 102, 104, 106, 108]
        avg = TrendAnalysisService.calculate_moving_average(prices, 3)
        # (104 + 106 + 108) / 3 = 106
        assert avg == 106.0
    
    def test_calculate_moving_average_insufficient_data(self):
        """Test moving average with insufficient data"""
        prices = [100, 102]
        avg = TrendAnalysisService.calculate_moving_average(prices, 5)
        assert avg is None
    
    def test_calculate_volatility_stable_prices(self):
        """Test volatility with stable prices"""
        prices = [100, 100, 100, 100, 100]
        volatility = TrendAnalysisService.calculate_volatility(prices)
        assert volatility == 0.0
    
    def test_calculate_volatility_varying_prices(self):
        """Test volatility with varying prices"""
        prices = [100, 110, 95, 115, 90]
        volatility = TrendAnalysisService.calculate_volatility(prices)
        assert volatility > 0
    
    def test_price_change_percent(self):
        """Test price change percentage calculation"""
        change = TrendAnalysisService.calculate_price_change_percent(110, 100)
        assert change == 10.0
        
        change = TrendAnalysisService.calculate_price_change_percent(90, 100)
        assert change == -10.0
    
    def test_detect_trend_direction_upward(self):
        """Test upward trend detection"""
        prices = [100, 102, 104, 106, 108, 110, 112]
        direction = TrendAnalysisService.detect_trend_direction(prices)
        assert direction == TrendDirection.UPWARD
    
    def test_detect_trend_direction_downward(self):
        """Test downward trend detection"""
        prices = [112, 110, 108, 106, 104, 102, 100]
        direction = TrendAnalysisService.detect_trend_direction(prices)
        assert direction == TrendDirection.DOWNWARD
    
    def test_detect_trend_direction_stable(self):
        """Test stable trend detection"""
        prices = [100, 100.5, 100.2, 100.3, 100.1]
        direction = TrendAnalysisService.detect_trend_direction(prices)
        assert direction == TrendDirection.STABLE
    
    def test_simple_forecast(self):
        """Test simple exponential smoothing forecast"""
        prices = [100, 102, 104, 106, 108]
        forecast = TrendAnalysisService.simple_forecast(prices, periods=1)
        assert forecast is not None
        assert isinstance(forecast, float)
        # Forecast should be close to recent price
        assert 100 < forecast < 120
    
    def test_simple_forecast_insufficient_data(self):
        """Test forecast with insufficient data"""
        prices = [100]
        forecast = TrendAnalysisService.simple_forecast(prices, periods=1)
        assert forecast is None
    
    def test_analyze_trend_comprehensive(self):
        """Test comprehensive trend analysis"""
        prices = [100, 102, 104, 106, 108, 110]
        timestamps = [
            datetime.utcnow() - timedelta(days=5),
            datetime.utcnow() - timedelta(days=4),
            datetime.utcnow() - timedelta(days=3),
            datetime.utcnow() - timedelta(days=2),
            datetime.utcnow() - timedelta(days=1),
            datetime.utcnow()
        ]
        
        trend_data = TrendAnalysisService.analyze_trend(prices, timestamps, AnalysisPeriod.DAILY)
        
        assert "direction" in trend_data
        assert trend_data["direction"] == TrendDirection.UPWARD
        assert trend_data["current_price"] == 110
        assert trend_data["previous_price"] == 100
        assert trend_data["volatility"] >= 0


class TestRiskScoringService:
    """Tests for risk scoring algorithms"""
    
    def test_calculate_price_risk_spike(self):
        """Test risk calculation for price spike"""
        score, alert_type = RiskScoringService.calculate_price_risk(
            current_price=115,
            moving_avg=100,
            volatility=5,
            threshold_percent=10
        )
        assert score > 0
        assert alert_type == AlertType.PRICE_SPIKE
    
    def test_calculate_price_risk_drop(self):
        """Test risk calculation for price drop"""
        score, alert_type = RiskScoringService.calculate_price_risk(
            current_price=85,
            moving_avg=100,
            volatility=5,
            threshold_percent=10
        )
        assert score > 0
        assert alert_type == AlertType.PRICE_DROP
    
    def test_calculate_volatility_risk(self):
        """Test volatility risk calculation"""
        # High volatility (20% of price)
        risk = RiskScoringService.calculate_volatility_risk(
            volatility=20,
            avg_price=100
        )
        assert risk > 0
        
        # Low volatility (2% of price)
        low_risk = RiskScoringService.calculate_volatility_risk(
            volatility=2,
            avg_price=100
        )
        assert low_risk < risk
    
    def test_calculate_supplier_risk_excellent(self):
        """Test supplier risk calculation for excellent performance"""
        risk = RiskScoringService.calculate_supplier_risk(
            supplier_score=95,
            on_time_delivery=98,
            quality_score=96
        )
        assert risk < 10  # Low risk
    
    def test_calculate_supplier_risk_poor(self):
        """Test supplier risk calculation for poor performance"""
        risk = RiskScoringService.calculate_supplier_risk(
            supplier_score=50,
            on_time_delivery=70,
            quality_score=60
        )
        assert risk > 30  # High risk
    
    def test_score_to_risk_level_low(self):
        """Test score to risk level conversion - low"""
        level = RiskScoringService.score_to_risk_level(20)
        assert level == RiskLevel.LOW
    
    def test_score_to_risk_level_critical(self):
        """Test score to risk level conversion - critical"""
        level = RiskScoringService.score_to_risk_level(90)
        assert level == RiskLevel.CRITICAL
    
    def test_generate_risk_signals_price_spike(self):
        """Test risk signal generation for price spike"""
        trend = PriceTrend(
            item_id="TEST-001",
            item_name="Test Item",
            period=AnalysisPeriod.MONTHLY,
            direction=TrendDirection.UPWARD,
            current_price=120,
            previous_price=100,
            price_change_percent=20.0,
            moving_average_7d=105,
            moving_average_30d=102,
            volatility=5,
            min_price=100,
            max_price=120,
            forecasted_price=125,
            forecast_confidence=0.85,
            data_points=30
        )
        
        signals = RiskScoringService.generate_risk_signals("TEST-001", trend)
        assert len(signals) > 0
        assert any(s.signal_type == AlertType.PRICE_SPIKE for s in signals)


class TestSupplierAnalyticsService:
    """Tests for supplier performance analytics"""
    
    def test_calculate_overall_score_weighted(self):
        """Test weighted overall score calculation"""
        score = SupplierAnalyticsService.calculate_overall_score(
            on_time_delivery=100,
            quality_score=100,
            price_competitiveness=100,
            responsiveness=100
        )
        assert score == 100.0
        
        score = SupplierAnalyticsService.calculate_overall_score(
            on_time_delivery=80,
            quality_score=80,
            price_competitiveness=80,
            responsiveness=80
        )
        assert score == 80.0
    
    def test_score_to_health_status_excellent(self):
        """Test score to health status - excellent"""
        status = SupplierAnalyticsService.score_to_health_status(92)
        assert status == SupplierHealthStatus.EXCELLENT
    
    def test_score_to_health_status_critical(self):
        """Test score to health status - critical"""
        status = SupplierAnalyticsService.score_to_health_status(40)
        assert status == SupplierHealthStatus.CRITICAL
    
    def test_identify_risk_factors_below_benchmark(self):
        """Test risk factor identification"""
        performance = {
            "on_time_delivery": 80,
            "quality_score": 75,
            "price_competitiveness": 70,
            "responsiveness": 85
        }
        benchmarks = {
            "on_time_delivery": 95,
            "quality_score": 90,
            "price_competitiveness": 85,
            "responsiveness": 85
        }
        
        risk_factors = SupplierAnalyticsService.identify_risk_factors(performance, benchmarks)
        assert len(risk_factors) > 0
        assert "delivery" in risk_factors[0].lower()
    
    def test_analyze_supplier_comprehensive(self):
        """Test comprehensive supplier analysis"""
        metrics = {
            "name": "Test Supplier",
            "on_time_delivery": 90,
            "quality_score": 85,
            "price_competitiveness": 80,
            "responsiveness": 88
        }
        
        analysis = SupplierAnalyticsService.analyze_supplier("SUPP-001", "Test Supplier", metrics)
        
        assert "overall_score" in analysis
        assert "health_status" in analysis
        assert "risk_factors" in analysis
        assert isinstance(analysis["overall_score"], float)
        assert isinstance(analysis["health_status"], SupplierHealthStatus)


class TestAnomalyDetectionService:
    """Tests for anomaly detection algorithms"""
    
    def test_detect_price_anomalies_with_outliers(self):
        """Test anomaly detection with clear outliers"""
        prices = [100, 101, 102, 103, 200, 104, 105]  # 200 is anomaly
        anomalies = AnomalyDetectionService.detect_price_anomalies(prices, threshold_std_dev=2)
        
        assert len(anomalies) > 0
        # Index 4 (200) should be detected
        indices = [a[0] for a in anomalies]
        assert 4 in indices
    
    def test_detect_price_anomalies_no_outliers(self):
        """Test anomaly detection with normal prices"""
        prices = [100, 101, 99, 102, 100, 101]
        anomalies = AnomalyDetectionService.detect_price_anomalies(prices, threshold_std_dev=2.5)
        
        assert len(anomalies) == 0
    
    def test_detect_trend_breaks_significant_change(self):
        """Test trend break detection with significant change"""
        # First half: stable around 100, second half: stable around 150
        prices = [100, 101, 99, 100, 150, 151, 149, 150]
        breaks = AnomalyDetectionService.detect_trend_breaks(prices, window=2)
        
        assert len(breaks) > 0


class TestSignalsService:
    """Integration tests for main signals service"""
    
    def setup_method(self):
        """Clear signals service before each test"""
        SignalsService.clear_all()
    
    def test_add_and_retrieve_price_point(self):
        """Test adding and retrieving price points"""
        point = PricePoint(
            timestamp=datetime.utcnow(),
            price=100.0,
            quantity=10,
            supplier_id="SUPP-001",
            document_id="DOC-001",
            confidence=0.95
        )
        
        SignalsService.add_price_point("ITEM-001", point)
        assert "ITEM-001" in SignalsService._price_history
        assert len(SignalsService._price_history["ITEM-001"]) == 1
    
    def test_get_price_trend(self):
        """Test retrieving price trend"""
        # Add multiple price points
        for i in range(10):
            point = PricePoint(
                timestamp=datetime.utcnow() - timedelta(days=10-i),
                price=100 + (i * 2),
                quantity=10,
                supplier_id="SUPP-001",
                document_id=f"DOC-{i}",
                confidence=0.95
            )
            SignalsService.add_price_point("ITEM-001", point)
        
        trend = SignalsService.get_price_trend("ITEM-001", days_back=30)
        assert trend is not None
        assert trend.item_id == "ITEM-001"
        assert trend.direction in [TrendDirection.UPWARD, TrendDirection.DOWNWARD, TrendDirection.STABLE, TrendDirection.VOLATILE]
    
    def test_get_price_trend_no_data(self):
        """Test retrieving trend for non-existent item"""
        trend = SignalsService.get_price_trend("NONEXISTENT", days_back=30)
        assert trend is None
    
    def test_create_and_retrieve_alert(self):
        """Test creating and retrieving risk alert"""
        signal = RiskSignal(
            signal_type=AlertType.PRICE_SPIKE,
            severity=RiskLevel.HIGH,
            score=75,
            title="Price Spike Detected",
            description="Item price increased significantly",
            impact="Budget impact",
            recommendation="Review pricing"
        )
        
        alert_id = SignalsService.create_risk_alert("ITEM-001", RiskLevel.HIGH, [signal])
        
        assert alert_id in SignalsService._risk_alerts
        alerts = SignalsService.get_risk_alerts(RiskLevel.HIGH)
        assert len(alerts) > 0
    
    def test_supplier_metrics_storage(self):
        """Test supplier metrics storage and retrieval"""
        metrics = {
            "name": "Test Supplier",
            "on_time_delivery": 92,
            "quality_score": 88,
            "price_competitiveness": 85,
            "responsiveness": 90
        }
        
        SignalsService.add_supplier_metrics("SUPP-001", metrics)
        perf = SignalsService.get_supplier_performance("SUPP-001")
        
        assert perf is not None
        assert perf.supplier_id == "SUPP-001"
        assert perf.overall_score > 0


class TestSignalsModels:
    """Tests for Pydantic models"""
    
    def test_price_point_model(self):
        """Test PricePoint model validation"""
        point = PricePoint(
            timestamp=datetime.utcnow(),
            price=100.0,
            quantity=10,
            supplier_id="SUPP-001",
            document_id="DOC-001",
            confidence=0.95
        )
        assert point.price > 0
        assert point.confidence <= 1.0
    
    def test_risk_signal_model(self):
        """Test RiskSignal model validation"""
        signal = RiskSignal(
            signal_type=AlertType.PRICE_SPIKE,
            severity=RiskLevel.HIGH,
            score=75,
            title="Test",
            description="Test signal",
            impact="Test impact",
            recommendation="Test recommendation"
        )
        assert signal.score >= 0
        assert signal.score <= 100
    
    def test_price_trend_model(self):
        """Test PriceTrend model validation"""
        trend = PriceTrend(
            item_id="ITEM-001",
            item_name="Test Item",
            period=AnalysisPeriod.MONTHLY,
            direction=TrendDirection.UPWARD,
            current_price=110,
            previous_price=100,
            price_change_percent=10,
            moving_average_7d=105,
            moving_average_30d=102,
            volatility=5,
            min_price=100,
            max_price=120,
            forecasted_price=115,
            forecast_confidence=0.85,
            data_points=30
        )
        assert trend.forecast_confidence <= 1.0


if __name__ == "__main__":
    # Run tests with: pytest test_signals.py -v
    pytest.main([__file__, "-v"])
