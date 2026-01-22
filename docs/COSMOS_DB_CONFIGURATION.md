# Cosmos DB Configuration for Production Deployment

**Status**: Existing Cosmos DB account available
**Task**: Configure existing account for KraftdIntel Task 8
**Expected Duration**: 15-20 minutes

---

## Step 1: Get Cosmos DB Connection Details

### Using Azure Portal

1. **Navigate to your Cosmos DB account**
   - Go to portal.azure.com
   - Find your Cosmos DB account

2. **Get Connection String**
   - Click "Keys" in left menu
   - Copy **Primary Connection String**
   - Format: `AccountEndpoint=https://xxx.documents.azure.com:443/;AccountKey=xxx==;`

3. **Extract Details**
   From the connection string, extract:
   - **COSMOS_DB_ENDPOINT**: `https://xxx.documents.azure.com:443/`
   - **COSMOS_DB_KEY**: The key portion (after `AccountKey=`)

### Using Azure CLI

```powershell
# Get connection string
az cosmosdb keys list --resource-group <your-rg> --name <your-account> --type connection-strings

# Get endpoint
az cosmosdb show --resource-group <your-rg> --name <your-account> --query documentEndpoint

# Get key
az cosmosdb keys list --resource-group <your-rg> --name <your-account> --type keys
```

---

## Step 2: Create Database & Container

### Option A: Using Azure Portal

1. **Create Database**
   - In Cosmos DB account, click "Data Explorer"
   - Click "New Database"
   - Name: `kraftd_audit`
   - Throughput: 400 RU/s
   - Click "OK"

2. **Create Container**
   - In new database, click "New Container"
   - Container ID: `audit_events`
   - Partition key: `/tenant_id`
   - Click "OK"

3. **Configure TTL**
   - Select container "audit_events"
   - Click "Scale & Settings"
   - Enable "Time to Live"
   - Default TTL: 221,280,000 (2555 days in seconds)
   - Click "Save"

### Option B: Using Azure CLI

```powershell
# Create database
az cosmosdb database create \
  --resource-group <your-rg> \
  --account-name <your-account> \
  --name kraftd_audit

# Create container with TTL
az cosmosdb collection create \
  --resource-group <your-rg> \
  --account-name <your-account> \
  --database-name kraftd_audit \
  --name audit_events \
  --partition-key-path /tenant_id \
  --default-ttl 221280000
```

---

## Step 3: Create Composite Indexes

### Using Azure Portal

1. **Navigate to Container**
   - Data Explorer → kraftd_audit → audit_events

2. **Click "Scale & Settings"**

3. **Go to "Indexing Policy"**

4. **Add Composite Indexes** (click "Add new index")

   Index 1:
   ```
   Path: /tenant_id, Order: Ascending
   Path: /timestamp, Order: Descending
   ```

   Index 2:
   ```
   Path: /tenant_id, Order: Ascending
   Path: /event_type, Order: Ascending
   ```

   Index 3:
   ```
   Path: /tenant_id, Order: Ascending
   Path: /user_email, Order: Ascending
   ```

5. **Click "Save"**

### Using Azure CLI (JSON Policy)

```powershell
# Create index policy file (indexing-policy.json):
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    {
      "path": "/*"
    }
  ],
  "excludedPaths": [
    {
      "path": "/\"_etag\"/?",
    }
  ],
  "compositeIndexes": [
    [
      {
        "path": "/tenant_id",
        "order": "ascending"
      },
      {
        "path": "/timestamp",
        "order": "descending"
      }
    ],
    [
      {
        "path": "/tenant_id",
        "order": "ascending"
      },
      {
        "path": "/event_type",
        "order": "ascending"
      }
    ],
    [
      {
        "path": "/tenant_id",
        "order": "ascending"
      },
      {
        "path": "/user_email",
        "order": "ascending"
      }
    ]
  ]
}

# Apply policy
az cosmosdb collection update \
  --resource-group <your-rg> \
  --account-name <your-account> \
  --database-name kraftd_audit \
  --name audit_events \
  --indexing-policy @indexing-policy.json
```

---

## Step 4: Set Environment Variables

### For Local Development

Create `.env` file in project root:
```
COSMOS_DB_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_DB_KEY=your-primary-key-here
COSMOS_DB_NAME=kraftd_audit
COSMOS_DB_AUDIT_CONTAINER=audit_events
COSMOS_DB_THROUGHPUT=400
COSMOS_DB_TTL_DAYS=2555
```

### For Azure App Service

1. **Go to App Service**
2. **Click "Configuration"**
3. **Add new application settings:**

| Key | Value |
|-----|-------|
| `COSMOS_DB_ENDPOINT` | `https://your-account.documents.azure.com:443/` |
| `COSMOS_DB_KEY` | Your primary key |
| `COSMOS_DB_NAME` | `kraftd_audit` |
| `COSMOS_DB_AUDIT_CONTAINER` | `audit_events` |
| `COSMOS_DB_THROUGHPUT` | `400` |
| `COSMOS_DB_TTL_DAYS` | `2555` |

4. **Click "Save"**

### For Docker/Container

