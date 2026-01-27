#!/usr/bin/env python3
"""
Simple Authentication Test Script
Tests authentication locally
"""

import requests
import json
import time

# Configuration
LOCAL_URL = "http://localhost:8002"
API_PREFIX = "/api/v1"
TEST_EMAIL = f"test.local.{int(time.time())}@kraftd.io"
TEST_PASSWORD = "Test@Kraftd2024Secure!"

def test_auth():
    """Test authentication flow"""
    print("Testing authentication locally...")

    # Register
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "firstName": "Test",
        "lastName": "User",
        "acceptTerms": True,
        "acceptPrivacy": True,
        "recaptchaToken": "test-token"
    }

    try:
        response = requests.post(f"{LOCAL_URL}{API_PREFIX}/auth/register", json=register_data)
        print(f"Register: {response.status_code}")
        if response.status_code != 201:
            print(f"Register failed: {response.text}")
            return

        # Login
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "recaptchaToken": "test-token"
        }

        response = requests.post(f"{LOCAL_URL}{API_PREFIX}/auth/login", json=login_data)
        print(f"Login: {response.status_code}")
        if response.status_code != 200:
            print(f"Login failed: {response.text}")
            return

        token = response.json().get("access_token")
        if not token:
            print("No token received")
            return

        headers = {"Authorization": f"Bearer {token}"}

        # Test profile
        response = requests.get(f"{LOCAL_URL}{API_PREFIX}/auth/profile", headers=headers)
        print(f"Profile: {response.status_code}")
        print(f"Profile headers sent: {headers}")
        print(f"Profile response: {response.text}")
        if response.status_code != 200:
            print(f"Profile failed: {response.text}")

        # Test logout
        response = requests.post(f"{LOCAL_URL}{API_PREFIX}/auth/logout", headers=headers)
        print(f"Logout: {response.status_code}")
        if response.status_code != 200:
            print(f"Logout failed: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_auth()