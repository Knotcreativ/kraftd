#!/usr/bin/env python3
"""
Diagnostic script to trace the database behavior
"""
import sys
import asyncio
sys.path.insert(0, '/c/Users/1R6/OneDrive/Project Catalyst/KraftdIntel/backend')

from services.ownership_service import OwnershipService, ResourceType
from services.tenant_service import TenantService, TenantContext
from models.user import UserRole

async def diagnose():
    print("=" * 60)
    print("DIAGNOSTIC: Database Key Format Issue")
    print("=" * 60)
    
    # Setup tenant 1
    print("\n[Step 1] Creating resource in tenant-1")
    context1 = TenantContext('tenant-1', 'owner1@example.com', UserRole.USER)
    TenantService.set_current_tenant(context1)
    TenantService._tenant_mapping['owner1@example.com'] = 'tenant-1'
    
    result1 = await OwnershipService.create_ownership_record(
        resource_id='res-123',
        resource_type=ResourceType.DOCUMENT,
        owner_email='owner1@example.com',
        tenant_id='tenant-1'
    )
    print(f"  ✓ Result: {result1}")
    print(f"  ✓ Database keys: {list(OwnershipService._ownership_db.keys())}")
    
    # Setup tenant 2
    print("\n[Step 2] Creating SAME resource (res-123) in tenant-2")
    context2 = TenantContext('tenant-2', 'owner2@example.com', UserRole.USER)
    TenantService.set_current_tenant(context2)
    TenantService._tenant_mapping['owner2@example.com'] = 'tenant-2'
    
    result2 = await OwnershipService.create_ownership_record(
        resource_id='res-123',  # SAME ID
        resource_type=ResourceType.DOCUMENT,
        owner_email='owner2@example.com',
        tenant_id='tenant-2'
    )
    print(f"  ✗ Result: {result2} (expected: True, got: {result2})")
    print(f"  ✓ Database keys: {list(OwnershipService._ownership_db.keys())}")
    
    # Show what's in database
    print("\n[Database Contents]")
    for key, record in OwnershipService._ownership_db.items():
        print(f"  Key: '{key}'")
        print(f"    Owner: {record.owner_email}")
        print(f"    Tenant: {record.tenant_id}")
        print(f"    Resource: {record.resource_type.value}:{record.resource_id}")
    
    print("\n[Analysis]")
    print("  Problem: Second creation returned False")
    print("  Reason: Key format '{type}:{id}' doesn't include tenant")
    print("  Result: Same key used for both tenants → collision!")
    print("\n  Current key:   document:res-123")
    print("  Should be:     tenant-1:document:res-123  (tenant-1 version)")
    print("                 tenant-2:document:res-123  (tenant-2 version)")
    
    print("\n[Code Location]")
    print("  File: backend/services/ownership_service.py")
    print("  Line: 95 - resource_key = f\"{resource_type.value}:{resource_id}\"")
    print("  Should: resource_key = f\"{tenant_id}:{resource_type.value}:{resource_id}\"")

asyncio.run(diagnose())
