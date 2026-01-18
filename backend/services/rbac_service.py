"""
RBAC Service - Role-Based Access Control

Implements role-based permission matrix for KraftdIntel.

Roles:
- ADMIN: Full system access
- USER: Standard user (create, read, update own resources)
- VIEWER: Read-only access
- GUEST: Unauthenticated access
"""

import logging
from enum import Enum
from typing import Set, Dict, Optional

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"       # Full system access
    USER = "user"         # Standard user (default)
    VIEWER = "viewer"     # Read-only access
    GUEST = "guest"       # Unauthenticated access


class Permission(str, Enum):
    """Fine-grained permissions for endpoints
    
    Format: resource:action
    - resource: auth, users, documents, workflows, templates, admin
    - action: register, login, logout, read, write, delete, admin
    """
    
    # Authentication
    AUTH_REGISTER = "auth:register"
    AUTH_LOGIN = "auth:login"
    AUTH_LOGOUT = "auth:logout"
    AUTH_PROFILE = "auth:profile"
    AUTH_REFRESH = "auth:refresh"
    
    # User Management
    USERS_READ_SELF = "users:read_self"
    USERS_READ_ALL = "users:read_all"
    USERS_WRITE_SELF = "users:write_self"
    USERS_WRITE_ALL = "users:write_all"
    USERS_DELETE = "users:delete"
    
    # Documents
    DOCUMENTS_CREATE = "documents:create"
    DOCUMENTS_READ_OWN = "documents:read_own"
    DOCUMENTS_READ_ALL = "documents:read_all"
    DOCUMENTS_UPDATE_OWN = "documents:update_own"
    DOCUMENTS_UPDATE_ALL = "documents:update_all"
    DOCUMENTS_DELETE_OWN = "documents:delete_own"
    DOCUMENTS_DELETE_ALL = "documents:delete_all"
    
    # Workflows
    WORKFLOWS_CREATE = "workflows:create"
    WORKFLOWS_READ_OWN = "workflows:read_own"
    WORKFLOWS_READ_ALL = "workflows:read_all"
    WORKFLOWS_EXECUTE_OWN = "workflows:execute_own"
    WORKFLOWS_EXECUTE_ALL = "workflows:execute_all"
    WORKFLOWS_DELETE_OWN = "workflows:delete_own"
    WORKFLOWS_DELETE_ALL = "workflows:delete_all"
    
    # Templates
    TEMPLATES_READ = "templates:read"
    TEMPLATES_READ_PUBLIC = "templates:read_public"
    TEMPLATES_CREATE = "templates:create"
    TEMPLATES_UPDATE = "templates:update"
    TEMPLATES_DELETE = "templates:delete"
    
    # Admin
    ADMIN_USERS = "admin:users"
    ADMIN_SETTINGS = "admin:settings"
    ADMIN_LOGS = "admin:logs"
    ADMIN_SYSTEM = "admin:system"
    
    # Reporting
    REPORTS_EXPORT = "reports:export"
    REPORTS_VIEW = "reports:view"
    
    # Streaming/Signals
    ALERTS_READ = "alerts:read"
    PRICES_READ = "prices:read"
    SIGNALS_READ = "signals:read"
    TRENDS_READ = "trends:read"
    ANOMALIES_READ = "anomalies:read"


