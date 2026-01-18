"""Alert Service for Security Monitoring

Monitors audit logs and generates real-time alerts for:
- Brute force attacks (multiple failed logins)
- Unusual access patterns (off-hours, bulk operations)
- Privilege escalation attempts
- GDPR requests and data operations
- Bulk deletions (data loss risk)
- Cross-tenant access attempts
- Admin actions and configuration changes
- System errors and anomalies

Alerts can be sent to:
- Email notifications
- Application logs (with high severity)
- Admin dashboard
- Webhook endpoints (for SIEM integration)
"""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import logging

from .audit_service import AuditService, AuditEvent, AuditEventType

logger = logging.getLogger("security_alerts")


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "CRITICAL"  # Immediate action required
    HIGH = "HIGH"  # Urgent attention needed
    MEDIUM = "MEDIUM"  # Should be reviewed
    LOW = "LOW"  # Informational


class AlertType(str, Enum):
    """Types of alerts that can be generated"""
    
    BRUTE_FORCE = "BRUTE_FORCE"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    CROSS_TENANT_ACCESS = "CROSS_TENANT_ACCESS"
    UNUSUAL_ACCESS_PATTERN = "UNUSUAL_ACCESS_PATTERN"
    BULK_DELETION = "BULK_DELETION"
    BULK_EXPORT = "BULK_EXPORT"
    FAILED_ACCESS = "FAILED_ACCESS"
    ADMIN_ACTION = "ADMIN_ACTION"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    GDPR_REQUEST = "GDPR_REQUEST"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"


@dataclass
class Alert:
    """Security alert"""
    
    id: str
    alert_type: AlertType
    severity: AlertSeverity
    timestamp: str
    tenant_id: str
    
    title: str
    description: str
    
    # Context
    user_email: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    
    # Details
    event_ids: List[str]  # Related audit event IDs
    metadata: Dict[str, Any]
    
    # Action
    recommended_action: str
    dismissed: bool = False
    resolved: bool = False


