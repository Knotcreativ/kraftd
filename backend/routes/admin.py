"""
Admin Routes - Administrative endpoints with role-based access control

Restricted to ADMIN users only. Provides user management and system operations.

Task 8 Integration: Audit logging for all admin operations (Role changes, Status changes, Deletions)
"""

import logging
from typing import List, Tuple
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status, Request

from models.user import User, UserRole, UserProfile
from middleware.rbac import require_admin, get_current_user_with_role
from services.rbac_service import RBACService
from services.tenant_service import TenantService
from services.audit_service import AuditService, AuditEventType, AuditEvent, AuditResult
from utils.query_scope import QueryScope

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

# Temporary in-memory user store (would use Cosmos DB in production)
users_db = {}


# ===== User Management Endpoints =====

@router.get("/users", response_model=List[UserProfile])
async def list_all_users(
    current_user: Tuple[str, UserRole] = Depends(require_admin)
):
    """
    List all users within current tenant (ADMIN only)
    
    Returns a list of all users in the current tenant.
    Cross-tenant access is prevented through automatic tenant scoping.
    """
    admin_email, admin_role = current_user
    
    # Get current tenant context
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
    
    logger.info(f"Admin {admin_email} listing users for tenant {current_tenant}")
    
    # Filter users by tenant (in-memory for now, would be scoped query in production)
    tenant_users = [
        UserProfile(
            email=user.email,
            name=user.name or "N/A",
            organization="N/A",  # Would come from user object
            created_at=user.created_at,
            is_active=user.is_active
        )
        for user in users_db.values()
        if getattr(user, 'tenant_id', None) == current_tenant
    ]
    
    return tenant_users


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user_detail(
    user_id: str,
    current_user: Tuple[str, UserRole] = Depends(require_admin)
):
    """
    Get detailed user information (ADMIN only)
    
    Validates that the requested user belongs to the current tenant.
    Returns 404 if user is in a different tenant (prevents tenant enumeration).
    
    Args:
        user_id: User email (used as ID)
    """
    admin_email, admin_role = current_user
    
    # Get current tenant context
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
    
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = users_db[user_id]
    
    # Verify user belongs to current tenant (prevent cross-tenant access)
    user_tenant = getattr(user, 'tenant_id', None)
    if user_tenant != current_tenant:
        logger.warning(
            f"Admin {admin_email} attempted to access user {user_id} from different tenant. "
            f"Expected: {current_tenant}, User's tenant: {user_tenant}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"  # Don't reveal tenant mismatch
        )
    
    logger.info(f"Admin {admin_email} viewing user: {user_id} in tenant {current_tenant}")
    
    return UserProfile(
        email=user.email,
        name=user.name or "N/A",
        organization="N/A",
        created_at=user.created_at,
        is_active=user.is_active
    )


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    new_role: UserRole,
    current_user: Tuple[str, UserRole] = Depends(require_admin)
):
    """
    Update user role (ADMIN only)
    
    Task 4 Integration: Validates tenant context (TenantService)
    Task 5 Integration: Admin-only resource ownership (only admins can modify users)
    
    Allows changing a user's role (admin, user, viewer, guest).
    
    Args:
        user_id: User email
        new_role: New role to assign
    """
    admin_email, admin_role = current_user
    
    # Task 4: Validate tenant context
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
    
    # Task 5: Verify user exists and belongs to current tenant
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = users_db[user_id]
    user_tenant = getattr(user, 'tenant_id', None)
    
    # Prevent cross-tenant modifications
    if user_tenant and user_tenant != current_tenant:
        logger.warning(
            f"Cross-tenant role change attempt: admin {admin_email} "
            f"({current_tenant}) attempted to modify user {user_id} ({user_tenant})"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"  # 404 to prevent enumeration
        )
    
    # Prevent admin from changing own role
    if user_id == admin_email and new_role != admin_role:
        logger.warning(
            f"Admin {admin_email} attempted to change their own role"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    # Perform role change
    old_role = user.role
    user.role = new_role
    user.updated_at = datetime.utcnow()
    
    # Log authorization decision
    rbac_service = RBACService()
    rbac_service.log_authorization_decision(
        user_email=admin_email,
        user_role=admin_role,
        resource="user",
        resource_id=user_id,
        action="update_role",
        allowed=True
    )
    
    logger.warning(
        f"Admin {admin_email} in tenant {current_tenant} changed user {user_id} "
        f"role from {old_role.value} to {new_role.value}"
    )
    
    # Log role change for audit trail (HIGH severity - privilege escalation risk)
    try:
        tenant_id = TenantService.get_current_tenant() or "default"
        
        await AuditService.log_modification(
            user_email=admin_email,
            user_role=admin_role,
            resource_type="user_role",
            resource_id=user_id,
            tenant_id=tenant_id,
            action="change_role",
            changes={
                "old_role": old_role.value,
                "new_role": new_role.value
            },
            ip_address=None,
            severity="HIGH"  # Privilege escalation risk
        )
    except Exception as audit_error:
        logger.error(f"Error logging role change audit event: {audit_error}")
    
    return {
        "message": f"User role updated from {old_role.value} to {new_role.value}",
        "user_id": user_id,
        "old_role": old_role.value,
        "new_role": new_role.value
    }


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    current_user: Tuple[str, UserRole] = Depends(require_admin)
):
    """
    Enable or disable user account (ADMIN only)
    
    Task 4 Integration: Validates tenant context (TenantService)
    Task 5 Integration: Admin-only resource ownership (only admins can modify users)
    
    Args:
        user_id: User email
        is_active: True to enable, False to disable
    """
    admin_email, admin_role = current_user
    
    # Task 4: Validate tenant context
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
    
    # Task 5: Verify user exists and belongs to current tenant
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = users_db[user_id]
    user_tenant = getattr(user, 'tenant_id', None)
    
    # Prevent cross-tenant modifications
    if user_tenant and user_tenant != current_tenant:
        logger.warning(
            f"Cross-tenant status change attempt: admin {admin_email} "
            f"({current_tenant}) attempted to modify user {user_id} ({user_tenant})"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"  # 404 to prevent enumeration
        )
    
    # Perform status change
    old_status = user.is_active
    user.is_active = is_active
    user.updated_at = datetime.utcnow()
    
    action = "enabled" if is_active else "disabled"
    
    # Log authorization decision
    rbac_service = RBACService()
    rbac_service.log_authorization_decision(
        user_email=admin_email,
        user_role=admin_role,
        resource="user",
        resource_id=user_id,
        action="update_status",
        allowed=True
    )
    
    logger.warning(
        f"Admin {admin_email} in tenant {current_tenant} {action} user: {user_id}"
    )
    
    # Log status change for audit trail (HIGH severity - account access control)
    try:
        tenant_id = TenantService.get_current_tenant() or "default"
        
        await AuditService.log_modification(
            user_email=admin_email,
            user_role=admin_role,
            resource_type="user_status",
            resource_id=user_id,
            tenant_id=tenant_id,
            action="change_status",
            changes={
                "old_status": "active" if old_status else "disabled",
                "new_status": "active" if is_active else "disabled"
            },
            ip_address=None,
            severity="HIGH"  # Account access control
        )
    except Exception as audit_error:
        logger.error(f"Error logging status change audit event: {audit_error}")
    
    return {
        "message": f"User account {action}",
        "user_id": user_id,
        "is_active": is_active
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Tuple[str, UserRole] = Depends(require_admin)
):
    """
    Delete a user (ADMIN only)
    
    Task 4 Integration: Validates tenant context (TenantService)
    Task 5 Integration: Admin-only resource ownership (only admins can delete users)
    
    Permanently removes a user from the system.
    
    Args:
        user_id: User email
    """
    admin_email, admin_role = current_user
    
    # Task 4: Validate tenant context
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
    
    # Prevent admin from deleting self
    if user_id == admin_email:
        logger.warning(
            f"Admin {admin_email} attempted to delete their own account in tenant {current_tenant}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Task 5: Verify user exists and belongs to current tenant
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = users_db[user_id]
    user_tenant = getattr(user, 'tenant_id', None)
    
    # Prevent cross-tenant deletion
    if user_tenant and user_tenant != current_tenant:
        logger.warning(
            f"Cross-tenant deletion attempt: admin {admin_email} "
            f"({current_tenant}) attempted to delete user {user_id} ({user_tenant})"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"  # 404 to prevent enumeration
        )
    
    # Perform deletion
    del users_db[user_id]
    
    # Log authorization decision
    rbac_service = RBACService()
    rbac_service.log_authorization_decision(
        user_email=admin_email,
        user_role=admin_role,
        resource="user",
        resource_id=user_id,
        action="delete",
        allowed=True
    )
    
    logger.warning(
        f"Admin {admin_email} in tenant {current_tenant} deleted user: {user_id}"
    )
    
    # Log user deletion for audit trail (CRITICAL severity - user removal)
    try:
        tenant_id = TenantService.get_current_tenant() or "default"
        
        await AuditService.log_modification(
            user_email=admin_email,
            user_role=admin_role,
            resource_type="user",
            resource_id=user_id,
            tenant_id=tenant_id,
            action="delete",
            changes={
                "deleted_user": user_id,
                "deletion_reason": "admin_initiated"
            },
            ip_address=None,
            severity="CRITICAL"  # User removal - highest severity
        )
    except Exception as audit_error:
        logger.error(f"Error logging user deletion audit event: {audit_error}")
    
    return {
        "message": "User deleted successfully",
        "user_id": user_id
    }


# ===== Role Management =====

@router.get("/roles")
async def list_roles(
    current_user: Tuple[str, UserRole] = Depends(require_admin)
):
    """
    List all available roles (ADMIN only)
    
    Returns information about each role and its permissions.
    """
    admin_email, admin_role = current_user
    
    roles_info = []
    
    for role in UserRole:
        permissions = RBACService.get_permissions(role)
        
        roles_info.append({
            "role": role.value,
            "description": f"{role.value.capitalize()} role",
            "permissions_count": len(permissions),
            "permissions": [p.value for p in permissions]
        })
    
    return {
        "roles": roles_info,
        "total_roles": len(roles_info)
    }


@router.get("/roles/{role_name}")
async def get_role_permissions(
    role_name: str,
    current_user: Tuple[str, UserRole] = Depends(require_admin)
):
    """
    Get permissions for a specific role (ADMIN only)
    
    Args:
        role_name: Role name (admin, user, viewer, guest)
    """
    admin_email, admin_role = current_user
    
    try:
        role = UserRole(role_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role_name}"
        )
    
    permissions = RBACService.get_permissions(role)
    
    return {
        "role": role.value,
        "permissions": [p.value for p in permissions],
        "total": len(permissions)
    }


