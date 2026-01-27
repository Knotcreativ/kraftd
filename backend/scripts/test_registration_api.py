#!/usr/bin/env python3
"""
Quick test of registration endpoint
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_registration_valid():
    """Test valid registration"""
    data = {
        "email": "testuser@example.com",
        "password": "SecurePass123",
        "acceptTerms": True,
        "acceptPrivacy": True,
        "name": "Test User",
        "marketingOptIn": False
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=data,
            timeout=5
        )
        print(f"✅ Registration (valid): {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 201
    except Exception as e:
        print(f"❌ Registration (valid) failed: {e}")
        return False

def test_registration_invalid_email():
    """Test registration with invalid email"""
    data = {
        "email": "not-an-email",
        "password": "SecurePass123",
        "acceptTerms": True,
        "acceptPrivacy": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=data,
            timeout=5
        )
        print(f"✅ Registration (invalid email): {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 400
    except Exception as e:
        print(f"❌ Registration (invalid email) failed: {e}")
        return False

def test_registration_weak_password():
    """Test registration with weak password"""
    data = {
        "email": "test@example.com",
        "password": "short",
        "acceptTerms": True,
        "acceptPrivacy": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=data,
            timeout=5
        )
        print(f"✅ Registration (weak password): {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 400
    except Exception as e:
        print(f"❌ Registration (weak password) failed: {e}")
        return False

def test_registration_duplicate():
    """Test registration with duplicate email"""
    data = {
        "email": "duplicate@example.com",
        "password": "SecurePass123",
        "acceptTerms": True,
        "acceptPrivacy": True
    }
    
    try:
        # First registration
        response1 = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=data,
            timeout=5
        )
        print(f"✅ Registration 1 (duplicate - first): {response1.status_code}")
        
        # Second registration (should fail)
        response2 = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=data,
            timeout=5
        )
        print(f"✅ Registration 2 (duplicate - second): {response2.status_code}")
        print(f"   Response: {response2.json()}")
        return response2.status_code == 409
    except Exception as e:
        print(f"❌ Registration (duplicate) failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 2 Registration Endpoint Tests")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health),
        ("Valid Registration", test_registration_valid),
        ("Invalid Email", test_registration_invalid_email),
        ("Weak Password", test_registration_weak_password),
        ("Duplicate Email", test_registration_duplicate),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\nTest: {name}")
        print("-" * 60)
        result = test_func()
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, r in results if r)
    print(f"\nTotal: {passed}/{len(results)} tests passed")
