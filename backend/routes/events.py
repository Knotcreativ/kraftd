"""
Historical Events REST API Routes

Endpoints:
- GET /api/v1/events/prices - Get historical price data
- GET /api/v1/events/alerts - Get historical alert data
- GET /api/v1/events/anomalies - Get historical anomaly data
- GET /api/v1/events/signals - Get historical supplier signal data
- GET /api/v1/events/trends - Get historical trend data
- GET /api/v1/events/stats - Get event statistics
- GET /api/v1/events/aggregate - Get aggregated event data for charts
"""

from fastapi import APIRouter, Query, Depends, HTTPException, status
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from pydantic import BaseModel, Field
import logging

from services.event_storage import EventStorageService, EventType, get_event_storage_service
from models.user import UserRole
from services.rbac_service import RBACService, Permission
from middleware.rbac import require_authenticated
from services.tenant_service import TenantService
from utils.query_scope import QueryScope

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/events",
    tags=["events"]
)


# ============================================================================
# Response Models
# ============================================================================

class EventQueryResponse(BaseModel):
    """Response model for event queries"""
    results: List[dict] = Field(default=[], description="List of events")
    total: int = Field(description="Total number of matching events")
    limit: int = Field(description="Requested limit")
    offset: int = Field(description="Requested offset")
    query_info: Optional[dict] = Field(default=None, description="Query parameters used")


class EventStatsResponse(BaseModel):
    """Response model for event statistics"""
    price: int = Field(description="Total price events")
    alert: int = Field(description="Total alert events")
    anomaly: int = Field(description="Total anomaly events")
    signal: int = Field(description="Total supplier signal events")
    trend: int = Field(description="Total trend events")
    date_range: Optional[dict] = Field(default=None, description="Query date range")


class AggregatedEventResponse(BaseModel):
    """Response model for aggregated events"""
    results: List[dict] = Field(default=[], description="Aggregated data points")
    group_by: str = Field(description="Grouping period (day, week, month, hour)")
    total_points: int = Field(description="Total aggregated points")


# ============================================================================
# Query Parameters
# ============================================================================

def get_date_range(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
) -> tuple:
    """Validate and return date range"""
    # Default to last 30 days if not specified
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    try:
        # Validate date format
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    return start_date, end_date


def get_pagination(
    limit: int = Query(100, ge=1, le=1000, description="Results per page"),
    offset: int = Query(0, ge=0, description="Results to skip")
) -> tuple:
    """Validate pagination parameters"""
    return limit, offset


# ============================================================================
# Price Events
# ============================================================================

