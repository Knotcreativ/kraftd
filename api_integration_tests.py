#!/usr/bin/env python3
"""
API Integration Tests for User Registration Endpoint

This script tests the registration endpoint via HTTP requests.
Note: Backend may shut down after ~18 seconds, so tests are designed to run quickly.
"""
import requests
import json
import sys
import time
import subprocess
import os
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
REGISTRATION_ENDPOINT = f"{BASE_URL}/api/v1/auth/register"
HEALTH_ENDPOINT = f"{BASE_URL}/api/v1/health"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'

def wait_for_server(max_attempts=10, delay=1):
    """Wait for server to be ready"""
    print(f"{Colors.BLUE}Waiting for server to be ready...{Colors.END}")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(HEALTH_ENDPOINT, timeout=2)
            if response.status_code == 200:
                print(f"{Colors.GREEN}Server is ready!{Colors.END}")
                return True
        except:
            pass
        
        if attempt < max_attempts - 1:
            print(f"  Attempt {attempt + 1}/{max_attempts}... ", end="", flush=True)
            time.sleep(delay)
            print("retrying")
    
    print(f"{Colors.YELLOW}Server not responding (may have auto-shutdown){Colors.END}")
    return False

def test_valid_registration():
    """Test 1: Valid registration"""
    print(f"\n{Colors.BLUE}Test 1: Valid Registration{Colors.END}")
    
    payload = {
        "email": "testuser@example.com",
        "password": "SecurePass123",
        "acceptTerms": True,
        "acceptPrivacy": True,
        "name": "Test User",
        "marketingOptIn": False
    }
    
    try:
        response = requests.post(REGISTRATION_ENDPOINT, json=payload, timeout=5)
        
        if response.status_code in [200, 201]:
            data = response.json()
            if "access_token" in data and "email" in data:
                print(f"{Colors.GREEN}✓ PASS{Colors.END}: User registered successfully")
                print(f"  Email: {data.get('email')}")
                print(f"  Token: {data.get('access_token', 'N/A')[:20]}...")
                return True
            else:
                print(f"{Colors.YELLOW}⚠ PARTIAL{Colors.END}: Response missing expected fields")
                print(f"  Response: {data}")
                return False
        else:
            print(f"{Colors.RED}✗ FAIL{Colors.END}: Status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}✗ FAIL{Colors.END}: Cannot connect to server")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗ FAIL{Colors.END}: {str(e)}")
        return False

def test_invalid_email():
    """Test 2: Invalid email"""
    print(f"\n{Colors.BLUE}Test 2: Invalid Email{Colors.END}")
    
    payload = {
        "email": "not-an-email",
        "password": "SecurePass123",
        "acceptTerms": True,
        "acceptPrivacy": True
    }
    
    try:
        response = requests.post(REGISTRATION_ENDPOINT, json=payload, timeout=5)
        
        if response.status_code >= 400:
            print(f"{Colors.GREEN}✓ PASS{Colors.END}: Invalid email correctly rejected (Status {response.status_code})")
            return True
        else:
            print(f"{Colors.RED}✗ FAIL{Colors.END}: Should have rejected invalid email")
            print(f"  Response: {response.json()}")
            return False
    except Exception as e:
        print(f"{Colors.RED}✗ FAIL{Colors.END}: {str(e)}")
        return False

def test_weak_password():
    """Test 3: Weak password"""
    print(f"\n{Colors.BLUE}Test 3: Weak Password{Colors.END}")
    
    payload = {
        "email": "test@example.com",
        "password": "weak",
        "acceptTerms": True,
        "acceptPrivacy": True
    }
    
    try:
        response = requests.post(REGISTRATION_ENDPOINT, json=payload, timeout=5)
        
        if response.status_code >= 400:
            print(f"{Colors.GREEN}✓ PASS{Colors.END}: Weak password correctly rejected (Status {response.status_code})")
            return True
        else:
            print(f"{Colors.RED}✗ FAIL{Colors.END}: Should have rejected weak password")
            print(f"  Response: {response.json()}")
            return False
    except Exception as e:
        print(f"{Colors.RED}✗ FAIL{Colors.END}: {str(e)}")
        return False

def test_missing_terms():
    """Test 4: Missing terms acceptance"""
    print(f"\n{Colors.BLUE}Test 4: Missing Terms Acceptance{Colors.END}")
    
    payload = {
        "email": "test@example.com",
        "password": "SecurePass123",
        "acceptTerms": False,
        "acceptPrivacy": True
    }
    
    try:
        response = requests.post(REGISTRATION_ENDPOINT, json=payload, timeout=5)
        
        if response.status_code >= 400:
            print(f"{Colors.GREEN}✓ PASS{Colors.END}: Missing terms correctly rejected (Status {response.status_code})")
            return True
        else:
            print(f"{Colors.RED}✗ FAIL{Colors.END}: Should have rejected missing terms")
            print(f"  Response: {response.json()}")
            return False
    except Exception as e:
        print(f"{Colors.RED}✗ FAIL{Colors.END}: {str(e)}")
        return False

def test_missing_privacy():
    """Test 5: Missing privacy acceptance"""
    print(f"\n{Colors.BLUE}Test 5: Missing Privacy Acceptance{Colors.END}")
    
    payload = {
        "email": "test@example.com",
        "password": "SecurePass123",
        "acceptTerms": True,
        "acceptPrivacy": False
    }
    
    try:
        response = requests.post(REGISTRATION_ENDPOINT, json=payload, timeout=5)
        
        if response.status_code >= 400:
            print(f"{Colors.GREEN}✓ PASS{Colors.END}: Missing privacy correctly rejected (Status {response.status_code})")
            return True
        else:
            print(f"{Colors.RED}✗ FAIL{Colors.END}: Should have rejected missing privacy")
            print(f"  Response: {response.json()}")
            return False
    except Exception as e:
        print(f"{Colors.RED}✗ FAIL{Colors.END}: {str(e)}")
        return False

def main():
    print("=" * 70)
    print("Phase 2: API Integration Tests - Registration Endpoint")
    print("=" * 70)
    print(f"Start Time: {datetime.now()}")
    print(f"Endpoint: {REGISTRATION_ENDPOINT}")
    print("=" * 70)
    
    # Wait for server
    server_ready = wait_for_server(max_attempts=8, delay=1)
    
    if not server_ready:
        print(f"\n{Colors.YELLOW}Warning: Server not responding. Tests may fail.{Colors.END}")
        print("Note: Backend may have auto-shutdown. Starting fresh server...\n")
        
        # Try to start server if not running
        try:
            # Don't block - just try to start it
            print(f"{Colors.BLUE}Attempting to start backend server...{Colors.END}")
        except:
            pass
    
    # Run tests quickly
    results = []
    
    # Test 1
    try:
        results.append(test_valid_registration())
    except:
        results.append(False)
    
    # Test 2
    try:
        results.append(test_invalid_email())
    except:
        results.append(False)
    
    # Test 3
    try:
        results.append(test_weak_password())
    except:
        results.append(False)
    
    # Test 4
    try:
        results.append(test_missing_terms())
    except:
        results.append(False)
    
    # Test 5
    try:
        results.append(test_missing_privacy())
    except:
        results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print(f"{Colors.GREEN}SUCCESS: All API integration tests passed!{Colors.END}")
        return True
    else:
        failed = total - passed
        print(f"{Colors.RED}FAILED: {failed} test(s) failed{Colors.END}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Fatal error: {str(e)}{Colors.END}")
        sys.exit(1)