Set environment variables when running:
```powershell
docker run \
  -e COSMOS_DB_ENDPOINT=https://your-account.documents.azure.com:443/ \
  -e COSMOS_DB_KEY=your-key \
  -e COSMOS_DB_NAME=kraftd_audit \
  -e COSMOS_DB_AUDIT_CONTAINER=audit_events \
  -e COSMOS_DB_THROUGHPUT=400 \
  -e COSMOS_DB_TTL_DAYS=2555 \
  your-image:latest
```

---

## Step 5: Test Connection

### Quick Test Script

Create `test_cosmos_connection.py`:

```python
import os
from azure.cosmos import CosmosClient

def test_connection():
    """Test Cosmos DB connection"""
    
    endpoint = os.getenv("COSMOS_DB_ENDPOINT")
    key = os.getenv("COSMOS_DB_KEY")
    db_name = os.getenv("COSMOS_DB_NAME", "kraftd_audit")
    container_name = os.getenv("COSMOS_DB_AUDIT_CONTAINER", "audit_events")
    
    try:
        print("Testing Cosmos DB connection...")
        
        # Create client
        client = CosmosClient(endpoint, key)
        
        # Get database
        db = client.get_database_client(db_name)
        print(f"✅ Connected to database: {db_name}")
        
        # Get container
        container = db.get_container_client(container_name)
        print(f"✅ Accessed container: {container_name}")
        
        # Query container
        query = "SELECT VALUE COUNT(1) FROM c"
        result = list(container.query_items(query))
        count = result[0] if result else 0
        print(f"✅ Container has {count} items")
        
        # Test write
        test_item = {
            "id": "test-connection",
            "tenant_id": "test-tenant",
            "event_type": "test",
            "timestamp": "2026-01-18T15:00:00Z"
        }
        
        container.upsert_item(test_item)
        print("✅ Successfully wrote test item")
        
        # Read it back
        read_item = container.read_item("test-connection", "test-tenant")
        print("✅ Successfully read test item")
        
        # Clean up
        container.delete_item("test-connection", "test-tenant")
        print("✅ Cleaned up test item")
        
        print("\n✅ All Cosmos DB connection tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
```

### Run Test

```powershell
# Install Azure Cosmos SDK
pip install azure-cosmos

# Set environment variables
$env:COSMOS_DB_ENDPOINT = "https://your-account.documents.azure.com:443/"
$env:COSMOS_DB_KEY = "your-key"
$env:COSMOS_DB_NAME = "kraftd_audit"
$env:COSMOS_DB_AUDIT_CONTAINER = "audit_events"

# Run test
python test_cosmos_connection.py
```

Expected output:
```
✅ Connected to database: kraftd_audit
✅ Accessed container: audit_events
✅ Container has 0 items
✅ Successfully wrote test item
✅ Successfully read test item
✅ Cleaned up test item

✅ All Cosmos DB connection tests passed!
```

---

## Step 6: Verify Configuration

### Check Database & Container

```powershell
# List databases
az cosmosdb database list \
  --resource-group <your-rg> \
  --account-name <your-account>

# Check container
az cosmosdb collection show \
  --resource-group <your-rg> \
  --account-name <your-account> \
  --database-name kraftd_audit \
  --name audit_events
```

### Verify Indexes

1. Go to Azure Portal
2. Navigate to your Cosmos DB account
3. Data Explorer → kraftd_audit → audit_events
4. Scale & Settings → Indexing Policy
5. Verify all 3 composite indexes are present

### Check Throughput & TTL

1. Data Explorer → audit_events
2. Scale & Settings tab
3. Verify:
   - Manual throughput: 400 RU/s (or your preferred setting)
   - TTL enabled: 2555 days (or preferred retention)

---

## Troubleshooting

### Connection String Issues

**Problem**: `Invalid connection string format`
- **Solution**: Ensure format is: `AccountEndpoint=https://xxx.documents.azure.com:443/;AccountKey=xxx==;`

### Authentication Failed

**Problem**: `Unauthorized: Invalid authorization token`
- **Solution**: Verify account key is correct in Azure Portal → Keys

### Container Not Found

**Problem**: `Resource not found`
- **Solution**: Verify database and container names match exactly (case-sensitive)

### TTL Not Working

**Problem**: Items not expiring after TTL date
- **Solution**: 
  1. TTL is in seconds (2555 days = 221,280,000 seconds)
  2. Items must have a `ttl` field or use default TTL
  3. Check indexing policy includes TTL field

### High RU/s Consumption

**Problem**: Cosmos DB running out of RU/s
- **Solution**: 
  1. Scale throughput in Portal (Scale & Settings)
  2. Enable autoscaling if heavy usage expected
  3. Optimize queries using composite indexes

---

## Quick Checklist

- [ ] Cosmos DB account exists and accessible
- [ ] Database `kraftd_audit` created
- [ ] Container `audit_events` created
- [ ] Partition key set to `/tenant_id`
- [ ] TTL policy configured (2555 days)
- [ ] 3 composite indexes created
- [ ] Connection string obtained
- [ ] Environment variables set
- [ ] Test connection passed
- [ ] Ready for application deployment

---

## Next Steps

1. **Set environment variables** in your deployment environment
2. **Run test script** to verify connection
3. **Deploy application** (see TASK8_PHASE6_DEPLOYMENT_READINESS.md)
4. **Monitor audit logs** in Azure Portal

---

**Status**: ✅ Configuration ready
**Next**: Deploy application to staging
