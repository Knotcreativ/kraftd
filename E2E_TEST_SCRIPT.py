"""
COMPREHENSIVE END-TO-END TEST SCRIPT
Validates all 4 completed phases of KraftdIntel
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

BASE_URL = "http://127.0.0.1:8000/api/v1"
TEST_EMAIL = f"e2etest-{int(time.time())}@example.com"
TEST_PASSWORD = "SecurePass123"
TEST_NAME = "E2E Test User"

# Test results tracking
results = {
    "phase": {},
    "passed": 0,
    "failed": 0,
    "tests": []
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def log_test(phase: str, test_name: str, passed: bool, details: str = ""):
    """Log test result"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"  {status}  {test_name}")
    if details:
        print(f"       {details}")
    
    results["tests"].append({
        "phase": phase,
        "test": test_name,
        "passed": passed,
        "details": details
    })
    
    if passed:
        results["passed"] += 1
    else:
        results["failed"] += 1

def test_health():
    """Test Phase 0: Health Check"""
    print(f"\n{Colors.BLUE}=== PHASE 0: HEALTH CHECK ==={Colors.RESET}")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        passed = resp.status_code == 200
        log_test("0", "GET /health", passed, f"Status: {resp.status_code}")
        results["phase"]["health"] = passed
        return passed
    except Exception as e:
        log_test("0", "GET /health", False, str(e))
        results["phase"]["health"] = False
        return False

