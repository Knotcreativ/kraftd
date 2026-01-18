"""
Admin Routes - Administrative endpoints with role-based access control

Restricted to ADMIN users only. Provides user management and system operations.
"""

import logging
from typing import List, Tuple
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status

from models.user import User, UserRole, UserProfile
from middleware.rbac import require_admin, get_current_user_with_role
from services.rbac_service import RBACService

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
    List all users (ADMIN only)
    
    Returns a list of all users in the system.
    """
    admin_email, admin_role = current_user
    
    logger.info(f"Admin {admin_email} listing all users")
    
    return [
        UserProfile(
            email=user.email,
            name=user.name or "N/A",
            organization="N/A",  # Would come from user object
            created_at=user.created_at,
            is_active=user.is_active
        )
        for user in users_db.values()
    ]


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user_detail(
    user_id: str,
    current_user: Tuple[str, UserRole] = Depends(require_admin)
):
    """
    Get detailed user information (ADMIN only)
    
    Args:
        user_id: User email (used as ID)
    """
    admin_email, admin_role = current_user
    
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = users_db[user_id]
    
    logger.info(f"Admin {admin_email} viewing user: {user_id}")
    
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
    
    Allows changing a user's role (admin, user, viewer, guest).
    
    Args:
        user_id: User email
        new_role: New role to assign
    """
    admin_email, admin_role = current_user
    
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = users_db[user_id]
    old_role = user.role
    user.role = new_role
    user.updated_at = datetime.utcnow()
    
    logger.warning(
        f"Admin {admin_email} changed user {user_id} role from {old_role.value} to {new_role.value}"
    )
    
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
    
    Args:
        user_id: User email
        is_active: True to enable, False to disable
    """
    admin_email, admin_role = current_user
    
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = users_db[user_id]
    old_status = user.is_active
    user.is_active = is_active
    user.updated_at = datetime.utcnow()
    
    action = "enabled" if is_active else "disabled"
    logger.warning(f"Admin {admin_email} {action} user: {user_id}")
    
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
    
    Permanently removes a user from the system.
    
    Args:
        user_id: User email
    """
    admin_email, admin_role = current_user
    
    # Prevent admin from deleting self
    if user_id == admin_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    del users_db[user_id]
    
    logger.warning(f"Admin {admin_email} deleted user: {user_id}")
    
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
    current_user: Tuple[str, UserRole] = Depends(require_admin)
):
    """
    Get authorization decision logs (ADMIN only)
    
    Shows recent authorization decisions for audit purposes.
    
    Args:
        limit: Maximum number of logs to return
    """
    admin_email, admin_role = current_user
    
    logger.info(f"Admin {admin_email} requesting authorization logs (limit: {limit})")
    
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
