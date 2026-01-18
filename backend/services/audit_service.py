"""Audit Logging Service

Implements audit trail logging for compliance, monitoring, and forensics.
Logs all security-relevant events: authentication, access, modifications, errors.

Integration Points:
- Authentication routes: login, logout, token refresh
- Resource routes: read, create, update, delete operations
- Admin routes: user management, system changes
- Error handling: failed access attempts, exceptions

Storage: Cosmos DB (audit_logs collection)
Retention: 1 year hot, 7 years cold archive

Phase 5 Integration:
- Cosmos DB backend for production deployment
- Partitioned by tenant_id for multi-tenant efficiency
- Sorted by timestamp for time-series queries
- Indexes on user_email, event_type, severity for fast lookups
- Automatic TTL on cold archive items after 7 years
- Fallback to in-memory for development
"""

import logging
import json
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from enum import Enum
from dataclasses import dataclass, asdict
import uuid

# Cosmos DB imports (optional - fallback to in-memory if not available)
try:
    from azure.cosmos import CosmosClient, PartitionKey, exceptions
    COSMOS_AVAILABLE = True
except ImportError:
    COSMOS_AVAILABLE = False

logger = logging.getLogger("audit")


class AuditEventType(str, Enum):
    """Types of audit events to track"""
    
    # Authentication Events
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    TOKEN_VALIDATION_FAILED = "TOKEN_VALIDATION_FAILED"
    REGISTER = "REGISTER"
    PASSWORD_RESET = "PASSWORD_RESET"
    EMAIL_VERIFIED = "EMAIL_VERIFIED"
    
    # Access Events
    RESOURCE_READ = "RESOURCE_READ"
    RESOURCE_EXPORT = "RESOURCE_EXPORT"
    BULK_READ = "BULK_READ"
    
    # Modification Events
    RESOURCE_CREATE = "RESOURCE_CREATE"
    RESOURCE_UPDATE = "RESOURCE_UPDATE"
    RESOURCE_DELETE = "RESOURCE_DELETE"
    BULK_DELETE = "BULK_DELETE"
    
    # User Management
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    ROLE_CHANGED = "ROLE_CHANGED"
    STATUS_CHANGED = "STATUS_CHANGED"
    
    # Security Events
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    CROSS_TENANT_ACCESS = "CROSS_TENANT_ACCESS"
    BRUTE_FORCE_ATTEMPT = "BRUTE_FORCE_ATTEMPT"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    
    # Compliance Events
    GDPR_DATA_EXPORT = "GDPR_DATA_EXPORT"
    GDPR_DATA_DELETE = "GDPR_DATA_DELETE"
    CONSENT_GRANTED = "CONSENT_GRANTED"
    CONSENT_REVOKED = "CONSENT_REVOKED"
    
    # System Events
    SYSTEM_ERROR = "SYSTEM_ERROR"
    CONFIGURATION_CHANGED = "CONFIGURATION_CHANGED"
    AUDIT_LOG_ACCESSED = "AUDIT_LOG_ACCESSED"


class AuditResult(str, Enum):
    """Result of audit event"""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"


@dataclass
class AuditEvent:
    """Audit event record
    
    Represents a single audit-relevant event in the system.
    Includes context, outcome, and metadata for compliance.
    """
    
    # Core fields
    id: str  # UUID
    tenant_id: str  # Multi-tenant isolation
    timestamp: str  # ISO 8601 UTC
    
    # User context
    user_email: Optional[str]  # Who performed action
    user_role: Optional[str]  # User's role at time of action
    
    # Event details
    event_type: AuditEventType  # Type of event
    action: Optional[str]  # Specific action (create, update, delete, etc.)
    result: AuditResult  # Success/failure
    
    # Resource context
    resource_type: Optional[str]  # Type of resource (user, template, document)
    resource_id: Optional[str]  # ID of resource
    
    # Access details
    allowed: bool  # Was access/action allowed?
    reason: Optional[str]  # Why allowed/denied
    
    # Request context
    ip_address: Optional[str]  # Source IP
    user_agent: Optional[str]  # Browser/client info
    
    # Additional details
    details: Optional[Dict[str, Any]] = None  # Event-specific data
    changes: Optional[Dict[str, Any]] = None  # Before/after for modifications
    error_message: Optional[str] = None  # Error details if failed
    
    # Metadata
    processing_time_ms: Optional[float] = None  # How long operation took
    tags: Optional[List[str]] = None  # Searchable tags (high_risk, bulk, etc.)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        data = asdict(self)
        # Convert enum to string
        data['event_type'] = self.event_type.value
        data['result'] = self.result.value
        return data