# ===== Audit & Logging =====

@router.get("/logs/authorization")
async def get_authorization_logs(
    limit: int = 100,
    current_user: Tuple[str, UserRole] = Depends(require_admin),
    request: Request = None
):
    """
    Get authorization decision logs (ADMIN only)
    
    Shows recent authorization decisions for audit purposes.
    
    Task 8 Integration: Logs access to authorization logs (audit log access tracking)

    Args:
        limit: Maximum number of logs to return
    """
    admin_email, admin_role = current_user
    
    logger.info(f"Admin {admin_email} requesting authorization logs (limit: {limit})")
    
    # Log authorization logs access for audit trail (HIGH severity - sensitive logs)
    try:
        client_ip = request.client.host if request and request.client else None
        tenant_id = TenantService.get_current_tenant() or "default"
        
        await AuditService.log_access(
            user_email=admin_email,
            user_role=admin_role,
            resource_type="authorization_logs",
            resource_id="audit_logs",
            tenant_id=tenant_id,
            action="access",
            ip_address=client_ip,
            details={
                "limit": limit,
                "access_type": "authorization_logs_query"
            }
        )
    except Exception as audit_error:
        logger.error(f"Error logging authorization logs access audit event: {audit_error}")
    
    # This would query the authorization log in production
    return {
        "message": "Authorization logs",
        "limit": limit,
        "logs": []  # Would be populated from log storage
    }


@router.get("/system/stats")
async def get_system_stats(
    current_user: Tuple[str, UserRole] = Depends(require_admin)
):
    """
    Get system statistics (ADMIN only)
    
    Returns counts of users, roles, active sessions, etc.
    """
    admin_email, admin_role = current_user
    
    # Count users by role
    role_counts = {}
    for user in users_db.values():
        role = user.role.value
        role_counts[role] = role_counts.get(role, 0) + 1
    
    logger.info(f"Admin {admin_email} viewing system stats")
    
    return {
        "total_users": len(users_db),
        "active_users": sum(1 for u in users_db.values() if u.is_active),
        "disabled_users": sum(1 for u in users_db.values() if not u.is_active),
        "users_by_role": role_counts,
        "timestamp": datetime.utcnow().isoformat()
    }
