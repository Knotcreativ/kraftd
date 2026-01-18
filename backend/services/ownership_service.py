"""
Ownership Service for resource ownership validation
Enforces resource ownership and access control across tenants
"""

import logging
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

from services.tenant_service import TenantService
from services.rbac_service import RBACService, UserRole

logger = logging.getLogger(__name__)


class ResourceType(str, Enum):
    """Supported resource types"""
    TEMPLATE = "template"
    DOCUMENT = "document"
    SIGNAL = "signal"
    PROFILE = "profile"
    PREFERENCE = "preference"
    EVENT = "event"


class OwnershipRecord:
    """Record of resource ownership"""
    
    def __init__(
        self,
        resource_id: str,
        resource_type: ResourceType,
        owner_email: str,
        tenant_id: str,
        created_at: datetime = None,
        shared_with: List[str] = None,
        is_public: bool = False
    ):
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.owner_email = owner_email
        self.tenant_id = tenant_id
        self.created_at = created_at or datetime.utcnow()
        self.shared_with = shared_with or []
        self.is_public = is_public


class OwnershipService:
    """Service for managing resource ownership and access"""
    
    # In-memory ownership mapping (resource_id -> OwnershipRecord)
    # In production, this would be stored in Cosmos DB with proper indexing
    _ownership_db: Dict[str, OwnershipRecord] = {}
    _rbac_service = RBACService()
    
    @staticmethod
    async def verify_resource_owner(
        user_email: str,
        resource_id: str,
        resource_type: ResourceType,
        tenant_id: str
    ) -> bool:
        """
        Verify user owns a resource
        
        Args:
            user_email: User email address
            resource_id: Resource ID
            resource_type: Type of resource
            tenant_id: Tenant ID for isolation
            
        Returns:
            True if user owns resource, False otherwise
        """
        # Get tenant context
        tenant_context = TenantService.get_current_tenant()
        if not tenant_context:
            logger.warning(f"No tenant context for ownership check: {resource_id}")
            return False
        
        # Verify tenant match
        if not TenantService.is_same_tenant(tenant_context.tenant_id, tenant_id):
            logger.warning(
                f"Cross-tenant ownership attempt: "
                f"{user_email} ({tenant_context.tenant_id}) -> {resource_id} ({tenant_id})"
            )
            return False
        
        # Build resource key
        resource_key = f"{resource_type.value}:{resource_id}"
        
        # Check if resource exists
        record = OwnershipService._ownership_db.get(resource_key)
        if not record:
            logger.debug(f"Resource not found in ownership db: {resource_key}")
            return False
        
        # Check ownership
        is_owner = record.owner_email == user_email
        is_admin = tenant_context.user_role == UserRole.ADMIN
        is_shared = user_email in record.shared_with
        
        allowed = is_owner or is_admin or is_shared
        
        if not allowed:
            logger.warning(
                f"Ownership verification failed: "
                f"{user_email} (role={tenant_context.user_role.value}) "
                f"cannot access {resource_key} (owner={record.owner_email})"
            )
        
        return allowed
    
    @staticmethod
    async def verify_resource_access(
        user_email: str,
        resource_id: str,
        resource_type: ResourceType,
        action: str = "read"
    ) -> bool:
        """
        Verify user can perform action on resource (comprehensive check)
        
        Args:
            user_email: User email address
            resource_id: Resource ID
            resource_type: Type of resource
            action: Action to perform (read, write, delete, share)
            
        Returns:
            True if access allowed, False otherwise
        """
        tenant_context = TenantService.get_current_tenant()
        if not tenant_context:
            return False
        
        resource_key = f"{resource_type.value}:{resource_id}"
        record = OwnershipService._ownership_db.get(resource_key)
        
        if not record:
            return False
        
        # Verify tenant isolation
        if not TenantService.is_same_tenant(record.tenant_id, tenant_context.tenant_id):
            logger.warning(f"Cross-tenant access attempt: {resource_key}")
            return False
        
        # Owner has full access
        if record.owner_email == user_email:
            logger.debug(f"Access granted to owner: {user_email} -> {resource_key}")
            return True
        
        # ADMIN has full access
        if tenant_context.user_role == UserRole.ADMIN:
            logger.warning(
                f"ADMIN access to resource: {user_email} -> {resource_key}"
            )
            return True
        
        # Check if shared
        if user_email in record.shared_with:
            logger.debug(f"Access granted via sharing: {user_email} -> {resource_key}")
            return True
        
        # Check if public
        if record.is_public and action == "read":
            logger.debug(f"Access granted to public resource: {user_email} -> {resource_key}")
            return True
        
        logger.warning(
            f"Access denied: {user_email} (role={tenant_context.user_role.value}) "
            f"cannot {action} {resource_key}"
        )
        return False
    
    @staticmethod
    async def get_owned_resources(
        user_email: str,
        resource_type: Optional[ResourceType] = None,
        tenant_id: Optional[str] = None
    ) -> List[str]:
        """
        Get all resources owned by user
        
        Args:
            user_email: User email address
            resource_type: Optional filter by resource type
            tenant_id: Optional filter by tenant
            
        Returns:
            List of resource IDs
        """
        tenant_context = TenantService.get_current_tenant()
        if not tenant_context:
            return []
        
        # Use tenant from context if not provided
        check_tenant = tenant_id or tenant_context.tenant_id
        
        owned = []
        for resource_key, record in OwnershipService._ownership_db.items():
            # Filter by tenant
            if not TenantService.is_same_tenant(record.tenant_id, check_tenant):
                continue
            
            # Filter by owner
            if record.owner_email != user_email:
                continue
            
            # Filter by type if specified
            if resource_type and not resource_key.startswith(resource_type.value):
                continue
            
            # Extract resource ID from key
            _, resource_id = resource_key.split(":", 1)
            owned.append(resource_id)
        
        logger.debug(
            f"Retrieved {len(owned)} owned resources for {user_email} "
            f"({resource_type.value if resource_type else 'all'} type)"
        )
        
        return owned
    
    @staticmethod
    async def create_ownership_record(
        resource_id: str,
        resource_type: ResourceType,
        owner_email: str,
        tenant_id: str,
        is_public: bool = False
    ) -> bool:
        """
        Create ownership record for new resource
        
        Args:
            resource_id: Resource ID
            resource_type: Type of resource
            owner_email: Owner email
            tenant_id: Tenant ID
            is_public: Whether resource is public
            
        Returns:
            True if created successfully
        """
        tenant_context = TenantService.get_current_tenant()
        if not tenant_context:
            logger.error("No tenant context for ownership record creation")
            return False
        
        # Verify owner is in same tenant
        if not TenantService.is_same_tenant(tenant_context.tenant_id, tenant_id):
            logger.warning(
                f"Cross-tenant ownership creation attempt: "
                f"{owner_email} ({tenant_id})"
            )
            return False
        
        resource_key = f"{resource_type.value}:{resource_id}"
        
        # Check if already exists
        if resource_key in OwnershipService._ownership_db:
            logger.debug(f"Ownership record already exists: {resource_key}")
            return False
        
        # Create record
        record = OwnershipRecord(
            resource_id=resource_id,
            resource_type=resource_type,
            owner_email=owner_email,
            tenant_id=tenant_id,
            is_public=is_public
        )
        
        OwnershipService._ownership_db[resource_key] = record
        logger.info(
            f"Ownership record created: {resource_key} "
            f"(owner={owner_email}, tenant={tenant_id})"
        )
        
        return True
    
    @staticmethod
    async def transfer_ownership(
        resource_id: str,
        resource_type: ResourceType,
        from_user: str,
        to_user: str,
        tenant_id: str
    ) -> bool:
        """
        Transfer resource ownership
        
        Args:
            resource_id: Resource ID
            resource_type: Type of resource
            from_user: Current owner email
            to_user: New owner email
            tenant_id: Tenant ID
            
        Returns:
            True if transfer successful
        """
        tenant_context = TenantService.get_current_tenant()
        if not tenant_context:
            logger.error("No tenant context for ownership transfer")
            return False
        
        resource_key = f"{resource_type.value}:{resource_id}"
        record = OwnershipService._ownership_db.get(resource_key)
        
        if not record:
            logger.warning(f"Resource not found for transfer: {resource_key}")
            return False
        
        # Verify tenant match
        if not TenantService.is_same_tenant(record.tenant_id, tenant_id):
            logger.warning(f"Cross-tenant ownership transfer attempt: {resource_key}")
            return False
        
        # Verify current ownership
        if record.owner_email != from_user:
            logger.warning(
                f"Ownership transfer from wrong owner: "
                f"{from_user} is not owner of {resource_key}"
            )
            return False
        
        # Verify permission to transfer
        is_owner = tenant_context.user_email == from_user
        is_admin = tenant_context.user_role == UserRole.ADMIN
        
        if not (is_owner or is_admin):
            logger.warning(
                f"No permission to transfer ownership: {tenant_context.user_email} "
                f"cannot transfer {resource_key}"
            )
            return False
        
        # Perform transfer
        old_owner = record.owner_email
        record.owner_email = to_user
        
        # Remove from shared list if was there
        if to_user in record.shared_with:
            record.shared_with.remove(to_user)
        
        logger.info(
            f"Ownership transferred: {resource_key} "
            f"({old_owner} -> {to_user})"
        )
        
        return True
    
    @staticmethod
    async def share_resource(
        resource_id: str,
        resource_type: ResourceType,
        share_with: List[str],
        tenant_id: str
    ) -> bool:
        """
        Share resource with other users
        
        Args:
            resource_id: Resource ID
            resource_type: Type of resource
            share_with: List of emails to share with
            tenant_id: Tenant ID
            
        Returns:
            True if shared successfully
        """
        tenant_context = TenantService.get_current_tenant()
        if not tenant_context:
            return False
        
        resource_key = f"{resource_type.value}:{resource_id}"
        record = OwnershipService._ownership_db.get(resource_key)
        
        if not record:
            logger.warning(f"Resource not found for sharing: {resource_key}")
            return False
        
        # Verify ownership or admin
        is_owner = record.owner_email == tenant_context.user_email
        is_admin = tenant_context.user_role == UserRole.ADMIN
        
        if not (is_owner or is_admin):
            logger.warning(
                f"Cannot share resource: {tenant_context.user_email} "
                f"is not owner of {resource_key}"
            )
            return False
        
        # Add to shared list
        for email in share_with:
            if email not in record.shared_with:
                record.shared_with.append(email)
        
        logger.info(
            f"Resource shared: {resource_key} "
            f"with {len(share_with)} users"
        )
        
        return True
    
    @staticmethod
    async def delete_ownership_record(
        resource_id: str,
        resource_type: ResourceType,
        tenant_id: str
    ) -> bool:
        """
        Delete ownership record (when resource is deleted)
        
        Args:
            resource_id: Resource ID
            resource_type: Type of resource
            tenant_id: Tenant ID
            
        Returns:
            True if deleted successfully
        """
        resource_key = f"{resource_type.value}:{resource_id}"
        
        if resource_key not in OwnershipService._ownership_db:
            logger.debug(f"Ownership record not found: {resource_key}")
            return False
        
        del OwnershipService._ownership_db[resource_key]
        logger.info(f"Ownership record deleted: {resource_key}")
        
        return True
