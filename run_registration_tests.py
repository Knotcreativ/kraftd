#!/usr/bin/env python3
"""
Phase 2 Runtime Testing - Registration Endpoint Tests
Connects to running backend instance
"""
import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "http://127.0.0.1:8000"
TEST_RESULTS = []

def log_test(name, passed, details=""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"   Details: {details}")
    TEST_RESULTS.append({
        "name": name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

def test_health_endpoint():
    """Test 1: Health endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
        success = response.status_code == 200
        log_test("Health Endpoint", success, f"Status: {response.status_code}")
        return success
    except Exception as e:
        log_test("Health Endpoint", False, str(e))
        return False

def test_valid_registration():
    """Test 2: Valid registration"""
    data = {
        "email": "validuser@example.com",
        "password": "SecurePass123!",
        "acceptTerms": True,
        "acceptPrivacy": True,
        "name": "Valid User",
        "marketingOptIn": False
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=data,
            timeout=10
        )
        success = response.status_code == 201
        body = response.json()
        log_test(
            "Valid Registration (201)",
            success,
            f"Status: {response.status_code}, Response: {json.dumps(body)[:100]}"
        )
        return success
    except Exception as e:
        log_test("Valid Registration (201)", False, str(e))
        return False

def test_invalid_email_format():
    """Test 3: Invalid email format"""
    data = {
        "email": "not-an-email",
        "password": "SecurePass123!",
        "acceptTerms": True,
        "acceptPrivacy": True
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=data,
            timeout=10
        )
        success = response.status_code == 400
        body = response.json()
        log_test(
            "Invalid Email Format (400)",
            success,
            f"Status: {response.status_code}"
        )
        return success
    except Exception as e:
        log_test("Invalid Email Format (400)", False, str(e))
        return False

def test_weak_password():
    """Test 4: Weak password (too short)"""
    data = {
        "email": "test@example.com",
        "password": "short",
        "acceptTerms": True,
        "acceptPrivacy": True
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=data,
            timeout=10
        )
        success = response.status_code == 400
        log_test(
            "Weak Password - Too Short (400)",
            success,
            f"Status: {response.status_code}"
        )
        return success
    except Exception as e:
        log_test("Weak Password - Too Short (400)", False, str(e))
        return False

def test_password_with_spaces():
    """Test 5: Password with spaces"""
    data = {
        "email": "test@example.com",
        "password": "Pass word 123",
        "acceptTerms": True,
        "acceptPrivacy": True
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=data,
            timeout=10
        )
        success = response.status_code == 400
        log_test(
            "Password With Spaces (400)",
            success,
            f"Status: {response.status_code}"
        )
        return success
    except Exception as e:
        log_test("Password With Spaces (400)", False, str(e))
        return False

def test_password_contains_email():
    """Test 6: Password contains email"""
    data = {
        "email": "user@example.com",
        "password": "user@example.com123!",
        "acceptTerms": True,
        "acceptPrivacy": True
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=data,
            timeout=10
        )
        success = response.status_code == 400
        log_test(
            "Password Contains Email (400)",
            success,
            f"Status: {response.status_code}"
        )
        return success
    except Exception as e:
        log_test("Password Contains Email (400)", False, str(e))
        return False

def test_missing_terms_acceptance():
    """Test 7: Missing terms acceptance"""
    data = {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "acceptTerms": False,
        "acceptPrivacy": True
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=data,
            timeout=10
        )
        success = response.status_code == 400
        log_test(
            "Missing Terms Acceptance (400)",
            success,
            f"Status: {response.status_code}"
        )
        return success
    except Exception as e:
        log_test("Missing Terms Acceptance (400)", False, str(e))
        return False

def test_missing_privacy_acceptance():
    """Test 8: Missing privacy acceptance"""
    data = {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "acceptTerms": True,
        "acceptPrivacy": False
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=data,
            timeout=10
        )
        success = response.status_code == 400
        log_test(
            "Missing Privacy Acceptance (400)",
            success,
            f"Status: {response.status_code}"
        )
        return success
    except Exception as e:
        log_test("Missing Privacy Acceptance (400)", False, str(e))
        return False

def test_duplicate_email():
    """Test 9: Duplicate email"""
    email = f"duplicate{datetime.now().timestamp()}@example.com"
    data = {
        "email": email,
        "password": "SecurePass123!",
        "acceptTerms": True,
        "acceptPrivacy": True
    }
    
    try:
        # First registration
        response1 = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=data,
            timeout=10
        )
        
        if response1.status_code != 201:
            log_test("Duplicate Email - First Registration", False, f"First registration failed: {response1.status_code}")
            return False
        
        # Second registration (should fail)
        response2 = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=data,
            timeout=10
        )
        success = response2.status_code == 409
        log_test(
            "Duplicate Email Returns 409",
            success,
            f"Status: {response2.status_code}"
        )
        return success
    except Exception as e:
        log_test("Duplicate Email Returns 409", False, str(e))
        return False

def test_login_after_registration():
    """Test 10: Login after registration"""
    email = f"logintest{datetime.now().timestamp()}@example.com"
    password = "SecurePass123!"
    
    # Register
    reg_data = {
        "email": email,
        "password": password,
        "acceptTerms": True,
        "acceptPrivacy": True,
        "name": "Login Test User"
    }
    
    try:
        reg_response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=reg_data,
            timeout=10
        )
        
        if reg_response.status_code != 201:
            log_test("Login After Registration", False, f"Registration failed: {reg_response.status_code}")
            return False
        
        # Login
        login_data = {
            "email": email,
            "password": password
        }
        
        login_response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json=login_data,
            timeout=10
        )
        
        success = login_response.status_code == 200
        if success:
            body = login_response.json()
            has_tokens = "access_token" in body and "refresh_token" in body
            success = has_tokens
            log_test(
                "Login After Registration",
                success,
                f"Status: {login_response.status_code}, Has tokens: {has_tokens}"
            )
        else:
            log_test(
                "Login After Registration",
                False,
                f"Login failed with status: {login_response.status_code}"
            )
        return success
    except Exception as e:
        log_test("Login After Registration", False, str(e))
        return False

def main():
    """Run all tests"""
    print("=" * 70)
    print("Phase 2: User Registration Runtime Testing")
    print("=" * 70)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Start Time: {datetime.now().isoformat()}")
    print("=" * 70)
    print()
    
    tests = [
        ("Test 1", test_health_endpoint),
        ("Test 2", test_valid_registration),
        ("Test 3", test_invalid_email_format),
        ("Test 4", test_weak_password),
        ("Test 5", test_password_with_spaces),
        ("Test 6", test_password_contains_email),
        ("Test 7", test_missing_terms_acceptance),
        ("Test 8", test_missing_privacy_acceptance),
        ("Test 9", test_duplicate_email),
        ("Test 10", test_login_after_registration),
    ]
    
    print("Running Tests:")
    print("-" * 70)
    
    for name, test_func in tests:
        test_func()
    
    # Summary
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for r in TEST_RESULTS if r["passed"])
    total = len(TEST_RESULTS)
    
    for result in TEST_RESULTS:
        status = "✅" if result["passed"] else "❌"
        print(f"{status} {result['name']}")
    
    print()
    print(f"Total: {passed}/{total} tests passed ({passed*100//total}%)")
    print()
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} tests failed")
    
    print()
    print("=" * 70)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
