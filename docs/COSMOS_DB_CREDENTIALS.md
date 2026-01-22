# Your Cosmos DB Configuration Details

**Retrieved**: January 18, 2026
**Status**: ✅ Ready to use

---

## Your Cosmos DB Account Details

### Basic Information
```
Account Name:        kraftdintel-cosmos
Resource Group:      kraftdintel-rg
Location:            UAE North
Endpoint:            https://kraftdintel-cosmos.documents.azure.com:443/
```

### Connection Credentials

#### Primary Connection String (USE THIS ONE)
```
AccountEndpoint=https://kraftdintel-cosmos.documents.azure.com:443/;AccountKey=Dg7UBtSjwXlavOZII1Da8M2lBuQVNhgaRYDcFHyfKVCtGcGLUbU9S2crsGlTB08dGR7LToOeYA6vACDb794KDA==;
```

#### Primary Master Key (Account Key)
```
Dg7UBtSjwXlavOZII1Da8M2lBuQVNhgaRYDcFHyfKVCtGcGLUbU9S2crsGlTB08dGR7LToOeYA6vACDb794KDA==
```

---

## Environment Variables for Deployment

### Copy and paste these into your deployment environment:

```powershell
$env:COSMOS_DB_ENDPOINT = "https://kraftdintel-cosmos.documents.azure.com:443/"
$env:COSMOS_DB_KEY = "Dg7UBtSjwXlavOZII1Da8M2lBuQVNhgaRYDcFHyfKVCtGcGLUbU9S2crsGlTB08dGR7LToOeYA6vACDb794KDA=="
$env:COSMOS_DB_NAME = "kraftd_audit"
$env:COSMOS_DB_AUDIT_CONTAINER = "audit_events"
$env:COSMOS_DB_THROUGHPUT = "400"
$env:COSMOS_DB_TTL_DAYS = "2555"
```

### Or for .env file:
```
COSMOS_DB_ENDPOINT=https://kraftdintel-cosmos.documents.azure.com:443/
COSMOS_DB_KEY=Dg7UBtSjwXlavOZII1Da8M2lBuQVNhgaRYDcFHyfKVCtGcGLUbU9S2crsGlTB08dGR7LToOeYA6vACDb794KDA==
COSMOS_DB_NAME=kraftd_audit
COSMOS_DB_AUDIT_CONTAINER=audit_events
COSMOS_DB_THROUGHPUT=400
COSMOS_DB_TTL_DAYS=2555
```

### For Azure App Service:
| Setting | Value |
|---------|-------|
| COSMOS_DB_ENDPOINT | `https://kraftdintel-cosmos.documents.azure.com:443/` |
| COSMOS_DB_KEY | `Dg7UBtSjwXlavOZII1Da8M2lBuQVNhgaRYDcFHyfKVCtGcGLUbU9S2crsGlTB08dGR7LToOeYA6vACDb794KDA==` |
| COSMOS_DB_NAME | `kraftd_audit` |
| COSMOS_DB_AUDIT_CONTAINER | `audit_events` |
| COSMOS_DB_THROUGHPUT | `400` |
| COSMOS_DB_TTL_DAYS | `2555` |

### For Docker:
```bash
docker run \
  -e COSMOS_DB_ENDPOINT="https://kraftdintel-cosmos.documents.azure.com:443/" \
  -e COSMOS_DB_KEY="Dg7UBtSjwXlavOZII1Da8M2lBuQVNhgaRYDcFHyfKVCtGcGLUbU9S2crsGlTB08dGR7LToOeYA6vACDb794KDA==" \
  -e COSMOS_DB_NAME="kraftd_audit" \
  -e COSMOS_DB_AUDIT_CONTAINER="audit_events" \
  -e COSMOS_DB_THROUGHPUT="400" \
  -e COSMOS_DB_TTL_DAYS="2555" \
  kraftdintel:v1.0.0
```

---

## Next Steps

1. **Set these environment variables** in your deployment environment
2. **Create the database & container** (see below)
3. **Test the connection** with provided script
4. **Deploy the application**

---

## Create Database & Container

### Using Azure CLI

```powershell
# Create database
az cosmosdb database create \
  --resource-group kraftdintel-rg \
  --account-name kraftdintel-cosmos \
  --name kraftd_audit

# Create container with TTL
az cosmosdb collection create \
  --resource-group kraftdintel-rg \
  --account-name kraftdintel-cosmos \
  --database-name kraftd_audit \
  --name audit_events \
  --partition-key-path /tenant_id \
  --default-ttl 221280000 \
  --throughput 400
```

### Create Composite Indexes

```powershell
# Index policy
$indexPolicy = @{
  "indexingMode" = "consistent"
  "automatic" = $true
  "includedPaths" = @(
    @{ "path" = "/*" }
  )
  "excludedPaths" = @(
    @{ "path" = "/\"_etag\"\/?" }
  )
  "compositeIndexes" = @(
    @(
      @{ "path" = "/tenant_id"; "order" = "ascending" },
      @{ "path" = "/timestamp"; "order" = "descending" }
    ),
    @(
      @{ "path" = "/tenant_id"; "order" = "ascending" },
      @{ "path" = "/event_type"; "order" = "ascending" }
    ),
    @(
      @{ "path" = "/tenant_id"; "order" = "ascending" },
      @{ "path" = "/user_email"; "order" = "ascending" }
    )
  )
} | ConvertTo-Json -Depth 10 | Out-File -FilePath indexPolicy.json

# Apply policy
az cosmosdb collection update \
  --resource-group kraftdintel-rg \
  --account-name kraftdintel-cosmos \
  --database-name kraftd_audit \
  --name audit_events \
  --indexing-policy @indexPolicy.json
```

---

## Test Connection Script

Save as `test_cosmos_connection.py`:

```python
import os
from azure.cosmos import CosmosClient

endpoint = os.getenv("COSMOS_DB_ENDPOINT")
key = os.getenv("COSMOS_DB_KEY")
db_name = os.getenv("COSMOS_DB_NAME", "kraftd_audit")
container_name = os.getenv("COSMOS_DB_AUDIT_CONTAINER", "audit_events")

try:
    print("Testing Cosmos DB connection...")
    client = CosmosClient(endpoint, key)
    db = client.get_database_client(db_name)
    print(f"✅ Connected to database: {db_name}")
    
    container = db.get_container_client(container_name)
    print(f"✅ Accessed container: {container_name}")
    
    # Test write
    test_item = {
        "id": "test-connection",
        "tenant_id": "test-tenant",
        "event_type": "test",
        "timestamp": "2026-01-18T15:00:00Z"
    }
    container.upsert_item(test_item)
    print("✅ Successfully wrote test item")
    
    # Read back
    read_item = container.read_item("test-connection", "test-tenant")
    print("✅ Successfully read test item")
    
    # Cleanup
    container.delete_item("test-connection", "test-tenant")
    print("✅ Cleaned up test item")
    
    print("\n✅ All Cosmos DB connection tests passed!")
    
except Exception as e:
    print(f"❌ Connection test failed: {e}")
```

Run test:
```powershell
pip install azure-cosmos
python test_cosmos_connection.py
```

---

## Summary

✅ **Cosmos DB Account**: `kraftdintel-cosmos`
✅ **Region**: UAE North  
✅ **Endpoint**: `https://kraftdintel-cosmos.documents.azure.com:443/`
✅ **Primary Key**: Retrieved and ready to use
✅ **Connection String**: Retrieved and ready to use

**You're ready to proceed with deployment!**

---

**Next**: Follow the deployment checklist in IMMEDIATE_ACTION_CHECKLIST.md
