#!/usr/bin/env python3
"""
Cosmos DB Connection Test
Tests connectivity to Azure Cosmos DB and validates basic operations.
"""

import os
import sys
import asyncio
from azure.cosmos import CosmosClient, exceptions
from azure.cosmos.partition_key import PartitionKey
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_cosmos_connection():
    """Test Cosmos DB connection and basic operations"""

    print("[TEST] Testing Cosmos DB Connection...")
    print("=" * 50)

    # Get connection details
    connection_string = os.getenv("AZURE_COSMOS_CONNECTION_STRING")
    database_name = os.getenv("COSMOS_DB_DATABASE", "kraftdintel")
    container_name = os.getenv("COSMOS_DB_CONTAINER", "documents")

    if not connection_string:
        print("[ERROR] AZURE_COSMOS_CONNECTION_STRING not found in environment")
        return False

    try:
        # Create client
        print("[INFO] Connecting to Cosmos DB...")
        client = CosmosClient.from_connection_string(connection_string)

        # Test database access
        print(f"[INFO] Checking database: {database_name}")
        database = client.get_database_client(database_name)

        # List databases to verify connection
        databases = list(client.list_databases())
        db_names = [db['id'] for db in databases]
        print(f"[SUCCESS] Available databases: {db_names}")

        if database_name not in db_names:
            print(f"[WARNING] Database '{database_name}' not found. Creating...")
            database = client.create_database(database_name)
            print("[SUCCESS] Database created successfully")

        # Test container access
        print(f"[INFO] Checking container: {container_name}")
        container = database.get_container_client(container_name)

        # Try to get container properties (this will fail if container doesn't exist)
        try:
            container_properties = container.get_container_properties()
            print(f"[SUCCESS] Container '{container_name}' exists")
            print(f"   Partition Key: {container_properties['partitionKey']}")
        except exceptions.CosmosResourceNotFoundError:
            print(f"[WARNING] Container '{container_name}' not found. Creating...")
            container = database.create_container(
                id=container_name,
                partition_key=PartitionKey(path="/user_email"),
                offer_throughput=400
            )
            print("[SUCCESS] Container created successfully")

        # Test basic CRUD operations
        print("[INFO] Testing CRUD operations...")

        # Create test document
        test_doc = {
            "id": "test-connection-doc",
            "user_email": "test@kraftdintel.com",
            "type": "connection_test",
            "timestamp": "2026-01-23T16:00:00Z",
            "message": "Connection test successful"
        }

        # Create
        created_doc = container.create_item(test_doc)
        print("[SUCCESS] Create operation successful")

        # Read
        read_doc = container.read_item("test-connection-doc", "test@kraftdintel.com")
        print("[SUCCESS] Read operation successful")

        # Update
        read_doc["message"] = "Connection test updated"
        updated_doc = container.replace_item("test-connection-doc", read_doc)
        print("[SUCCESS] Update operation successful")

        # Delete
        container.delete_item("test-connection-doc", "test@kraftdintel.com")
        print("[SUCCESS] Delete operation successful")

        # Test query
        query = "SELECT * FROM c WHERE c.type = 'connection_test'"
        items = list(container.query_items(query, enable_cross_partition_query=True))
        print(f"[SUCCESS] Query operation successful (found {len(items)} items)")

        print("\n" + "=" * 50)
        print("[SUCCESS] COSMOS DB CONNECTION TEST PASSED!")
        print("[SUCCESS] All operations successful")
        print("[SUCCESS] Database and container accessible")
        print("[SUCCESS] CRUD operations working")
        print("[SUCCESS] Query functionality verified")
        return True

    except exceptions.CosmosHttpResponseError as e:
        print(f"[ERROR] Cosmos DB Error: {e.status_code} - {e.message}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return False

async def main():
    """Main test function"""
    print("[TEST] KRAFTD COSMOS DB READINESS TEST")
    print("==================================")

    success = await test_cosmos_connection()

    if success:
        print("\n[SUCCESS] READY FOR DEPLOYMENT: Cosmos DB connection verified")
        sys.exit(0)
    else:
        print("\n[ERROR] DEPLOYMENT BLOCKED: Cosmos DB connection failed")
        print("[INFO] Check your .env file and Azure Cosmos DB configuration")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())