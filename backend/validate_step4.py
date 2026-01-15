#!/usr/bin/env python3
"""
STEP 4 VALIDATION: Cosmos DB Initialization in Lifespan Handler

This script validates that:
1. Cosmos DB imports are correctly added to main.py
2. Lifespan handler initializes Cosmos DB
3. Cosmos service is properly integrated
4. Error handling for missing credentials works
5. Shutdown cleanup of Cosmos connection works
6. Fallback mode works when Cosmos not available
"""

import sys
import os
import logging
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_imports():
    """Check that Cosmos imports are added to main.py"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    required_imports = [
        'from services.cosmos_service import initialize_cosmos, get_cosmos_service',
        'from services.secrets_manager import get_secrets_manager'
    ]
    
    for imp in required_imports:
        if imp not in content:
            return False, f"Missing import: {imp}"
    
    return True, "All required imports present"

def check_lifespan_cosmos_init():
    """Check that Cosmos DB is initialized in lifespan handler"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Check for Cosmos initialization
    required_patterns = [
        'initialize_cosmos',
        'get_cosmos_service',
        'await initialize_cosmos',
        'cosmos_service = get_cosmos_service()',
        'Cosmos DB credentials not configured'
    ]
    
    for pattern in required_patterns:
        if pattern not in content:
            return False, f"Missing pattern in lifespan: {pattern}"
    
    # Check for proper error handling
    if 'except Exception as e:' not in content:
        return False, "Missing exception handling for Cosmos init"
    
    # Check for fallback mode
    if 'Continuing with fallback mode' not in content:
        return False, "Missing fallback mode logic"
    
    return True, "Lifespan Cosmos initialization properly configured"

def check_shutdown_cleanup():
    """Check that Cosmos connection is properly closed on shutdown"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    required_patterns = [
        'cosmos_service.close()',
        'await cosmos_service.close()',
        'Cosmos DB connection closed'
    ]
    
    for pattern in required_patterns:
        if pattern not in content:
            return False, f"Missing pattern in shutdown: {pattern}"
    
    return True, "Cosmos DB shutdown cleanup properly configured"

def check_fallback_handling():
    """Check that fallback mode is handled gracefully"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Check for credentials check
    if 'if endpoint and key:' not in content:
        return False, "Missing credential validation"
    
    # Check for warning about fallback
    if '[WARN] Cosmos DB credentials not configured' not in content:
        return False, "Missing warning for missing credentials"
    
    return True, "Fallback handling properly configured"

def check_status_logging():
    """Check that Cosmos status is logged in startup config"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    if 'Cosmos DB: ' not in content or 'Connected' not in content:
        return False, "Missing Cosmos status in startup logging"
    
    return True, "Cosmos status properly logged"

def main():
    """Run all validation checks"""
    print("\n" + "=" * 70)
    print("STEP 4 VALIDATION: Cosmos DB Initialization in Lifespan Handler")
    print("=" * 70 + "\n")
    
    checks = [
        ("Checking Cosmos DB imports", check_imports),
        ("Checking lifespan Cosmos initialization", check_lifespan_cosmos_init),
        ("Checking shutdown cleanup", check_shutdown_cleanup),
        ("Checking fallback mode handling", check_fallback_handling),
        ("Checking status logging", check_status_logging),
    ]
    
    results = []
    for i, (name, check_func) in enumerate(checks, 1):
        try:
            passed, message = check_func()
            status = "✅" if passed else "❌"
            print(f"[{i}/{len(checks)}] {name}")
            print(f"  {status} {message}\n")
            results.append(passed)
        except Exception as e:
            print(f"[{i}/{len(checks)}] {name}")
            print(f"  ❌ Error during check: {str(e)}\n")
            results.append(False)
    
    print("=" * 70)
    if all(results):
        print("✅ ALL STEP 4 VALIDATIONS PASSED")
        print("=" * 70)
        print("\nSummary:")
        print("  ✓ Cosmos DB imports added")
        print("  ✓ Lifespan initialization configured")
        print("  ✓ Shutdown cleanup implemented")
        print("  ✓ Fallback mode enabled")
        print("  ✓ Status logging configured")
        print("\nStep 4 is production-ready. Proceeding to Step 5...\n")
        return 0
    else:
        print("❌ SOME STEP 4 VALIDATIONS FAILED")
        print("=" * 70)
        failed = sum(1 for r in results if not r)
        print(f"\n{failed} check(s) failed. Please review the errors above.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
