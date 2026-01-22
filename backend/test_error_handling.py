#!/usr/bin/env python3
"""
Test script for standardized error handling in KraftdIntel API.

This script tests that all endpoints return consistent error responses.
"""

import json
from fastapi.testclient import TestClient
from main import app

def test_standardized_errors():
    """Test that endpoints return standardized error responses."""
    client = TestClient(app)

    print("Testing Standardized Error Handling")
    print("=" * 50)

    # Test 1: Register endpoint without auth (should work - register doesn't require auth)
    print("\n1. Testing register endpoint (should succeed)...")
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123",
        "firstName": "Test",
        "lastName": "User",
        "acceptTerms": True,
        "acceptPrivacy": True,
        "recaptchaToken": "test-token"
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        print("✓ Register succeeded (expected)")
    else:
        print(f"✗ Register failed: {response.text}")

    # Test 2: Register with duplicate email
    print("\n2. Testing duplicate email registration...")
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123",
        "firstName": "Test",
        "lastName": "User2",
        "acceptTerms": True,
        "acceptPrivacy": True,
        "recaptchaToken": "test-token"
    })
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        if response.status_code == 409 and "error" in data and data.get("success") == False:
            print("✓ Standardized error response format")
        else:
            print("✗ Non-standardized error response")
    except:
        print(f"✗ Invalid JSON response: {response.text}")

    # Test 3: Get profile without auth (should fail with 401)
    print("\n3. Testing protected endpoint without auth...")
    response = client.get("/api/v1/auth/profile")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        if response.status_code == 401 and "error" in data and data.get("success") == False:
            print("✓ Standardized authentication error")
        else:
            print("✗ Non-standardized authentication error")
    except:
        print(f"✗ Invalid JSON response: {response.text}")

    # Test 4: Create conversion without auth (should fail with 401)
    print("\n4. Testing conversion creation without auth...")
    response = client.post("/api/v1/conversions")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        if response.status_code == 401 and "error" in data and data.get("success") == False:
            print("✓ Standardized authentication error")
        else:
            print("✗ Non-standardized authentication error")
    except:
        print(f"✗ Invalid JSON response: {response.text}")

    # Test 5: Health check (should succeed)
    print("\n5. Testing health endpoint...")
    response = client.get("/api/v1/health")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✓ Health check succeeded")
    else:
        print(f"✗ Health check failed: {response.text}")

    print("\n" + "=" * 50)
    print("Error handling standardization test completed!")

if __name__ == "__main__":
    test_standardized_errors()