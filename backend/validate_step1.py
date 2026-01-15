#!/usr/bin/env python
"""Validate Step 1: JWT Secret Management"""

import sys
import os

print("="*80)
print("STEP 1 VALIDATION: JWT Secret Management")
print("="*80)

# Check 1: secrets_manager.py exists and imports
print("\n[1/6] Checking secrets_manager.py exists...")
if not os.path.exists("services/secrets_manager.py"):
    print("  ❌ FAIL: secrets_manager.py not found")
    sys.exit(1)
print("  ✅ File exists")

# Check 2: Import secrets_manager
print("\n[2/6] Importing SecretsManager...")
try:
    from services.secrets_manager import SecretsManager, get_secrets_manager, initialize_secrets
    print("  ✅ Import successful")
except ImportError as e:
    print(f"  ❌ FAIL: {e}")
    sys.exit(1)

# Check 3: Import auth_service
print("\n[3/6] Importing AuthService...")
try:
    from services.auth_service import AuthService
    print("  ✅ Import successful")
except ImportError as e:
    print(f"  ❌ FAIL: {e}")
    sys.exit(1)

# Check 4: Verify no hardcoded SECRET_KEY in auth_service.py
print("\n[4/6] Verifying no hardcoded SECRET_KEY in auth_service.py...")
with open("services/auth_service.py", "r") as f:
    content = f.read()
    # Check that old pattern is gone
    if "your-secret-key-change-in-production" in content:
        print("  ❌ FAIL: Hardcoded secret default still in code")
        sys.exit(1)
    if "_get_secret_key()" not in content:
        print("  ❌ FAIL: _get_secret_key() not used")
        sys.exit(1)
    if "from services.secrets_manager import" not in content:
        print("  ❌ FAIL: secrets_manager not imported")
        sys.exit(1)
print("  ✅ auth_service.py properly integrated")

# Check 5: Test secret retrieval
print("\n[5/6] Testing secret retrieval with environment variable...")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-from-environment-minimum-32-chars-long-secret"
try:
    secrets = SecretsManager()
    secret = secrets.get_jwt_secret()
    if secret != "test-secret-key-from-environment-minimum-32-chars-long-secret":
        print(f"  ❌ FAIL: Got unexpected secret: {secret[:20]}...")
        sys.exit(1)
    print("  ✅ Secret retrieved correctly")
except Exception as e:
    print(f"  ❌ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check 6: Test JWT token creation and verification
print("\n[6/6] Testing JWT token creation and verification...")
try:
    token = AuthService.create_access_token("test@example.com")
    payload = AuthService.verify_token(token)
    if not payload or payload.get("sub") != "test@example.com":
        print("  ❌ FAIL: Token verification failed")
        sys.exit(1)
    print("  ✅ JWT tokens work correctly")
except Exception as e:
    print(f"  ❌ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("✅ ALL STEP 1 VALIDATIONS PASSED")
print("="*80)
print("\nStep 1 is production-ready. Proceeding to Step 2...")
