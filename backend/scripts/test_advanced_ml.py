"""
Test Advanced ML Endpoints
Tests mobility clustering, pricing index, and supplier ecosystem models
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"
TEST_EMAIL = f"ml_test_{int(time.time())}@example.com"
TEST_PASSWORD = "SecurePass123"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def test_health():
    """Test backend health"""
    print_section("1. Testing Backend Health")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Backend is healthy")
            return True
        else:
            print(f"✗ Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_registration():
    """Register a test user and get token"""
    print_section("2. User Registration & Authentication")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "acceptTerms": True,
                "acceptPrivacy": True,
                "name": "ML Test User"
            }
        )
        print(f"Registration Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            token = data.get("access_token")
            print(f"✓ User registered successfully")
            print(f"✓ Token received: {token[:20]}...")
            return token
        else:
            print(f"✗ Registration failed: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def create_test_documents():
    """Create sample procurement documents"""
    base_date = datetime.now()
    
    docs = [
        {
            "id": "doc-001",
            "type": "PROCUREMENT_ORDER",
            "title": "Shanghai-LA Shipment",
            "supplier_name": "GlobalSupply Inc",
            "supplier_location": "Shanghai, China",
            "delivery_location": "Los Angeles, USA",
            "order_date": base_date.isoformat(),
            "delivery_date": (base_date + timedelta(days=45)).isoformat(),
            "transport_mode": "sea",
            "unit_price": 50.0,
            "currency": "USD",
            "quantity": 100,
            "status": "RECEIVED"
        },
        {
            "id": "doc-002",
            "type": "PROCUREMENT_ORDER",
            "title": "Bangkok-Singapore Route",
            "supplier_name": "AsiaTrade Ltd",
            "supplier_location": "Bangkok, Thailand",
            "delivery_location": "Singapore",
            "order_date": base_date.isoformat(),
            "delivery_date": (base_date + timedelta(days=7)).isoformat(),
            "transport_mode": "land",
            "unit_price": 35.0,
            "currency": "USD",
            "quantity": 250,
            "status": "RECEIVED"
        },
        {
            "id": "doc-003",
            "type": "PROCUREMENT_ORDER",
            "title": "EU Electronics",
            "supplier_name": "EuroTech GmbH",
            "supplier_location": "Berlin, Germany",
            "delivery_location": "Frankfurt, Germany",
            "order_date": base_date.isoformat(),
            "delivery_date": (base_date + timedelta(days=3)).isoformat(),
            "transport_mode": "air",
            "unit_price": 120.0,
            "currency": "EUR",
            "quantity": 50,
            "status": "RECEIVED"
        }
    ]
    return docs

def test_mobility_analysis(token):
    """Test mobility clustering endpoint"""
    print_section("3. Testing Mobility Clustering Analysis")
    
    docs = create_test_documents()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ml/advanced/mobility/analyze",
            json={"documents": docs, "eps": 0.5, "min_samples": 2},
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Mobility analysis successful")
            print(f"\nClusters Found:")
            for i, cluster in enumerate(data.get("clusters", {}).items()):
                cluster_id, routes = cluster
                print(f"  Cluster {cluster_id}: {len(routes)} routes")
                for route in routes[:2]:  # Show first 2
                    print(f"    - {route.get('supplier_location')} → {route.get('delivery_location')}")
            
            anomalies = data.get("anomalies", [])
            if anomalies:
                print(f"\nAnomalies Detected: {len(anomalies)}")
                for anomaly in anomalies[:2]:
                    print(f"  - {anomaly.get('anomaly_type')}: {anomaly.get('description')[:50]}...")
            
            return True
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"  Response: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_pricing_index(token):
    """Test pricing index endpoint"""
    print_section("4. Testing Pricing Index Analysis")
    
    docs = create_test_documents()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ml/advanced/pricing/index",
            json={
                "documents": docs,
                "commodity_category": "Electronics",
                "region": "APAC",
                "include_trend": True
            },
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Pricing index calculation successful")
            print(f"\nPricing Metrics:")
            print(f"  Index Value: {data.get('index_value'):.2f}")
            print(f"  Volatility Score: {data.get('volatility_score', 'N/A'):.2f}")
            
            fair_price = data.get('fair_price_range', {})
            print(f"  Fair Price Range: ${fair_price.get('p25'):.2f} - ${fair_price.get('p75'):.2f}")
            
            trend = data.get('trend', 'stable')
            print(f"  Price Trend: {trend}")
            
            return True
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"  Response: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_supplier_ecosystem(token):
    """Test supplier ecosystem scoring endpoint"""
    print_section("5. Testing Supplier Ecosystem Scoring")
    
    docs = create_test_documents()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ml/advanced/suppliers/ecosystem",
            json={"documents": docs, "include_predictions": True},
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Supplier ecosystem analysis successful")
            
            suppliers = data.get('supplier_scores', [])
            print(f"\nSupplier Scores ({len(suppliers)} suppliers):")
            for supplier in suppliers:
                name = supplier.get('supplier_name')
                score = supplier.get('ecosystem_score', 0)
                grade = supplier.get('grade', 'N/A')
                print(f"  {name}: {score:.1f}/100 (Grade: {grade})")
            
            summary = data.get('ecosystem_summary', {})
            print(f"\nEcosystem Summary:")
            print(f"  Average Score: {summary.get('average_score', 0):.1f}")
            print(f"  Highest Score: {summary.get('highest_score', 0):.1f}")
            print(f"  Lowest Score: {summary.get('lowest_score', 0):.1f}")
            
            return True
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"  Response: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_investment_opportunities(token):
    """Test investment opportunities endpoint"""
    print_section("6. Testing Investment Opportunities")
    
    docs = create_test_documents()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ml/advanced/suppliers/investment-opportunities",
            json={"documents": docs, "min_score": 50},
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Investment opportunities identified")
            
            opportunities = data.get('opportunities', [])
            print(f"\nTop Investment Opportunities ({len(opportunities)}):")
            for opp in opportunities[:5]:
                name = opp.get('supplier_name')
                score = opp.get('investment_score', 0)
                print(f"  {name}: Score {score:.1f}/100")
            
            return True
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"  Response: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n")
    print("█" * 70)
    print("█ ADVANCED ML SYSTEM - INTEGRATION TEST")
    print("█" * 70)
    
    results = []
    
    # Test 1: Health
    if not test_health():
        print("\n✗ Backend is not running. Please start the backend server.")
        return
    results.append(("Backend Health", True))
    
    # Test 2: Registration & Auth
    token = test_registration()
    if not token:
        print("\n✗ Could not authenticate. Aborting remaining tests.")
        return
    results.append(("User Registration", True))
    
    # Test 3-6: Advanced ML Endpoints
    results.append(("Mobility Clustering", test_mobility_analysis(token)))
    time.sleep(0.5)
    results.append(("Pricing Index", test_pricing_index(token)))
    time.sleep(0.5)
    results.append(("Supplier Ecosystem", test_supplier_ecosystem(token)))
    time.sleep(0.5)
    results.append(("Investment Opportunities", test_investment_opportunities(token)))
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed\n")
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print("\n" + "=" * 70)
    if passed == total:
        print("✓ ALL TESTS PASSED - Advanced ML System is fully operational!")
    else:
        print(f"⚠ {total - passed} test(s) failed - Check errors above")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
