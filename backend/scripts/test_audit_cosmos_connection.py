import os
import sys
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

def test_connection():
    """Test Cosmos DB connection with credentials from environment"""
    
    endpoint = os.getenv("COSMOS_ENDPOINT")
    key = os.getenv("COSMOS_KEY")
    db_name = os.getenv("COSMOS_DATABASE", "KraftdDB")
    container_name = os.getenv("COSMOS_DB_AUDIT_CONTAINER", "audit_events")
    
    print("=" * 60)
    print("Testing Cosmos DB Connection")
    print("=" * 60)
    print()
    
    # Verify credentials are set
    if not endpoint:
        print("❌ ERROR: COSMOS_ENDPOINT not set")
        return False
    if not key:
        print("❌ ERROR: COSMOS_KEY not set")
        return False
    
    print(f"✓ Endpoint: {endpoint}")
    print(f"✓ Key: {key[:20]}...")
    print(f"✓ Database: {db_name}")
    print(f"✓ Container: {container_name}")
    print()
    
    try:
        print("Connecting to Cosmos DB...")
        client = CosmosClient(endpoint, key)
        print("✅ Successfully created CosmosClient")
        
        print(f"\nConnecting to database '{db_name}'...")
        db = client.get_database_client(db_name)
        print(f"✅ Successfully accessed database: {db_name}")
        
        print(f"\nAccessing container '{container_name}'...")
        container = db.get_container_client(container_name)
        print(f"✅ Successfully accessed container: {container_name}")
        
        # Test write
        print("\nWriting test item...")
        test_item = {
            "id": "test-connection-2026",
            "tenant_id": "test-tenant-001",
            "event_type": "CONNECTION_TEST",
            "timestamp": "2026-01-18T22:45:00Z",
            "user_email": "test@example.com",
            "action": "test_connection",
            "status": "success"
        }
        container.upsert_item(test_item)
        print("✅ Successfully wrote test item")
        
        # Test read
        print("\nReading test item back...")
        read_item = container.read_item("test-connection-2026", "test@example.com")
        print(f"✅ Successfully read test item: {read_item['id']}")
        
        # Verify data
        if read_item['event_type'] == "CONNECTION_TEST":
            print("✅ Test item data verified correctly")
        
        # Cleanup
        print("\nCleaning up test item...")
        container.delete_item("test-connection-2026", "test@example.com")
        print("✅ Successfully deleted test item")
        
        print()
        print("=" * 60)
        print("✅ ALL COSMOS DB CONNECTION TESTS PASSED!")
        print("=" * 60)
        print()
        print("Your Cosmos DB is ready to receive audit events.")
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ CONNECTION TEST FAILED")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        print("Troubleshooting tips:")
        print("1. Verify COSMOS_DB_ENDPOINT is set correctly")
        print("2. Verify COSMOS_DB_KEY is set correctly")
        print("3. Check that database 'kraftd_audit' exists")
        print("4. Check that container 'audit_events' exists")
        print("5. Verify network connectivity to Azure")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