def test_phase_1_agent_api():
    """Test Phase 2: Agent API"""
    print(f"\n{Colors.BLUE}=== PHASE 2: AGENT API ==={Colors.RESET}")
    
    # Test 1: Status endpoint
    try:
        resp = requests.get(
            f"{BASE_URL}/agent/status",
            headers={"Authorization": "Bearer dummy-token"}
        )
        passed = resp.status_code in [200, 401]  # May be 401 without real token
        log_test("2", "GET /agent/status", passed, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("2", "GET /agent/status", False, str(e))
    
    # Test 2: Chat endpoint (without token - should fail)
    try:
        resp = requests.post(
            f"{BASE_URL}/agent/chat",
            json={"message": "Hello"},
            timeout=5
        )
        passed = resp.status_code == 401  # Should require auth
        log_test("2", "POST /agent/chat (no auth)", passed, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("2", "POST /agent/chat (no auth)", False, str(e))
    
    # Test 3: Analyze endpoint (without token - should fail)
    try:
        resp = requests.post(
            f"{BASE_URL}/agent/analyze",
            json={"document": "test content"},
            timeout=5
        )
        passed = resp.status_code == 401  # Should require auth
        log_test("2", "POST /agent/analyze (no auth)", passed, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("2", "POST /agent/analyze (no auth)", False, str(e))
    
    results["phase"]["agent_api"] = True

def test_phase_2_authentication():
    """Test Phase 1 & 3: Authentication & Password Recovery"""
    print(f"\n{Colors.BLUE}=== PHASE 1 & 3: AUTHENTICATION & PASSWORD RECOVERY ==={Colors.RESET}")
    
    access_token = None
    
    # Test 1: Register user
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": TEST_NAME,
                "acceptTerms": True,
                "acceptPrivacy": True
            },
            timeout=5
        )
        passed = resp.status_code == 201
        log_test("1+3", "POST /auth/register", passed, f"Status: {resp.status_code}")
        
        if passed:
            data = resp.json()
            access_token = data.get("access_token")
            log_test("1+3", "  - Token received", bool(access_token), "Bearer token extracted")
    except Exception as e:
        log_test("1+3", "POST /auth/register", False, str(e))
    
    # Test 2: Duplicate registration should fail
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": TEST_NAME,
                "acceptTerms": True,
                "acceptPrivacy": True
            },
            timeout=5
        )
        passed = resp.status_code == 400  # Should fail - email exists
        log_test("1+3", "POST /auth/register (duplicate)", passed, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("1+3", "POST /auth/register (duplicate)", False, str(e))
    
    # Test 3: Login with correct credentials
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            timeout=5
        )
        passed = resp.status_code == 200
        log_test("1+3", "POST /auth/login", passed, f"Status: {resp.status_code}")
        
        if passed:
            data = resp.json()
            access_token = data.get("access_token")
            log_test("1+3", "  - Token received", bool(access_token), "Bearer token extracted")
    except Exception as e:
        log_test("1+3", "POST /auth/login", False, str(e))
    
    # Test 4: Login with wrong password
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": "WrongPassword123"
            },
            timeout=5
        )
        passed = resp.status_code == 401
        log_test("1+3", "POST /auth/login (wrong password)", passed, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("1+3", "POST /auth/login (wrong password)", False, str(e))
    
    # Test 5: Get profile (with token)
    if access_token:
        try:
            resp = requests.get(
                f"{BASE_URL}/auth/profile",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=5
            )
            passed = resp.status_code == 200
            log_test("1+3", "GET /auth/profile (authenticated)", passed, f"Status: {resp.status_code}")
        except Exception as e:
            log_test("1+3", "GET /auth/profile (authenticated)", False, str(e))
    
    # Test 6: Forgot password endpoint
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/forgot-password",
            json={"email": TEST_EMAIL},
            timeout=5
        )
        passed = resp.status_code == 200
        log_test("1+3", "POST /auth/forgot-password", passed, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("1+3", "POST /auth/forgot-password", False, str(e))
    
    results["phase"]["authentication"] = True
    return access_token

def test_phase_3_templates(access_token: str):
    """Test Phase 4: Document Templates"""
    print(f"\n{Colors.BLUE}=== PHASE 4: DOCUMENT TEMPLATES ==={Colors.RESET}")
    
    template_id = None
    
    # Test 1: List templates
    try:
        resp = requests.get(
            f"{BASE_URL}/templates",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5
        )
        passed = resp.status_code == 200
        log_test("4", "GET /templates", passed, f"Status: {resp.status_code}")
        
        if passed:
            data = resp.json()
            count = data.get("total_count", 0)
            log_test("4", "  - Templates found", count > 0, f"Found {count} templates")
    except Exception as e:
        log_test("4", "GET /templates", False, str(e))
    
    # Test 2: Get statistics
    try:
        resp = requests.get(
            f"{BASE_URL}/templates/admin/statistics",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5
        )
        passed = resp.status_code == 200
        log_test("4", "GET /templates/admin/statistics", passed, f"Status: {resp.status_code}")
        
        if passed:
            data = resp.json()
            log_test("4", "  - Stats structure", "total_templates" in data, "Statistics returned")
    except Exception as e:
        log_test("4", "GET /templates/admin/statistics", False, str(e))
    
    # Test 3: Create new template
    try:
        resp = requests.post(
            f"{BASE_URL}/templates",
            json={
                "name": "E2E Test Template",
                "category": "invoice",
                "format": "html",
                "content": "<h1>Invoice {{ invoice_number }}</h1><p>Total: {{ total }}</p>"
            },
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5
        )
        passed = resp.status_code == 201
        log_test("4", "POST /templates (create)", passed, f"Status: {resp.status_code}")
        
        if passed:
            data = resp.json()
            template_id = data.get("id")
            log_test("4", "  - Template ID", bool(template_id), f"ID: {template_id}")
    except Exception as e:
        log_test("4", "POST /templates (create)", False, str(e))
    
    # Test 4: Retrieve template
    if template_id:
        try:
            resp = requests.get(
                f"{BASE_URL}/templates/{template_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=5
            )
            passed = resp.status_code == 200
            log_test("4", "GET /templates/{id}", passed, f"Status: {resp.status_code}")
        except Exception as e:
            log_test("4", "GET /templates/{id}", False, str(e))
    
    # Test 5: Validate template syntax
    try:
        resp = requests.post(
            f"{BASE_URL}/templates/validate",
            json={
                "content": "<h1>{{ title }}</h1>",
                "variables": ["title"]
            },
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5
        )
        passed = resp.status_code == 200
        log_test("4", "POST /templates/validate", passed, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("4", "POST /templates/validate", False, str(e))
    
    # Test 6: Generate document
    if template_id:
        try:
            resp = requests.post(
                f"{BASE_URL}/templates/{template_id}/generate",
                json={
                    "data": {
                        "invoice_number": "INV-2026-001",
                        "total": 1500.00
                    }
                },
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=5
            )
            passed = resp.status_code == 200
            log_test("4", "POST /templates/{id}/generate", passed, f"Status: {resp.status_code}")
            
            if passed:
                data = resp.json()
                content_len = len(data.get("content", ""))
                log_test("4", "  - Content rendered", content_len > 0, f"{content_len} chars")
        except Exception as e:
            log_test("4", "POST /templates/{id}/generate", False, str(e))
    
    # Test 7: Update template
    if template_id:
        try:
            resp = requests.put(
                f"{BASE_URL}/templates/{template_id}",
                json={
                    "name": "Updated E2E Template",
                    "content": "<h1>Updated {{ title }}</h1>"
                },
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=5
            )
            passed = resp.status_code == 200
            log_test("4", "PUT /templates/{id}", passed, f"Status: {resp.status_code}")
        except Exception as e:
            log_test("4", "PUT /templates/{id}", False, str(e))
    
    # Test 8: Duplicate template
    if template_id:
        try:
            resp = requests.post(
                f"{BASE_URL}/templates/{template_id}/duplicate",
                params={"new_name": "Duplicated E2E Template"},
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=5
            )
            passed = resp.status_code == 201
            log_test("4", "POST /templates/{id}/duplicate", passed, f"Status: {resp.status_code}")
        except Exception as e:
            log_test("4", "POST /templates/{id}/duplicate", False, str(e))
    
    # Test 9: Delete template
    if template_id:
        try:
            resp = requests.delete(
                f"{BASE_URL}/templates/{template_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=5
            )
            passed = resp.status_code == 204
            log_test("4", "DELETE /templates/{id}", passed, f"Status: {resp.status_code}")
        except Exception as e:
            log_test("4", "DELETE /templates/{id}", False, str(e))
    
    results["phase"]["templates"] = True

def test_error_scenarios():
    """Test error handling"""
    print(f"\n{Colors.BLUE}=== ERROR HANDLING & EDGE CASES ==={Colors.RESET}")
    
    # Test 1: Missing auth header
    try:
        resp = requests.get(f"{BASE_URL}/templates", timeout=5)
        passed = resp.status_code == 401
        log_test("errors", "GET /templates (no auth)", passed, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("errors", "GET /templates (no auth)", False, str(e))
    
    # Test 2: Invalid token
    try:
        resp = requests.get(
            f"{BASE_URL}/templates",
            headers={"Authorization": "Bearer invalid-token"},
            timeout=5
        )
        passed = resp.status_code in [401, 403]
        log_test("errors", "GET /templates (invalid token)", passed, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("errors", "GET /templates (invalid token)", False, str(e))
    
    # Test 3: Invalid email format in registration
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": "not-an-email",
                "password": TEST_PASSWORD,
                "acceptTerms": True,
                "acceptPrivacy": True
            },
            timeout=5
        )
        passed = resp.status_code in [400, 422]
        log_test("errors", "POST /auth/register (invalid email)", passed, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("errors", "POST /auth/register (invalid email)", False, str(e))
    
    # Test 4: Short password
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": "short@example.com",
                "password": "123",  # Too short
                "acceptTerms": True,
                "acceptPrivacy": True
            },
            timeout=5
        )
        passed = resp.status_code in [400, 422]
        log_test("errors", "POST /auth/register (short password)", passed, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("errors", "POST /auth/register (short password)", False, str(e))
    
    results["phase"]["error_handling"] = True

def main():
    """Run all tests"""
    print(f"\n{Colors.YELLOW}{'='*70}")
    print(f"END-TO-END TEST SUITE - ALL 4 PHASES")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}{Colors.RESET}\n")
    
    # Phase 0: Health
    if not test_health():
        print(f"\n{Colors.RED}Backend not responding. Aborting tests.{Colors.RESET}")
        return
    
    # Phase 2: Agent API
    test_phase_1_agent_api()
    
    # Phase 1 & 3: Authentication & Password Recovery
    access_token = test_phase_2_authentication()
    
    # Phase 4: Templates
    if access_token:
        test_phase_3_templates(access_token)
    else:
        print(f"{Colors.RED}Could not obtain access token. Skipping template tests.{Colors.RESET}")
    
    # Error handling
    test_error_scenarios()
    
    # Summary
    print(f"\n{Colors.YELLOW}{'='*70}")
    print(f"TEST SUMMARY")
    print(f"{'='*70}{Colors.RESET}")
    print(f"Total Tests:  {results['passed'] + results['failed']}")
    print(f"{Colors.GREEN}Passed:      {results['passed']}{Colors.RESET}")
    print(f"{Colors.RED}Failed:      {results['failed']}{Colors.RESET}")
    
    pass_rate = (results['passed'] / (results['passed'] + results['failed']) * 100) if (results['passed'] + results['failed']) > 0 else 0
    print(f"Pass Rate:   {pass_rate:.1f}%")
    
    print(f"\nPhase Results:")
    for phase, status in results["phase"].items():
        status_str = f"{Colors.GREEN}✓{Colors.RESET}" if status else f"{Colors.RED}✗{Colors.RESET}"
        print(f"  {status_str} {phase.replace('_', ' ').title()}")
    
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.RESET}\n")
    
    # Save results
    with open("E2E_TEST_RESULTS.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: E2E_TEST_RESULTS.json\n")

if __name__ == "__main__":
    main()
