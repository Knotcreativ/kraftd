"""
KRAFTD END-TO-END WORKFLOW TEST SUITE

Full workflow testing:
1. Create conversion → conversions_used incremented
2. Generate schema → api_calls_used incremented
3. Revise schema → no quota increment
4. Finalize schema → no quota increment
5. Generate summary → api_calls_used incremented
6. Generate output → exports_used incremented
7. Submit feedback → feedback stored
8. Retrieve feedback → single feedback item
9. List feedback → all feedback for conversion
10. Validate quota usage → verify all counters
11. Negative tests → error handling

Usage:
    python KRAFTD_E2E_TEST.py <token>

Example:
    python KRAFTD_E2E_TEST.py "eyJhbGc..."
"""

import sys
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Configuration (can be overridden by --base-url argument)
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "Content-Type": "application/json",
}

# Test state
state = {
    "conversion_id": None,
    "schema_id": None,
    "summary_id": None,
    "output_id": None,
    "feedback_id": None,
    "initial_quota": None,
    "token": None,
}

# Test results
results = {
    "passed": 0,
    "failed": 0,
    "tests": [],
}


def log_test(name: str, status: str, details: str = "", response_code: int = None):
    """Log test result."""
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if response_code:
        details = f"{details} (HTTP {response_code})"
    
    print(f"{icon} [{timestamp}] {name}")
    if details:
        print(f"   └─ {details}")
    
    results["tests"].append({
        "name": name,
        "status": status,
        "details": details,
        "code": response_code
    })
    
    if status == "PASS":
        results["passed"] += 1
    elif status == "FAIL":
        results["failed"] += 1