@router.get(
    "/prices",
    response_model=EventQueryResponse,
    summary="Get historical price data",
    description="Retrieve historical commodity price events with optional filters (scoped to current tenant)"
)
async def get_price_events(
    item_id: Optional[str] = Query(None, description="Filter by item ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Tuple[str, UserRole] = Depends(require_authenticated()),
    storage: EventStorageService = Depends(get_event_storage_service)
):
    """
    Get historical price events for current tenant

    **Filters:**
    - item_id: Specific commodity item
    - start_date: Filter by date range start
    - end_date: Filter by date range end

    **Pagination:**
    - limit: 1-1000 results per page (default: 100)
    - offset: Results to skip (default: 0)

    **Security:** Results are automatically scoped to current tenant.
    
    **Returns:** List of price events with metadata
    """
    try:
        email, role = current_user
        
        # Get current tenant context for scoping
        try:
            current_tenant = TenantService.get_current_tenant()
            if not current_tenant:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tenant context found"
                )
        except Exception as e:
            logger.error(f"Error getting tenant context: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Failed to retrieve tenant context"
            )
        
        logger.info(f"User {email} (role: {role}, tenant: {current_tenant}) querying price events")
        
        # Get and validate dates
        if not start_date or not end_date:
            dates = get_date_range(start_date, end_date)
            start_date, end_date = dates

        # Query events with tenant scoping
        result = await storage.query_events(
            event_type=EventType.PRICE,
            tenant_id=current_tenant,
            start_date=start_date,
            end_date=end_date,
            item_id=item_id,
            limit=limit,
            offset=offset
        )

        return EventQueryResponse(
            results=result.get("results", []),
            total=result.get("total", 0),
            limit=limit,
            offset=offset,
            query_info={
                "item_id": item_id,
                "start_date": start_date,
                "end_date": end_date,
                "tenant_id": current_tenant
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get price events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price events"
        )


# ============================================================================
# Alert Events
# ============================================================================

@router.get(
    "/alerts",
    response_model=EventQueryResponse,
    summary="Get historical alert data",
    description="Retrieve historical risk alert events with optional filters"
)
async def get_alert_events(
    item_id: Optional[str] = Query(None, description="Filter by item ID"),
    supplier_id: Optional[str] = Query(None, description="Filter by supplier ID"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (CRITICAL, HIGH, MEDIUM, LOW)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Tuple[str, UserRole] = Depends(require_authenticated()),
    storage: EventStorageService = Depends(get_event_storage_service)
):
    """
    Get historical alert events

    **Filters:**
    - item_id: Specific commodity item
    - supplier_id: Specific supplier
    - risk_level: Alert severity (CRITICAL, HIGH, MEDIUM, LOW)
    - start_date: Filter by date range start
    - end_date: Filter by date range end

    **Returns:** List of alert events with metadata
    """
    try:
        email, role = current_user
        
        # Get current tenant context for scoping
        try:
            current_tenant = TenantService.get_current_tenant()
            if not current_tenant:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tenant context found"
                )
        except Exception as e:
            logger.error(f"Error getting tenant context: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Failed to retrieve tenant context"
            )
        
        logger.info(f"User {email} (role: {role}, tenant: {current_tenant}) querying alert events")
        
        if not start_date or not end_date:
            dates = get_date_range(start_date, end_date)
            start_date, end_date = dates

        result = await storage.query_events(
            event_type=EventType.ALERT,
            tenant_id=current_tenant,
            start_date=start_date,
            end_date=end_date,
            item_id=item_id,
            supplier_id=supplier_id,
            risk_level=risk_level,
            limit=limit,
            offset=offset
        )

        return EventQueryResponse(
            results=result.get("results", []),
            total=result.get("total", 0),
            limit=limit,
            offset=offset,
            query_info={
                "item_id": item_id,
                "supplier_id": supplier_id,
                "risk_level": risk_level,
                "start_date": start_date,
                "end_date": end_date,
                "tenant_id": current_tenant
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alert events"
        )


# ============================================================================
# Anomaly Events
# ============================================================================

@router.get(
    "/anomalies",
    response_model=EventQueryResponse,
    summary="Get historical anomaly data",
    description="Retrieve historical anomaly events with optional filters"
)
async def get_anomaly_events(
    item_id: Optional[str] = Query(None, description="Filter by item ID"),
    supplier_id: Optional[str] = Query(None, description="Filter by supplier ID"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Tuple[str, UserRole] = Depends(require_authenticated()),
    storage: EventStorageService = Depends(get_event_storage_service)
):
    """
    Get historical anomaly events

    **Filters:**
    - item_id: Specific commodity item
    - supplier_id: Specific supplier
    - severity: Anomaly severity (CRITICAL, HIGH, MEDIUM, LOW)
    - start_date: Filter by date range start
    - end_date: Filter by date range end

    **Returns:** List of anomaly events with Z-scores and severity
    """
    try:
        email, role = current_user
        
        # Get current tenant context for scoping
        try:
            current_tenant = TenantService.get_current_tenant()
            if not current_tenant:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tenant context found"
                )
        except Exception as e:
            logger.error(f"Error getting tenant context: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Failed to retrieve tenant context"
            )
        
        logger.info(f"User {email} (role: {role}, tenant: {current_tenant}) querying anomaly events")
        
        if not start_date or not end_date:
            dates = get_date_range(start_date, end_date)
            start_date, end_date = dates

        result = await storage.query_events(
            event_type=EventType.ANOMALY,
            tenant_id=current_tenant,
            start_date=start_date,
            end_date=end_date,
            item_id=item_id,
            supplier_id=supplier_id,
            severity=severity,
            limit=limit,
            offset=offset
        )

        return EventQueryResponse(
            results=result.get("results", []),
            total=result.get("total", 0),
            limit=limit,
            offset=offset,
            query_info={
                "item_id": item_id,
                "supplier_id": supplier_id,
                "severity": severity,
                "start_date": start_date,
                "end_date": end_date,
                "tenant_id": current_tenant
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get anomaly events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve anomaly events"
        )


# ============================================================================
# Supplier Signal Events
# ============================================================================

@router.get(
    "/signals",
    response_model=EventQueryResponse,
    summary="Get historical supplier signal data",
    description="Retrieve historical supplier signal events with optional filters"
)
async def get_signal_events(
    supplier_id: Optional[str] = Query(None, description="Filter by supplier ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Tuple[str, UserRole] = Depends(require_authenticated()),
    storage: EventStorageService = Depends(get_event_storage_service)
):
    """
    Get historical supplier signal events

    **Filters:**
    - supplier_id: Specific supplier
    - start_date: Filter by date range start
    - end_date: Filter by date range end

    **Returns:** List of supplier signal events with value changes
    """
    try:
        email, role = current_user
        logger.info(f"User {email} (role: {role}) querying supplier signals")
        
        # Get current tenant context for scoping
        try:
            current_tenant = TenantService.get_current_tenant()
            if not current_tenant:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tenant context found"
                )
        except Exception as e:
            logger.error(f"Error getting tenant context: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Failed to retrieve tenant context"
            )
        
        logger.info(f"User {email} (role: {role}, tenant: {current_tenant}) querying supplier signals")
        
        if not start_date or not end_date:
            dates = get_date_range(start_date, end_date)
            start_date, end_date = dates

        result = await storage.query_events(
            event_type=EventType.SIGNAL,
            tenant_id=current_tenant,
            start_date=start_date,
            end_date=end_date,
            supplier_id=supplier_id,
            limit=limit,
            offset=offset
        )

        return EventQueryResponse(
            results=result.get("results", []),
            total=result.get("total", 0),
            limit=limit,
            offset=offset,
            query_info={
                "supplier_id": supplier_id,
                "start_date": start_date,
                "end_date": end_date,
                "tenant_id": current_tenant
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get signal events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve signal events"
        )


# ============================================================================
# Trend Events
# ============================================================================

@router.get(
    "/trends",
    response_model=EventQueryResponse,
    summary="Get historical trend data",
    description="Retrieve historical trend events with optional filters"
)
async def get_trend_events(
    item_id: Optional[str] = Query(None, description="Filter by item ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Tuple[str, UserRole] = Depends(require_authenticated()),
    storage: EventStorageService = Depends(get_event_storage_service)
):
    """
    Get historical trend events

    **Filters:**
    - item_id: Specific commodity item
    - start_date: Filter by date range start
    - end_date: Filter by date range end

    **Returns:** List of trend events with direction and confidence
    """
    try:
        email, role = current_user
        
        # Get current tenant context for scoping
        try:
            current_tenant = TenantService.get_current_tenant()
            if not current_tenant:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tenant context found"
                )
        except Exception as e:
            logger.error(f"Error getting tenant context: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Failed to retrieve tenant context"
            )
        
        logger.info(f"User {email} (role: {role}, tenant: {current_tenant}) querying trend events")
        
        if not start_date or not end_date:
            dates = get_date_range(start_date, end_date)
            start_date, end_date = dates

        result = await storage.query_events(
            event_type=EventType.TREND,
            tenant_id=current_tenant,
            start_date=start_date,
            end_date=end_date,
            item_id=item_id,
            limit=limit,
            offset=offset
        )

        return EventQueryResponse(
            results=result.get("results", []),
            total=result.get("total", 0),
            limit=limit,
            offset=offset,
            query_info={
                "item_id": item_id,
                "start_date": start_date,
                "end_date": end_date,
                "tenant_id": current_tenant
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trend events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trend events"
        )


# ============================================================================
# Statistics & Aggregation
# ============================================================================

@router.get(
    "/stats",
    response_model=EventStatsResponse,
    summary="Get event statistics",
    description="Get total event counts by type for a date range"
)
async def get_event_stats(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: Tuple[str, UserRole] = Depends(require_authenticated()),
    storage: EventStorageService = Depends(get_event_storage_service)
):
    """
    Get event statistics

    Returns total counts for each event type in the specified date range
    """
    try:
        email, role = current_user
        
        # Get current tenant context for scoping
        try:
            current_tenant = TenantService.get_current_tenant()
            if not current_tenant:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tenant context found"
                )
        except Exception as e:
            logger.error(f"Error getting tenant context: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Failed to retrieve tenant context"
            )
        
        logger.info(f"User {email} (role: {role}, tenant: {current_tenant}) querying event statistics")
        
        if not start_date or not end_date:
            dates = get_date_range(start_date, end_date)
            start_date, end_date = dates

        stats = await storage.get_event_stats(start_date, end_date, tenant_id=current_tenant)

        return EventStatsResponse(
            price=stats.get("price", 0),
            alert=stats.get("alert", 0),
            anomaly=stats.get("anomaly", 0),
            signal=stats.get("signal", 0),
            trend=stats.get("trend", 0),
            date_range={
                "start_date": start_date,
                "end_date": end_date
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get event stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event statistics"
        )


@router.get(
    "/aggregate/{event_type}",
    response_model=AggregatedEventResponse,
    summary="Get aggregated event data",
    description="Get aggregated events for charting (grouped by period)"
)
async def get_aggregated_events(
    event_type: str = Query(..., description="Event type (price, alert, anomaly, signal, trend)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    group_by: str = Query("day", description="Grouping period (day, week, month, hour)"),
    item_id: Optional[str] = Query(None, description="Filter by item ID"),
    supplier_id: Optional[str] = Query(None, description="Filter by supplier ID"),
    current_user: Tuple[str, UserRole] = Depends(require_authenticated()),
    storage: EventStorageService = Depends(get_event_storage_service)
):
    """
    Get aggregated event data for charting

    **Grouping:**
    - day: Group by calendar day
    - week: Group by ISO week
    - month: Group by calendar month
    - hour: Group by hour

    **Returns:** Aggregated data points with counts, averages, etc.
    """
    try:
        email, role = current_user
        
        # Get current tenant context for scoping
        try:
            current_tenant = TenantService.get_current_tenant()
            if not current_tenant:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tenant context found"
                )
        except Exception as e:
            logger.error(f"Error getting tenant context: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Failed to retrieve tenant context"
            )
        
        logger.info(f"User {email} (role: {role}, tenant: {current_tenant}) querying aggregated {event_type} events")
        
        # Validate event type
        try:
            event_enum = EventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type. Must be one of: {', '.join([e.value for e in EventType])}"
            )

        if not start_date or not end_date:
            dates = get_date_range(start_date, end_date)
            start_date, end_date = dates

        results = await storage.aggregate_events(
            event_type=event_enum,
            tenant_id=current_tenant,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by,
            item_id=item_id,
            supplier_id=supplier_id
        )

        return AggregatedEventResponse(
            results=results,
            group_by=group_by,
            total_points=len(results)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get aggregated events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve aggregated events"
        )


