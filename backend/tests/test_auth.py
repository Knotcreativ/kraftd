#!/usr/bin/env python3
"""Quick test of auth endpoints"""
import sys
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_auth_flow():
    print("=" * 60)
    print("Testing Auth System - Week 1 MVP")
    print("=" * 60)
    
    # Test data
    test_user = {
        "email": "test@kraftdintel.com",
        "name": "Test User",
        "organization": "Kraftd Inc",
        "password": "SecurePassword123!"
    }
    
    print(f"\n[1] Testing Registration...")
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=test_user, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            print(f"[OK] Registration successful!")
            print(f"   Access Token: {access_token[:50]}...")
            print(f"   Refresh Token: {refresh_token[:50]}...")
        else:
            print(f"[FAIL] Registration failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Registration error: {e}")
        return False
    
    print(f"\n[2] Testing Login...")
    try:
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            print(f"[OK] Login successful!")
            print(f"   Access Token: {access_token[:50]}...")
            print(f"   Refresh Token: {refresh_token[:50]}...")
        else:
            print(f"[FAIL] Login failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Login error: {e}")
        return False
    
    print(f"\n[3] Testing Get Profile (Protected Endpoint)...")
    try:
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(f"{BASE_URL}/auth/profile", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Profile retrieved!")
            print(f"   Name: {data.get('name')}")
            print(f"   Email: {data.get('email')}")
            print(f"   Organization: {data.get('organization')}")
            print(f"   Active: {data.get('is_active')}")
        else:
            print(f"[FAIL] Profile retrieval failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Profile error: {e}")
        return False
    
    print(f"\n[4] Testing Token Validation...")
    try:
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(f"{BASE_URL}/auth/validate", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Token validation successful!")
            print(f"   Email: {data.get('email')}")
            print(f"   Valid: {data.get('valid')}")
        else:
            print(f"[FAIL] Token validation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Token validation error: {e}")
        return False
    
    print(f"\n[5] Testing Token Refresh...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": refresh_token},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            new_access_token = data.get("access_token")
            print(f"[OK] Token refresh successful!")
            print(f"   New Access Token: {new_access_token[:50]}...")
        else:
            print(f"[FAIL] Token refresh failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Token refresh error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("[OK] ALL AUTH TESTS PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        # First check if server is running
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"[OK] Server is running (health check: {response.status_code})")
        print()
        
        # Run auth tests
        success = test_auth_flow()
        sys.exit(0 if success else 1)
        
    except requests.exceptions.ConnectionError:
        print("[FAIL] Cannot connect to server. Is it running?")
        print(f"   Try: cd backend && .venv\\Scripts\\python.exe -m uvicorn main:app --port 8000 --reload")
        sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Test error: {e}")
        sys.exit(1)
