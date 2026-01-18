"""
Query Scope Utility for automatic query scoping
Provides utilities for scoping database queries to tenant and user context
"""

import logging
from typing import Dict, Any, Optional

from services.tenant_service import TenantService

logger = logging.getLogger(__name__)


class QueryScope:
    """Utility for scoping queries to tenant/user context"""
    
    @staticmethod
    def add_tenant_filter(query: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """
        Add tenant filter to query
        
        Args:
            query: Original query dict
            tenant_id: Tenant ID to filter by
            
        Returns:
            Modified query with tenant filter
        """
        if query is None:
            query = {}
        
        # Add tenant filter
        query["tenant_id"] = tenant_id
        logger.debug(f"Added tenant filter: {tenant_id}")
        
        return query
    
    @staticmethod
    def add_user_filter(query: Dict[str, Any], user_email: str) -> Dict[str, Any]:
        """
        Add user filter to query
        
        Args:
            query: Original query dict
            user_email: User email to filter by
            
        Returns:
            Modified query with user filter
        """
        if query is None:
            query = {}
        
        # Add user filter (assumes owner_email field)
        query["owner_email"] = user_email
        logger.debug(f"Added user filter: {user_email}")
        
        return query
    
    @staticmethod
    def scope_to_tenant_and_user(
        query: Dict[str, Any],
        tenant_id: Optional[str] = None,
        user_email: Optional[str] = None,
        require_ownership: bool = False
    ) -> Dict[str, Any]:
        """
        Scope query to both tenant and user
        
        Automatically applies tenant and optionally user filtering based on
        current tenant context
        
        Args:
            query: Original query dict
            tenant_id: Optional explicit tenant ID (uses context if not provided)
            user_email: Optional explicit user email (uses context if not provided)
            require_ownership: If True, filter by owner_email
            
        Returns:
            Modified query with appropriate filters
        """
        if query is None:
            query = {}
        
        # Get tenant context
        tenant_context = TenantService.get_current_tenant()
        if not tenant_context:
            logger.warning("No tenant context available for query scoping")
            # Still apply tenant filter if provided
            if tenant_id:
                query = QueryScope.add_tenant_filter(query, tenant_id)
            return query
        
        # Use provided tenant_id or get from context
        scope_tenant = tenant_id or tenant_context.tenant_id
        
        # Always add tenant filter
        query = QueryScope.add_tenant_filter(query, scope_tenant)
        
        # Optionally add user filter
        if require_ownership:
            # Use provided user_email or get from context
            scope_user = user_email or tenant_context.user_email
            query = QueryScope.add_user_filter(query, scope_user)
        elif user_email:
            # If explicit user_email provided, use it
            query = QueryScope.add_user_filter(query, user_email)
        
        logger.debug(
            f"Query scoped to tenant={scope_tenant}, "
            f"user={user_email if require_ownership or user_email else 'all'}"
        )
        
        return query
    
    @staticmethod
    def scope_to_tenant(
        query: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scope query to tenant only (read-only safe)
        
        Args:
            query: Original query dict
            tenant_id: Optional explicit tenant ID
            
        Returns:
            Modified query with tenant filter
        """
        if query is None:
            query = {}
        
        tenant_context = TenantService.get_current_tenant()
        scope_tenant = tenant_id or (tenant_context.tenant_id if tenant_context else None)
        
        if scope_tenant:
            query = QueryScope.add_tenant_filter(query, scope_tenant)
        else:
            logger.warning("No tenant information available for query scoping")
        
        return query
    
    @staticmethod
    def get_tenant_scope() -> Optional[str]:
        """
        Get current tenant scope
        
        Returns:
            Current tenant ID or None
        """
        tenant_context = TenantService.get_current_tenant()
        if tenant_context:
            return tenant_context.tenant_id
        return None
    
    @staticmethod
    def get_user_scope() -> Optional[str]:
        """
        Get current user scope
        
        Returns:
            Current user email or None
        """
        tenant_context = TenantService.get_current_tenant()
        if tenant_context:
            return tenant_context.user_email
        return None
    
    @staticmethod
    def build_ownership_filter(
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build filter for user-owned resources
        
        Args:
            user_email: Optional explicit user email
            
        Returns:
            Filter dict for owned resources
        """
        query = {}
        
        # Add tenant filter
        query = QueryScope.scope_to_tenant(query)
        
        # Add ownership filter
        owner = user_email or QueryScope.get_user_scope()
        if owner:
            query["owner_email"] = owner
        
        return query
    
    @staticmethod
    def build_shared_resources_filter(user_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Build filter for resources shared with user
        
        Args:
            user_email: Optional explicit user email
            
        Returns:
            Filter dict for shared resources
        """
        query = {}
        
        # Add tenant filter
        query = QueryScope.scope_to_tenant(query)
        
        # Add shared filter
        email = user_email or QueryScope.get_user_scope()
        if email:
            query["shared_with"] = {"$in": [email]}
        
        return query
    
    @staticmethod
    def build_public_resources_filter() -> Dict[str, Any]:
        """
        Build filter for public resources in tenant
        
        Returns:
            Filter dict for public resources
        """
        query = {}
        
        # Add tenant filter
        query = QueryScope.scope_to_tenant(query)
        
        # Add public filter
        query["is_public"] = True
        
        return query
    
    @staticmethod
    def validate_cross_tenant_query(
        query: Dict[str, Any],
        expected_tenant: str
    ) -> bool:
        """
        Validate query doesn't access cross-tenant data
        
        Args:
            query: Query dict to validate
            expected_tenant: Expected tenant in query
            
        Returns:
            True if query is valid (same tenant)
        """
        query_tenant = query.get("tenant_id")
        
        if query_tenant and query_tenant != expected_tenant:
            logger.warning(
                f"Cross-tenant query detected: "
                f"query={query_tenant}, expected={expected_tenant}"
            )
            return False
        
        return True
    
    @staticmethod
    def merge_filters(
        *filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge multiple filter dicts safely
        
        Args:
            *filters: Multiple filter dicts to merge
            
        Returns:
            Merged filter dict
        """
        merged = {}
        
        for f in filters:
            if f:
                merged.update(f)
        
        # Verify tenant filter present
        if "tenant_id" not in merged:
            logger.warning("Merged filter missing tenant_id - this is dangerous!")
        
        return merged


# Convenience functions

def get_scoped_query(
    base_query: Optional[Dict[str, Any]] = None,
    require_ownership: bool = False
) -> Dict[str, Any]:
    """
    Get a query scoped to current tenant context
    
    Args:
        base_query: Optional base query to extend
        require_ownership: If True, filter by current user ownership
        
    Returns:
        Scoped query dict
    """
    return QueryScope.scope_to_tenant_and_user(
        base_query or {},
        require_ownership=require_ownership
    )


def get_tenant_scoped_query(
    base_query: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get a query scoped to current tenant only
    
    Args:
        base_query: Optional base query to extend
        
    Returns:
        Tenant-scoped query dict
    """
    return QueryScope.scope_to_tenant(base_query or {})
