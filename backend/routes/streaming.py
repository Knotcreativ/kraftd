"""
Phase 7: Real-Time Streaming WebSocket Routes

Provides 6 WebSocket endpoints for real-time streaming of:
- Price updates
- Risk alerts
- Supplier signals
- Anomaly detection
- Trend changes
- Health checks
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from typing import Optional, Dict, Any, Tuple
import logging
import asyncio
import json
from datetime import datetime

from models.streaming import (
    SubscriptionRequest,
    UnsubscriptionRequest,
    AcknowledgeAlertRequest,
    PriceUpdate,
    RiskAlert,
    SupplierSignal,
    AnomalyDetected,
    TrendChange,
    HealthCheck
)
from models.user import UserRole
from services.event_broadcaster import broadcaster
from services.auth_service import AuthService
from services.rbac_service import RBACService, Permission
from middleware.rbac import require_authenticated

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ws", tags=["websocket-streaming"])

auth_service = AuthService()
rbac_service = RBACService()


# ============= UTILITY FUNCTIONS =============

async def verify_websocket_token(token: Optional[str]) -> Tuple[str, UserRole]:
    """
    Extract user email and role from Bearer token for WebSocket.
    
    Args:
        token: Bearer token from query parameter
        
    Returns:
        Tuple of (email, role)
        
    Raises:
        ValueError: If token is invalid or missing
    """
    if not token:
        raise ValueError("Missing token in query parameter")
    
    try:
        # Extract token from "Bearer <token>" format if present
        if token.startswith("Bearer "):
            token = token.replace("Bearer ", "")
        
        # Verify token using AuthService
        payload = auth_service.verify_token(token)
        email = payload.get("email") or payload.get("sub")
        
        # Get user role (for now, default to USER if not in token)
        # In production, would fetch from database
        role_str = payload.get("role", "USER")
        role = UserRole[role_str.upper()] if role_str else UserRole.USER
        
        return email, role
        
    except Exception as e:
        logger.warning(f"WebSocket token verification failed: {e}")
        raise ValueError(f"Invalid token: {str(e)}")


async def get_current_user_from_token(token: str) -> Optional[str]:
    """
    Legacy function for backward compatibility.
    Extract user email from Bearer token.
    """
    try:
        email, role = await verify_websocket_token(token)
        return email
    except ValueError:
        return None


# ============= WEBSOCKET ENDPOINTS =============

@router.websocket("/alerts")
async def websocket_alerts(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
) -> None:
    """
    WebSocket endpoint for risk alerts
    
    Query Parameters:
    - token: Bearer token for authentication (can be "Bearer <token>" or just "<token>")
    
    Clients can subscribe to:
    - By risk level: CRITICAL, HIGH, MEDIUM, LOW
    - By alert type: PRICE_VOLATILITY, SUPPLIER_RISK, etc.
    
    Subscribe message:
    {
        "action": "subscribe",
        "filters": {
            "risk_level": ["CRITICAL", "HIGH"],
            "alert_type": ["PRICE_VOLATILITY"]
        }
    }
    """
    
    # Authenticate with RBAC
    try:
        email, role = await verify_websocket_token(token)
    except ValueError as e:
        await websocket.close(code=4001, reason=f"Unauthorized: {str(e)}")
        logger.warning(f"WebSocket /alerts connection rejected: {str(e)}")
        return
    
    # Check permission to subscribe to alerts
    if not rbac_service.has_permission(role, Permission.ALERTS_READ):
        await websocket.close(code=4003, reason="Forbidden: Insufficient permissions")
        logger.warning(f"User {email} (role: {role}) denied access to /ws/alerts - missing ALERTS_READ permission")
        return
    
    # Accept connection
    await websocket.accept()
    client = broadcaster.register_client(websocket, email)
    
    if not client:
        await websocket.close(code=4029, reason="Connection limit reached")
        return
    
    logger.info(f"User {email} (role: {role}) connected to /ws/alerts")
    
    # Log authorization decision
    rbac_service.log_authorization_decision(
        user_email=email,
        user_role=role,
        resource="websocket",
        resource_id="alerts",
        action="subscribe",
        allowed=True
    )
    
    try:
        # Message loop
        while True:
            data = await client.receive_message()
            if not data:
                break
            
            # Parse subscription request
            try:
                req = SubscriptionRequest(**data)
            except Exception as e:
                logger.warning(f"Invalid message from {client.client_id}: {e}")
                await client.send_event({
                    "type": "error",
                    "message": "Invalid message format",
                    "details": str(e)
                })
                continue
            
            # Handle actions
            if req.action == "subscribe":
                broadcaster.subscribe(
                    client.client_id,
                    "alerts",
                    filters=req.filters
                )
                await client.send_event({
                    "type": "subscription_confirmed",
                    "topic": "alerts",
                    "filters": req.filters
                })
            
            elif req.action == "unsubscribe":
                broadcaster.unsubscribe(client.client_id, "alerts")
                await client.send_event({
                    "type": "unsubscription_confirmed",
                    "topic": "alerts"
                })
    
    except WebSocketDisconnect:
        logger.info(f"Client {client.client_id} disconnected from /ws/alerts")
    
    except Exception as e:
        logger.error(f"Error in /ws/alerts for {client.client_id}: {e}")
    
    finally:
        broadcaster.unregister_client(client.client_id)


@router.websocket("/prices")
async def websocket_prices(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
) -> None:
    """
    WebSocket endpoint for real-time price updates
    
    Subscribe message:
    {
        "action": "subscribe",
        "items": ["COPPER", "STEEL"],
        "interval": "1s"
    }
    """
    
    # Authenticate and verify permissions
    try:
        email, role = await verify_websocket_token(token)
    except ValueError as e:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    # Check RBAC permissions
    if not rbac_service.has_permission(role, Permission.PRICES_READ):
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource="websocket",
            resource_id="prices",
            action="subscribe",
            allowed=False
        )
        await websocket.close(code=4003, reason="Forbidden")
        return
    
    await websocket.accept()
    client = broadcaster.register_client(websocket, email)
    
    if not client:
        await websocket.close(code=4029, reason="Connection limit reached")
        return
    
    rbac_service.log_authorization_decision(
        user_email=email,
        user_role=role,
        resource="websocket",
        resource_id="prices",
        action="subscribe",
        allowed=True
    )
    
    logger.info(f"Client {client.client_id} connected to /ws/prices")
    
    try:
        while True:
            data = await client.receive_message()
            if not data:
                break
            
            try:
                req = SubscriptionRequest(**data)
            except Exception as e:
                logger.warning(f"Invalid message from {client.client_id}: {e}")
                continue
            
            if req.action == "subscribe":
                broadcaster.subscribe(
                    client.client_id,
                    "prices",
                    filters={"item_id": req.items} if req.items else None
                )
                await client.send_event({
                    "type": "subscription_confirmed",
                    "topic": "prices",
                    "items": req.items
                })
            
            elif req.action == "unsubscribe":
                broadcaster.unsubscribe(client.client_id, "prices")
                await client.send_event({
                    "type": "unsubscription_confirmed",
                    "topic": "prices"
                })
    
    except WebSocketDisconnect:
        logger.info(f"Client {client.client_id} disconnected from /ws/prices")
    
    finally:
        broadcaster.unregister_client(client.client_id)


@router.websocket("/signals")
async def websocket_signals(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
) -> None:
    """
    WebSocket endpoint for supplier performance signals
    
    Subscribe message:
    {
        "action": "subscribe",
        "suppliers": ["SUPPLIER_A"],
        "signal_types": ["HEALTH_CHANGE", "PERFORMANCE_ALERT"]
    }
    """
    
    # Authenticate and verify permissions
    try:
        email, role = await verify_websocket_token(token)
    except ValueError as e:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    # Check RBAC permissions
    if not rbac_service.has_permission(role, Permission.SIGNALS_READ):
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource="websocket",
            resource_id="signals",
            action="subscribe",
            allowed=False
        )
        await websocket.close(code=4003, reason="Forbidden")
        return
    
    await websocket.accept()
    client = broadcaster.register_client(websocket, email)
    
    if not client:
        await websocket.close(code=4029, reason="Connection limit reached")
        return
    
    rbac_service.log_authorization_decision(
        user_email=email,
        user_role=role,
        resource="websocket",
        resource_id="signals",
        action="subscribe",
        allowed=True
    )
    
    logger.info(f"Client {client.client_id} connected to /ws/signals")
    
    try:
        while True:
            data = await client.receive_message()
            if not data:
                break
            
            try:
                req = SubscriptionRequest(**data)
            except Exception as e:
                logger.warning(f"Invalid message from {client.client_id}: {e}")
                continue
            
            if req.action == "subscribe":
                broadcaster.subscribe(
                    client.client_id,
                    "signals",
                    filters={"supplier_id": req.suppliers} if req.suppliers else None
                )
                await client.send_event({
                    "type": "subscription_confirmed",
                    "topic": "signals",
                    "suppliers": req.suppliers
                })
            
            elif req.action == "unsubscribe":
                broadcaster.unsubscribe(client.client_id, "signals")
                await client.send_event({
                    "type": "unsubscription_confirmed",
                    "topic": "signals"
                })
    
    except WebSocketDisconnect:
        logger.info(f"Client {client.client_id} disconnected from /ws/signals")
    
    finally:
        broadcaster.unregister_client(client.client_id)


@router.websocket("/anomalies")
async def websocket_anomalies(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
) -> None:
    """
    WebSocket endpoint for anomaly detection alerts
    
    Subscribe message:
    {
        "action": "subscribe",
        "anomaly_types": ["PRICE_ANOMALY", "TREND_BREAK"],
        "sensitivity": "HIGH"
    }
    """
    
    # Authenticate and verify permissions
    try:
        email, role = await verify_websocket_token(token)
    except ValueError as e:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    # Check RBAC permissions
    if not rbac_service.has_permission(role, Permission.ANOMALIES_READ):
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource="websocket",
            resource_id="anomalies",
            action="subscribe",
            allowed=False
        )
        await websocket.close(code=4003, reason="Forbidden")
        return
    
    await websocket.accept()
    client = broadcaster.register_client(websocket, email)
    
    if not client:
        await websocket.close(code=4029, reason="Connection limit reached")
        return
    
    rbac_service.log_authorization_decision(
        user_email=email,
        user_role=role,
        resource="websocket",
        resource_id="anomalies",
        action="subscribe",
        allowed=True
    )
    
    logger.info(f"Client {client.client_id} connected to /ws/anomalies")
    
    try:
        while True:
            data = await client.receive_message()
            if not data:
                break
            
            try:
                req = SubscriptionRequest(**data)
            except Exception as e:
                logger.warning(f"Invalid message from {client.client_id}: {e}")
                continue
            
            if req.action == "subscribe":
                broadcaster.subscribe(
                    client.client_id,
                    "anomalies",
                    filters={
                        "anomaly_type": req.anomaly_types,
                        "sensitivity": req.sensitivity
                    } if req.anomaly_types else None
                )
                await client.send_event({
                    "type": "subscription_confirmed",
                    "topic": "anomalies",
                    "anomaly_types": req.anomaly_types
                })
            
            elif req.action == "unsubscribe":
                broadcaster.unsubscribe(client.client_id, "anomalies")
                await client.send_event({
                    "type": "unsubscription_confirmed",
                    "topic": "anomalies"
                })
    
    except WebSocketDisconnect:
        logger.info(f"Client {client.client_id} disconnected from /ws/anomalies")
    
    finally:
        broadcaster.unregister_client(client.client_id)


@router.websocket("/trends")
async def websocket_trends(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
) -> None:
    """
    WebSocket endpoint for trend change notifications
    
    Subscribe message:
    {
        "action": "subscribe",
        "items": ["COPPER", "STEEL"],
        "notify_on": ["DIRECTION_CHANGE", "STRENGTH_CHANGE"]
    }
    """
    
    # Authenticate and verify permissions
    try:
        email, role = await verify_websocket_token(token)
    except ValueError as e:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    # Check RBAC permissions
    if not rbac_service.has_permission(role, Permission.TRENDS_READ):
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource="websocket",
            resource_id="trends",
            action="subscribe",
            allowed=False
        )
        await websocket.close(code=4003, reason="Forbidden")
        return
    
    await websocket.accept()
    client = broadcaster.register_client(websocket, email)
    
    if not client:
        await websocket.close(code=4029, reason="Connection limit reached")
        return
    
    rbac_service.log_authorization_decision(
        user_email=email,
        user_role=role,
        resource="websocket",
        resource_id="trends",
        action="subscribe",
        allowed=True
    )
    
    logger.info(f"Client {client.client_id} connected to /ws/trends")
    
    try:
        while True:
            data = await client.receive_message()
            if not data:
                break
            
            try:
                req = SubscriptionRequest(**data)
            except Exception as e:
                logger.warning(f"Invalid message from {client.client_id}: {e}")
                continue
            
            if req.action == "subscribe":
                broadcaster.subscribe(
                    client.client_id,
                    "trends",
                    filters={"item_id": req.items} if req.items else None
                )
                await client.send_event({
                    "type": "subscription_confirmed",
                    "topic": "trends",
                    "items": req.items
                })
            
            elif req.action == "unsubscribe":
                broadcaster.unsubscribe(client.client_id, "trends")
                await client.send_event({
                    "type": "unsubscription_confirmed",
                    "topic": "trends"
                })
    
    except WebSocketDisconnect:
        logger.info(f"Client {client.client_id} disconnected from /ws/trends")
    
    finally:
        broadcaster.unregister_client(client.client_id)


@router.websocket("/health")
async def websocket_health(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
) -> None:
    """
    WebSocket endpoint for server health checks and keepalive
    
    Receives periodic health check messages from server.
    Client must respond with pong to keep connection alive.
    """
    
    # Authenticate and verify permissions
    try:
        email, role = await verify_websocket_token(token)
    except ValueError as e:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    # Check RBAC permissions
    if not rbac_service.has_permission(role, Permission.ALERTS_READ):
        rbac_service.log_authorization_decision(
            user_email=email,
            user_role=role,
            resource="websocket",
            resource_id="health",
            action="subscribe",
            allowed=False
        )
        await websocket.close(code=4003, reason="Forbidden")
        return
    
    await websocket.accept()
    client = broadcaster.register_client(websocket, email)
    
    if not client:
        await websocket.close(code=4029, reason="Connection limit reached")
        return
    
    rbac_service.log_authorization_decision(
        user_email=email,
        user_role=role,
        resource="websocket",
        resource_id="health",
        action="subscribe",
        allowed=True
    )
    
    logger.info(f"Client {client.client_id} connected to /ws/health")
    
    try:
        # Subscribe to health topic
        broadcaster.subscribe(client.client_id, "health")
        
        # Send initial health check
        stats = broadcaster.get_stats()
        await client.send_event({
            "type": "health_check",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "HEALTHY",
            "active_connections": stats["active_connections"],
            "messages_sent_total": stats["messages_sent_total"],
            "errors_last_minute": stats["errors_last_minute"],
            "avg_latency_ms": 45.2
        })
        
        # Send health checks every 30 seconds
        while True:
            # Wait for message or timeout
            try:
                data = await asyncio.wait_for(client.receive_message(), timeout=30.0)
                if not data:
                    break
                
                # Client sent pong or other message - just acknowledge
                logger.debug(f"Health check response from {client.client_id}")
            
            except asyncio.TimeoutError:
                # Time to send health check
                stats = broadcaster.get_stats()
                await client.send_event({
                    "type": "health_check",
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "HEALTHY",
                    "active_connections": stats["active_connections"],
                    "messages_sent_total": stats["messages_sent_total"],
                    "errors_last_minute": stats["errors_last_minute"],
                    "avg_latency_ms": 45.2
                })
    
    except WebSocketDisconnect:
        logger.info(f"Client {client.client_id} disconnected from /ws/health")
    
    except Exception as e:
        logger.error(f"Error in /ws/health for {client.client_id}: {e}")
    
    finally:
        broadcaster.unregister_client(client.client_id)


# ============= MANAGEMENT ENDPOINTS (HTTP REST) =============

@router.get("/stats")
async def get_stats(token: str = Query(...)) -> dict:
    """Get WebSocket server statistics"""
    user_id = await get_current_user_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return broadcaster.get_stats()


@router.get("/clients/stats")
async def get_clients_stats(token: str = Query(...)) -> list:
    """Get statistics for all connected clients"""
    user_id = await get_current_user_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return broadcaster.get_clients_stats()


@router.post("/cleanup")
async def trigger_cleanup(token: str = Query(...)) -> dict:
    """Manually trigger cleanup of inactive clients"""
    user_id = await get_current_user_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    removed = await broadcaster.cleanup_inactive_clients()
    return {
        "message": f"Cleaned up {removed} inactive clients",
        "removed_count": removed
    }
