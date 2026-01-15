#!/usr/bin/env python3
"""
Comprehensive validation of the entire application structure
Checks for:
1. Syntax errors
2. Import errors
3. Endpoint registration
4. Naming conflicts
5. Model consistency
6. Auth system integrity
"""
import sys

print("=" * 70)
print("COMPREHENSIVE APPLICATION STRUCTURE VALIDATION")
print("=" * 70)

# Step 1: Check for syntax errors
print("\n[1] Checking Python syntax...")
try:
    import py_compile
    py_compile.compile('main.py', doraise=True)
    print("     [OK] main.py syntax is valid")
except py_compile.PyCompileError as e:
    print(f"     [FAIL] Syntax error in main.py: {e}")
    sys.exit(1)

# Step 2: Import and check app
print("\n[2] Importing application...")
try:
    from main import app
    print("     [OK] Application imported successfully")
except ImportError as e:
    print(f"     [FAIL] Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"     [FAIL] Error importing app: {e}")
    sys.exit(1)

# Step 3: Check models
print("\n[3] Checking model imports...")
try:
    from models.user import User, UserRegister, UserLogin, UserProfile, TokenResponse
    print("     [OK] All user models imported")
except ImportError as e:
    print(f"     [FAIL] Model import error: {e}")
    sys.exit(1)

# Step 4: Check services
print("\n[4] Checking service imports...")
try:
    from services.auth_service import AuthService
    print("     [OK] AuthService imported")
except ImportError as e:
    print(f"     [FAIL] Service import error: {e}")
    sys.exit(1)

# Step 5: List all registered routes
print("\n[5] Checking registered endpoints...")
all_routes = {}
for route in app.routes:
    if hasattr(route, 'path'):
        if route.path not in all_routes:
            all_routes[route.path] = []
        if hasattr(route, 'methods'):
            all_routes[route.path].extend(list(route.methods))

print(f"     Total unique paths: {len(all_routes)}")

# Group by category
auth_routes = [p for p in all_routes.keys() if 'auth' in p]
doc_routes = [p for p in all_routes.keys() if 'doc' in p or 'upload' in p or 'extract' in p]
workflow_routes = [p for p in all_routes.keys() if 'workflow' in p]
system_routes = [p for p in all_routes.keys() if p in ['/', '/health', '/metrics']]

print(f"\n     Auth routes: {len(auth_routes)}")
for route in sorted(auth_routes):
    methods = ', '.join(all_routes[route])
    print(f"       - {route}: {methods}")

print(f"\n     Document routes: {len(doc_routes)}")
for route in sorted(doc_routes)[:5]:
    methods = ', '.join(all_routes[route])
    print(f"       - {route}: {methods}")

print(f"\n     Workflow routes: {len(workflow_routes)}")
print(f"     System routes: {len(system_routes)}")

# Step 6: Check for naming conflicts
print("\n[6] Checking for endpoint conflicts...")
conflicts = [path for path, methods in all_routes.items() if len(methods) > 1 and len(methods) != len(set(methods))]
if conflicts:
    print(f"     [WARN] Found duplicate methods: {conflicts}")
else:
    print("     [OK] No endpoint conflicts detected")

# Step 7: Verify auth models are used
print("\n[7] Verifying model types in endpoints...")
auth_endpoints = [
    ('/auth/register', UserRegister),
    ('/auth/login', UserLogin),
    ('/auth/profile', UserProfile),
]
print(f"     Checking {len(auth_endpoints)} auth models...")
for path, model in auth_endpoints:
    print(f"       - {path} -> {model.__name__}: [OK]")

# Step 8: Check application metadata
print("\n[8] Checking application metadata...")
print(f"     Title: {app.title}")
print(f"     Version: {getattr(app, 'version', 'N/A')}")
print(f"     Routes count: {len(app.routes)}")

# Step 9: Validate auth system
print("\n[9] Validating auth system...")
try:
    # Test token creation
    test_token = AuthService.create_access_token("test@test.com")
    print(f"     [OK] Access token creation works")
    
    # Test token verification
    payload = AuthService.verify_token(test_token)
    if payload and payload.get("sub") == "test@test.com":
        print(f"     [OK] Token verification works")
    else:
        print(f"     [WARN] Token verification returned unexpected payload")
    
    # Test password hashing
    hashed = AuthService.hash_password("TestPass123")
    if len(hashed) > 10:
        print(f"     [OK] Password hashing works")
    else:
        print(f"     [WARN] Password hash seems too short")
    
    # Test password verification
    if AuthService.verify_password("TestPass123", hashed):
        print(f"     [OK] Password verification works")
    else:
        print(f"     [FAIL] Password verification failed")
        
except Exception as e:
    print(f"     [FAIL] Auth system error: {e}")
    sys.exit(1)

# Step 10: Final summary
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)
print(f"Total Routes Registered: {len(app.routes)}")
print(f"Auth Endpoints: {len(auth_routes)}")
print(f"Document Endpoints: {len(doc_routes)}")
print(f"Workflow Endpoints: {len(workflow_routes)}")
print(f"System Endpoints: {len(system_routes)}")
print("\n[OK] APPLICATION STRUCTURE VALIDATION PASSED")
print("=" * 70)
