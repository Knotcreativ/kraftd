#!/usr/bin/env python3
"""
Check Cosmos DB container schema and partition keys
"""

import os
import sys
from azure.cosmos import CosmosClient

endpoint = os.getenv("COSMOS_ENDPOINT")
key = os.getenv("COSMOS_KEY")

if not endpoint or not key:
    print("ERROR: COSMOS_ENDPOINT and COSMOS_KEY required")
    sys.exit(1)

client = CosmosClient(endpoint, key)
database = client.get_database_client("KraftdIntel")

containers = ["events", "dashboards", "preferences"]

for container_name in containers:
    try:
        container = database.get_container_client(container_name)
        props = container.read()
        
        print(f"\nContainer: {container_name}")
        print(f"  ID: {props.get('id')}")
        print(f"  Partition Key: {props.get('partitionKey', {}).get('paths', 'NOT SET')}")
        print(f"  TTL: {props.get('defaultTtl', 'NOT SET')}")
        
    except Exception as e:
        print(f"Error reading {container_name}: {e}")
