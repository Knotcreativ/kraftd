#!/usr/bin/env python3
"""Debug auth routes registration"""
import sys

print("[DEBUG] Testing app initialization...")
try:
    print("[1] Importing main...")
    from main import app
    print("[2] Main imported successfully")
    
    print("[3] Checking app.routes...")
    total = len(app.routes)
    auth_routes = [r for r in app.routes if "auth" in str(r.path).lower()]
    print(f"[4] Total routes: {total}, Auth routes: {len(auth_routes)}")
    for r in auth_routes:
        print(f"    - {r.path}")
    
    print("[5] Checking router attribute...")
    print(f"    App has router: {hasattr(app, 'router')}")
    
    print("[6] All route paths:")
    for r in app.routes:
        if hasattr(r, 'path'):
            print(f"    - {r.path}")
    
except Exception as e:
    import traceback
    print(f"[ERROR] {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.exit(1)