class RBACService:
    """Service for role-based access control
    
    Manages permissions matrix and authorization checks.
    """
    
    # Permission matrix: maps roles to their allowed permissions
    ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
        UserRole.ADMIN: {
            # Authentication (all)
            Permission.AUTH_REGISTER,
            Permission.AUTH_LOGIN,
            Permission.AUTH_LOGOUT,
            Permission.AUTH_PROFILE,
            Permission.AUTH_REFRESH,
            
            # User Management (all)
            Permission.USERS_READ_SELF,
            Permission.USERS_READ_ALL,
            Permission.USERS_WRITE_SELF,
            Permission.USERS_WRITE_ALL,
            Permission.USERS_DELETE,
            
            # Documents (all)
            Permission.DOCUMENTS_CREATE,
            Permission.DOCUMENTS_READ_OWN,
            Permission.DOCUMENTS_READ_ALL,
            Permission.DOCUMENTS_UPDATE_OWN,
            Permission.DOCUMENTS_UPDATE_ALL,
            Permission.DOCUMENTS_DELETE_OWN,
            Permission.DOCUMENTS_DELETE_ALL,
            
            # Workflows (all)
            Permission.WORKFLOWS_CREATE,
            Permission.WORKFLOWS_READ_OWN,
            Permission.WORKFLOWS_READ_ALL,
            Permission.WORKFLOWS_EXECUTE_OWN,
            Permission.WORKFLOWS_EXECUTE_ALL,
            Permission.WORKFLOWS_DELETE_OWN,
            Permission.WORKFLOWS_DELETE_ALL,
            
            # Templates (all)
            Permission.TEMPLATES_READ,
            Permission.TEMPLATES_READ_PUBLIC,
            Permission.TEMPLATES_CREATE,
            Permission.TEMPLATES_UPDATE,
            Permission.TEMPLATES_DELETE,
            
            # Admin (all)
            Permission.ADMIN_USERS,
            Permission.ADMIN_SETTINGS,
            Permission.ADMIN_LOGS,
            Permission.ADMIN_SYSTEM,
            
            # Reports (all)
            Permission.REPORTS_EXPORT,
            Permission.REPORTS_VIEW,
            
            # Streaming/Signals (all)
            Permission.ALERTS_READ,
            Permission.PRICES_READ,
            Permission.SIGNALS_READ,
            Permission.TRENDS_READ,
            Permission.ANOMALIES_READ,
        },
        
        UserRole.USER: {
            # Authentication (own)
            Permission.AUTH_REGISTER,
            Permission.AUTH_LOGIN,
            Permission.AUTH_LOGOUT,
            Permission.AUTH_PROFILE,
            Permission.AUTH_REFRESH,
            
            # User Management (own)
            Permission.USERS_READ_SELF,
            Permission.USERS_WRITE_SELF,
            
            # Documents (own)
            Permission.DOCUMENTS_CREATE,
            Permission.DOCUMENTS_READ_OWN,
            Permission.DOCUMENTS_UPDATE_OWN,
            Permission.DOCUMENTS_DELETE_OWN,
            
            # Workflows (own)
            Permission.WORKFLOWS_CREATE,
            Permission.WORKFLOWS_READ_OWN,
            Permission.WORKFLOWS_EXECUTE_OWN,
            Permission.WORKFLOWS_DELETE_OWN,
            
            # Templates (shared/public)
            Permission.TEMPLATES_READ,
            Permission.TEMPLATES_READ_PUBLIC,
            
            # Reports (own)
            Permission.REPORTS_EXPORT,
            Permission.REPORTS_VIEW,
            
            # Streaming/Signals (all authenticated can read)
            Permission.ALERTS_READ,
            Permission.PRICES_READ,
            Permission.SIGNALS_READ,
            Permission.TRENDS_READ,
            Permission.ANOMALIES_READ,
        },
        
        UserRole.VIEWER: {
            # Authentication (read only)
            Permission.AUTH_LOGIN,
            Permission.AUTH_LOGOUT,
            Permission.AUTH_PROFILE,
            Permission.AUTH_REFRESH,
            
            # User Management (none)
            # (Removed: cannot read or write other user data)
            
            # Documents (read only, own)
            Permission.DOCUMENTS_READ_OWN,
            
            # Workflows (read only, own)
            Permission.WORKFLOWS_READ_OWN,
            
            # Templates (read only)
            Permission.TEMPLATES_READ,
            Permission.TEMPLATES_READ_PUBLIC,
            
            # Reports (view only)
            Permission.REPORTS_VIEW,
            
            # Streaming/Signals (all authenticated can read)
            Permission.ALERTS_READ,
            Permission.PRICES_READ,
            Permission.SIGNALS_READ,
            Permission.TRENDS_READ,
            Permission.ANOMALIES_READ,
        },
        
        UserRole.GUEST: {
            # Authentication (public endpoints)
            Permission.AUTH_REGISTER,
            Permission.AUTH_LOGIN,
            
            # Templates (public only)
            Permission.TEMPLATES_READ_PUBLIC,
        },
    }
    
    @staticmethod
    def has_permission(role: UserRole, permission: Permission) -> bool:
        """Check if a role has a specific permission
        
        Args:
            role: User role
            permission: Permission to check
            
        Returns:
            True if role has permission, False otherwise
        """
        if role not in RBACService.ROLE_PERMISSIONS:
            logger.warning(f"Unknown role: {role}")
            return False
        
        return permission in RBACService.ROLE_PERMISSIONS[role]
    
    @staticmethod
    def has_any_permission(role: UserRole, permissions: list) -> bool:
        """Check if role has any of the given permissions
        
        Args:
            role: User role
            permissions: List of permissions
            
        Returns:
            True if role has at least one permission
        """
        return any(RBACService.has_permission(role, perm) for perm in permissions)
    
    @staticmethod
    def has_all_permissions(role: UserRole, permissions: list) -> bool:
        """Check if role has all of the given permissions
        
        Args:
            role: User role
            permissions: List of permissions
            
        Returns:
            True if role has all permissions
        """
        return all(RBACService.has_permission(role, perm) for perm in permissions)
    
    @staticmethod
    def get_permissions(role: UserRole) -> Set[Permission]:
        """Get all permissions for a role
        
        Args:
            role: User role
            
        Returns:
            Set of permissions for the role
        """
        return RBACService.ROLE_PERMISSIONS.get(role, set())
    
    @staticmethod
    def can_access_resource(
        role: UserRole,
        resource_owner_email: str,
        current_user_email: str,
        is_shared: bool = False
    ) -> bool:
        """Check if user can access a resource based on ownership
        
        Args:
            role: User role
            resource_owner_email: Email of resource owner
            current_user_email: Email of current user
            is_shared: Whether resource is shared with all users
            
        Returns:
            True if user can access resource
        """
        # Admin can access anything
        if role == UserRole.ADMIN:
            return True
        
        # Shared resources accessible to authenticated users
        if is_shared and role != UserRole.GUEST:
            return True
        
        # Only owner can access own resources
        return resource_owner_email == current_user_email
    
    @staticmethod
    def require_role(allowed_roles: list) -> bool:
        """Check if a role is in the allowed roles
        
        Args:
            allowed_roles: List of allowed roles
            
        Returns:
            True if role is allowed
        """
        def check_role(role: UserRole) -> bool:
            return role in allowed_roles
        
        return check_role
    
    @staticmethod
    def get_role_hierarchy() -> Dict[UserRole, int]:
        """Get role hierarchy (higher number = higher privilege)
        
        Returns:
            Dictionary mapping roles to privilege levels
        """
        return {
            UserRole.GUEST: 0,
            UserRole.VIEWER: 1,
            UserRole.USER: 2,
            UserRole.ADMIN: 3,
        }
    
    @staticmethod
    def is_privilege_level_sufficient(
        user_role: UserRole,
        required_role: UserRole
    ) -> bool:
        """Check if user's role has sufficient privilege level
        
        Args:
            user_role: User's actual role
            required_role: Required role level
            
        Returns:
            True if user's privilege level >= required level
        """
        hierarchy = RBACService.get_role_hierarchy()
        return hierarchy.get(user_role, -1) >= hierarchy.get(required_role, -1)
    
    @staticmethod
    def log_authorization_decision(
        user_email: str,
        user_role: UserRole,
        resource: str,
        action: str,
        allowed: bool,
        reason: Optional[str] = None
    ):
        """Log authorization decision for audit trail
        
        Args:
            user_email: User's email
            user_role: User's role
            resource: Resource being accessed
            action: Action being performed
            allowed: Whether access was granted
            reason: Reason for decision
        """
        status = "ALLOWED" if allowed else "DENIED"
        log_level = logging.INFO if allowed else logging.WARNING
        
        message = f"Authorization {status}: {user_email} ({user_role.value}) -> {resource}:{action}"
        if reason:
            message += f" - {reason}"
        
        logger.log(log_level, message)


# Helper function for quick role checks
def can_user_access(
    user_role: UserRole,
    permission: Permission
) -> bool:
    """Quick check if user has permission
    
    Args:
        user_role: User's role
        permission: Permission to check
        
    Returns:
        True if user has permission
    """
    return RBACService.has_permission(user_role, permission)
