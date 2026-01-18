"""
Test suite for Ownership Service - Resource Ownership and Access Control Tests
"""

import pytest
from datetime import datetime

from services.ownership_service import (
    OwnershipService, OwnershipRecord, ResourceType
)
from services.tenant_service import TenantService, TenantContext
from models.user import UserRole


class TestOwnershipRecord:
    """Test cases for OwnershipRecord dataclass"""
    
    def test_create_ownership_record(self):
        """Test creating an ownership record"""
        record = OwnershipRecord(
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            owner_email="owner@example.com",
            tenant_id="tenant-123"
        )
        
        assert record.resource_id == "res-123"
        assert record.resource_type == ResourceType.TEMPLATE
        assert record.owner_email == "owner@example.com"
        assert record.tenant_id == "tenant-123"
        assert record.shared_with == []
        assert record.is_public is False
    
    def test_ownership_record_sharing(self):
        """Test sharing functionality in ownership record"""
        record = OwnershipRecord(
            resource_id="res-123",
            resource_type=ResourceType.DOCUMENT,
            owner_email="owner@example.com",
            tenant_id="tenant-123"
        )
        
        record.shared_with = ["user1@example.com", "user2@example.com"]
        
        assert "user1@example.com" in record.shared_with
        assert len(record.shared_with) == 2
    
    def test_ownership_record_public_flag(self):
        """Test public flag in ownership record"""
        record = OwnershipRecord(
            resource_id="res-123",
            resource_type=ResourceType.SIGNAL,
            owner_email="owner@example.com",
            tenant_id="tenant-123",
            is_public=True
        )
        
        assert record.is_public is True


