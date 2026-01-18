"""Signals Intelligence REST API Routes

Endpoints for price trend analysis, risk alerts, supplier performance, and predictions.
Part of Phase 5: Signals Intelligence layer.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status, Header

from models.signals import (
    TrendListResponse, AlertListResponse, SupplierListResponse,
    TrendQueryRequest, AlertQueryRequest, SupplierQueryRequest, PredictionRequest,
    SignalsErrorResponse, RiskLevel, SupplierHealthStatus, AnalysisPeriod,
    PricePoint, PriceTrend
)
from services.signals_service import (
    SignalsService, TrendAnalysisService, RiskScoringService,
    SupplierAnalyticsService, AnomalyDetectionService
)
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/signals",
    tags=["signals"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing Bearer token"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


# ============================================================================
# Dependency: Verify Bearer Token
# ============================================================================

def verify_bearer_token(authorization: Optional[str] = Header(None)) -> str:
    """Verify Bearer token is present and valid format.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        Bearer token
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected: Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return parts[1]


# ============================================================================
# Price Trend Endpoints
# ============================================================================

@router.get("/trends", response_model=TrendListResponse)
async def get_trends(
    period: AnalysisPeriod = Query(AnalysisPeriod.MONTHLY),
    days_back: int = Query(90, ge=1, le=365),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    auth: str = Depends(verify_bearer_token)
) -> TrendListResponse:
    """
    Get price trends across all items
    
    Query Parameters:
    - period: Analysis period (daily, weekly, monthly, quarterly, yearly)
    - days_back: Number of days to analyze (1-365)
    - skip: Pagination skip
    - limit: Pagination limit (1-100)
    """
    try:
        trends = []
        
        # Get all price histories
        for item_id in SignalsService._price_history.keys():
            trend = SignalsService.get_price_trend(item_id, days_back, period)
            if trend:
                trends.append(trend)
        
        # Sort by volatility (riskiest first)
        trends.sort(key=lambda t: t.volatility, reverse=True)
        
        # Apply pagination
        total = len(trends)
        trends = trends[skip:skip + limit]
        
        return TrendListResponse(
            total_count=total,
            trends=trends,
            period=period,
            generated_at=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Error fetching trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trends"
        )


@router.get("/trends/{item_id}", response_model=PriceTrend)
async def get_item_trend(
    item_id: str = Query(..., min_length=1),
    period: AnalysisPeriod = Query(AnalysisPeriod.MONTHLY),
    days_back: int = Query(90, ge=1, le=365),
    auth: str = Depends(verify_bearer_token)
) -> PriceTrend:
    """
    Get price trend for a specific item
    
    Path Parameters:
    - item_id: Item identifier
    
    Query Parameters:
    - period: Analysis period
    - days_back: Number of days to analyze
    """
    try:
        trend = SignalsService.get_price_trend(item_id, days_back, period)
        
        if not trend:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No price data found for item {item_id}"
            )
        
        return trend
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trend for {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trend"
        )


@router.post("/trends/query", response_model=TrendListResponse)
async def query_trends(
    request: TrendQueryRequest,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    auth: str = Depends(verify_bearer_token)
) -> TrendListResponse:
    """
    Advanced trend query with multiple filters
    
    Request Body:
    - item_ids: List of item IDs to query
    - period: Analysis period
    - supplier_id: Optional supplier filter
    - days_back: Number of days to analyze
    """
    try:
        trends = []
        
        # Query trends for specified items
        for item_id in request.item_ids:
            trend = SignalsService.get_price_trend(
                item_id,
                request.days_back,
                request.period
            )
            if trend:
                # Apply supplier filter if provided
                if request.supplier_id is None:
                    trends.append(trend)
        
        # Sort by volatility
        trends.sort(key=lambda t: t.volatility, reverse=True)
        
        # Apply pagination
        total = len(trends)
        trends = trends[skip:skip + limit]
        
        return TrendListResponse(
            total_count=total,
            trends=trends,
            period=request.period,
            generated_at=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Error querying trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query trends"
        )


# ============================================================================
# Risk Alert Endpoints
# ============================================================================

@router.get("/alerts", response_model=AlertListResponse)
async def get_alerts(
    risk_level: Optional[RiskLevel] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    days_back: int = Query(30, ge=1, le=365),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    auth: str = Depends(verify_bearer_token)
) -> AlertListResponse:
    """
    Get risk alerts with optional filtering
    
    Query Parameters:
    - risk_level: Filter by risk level (low, medium, high, critical)
    - acknowledged: Filter by acknowledgment status
    - days_back: Number of days to retrieve (1-365)
    - skip: Pagination skip
    - limit: Pagination limit
    """
    try:
        # Get all alerts
        all_alerts = SignalsService.get_risk_alerts(risk_level, days_back)
        
        # Apply acknowledged filter
        if acknowledged is not None:
            all_alerts = [a for a in all_alerts if a.acknowledged == acknowledged]
        
        # Sort by risk score (highest first)
        all_alerts.sort(key=lambda a: a.overall_risk_score, reverse=True)
        
        # Apply pagination
        total = len(all_alerts)
        alerts = all_alerts[skip:skip + limit]
        
        return AlertListResponse(
            total_count=total,
            alerts=alerts,
            filters_applied={
                "risk_level": risk_level.value if risk_level else None,
                "acknowledged": acknowledged,
                "days_back": days_back
            },
            generated_at=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Error fetching alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )


