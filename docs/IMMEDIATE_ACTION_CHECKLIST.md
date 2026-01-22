# 🚀 DEPLOYMENT START - Immediate Action Items

**Status**: ✅ Cosmos DB account ready
**Timeline**: ~2-3 hours to production
**Start**: Now

---

## ✅ CHECKLIST: What to Do Right Now

### Phase 1: Get Cosmos DB Details (5 min)

```
☐ Go to Azure Portal
☐ Navigate to your Cosmos DB account
☐ Click "Keys" in left sidebar
☐ Copy connection string (full one)
☐ Note the endpoint URL
☐ Note the primary key
```

**What you'll have**:
```
COSMOS_DB_ENDPOINT = https://your-account.documents.azure.com:443/
COSMOS_DB_KEY = <long key string>
```

---

### Phase 2: Setup Cosmos DB Structure (15 min)

**Choose one method below:**

#### Option A: Using Azure Portal (easiest)
```
☐ In Cosmos DB account, click "Data Explorer"
☐ Click "New Database"
  ├─ Name: kraftd_audit
  ├─ Throughput: 400 RU/s
  └─ Click OK
☐ In new database, click "New Container"
  ├─ Container ID: audit_events
  ├─ Partition key: /tenant_id
  └─ Click OK
☐ Select container "audit_events"
☐ Click "Scale & Settings"
☐ Find "Time to Live" section
  ├─ Enable it
  ├─ Set to: 221280000 (2555 days in seconds)
  └─ Save
```

#### Option B: Using Azure CLI (faster if automated)
```powershell
# Create database
az cosmosdb database create \
  --resource-group <your-resource-group> \
  --account-name <your-account-name> \
  --name kraftd_audit

# Create container
az cosmosdb collection create \
  --resource-group <your-resource-group> \
  --account-name <your-account-name> \
  --database-name kraftd_audit \
  --name audit_events \
  --partition-key-path /tenant_id \
  --default-ttl 221280000 \
  --throughput 400
```

---

### Phase 3: Create Indexes (10 min)

**Go to Azure Portal Data Explorer:**

1. Select: `kraftd_audit` → `audit_events`
2. Click "Scale & Settings"
3. Click "Indexing Policy" tab
4. Click "Add Composite Index"

**Add these 3 indexes:**

```
Index 1:
  - First path: /tenant_id (Ascending)
  - Second path: /timestamp (Descending)
  
Index 2:
  - First path: /tenant_id (Ascending)
  - Second path: /event_type (Ascending)
  
Index 3:
  - First path: /tenant_id (Ascending)
  - Second path: /user_email (Ascending)
```

Click Save after adding all three.

---

### Phase 4: Set Environment Variables (5 min)

**For Local Testing:**
```powershell
# In PowerShell, run:
$env:COSMOS_DB_ENDPOINT = "https://your-account.documents.azure.com:443/"
$env:COSMOS_DB_KEY = "your-key-from-portal"
$env:COSMOS_DB_NAME = "kraftd_audit"
$env:COSMOS_DB_AUDIT_CONTAINER = "audit_events"
$env:COSMOS_DB_THROUGHPUT = "400"
$env:COSMOS_DB_TTL_DAYS = "2555"

# Or add to .env file in project root
```

**For Production (Azure App Service):**
1. Go to your App Service in Azure Portal
2. Click "Configuration"
3. Click "New application setting" for each:

| Setting | Value |
|---------|-------|
| COSMOS_DB_ENDPOINT | `https://your-account.documents.azure.com:443/` |
| COSMOS_DB_KEY | Your key from portal |
| COSMOS_DB_NAME | `kraftd_audit` |
| COSMOS_DB_AUDIT_CONTAINER | `audit_events` |
| COSMOS_DB_THROUGHPUT | `400` |
| COSMOS_DB_TTL_DAYS | `2555` |

4. Click Save

---

### Phase 5: Test Connection (5 min)

