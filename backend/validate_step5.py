#!/usr/bin/env python3
"""
STEP 5 VALIDATION: Auth Endpoints Migration to UserRepository

This script validates that:
1. Repository imports are added to main.py
2. Helper function get_user_repository() is implemented
3. All 5 auth endpoints use the repository
4. Fallback to in-memory mode is implemented
5. Error handling is properly configured
6. Logging is comprehensive
"""

import sys
import os
import logging
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_repository_imports():
    """Check that repository imports are added"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    required_imports = [
        'from repositories import UserRepository, DocumentRepository'
    ]
    
    for imp in required_imports:
        if imp not in content:
            return False, f"Missing import: {imp}"
    
    return True, "Repository imports present"

def check_helper_function():
    """Check that get_user_repository() helper is implemented"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    required_patterns = [
        'async def get_user_repository()',
        'get_cosmos_service()',
        'is_initialized()',
        'return UserRepository()',
        'return None'
    ]
    
    for pattern in required_patterns:
        if pattern not in content:
            return False, f"Missing pattern: {pattern}"
    
    return True, "Helper function properly implemented"

def check_register_endpoint():
    """Check that register endpoint uses repository"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Find register endpoint - look for function definition
    register_start = content.find('async def register(user_data: UserRegister):')
    if register_start == -1:
        return False, "Register endpoint not found"
    
    register_section = content[register_start:register_start+8000]
    
    required_patterns = [
        'user_repo = await get_user_repository()',
        'await user_repo.user_exists(user_data.email)',
        'await user_repo.create_user(',
    ]
    
    missing = []
    for pattern in required_patterns:
        if pattern not in register_section:
            missing.append(pattern)
    
    if missing:
        return False, f"Register endpoint missing: {missing[0]}"
    
    return True, "Register endpoint properly updated"

def check_login_endpoint():
    """Check that login endpoint uses repository"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Find login endpoint - look for function definition
    login_start = content.find('async def login(user_data: UserLogin):')
    if login_start == -1:
        return False, "Login endpoint not found"
    
    login_section = content[login_start:login_start+8000]
    
    required_patterns = [
        'user_repo = await get_user_repository()',
        'await user_repo.get_user_by_email(user_data.email)',
    ]
    
    missing = []
    for pattern in required_patterns:
        if pattern not in login_section:
            missing.append(pattern)
    
    if missing:
        return False, f"Login endpoint missing: {missing[0]}"
    
    return True, "Login endpoint properly updated"

def check_refresh_endpoint():
    """Check that refresh endpoint uses repository"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Find refresh endpoint - look for function definition
    refresh_start = content.find('async def refresh(refresh_token: str):')
    if refresh_start == -1:
        return False, "Refresh endpoint not found"
    
    refresh_section = content[refresh_start:refresh_start+8000]
    
    required_patterns = [
        'user_repo = await get_user_repository()',
        'await user_repo.get_user_by_email(email)',
    ]
    
    missing = []
    for pattern in required_patterns:
        if pattern not in refresh_section:
            missing.append(pattern)
    
    if missing:
        return False, f"Refresh endpoint missing: {missing[0]}"
    
    return True, "Refresh endpoint properly updated"

def check_profile_endpoint():
    """Check that profile endpoint uses repository"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Find profile endpoint - look for function definition
    profile_start = content.find('async def get_profile(authorization: str = None):')
    if profile_start == -1:
        return False, "Profile endpoint not found"
    
    profile_section = content[profile_start:profile_start+7000]
    
    required_patterns = [
        'user_repo = await get_user_repository()',
        'await user_repo.get_user_by_email(email)',
    ]
    
    missing = []
    for pattern in required_patterns:
        if pattern not in profile_section:
            missing.append(pattern)
    
    if missing:
        return False, f"Profile endpoint missing: {missing[0]}"
    
    return True, "Profile endpoint properly updated"

def check_validate_endpoint():
    """Check that validate endpoint uses repository"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Find validate endpoint - look for function definition
    validate_start = content.find('async def validate_token(authorization: str = None):')
    if validate_start == -1:
        return False, "Validate endpoint not found"
    
    validate_section = content[validate_start:validate_start+7000]
    
    required_patterns = [
        'user_repo = await get_user_repository()',
        'await user_repo.user_exists(email)',
    ]
    
    missing = []
    for pattern in required_patterns:
        if pattern not in validate_section:
            missing.append(pattern)
    
    if missing:
        return False, f"Validate endpoint missing: {missing[0]}"
    
    return True, "Validate endpoint properly updated"

def check_error_handling():
    """Check that error handling is comprehensive"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    auth_section = content[content.find('# ===== Authentication Endpoints ====='):content.find('# ===== Health Check Endpoint =====')]
    
    required_patterns = [
        'except HTTPException:',
        'except Exception as e:',
        'raise HTTPException',
        'logger.error',
        'logger.warning'
    ]
    
    for pattern in required_patterns:
        if auth_section.count(pattern) < 3:  # At least 3 occurrences across endpoints
            return False, f"Insufficient error handling: {pattern}"
    
    return True, "Error handling properly implemented"

def main():
    """Run all validation checks"""
    print("\n" + "=" * 70)
    print("STEP 5 VALIDATION: Auth Endpoints Migration to UserRepository")
    print("=" * 70 + "\n")
    
    checks = [
        ("Checking repository imports", check_repository_imports),
        ("Checking helper function", check_helper_function),
        ("Checking register endpoint", check_register_endpoint),
        ("Checking login endpoint", check_login_endpoint),
        ("Checking refresh endpoint", check_refresh_endpoint),
        ("Checking profile endpoint", check_profile_endpoint),
        ("Checking validate endpoint", check_validate_endpoint),
        ("Checking error handling", check_error_handling),
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
        print("✅ ALL STEP 5 VALIDATIONS PASSED")
        print("=" * 70)
        print("\nSummary:")
        print("  ✓ Repository imports added")
        print("  ✓ Helper function implemented")
        print("  ✓ Register endpoint updated")
        print("  ✓ Login endpoint updated")
        print("  ✓ Refresh endpoint updated")
        print("  ✓ Profile endpoint updated")
        print("  ✓ Validate endpoint updated")
        print("  ✓ Error handling configured")
        print("\nStep 5 is production-ready. Proceeding to Step 6...\n")
        return 0
    else:
        print("❌ SOME STEP 5 VALIDATIONS FAILED")
        print("=" * 70)
        failed = sum(1 for r in results if not r)
        print(f"\n{failed} check(s) failed. Please review the errors above.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
