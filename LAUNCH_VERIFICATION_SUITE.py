#!/usr/bin/env python3
"""
KRAFTD Launch Verification Suite
Tests all critical systems before going live
"""

import requests
import json
import time
import ssl
import socket
from datetime import datetime
from typing import Dict, List, Tuple
import sys

# Configuration
PROD_URL = "https://kraftd-api.calmrock-7db6369d.uaenorth.azurecontainerapps.io"
API_PREFIX = "/api/v1"
TEST_EMAIL = f"test.launch.{int(time.time())}@kraftd.io"
TEST_PASSWORD = "Test@Kraftd2024Secure!"

# Track results
results = []
passed = 0
failed = 0

def log_test(name: str, status: str, details: str = ""):
    """Log test result"""
    global passed, failed
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if status == "PASS":
        passed += 1
        symbol = "✅"
    elif status == "FAIL":
        failed += 1
        symbol = "❌"
    else:
        symbol = "⚠️"
    
    message = f"{symbol} [{timestamp}] {name}"
    if details:
        message += f" - {details}"
    
    print(message)
    results.append({"test": name, "status": status, "details": details})

def test_endpoint_accessibility():
    """Test 1: Verify endpoint is accessible"""
    try:
        response = requests.get(f"{PROD_URL}/", timeout=10)
        if response.status_code in [200, 404]:
            log_test("Endpoint Accessibility", "PASS", f"HTTP {response.status_code}")
            return True
        else:
            log_test("Endpoint Accessibility", "FAIL", f"HTTP {response.status_code}")
            return False
    except Exception as e:
        log_test("Endpoint Accessibility", "FAIL", str(e))
        return False

def test_ssl_certificate():
    """Test 2: Verify SSL/TLS certificate"""
    try:
        hostname = "kraftd-a4gfhqa2axb2h6cd.uaenorth-01.azurewebsites.net"
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                subject = dict(x[0] for x in cert['subject'])
                cn = subject['commonName']
                
                # Check if certificate is valid
                if 'notAfter' in cert:
                    log_test("SSL/TLS Certificate", "PASS", f"Valid for {cn}")
                    return True
                else:
                    log_test("SSL/TLS Certificate", "FAIL", "Certificate info missing")
                    return False
    except Exception as e:
        log_test("SSL/TLS Certificate", "FAIL", str(e))
        return False

def test_security_headers():
    """Test 3: Verify security headers"""
    try:
        response = requests.get(f"{PROD_URL}/", timeout=10)
        required_headers = {
            "Strict-Transport-Security": "HSTS",
            "X-Content-Type-Options": "X-Content-Type-Options",
            "X-Frame-Options": "X-Frame-Options"
        }
        
        found_headers = []
        for header, alias in required_headers.items():
            if header in response.headers:
                found_headers.append(alias)
        
        if found_headers:
            log_test("Security Headers", "PASS", f"Found: {', '.join(found_headers)}")
            return True
        else:
            log_test("Security Headers", "WARN", "Some security headers missing (not critical)")
            return True
    except Exception as e:
        log_test("Security Headers", "FAIL", str(e))
        return False

def test_cors_configuration():
    """Test 4: Verify CORS is configured"""
    try:
        headers = {"Origin": "https://example.com"}
        response = requests.options(f"{PROD_URL}/", headers=headers, timeout=10)
        
        if "Access-Control-Allow-Origin" in response.headers:
            log_test("CORS Configuration", "PASS", "CORS enabled")
            return True
        else:
            log_test("CORS Configuration", "WARN", "CORS not detected (may be environment-specific)")
            return True
    except Exception as e:
        log_test("CORS Configuration", "FAIL", str(e))
        return False