**Create test file: `test_cosmos.py`**
```python
import os
from azure.cosmos import CosmosClient

# Get from environment
endpoint = os.getenv("COSMOS_DB_ENDPOINT")
key = os.getenv("COSMOS_DB_KEY")

# Test
try:
    client = CosmosClient(endpoint, key)
    db = client.get_database_client("kraftd_audit")
    container = db.get_container_client("audit_events")
    
    # Write test
    test_item = {
        "id": "test-123",
        "tenant_id": "test-tenant",
        "event_type": "test",
        "timestamp": "2026-01-18T15:00:00Z"
    }
    container.upsert_item(test_item)
    
    # Read test
    result = container.read_item("test-123", "test-tenant")
    
    # Cleanup
    container.delete_item("test-123", "test-tenant")
    
    print("✅ Cosmos DB connection test PASSED!")
    
except Exception as e:
    print(f"❌ Cosmos DB connection test FAILED: {e}")
```

**Run test:**
```powershell
pip install azure-cosmos
python test_cosmos.py
```

**Expected output:**
```
✅ Cosmos DB connection test PASSED!
```

---

### Phase 6: Deploy Application (30 min)

#### Option A: Local Deployment (for testing)
```powershell
cd c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel
pip install -r requirements.txt
python -m backend.main

# Then test endpoints:
curl http://localhost:8000/health
```

#### Option B: Azure App Service
```powershell
# Deploy code
az webapp deployment source config-zip \
  --resource-group <your-rg> \
  --name <your-app-service> \
  --src deployment.zip

# Monitor deployment in portal
```

#### Option C: Docker
```powershell
docker build -t kraftdintel:v1.0.0 .
docker run -p 8000:8000 \
  -e COSMOS_DB_ENDPOINT="https://your-account.documents.azure.com:443/" \
  -e COSMOS_DB_KEY="your-key" \
  -e COSMOS_DB_NAME="kraftd_audit" \
  -e COSMOS_DB_AUDIT_CONTAINER="audit_events" \
  -e COSMOS_DB_THROUGHPUT="400" \
  -e COSMOS_DB_TTL_DAYS="2555" \
  kraftdintel:v1.0.0
```

---

### Phase 7: Verify Deployment (10 min)

```powershell
# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/profile
curl http://localhost:8000/admin/logs/authorization

# Check logs for:
# "Successfully initialized Cosmos DB backend"
# OR "Falling back to in-memory storage" (if Cosmos DB not ready)

# In Azure Portal:
# Go to Cosmos DB → Collections → audit_events
# Should see audit events being created (if you tested endpoints)
```

---

### Phase 8: Monitor (24 hours)

```
☐ Monitor error rate (should be <0.1%)
☐ Monitor Cosmos DB RU/s usage
☐ Check audit logs are being created
☐ Verify no critical errors in logs
☐ Check compliance reports generate correctly
```

---

## 📊 Timeline

| Task | Time | Status |
|------|------|--------|
| Get Cosmos DB details | 5 min | Do now |
| Setup DB structure | 15 min | Do now |
| Create indexes | 10 min | Do now |
| Set env variables | 5 min | Do now |
| Test connection | 5 min | Do now |
| **Total Setup** | **~40 min** | |
| Deploy application | 30 min | After setup |
| Verify deployment | 10 min | After deploy |
| **Total to Production** | **~80 min** | |
| 24h monitoring | Continuous | After deploy |

**Expected finish time: ~1.5-2 hours from now**

---

## 📞 References

- **Cosmos DB Setup**: [COSMOS_DB_CONFIGURATION.md](COSMOS_DB_CONFIGURATION.md)
- **Full Deployment Guide**: [TASK8_PHASE6_DEPLOYMENT_READINESS.md](TASK8_PHASE6_DEPLOYMENT_READINESS.md)
- **Accelerated Plan**: [ACCELERATED_DEPLOYMENT_PLAN.md](ACCELERATED_DEPLOYMENT_PLAN.md)
- **Master Index**: [TASK8_MASTER_INDEX.md](TASK8_MASTER_INDEX.md)

---

## ✅ You're Ready!

**Everything is prepared. Just follow the checklist above and you'll be in production in ~2 hours.**

The system is production-ready. Your Cosmos DB account is ready. Let's deploy! 🚀
