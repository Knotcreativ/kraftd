#!/usr/bin/env python3
"""
Create Cosmos DB database and containers from scratch

This will:
1. Create the KraftdIntel database if it doesn't exist
2. Create events container with /user_id partition key
3. Create dashboards container with /user_id partition key
4. Create preferences container with /user_id partition key
"""

import os
import sys
from azure.cosmos import CosmosClient, PartitionKey, exceptions
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

endpoint = os.getenv("COSMOS_ENDPOINT")
key = os.getenv("COSMOS_KEY")

if not endpoint or not key:
    print("ERROR: COSMOS_ENDPOINT and COSMOS_KEY required")
    sys.exit(1)

print("Connecting to Cosmos DB...")
client = CosmosClient(endpoint, key)

# Create database
print("Creating database 'KraftdIntel'...")
try:
    database = client.create_database(id="KraftdIntel")
    print("  ✓ Database created")
except exceptions.CosmosResourceExistsError:
    print("  ✓ Database already exists")
    database = client.get_database_client("KraftdIntel")

# Create events container
print("Creating 'events' container...")
try:
    events_container = database.create_container(
        id="events",
        partition_key=PartitionKey(path="/user_id"),
        default_ttl=180 * 86400  # 180 days in seconds
    )
    print("  ✓ events container created with /user_id partition key")
except exceptions.CosmosResourceExistsError:
    print("  ✓ events container already exists")

# Create dashboards container
print("Creating 'dashboards' container...")
try:
    dashboards_container = database.create_container(
        id="dashboards",
        partition_key=PartitionKey(path="/user_id"),
        default_ttl=None  # No expiration
    )
    print("  ✓ dashboards container created with /user_id partition key")
except exceptions.CosmosResourceExistsError:
    print("  ✓ dashboards container already exists")

# Create preferences container
print("Creating 'preferences' container...")
try:
    preferences_container = database.create_container(
        id="preferences",
        partition_key=PartitionKey(path="/user_id"),
        default_ttl=None  # No expiration
    )
    print("  ✓ preferences container created with /user_id partition key")
except exceptions.CosmosResourceExistsError:
    print("  ✓ preferences container already exists")

print("\n✓ All containers ready!")
print("\nNext steps:")
print("  1. Run test_cosmos_integration.py to verify CRUD operations")
print("  2. Start backend server: python -m uvicorn main:app")
print("  3. Test event storage endpoints")