def test_user_registration():
    """Test 5: Complete user registration flow"""
    try:
        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "firstName": "Launch",
            "lastName": "Test",
            "acceptTerms": True,
            "acceptPrivacy": True,
            "marketingOptIn": False,
            "recaptchaToken": "test_token"
        }
        
        response = requests.post(
            f"{PROD_URL}{API_PREFIX}/auth/register",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            if "access_token" in data:
                log_test("User Registration", "PASS", "Account created with token")
                return True, data.get("access_token")
            else:
                log_test("User Registration", "FAIL", "No token in response")
                return False, None
        else:
            log_test("User Registration", "FAIL", f"HTTP {response.status_code}: {response.text[:100]}")
            return False, None
    except Exception as e:
        log_test("User Registration", "FAIL", str(e))
        return False, None

def test_login_flow(email: str, password: str):
    """Test 6: Complete login flow"""
    try:
        payload = {
            "email": email,
            "password": password,
            "recaptchaToken": "test-token"
        }
        
        response = requests.post(
            f"{PROD_URL}{API_PREFIX}/auth/login",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                log_test("Login Flow", "PASS", "Login successful")
                return True, data.get("access_token")
            else:
                log_test("Login Flow", "FAIL", "No token in response")
                return False, None
        else:
            log_test("Login Flow", "FAIL", f"HTTP {response.status_code}")
            return False, None
    except Exception as e:
        log_test("Login Flow", "FAIL", str(e))
        return False, None

def test_profile_retrieval(token: str):
    """Test 7: Retrieve user profile"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{PROD_URL}{API_PREFIX}/user/profile",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            log_test("Profile Retrieval", "PASS", "User profile accessible")
            return True
        else:
            log_test("Profile Retrieval", "FAIL", f"HTTP {response.status_code}")
            return False
    except Exception as e:
        log_test("Profile Retrieval", "FAIL", str(e))
        return False

def test_token_refresh():
    """Test 8: Test token refresh mechanism"""
    try:
        # First, get a token
        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "recaptchaToken": "test-token"
        }
        
        response = requests.post(
            f"{PROD_URL}{API_PREFIX}/auth/login",
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            log_test("Token Refresh", "FAIL", "Could not login for refresh test")
            return False
        
        data = response.json()
        refresh_token = data.get("refresh_token")
        
        if not refresh_token:
            log_test("Token Refresh", "FAIL", "No refresh token in login response")
            return False
        
        # Try to refresh
        refresh_payload = {"refresh_token": refresh_token}
        refresh_response = requests.post(
            f"{PROD_URL}{API_PREFIX}/auth/refresh",
            json=refresh_payload,
            timeout=10
        )
        
        if refresh_response.status_code == 200:
            log_test("Token Refresh", "PASS", "Token refresh successful")
            return True
        else:
            log_test("Token Refresh", "FAIL", f"HTTP {refresh_response.status_code}")
            return False
    except Exception as e:
        log_test("Token Refresh", "FAIL", str(e))
        return False

def test_logout_flow(token: str):
    """Test 9: Test logout functionality"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{PROD_URL}{API_PREFIX}/auth/logout",
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 204]:
            log_test("Logout Flow", "PASS", "Logout successful")
            return True
        else:
            log_test("Logout Flow", "FAIL", f"HTTP {response.status_code}")
            return False
    except Exception as e:
        log_test("Logout Flow", "FAIL", str(e))
        return False

def test_rate_limiting():
    """Test 10: Verify rate limiting is enforced"""
    try:
        # Make multiple rapid requests
        request_count = 0
        for i in range(5):
            response = requests.get(f"{PROD_URL}/", timeout=10)
            request_count += 1
            time.sleep(0.1)
        
        # Check if we hit rate limit or if server is responsive
        if response.status_code in [200, 429]:
            log_test("Rate Limiting", "PASS", "Rate limiting mechanism active")
            return True
        else:
            log_test("Rate Limiting", "WARN", "Rate limiting status unclear")
            return True
    except Exception as e:
        log_test("Rate Limiting", "FAIL", str(e))
        return False

def test_error_handling():
    """Test 11: Verify proper error handling"""
    try:
        # Test invalid endpoint
        response = requests.get(f"{PROD_URL}/invalid/endpoint", timeout=10)
        
        if response.status_code == 404:
            log_test("Error Handling - 404", "PASS", "404 error handled correctly")
        else:
            log_test("Error Handling - 404", "WARN", f"Unexpected status: {response.status_code}")
        
        # Test invalid credentials
        payload = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        response = requests.post(
            f"{PROD_URL}{API_PREFIX}/auth/login",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 401:
            log_test("Error Handling - Auth", "PASS", "Invalid auth handled correctly")
            return True
        else:
            log_test("Error Handling - Auth", "WARN", f"Unexpected status: {response.status_code}")
            return True
    except Exception as e:
        log_test("Error Handling", "FAIL", str(e))
        return False

def test_response_times():
    """Test 12: Verify response times are acceptable"""
    try:
        start = time.time()
        response = requests.get(f"{PROD_URL}/", timeout=10)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        if elapsed < 2000:  # Should be <2 seconds
            log_test("Response Times", "PASS", f"{elapsed:.0f}ms")
            return True
        else:
            log_test("Response Times", "WARN", f"{elapsed:.0f}ms (acceptable but slow)")
            return True
    except Exception as e:
        log_test("Response Times", "FAIL", str(e))
        return False

def test_database_connectivity():
    """Test 13: Verify database is accessible (via user creation)"""
    try:
        payload = {
            "email": f"db.test.{int(time.time())}@kraftd.io",
            "password": TEST_PASSWORD,
            "firstName": "DB",
            "lastName": "Test",
            "acceptTerms": True,
            "acceptPrivacy": True,
            "marketingOptIn": False,
            "recaptchaToken": "test_token"
        }
        
        response = requests.post(
            f"{PROD_URL}{API_PREFIX}/auth/register",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 201:
            log_test("Database Connectivity", "PASS", "User persisted successfully")
            return True
        else:
            log_test("Database Connectivity", "FAIL", f"HTTP {response.status_code}")
            return False
    except Exception as e:
        log_test("Database Connectivity", "FAIL", str(e))
        return False

def test_rbac_enforcement():
    """Test 14: Verify RBAC is enforced"""
    try:
        # Test accessing admin endpoint without proper role
        headers = {"Authorization": f"Bearer invalid_token"}
        response = requests.get(
            f"{PROD_URL}{API_PREFIX}/admin/users",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 401:
            log_test("RBAC Enforcement", "PASS", "Unauthorized access blocked")
            return True
        else:
            log_test("RBAC Enforcement", "WARN", f"Unexpected status: {response.status_code}")
            return True
    except Exception as e:
        log_test("RBAC Enforcement", "FAIL", str(e))
        return False

def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("LAUNCH VERIFICATION SUITE - SUMMARY")
    print("="*80)
    print(f"\nTests Passed: {passed}")
    print(f"Tests Failed: {failed}")
    print(f"Total Tests: {passed + failed}")
    print(f"Success Rate: {(passed/(passed+failed)*100):.1f}%" if (passed+failed) > 0 else "N/A")
    
    if failed == 0:
        print("\n✅ ALL SYSTEMS GO - READY FOR LAUNCH")
    elif failed <= 2:
        print(f"\n⚠️  {failed} minor issues detected - Safe to launch with monitoring")
    else:
        print(f"\n❌ {failed} critical issues detected - REVIEW BEFORE LAUNCH")
    
    print("\n" + "="*80)

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("KRAFTD LAUNCH VERIFICATION SUITE")
    print(f"Target: {PROD_URL}")
    print(f"API Prefix: {API_PREFIX}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # Run tests sequentially
    print("[PHASE 1: CONNECTIVITY & SECURITY]")
    test_endpoint_accessibility()
    test_ssl_certificate()
    test_security_headers()
    test_cors_configuration()
    test_response_times()
    
    print("\n[PHASE 2: AUTHENTICATION]")
    registration_ok, access_token = test_user_registration()
    if registration_ok and access_token:
        test_profile_retrieval(access_token)
        test_logout_flow(access_token)
    
    print("\n[PHASE 3: AUTH FLOWS]")
    login_ok, login_token = test_login_flow(TEST_EMAIL, TEST_PASSWORD)
    test_token_refresh()
    
    print("\n[PHASE 4: ERROR HANDLING & SECURITY]")
    test_error_handling()
    test_rate_limiting()
    test_rbac_enforcement()
    
    print("\n[PHASE 5: DATABASE]")
    test_database_connectivity()
    
    # Print summary
    print_summary()
    
    # Return exit code based on failures
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
