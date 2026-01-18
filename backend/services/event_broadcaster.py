"""
Phase 7: Event Broadcasting Service

Manages WebSocket connections and broadcasts events to subscribed clients.
"""

from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import uuid

logger = logging.getLogger(__name__)


class ClientConnection:
    """Represents a connected WebSocket client with subscriptions and metadata"""
    
    def __init__(self, client_id: str, websocket: WebSocket, user_id: str):
        self.client_id = client_id
        self.websocket = websocket
        self.user_id = user_id
        self.subscribed_topics: Set[str] = set()
        self.filters: Dict[str, Dict] = {}  # topic -> filter dict
        self.connected_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.messages_received = 0
        self.messages_sent = 0
        self.errors = 0
    
    async def send_event(self, event: dict) -> bool:
        """
        Send event to client
        
        Returns:
            True if sent successfully, False if disconnected
        """
        try:
            await self.websocket.send_json(event)
            self.messages_sent += 1
            self.last_activity = datetime.utcnow()
            return True
        except Exception as e:
            logger.warning(f"Failed to send to {self.client_id}: {e}")
            self.errors += 1
            return False
    
    async def receive_message(self) -> Optional[dict]:
        """
        Receive message from client
        
        Returns:
            Parsed JSON message or None if disconnected
        """
        try:
            data = await self.websocket.receive_json()
            self.messages_received += 1
            self.last_activity = datetime.utcnow()
            return data
        except Exception as e:
            logger.debug(f"Client {self.client_id} disconnected or sent invalid data: {e}")
            return None
    
    async def close(self):
        """Close WebSocket connection"""
        try:
            await self.websocket.close()
        except Exception as e:
            logger.debug(f"Error closing connection {self.client_id}: {e}")
    
    def is_active(self, timeout_seconds: int = 120) -> bool:
        """Check if client is still active (received message within timeout)"""
        elapsed = (datetime.utcnow() - self.last_activity).total_seconds()
        return elapsed < timeout_seconds
    
    def get_stats(self) -> dict:
        """Get client statistics"""
        return {
            "client_id": self.client_id,
            "user_id": self.user_id,
            "connected_at": self.connected_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "messages_received": self.messages_received,
            "messages_sent": self.messages_sent,
            "errors": self.errors,
            "subscribed_topics": list(self.subscribed_topics)
        }


