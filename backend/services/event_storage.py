"""
Event Storage Service - Persists WebSocket events to Cosmos DB

Handles:
- Writing events asynchronously to Cosmos DB
- Querying historical events with filters
- Pagination support
- TTL management
- Error handling and retry logic
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum

from azure.cosmos import CosmosClient, PartitionKey, exceptions
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event type enumeration"""
    PRICE = "price"
    ALERT = "alert"
    ANOMALY = "anomaly"
    SIGNAL = "signal"
    TREND = "trend"


class EventStorageService:
    """Service for persisting and retrieving events from Cosmos DB"""

    # TTL values in seconds (0 = no expiration)
    TTL_DEFAULTS = {
        EventType.PRICE: 180 * 86400,      # 180 days
        EventType.ALERT: 365 * 86400,      # 365 days
        EventType.ANOMALY: 365 * 86400,    # 365 days
        EventType.SIGNAL: 180 * 86400,     # 180 days
        EventType.TREND: 180 * 86400,      # 180 days
    }

    def __init__(self, cosmos_endpoint: str, cosmos_key: str):
        """Initialize Cosmos DB client and containers"""
        try:
            self.client = CosmosClient(cosmos_endpoint, cosmos_key)
            self.database = self.client.get_database_client("KraftdIntel")
            self.events_container = self.database.get_container_client("events")
            self.dashboards_container = self.database.get_container_client("dashboards")
            self.preferences_container = self.database.get_container_client("preferences")
            logger.info("EventStorageService initialized successfully")
        except exceptions.CosmosResourceNotFoundError:
            logger.warning("Cosmos DB containers not found. Event storage disabled.")
            self.events_container = None
            self.dashboards_container = None
            self.preferences_container = None
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB client: {e}")
            self.events_container = None
            self.dashboards_container = None
            self.preferences_container = None

    async def store_event(self, event_data: Dict[str, Any], event_type: EventType) -> Optional[str]:
        """
        Store event to Cosmos DB asynchronously (fire-and-forget)

        Args:
            event_data: Event dictionary with data
            event_type: Type of event (price, alert, anomaly, signal, trend)

        Returns:
            Event ID if stored, None if container not available
        """
        if self.events_container is None:
            return None

        try:
            # Prepare document
            doc = {
                "id": str(uuid.uuid4()),
                "event_type": event_type.value,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "ttl": self.TTL_DEFAULTS.get(event_type, 0),
                **event_data
            }

            # Store asynchronously (don't wait for response)
            asyncio.create_task(self._async_create_item(doc))
            return doc["id"]

        except Exception as e:
            logger.error(f"Failed to prepare event for storage: {e}")
            return None

    async def _async_create_item(self, doc: Dict[str, Any]):
        """Create item in Cosmos DB (async wrapper)"""
        try:
            self.events_container.create_item(body=doc)
        except Exception as e:
            logger.error(f"Failed to store event in Cosmos DB: {e}")

    async def query_events(
        self,
        event_type: EventType,
        tenant_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        item_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        severity: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "DESC"
    ) -> Dict[str, Any]:
        """
        Query events with multiple filters, scoped to tenant

        Args:
            event_type: Type of event to query
            tenant_id: Tenant ID for filtering (required for multi-tenant isolation)
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            item_id: Filter by item_id
            supplier_id: Filter by supplier_id
            severity: Filter by severity (for anomalies)
            risk_level: Filter by risk_level (for alerts)
            limit: Number of results to return (max 1000)
            offset: Number of results to skip (pagination)
            order_by: Sort order (ASC/DESC)

        Returns:
            Dictionary with results and total count, scoped to tenant
        """
        if self.events_container is None:
            return {"results": [], "total": 0, "limit": limit, "offset": offset}

        try:
            # Build query
            where_clauses = [f"c.event_type = '{event_type.value}'"]
            parameters = []

            # Tenant filtering (CRITICAL for multi-tenant isolation)
            if tenant_id:
                where_clauses.append("c.tenant_id = @tenant_id")
                parameters.append(("@tenant_id", tenant_id))

            # Date range filter
            if start_date:
                where_clauses.append("c.date >= @start_date")
                parameters.append(("@start_date", start_date))

            if end_date:
                where_clauses.append("c.date <= @end_date")
                parameters.append(("@end_date", end_date))

            # Item filter
            if item_id:
                where_clauses.append("c.item_id = @item_id")
                parameters.append(("@item_id", item_id))

            # Supplier filter
            if supplier_id:
                where_clauses.append("c.supplier_id = @supplier_id")
                parameters.append(("@supplier_id", supplier_id))

            # Severity filter (for anomalies)
            if severity:
                where_clauses.append("c.severity = @severity")
                parameters.append(("@severity", severity))

            # Risk level filter (for alerts)
            if risk_level:
                where_clauses.append("c.risk_level = @risk_level")
                parameters.append(("@risk_level", risk_level))

            # Build final query
            query = f"SELECT * FROM c WHERE {' AND '.join(where_clauses)} ORDER BY c.timestamp {order_by}"

            # Execute query
            items = list(
                self.events_container.query_items(
                    query=query,
                    parameters=parameters,
                    max_item_count=limit + offset
                )
            )

            # Apply pagination
            total = len(items)
            results = items[offset : offset + limit]

            logger.info(f"Query events: type={event_type.value}, results={len(results)}, total={total}")

            return {
                "results": results,
                "total": total,
                "limit": limit,
                "offset": offset,
                "query_info": {
                    "event_type": event_type.value,
                    "start_date": start_date,
                    "end_date": end_date,
                    "item_id": item_id,
                    "supplier_id": supplier_id,
                    "severity": severity,
                    "risk_level": risk_level,
                }
            }

        except Exception as e:
            logger.error(f"Query events failed: {e}")
            return {"results": [], "total": 0, "limit": limit, "offset": offset, "error": str(e)}

    async def aggregate_events(
        self,
        event_type: EventType,
        start_date: str,
        end_date: str,
        tenant_id: Optional[str] = None,
        group_by: str = "day",  # day, week, month, hour
        item_id: Optional[str] = None,
        supplier_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Aggregate events for charting (count, average, etc), scoped to tenant

        Args:
            event_type: Type of event
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            tenant_id: Tenant ID for filtering (required for multi-tenant isolation)
            group_by: Grouping period (day, week, month, hour)
            item_id: Optional filter by item
            supplier_id: Optional filter by supplier

        Returns:
            List of aggregated results scoped to tenant
        """
        if self.events_container is None:
            return []

        try:
            # Build aggregation query
            where_clauses = [
                f"c.event_type = '{event_type.value}'",
                f"c.date >= '{start_date}'",
                f"c.date <= '{end_date}'"
            ]

            # Tenant filtering (CRITICAL for multi-tenant isolation)
            if tenant_id:
                where_clauses.append(f"c.tenant_id = '{tenant_id}'")

            if item_id:
                where_clauses.append(f"c.item_id = '{item_id}'")

            if supplier_id:
                where_clauses.append(f"c.supplier_id = '{supplier_id}'")

            # Different grouping logic based on event type
            if event_type == EventType.PRICE:
                select = """
                    c.date as date,
                    c.item_id as item_id,
                    AVG(c.price) as avg_price,
                    MIN(c.price) as min_price,
                    MAX(c.price) as max_price,
                    AVG(c.change_percent) as avg_change,
                    COUNT(1) as count
                """
                group = "c.date, c.item_id"
            elif event_type == EventType.ALERT:
                select = """
                    c.date as date,
                    c.risk_level as risk_level,
                    COUNT(1) as count
                """
                group = "c.date, c.risk_level"
            elif event_type == EventType.ANOMALY:
                select = """
                    c.date as date,
                    c.severity as severity,
                    AVG(c.z_score) as avg_z_score,
                    COUNT(1) as count
                """
                group = "c.date, c.severity"
            elif event_type == EventType.SIGNAL:
                select = """
                    c.date as date,
                    c.signal_type as signal_type,
                    COUNT(1) as count
                """
                group = "c.date, c.signal_type"
            elif event_type == EventType.TREND:
                select = """
                    c.date as date,
                    c.trend_direction as trend_direction,
                    AVG(c.confidence) as avg_confidence,
                    COUNT(1) as count
                """
                group = "c.date, c.trend_direction"
            else:
                return []

            query = f"""
                SELECT {select}
                FROM c
                WHERE {' AND '.join(where_clauses)}
                GROUP BY {group}
                ORDER BY c.date DESC
            """

            results = list(self.events_container.query_items(query=query))
            logger.info(f"Aggregated {len(results)} records for {event_type.value}")
            return results

        except Exception as e:
            logger.error(f"Aggregate events failed: {e}")
            return []

    async def get_event_stats(
        self,
        start_date: str,
        end_date: str,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get overall event statistics, scoped to tenant

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            tenant_id: Tenant ID for filtering (required for multi-tenant isolation)

        Returns:
            Dictionary with event counts by type, scoped to tenant
        """
        if self.events_container is None:
            return {}

        try:
            stats = {}

            for event_type in EventType:
                # Build query with tenant filter
                where = f"c.event_type = '{event_type.value}' AND c.date >= '{start_date}' AND c.date <= '{end_date}'"
                if tenant_id:
                    where += f" AND c.tenant_id = '{tenant_id}'"
                
                query = f"""
                    SELECT COUNT(1) as count
                    FROM c
                    WHERE {where}
                """
                result = list(self.events_container.query_items(query=query))
                stats[event_type.value] = result[0]["count"] if result else 0

            logger.info(f"Event stats: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Get event stats failed: {e}")
            return {}

    async def delete_old_events(self, days_to_keep: int = 90) -> int:
        """
        Delete events older than specified days (for manual cleanup)

        Args:
            days_to_keep: Number of days of events to retain

        Returns:
            Number of items deleted
        """
        if self.events_container is None:
            return 0

        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")

            query = f"""
                SELECT c.id, c.event_type
                FROM c
                WHERE c.date < '{cutoff_date}'
            """

            items = list(self.events_container.query_items(query=query))
            deleted_count = 0

            for item in items:
                try:
                    self.events_container.delete_item(
                        item=item["id"],
                        partition_key=item["event_type"]
                    )
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete item {item['id']}: {e}")

            logger.info(f"Deleted {deleted_count} old events (before {cutoff_date})")
            return deleted_count

        except Exception as e:
            logger.error(f"Delete old events failed: {e}")
            return 0

    # Dashboard storage methods

    async def save_dashboard(
        self,
        user_id: str,
        dashboard_name: str,
        layout: Dict[str, Any],
        filters: Dict[str, Any] = None
    ) -> Optional[str]:
        """Save user's custom dashboard layout"""
        if self.dashboards_container is None:
            return None

        try:
            doc = {
                "id": f"{user_id}:{dashboard_name}",
                "user_id": user_id,
                "name": dashboard_name,
                "layout": layout,
                "filters": filters or {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            asyncio.create_task(self._async_create_item_dashboards(doc))
            return doc["id"]

        except Exception as e:
            logger.error(f"Failed to save dashboard: {e}")
            return None

    async def _async_create_item_dashboards(self, doc: Dict[str, Any]):
        """Create dashboard item in Cosmos DB (async)"""
        try:
            self.dashboards_container.create_item(body=doc)
        except Exception as e:
            logger.error(f"Failed to store dashboard: {e}")

    async def get_dashboard(self, user_id: str, dashboard_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve user's dashboard"""
        if self.dashboards_container is None:
            return None

        try:
            item = self.dashboards_container.read_item(
                item=f"{user_id}:{dashboard_name}",
                partition_key=user_id
            )
            return item
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Dashboard not found: {user_id}:{dashboard_name}")
            return None
        except Exception as e:
            logger.error(f"Failed to get dashboard: {e}")
            return None

    # Preferences storage methods

    async def save_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> Optional[str]:
        """Save user notification preferences"""
        if self.preferences_container is None:
            return None

        try:
            doc = {
                "id": user_id,
                "user_id": user_id,
                "alert_thresholds": preferences.get("alert_thresholds", {}),
                "notification_methods": preferences.get("notification_methods", []),
                "quiet_hours": preferences.get("quiet_hours", {}),
                "digest_frequency": preferences.get("digest_frequency", "daily"),
                "updated_at": datetime.utcnow().isoformat()
            }

            asyncio.create_task(self._async_create_item_preferences(doc))
            return doc["id"]

        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
            return None

    async def _async_create_item_preferences(self, doc: Dict[str, Any]):
        """Create preferences item in Cosmos DB (async)"""
        try:
            self.preferences_container.create_item(body=doc)
        except Exception as e:
            logger.error(f"Failed to store preferences: {e}")

    async def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user preferences"""
        if self.preferences_container is None:
            return None

        try:
            item = self.preferences_container.read_item(
                item=user_id,
                partition_key=user_id
            )
            return item
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Preferences not found for user: {user_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get preferences: {e}")
            return None


# Global instance (singleton pattern)
_event_storage_service: Optional[EventStorageService] = None


def get_event_storage_service(
    cosmos_endpoint: str = None,
    cosmos_key: str = None
) -> EventStorageService:
    """Get or create event storage service instance"""
    global _event_storage_service

    if _event_storage_service is None:
        if cosmos_endpoint and cosmos_key:
            _event_storage_service = EventStorageService(cosmos_endpoint, cosmos_key)
        else:
            import os
            _event_storage_service = EventStorageService(
                os.getenv("COSMOS_ENDPOINT", ""),
                os.getenv("COSMOS_KEY", "")
            )

    return _event_storage_service
