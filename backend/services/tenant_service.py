"""
Tenant Service for multi-tenant isolation
Manages tenant context and multi-tenant data isolation
"""

import logging
from contextvars import ContextVar
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

from services.rbac_service import UserRole

logger = logging.getLogger(__name__)

# Context variable for tenant context (async-safe)
_tenant_context: ContextVar[Optional['TenantContext']] = ContextVar('tenant_context', default=None)


@dataclass
class TenantContext:
    """Tenant context for request-scoped isolation"""
    
    tenant_id: str
    user_email: str
    user_role: UserRole
    
    def is_tenant_admin(self) -> bool:
        """
        Check if user is tenant admin
        
        Returns True for ADMIN (system admin) and TENANT_ADMIN roles
        """
        return self.user_role in [UserRole.ADMIN, UserRole.TENANT_ADMIN]
    
    def can_access_resource(self, resource_owner_email: str) -> bool:
        """
        Verify if user can access resource within tenant
        
        Args:
            resource_owner_email: Email of resource owner
            
        Returns:
            True if user is owner, tenant admin, or ADMIN role
        """
        # Owners can access their own resources
        if resource_owner_email == self.user_email:
            return True
        
        # ADMIN and TENANT_ADMIN can access any resource in tenant
        if self.user_role in [UserRole.ADMIN, UserRole.TENANT_ADMIN]:
            return True
        
        # Default: deny access
        return False
    
    def __repr__(self) -> str:
        return f"TenantContext(tenant={self.tenant_id}, user={self.user_email}, role={self.user_role.value})"


class TenantService:
    """Service for managing tenant context and isolation"""
    
    # Context variable for tenant context (async-safe)
    _tenant_context: ContextVar[Optional[TenantContext]] = _tenant_context
    
    # In-memory tenant mapping (user_email -> tenant_id)
    # In production, this would be stored in Cosmos DB
    _tenant_mapping: Dict[str, str] = {}
    
    # Default tenant for MVP
    DEFAULT_TENANT_ID = "default"
    
    @staticmethod
    def get_current_tenant() -> Optional[TenantContext]:
        """
        Get current tenant context from context variable
        
        Returns:
            TenantContext if set, None otherwise
        """
        return _tenant_context.get()
    
    @staticmethod
    def set_current_tenant(context: TenantContext) -> None:
        """
        Set tenant context for current request
        
        Args:
            context: TenantContext instance
        """
        _tenant_context.set(context)
        logger.debug(f"Tenant context set: {context}")
    
    @staticmethod
    def clear_current_tenant() -> None:
        """Clear tenant context for current request"""
        _tenant_context.set(None)
    
    @staticmethod
    def verify_tenant_access(user_email: str) -> str:
        """
        Verify user has access to a tenant and return tenant_id
        
        Args:
            user_email: User email address
            
        Returns:
            tenant_id for the user
            
        Raises:
            ValueError: If user is not authorized for any tenant
        """
        # Check if user has mapped tenant
        if user_email in TenantService._tenant_mapping:
            tenant_id = TenantService._tenant_mapping[user_email]
            logger.debug(f"User {user_email} assigned to tenant {tenant_id}")
            return tenant_id
        
        # Default: assign to default tenant
        # In production, new users would need explicit tenant assignment
        logger.debug(f"User {user_email} assigned to DEFAULT tenant")
        TenantService._tenant_mapping[user_email] = TenantService.DEFAULT_TENANT_ID
        return TenantService.DEFAULT_TENANT_ID
    
    @staticmethod
    def assign_tenant(user_email: str, tenant_id: Optional[str] = None) -> str:
        """
        Assign user to a tenant
        
        Args:
            user_email: User email address
            tenant_id: Tenant ID to assign (uses DEFAULT_TENANT_ID if not provided)
            
        Returns:
            The tenant_id assigned
        """
        if tenant_id is None:
            tenant_id = TenantService.DEFAULT_TENANT_ID
        TenantService._tenant_mapping[user_email] = tenant_id
        logger.info(f"User {user_email} assigned to tenant {tenant_id}")
        return tenant_id
    
    @staticmethod
    def get_tenant_for_user(user_email: str) -> Optional[str]:
        """
        Get tenant ID for user
        
        Args:
            user_email: User email address
            
        Returns:
            tenant_id or None if not assigned
        """
        return TenantService._tenant_mapping.get(user_email)
    
    @staticmethod
    def get_users_in_tenant(tenant_id: str) -> list:
        """
        Get all users in a tenant
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            List of user emails in tenant
        """
        return [
            email for email, tid in TenantService._tenant_mapping.items()
            if tid == tenant_id
        ]
    
    @staticmethod
    def remove_user_from_tenant(user_email: str) -> bool:
        """
        Remove user from all tenants
        
        Args:
            user_email: User email address
            
        Returns:
            True if user was removed
        """
        if user_email in TenantService._tenant_mapping:
            del TenantService._tenant_mapping[user_email]
            logger.info(f"User {user_email} removed from tenant mapping")
            return True
        return False
    
    @staticmethod
    def create_tenant_context(
        tenant_id: str,
        user_email: str,
        user_role: UserRole
    ) -> TenantContext:
        """
        Create a new tenant context
        
        Args:
            tenant_id: Tenant ID
            user_email: User email
            user_role: User role
            
        Returns:
            New TenantContext instance
        """
        return TenantContext(
            tenant_id=tenant_id,
            user_email=user_email,
            user_role=user_role
        )
    
    @staticmethod
    def is_same_tenant(tenant_id1: str, tenant_id2: str) -> bool:
        """
        Check if two tenant IDs are the same
        
        Args:
            tenant_id1: First tenant ID
            tenant_id2: Second tenant ID
            
        Returns:
            True if same tenant
        """
        return tenant_id1 == tenant_id2
    
    @staticmethod
    def validate_cross_tenant_access(
        current_tenant: str,
        target_tenant: str,
        user_role: UserRole
    ) -> bool:
        """
        Validate if user can access resource in different tenant
        
        Args:
            current_tenant: Current user's tenant
            target_tenant: Target resource's tenant
            user_role: User role
            
        Returns:
            True if access is allowed
        """
        # ADMIN and SYSTEM_ADMIN users can access across tenants (with logging)
        if user_role in [UserRole.ADMIN, UserRole.SYSTEM_ADMIN]:
            logger.warning(
                f"{user_role.value.upper()} user accessing cross-tenant resource: "
                f"{current_tenant} -> {target_tenant}"
            )
            return True
        
        # Regular users and tenant admins cannot access cross-tenant
        return current_tenant == target_tenant


# Utility functions

async def get_or_create_tenant_context(
    user_email: str,
    user_role: UserRole
) -> TenantContext:
    """
    Get or create tenant context for user
    
    Args:
        user_email: User email
        user_role: User role
        
    Returns:
        TenantContext instance
    """
    tenant_id = TenantService.verify_tenant_access(user_email)
    return TenantService.create_tenant_context(tenant_id, user_email, user_role)


def require_tenant_context(func):
    """
    Decorator to ensure tenant context is set
    Raises ValueError if context not found
    """
    async def wrapper(*args, **kwargs):
        context = TenantService.get_current_tenant()
        if not context:
            raise ValueError("Tenant context not set")
        return await func(*args, **kwargs)
    return wrapper
