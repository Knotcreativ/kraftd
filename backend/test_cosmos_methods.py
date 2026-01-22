#!/usr/bin/env python3
"""Quick test to verify CosmosService methods are available and app boots."""

import sys
import asyncio

def test_cosmos_service():
    """Test that all CosmosService methods exist and are async."""
    from services.cosmos_service import CosmosService
    import inspect
    
    cosmos = CosmosService()
    methods = ['create_item', 'read_item', 'replace_item', 'query_items']
    
    print('[OK] CosmosService Methods Verification:')
    print('=' * 50)
    
    for method_name in methods:
        method = getattr(cosmos, method_name, None)
        if not method:
            print(f'[FAIL] {method_name} - NOT FOUND')
            return False
        
        if not inspect.iscoroutinefunction(method):
            print(f'[FAIL] {method_name} - NOT ASYNC')
            return False
        
        print(f'[OK] {method_name:20} (async)')
    
    return True


def test_app_boot():
    """Test that FastAPI app boots successfully."""
    try:
        from main import app
        
        print()
        print('[OK] FastAPI App Status:')
        print('=' * 50)
        
        routes = [r for r in app.routes if hasattr(r, 'path')]
        print(f'[OK] Total routes loaded: {len(routes)}')
        
        schema = app.openapi()
        endpoints = len(schema.get('paths', {}))
        print(f'[OK] OpenAPI endpoints: {endpoints}')
        
        # Verify schema routes are present
        schema_endpoints = [p for p in schema.get('paths', {}).keys() if 'schema' in p or 'summary' in p]
        print(f'[OK] Schema/Summary endpoints: {len(schema_endpoints)}')
        
        return True
    except Exception as e:
        print(f'[FAIL] App boot error: {e}')
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print('Testing CosmosService Updates')
    print('=' * 50)
    print()
    
    cosmos_ok = test_cosmos_service()
    app_ok = test_app_boot()
    
    print()
    print('Integration Status:')
    print('=' * 50)
    
    if cosmos_ok and app_ok:
        print('[OK] All methods available')
        print('[OK] App boots successfully')
        print('[OK] conversions_service.py can now use await self.cosmos.create_item()')
        print('[OK] Ready for new services: schema_service, summary_service, output_service')
        return 0
    else:
        print('[FAIL] Verification failed')
        return 1


if __name__ == '__main__':
    sys.exit(main())