class TestOwnershipService:
    """Test cases for OwnershipService"""
    
    def setup_method(self):
        """Reset services before each test"""
        TenantService.clear_current_tenant()
        TenantService._tenant_mapping.clear()
        OwnershipService._ownership_db.clear()
    
    def _setup_tenant_context(self, tenant_id="tenant-123", 
                              user_email="user@example.com",
                              user_role=UserRole.USER):
        """Helper to set up tenant context"""
        context = TenantContext(
            tenant_id=tenant_id,
            user_email=user_email,
            user_role=user_role
        )
        TenantService.set_current_tenant(context)
        TenantService._tenant_mapping[user_email] = tenant_id
        return context
    
    async def test_create_ownership_record(self):
        """Test creating an ownership record"""
        self._setup_tenant_context()
        
        result = await OwnershipService.create_ownership_record(
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            owner_email="owner@example.com",
            tenant_id="tenant-123"
        )
        
        assert result is True
        assert "tenant-123:template:res-123" in OwnershipService._ownership_db
    
    async def test_verify_resource_owner_success(self):
        """Test verifying resource owner succeeds for actual owner"""
        self._setup_tenant_context(user_email="owner@example.com")
        
        # Create ownership record
        await OwnershipService.create_ownership_record(
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            owner_email="owner@example.com",
            tenant_id="tenant-123"
        )
        
        # Verify ownership
        result = await OwnershipService.verify_resource_owner(
            user_email="owner@example.com",
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            tenant_id="tenant-123"
        )
        
        assert result is True
    
    async def test_verify_resource_owner_failure_wrong_owner(self):
        """Test verifying ownership fails for non-owner"""
        self._setup_tenant_context()
        
        # Create ownership record
        await OwnershipService.create_ownership_record(
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            owner_email="owner@example.com",
            tenant_id="tenant-123"
        )
        
        # Try to verify with different user
        result = await OwnershipService.verify_resource_owner(
            user_email="other@example.com",
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            tenant_id="tenant-123"
        )
        
        assert result is False
    
    async def test_verify_resource_owner_cross_tenant_denied(self):
        """Test cross-tenant ownership verification is denied"""
        self._setup_tenant_context(tenant_id="tenant-123")
        
        # Create ownership record in tenant-123
        await OwnershipService.create_ownership_record(
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            owner_email="owner@example.com",
            tenant_id="tenant-123"
        )
        
        # Try to verify from different tenant
        result = await OwnershipService.verify_resource_owner(
            user_email="owner@example.com",
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            tenant_id="tenant-456"  # Different tenant
        )
        
        assert result is False
    
    async def test_verify_resource_access_owner(self):
        """Test resource access for owner"""
        self._setup_tenant_context(user_email="owner@example.com")
        
        await OwnershipService.create_ownership_record(
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            owner_email="owner@example.com",
            tenant_id="tenant-123"
        )
        
        result = await OwnershipService.verify_resource_access(
            user_email="owner@example.com",
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            action="read"
        )
        
        assert result is True
    
    async def test_verify_resource_access_shared(self):
        """Test resource access for shared user"""
        self._setup_tenant_context(user_email="owner@example.com")
        
        # Create ownership record
        await OwnershipService.create_ownership_record(
            resource_id="res-123",
            resource_type=ResourceType.DOCUMENT,
            owner_email="owner@example.com",
            tenant_id="tenant-123"
        )
        
        # Share with another user
        await OwnershipService.share_resource(
            resource_id="res-123",
            resource_type=ResourceType.DOCUMENT,
            share_with=["user@example.com"],
            tenant_id="tenant-123"
        )
        
        # Setup context for shared user and verify access
        self._setup_tenant_context(user_email="user@example.com")
        result = await OwnershipService.verify_resource_access(
            user_email="user@example.com",
            resource_id="res-123",
            resource_type=ResourceType.DOCUMENT,
            action="read"
        )
        
        assert result is True
    
    async def test_verify_resource_access_public(self):
        """Test resource access for public resources"""
        self._setup_tenant_context()
        
        # Create ownership record
        record = OwnershipRecord(
            resource_id="res-123",
            resource_type=ResourceType.SIGNAL,
            owner_email="owner@example.com",
            tenant_id="tenant-123",
            is_public=True
        )
        OwnershipService._ownership_db["tenant-123:signal:res-123"] = record
        
        # Any user should have access to public resource
        result = await OwnershipService.verify_resource_access(
            user_email="anyone@example.com",
            resource_id="res-123",
            resource_type=ResourceType.SIGNAL,
            action="read"
        )
        
        assert result is True
    
    async def test_verify_resource_access_admin_override(self):
        """Test admin can access any resource"""
        self._setup_tenant_context(user_role=UserRole.ADMIN)
        
        await OwnershipService.create_ownership_record(
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            owner_email="owner@example.com",
            tenant_id="tenant-123"
        )
        
        # Admin should have access regardless of ownership
        result = await OwnershipService.verify_resource_access(
            user_email="admin@example.com",
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            action="delete"
        )
        
        assert result is True
    
    async def test_get_owned_resources(self):
        """Test getting resources owned by user"""
        self._setup_tenant_context()
        
        # Create multiple resources
        for i in range(3):
            await OwnershipService.create_ownership_record(
                resource_id=f"res-{i}",
                resource_type=ResourceType.TEMPLATE,
                owner_email="owner@example.com",
                tenant_id="tenant-123"
            )
        
        # Get owned resources
        resources = await OwnershipService.get_owned_resources(
            user_email="owner@example.com",
            tenant_id="tenant-123"
        )
        
        assert len(resources) == 3
        assert all(r == f"res-{i}" for i, r in enumerate(sorted(resources)))
    
    async def test_share_resource(self):
        """Test sharing resource with another user"""
        self._setup_tenant_context(user_email="owner@example.com")
        
        await OwnershipService.create_ownership_record(
            resource_id="res-123",
            resource_type=ResourceType.DOCUMENT,
            owner_email="owner@example.com",
            tenant_id="tenant-123"
        )
        
        result = await OwnershipService.share_resource(
            resource_id="res-123",
            resource_type=ResourceType.DOCUMENT,
            share_with=["user@example.com"],
            tenant_id="tenant-123"
        )
        
        assert result is True
        record = OwnershipService._ownership_db["tenant-123:document:res-123"]
        assert "user@example.com" in record.shared_with
    
    async def test_transfer_ownership(self):
        """Test transferring ownership to another user"""
        self._setup_tenant_context(user_email="owner@example.com")
        
        await OwnershipService.create_ownership_record(
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            owner_email="owner@example.com",
            tenant_id="tenant-123"
        )
        
        result = await OwnershipService.transfer_ownership(
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            from_user="owner@example.com",
            to_user="newowner@example.com",
            tenant_id="tenant-123"
        )
        
        assert result is True
        record = OwnershipService._ownership_db["tenant-123:template:res-123"]
        assert record.owner_email == "newowner@example.com"
    
    async def test_delete_ownership_record(self):
        """Test deleting ownership record"""
        self._setup_tenant_context()
        
        await OwnershipService.create_ownership_record(
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            owner_email="owner@example.com",
            tenant_id="tenant-123"
        )
        
        result = await OwnershipService.delete_ownership_record(
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            tenant_id="tenant-123"
        )
        
        assert result is True
        assert "res-123" not in OwnershipService._ownership_db