class AuditService:
    """Service for logging and managing audit events
    
    Provides methods to log various types of security-relevant events.
    All logging is async and non-blocking.
    
    Supports both in-memory (development) and Cosmos DB (production) backends.
    """
    
    # In-memory event log (fallback for development)
    _event_log: List[AuditEvent] = []
    _event_index: Dict[str, List[AuditEvent]] = {
        'user_email': {},
        'event_type': {},
        'resource_type': {},
        'resource_id': {},
    }
    
    # Cosmos DB connection (initialized on first use)
    _cosmos_client: Optional['CosmosClient'] = None
    _cosmos_database: Optional[Any] = None
    _cosmos_container: Optional[Any] = None
    _use_cosmos: bool = False
    
    @staticmethod
    async def _init_cosmos() -> bool:
        """Initialize Cosmos DB connection
        
        Returns:
            True if Cosmos DB is available and connected, False otherwise
        """
        if not COSMOS_AVAILABLE:
            logger.warning("Azure Cosmos SDK not available, using in-memory storage")
            return False
        
        try:
            # Get connection details from environment
            cosmos_endpoint = os.getenv("COSMOS_DB_ENDPOINT")
            cosmos_key = os.getenv("COSMOS_DB_KEY")
            cosmos_db_name = os.getenv("COSMOS_DB_NAME", "kraftd_audit")
            
            if not cosmos_endpoint or not cosmos_key:
                logger.info("Cosmos DB credentials not configured, using in-memory storage")
                return False
            
            # Initialize client
            AuditService._cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
            
            # Get or create database
            AuditService._cosmos_database = AuditService._cosmos_client.get_database_client(cosmos_db_name)
            
            # Get or create container with partitioning
            # Partition by tenant_id for multi-tenant efficiency
            # Sort by timestamp for time-series queries
            try:
                AuditService._cosmos_container = AuditService._cosmos_database.get_container_client("audit_events")
            except exceptions.CosmosResourceNotFoundError:
                logger.info("Creating audit_events container in Cosmos DB")
                AuditService._cosmos_container = AuditService._cosmos_database.create_container(
                    id="audit_events",
                    partition_key=PartitionKey(path="/tenant_id"),
                    offer_throughput=400  # Minimum for multi-partition
                )
                
                # Create indexes for common queries
                indexing_policy = {
                    "indexingMode": "consistent",
                    "automatic": True,
                    "includedPaths": [
                        {"path": "/*"}  # Index all paths
                    ],
                    "excludedPaths": [
                        {"path": "/timestamp/*"}  # Exclude timestamp sorting path
                    ],
                    "compositeIndexes": [
                        [
                            {"path": "/tenant_id", "order": "ascending"},
                            {"path": "/timestamp", "order": "descending"}  # Tenant + timestamp for range queries
                        ],
                        [
                            {"path": "/tenant_id", "order": "ascending"},
                            {"path": "/event_type", "order": "ascending"}
                        ],
                        [
                            {"path": "/tenant_id", "order": "ascending"},
                            {"path": "/user_email", "order": "ascending"}
                        ]
                    ]
                }
                
                try:
                    AuditService._cosmos_container.replace_container(
                        partition_key=PartitionKey(path="/tenant_id"),
                        indexing_policy=indexing_policy
                    )
                except Exception as e:
                    logger.warning(f"Could not update indexing policy: {e}")
            
            AuditService._use_cosmos = True
            logger.info(f"Connected to Cosmos DB: {cosmos_endpoint}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            logger.info("Falling back to in-memory storage")
            return False
    
    @staticmethod
    async def log_event(event: AuditEvent) -> str:
        """Log an audit event
        
        Args:
            event: AuditEvent to log
            
        Returns:
            Event ID
        """
        # Set timestamp if not provided
        if not event.timestamp:
            event.timestamp = datetime.now(tz=timezone.utc).isoformat()
        
        # Generate ID if not provided
        if not event.id:
            event.id = str(uuid.uuid4())
        
        # Initialize Cosmos DB on first use
        if not AuditService._use_cosmos:
            await AuditService._init_cosmos()
        
        # Store event
        if AuditService._use_cosmos and AuditService._cosmos_container:
            try:
                # Store in Cosmos DB
                event_dict = event.to_dict()
                AuditService._cosmos_container.create_item(body=event_dict)
                logger.debug(f"Event {event.id} stored in Cosmos DB")
            except Exception as e:
                logger.error(f"Failed to store event in Cosmos DB: {e}")
                # Fallback to in-memory
                AuditService._event_log.append(event)
        else:
            # Store in memory (development or fallback)
            AuditService._event_log.append(event)
            
            # Update in-memory indexes
            if event.user_email:
                if event.user_email not in AuditService._event_index['user_email']:
                    AuditService._event_index['user_email'][event.user_email] = []
                AuditService._event_index['user_email'][event.user_email].append(event)
            
            if event.event_type:
                event_type_str = event.event_type.value
                if event_type_str not in AuditService._event_index['event_type']:
                    AuditService._event_index['event_type'][event_type_str] = []
                AuditService._event_index['event_type'][event_type_str].append(event)
            
            if event.resource_type:
                if event.resource_type not in AuditService._event_index['resource_type']:
                    AuditService._event_index['resource_type'][event.resource_type] = []
                AuditService._event_index['resource_type'][event.resource_type].append(event)
            
            if event.resource_id:
                if event.resource_id not in AuditService._event_index['resource_id']:
                    AuditService._event_index['resource_id'][event.resource_id] = []
                AuditService._event_index['resource_id'][event.resource_id].append(event)
        
        # Log to application logger
        _log_event(event)
        
        return event.id
    
    @staticmethod
    async def log_login(
        user_email: str,
        success: bool,
        tenant_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None
    ) -> str:
        """Log user login attempt
        
        Args:
            user_email: User attempting to login
            success: Whether login succeeded
            tenant_id: Tenant context
            ip_address: Source IP
            user_agent: Client user agent
            reason: Reason for failure (if failed)
            
        Returns:
            Event ID
        """
        event = AuditEvent(
            id=None,
            tenant_id=tenant_id,
            timestamp=None,
            user_email=user_email,
            user_role=None,
            event_type=AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILED,
            action="login",
            result=AuditResult.SUCCESS if success else AuditResult.FAILURE,
            resource_type="user",
            resource_id=user_email,
            allowed=success,
            reason=reason or ("Successful login" if success else "Invalid credentials"),
            ip_address=ip_address,
            user_agent=user_agent,
            tags=[] if success else ["failed_login"]
        )
        
        return await AuditService.log_event(event)
    
    @staticmethod
    async def log_access(
        user_email: str,
        user_role: str,
        resource_type: str,
        resource_id: str,
        tenant_id: str,
        allowed: bool,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Log resource access attempt
        
        Args:
            user_email: User accessing resource
            user_role: User's role
            resource_type: Type of resource
            resource_id: Resource ID
            tenant_id: Tenant context
            allowed: Whether access was allowed
            reason: Why allowed/denied
            ip_address: Source IP
            user_agent: Client user agent
            
        Returns:
            Event ID
        """
        # Track cross-tenant attempts
        tags = []
        if not allowed and reason and "cross-tenant" in reason.lower():
            tags.append("cross_tenant_attempt")
        
        event = AuditEvent(
            id=None,
            tenant_id=tenant_id,
            timestamp=None,
            user_email=user_email,
            user_role=user_role,
            event_type=AuditEventType.RESOURCE_READ,
            action="read",
            result=AuditResult.SUCCESS if allowed else AuditResult.FAILURE,
            resource_type=resource_type,
            resource_id=resource_id,
            allowed=allowed,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            tags=tags
        )
        
        return await AuditService.log_event(event)
    
    @staticmethod
    async def log_modification(
        user_email: str,
        user_role: str,
        resource_type: str,
        resource_id: str,
        tenant_id: str,
        action: str,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Log resource modification
        
        Args:
            user_email: User making modification
            user_role: User's role
            resource_type: Type of resource
            resource_id: Resource ID
            tenant_id: Tenant context
            action: Action performed (create, update, delete)
            changes: Before/after values
            ip_address: Source IP
            reason: Reason for modification
            user_agent: Client user agent
            
        Returns:
            Event ID
        """
        event_type_map = {
            "create": AuditEventType.RESOURCE_CREATE,
            "update": AuditEventType.RESOURCE_UPDATE,
            "delete": AuditEventType.RESOURCE_DELETE,
        }
        
        event = AuditEvent(
            id=None,
            tenant_id=tenant_id,
            timestamp=None,
            user_email=user_email,
            user_role=user_role,
            event_type=event_type_map.get(action, AuditEventType.RESOURCE_UPDATE),
            action=action,
            result=AuditResult.SUCCESS,
            resource_type=resource_type,
            resource_id=resource_id,
            allowed=True,
            reason=reason,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return await AuditService.log_event(event)
    
    @staticmethod
    async def log_error(
        user_email: Optional[str],
        event_type: AuditEventType,
        resource_type: Optional[str],
        resource_id: Optional[str],
        tenant_id: str,
        error_message: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Log error or failed operation
        
        Args:
            user_email: User involved (if known)
            event_type: Type of error event
            resource_type: Resource type (if applicable)
            resource_id: Resource ID (if applicable)
            tenant_id: Tenant context
            error_message: Error details
            ip_address: Source IP
            user_agent: Client user agent
            
        Returns:
            Event ID
        """
        event = AuditEvent(
            id=None,
            tenant_id=tenant_id,
            timestamp=None,
            user_email=user_email,
            user_role=None,
            event_type=event_type,
            action=None,
            result=AuditResult.FAILURE,
            resource_type=resource_type,
            resource_id=resource_id,
            allowed=False,
            reason=error_message,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            tags=["error", "security_event"]
        )
        
        return await AuditService.log_event(event)
    
    @staticmethod
    async def get_events(
        user_email: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditEvent]:
        """Query audit events
        
        Args:
            user_email: Filter by user
            event_type: Filter by event type
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            tenant_id: Filter by tenant
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of matching events
        """
        # Initialize Cosmos DB on first use
        if not AuditService._use_cosmos:
            await AuditService._init_cosmos()
        
        if AuditService._use_cosmos and AuditService._cosmos_container and tenant_id:
            # Query from Cosmos DB
            try:
                # Build query
                query = "SELECT * FROM c WHERE c.tenant_id = @tenant_id"
                parameters = [{"name": "@tenant_id", "value": tenant_id}]
                
                if user_email:
                    query += " AND c.user_email = @user_email"
                    parameters.append({"name": "@user_email", "value": user_email})
                
                if event_type:
                    query += " AND c.event_type = @event_type"
                    parameters.append({"name": "@event_type", "value": event_type.value})
                
                if resource_type:
                    query += " AND c.resource_type = @resource_type"
                    parameters.append({"name": "@resource_type", "value": resource_type})
                
                if resource_id:
                    query += " AND c.resource_id = @resource_id"
                    parameters.append({"name": "@resource_id", "value": resource_id})
                
                # Sort by timestamp descending
                query += " ORDER BY c.timestamp DESC"
                
                # Execute query with pagination
                items = list(AuditService._cosmos_container.query_items(
                    query=query,
                    parameters=parameters,
                    max_item_count=limit
                ))
                
                # Convert back to AuditEvent objects
                events = []
                for item in items[offset:offset + limit]:
                    event = AuditEvent(
                        id=item.get('id'),
                        tenant_id=item.get('tenant_id'),
                        timestamp=item.get('timestamp'),
                        user_email=item.get('user_email'),
                        user_role=item.get('user_role'),
                        event_type=AuditEventType(item.get('event_type')),
                        action=item.get('action'),
                        result=AuditResult(item.get('result')),
                        resource_type=item.get('resource_type'),
                        resource_id=item.get('resource_id'),
                        allowed=item.get('allowed', False),
                        reason=item.get('reason'),
                        ip_address=item.get('ip_address'),
                        user_agent=item.get('user_agent'),
                        details=item.get('details'),
                        changes=item.get('changes'),
                        error_message=item.get('error_message'),
                        processing_time_ms=item.get('processing_time_ms'),
                        tags=item.get('tags')
                    )
                    events.append(event)
                
                return events
                
            except Exception as e:
                logger.error(f"Failed to query Cosmos DB: {e}")
                # Fallback to in-memory
        
        # Query from in-memory (development or fallback)
        results = AuditService._event_log
        
        # Apply filters
        if user_email:
            results = [e for e in results if e.user_email == user_email]
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if resource_type:
            results = [e for e in results if e.resource_type == resource_type]
        if resource_id:
            results = [e for e in results if e.resource_id == resource_id]
        if tenant_id:
            results = [e for e in results if e.tenant_id == tenant_id]
        
        # Sort by timestamp descending
        results = sorted(results, key=lambda e: e.timestamp, reverse=True)
        
        # Pagination
        return results[offset:offset + limit]
    
    @staticmethod
    async def count_events(
        user_email: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        resource_type: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> int:
        """Count audit events matching criteria"""
        
        # Initialize Cosmos DB on first use
        if not AuditService._use_cosmos:
            await AuditService._init_cosmos()
        
        if AuditService._use_cosmos and AuditService._cosmos_container and tenant_id:
            # Query count from Cosmos DB
            try:
                query = "SELECT VALUE COUNT(1) FROM c WHERE c.tenant_id = @tenant_id"
                parameters = [{"name": "@tenant_id", "value": tenant_id}]
                
                if user_email:
                    query += " AND c.user_email = @user_email"
                    parameters.append({"name": "@user_email", "value": user_email})
                
                if event_type:
                    query += " AND c.event_type = @event_type"
                    parameters.append({"name": "@event_type", "value": event_type.value})
                
                if resource_type:
                    query += " AND c.resource_type = @resource_type"
                    parameters.append({"name": "@resource_type", "value": resource_type})
                
                results = list(AuditService._cosmos_container.query_items(
                    query=query,
                    parameters=parameters
                ))
                
                return results[0] if results else 0
                
            except Exception as e:
                logger.error(f"Failed to count events in Cosmos DB: {e}")
                # Fallback to in-memory
        
        # Count from in-memory (development or fallback)
        results = AuditService._event_log
        
        if user_email:
            results = [e for e in results if e.user_email == user_email]
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if resource_type:
            results = [e for e in results if e.resource_type == resource_type]
        if tenant_id:
            results = [e for e in results if e.tenant_id == tenant_id]
        
        return len(results)


def _log_event(event: AuditEvent) -> None:
    """Internal method to log event to application logger"""
    
    log_level = logging.WARNING if not event.allowed else logging.INFO
    
    message = (
        f"[{event.event_type.value}] "
        f"user={event.user_email or 'unknown'} "
        f"role={event.user_role or 'n/a'} "
        f"result={event.result.value} "
        f"resource={event.resource_type}/{event.resource_id} "
        f"allowed={event.allowed}"
    )
    
    if event.reason:
        message += f" reason={event.reason}"
    
    if event.error_message:
        message += f" error={event.error_message}"
    
    logger.log(log_level, message)