@router.get("/alerts/{alert_id}")
async def get_alert_detail(
    alert_id: str = Query(..., min_length=1),
    auth: str = Depends(verify_bearer_token)
):
    """
    Get detailed information about a specific alert
    
    Path Parameters:
    - alert_id: Alert identifier
    """
    try:
        if alert_id not in SignalsService._risk_alerts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )
        
        alert = SignalsService._risk_alerts[alert_id]
        return alert
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching alert {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alert"
        )


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    auth: str = Depends(verify_bearer_token)
):
    """
    Acknowledge a risk alert
    
    Path Parameters:
    - alert_id: Alert identifier to acknowledge
    
    Response:
    - success: Boolean indicating acknowledgment was recorded
    """
    try:
        if alert_id not in SignalsService._risk_alerts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )
        
        alert = SignalsService._risk_alerts[alert_id]
        alert.acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = auth
        
        logger.info(f"Alert {alert_id} acknowledged by {auth}")
        
        return {
            "success": True,
            "alert_id": alert_id,
            "acknowledged_at": alert.acknowledged_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert"
        )


# ============================================================================
# Supplier Performance Endpoints
# ============================================================================

@router.get("/suppliers", response_model=SupplierListResponse)
async def get_suppliers(
    health_status: Optional[SupplierHealthStatus] = Query(None),
    category: Optional[str] = Query(None),
    min_score: float = Query(0, ge=0, le=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    auth: str = Depends(verify_bearer_token)
) -> SupplierListResponse:
    """
    Get supplier performance data with optional filtering
    
    Query Parameters:
    - health_status: Filter by health status (excellent, good, fair, poor, critical)
    - category: Filter by supplier category
    - min_score: Minimum performance score (0-100)
    - skip: Pagination skip
    - limit: Pagination limit
    """
    try:
        suppliers = []
        
        # Get all supplier performances
        for supplier_id in SignalsService._supplier_metrics.keys():
            perf = SignalsService.get_supplier_performance(supplier_id)
            if perf:
                # Apply filters
                if health_status and perf.health_status != health_status:
                    continue
                if perf.overall_score < min_score:
                    continue
                
                suppliers.append(perf)
        
        # Sort by health status criticality and score
        health_order = {
            SupplierHealthStatus.CRITICAL: 0,
            SupplierHealthStatus.POOR: 1,
            SupplierHealthStatus.FAIR: 2,
            SupplierHealthStatus.GOOD: 3,
            SupplierHealthStatus.EXCELLENT: 4
        }
        suppliers.sort(
            key=lambda s: (health_order.get(s.health_status, 5), -s.overall_score)
        )
        
        # Apply pagination
        total = len(suppliers)
        suppliers = suppliers[skip:skip + limit]
        
        return SupplierListResponse(
            total_count=total,
            suppliers=suppliers,
            category=category,
            generated_at=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Error fetching suppliers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve suppliers"
        )


@router.get("/suppliers/{supplier_id}")
async def get_supplier_detail(
    supplier_id: str = Query(..., min_length=1),
    auth: str = Depends(verify_bearer_token)
):
    """
    Get detailed performance analysis for a supplier
    
    Path Parameters:
    - supplier_id: Supplier identifier
    """
    try:
        perf = SignalsService.get_supplier_performance(supplier_id)
        
        if not perf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for supplier {supplier_id}"
            )
        
        return perf
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching supplier {supplier_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve supplier data"
        )


# ============================================================================
# Prediction Endpoints
# ============================================================================

@router.post("/predictions")
async def get_predictions(
    request: PredictionRequest,
    auth: str = Depends(verify_bearer_token)
):
    """
    Get price predictions for an item
    
    Request Body:
    - item_id: Item identifier
    - periods_ahead: Number of periods to forecast (1-12)
    - confidence_level: Confidence level (0.0-1.0)
    
    Response:
    - predictions: List of forecasted prices
    - confidence_interval: Min/max expected price range
    """
    try:
        # Get price history
        if request.item_id not in SignalsService._price_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No price data for item {request.item_id}"
            )
        
        history = SignalsService._price_history[request.item_id]
        prices = [p.price for p in history[-90:]]  # Last 90 days
        
        if len(prices) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient data for prediction"
            )
        
        # Generate forecast
        forecast = TrendAnalysisService.simple_forecast(prices, request.periods_ahead)
        
        if forecast is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to generate forecast"
            )
        
        # Calculate confidence interval
        volatility = TrendAnalysisService.calculate_volatility(prices)
        margin = volatility * 2.0  # 2 standard deviations
        
        return {
            "item_id": request.item_id,
            "periods_ahead": request.periods_ahead,
            "forecasted_price": forecast,
            "confidence_interval_lower": max(0, forecast - margin),
            "confidence_interval_upper": forecast + margin,
            "confidence_level": request.confidence_level,
            "generated_at": datetime.utcnow()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating predictions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate predictions"
        )