class TestCrossTenantOwnershipIsolation:
    """Test cases for cross-tenant ownership isolation"""
    
    def setup_method(self):
        """Reset services before each test"""
        TenantService.clear_current_tenant()
        TenantService._tenant_mapping.clear()
        OwnershipService._ownership_db.clear()
    
    def _setup_tenant_context(self, tenant_id, user_email, user_role=UserRole.USER):
        """Helper to set up tenant context"""
        context = TenantContext(
            tenant_id=tenant_id,
            user_email=user_email,
            user_role=user_role
        )
        TenantService.set_current_tenant(context)
        TenantService._tenant_mapping[user_email] = tenant_id
        return context
    
    async def test_tenant_1_cannot_access_tenant_2_ownership(self):
        """Test tenant 1 user cannot access tenant 2 resources"""
        # Set up tenant 1
        self._setup_tenant_context("tenant-1", "user1@example.com")
        
        # Create resource in tenant 1
        await OwnershipService.create_ownership_record(
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            owner_email="user1@example.com",
            tenant_id="tenant-1"
        )
        
        # Set up tenant 2
        self._setup_tenant_context("tenant-2", "user2@example.com")
        
        # Try to access tenant 1's resource
        result = await OwnershipService.verify_resource_access(
            user_email="user2@example.com",
            resource_id="res-123",
            resource_type=ResourceType.TEMPLATE,
            action="read"
        )
        
        assert result is False
    
    async def test_resources_isolated_by_tenant(self):
        """Test resources are isolated by tenant"""
        # Create resource in tenant 1
        self._setup_tenant_context("tenant-1", "owner1@example.com")
        
        await OwnershipService.create_ownership_record(
            resource_id="res-123",
            resource_type=ResourceType.DOCUMENT,
            owner_email="owner1@example.com",
            tenant_id="tenant-1"
        )
        
        # Create resource with same ID in tenant 2
        self._setup_tenant_context("tenant-2", "owner2@example.com")
        
        await OwnershipService.create_ownership_record(
            resource_id="res-123",  # Same ID
            resource_type=ResourceType.DOCUMENT,
            owner_email="owner2@example.com",
            tenant_id="tenant-2"  # Different tenant
        )
        
        # Both should exist but be separate
        resources_t1 = await OwnershipService.get_owned_resources(
            user_email="owner1@example.com",
            tenant_id="tenant-1"
        )
        
        resources_t2 = await OwnershipService.get_owned_resources(
            user_email="owner2@example.com",
            tenant_id="tenant-2"
        )
        
        assert len(resources_t1) == 1
        assert len(resources_t2) == 1


# Run tests with: pytest backend/tests/test_ownership.py -v
