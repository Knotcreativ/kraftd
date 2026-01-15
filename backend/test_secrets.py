#!/usr/bin/env python
"""Test script to verify JWT secret is loaded from secure storage, not hardcoded."""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_secrets_manager():
    """Test that secrets are loaded correctly from env variables."""
    
    print("\n" + "="*60)
    print("Testing JWT Secret Management")
    print("="*60 + "\n")
    
    # Test 1: Load from environment variable
    print("✓ Test 1: Loading JWT secret from environment variable")
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-from-environment-minimum-32-chars-long-secret"
    
    try:
        from services.secrets_manager import SecretsManager
        secrets = SecretsManager()
        secret = secrets.get_jwt_secret()
        
        if secret == "test-secret-key-from-environment-minimum-32-chars-long-secret":
            print("  ✅ PASS: Secret loaded from environment variable correctly")
        else:
            print(f"  ❌ FAIL: Got unexpected secret: {secret[:20]}...")
            return False
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False
    
    # Test 2: Fallback to default in dev mode
    print("\n✓ Test 2: Fallback behavior when secret not set")
    del os.environ["JWT_SECRET_KEY"]
    os.environ["ENVIRONMENT"] = "development"
    
    try:
        from services.secrets_manager import SecretsManager
        secrets = SecretsManager()
        secret = secrets.get_jwt_secret()
        
        if secret:
            print(f"  ✅ PASS: Fallback secret retrieved (length: {len(secret)} chars)")
        else:
            print("  ❌ FAIL: No fallback secret")
            return False
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False
    
    # Test 3: Verify auth_service uses the secret manager
    print("\n✓ Test 3: Verify AuthService uses SecretManager (no hardcoded SECRET_KEY)")
    try:
        with open("services/auth_service.py", "r") as f:
            content = f.read()
            
        # Check that hardcoded SECRET_KEY is gone
        if 'SECRET_KEY = os.getenv("JWT_SECRET_KEY"' in content:
            print("  ❌ FAIL: Hardcoded SECRET_KEY still exists in auth_service.py")
            return False
        
        # Check that secrets_manager is imported
        if "from services.secrets_manager import" not in content:
            print("  ❌ FAIL: auth_service.py doesn't import secrets_manager")
            return False
        
        # Check that _get_secret_key is defined
        if "def _get_secret_key()" not in content:
            print("  ❌ FAIL: _get_secret_key function not defined")
            return False
        
        # Check that create_access_token uses _get_secret_key
        if "_get_secret_key()" not in content:
            print("  ❌ FAIL: AuthService methods don't call _get_secret_key()")
            return False
        
        print("  ✅ PASS: AuthService properly integrated with SecretManager")
        
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False
    
    # Test 4: Create and verify a token
    print("\n✓ Test 4: Create and verify JWT tokens")
    try:
        # Set a known secret for testing
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-minimum-32-characters-long-key-for-testing-purposes"
        
        from services.auth_service import AuthService
        
        # Create a token
        token = AuthService.create_access_token("test@example.com")
        if not token:
            print("  ❌ FAIL: Could not create token")
            return False
        
        # Verify the token
        payload = AuthService.verify_token(token)
        if not payload or payload.get("sub") != "test@example.com":
            print("  ❌ FAIL: Token verification failed")
            return False
        
        print("  ✅ PASS: JWT tokens created and verified successfully")
        
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("All tests passed! ✅")
    print("="*60 + "\n")
    return True


if __name__ == "__main__":
    success = test_secrets_manager()
    sys.exit(0 if success else 1)
