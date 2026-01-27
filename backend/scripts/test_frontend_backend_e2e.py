#!/usr/bin/env python3
"""
Frontend-Backend E2E Test Script
Tests CORS and API communication between frontend and backend
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
FRONTEND_ORIGIN = "https://green-mushroom-06da9040f.1.azurestaticapps.net"
BACKEND_BASE_URL = "https://kraftd-api.calmrock-7db6369d.uaenorth.azurecontainerapps.io/api/v1"

# Headers to simulate frontend requests
HEADERS = {
    "Origin": FRONTEND_ORIGIN,
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def test_cors_preflight(endpoint: str, method: str = "POST") -> bool:
    """Test CORS preflight request"""
    try:
        response = requests.options(
            f"{BACKEND_BASE_URL}{endpoint}",
            headers={
                **HEADERS,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "content-type"
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Preflight test failed: {e}")
        return False

def test_api_endpoint(endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test API endpoint with CORS headers"""
    try:
        if method == "GET":
            response = requests.get(
                f"{BACKEND_BASE_URL}{endpoint}",
                headers=HEADERS,
                timeout=10
            )
        elif method == "POST":
            response = requests.post(
                f"{BACKEND_BASE_URL}{endpoint}",
                headers=HEADERS,
                json=data,
                timeout=10
            )
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}

        return {
            "success": response.status_code in [200, 201, 422],  # 422 is validation error, still means CORS works
            "status_code": response.status_code,
            "cors_allowed": "access-control-allow-origin" in response.headers,
            "cors_credentials": response.headers.get("access-control-allow-credentials") == "true",
            "response": response.text[:200] + "..." if len(response.text) > 200 else response.text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    print("🚀 Frontend-Backend E2E Test")
    print(f"Frontend Origin: {FRONTEND_ORIGIN}")
    print(f"Backend URL: {BACKEND_BASE_URL}")
    print("=" * 60)

    tests = [
        {
            "name": "Health Check (GET)",
            "endpoint": "/health",
            "method": "GET"
        },
        {
            "name": "Agent Status (GET)",
            "endpoint": "/agent/status",
            "method": "GET"
        },
        {
            "name": "User Registration (POST)",
            "endpoint": "/auth/register",
            "method": "POST",
            "data": {
                "email": f"test{int(time.time())}@example.com",
                "password": "TestPass123!",
                "firstName": "Test",
                "lastName": "User",
                "acceptTerms": True,
                "acceptPrivacy": True,
                "recaptchaToken": "test-token"
            }
        }
    ]

    results = []

    for test in tests:
        print(f"\n🔍 Testing: {test['name']}")
        print(f"   Endpoint: {test['endpoint']}")
        print(f"   Method: {test['method']}")

        # Test CORS preflight if POST
        if test['method'] == 'POST':
            preflight_ok = test_cors_preflight(test['endpoint'], test['method'])
            print(f"   Preflight CORS: {'✅' if preflight_ok else '❌'}")

        # Test actual API call
        result = test_api_endpoint(
            test['endpoint'],
            test['method'],
            test.get('data')
        )

        if result['success']:
            print("   API Call: ✅")
            print(f"   Status: {result['status_code']}")
            print(f"   CORS Allowed: {'✅' if result['cors_allowed'] else '❌'}")
            print(f"   CORS Credentials: {'✅' if result['cors_credentials'] else '❌'}")
        else:
            print("   API Call: ❌")
            print(f"   Error: {result.get('error', 'Unknown error')}")

        results.append({
            "test": test['name'],
            "success": result['success'],
            "cors_working": result.get('cors_allowed', False) and result.get('cors_credentials', False)
        })

    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")

    all_success = all(r['success'] for r in results)
    cors_working = all(r['cors_working'] for r in results)

    print(f"API Communication: {'✅ ALL TESTS PASSED' if all_success else '❌ SOME TESTS FAILED'}")
    print(f"CORS Configuration: {'✅ WORKING' if cors_working else '❌ NOT WORKING'}")

    if all_success and cors_working:
        print("\n🎉 Frontend-Backend E2E Test: SUCCESS!")
        print("The frontend can successfully communicate with the backend APIs.")
    else:
        print("\n❌ Frontend-Backend E2E Test: ISSUES FOUND")
        if not cors_working:
            print("   - CORS configuration needs to be fixed")
        if not all_success:
            print("   - Some API endpoints are not responding correctly")

if __name__ == "__main__":
    main()