@router.post("/anomalies/detect")
async def detect_anomalies(
    item_id: str = Query(..., min_length=1),
    threshold_std_dev: float = Query(2.5, ge=1.0, le=5.0),
    auth: str = Depends(verify_bearer_token)
):
    """
    Detect anomalies in price data
    
    Query Parameters:
    - item_id: Item identifier
    - threshold_std_dev: Standard deviation threshold (1.0-5.0)
    
    Response:
    - anomalies: List of detected anomalies with indexes and deviations
    """
    try:
        if item_id not in SignalsService._price_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No price data for item {item_id}"
            )
        
        history = SignalsService._price_history[item_id]
        prices = [p.price for p in history]
        
        # Detect anomalies
        anomalies = AnomalyDetectionService.detect_price_anomalies(
            prices,
            threshold_std_dev
        )
        
        return {
            "item_id": item_id,
            "total_data_points": len(prices),
            "anomalies_detected": len(anomalies),
            "anomalies": [
                {
                    "index": idx,
                    "deviation_percent": dev,
                    "price": prices[idx]
                }
                for idx, dev in anomalies
            ],
            "generated_at": datetime.utcnow()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect anomalies"
        )


# ============================================================================
# Real-Time Price Ingestion Endpoint (Phase 7 Integration)
# ============================================================================

@router.post("/ingest/price")
async def ingest_real_time_price(
    item_id: str = Query(..., description="Item/Product ID"),
    price: float = Query(..., gt=0, description="Current price"),
    auth: str = Depends(verify_bearer_token)
):
    """
    Ingest a real-time price point and broadcast to connected WebSocket clients
    
    This endpoint:
    1. Adds the price to the item's history
    2. Analyzes the price trend
    3. Detects any risk signals
    4. Broadcasts price update to all connected clients on /ws/prices
    5. Broadcasts risk alerts if thresholds exceeded
    
    Query Parameters:
    - item_id: Item/Product ID (required)
    - price: Current price in dollars (required, > 0)
    
    Returns:
        Ingestion confirmation with broadcast details
    """
    try:
        from models.signals import PricePoint
        from services.signals_broadcaster_bridge import SignalsBroadcasterBridge
        
        # Record the price point
        price_point = PricePoint(
            price=price,
            timestamp=datetime.utcnow(),
            source="api_ingestion"
        )
        SignalsService.add_price_point(item_id, price_point)
        
        # Analyze trend and get historical context
        trend = SignalsService.get_price_trend(item_id, days_back=90)
        
        if not trend:
            # Not enough history yet
            return {
                "status": "ingested",
                "item_id": item_id,
                "price": price,
                "message": "Price recorded. Insufficient history for trend analysis.",
                "broadcasts_sent": 0,
                "timestamp": datetime.utcnow()
            }
        
        # Broadcast price update
        price_broadcasted = await SignalsBroadcasterBridge.broadcast_price_update(
            item_id=item_id,
            current_price=price,
            previous_price=trend.previous_price,
            trend=trend,
            volatility=trend.volatility,
            moving_avg_30=trend.moving_avg_30,
            moving_avg_90=trend.moving_avg_90
        )
        
        broadcasts_sent = 1 if price_broadcasted else 0
        
        # Check for risk signals and broadcast alerts
        risk_signals = RiskScoringService.generate_risk_signals(item_id, trend)
        
        for signal in risk_signals:
            alert_broadcasted = await SignalsBroadcasterBridge.broadcast_risk_alert(
                item_id=item_id,
                signal=signal
            )
            if alert_broadcasted:
                broadcasts_sent += 1
        
        # Detect anomalies
        prices = [pp.price for pp in SignalsService._price_history.get(item_id, [])]
        anomalies = AnomalyDetectionService.detect_price_anomalies(prices)
        
        for idx, deviation in anomalies:
            anomaly_broadcasted = await SignalsBroadcasterBridge.broadcast_anomaly_detected(
                item_id=item_id,
                anomaly_type="PRICE_SPIKE",
                current_value=price,
                expected_value=trend.moving_avg_90 or trend.previous_price,
                deviation_percent=deviation,
                z_score=2.5 if deviation > 10 else 1.5,
                severity="HIGH" if deviation > 20 else "MEDIUM"
            )
            if anomaly_broadcasted:
                broadcasts_sent += 1
        
        return {
            "status": "ingested_and_broadcast",
            "item_id": item_id,
            "price": price,
            "price_change_percent": trend.price_change_percent,
            "trend_direction": trend.direction.value,
            "broadcasts_sent": broadcasts_sent,
            "risk_signals_detected": len(risk_signals),
            "anomalies_detected": len(anomalies),
            "timestamp": datetime.utcnow()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting real-time price: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest real-time price"
        )


# ============================================================================
# Health Check Endpoint
# ============================================================================

@router.get("/health")
async def signals_health():
    """Health check for signals service"""
    return {
        "status": "healthy",
        "service": "signals-intelligence",
        "timestamp": datetime.utcnow()
    }
