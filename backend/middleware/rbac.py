"""
RBAC Middleware - Role-Based Access Control Middleware

Provides FastAPI dependencies and decorators for role-based authorization.
Includes tenant context management for multi-tenant isolation.
"""

import logging
from typing import Callable, List, Optional, Tuple
from functools import wraps

from fastapi import Depends, HTTPException, Header, status

from services.token_service import TokenService
from services.rbac_service import RBACService, UserRole, Permission
from services.tenant_service import TenantService, get_or_create_tenant_context
from services.user_service import UserService
from models.user import User

logger = logging.getLogger(__name__)

# In-memory user store (temporary - would use Cosmos DB in production)
users_db = {}

# UserService instance (will be injected with database)
user_service: Optional[UserService] = None

def set_user_service(service: UserService):
    """Inject UserService instance"""
    global user_service
    user_service = service

def get_user_service() -> UserService:
    """Get UserService instance"""
    if not user_service:
        raise HTTPException(status_code=500, detail="User service not initialized")
    return user_service


async def get_current_user_with_role(
    authorization: str = Header(None)
) -> Tuple[str, UserRole]:
    """
    Extract user email and role from JWT token
    Also sets tenant context for multi-tenant isolation
    
    This dependency verifies the access token and retrieves the user's role,
    then establishes the tenant context for the request.
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        Tuple of (email, role)
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Verify token using TokenService (includes revocation checking)
    payload = TokenService.verify_token(token, check_revocation=True)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token - missing user email",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user to get role
    user = None
    try:
        service = get_user_service()
        user = await service.get_user_by_email(email)
    except Exception:
        # Fallback to in-memory lookup if UserService not available
        user = users_db.get(email)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    logger.debug(f"User authenticated: {email} (role: {user.role.value})")
    
    # Phase 4: Set tenant context for multi-tenant isolation
    try:
        tenant_context = await get_or_create_tenant_context(email, user.role)
        TenantService.set_current_tenant(tenant_context)
        logger.debug(f"Tenant context established: {tenant_context}")
    except Exception as e:
        logger.error(f"Failed to establish tenant context for {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to establish tenant context",
        )
    
    return email, user.role


def require_role(*allowed_roles: UserRole):
    """
    Dependency to require specific roles
    
    Usage:
        @router.get("/admin/users")
        async def get_users(
            email: str,
            role: UserRole,
            deps=Depends(require_role(UserRole.ADMIN))
        ):
            ...
    
    Args:
        allowed_roles: Roles that are allowed to access the endpoint
        
    Returns:
        Dependency function that checks roles
    """
    async def role_checker(
        email: str = Depends(lambda: None),
        current_user: Tuple[str, UserRole] = Depends(get_current_user_with_role)
    ) -> Tuple[str, UserRole]:
        user_email, user_role = current_user
        
        if user_role not in allowed_roles:
            RBACService.log_authorization_decision(
                user_email,
                user_role,
                "endpoint",
                "access",
                False,
                f"Role {user_role.value} not in allowed roles: {[r.value for r in allowed_roles]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires one of these roles: {[r.value for r in allowed_roles]}"
            )
        
        RBACService.log_authorization_decision(
            user_email,
            user_role,
            "endpoint",
            "access",
            True
        )
        
        return user_email, user_role
    
    return role_checker


def require_permission(*permissions: Permission):
    """
    Dependency to require specific permissions
    
    Usage:
        @router.post("/documents")
        async def create_document(
            doc: DocumentCreate,
            deps=Depends(require_permission(Permission.DOCUMENTS_CREATE))
        ):
            ...
    
    Args:
        permissions: Permissions required to access the endpoint
        
    Returns:
        Dependency function that checks permissions
    """
    async def permission_checker(
        current_user: Tuple[str, UserRole] = Depends(get_current_user_with_role)
    ) -> Tuple[str, UserRole]:
        user_email, user_role = current_user
        
        # Check if user has all required permissions
        has_all = all(
            RBACService.has_permission(user_role, perm) 
            for perm in permissions
        )
        
        if not has_all:
            missing_perms = [
                perm.value for perm in permissions
                if not RBACService.has_permission(user_role, perm)
            ]
            
            RBACService.log_authorization_decision(
                user_email,
                user_role,
                "endpoint",
                "access",
                False,
                f"Missing permissions: {missing_perms}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires permissions: {[p.value for p in permissions]}"
            )
        
        RBACService.log_authorization_decision(
            user_email,
            user_role,
            "endpoint",
            "access",
            True
        )
        
        return user_email, user_role
    
    return permission_checker


def require_permission_any(*permissions: Permission):
    """
    Dependency to require any of the specified permissions
    
    Usage:
        @router.get("/documents/{doc_id}")
        async def get_document(
            doc_id: str,
            deps=Depends(require_permission_any(
                Permission.DOCUMENTS_READ_OWN,
                Permission.DOCUMENTS_READ_ALL
            ))
        ):
            ...
    
    Args:
        permissions: Permissions, user must have at least one
        
    Returns:
        Dependency function that checks permissions
    """
    async def permission_checker(
        current_user: Tuple[str, UserRole] = Depends(get_current_user_with_role)
    ) -> Tuple[str, UserRole]:
        user_email, user_role = current_user
        
        # Check if user has any required permission
        has_any = any(
            RBACService.has_permission(user_role, perm)
            for perm in permissions
        )
        
        if not has_any:
            RBACService.log_authorization_decision(
                user_email,
                user_role,
                "endpoint",
                "access",
                False,
                f"Missing any of permissions: {[p.value for p in permissions]}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires one of these permissions: {[p.value for p in permissions]}"
            )
        
        RBACService.log_authorization_decision(
            user_email,
            user_role,
            "endpoint",
            "access",
            True
        )
        
        return user_email, user_role
    
    return permission_checker


# Convenience dependencies for common role checks

def require_admin():
    """
    Dependency to require ADMIN role
    
    Returns:
        Dependency function
    """
    async def dependency(
        current_user: Tuple[str, UserRole] = Depends(require_role(UserRole.ADMIN))
    ) -> Tuple[str, UserRole]:
        return current_user
    
    return dependency


def require_authenticated():
    """
    Dependency to require any authenticated user (not GUEST)
    
    Returns:
        Dependency function
    """
    async def dependency(
        current_user: Tuple[str, UserRole] = Depends(get_current_user_with_role)
    ) -> Tuple[str, UserRole]:
        user_email, user_role = current_user
        
        if user_role == UserRole.GUEST:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        return current_user
    
    return dependency


def check_resource_ownership(
    resource_owner_email: str,
    current_user_email: str,
    user_role: UserRole
) -> bool:
    """
    Check if user can access resource based on ownership
    
    Args:
        resource_owner_email: Email of resource owner
        current_user_email: Email of current user
        user_role: Role of current user
        
    Returns:
        True if user can access resource
        
    Example:
        owner_email = document.owner
        user_email, user_role = current_user
        
        if not check_resource_ownership(owner_email, user_email, user_role):
            raise HTTPException(403, "Cannot access this document")
    """
    return RBACService.can_access_resource(
        user_role,
        resource_owner_email,
        current_user_email,
        is_shared=False
    )
