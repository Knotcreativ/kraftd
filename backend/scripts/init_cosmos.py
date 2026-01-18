#!/usr/bin/env python3
"""
Initialize Azure Cosmos DB for KraftdIntel Platform

Creates database and containers with proper schema, partition keys, and indexes.
Supports both local emulator and Azure cloud instances.

Usage:
    python scripts/init_cosmos.py                    # Local emulator
    python scripts/init_cosmos.py --production       # Azure cloud
"""

import os
import sys
import asyncio
import logging
from typing import Optional
from pathlib import Path

try:
    from azure.cosmos import CosmosClient, PartitionKey, exceptions
except ImportError:
    print("ERROR: azure-cosmos not installed")
    print("Run: pip install azure-cosmos")
    sys.exit(1)

# Load .env file
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CosmosDBInitializer:
    """Initializes Cosmos DB database and containers"""

    def __init__(self, endpoint: str, key: str):
        """
        Initialize with connection details
        
        Args:
            endpoint: Cosmos DB endpoint URL
            key: Cosmos DB primary key
        """
        self.endpoint = endpoint
        self.key = key
        self.client = None
        self.database = None

    def connect(self) -> bool:
        """
        Test connection to Cosmos DB
        
        Returns:
            True if connection successful
        """
        try:
            logger.info(f"Connecting to Cosmos DB at {self.endpoint}...")
            self.client = CosmosClient(self.endpoint, self.key)
            
            # Test connection with simple query
            account_info = self.client.get_database_account()
            logger.info(f"✓ Connected successfully")
            logger.info(f"  Account: {account_info.WritableLocations[0]['name']}")
            return True
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"✗ Connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Unexpected error: {e}")
            return False

    def create_database(self, database_name: str = "KraftdIntel") -> bool:
        """
        Create or get database
        
        Args:
            database_name: Name of database to create
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Creating/getting database '{database_name}'...")
            
            try:
                self.database = self.client.get_database_client(database_name)
                logger.info(f"✓ Database '{database_name}' exists")
            except exceptions.CosmosResourceNotFoundError:
                logger.info(f"  Creating new database...")
                self.database = self.client.create_database(database_name)
                logger.info(f"✓ Database '{database_name}' created")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to create database: {e}")
            return False

    def create_container(
        self, 
        container_name: str,
        partition_key: str = "/user_id",
        ttl: Optional[int] = None,
        throughput: int = 400
    ) -> bool:
        """
        Create or get container with partition key
        
        Args:
            container_name: Name of container
            partition_key: Partition key path (must start with /)
            ttl: Default TTL in seconds (None = no expiration)
            throughput: RU/s provisioned (minimum 400)
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Creating/getting container '{container_name}'...")
            
            try:
                container = self.database.get_container_client(container_name)
                logger.info(f"✓ Container '{container_name}' exists")
                return True
                
            except exceptions.CosmosResourceNotFoundError:
                logger.info(f"  Creating new container...")
                
                # Prepare container configuration
                container_properties = {
                    "id": container_name,
                    "partitionKey": {
                        "paths": [partition_key],
                        "kind": "Hash"
                    },
                    "indexingPolicy": {
                        "indexingMode": "consistent",
                        "automatic": True,
                        "includedPaths": [
                            {"path": "/*"}
                        ],
                        "excludedPaths": [
                            {"path": "/\"_etag\"/?"}
                        ]
                    }
                }
                
                # Add TTL if specified
                if ttl is not None:
                    container_properties["defaultTtl"] = ttl
                
                # Create container
                self.database.create_container(
                    **container_properties
                )
                
                logger.info(f"✓ Container '{container_name}' created")
                logger.info(f"  - Partition key: {partition_key}")
                if ttl:
                    logger.info(f"  - Default TTL: {ttl} seconds ({ttl // 86400} days)")
                else:
                    logger.info(f"  - Default TTL: None (never expires)")
                
                return True
                
        except Exception as e:
            logger.error(f"✗ Failed to create container '{container_name}': {e}")
            return False

    def initialize_all(self) -> bool:
        """
        Initialize complete database schema
        
        Returns:
            True if all steps successful
        """
        logger.info("\n" + "="*60)
        logger.info("KraftdIntel Cosmos DB Initialization")
        logger.info("="*60)
        
        # Step 1: Connect
        if not self.connect():
            return False
        
        # Step 2: Create database
        if not self.create_database("KraftdIntel"):
            return False
        
        # Step 3: Create containers
        containers = [
            {
                "name": "events",
                "partition_key": "/user_id",
                "ttl": 180 * 86400,  # 180 days
                "description": "Stores price, alert, anomaly, signal, and trend events"
            },
            {
                "name": "dashboards",
                "partition_key": "/user_id",
                "ttl": None,  # Never expires
                "description": "Stores user dashboard configurations and widget layouts"
            },
            {
                "name": "preferences",
                "partition_key": "/user_id",
                "ttl": None,  # Never expires
                "description": "Stores user alert preferences and settings"
            }
        ]
        
        logger.info("\nCreating containers...")
        all_successful = True
        
        for container_config in containers:
            logger.info(f"\n{container_config['name']}: {container_config['description']}")
            success = self.create_container(
                container_name=container_config['name'],
                partition_key=container_config['partition_key'],
                ttl=container_config['ttl']
            )
            all_successful = all_successful and success
        
        if all_successful:
            logger.info("\n" + "="*60)
            logger.info("✓ SUCCESS: Cosmos DB initialized completely")
            logger.info("="*60)
            logger.info("\nYou can now:")
            logger.info("1. Start the backend server")
            logger.info("2. Run end-to-end tests")
            logger.info("3. Proceed with frontend integration")
            return True
        else:
            logger.error("\n" + "="*60)
            logger.error("✗ FAILED: Some containers could not be created")
            logger.error("="*60)
            return False


def get_credentials(production: bool = False) -> tuple[str, str]:
    """
    Get Cosmos DB credentials from environment or defaults
    
    Args:
        production: If True, require Azure cloud credentials
        
    Returns:
        Tuple of (endpoint, key)
    """
    endpoint = os.getenv("COSMOS_ENDPOINT")
    key = os.getenv("COSMOS_KEY")
    
    if endpoint and key:
        logger.info("Using credentials from environment variables")
        return endpoint, key
    
    if production:
        logger.error("✗ Production mode requires COSMOS_ENDPOINT and COSMOS_KEY")
        logger.error("  Set environment variables and try again")
        sys.exit(1)
    
    # Default to local emulator
    logger.info("Using local Cosmos DB Emulator credentials")
    return (
        "https://localhost:8081/",
        "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVo+2xNqaC8h/RVi12NewNQYoNkVRZo0v6a7t1E=="
    )


def main():
    """Main entry point"""
    production = "--production" in sys.argv
    
    # Get credentials
    endpoint, key = get_credentials(production)
    
    # Initialize
    initializer = CosmosDBInitializer(endpoint, key)
    success = initializer.initialize_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
