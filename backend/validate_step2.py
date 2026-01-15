#!/usr/bin/env python
"""Validate Step 2: Route Path Fixes"""

import sys
import os

print("="*80)
print("STEP 2 VALIDATION: Route Path Fixes (/api/v1/ versioning)")
print("="*80)

# Check 1: Verify no old routes remain  
print("\n[1/4] Checking for old route patterns...")
with open("main.py", "r") as f:
    content = f.read()
    
old_patterns = [
    'route("/', '@app.post("/auth', '@app.get("/auth', '@app.post("/docs',
    '@app.post("/convert', '@app.post("/extract', '@app.post("/workflow',
    '@app.get("/documents', '@app.post("/agent', '@app.get("/health',
    '@app.get("/metrics', '@app.get("/"'
]

found_old = [p for p in old_patterns if p in content]
if found_old:
    print(f"  ❌ FAIL: Found old route patterns: {found_old}")
    sys.exit(1)
print("  ✅ No old route patterns found")

# Check 2: Verify all new routes use /api/v1/ prefix
print("\n[2/4] Checking for new route patterns with /api/v1/ prefix...")
required_routes = [
    '@app.post("/api/v1/auth/register',
    '@app.post("/api/v1/auth/login',
    '@app.post("/api/v1/auth/refresh',
    '@app.get("/api/v1/auth/profile',
    '@app.get("/api/v1/auth/validate',
    '@app.get("/api/v1/health',
    '@app.get("/api/v1/metrics',
    '@app.get("/api/v1/"',
    '@app.post("/api/v1/docs/upload',
    '@app.post("/api/v1/docs/convert',
    '@app.post("/api/v1/docs/extract',
    '@app.post("/api/v1/workflow/inquiry',
    '@app.post("/api/v1/workflow/estimation',
    '@app.post("/api/v1/workflow/normalize-quotes',
    '@app.post("/api/v1/workflow/comparison',
    '@app.post("/api/v1/workflow/proposal',
    '@app.post("/api/v1/workflow/po',
    '@app.post("/api/v1/workflow/proforma-invoice',
    '@app.get("/api/v1/documents/{document_id}/output',
    '@app.get("/api/v1/documents/{document_id}"',
    '@app.get("/api/v1/documents/{document_id}/status',
]

missing_routes = [r for r in required_routes if r not in content]
if missing_routes:
    print(f"  ❌ FAIL: Missing new route patterns: {missing_routes}")
    sys.exit(1)
    
print(f"  ✅ All {len(required_routes)} required routes found with /api/v1/ prefix")

# Check 3: Test that the app can be imported without errors
print("\n[3/4] Testing that main.py imports correctly...")
try:
    from main import app
    print("  ✅ main.py imported successfully")
except Exception as e:
    print(f"  ❌ FAIL: Could not import main.py: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check 4: Verify OpenAPI routes are updated
print("\n[4/4] Verifying OpenAPI schema shows new routes...")
try:
    # Get the routes from the app
    api_v1_routes = [str(route.path) for route in app.routes if '/api/v1/' in str(route.path)]
    
    if len(api_v1_routes) < 15:
        print(f"  ❌ FAIL: Expected at least 15 /api/v1/ routes, found {len(api_v1_routes)}")
        print(f"     Routes: {api_v1_routes}")
        sys.exit(1)
    
    print(f"  ✅ Found {len(api_v1_routes)} /api/v1/ routes in FastAPI app")
    print(f"     Sample routes: {api_v1_routes[:5]}")
except Exception as e:
    print(f"  ❌ FAIL: Could not verify routes: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("✅ ALL STEP 2 VALIDATIONS PASSED")
print("="*80)
print("\nSummary:")
print("  ✓ All old route patterns removed")
print("  ✓ All new routes use /api/v1/ versioning")
print("  ✓ All 21 routes successfully updated")
print("  ✓ app imports correctly")
print("  ✓ OpenAPI schema reflects new paths")
print("\nStep 2 is production-ready. Proceeding to Step 3...")
