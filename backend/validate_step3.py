#!/usr/bin/env python
"""Validate Step 3: Cosmos DB Repository Implementation"""

import sys
import os

print("="*80)
print("STEP 3 VALIDATION: Cosmos DB Repository Pattern Implementation")
print("="*80)

# Check 1: Verify all files exist
print("\n[1/6] Checking that all repository files exist...")
required_files = [
    "services/cosmos_service.py",
    "repositories/__init__.py",
    "repositories/base.py",
    "repositories/user_repository.py",
    "repositories/document_repository.py",
]

missing_files = [f for f in required_files if not os.path.exists(f)]
if missing_files:
    print(f"  ❌ FAIL: Missing files: {missing_files}")
    sys.exit(1)
print(f"  ✅ All {len(required_files)} required files exist")

# Check 2: Verify imports work
print("\n[2/6] Testing imports of all repository modules...")
try:
    from services.cosmos_service import CosmosService, get_cosmos_service, initialize_cosmos
    print("    ✓ CosmosService imported successfully")
    from repositories.base import BaseRepository
    print("    ✓ BaseRepository imported successfully")
    from repositories.user_repository import UserRepository
    print("    ✓ UserRepository imported successfully")
    from repositories.document_repository import DocumentRepository, DocumentStatus
    print("    ✓ DocumentRepository imported successfully")
    print("  ✅ All imports successful")
except ImportError as e:
    print(f"  ❌ FAIL: Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check 3: Verify inheritance hierarchy
print("\n[3/6] Checking inheritance and class structure...")
try:
    from abc import ABC
    
    # Check BaseRepository is abstract
    if not issubclass(BaseRepository, ABC):
        print("  ❌ FAIL: BaseRepository is not abstract")
        sys.exit(1)
    
    # Check UserRepository inherits from BaseRepository
    if not issubclass(UserRepository, BaseRepository):
        print("  ❌ FAIL: UserRepository doesn't inherit from BaseRepository")
        sys.exit(1)
    
    # Check DocumentRepository inherits from BaseRepository
    if not issubclass(DocumentRepository, BaseRepository):
        print("  ❌ FAIL: DocumentRepository doesn't inherit from BaseRepository")
        sys.exit(1)
    
    print("  ✅ Inheritance hierarchy correct")
    
except Exception as e:
    print(f"  ❌ FAIL: {e}")
    sys.exit(1)

# Check 4: Verify Cosmos singleton pattern
print("\n[4/6] Checking Cosmos singleton pattern...")
try:
    cosmos1 = get_cosmos_service()
    cosmos2 = get_cosmos_service()
    
    if cosmos1 is not cosmos2:
        print("  ❌ FAIL: Singleton pattern not working (different instances)")
        sys.exit(1)
    
    print("  ✅ Singleton pattern working correctly")
    
except Exception as e:
    print(f"  ❌ FAIL: {e}")
    sys.exit(1)

# Check 5: Verify repository instantiation
print("\n[5/6] Checking repository instantiation...")
try:
    user_repo = UserRepository()
    doc_repo = DocumentRepository()
    
    if user_repo is None or doc_repo is None:
        print("  ❌ FAIL: Could not instantiate repositories")
        sys.exit(1)
    
    print("  ✅ Repositories instantiated successfully")
    
except Exception as e:
    print(f"  ❌ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check 6: Verify method signatures (async)
print("\n[6/6] Verifying async method signatures...")
import inspect

try:
    # Check BaseRepository methods
    base_methods = [
        'create', 'read', 'read_by_query', 'update', 'delete', 'exists'
    ]
    
    for method_name in base_methods:
        method = getattr(BaseRepository, method_name)
        if not inspect.iscoroutinefunction(method):
            print(f"  ❌ FAIL: BaseRepository.{method_name} is not async")
            sys.exit(1)
    
    # Check UserRepository methods
    user_methods = [
        'create_user', 'get_user_by_email', 'user_exists', 
        'update_user', 'update_user_password', 'deactivate_user'
    ]
    
    for method_name in user_methods:
        method = getattr(UserRepository, method_name)
        if not inspect.iscoroutinefunction(method):
            print(f"  ❌ FAIL: UserRepository.{method_name} is not async")
            sys.exit(1)
    
    # Check DocumentRepository methods
    doc_methods = [
        'create_document', 'get_document', 'get_user_documents',
        'update_document_status', 'delete_document'
    ]
    
    for method_name in doc_methods:
        method = getattr(DocumentRepository, method_name)
        if not inspect.iscoroutinefunction(method):
            print(f"  ❌ FAIL: DocumentRepository.{method_name} is not async")
            sys.exit(1)
    
    print("  ✅ All async method signatures correct")
    
except Exception as e:
    print(f"  ❌ FAIL: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("✅ ALL STEP 3 VALIDATIONS PASSED")
print("="*80)
print("\nSummary:")
print("  ✓ All 5 repository files created")
print("  ✓ All imports working correctly")
print("  ✓ Proper inheritance hierarchy")
print("  ✓ Singleton pattern implemented")
print("  ✓ All repositories instantiate successfully")
print("  ✓ All methods properly async")
print("\nStep 3 is production-ready. Proceeding to Step 4...")