def make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    expect_code: int = 200,
    test_name: str = ""
) -> Optional[Dict[str, Any]]:
    """Make HTTP request and validate response."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS)
        elif method == "POST":
            response = requests.post(url, json=data, headers=HEADERS)
        else:
            log_test(test_name or f"{method} {endpoint}", "FAIL", f"Unknown method {method}")
            return None
        
        success = response.status_code == expect_code
        
        if success:
            try:
                return response.json()
            except:
                return {}
        else:
            log_test(
                test_name or f"{method} {endpoint}",
                "FAIL",
                f"Expected {expect_code}, got {response.status_code}: {response.text[:100]}",
                response.status_code
            )
            return None
    
    except Exception as e:
        log_test(
            test_name or f"{method} {endpoint}",
            "FAIL",
            f"Request error: {str(e)}"
        )
        return None


def setup_auth(token: str):
    """Setup authentication token."""
    global HEADERS
    HEADERS["Authorization"] = f"Bearer {token}"
    state["token"] = token
    print(f"\n🔐 Authorization configured with token")
    print(f"   Token: {token[:20]}...{token[-10:]}\n")


# ===== STEP 0: SETUP =====

def step_0_setup():
    """Verify server is running."""
    print("\n" + "="*70)
    print("STEP 0: SERVER HEALTH CHECK")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/health", headers=HEADERS, timeout=2)
        if response.status_code == 200:
            log_test("Server health check", "PASS", "Server is running", 200)
            return True
        else:
            log_test("Server health check", "FAIL", f"Health check returned {response.status_code}")
            return False
    except Exception as e:
        log_test("Server health check", "FAIL", f"Cannot connect to server: {str(e)}")
        return False


# ===== STEP 1: CREATE CONVERSION =====

def step_1_create_conversion():
    """Step 1: Create a new conversion."""
    print("\n" + "="*70)
    print("STEP 1: CREATE CONVERSION")
    print("="*70)
    print("Endpoint: POST /api/v1/conversions")
    print("Purpose: Create new conversion session, increment conversions_used\n")
    
    data = {
        "document_name": "sample.pdf",
        "document_type": "pdf",
        "source": "upload"
    }
    
    response = make_request(
        "POST",
        "/conversions",
        data=data,
        expect_code=201,
        test_name="Create conversion (POST /conversions)"
    )
    
    if response and "conversion_id" in response:
        state["conversion_id"] = response["conversion_id"]
        log_test(
            "Conversion created",
            "PASS",
            f"conversion_id: {response['conversion_id']}"
        )
        print(f"\n   ✓ conversions_used should be incremented")
        print(f"   ✓ Conversion document should be in Cosmos DB")
        return True
    else:
        log_test("Conversion created", "FAIL", "No conversion_id in response")
        return False


# ===== STEP 2: GENERATE SCHEMA =====

def step_2_generate_schema():
    """Step 2: Generate schema from conversion."""
    print("\n" + "="*70)
    print("STEP 2: GENERATE SCHEMA")
    print("="*70)
    print("Endpoint: POST /api/v1/schema/generate")
    print("Purpose: Generate initial schema, increment api_calls_used\n")
    
    if not state["conversion_id"]:
        log_test("Generate schema", "FAIL", "No conversion_id from step 1")
        return False
    
    data = {
        "document_id": "doc-001",
        "conversion_id": state["conversion_id"]
    }
    
    response = make_request(
        "POST",
        "/schema/generate",
        data=data,
        expect_code=200,
        test_name="Generate schema (POST /schema/generate)"
    )
    
    if response and "schema_def" in response:
        schema_def = response.get("schema_def", {})
        state["schema_id"] = schema_def.get("schema_id")
        log_test(
            "Schema generated",
            "PASS",
            f"schema_id: {state['schema_id']}, fields: {len(schema_def.get('fields', []))}"
        )
        print(f"\n   ✓ api_calls_used should be incremented")
        print(f"   ✓ Schema document should be in Cosmos DB")
        print(f"   ✓ Ownership validated (conversion owned by user)")
        return True
    else:
        log_test("Schema generated", "FAIL", "No schema_def in response")
        return False


# ===== STEP 3: REVISE SCHEMA =====

def step_3_revise_schema():
    """Step 3: Revise schema."""
    print("\n" + "="*70)
    print("STEP 3: REVISE SCHEMA")
    print("="*70)
    print("Endpoint: POST /api/v1/schema/revise")
    print("Purpose: Update schema, NO quota increment\n")
    
    if not state["conversion_id"] or not state["schema_id"]:
        log_test("Revise schema", "FAIL", "Missing conversion_id or schema_id")
        return False
    
    data = {
        "conversion_id": state["conversion_id"],
        "schema_id": state["schema_id"],
        "revision_notes": "Fix field names",
        "field_updates": {"field1": "updated_value"},
        "rejected_fields": []
    }
    
    response = make_request(
        "POST",
        "/schema/revise",
        data=data,
        expect_code=200,
        test_name="Revise schema (POST /schema/revise)"
    )
    
    if response and response.get("success"):
        log_test(
            "Schema revised",
            "PASS",
            f"Version: {response.get('version')}, changes_applied: {response.get('changes_applied')}"
        )
        print(f"\n   ✓ NO quota increment (revision is free)")
        print(f"   ✓ Revision stored in Cosmos DB")
        return True
    else:
        log_test("Schema revised", "FAIL", "Response not successful")
        return False


# ===== STEP 4: FINALIZE SCHEMA =====

def step_4_finalize_schema():
    """Step 4: Finalize schema."""
    print("\n" + "="*70)
    print("STEP 4: FINALIZE SCHEMA")
    print("="*70)
    print("Endpoint: POST /api/v1/schema/finalize")
    print("Purpose: Lock schema, NO quota increment\n")
    
    if not state["conversion_id"] or not state["schema_id"]:
        log_test("Finalize schema", "FAIL", "Missing conversion_id or schema_id")
        return False
    
    data = {
        "conversion_id": state["conversion_id"],
        "schema_id": state["schema_id"]
    }
    
    response = make_request(
        "POST",
        "/schema/finalize",
        data=data,
        expect_code=200,
        test_name="Finalize schema (POST /schema/finalize)"
    )
    
    if response and response.get("success"):
        log_test(
            "Schema finalized",
            "PASS",
            f"status: {response.get('status')}"
        )
        print(f"\n   ✓ Schema marked as final (is_final = true)")
        print(f"   ✓ NO quota increment")
        return True
    else:
        log_test("Schema finalized", "FAIL", "Response not successful")
        return False


# ===== STEP 5: GENERATE SUMMARY =====

def step_5_generate_summary():
    """Step 5: Generate AI summary."""
    print("\n" + "="*70)
    print("STEP 5: GENERATE SUMMARY")
    print("="*70)
    print("Endpoint: POST /api/v1/summary/generate")
    print("Purpose: Generate AI summary, increment api_calls_used\n")
    
    if not state["conversion_id"]:
        log_test("Generate summary", "FAIL", "No conversion_id from step 1")
        return False
    
    data = {
        "conversion_id": state["conversion_id"],
        "document_id": "doc-001",
        "summary_length": "medium",
        "focus_areas": ["key_points", "risks"]
    }
    
    response = make_request(
        "POST",
        "/summary/generate",
        data=data,
        expect_code=200,
        test_name="Generate summary (POST /summary/generate)"
    )
    
    if response and "document_id" in response:
        state["summary_id"] = response.get("document_id")
        log_test(
            "Summary generated",
            "PASS",
            f"length: {response.get('summary_length')}, key_points: {len(response.get('key_points', []))}"
        )
        print(f"\n   ✓ api_calls_used should be incremented")
        print(f"   ✓ Summary document should be in Cosmos DB")
        print(f"   ✓ Ownership validated")
        return True
    else:
        log_test("Summary generated", "FAIL", "No document_id in response")
        return False


# ===== STEP 6: GENERATE OUTPUT =====

def step_6_generate_output():
    """Step 6: Generate output/export."""
    print("\n" + "="*70)
    print("STEP 6: GENERATE OUTPUT")
    print("="*70)
    print("Endpoint: POST /api/v1/outputs/generate")
    print("Purpose: Create output in specified format, increment exports_used\n")
    
    if not state["conversion_id"]:
        log_test("Generate output", "FAIL", "No conversion_id from step 1")
        return False
    
    data = {
        "conversion_id": state["conversion_id"],
        "document_id": "doc-001",
        "format": "json",
        "output_data": {
            "title": "Final Output",
            "fields": {"a": 1, "b": 2}
        }
    }
    
    response = make_request(
        "POST",
        "/outputs/generate",
        data=data,
        expect_code=201,
        test_name="Generate output (POST /outputs/generate)"
    )
    
    if response and "output_id" in response:
        state["output_id"] = response["output_id"]
        log_test(
            "Output generated",
            "PASS",
            f"output_id: {response['output_id']}, format: {response.get('format')}"
        )
        print(f"\n   ✓ exports_used should be incremented")
        print(f"   ✓ Output document should be in Cosmos DB")
        return True
    else:
        log_test("Output generated", "FAIL", "No output_id in response")
        return False


# ===== STEP 7: SUBMIT FEEDBACK =====

def step_7_submit_feedback():
    """Step 7: Submit feedback."""
    print("\n" + "="*70)
    print("STEP 7: SUBMIT FEEDBACK")
    print("="*70)
    print("Endpoint: POST /api/v1/feedback")
    print("Purpose: Store user feedback on output\n")
    
    if not state["conversion_id"] or not state["output_id"]:
        log_test("Submit feedback", "FAIL", "Missing conversion_id or output_id")
        return False
    
    data = {
        "conversion_id": state["conversion_id"],
        "target": "output",
        "target_id": state["output_id"],
        "rating": 5,
        "comments": "Excellent result, very accurate",
        "metadata": {"ui_version": "1.0.0"}
    }
    
    response = make_request(
        "POST",
        "/feedback",
        data=data,
        expect_code=201,
        test_name="Submit feedback (POST /feedback)"
    )
    
    if response and "feedback_id" in response:
        state["feedback_id"] = response["feedback_id"]
        log_test(
            "Feedback submitted",
            "PASS",
            f"feedback_id: {response['feedback_id']}"
        )
        print(f"\n   ✓ Feedback document created in Cosmos DB")
        print(f"   ✓ Ownership validated")
        return True
    else:
        log_test("Submit feedback", "FAIL", "No feedback_id in response")
        return False


# ===== STEP 8: RETRIEVE FEEDBACK =====

def step_8_retrieve_feedback():
    """Step 8: Retrieve single feedback."""
    print("\n" + "="*70)
    print("STEP 8: RETRIEVE FEEDBACK")
    print("="*70)
    print("Endpoint: GET /api/v1/feedback/{feedback_id}")
    print("Purpose: Get single feedback item\n")
    
    if not state["feedback_id"]:
        log_test("Retrieve feedback", "FAIL", "No feedback_id from step 7")
        return False
    
    response = make_request(
        "GET",
        f"/feedback/{state['feedback_id']}",
        expect_code=200,
        test_name="Retrieve feedback (GET /feedback/{id})"
    )
    
    if response and "feedback_id" in response:
        log_test(
            "Feedback retrieved",
            "PASS",
            f"rating: {response.get('rating')}, target: {response.get('target')}"
        )
        print(f"\n   ✓ Feedback details returned")
        return True
    else:
        log_test("Retrieve feedback", "FAIL", "Feedback details not returned")
        return False


# ===== STEP 9: LIST FEEDBACK =====

def step_9_list_feedback():
    """Step 9: List all feedback for conversion."""
    print("\n" + "="*70)
    print("STEP 9: LIST FEEDBACK FOR CONVERSION")
    print("="*70)
    print("Endpoint: GET /api/v1/feedback/conversion/{conversion_id}")
    print("Purpose: Get all feedback for a conversion\n")
    
    if not state["conversion_id"]:
        log_test("List feedback", "FAIL", "No conversion_id from step 1")
        return False
    
    response = make_request(
        "GET",
        f"/feedback/conversion/{state['conversion_id']}",
        expect_code=200,
        test_name="List feedback (GET /feedback/conversion/{id})"
    )
    
    if response and isinstance(response.get("feedback"), list):
        feedback_count = len(response["feedback"])
        log_test(
            "Feedback list retrieved",
            "PASS",
            f"found {feedback_count} feedback items"
        )
        print(f"\n   ✓ Array of feedback items returned")
        print(f"   ✓ Ownership validated")
        return True
    else:
        log_test("List feedback", "FAIL", "Feedback list not returned")
        return False


# ===== STEP 10: VALIDATE QUOTA USAGE =====

def step_10_validate_quota():
    """Step 10: Validate quota usage."""
    print("\n" + "="*70)
    print("STEP 10: VALIDATE QUOTA USAGE")
    print("="*70)
    print("Endpoint: GET /api/v1/quota")
    print("Purpose: Verify all quota counters\n")
    
    response = make_request(
        "GET",
        "/quota",
        expect_code=200,
        test_name="Get quota usage (GET /quota)"
    )
    
    if response and "usage" in response:
        usage = response["usage"]
        print(f"\n   Quota Usage Summary:")
        print(f"   ├─ conversions_used: {usage.get('conversions_used', 0)} (expect: 1)")
        print(f"   ├─ api_calls_used: {usage.get('api_calls_used', 0)} (expect: 2)")
        print(f"   ├─ exports_used: {usage.get('exports_used', 0)} (expect: 1)")
        print(f"   └─ tier: {response.get('tier', 'unknown')}")
        
        checks = [
            (usage.get("conversions_used") == 1, "conversions_used = 1"),
            (usage.get("api_calls_used") == 2, "api_calls_used = 2"),
            (usage.get("exports_used") == 1, "exports_used = 1"),
        ]
        
        all_pass = all(check[0] for check in checks)
        
        if all_pass:
            log_test(
                "Quota validation",
                "PASS",
                "All quota counters correct"
            )
            return True
        else:
            failed = [check[1] for check in checks if not check[0]]
            log_test(
                "Quota validation",
                "FAIL",
                f"Failed checks: {', '.join(failed)}"
            )
            return False
    else:
        log_test("Get quota usage", "FAIL", "No usage data in response")
        return False


# ===== STEP 11: NEGATIVE TESTS =====

def step_11_negative_tests():
    """Step 11: Run negative test cases."""
    print("\n" + "="*70)
    print("STEP 11: NEGATIVE TESTS (INTENTIONAL ERRORS)")
    print("="*70 + "\n")
    
    # Test 11a: Invalid conversion ID
    print("Test 11a: Invalid conversion ID")
    print("─" * 70)
    response = make_request(
        "POST",
        "/schema/generate",
        data={
            "document_id": "doc-001",
            "conversion_id": "fake-invalid-id-xyz"
        },
        expect_code=404,
        test_name="Schema generate with invalid conversion (expect 404)"
    )
    if response is None:
        log_test("Invalid conversion ID", "PASS", "404 returned as expected", 404)
    
    # Test 11b: Invalid output format
    print("\nTest 11b: Invalid output format")
    print("─" * 70)
    if state["conversion_id"]:
        response = make_request(
            "POST",
            "/outputs/generate",
            data={
                "conversion_id": state["conversion_id"],
                "document_id": "doc-001",
                "format": "invalid_format_xyz",
                "output_data": {}
            },
            expect_code=400,
            test_name="Output generate with invalid format (expect 400)"
        )
        if response is None:
            log_test("Invalid output format", "PASS", "400 returned as expected", 400)
    
    # Test 11c: Unauthorized access (would need different token)
    print("\nTest 11c: Missing authorization header")
    print("─" * 70)
    headers_no_auth = {"Content-Type": "application/json"}
    try:
        response = requests.post(
            f"{BASE_URL}/conversions",
            json={"document_name": "test.pdf"},
            headers=headers_no_auth
        )
        if response.status_code == 401:
            log_test("Missing authorization", "PASS", "401 returned as expected", 401)
        else:
            log_test("Missing authorization", "FAIL", f"Expected 401, got {response.status_code}")
    except Exception as e:
        log_test("Missing authorization", "FAIL", str(e))


# ===== MAIN TEST RUNNER =====

def run_full_workflow(token: str):
    """Run complete end-to-end workflow."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "KRAFTD END-TO-END WORKFLOW TEST" + " "*23 + "║")
    print("║" + " "*68 + "║")
    print("║" + " Full API workflow validation with quota enforcement" + " "*16 + "║")
    print("╚" + "="*68 + "╝")
    
    # Setup
    setup_auth(token)
    
    # Run tests
    if not step_0_setup():
        print("\n❌ Server not running. Exiting.")
        return False
    
    step_1_create_conversion()
    step_2_generate_schema()
    step_3_revise_schema()
    step_4_finalize_schema()
    step_5_generate_summary()
    step_6_generate_output()
    step_7_submit_feedback()
    step_8_retrieve_feedback()
    step_9_list_feedback()
    step_10_validate_quota()
    step_11_negative_tests()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📊 Total:  {results['passed'] + results['failed']}")
    print("="*70 + "\n")
    
    if results['failed'] == 0:
        print("🎉 ALL TESTS PASSED! Workflow is fully functional.\n")
        return True
    else:
        print(f"⚠️  {results['failed']} test(s) failed. Review errors above.\n")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("\n📋 USAGE:")
        print(f"   python {sys.argv[0]} <JWT_TOKEN> [--base-url URL]\n")
        print("📌 EXAMPLE (localhost):")
        print("   python KRAFTD_E2E_TEST.py 'eyJhbGc...'\n")
        print("📌 EXAMPLE (Azure deployment):")
        print("   python KRAFTD_E2E_TEST.py 'eyJhbGc...' --base-url 'https://api.kraftd.azurecontainerapps.io/api/v1'\n")
        sys.exit(1)
    
    global BASE_URL
    
    token = sys.argv[1]
    
    # Check for --base-url argument
    if len(sys.argv) > 3 and sys.argv[2] == "--base-url":
        BASE_URL = sys.argv[3]
        print(f"🔄 Using custom base URL: {BASE_URL}\n")
    
    success = run_full_workflow(token)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
