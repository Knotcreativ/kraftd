#!/usr/bin/env python3
"""
Quick API Integration Test - Tests registration endpoint
Starts backend server and runs tests quickly before server shuts down
"""
import subprocess
import time
import sys
import json
import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
REGISTRATION_ENDPOINT = f"{BASE_URL}/api/v1/auth/register"

def test_registration_quick():
    """Quick test of registration endpoint"""
    print("\n" + "=" * 70)
    print("Quick API Integration Test - Registration Endpoint")
    print("=" * 70)
    print(f"Start: {datetime.now()}")
    
    # Give server a moment to fully start
    time.sleep(2)
    
    # Test 1: Valid registration
    print("\nTest 1: Valid Registration...", flush=True)
    try:
        response = requests.post(
            REGISTRATION_ENDPOINT,
            json={
                "email": "test1@example.com",
                "password": "TestPass123",
                "acceptTerms": True,
                "acceptPrivacy": True
            },
            timeout=3
        )
        if response.status_code in [200, 201]:
            data = response.json()
            if "access_token" in data:
                print("  ✓ PASS - User registered successfully")
            else:
                print(f"  ⚠ PARTIAL - Response: {data}")
        else:
            print(f"  ✗ FAIL - Status {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"  ✗ FAIL - {str(e)}")
    
    # Test 2: Invalid email
    print("\nTest 2: Invalid Email...", flush=True)
    try:
        response = requests.post(
            REGISTRATION_ENDPOINT,
            json={
                "email": "invalid",
                "password": "TestPass123",
                "acceptTerms": True,
                "acceptPrivacy": True
            },
            timeout=3
        )
        if response.status_code >= 400:
            print("  ✓ PASS - Invalid email rejected")
        else:
            print(f"  ✗ FAIL - Should have rejected (got {response.status_code})")
    except Exception as e:
        print(f"  ✗ FAIL - {str(e)}")
    
    # Test 3: Weak password
    print("\nTest 3: Weak Password...", flush=True)
    try:
        response = requests.post(
            REGISTRATION_ENDPOINT,
            json={
                "email": "test3@example.com",
                "password": "weak",
                "acceptTerms": True,
                "acceptPrivacy": True
            },
            timeout=3
        )
        if response.status_code >= 400:
            print("  ✓ PASS - Weak password rejected")
        else:
            print(f"  ✗ FAIL - Should have rejected (got {response.status_code})")
    except Exception as e:
        print(f"  ✗ FAIL - {str(e)}")
    
    # Test 4: Missing terms
    print("\nTest 4: Missing Terms...", flush=True)
    try:
        response = requests.post(
            REGISTRATION_ENDPOINT,
            json={
                "email": "test4@example.com",
                "password": "TestPass123",
                "acceptTerms": False,
                "acceptPrivacy": True
            },
            timeout=3
        )
        if response.status_code >= 400:
            print("  ✓ PASS - Missing terms rejected")
        else:
            print(f"  ✗ FAIL - Should have rejected (got {response.status_code})")
    except Exception as e:
        print(f"  ✗ FAIL - {str(e)}")
    
    print("\n" + "=" * 70)
    print(f"End: {datetime.now()}")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_registration_quick()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        sys.exit(1)
