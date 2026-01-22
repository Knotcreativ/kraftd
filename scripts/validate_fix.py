#!/usr/bin/env python3
"""
Validation script to verify that adding tenant_id to key format fixes the failure
"""
import sys
sys.path.insert(0, './backend')

# Simulate the fix by monkey-patching
from services.ownership_service import OwnershipService, ResourceType
from services.tenant_service import TenantService, TenantContext
from models.user import UserRole
import asyncio

async def validate_fix():
    print("=" * 70)
    print("VALIDATION: Will Adding Tenant ID to Key Format Fix the Test?")
    print("=" * 70)
    
    # Simulate the fix by monkey-patching the key generation
    original_create = OwnershipService.create_ownership_record
    original_get = OwnershipService.get_owned_resources
    
    # Override create_ownership_record to use tenant_id in key
    async def create_with_tenant_key(resource_id, resource_type, owner_email, tenant_id, is_public=False):
        tenant_context = TenantService.get_current_tenant()
        if not tenant_context:
            return False
        
        if not TenantService.is_same_tenant(tenant_context.tenant_id, tenant_id):
            return False
        
        # FIX: Include tenant_id in key
        resource_key = f"{tenant_id}:{resource_type.value}:{resource_id}"
        
        if resource_key in OwnershipService._ownership_db:
            return False
        
        from services.ownership_service import OwnershipRecord
        record = OwnershipRecord(
            resource_id=resource_id,
            resource_type=resource_type,
            owner_email=owner_email,
            tenant_id=tenant_id,
            is_public=is_public
        )
        
        OwnershipService._ownership_db[resource_key] = record
        return True
    
    # Override get_owned_resources to use tenant_id in key
    async def get_with_tenant_key(user_email, resource_type=None, tenant_id=None):
        tenant_context = TenantService.get_current_tenant()
        if not tenant_context:
            return []
        
        check_tenant = tenant_id or tenant_context.tenant_id
        owned = []
        
        for resource_key, record in OwnershipService._ownership_db.items():
            # FIX: Check tenant_id in key format
            if not TenantService.is_same_tenant(record.tenant_id, check_tenant):
                continue
            
            if record.owner_email != user_email:
                continue
            
            if resource_type and not resource_key.split(":")[1] == resource_type.value:
                continue
            
            # Extract resource ID from key (now format is tenant:type:id)
            _, _, resource_id = resource_key.split(":", 2)
            owned.append(resource_id)
        
        return owned
    
    # Apply monkey-patches
    OwnershipService.create_ownership_record = create_with_tenant_key
    OwnershipService.get_owned_resources = get_with_tenant_key
    
    # Now run the failing test scenario
    print("\n[TEST SCENARIO: test_resources_isolated_by_tenant]")
    print("\nStep 1: Create resource 'res-123' in tenant-1")
    context1 = TenantContext('tenant-1', 'owner1@example.com', UserRole.USER)
    TenantService.set_current_tenant(context1)
    TenantService._tenant_mapping['owner1@example.com'] = 'tenant-1'
    
    result1 = await OwnershipService.create_ownership_record(
        resource_id='res-123',
        resource_type=ResourceType.DOCUMENT,
        owner_email='owner1@example.com',
        tenant_id='tenant-1'
    )
    print(f"  ✓ Create result: {result1} (expected: True)")
    
    resources_t1 = await OwnershipService.get_owned_resources(
        user_email='owner1@example.com',
        tenant_id='tenant-1'
    )
    print(f"  ✓ Resources in tenant-1: {resources_t1} (length: {len(resources_t1)})")
    print(f"  ✓ Database keys: {list(OwnershipService._ownership_db.keys())}")
    
    print("\nStep 2: Create SAME resource 'res-123' in tenant-2")
    context2 = TenantContext('tenant-2', 'owner2@example.com', UserRole.USER)
    TenantService.set_current_tenant(context2)
    TenantService._tenant_mapping['owner2@example.com'] = 'tenant-2'
    
    result2 = await OwnershipService.create_ownership_record(
        resource_id='res-123',  # SAME ID
        resource_type=ResourceType.DOCUMENT,
        owner_email='owner2@example.com',
        tenant_id='tenant-2'
    )
    print(f"  ✓ Create result: {result2} (expected: True)")
    
    resources_t2 = await OwnershipService.get_owned_resources(
        user_email='owner2@example.com',
        tenant_id='tenant-2'
    )
    print(f"  ✓ Resources in tenant-2: {resources_t2} (length: {len(resources_t2)})")
    print(f"  ✓ Database keys: {list(OwnershipService._ownership_db.keys())}")
    
    # Validate the fix
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    
    test_passes = (
        result1 == True and 
        len(resources_t1) == 1 and 
        result2 == True and 
        len(resources_t2) == 1
    )
    
    print(f"\nAssertion 1: len(resources_t1) == 1")
    print(f"  Result: {len(resources_t1)} == 1 → {'✓ PASS' if len(resources_t1) == 1 else '✗ FAIL'}")
    
    print(f"\nAssertion 2: len(resources_t2) == 1")
    print(f"  Result: {len(resources_t2)} == 1 → {'✓ PASS' if len(resources_t2) == 1 else '✗ FAIL'}")
    
    print(f"\nOverall Test Result: {'✓ WILL PASS' if test_passes else '✗ WILL FAIL'}")
    
    print("\n" + "=" * 70)
    print("SCOPE OF CHANGES REQUIRED")
    print("=" * 70)
    print("""
Changes needed in backend/services/ownership_service.py:
  • Line 91  (verify_resource_owner)
  • Line 138 (verify_resource_access)
  • Line 260 (create_ownership_record)
  • Line 310 (transfer_ownership)
  • Line 379 (share_resource)
  • Line 426 (delete_ownership_record)

Each location changes from:
  resource_key = f"{resource_type.value}:{resource_id}"

To:
  resource_key = f"{tenant_id}:{resource_type.value}:{resource_id}"

Note: Line 209 in get_owned_resources needs key parsing adjustment:
  Change from: _, resource_id = resource_key.split(":", 1)
  To:          _, _, resource_id = resource_key.split(":", 2)
""")
    
    return test_passes

if __name__ == "__main__":
    result = asyncio.run(validate_fix())
    sys.exit(0 if result else 1)
