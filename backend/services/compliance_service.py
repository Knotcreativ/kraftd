"""Compliance Reporting Service

Generates compliance reports from audit logs for:
- GDPR data subject access requests
- SOC2 audit trails
- Access control verification
- Data change tracking
- Security incident investigation
- User activity analysis

Report Types:
1. Access Audit Report - Who accessed what, when, from where
2. Data Change Report - Complete audit trail of modifications
3. User Activity Report - Login patterns, actions per user
4. Security Events Report - Failed access, unauthorized attempts, alerts
5. GDPR/Privacy Report - Data exports, deletions, consent changes
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from collections import defaultdict

from .audit_service import AuditService, AuditEvent, AuditEventType, AuditResult


@dataclass
class ComplianceReport:
    """Base compliance report"""
    report_id: str
    report_type: str
    generated_at: str
    generated_by: Optional[str]
    tenant_id: str
    period_start: Optional[str]
    period_end: Optional[str]
    summary: Dict[str, Any]
    details: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class ComplianceReportService:
    """Service for generating compliance reports from audit logs"""
    
    @staticmethod
    async def generate_access_audit_report(
        tenant_id: str,
        period_days: int = 30,
        include_failed: bool = True
    ) -> ComplianceReport:
        """Generate access audit report
        
        Shows who accessed what resources, when, and the outcome.
        Essential for SOC2 and regulatory compliance.
        
        Args:
            tenant_id: Tenant to report on
            period_days: Days of history to include
            include_failed: Include failed access attempts
            
        Returns:
            ComplianceReport with access details
        """
        events = await AuditService.get_events(
            tenant_id=tenant_id,
            limit=10000
        )
        
        # Filter to access events in period
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=period_days)
        access_events = [
            e for e in events
            if e.event_type == AuditEventType.RESOURCE_READ
            and (include_failed or e.allowed)
            and datetime.fromisoformat(e.timestamp.replace('Z', '+00:00')) > cutoff
        ]
        
        # Group by user
        by_user = defaultdict(list)
        for event in access_events:
            by_user[event.user_email].append(event)
        
        # Build summary
        summary = {
            'total_access_events': len(access_events),
            'unique_users': len(by_user),
            'failed_access_attempts': len([e for e in access_events if not e.allowed]),
            'resource_types_accessed': len(set(e.resource_type for e in access_events if e.resource_type))
        }
        
        # Build details
        details = []
        for user_email, user_events in by_user.items():
            details.append({
                'user': user_email,
                'access_count': len(user_events),
                'failed_attempts': len([e for e in user_events if not e.allowed]),
                'resource_types': list(set(e.resource_type for e in user_events if e.resource_type)),
                'first_access': min(e.timestamp for e in user_events),
                'last_access': max(e.timestamp for e in user_events),
            })
        
        report = ComplianceReport(
            report_id='access_audit_' + datetime.now(tz=timezone.utc).isoformat(),
            report_type='ACCESS_AUDIT',
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
            generated_by=None,
            tenant_id=tenant_id,
            period_start=(datetime.now(tz=timezone.utc) - timedelta(days=period_days)).isoformat(),
            period_end=datetime.now(tz=timezone.utc).isoformat(),
            summary=summary,
            details=details,
            metadata={'period_days': period_days, 'include_failed': include_failed}
        )
        
        return report
    
    @staticmethod
    async def generate_data_change_report(
        tenant_id: str,
        resource_type: Optional[str] = None,
        period_days: int = 30
    ) -> ComplianceReport:
        """Generate data change audit trail
        
        Complete record of all data modifications with before/after values.
        Required for data governance and change management.
        
        Args:
            tenant_id: Tenant to report on
            resource_type: Optional specific resource type
            period_days: Days of history to include
            
        Returns:
            ComplianceReport with change details
        """
        events = await AuditService.get_events(
            tenant_id=tenant_id,
            limit=10000
        )
        
        # Filter to modification events
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=period_days)
        change_events = [
            e for e in events
            if e.event_type in [
                AuditEventType.RESOURCE_CREATE,
                AuditEventType.RESOURCE_UPDATE,
                AuditEventType.RESOURCE_DELETE,
            ]
            and (not resource_type or e.resource_type == resource_type)
            and datetime.fromisoformat(e.timestamp.replace('Z', '+00:00')) > cutoff
        ]
        
        # Group by resource
        by_resource = defaultdict(list)
        for event in change_events:
            key = f"{event.resource_type}:{event.resource_id}"
            by_resource[key].append(event)
        
        # Build summary
        summary = {
            'total_changes': len(change_events),
            'creates': len([e for e in change_events if e.event_type == AuditEventType.RESOURCE_CREATE]),
            'updates': len([e for e in change_events if e.event_type == AuditEventType.RESOURCE_UPDATE]),
            'deletes': len([e for e in change_events if e.event_type == AuditEventType.RESOURCE_DELETE]),
            'resources_modified': len(by_resource),
            'users_making_changes': len(set(e.user_email for e in change_events if e.user_email))
        }
        
        # Build details
        details = []
        for resource_key, resource_events in by_resource.items():
            for event in sorted(resource_events, key=lambda e: e.timestamp):
                details.append({
                    'timestamp': event.timestamp,
                    'user': event.user_email,
                    'resource': resource_key,
                    'action': event.action,
                    'event_type': event.event_type.value,
                    'changes': event.changes,
                    'ip_address': event.ip_address,
                })
        
        report = ComplianceReport(
            report_id='data_change_' + datetime.now(tz=timezone.utc).isoformat(),
            report_type='DATA_CHANGE',
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
            generated_by=None,
            tenant_id=tenant_id,
            period_start=(datetime.now(tz=timezone.utc) - timedelta(days=period_days)).isoformat(),
            period_end=datetime.now(tz=timezone.utc).isoformat(),
            summary=summary,
            details=details,
            metadata={'period_days': period_days, 'resource_type': resource_type}
        )
        
        return report
    
    @staticmethod
    async def generate_user_activity_report(
        tenant_id: str,
        user_email: Optional[str] = None,
        period_days: int = 30
    ) -> ComplianceReport:
        """Generate user activity report
        
        Login patterns, actions performed, activity analysis.
        Shows user behavior and access patterns.
        
        Args:
            tenant_id: Tenant to report on
            user_email: Optional specific user
            period_days: Days of history to include
            
        Returns:
            ComplianceReport with activity details
        """
        events = await AuditService.get_events(
            tenant_id=tenant_id,
            user_email=user_email,
            limit=10000
        )
        
        # Filter to period
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=period_days)
        activity_events = [
            e for e in events
            if datetime.fromisoformat(e.timestamp.replace('Z', '+00:00')) > cutoff
        ]
        
        # Group by user
        by_user = defaultdict(list)
        for event in activity_events:
            by_user[event.user_email].append(event)
        
        # Build summary
        summary = {
            'total_events': len(activity_events),
            'active_users': len(by_user),
            'logins': len([e for e in activity_events if e.event_type in [
                AuditEventType.LOGIN_SUCCESS,
                AuditEventType.LOGIN_FAILED
            ]]),
            'modifications': len([e for e in activity_events if e.event_type in [
                AuditEventType.RESOURCE_CREATE,
                AuditEventType.RESOURCE_UPDATE,
                AuditEventType.RESOURCE_DELETE,
            ]]),
            'failed_access_attempts': len([e for e in activity_events if not e.allowed])
        }
        
        # Build details
        details = []
        for user, user_events in by_user.items():
            user_details = {
                'user': user,
                'total_events': len(user_events),
                'logins': len([e for e in user_events if 'LOGIN' in e.event_type.value]),
                'reads': len([e for e in user_events if e.event_type == AuditEventType.RESOURCE_READ]),
                'modifications': len([e for e in user_events if 'UPDATE' in e.event_type.value or 'CREATE' in e.event_type.value]),
                'failed_access': len([e for e in user_events if not e.allowed]),
                'first_activity': min(e.timestamp for e in user_events) if user_events else None,
                'last_activity': max(e.timestamp for e in user_events) if user_events else None,
            }
            
            if user_events:
                # Find unusual patterns
                login_events = [e for e in user_events if 'LOGIN' in e.event_type.value]
                if login_events:
                    user_details['unusual_login_times'] = _find_unusual_times(login_events)
            
            details.append(user_details)
        
        report = ComplianceReport(
            report_id='user_activity_' + datetime.now(tz=timezone.utc).isoformat(),
            report_type='USER_ACTIVITY',
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
            generated_by=None,
            tenant_id=tenant_id,
            period_start=(datetime.now(tz=timezone.utc) - timedelta(days=period_days)).isoformat(),
            period_end=datetime.now(tz=timezone.utc).isoformat(),
            summary=summary,
            details=details,
            metadata={'period_days': period_days, 'user_email': user_email}
        )
        
        return report
    
    @staticmethod
    async def generate_security_events_report(
        tenant_id: str,
        period_days: int = 30
    ) -> ComplianceReport:
        """Generate security events report
        
        Failed access attempts, unauthorized actions, suspicious activities.
        Used for security investigations and incident response.
        
        Args:
            tenant_id: Tenant to report on
            period_days: Days of history to include
            
        Returns:
            ComplianceReport with security events
        """
        events = await AuditService.get_events(
            tenant_id=tenant_id,
            limit=10000
        )
        
        # Filter to security events
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=period_days)
        security_events = [
            e for e in events
            if (e.event_type in [
                AuditEventType.LOGIN_FAILED,
                AuditEventType.UNAUTHORIZED_ACCESS,
                AuditEventType.CROSS_TENANT_ACCESS,
                AuditEventType.BRUTE_FORCE_ATTEMPT,
                AuditEventType.PRIVILEGE_ESCALATION,
                AuditEventType.SUSPICIOUS_ACTIVITY,
                AuditEventType.TOKEN_VALIDATION_FAILED,
            ] or not e.allowed)
            and datetime.fromisoformat(e.timestamp.replace('Z', '+00:00')) > cutoff
        ]
        
        # Group by type
        by_type = defaultdict(list)
        by_user = defaultdict(list)
        for event in security_events:
            by_type[event.event_type.value].append(event)
            if event.user_email:
                by_user[event.user_email].append(event)
        
        # Build summary
        summary = {
            'total_security_events': len(security_events),
            'event_types': len(by_type),
            'affected_users': len(by_user),
            'failed_logins': len([e for e in security_events if e.event_type == AuditEventType.LOGIN_FAILED]),
            'unauthorized_access': len([e for e in security_events if e.event_type == AuditEventType.UNAUTHORIZED_ACCESS]),
            'cross_tenant_attempts': len([e for e in security_events if e.event_type == AuditEventType.CROSS_TENANT_ACCESS]),
            'privilege_escalation_attempts': len([e for e in security_events if e.event_type == AuditEventType.PRIVILEGE_ESCALATION]),
        }
        
        # Build details
        details = []
        for event in sorted(security_events, key=lambda e: e.timestamp, reverse=True)[:100]:
            details.append({
                'timestamp': event.timestamp,
                'event_type': event.event_type.value,
                'user': event.user_email or 'unknown',
                'resource': f"{event.resource_type}/{event.resource_id}" if event.resource_type else None,
                'allowed': event.allowed,
                'reason': event.reason,
                'ip_address': event.ip_address,
            })
        
        report = ComplianceReport(
            report_id='security_' + datetime.now(tz=timezone.utc).isoformat(),
            report_type='SECURITY_EVENTS',
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
            generated_by=None,
            tenant_id=tenant_id,
            period_start=(datetime.now(tz=timezone.utc) - timedelta(days=period_days)).isoformat(),
            period_end=datetime.now(tz=timezone.utc).isoformat(),
            summary=summary,
            details=details,
            metadata={'period_days': period_days}
        )
        
        return report
    
    @staticmethod
    async def generate_gdpr_report(
        tenant_id: str,
        user_email: Optional[str] = None,
        period_days: int = 365
    ) -> ComplianceReport:
        """Generate GDPR/Privacy compliance report
        
        Data subject access requests, data deletions, consent changes.
        Required for GDPR Article 15 (subject access rights).
        
        Args:
            tenant_id: Tenant to report on
            user_email: Optional specific user for SAR
            period_days: Days of history to include
            
        Returns:
            ComplianceReport with privacy data
        """
        events = await AuditService.get_events(
            tenant_id=tenant_id,
            limit=10000
        )
        
        # Filter to privacy-relevant events
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=period_days)
        privacy_events = [
            e for e in events
            if e.event_type in [
                AuditEventType.GDPR_DATA_EXPORT,
                AuditEventType.GDPR_DATA_DELETE,
                AuditEventType.CONSENT_GRANTED,
                AuditEventType.CONSENT_REVOKED,
                AuditEventType.EMAIL_VERIFIED,
                AuditEventType.PASSWORD_RESET,
            ]
            and (not user_email or e.user_email == user_email)
            and datetime.fromisoformat(e.timestamp.replace('Z', '+00:00')) > cutoff
        ]
        
        # Build summary
        summary = {
            'total_privacy_events': len(privacy_events),
            'data_exports': len([e for e in privacy_events if e.event_type == AuditEventType.GDPR_DATA_EXPORT]),
            'data_deletions': len([e for e in privacy_events if e.event_type == AuditEventType.GDPR_DATA_DELETE]),
            'consents_granted': len([e for e in privacy_events if e.event_type == AuditEventType.CONSENT_GRANTED]),
            'consents_revoked': len([e for e in privacy_events if e.event_type == AuditEventType.CONSENT_REVOKED]),
        }
        
        # Build details
        details = []
        for event in sorted(privacy_events, key=lambda e: e.timestamp, reverse=True):
            details.append({
                'timestamp': event.timestamp,
                'event_type': event.event_type.value,
                'user': event.user_email,
                'action': event.action,
                'details': event.details or {},
            })
        
        report = ComplianceReport(
            report_id='gdpr_' + datetime.now(tz=timezone.utc).isoformat(),
            report_type='GDPR_PRIVACY',
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
            generated_by=None,
            tenant_id=tenant_id,
            period_start=(datetime.now(tz=timezone.utc) - timedelta(days=period_days)).isoformat(),
            period_end=datetime.now(tz=timezone.utc).isoformat(),
            summary=summary,
            details=details,
            metadata={'period_days': period_days, 'user_email': user_email}
        )
        
        return report


def _find_unusual_times(events: List[AuditEvent]) -> List[str]:
    """Find login times outside normal business hours"""
    unusual = []
    
    for event in events:
        try:
            ts = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
            hour = ts.hour
            weekday = ts.weekday()
            
            # Flag off-hours (before 6 AM or after 10 PM)
            if hour < 6 or hour > 22:
                unusual.append(event.timestamp)
            
            # Flag weekend activity
            if weekday >= 5:  # Saturday/Sunday
                unusual.append(event.timestamp)
        except:
            pass
    
    return unusual[:10]  # Return first 10 unusual times