class AlertService:
    """Service for monitoring audit logs and generating alerts"""
    
    # Thresholds
    FAILED_LOGIN_THRESHOLD = 5  # Failed logins in 15 minutes
    FAILED_LOGIN_WINDOW = 900  # 15 minutes in seconds
    
    BULK_DELETE_THRESHOLD = 10  # Delete 10+ items
    BULK_EXPORT_THRESHOLD = 50  # Export 50+ items
    
    OFF_HOURS_ALERT_THRESHOLD = 3  # Off-hours actions to trigger alert
    
    # Storage for alerts (in-memory, would use Cosmos DB)
    _alerts: List[Alert] = []
    _alert_handlers: Dict[AlertType, List[Callable]] = {}
    
    @staticmethod
    async def check_for_alerts(tenant_id: str) -> List[Alert]:
        """Check audit logs for alert conditions
        
        Scans recent audit events and generates alerts for:
        - Brute force attempts
        - Unusual patterns
        - Security events
        - Compliance violations
        
        Args:
            tenant_id: Tenant to check
            
        Returns:
            List of generated alerts
        """
        new_alerts = []
        
        # Get recent events (last 1 hour)
        cutoff = datetime.utcnow() - timedelta(hours=1)
        events = await AuditService.get_events(
            tenant_id=tenant_id,
            limit=1000
        )
        recent = [
            e for e in events
            if datetime.fromisoformat(e.timestamp.replace('Z', '+00:00')) > cutoff
        ]
        
        # Check for brute force
        alerts = await AlertService._check_brute_force(recent, tenant_id)
        new_alerts.extend(alerts)
        
        # Check for privilege escalation
        alerts = await AlertService._check_privilege_escalation(recent, tenant_id)
        new_alerts.extend(alerts)
        
        # Check for cross-tenant access
        alerts = await AlertService._check_cross_tenant_access(recent, tenant_id)
        new_alerts.extend(alerts)
        
        # Check for unusual patterns
        alerts = await AlertService._check_unusual_patterns(recent, tenant_id)
        new_alerts.extend(alerts)
        
        # Check for bulk operations
        alerts = await AlertService._check_bulk_operations(recent, tenant_id)
        new_alerts.extend(alerts)
        
        # Check for GDPR requests
        alerts = await AlertService._check_gdpr_requests(recent, tenant_id)
        new_alerts.extend(alerts)
        
        # Check for admin actions
        alerts = await AlertService._check_admin_actions(recent, tenant_id)
        new_alerts.extend(alerts)
        
        # Store and trigger handlers
        for alert in new_alerts:
            AlertService._alerts.append(alert)
            await AlertService._trigger_alert(alert)
        
        return new_alerts
    
    @staticmethod
    async def _check_brute_force(
        events: List[AuditEvent],
        tenant_id: str
    ) -> List[Alert]:
        """Detect brute force login attempts"""
        alerts = []
        
        # Group failed logins by user and time window
        from collections import defaultdict
        failed_logins = [
            e for e in events
            if e.event_type == AuditEventType.LOGIN_FAILED
        ]
        
        by_user = defaultdict(list)
        for event in failed_logins:
            by_user[event.user_email].append(event)
        
        # Check for threshold breaches
        for user_email, user_events in by_user.items():
            if len(user_events) >= AlertService.FAILED_LOGIN_THRESHOLD:
                alert = Alert(
                    id=f"brute_{user_email}_{datetime.utcnow().isoformat()}",
                    alert_type=AlertType.BRUTE_FORCE,
                    severity=AlertSeverity.CRITICAL,
                    timestamp=datetime.utcnow().isoformat() + 'Z',
                    tenant_id=tenant_id,
                    title=f"Brute Force Detected: {user_email}",
                    description=f"{len(user_events)} failed login attempts in 15 minutes",
                    user_email=user_email,
                    resource_type="user_authentication",
                    resource_id=user_email,
                    event_ids=[e.id for e in user_events],
                    metadata={
                        'failed_attempts': len(user_events),
                        'ips': list(set(e.ip_address for e in user_events if e.ip_address))
                    },
                    recommended_action=f"Lock account {user_email} and investigate failed login attempts"
                )
                alerts.append(alert)
        
        return alerts
    
    @staticmethod
    async def _check_privilege_escalation(
        events: List[AuditEvent],
        tenant_id: str
    ) -> List[Alert]:
        """Detect privilege escalation attempts"""
        alerts = []
        
        privilege_events = [
            e for e in events
            if e.event_type == AuditEventType.ROLE_CHANGED or \
               e.event_type == AuditEventType.PRIVILEGE_ESCALATION
        ]
        
        for event in privilege_events:
            if not event.allowed or event.event_type == AuditEventType.PRIVILEGE_ESCALATION:
                severity = AlertSeverity.CRITICAL if not event.allowed else AlertSeverity.HIGH
                
                alert = Alert(
                    id=f"priv_esc_{event.id}",
                    alert_type=AlertType.PRIVILEGE_ESCALATION,
                    severity=severity,
                    timestamp=event.timestamp,
                    tenant_id=tenant_id,
                    title=f"Privilege Escalation: {event.user_email}",
                    description=f"Attempted to change role for {event.resource_id}",
                    user_email=event.user_email,
                    resource_type=event.resource_type,
                    resource_id=event.resource_id,
                    event_ids=[event.id],
                    metadata={
                        'old_role': event.details.get('old_role') if event.details else None,
                        'new_role': event.details.get('new_role') if event.details else None,
                    },
                    recommended_action="Review role changes and investigate if unauthorized"
                )
                alerts.append(alert)
        
        return alerts
    
    @staticmethod
    async def _check_cross_tenant_access(
        events: List[AuditEvent],
        tenant_id: str
    ) -> List[Alert]:
        """Detect cross-tenant access attempts"""
        alerts = []
        
        cross_tenant_events = [
            e for e in events
            if e.event_type == AuditEventType.CROSS_TENANT_ACCESS or \
               (not e.allowed and "cross-tenant" in (e.reason or "").lower())
        ]
        
        for event in cross_tenant_events:
            alert = Alert(
                id=f"cross_tenant_{event.id}",
                alert_type=AlertType.CROSS_TENANT_ACCESS,
                severity=AlertSeverity.CRITICAL,
                timestamp=event.timestamp,
                tenant_id=tenant_id,
                title=f"Cross-Tenant Access Attempt: {event.user_email}",
                description=f"User attempted to access resource from different tenant",
                user_email=event.user_email,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                event_ids=[event.id],
                metadata={
                    'ip_address': event.ip_address,
                    'user_agent': event.user_agent
                },
                recommended_action="Investigate potential security breach or account compromise"
            )
            alerts.append(alert)
        
        return alerts
    
    @staticmethod
    async def _check_unusual_patterns(
        events: List[AuditEvent],
        tenant_id: str
    ) -> List[Alert]:
        """Detect unusual access patterns"""
        alerts = []
        
        # Check for off-hours access
        off_hours_events = []
        for event in events:
            if event.event_type == AuditEventType.RESOURCE_READ:
                try:
                    ts = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
                    hour = ts.hour
                    weekday = ts.weekday()
                    
                    # Off-hours: before 6 AM or after 10 PM or weekends
                    if hour < 6 or hour > 22 or weekday >= 5:
                        off_hours_events.append(event)
                except:
                    pass
        
        # Group by user
        from collections import defaultdict
        by_user = defaultdict(list)
        for event in off_hours_events:
            by_user[event.user_email].append(event)
        
        # Alert if user has multiple off-hours accesses
        for user_email, user_events in by_user.items():
            if len(user_events) >= AlertService.OFF_HOURS_ALERT_THRESHOLD:
                alert = Alert(
                    id=f"unusual_{user_email}_{datetime.utcnow().isoformat()}",
                    alert_type=AlertType.UNUSUAL_ACCESS_PATTERN,
                    severity=AlertSeverity.MEDIUM,
                    timestamp=datetime.utcnow().isoformat() + 'Z',
                    tenant_id=tenant_id,
                    title=f"Unusual Access Pattern: {user_email}",
                    description=f"{len(user_events)} off-hours access attempts detected",
                    user_email=user_email,
                    resource_type="access_pattern",
                    resource_id=user_email,
                    event_ids=[e.id for e in user_events],
                    metadata={
                        'off_hours_accesses': len(user_events),
                        'ips': list(set(e.ip_address for e in user_events if e.ip_address))
                    },
                    recommended_action="Review access patterns and verify legitimate activity"
                )
                alerts.append(alert)
        
        return alerts
    
    @staticmethod
    async def _check_bulk_operations(
        events: List[AuditEvent],
        tenant_id: str
    ) -> List[Alert]:
        """Detect bulk delete/export operations"""
        alerts = []
        
        # Check for bulk deletes
        delete_events = [
            e for e in events
            if e.event_type in [
                AuditEventType.RESOURCE_DELETE,
                AuditEventType.BULK_DELETE
            ]
        ]
        
        # Group by user and time window (30 minutes)
        from collections import defaultdict
        by_user = defaultdict(list)
        for event in delete_events:
            by_user[event.user_email].append(event)
        
        for user_email, user_events in by_user.items():
            if len(user_events) >= AlertService.BULK_DELETE_THRESHOLD:
                alert = Alert(
                    id=f"bulk_delete_{user_email}_{datetime.utcnow().isoformat()}",
                    alert_type=AlertType.BULK_DELETION,
                    severity=AlertSeverity.HIGH,
                    timestamp=datetime.utcnow().isoformat() + 'Z',
                    tenant_id=tenant_id,
                    title=f"Bulk Deletion: {user_email}",
                    description=f"{len(user_events)} items deleted in short time window",
                    user_email=user_email,
                    resource_type="bulk_operation",
                    resource_id=user_email,
                    event_ids=[e.id for e in user_events],
                    metadata={
                        'deleted_count': len(user_events),
                        'resource_types': list(set(e.resource_type for e in user_events if e.resource_type))
                    },
                    recommended_action="Verify bulk deletion was authorized"
                )
                alerts.append(alert)
        
        # Check for bulk exports
        export_events = [
            e for e in events
            if e.event_type in [
                AuditEventType.RESOURCE_EXPORT,
                AuditEventType.GDPR_DATA_EXPORT
            ]
        ]
        
        by_user_export = defaultdict(list)
        for event in export_events:
            by_user_export[event.user_email].append(event)
        
        for user_email, user_events in by_user_export.items():
            if len(user_events) >= AlertService.BULK_EXPORT_THRESHOLD:
                alert = Alert(
                    id=f"bulk_export_{user_email}_{datetime.utcnow().isoformat()}",
                    alert_type=AlertType.BULK_EXPORT,
                    severity=AlertSeverity.MEDIUM,
                    timestamp=datetime.utcnow().isoformat() + 'Z',
                    tenant_id=tenant_id,
                    title=f"Bulk Data Export: {user_email}",
                    description=f"{len(user_events)} items exported in short time",
                    user_email=user_email,
                    resource_type="bulk_export",
                    resource_id=user_email,
                    event_ids=[e.id for e in user_events],
                    metadata={
                        'export_count': len(user_events),
                    },
                    recommended_action="Verify large data export is authorized"
                )
                alerts.append(alert)
        
        return alerts
    
    @staticmethod
    async def _check_gdpr_requests(
        events: List[AuditEvent],
        tenant_id: str
    ) -> List[Alert]:
        """Detect and alert on GDPR requests"""
        alerts = []
        
        gdpr_events = [
            e for e in events
            if e.event_type in [
                AuditEventType.GDPR_DATA_EXPORT,
                AuditEventType.GDPR_DATA_DELETE
            ]
        ]
        
        for event in gdpr_events:
            severity = AlertSeverity.HIGH
            action = "Data Export Request"
            
            if event.event_type == AuditEventType.GDPR_DATA_DELETE:
                severity = AlertSeverity.CRITICAL
                action = "Data Deletion Request"
            
            alert = Alert(
                id=f"gdpr_{event.id}",
                alert_type=AlertType.GDPR_REQUEST,
                severity=severity,
                timestamp=event.timestamp,
                tenant_id=tenant_id,
                title=f"GDPR Request: {action}",
                description=f"User {event.user_email} requested {action.lower()}",
                user_email=event.user_email,
                resource_type="gdpr_request",
                resource_id=event.user_email,
                event_ids=[event.id],
                metadata={
                    'request_type': action,
                    'timestamp': event.timestamp
                },
                recommended_action="Process GDPR request according to policy within 30 days"
            )
            alerts.append(alert)
        
        return alerts
    
    @staticmethod
    async def _check_admin_actions(
        events: List[AuditEvent],
        tenant_id: str
    ) -> List[Alert]:
        """Alert on sensitive admin actions"""
        alerts = []
        
        admin_events = [
            e for e in events
            if e.event_type in [
                AuditEventType.USER_DELETED,
                AuditEventType.ROLE_CHANGED,
                AuditEventType.CONFIGURATION_CHANGED
            ]
        ]
        
        for event in admin_events:
            alert = Alert(
                id=f"admin_{event.id}",
                alert_type=AlertType.ADMIN_ACTION,
                severity=AlertSeverity.HIGH,
                timestamp=event.timestamp,
                tenant_id=tenant_id,
                title=f"Admin Action: {event.action}",
                description=f"Admin {event.user_email} performed {event.action} on {event.resource_id}",
                user_email=event.user_email,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                event_ids=[event.id],
                metadata={
                    'action': event.action,
                    'affected_resource': event.resource_id
                },
                recommended_action="Log and review sensitive admin action"
            )
            alerts.append(alert)
        
        return alerts
    
    @staticmethod
    async def _trigger_alert(alert: Alert) -> None:
        """Trigger alert handlers for notification"""
        
        # Log with appropriate level
        log_level = {
            AlertSeverity.CRITICAL: logging.CRITICAL,
            AlertSeverity.HIGH: logging.ERROR,
            AlertSeverity.MEDIUM: logging.WARNING,
            AlertSeverity.LOW: logging.INFO,
        }[alert.severity]
        
        logger.log(
            log_level,
            f"[{alert.alert_type.value}] {alert.title}: {alert.description}"
        )
        
        # Call registered handlers
        handlers = AlertService._alert_handlers.get(alert.alert_type, [])
        for handler in handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
    
    @staticmethod
    def register_handler(alert_type: AlertType, handler: Callable) -> None:
        """Register a handler for alert type
        
        Args:
            alert_type: Type of alert
            handler: Async callable(alert) -> None
        """
        if alert_type not in AlertService._alert_handlers:
            AlertService._alert_handlers[alert_type] = []
        
        AlertService._alert_handlers[alert_type].append(handler)
    
    @staticmethod
    async def get_alerts(
        tenant_id: str,
        alert_type: Optional[AlertType] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 100
    ) -> List[Alert]:
        """Get alerts for tenant
        
        Args:
            tenant_id: Tenant to get alerts for
            alert_type: Optional filter by type
            severity: Optional filter by severity
            limit: Maximum results
            
        Returns:
            List of alerts
        """
        alerts = [
            a for a in AlertService._alerts
            if a.tenant_id == tenant_id
            and (not alert_type or a.alert_type == alert_type)
            and (not severity or a.severity == severity)
            and not a.dismissed
        ]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)[:limit]
    
    @staticmethod
    async def dismiss_alert(alert_id: str) -> bool:
        """Dismiss an alert
        
        Args:
            alert_id: ID of alert to dismiss
            
        Returns:
            Whether alert was found and dismissed
        """
        for alert in AlertService._alerts:
            if alert.id == alert_id:
                alert.dismissed = True
                return True
        return False
    
    @staticmethod
    async def resolve_alert(alert_id: str) -> bool:
        """Mark alert as resolved
        
        Args:
            alert_id: ID of alert to resolve
            
        Returns:
            Whether alert was found and resolved
        """
        for alert in AlertService._alerts:
            if alert.id == alert_id:
                alert.resolved = True
                return True
        return False