class EventBroadcasterService:
    """
    Manages WebSocket connections and broadcasts events to clients.
    
    Architecture:
    - Maintains registry of all connected clients
    - Tracks subscriptions by topic
    - Filters events before broadcasting
    - Handles reconnections and cleanup
    - Supports selective delivery based on filters
    """
    
    def __init__(self, max_concurrent_connections: int = 1000):
        self.clients: Dict[str, ClientConnection] = {}
        self.topic_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        # topic -> Set[client_ids]
        self.max_concurrent_connections = max_concurrent_connections
        
        # Statistics
        self.total_messages_sent = 0
        self.total_messages_received = 0
        self.total_errors = 0
        self.last_minute_errors = 0
        self.last_error_cleanup = datetime.utcnow()
    
    def register_client(self, websocket: WebSocket, user_id: str) -> Optional[ClientConnection]:
        """
        Register a new WebSocket client
        
        Args:
            websocket: FastAPI WebSocket connection
            user_id: User ID from authentication token
        
        Returns:
            ClientConnection object or None if limit reached
        """
        if len(self.clients) >= self.max_concurrent_connections:
            logger.warning(
                f"Max concurrent connections ({self.max_concurrent_connections}) reached"
            )
            return None
        
        client_id = f"client-{uuid.uuid4()}"
        client = ClientConnection(client_id, websocket, user_id)
        self.clients[client_id] = client
        logger.info(
            f"Client {client_id} (user: {user_id}) registered. "
            f"Total: {len(self.clients)}"
        )
        return client
    
    def unregister_client(self, client_id: str) -> bool:
        """
        Unregister a client and remove from all subscriptions
        
        Returns:
            True if client was registered and removed, False otherwise
        """
        if client_id not in self.clients:
            return False
        
        client = self.clients[client_id]
        
        # Remove from all topic subscriptions
        for topic in list(client.subscribed_topics):
            self.topic_subscriptions[topic].discard(client_id)
        
        del self.clients[client_id]
        logger.info(f"Client {client_id} unregistered. Total: {len(self.clients)}")
        return True
    
    def subscribe(
        self,
        client_id: str,
        topic: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Subscribe client to a topic with optional filters
        
        Args:
            client_id: Client ID
            topic: Topic name (e.g., "alerts", "prices", "signals")
            filters: Optional dict of filters (e.g., {"risk_level": ["CRITICAL"]})
        
        Returns:
            True if successful, False if client not found
        """
        if client_id not in self.clients:
            logger.warning(f"Cannot subscribe unknown client {client_id}")
            return False
        
        client = self.clients[client_id]
        client.subscribed_topics.add(topic)
        client.filters[topic] = filters or {}
        self.topic_subscriptions[topic].add(client_id)
        
        logger.info(
            f"Client {client_id} subscribed to topic '{topic}' "
            f"with filters: {filters}"
        )
        return True
    
    def unsubscribe(self, client_id: str, topic: Optional[str] = None) -> bool:
        """
        Unsubscribe client from a topic (or all topics if not specified)
        
        Returns:
            True if successful, False if client not found
        """
        if client_id not in self.clients:
            return False
        
        client = self.clients[client_id]
        
        if topic:
            client.subscribed_topics.discard(topic)
            self.topic_subscriptions[topic].discard(client_id)
            logger.info(f"Client {client_id} unsubscribed from topic '{topic}'")
        else:
            # Unsubscribe from all topics
            for t in list(client.subscribed_topics):
                self.topic_subscriptions[t].discard(client_id)
            client.subscribed_topics.clear()
            logger.info(f"Client {client_id} unsubscribed from all topics")
        
        return True
    
    def _matches_filters(self, event: dict, filters: Dict[str, Any]) -> bool:
        """
        Check if event matches subscription filters
        
        Args:
            event: Event dictionary
            filters: Filter dictionary (e.g., {"risk_level": ["CRITICAL"]})
        
        Returns:
            True if event matches filters, False otherwise
        """
        if not filters:
            return True
        
        for key, allowed_values in filters.items():
            if key not in event:
                continue
            
            # Convert single value to list
            if not isinstance(allowed_values, (list, set)):
                allowed_values = [allowed_values]
            
            # Check if event value is in allowed values
            if event.get(key) not in allowed_values:
                return False
        
        return True
    
    async def broadcast_event(
        self,
        event: dict,
        topic: str,
        exclude_client: Optional[str] = None
    ) -> int:
        """
        Broadcast event to all subscribed clients matching filters
        
        Args:
            event: Event data (dict or can convert Pydantic model)
            topic: Topic to broadcast to (e.g., "alerts", "prices")
            exclude_client: Optional client ID to exclude from broadcast
        
        Returns:
            Number of clients successfully sent to
        """
        
        # Convert Pydantic models to dict
        if hasattr(event, 'dict'):
            event = event.dict()
        
        # Get subscribed clients
        client_ids = list(self.topic_subscriptions.get(topic, set()))
        
        if not client_ids:
            logger.debug(f"No subscribers for topic '{topic}'")
            return 0
        
        # Filter out excluded client and invalid clients
        client_ids = [
            cid for cid in client_ids
            if cid in self.clients and cid != exclude_client
        ]
        
        # Send to all matching clients in parallel
        tasks = []
        valid_clients = []
        
        for client_id in client_ids:
            client = self.clients[client_id]
            
            # Apply filters
            if not self._matches_filters(event, client.filters.get(topic, {})):
                continue
            
            valid_clients.append(client_id)
            tasks.append(client.send_event(event))
        
        if not tasks:
            logger.debug(
                f"No clients matched filters for topic '{topic}' "
                f"(subscribed: {len(client_ids)})"
            )
            return 0
        
        # Execute sends in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes
        successful = sum(1 for r in results if r is True)
        self.total_messages_sent += successful
        
        # Track errors
        failed = len([r for r in results if r is False])
        if failed > 0:
            self.total_errors += failed
            self.last_minute_errors += failed
            logger.warning(
                f"Failed to send to {failed}/{len(valid_clients)} clients "
                f"for topic '{topic}'"
            )
        
        logger.debug(
            f"Sent event to {successful}/{len(valid_clients)} subscribers "
            f"on topic '{topic}'"
        )
        return successful
    
    async def cleanup_inactive_clients(self, timeout_seconds: int = 120) -> int:
        """
        Remove clients with no activity within timeout period
        
        Args:
            timeout_seconds: Inactivity timeout in seconds
        
        Returns:
            Number of clients removed
        """
        inactive = [
            client_id for client_id, client in self.clients.items()
            if not client.is_active(timeout_seconds)
        ]
        
        for client_id in inactive:
            await self.clients[client_id].close()
            self.unregister_client(client_id)
        
        if inactive:
            logger.info(f"Cleaned up {len(inactive)} inactive clients")
        
        # Reset error counter every minute
        now = datetime.utcnow()
        if (now - self.last_error_cleanup).total_seconds() > 60:
            self.last_minute_errors = 0
            self.last_error_cleanup = now
        
        return len(inactive)
    
    def get_client(self, client_id: str) -> Optional[ClientConnection]:
        """Get client by ID"""
        return self.clients.get(client_id)
    
    def get_stats(self) -> dict:
        """Get server statistics"""
        return {
            "active_connections": len(self.clients),
            "total_topics": len(self.topic_subscriptions),
            "messages_sent_total": self.total_messages_sent,
            "messages_received_total": self.total_messages_received,
            "errors_total": self.total_errors,
            "errors_last_minute": self.last_minute_errors,
            "topics": {
                topic: len(client_ids)
                for topic, client_ids in self.topic_subscriptions.items()
            }
        }
    
    def get_clients_stats(self) -> List[dict]:
        """Get statistics for all connected clients"""
        return [client.get_stats() for client in self.clients.values()]


# Global broadcaster instance (singleton)
broadcaster = EventBroadcasterService()
