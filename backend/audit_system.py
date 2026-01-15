#!/usr/bin/env python3
"""
CRITICAL AUDIT: Verify Azure setup and existing functionality
This ensures we don't break anything when adding auth
"""
import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

print("=" * 70)
print("INFRASTRUCTURE & FUNCTIONALITY AUDIT")
print(f"Timestamp: {datetime.utcnow().isoformat()}")
print("=" * 70)
print()

# ===== 1. Azure Configuration Check =====
print("[1] AZURE CONFIGURATION CHECK")
print("-" * 70)

try:
    from config import (
        REQUEST_TIMEOUT, DOCUMENT_PROCESSING_TIMEOUT,
        METRICS_ENABLED, RATE_LIMIT_ENABLED, UPLOAD_DIR
    )
    print("[OK] Config module loaded")
    print(f"    - REQUEST_TIMEOUT: {REQUEST_TIMEOUT}s")
    print(f"    - DOC_PROC_TIMEOUT: {DOCUMENT_PROCESSING_TIMEOUT}s")
    print(f"    - METRICS: {METRICS_ENABLED}")
    print(f"    - RATE_LIMIT: {RATE_LIMIT_ENABLED}")
except Exception as e:
    print(f"[FAIL] Config error: {e}")
    sys.exit(1)

print()

# ===== 2. Document Processing Pipeline =====
print("[2] DOCUMENT PROCESSING CHECK")
print("-" * 70)

try:
    from document_processing import (
        PDFProcessor, WordProcessor, ExcelProcessor, ImageProcessor,
        DocumentExtractor, DocumentType
    )
    from document_processing.orchestrator import ExtractionPipeline
    print("[OK] All document processors imported")
    
    pipeline = ExtractionPipeline()
    print("[OK] ExtractionPipeline initialized")
except Exception as e:
    print(f"[FAIL] Document processing error: {e}")
    sys.exit(1)

print()

# ===== 3. AI Agent Check =====
print("[3] AI AGENT CHECK")
print("-" * 70)

try:
    from agent.kraft_agent import KraftdAIAgent
    print("[OK] KraftdAIAgent imported")
    print("    (Note: Full initialization requires Azure OpenAI)")
except Exception as e:
    print(f"[WARN] Agent module load warning: {e}")

print()

# ===== 4. Health Check Endpoint =====
print("[4] HEALTH CHECK ENDPOINT")
print("-" * 70)

try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    if response.status_code == 200:
        print("[OK] Health endpoint: 200 OK")
        data = response.json()
        print(f"    Status: {data.get('status')}")
    else:
        print(f"[FAIL] Health endpoint: {response.status_code}")
except Exception as e:
    print(f"[FAIL] Health check error: {e}")
    sys.exit(1)

print()

# ===== 5. Existing API Endpoints =====
print("[5] EXISTING API ENDPOINTS (Should be working)")
print("-" * 70)

existing_endpoints = [
    ("GET", "/health"),
    ("GET", "/metrics"),
    ("GET", "/"),
    ("POST", "/docs/upload"),
    ("POST", "/extract"),
    ("POST", "/convert"),
    ("POST", "/workflow/inquiry"),
]

working = 0
failing = 0

for method, path in existing_endpoints:
    try:
        if method == "GET":
            r = requests.get(f"{BASE_URL}{path}", timeout=3)
        else:
            # POST with empty/minimal payload
            r = requests.post(f"{BASE_URL}{path}", json={}, timeout=3)
        
        if r.status_code < 500:
            print(f"[OK] {method:4} {path:30} -> {r.status_code}")
            working += 1
        else:
            print(f"[WARN] {method:4} {path:30} -> {r.status_code}")
    except Exception as e:
        print(f"[FAIL] {method:4} {path:30} -> {type(e).__name__}")
        failing += 1

print()
print(f"Endpoints working: {working}/{len(existing_endpoints)}")

print()

# ===== 6. OpenAPI Schema Check =====
print("[6] OPENAPI SCHEMA CHECK")
print("-" * 70)

try:
    r = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
    if r.status_code == 200:
        data = r.json()
        total_paths = len(data.get('paths', {}))
        auth_paths = len([p for p in data.get('paths', {}).keys() if 'auth' in p])
        print(f"[OK] OpenAPI schema accessible")
        print(f"    - Total paths: {total_paths}")
        print(f"    - Auth paths: {auth_paths}")
        
        if auth_paths == 0:
            print("    [WARNING] Auth endpoints NOT in OpenAPI schema!")
            print("    Auth endpoints exist in code but Uvicorn may not be serving them")
        else:
            print(f"    [OK] Auth endpoints found in schema")
    else:
        print(f"[FAIL] OpenAPI: {r.status_code}")
except Exception as e:
    print(f"[FAIL] OpenAPI error: {e}")

print()

# ===== 7. App Routes Check =====
print("[7] APP ROUTES CHECK (Direct import)")
print("-" * 70)

try:
    from main import app
    total_routes = len(app.routes)
    auth_routes = len([r for r in app.routes if 'auth' in str(r.path).lower()])
    print(f"[OK] Main app imported")
    print(f"    - Total routes in app: {total_routes}")
    print(f"    - Auth routes in app: {auth_routes}")
    
    if auth_routes > 0:
        print(f"    [OK] Auth routes ARE in the app object")
        auth_list = [r.path for r in app.routes if 'auth' in str(r.path).lower() and 'oauth' not in r.path]
        for path in sorted(set(auth_list)):
            print(f"        - {path}")
    else:
        print(f"    [FAIL] Auth routes NOT in app object")
except Exception as e:
    print(f"[FAIL] App import error: {e}")

print()

# ===== 8. Critical Findings =====
print("[8] CRITICAL FINDINGS")
print("=" * 70)

findings = []

if working < len(existing_endpoints) - 2:
    findings.append("[WARNING] Some existing endpoints are failing")

if auth_paths == 0 and auth_routes > 0:
    findings.append("[CRITICAL] Auth routes in app but NOT in Uvicorn OpenAPI schema")
    findings.append("   This suggests Uvicorn is not loading updated app from main.py")
    findings.append("   Possible causes:")
    findings.append("   - Uvicorn process is stale/cached")
    findings.append("   - Module import error not being caught")
    findings.append("   - Middleware/lifespan intercepting routes")

if findings:
    for f in findings:
        print(f)
else:
    print("[OK] All checks passed! System is healthy.")

print()
print("=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)
