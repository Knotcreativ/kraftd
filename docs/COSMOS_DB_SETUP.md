# Phase 10 Task 1: Cosmos DB Setup & Initialization

## Overview
This document guides you through setting up Azure Cosmos DB for the KraftdIntel platform. You have two options:

1. **Local Emulator** (Fast, Free, Development)
2. **Azure Cloud** (Production, Scalable)

## Option 1: Local Cosmos DB Emulator (Recommended for Development)

### Prerequisites
- Docker Desktop installed
- 4GB+ available memory
- Port 8081 and 10250-10255 available

### Step 1: Start Cosmos DB Emulator

```powershell
# Pull and run the emulator Docker image
docker run --rm -p 8081:8081 mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest

# Wait for startup (30-60 seconds)
# You'll see: "Started Cosmos DB Emulator"
```

### Step 2: Get Emulator Credentials

Once running, the emulator credentials are:

```
Endpoint: https://localhost:8081/
Key: <REDACTED — emulator key removed; use emulator or set COSMOS_KEY via env or Key Vault>
```

### Step 3: Create `.env` File

```powershell
cd c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel\backend
```

Create or update `.env`:

```
COSMOS_ENDPOINT=https://localhost:8081/
COSMOS_KEY=<REDACTED — do not commit secrets; use Key Vault or set locally>
ENVIRONMENT=development
```

### Step 4: Initialize Database & Containers

Run the initialization script:

```powershell
cd backend
.venv\Scripts\Activate.ps1
python scripts/init_cosmos.py
```

This will:
- Create database: `KraftdIntel`
- Create 3 containers:
  - `events` (partition key: `/user_id`)
  - `dashboards` (partition key: `/user_id`)
  - `preferences` (partition key: `/user_id`)
- Set TTL policies
- Configure indexes

### Step 5: Verify Connection

```powershell
python -c "
from services.cosmos_service import CosmosService
import asyncio

async def test():
    service = CosmosService(
        endpoint='https://localhost:8081/',
        key='C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVo+2xNqaC8h/RVi12NewNQYoNkVRZo0v6a7t1E=='
    )
    await service.initialize()
    print('✓ Cosmos DB connected!')

asyncio.run(test())
"
```

Expected output:
```
✓ Cosmos DB connected!
```

---

## Option 2: Azure Cloud Cosmos DB (Production)

### Prerequisites
- Azure subscription with active credits/payment method
- Azure CLI installed
- Owner or Contributor role on subscription

### Step 1: Create Azure Resource Group

```powershell
# Set variables
$resourceGroup = "KraftdIntel-RG"
$location = "eastus"
$cosmosAccountName = "kraftdintel-cosmos-$(Get-Random)"

# Create resource group
az group create `
  --name $resourceGroup `
  --location $location
```

### Step 2: Create Cosmos DB Account

```powershell
# Create Cosmos DB account (SQL API)
az cosmosdb create `
  --resource-group $resourceGroup `
  --name $cosmosAccountName `
  --locations regionName=$location failoverPriority=0 `
  --kind GlobalDocumentDB `
  --enable-free-tier true `
  --default-consistency-level "Session"

echo "✓ Cosmos DB account created: $cosmosAccountName"
```

### Step 3: Get Connection String

```powershell
# Retrieve primary connection string
$connString = az cosmosdb keys list-connection-strings `
  --resource-group $resourceGroup `
  --name $cosmosAccountName `
  --query "connectionStrings[0].connectionString" `
  --output tsv

echo "Connection String: $connString"
```

### Step 4: Update .env

```powershell
# Extract endpoint and key from connection string
# Format: AccountEndpoint=https://<account>.documents.azure.com:443/;AccountKey=<key>;

# For example:
$env:COSMOS_ENDPOINT="https://kraftdintel-cosmos-12345.documents.azure.com:443/"
$env:COSMOS_KEY="your-primary-key-here"
```

### Step 5: Initialize Database & Containers

```powershell
python scripts/init_cosmos.py --production
```

This will create the same containers with production-optimized settings.

---

## Container Schema

### events Container
```json
{
  "id": "uuid-string",
  "user_id": "user-uuid",
  "event_type": "price|alert|anomaly|signal|trend",
  "timestamp": "2024-01-18T10:30:00Z",
  "date": "2024-01-18",
  "data": {
    "value": 123.45,
    "change": 2.5,
    "source": "api|manual|system"
  },
  "ttl": 15552000,  // 180 days in seconds
  "_ts": 1705584600
}
```

**Partition Key:** `/user_id`  
**TTL:** Configurable per event type (default 180 days)  
**Index Policy:** All paths indexed

### dashboards Container
```json
{
  "id": "uuid-string",
  "user_id": "user-uuid",
  "name": "My Dashboard",
  "widgets": [
    {
      "id": "widget-1",
      "type": "chart|scorecard|table",
      "position": 0,
      "config": {}
    }
  ],
  "created_at": "2024-01-18T10:30:00Z",
  "updated_at": "2024-01-18T10:30:00Z"
}
```

**Partition Key:** `/user_id`  
**TTL:** Never expires (0)

### preferences Container
```json
{
  "id": "user-uuid",
  "user_id": "user-uuid",
  "alerts": {
    "low_severity_threshold": 10,
    "medium_severity_threshold": 50,
    "high_severity_threshold": 90
  },
  "notifications": {
    "email": true,
    "sms": false,
    "in_app": true,
    "quiet_hours": "22:00-08:00"
  },
  "display": {
    "theme": "auto",  // light, dark, auto
    "sidebar_collapsed": false,
    "animations_enabled": true
  },
  "updated_at": "2024-01-18T10:30:00Z"
}
```

**Partition Key:** `/user_id`  
**TTL:** Never expires (0)

---

## Cost Estimation

### Local Emulator
- **Cost:** FREE
- **Throughput:** Unlimited
- **Storage:** Limited by Docker resources
- **Best for:** Development, testing, learning

### Azure Free Tier (if eligible)
- **Cost:** FREE for first 12 months
- **Throughput:** 400 RU/s (free)
- **Storage:** 25 GB (free)
- **Region:** 1 primary region
- **Best for:** Small projects, startups

### Production Tier
- **Cost:** ~$0.25/hour for 1000 RU/s
- **Throughput:** Autoscale 1000-4000 RU/s
- **Storage:** Pay per GB used (~$1.25/GB/month)
- **Regions:** Multi-region for high availability
- **Best for:** Production, business-critical

---

## Environment Variables

### Development (Emulator)
```env
COSMOS_ENDPOINT=https://localhost:8081/
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVo+2xNqaC8h/RVi12NewNQYoNkVRZo0v6a7t1E==
ENVIRONMENT=development
COSMOS_MAX_RETRIES=3
COSMOS_TIMEOUT=30
```

### Production (Azure)
```env
COSMOS_ENDPOINT=https://<account>.documents.azure.com:443/
COSMOS_KEY=<your-primary-key>
ENVIRONMENT=production
COSMOS_MAX_RETRIES=5
COSMOS_TIMEOUT=60
```

---

## Verification Steps

### 1. Test Backend Connection

```powershell
# Start backend
cd backend
.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 127.0.0.1 --port 8000

# In another terminal, test health endpoint
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/health" | ConvertFrom-Json | ConvertTo-Json
```

Expected output:
```json
{
  "status": "healthy",
  "cosmos_db": "connected",
  "timestamp": "2024-01-18T10:30:00Z"
}
```

### 2. Test Event Storage

```powershell
# Create test event
$event = @{
  "user_id" = "test-user-1"
  "event_type" = "price"
  "data" = @{
    "value" = 123.45
    "change" = 2.5
  }
}

Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/events" `
  -Method POST `
  -Headers @{ "Authorization" = "Bearer <your-token>" } `
  -Body ($event | ConvertTo-Json) `
  -ContentType "application/json"
```

### 3. Test Event Retrieval

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/events?user_id=test-user-1" `
  -Headers @{ "Authorization" = "Bearer <your-token>" } | ConvertFrom-Json
```

---

## Troubleshooting

### Emulator won't start
```powershell
# Check if port 8081 is in use
netstat -ano | findstr :8081

# If in use, kill the process
taskkill /PID <PID> /F

# Restart emulator
docker run --rm -p 8081:8081 mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest
```

### Connection timeout
- Emulator: Check Docker is running and port 8081 is accessible
- Azure: Check network connectivity and firewall rules
- Check `.env` file has correct endpoint and key

### Container not found
```powershell
# Re-run initialization script
python scripts/init_cosmos.py
```

### Rate limiting (429 errors)
- Increase RU/s in Azure portal
- Implement exponential backoff (already in code)
- Batch operations where possible

---

## Next Steps

Once Cosmos DB is configured and verified:

1. ✅ **Task 1:** Cosmos DB Setup (IN PROGRESS)
2. **Task 2:** Backend Integration (EventStorageService)
3. **Task 3:** Frontend API Integration
4. **Task 4:** Real-time Updates & Sync
5. **Task 5:** Performance Optimization
6. **Task 6:** Security Hardening
7. **Task 7:** Azure Static Web App Setup
8. **Task 8:** CI/CD Pipeline
9. **Task 9:** End-to-End Testing
10. **Task 10:** Production Deployment

---

## References

- [Azure Cosmos DB Python SDK](https://learn.microsoft.com/en-us/azure/cosmos-db/sql/quickstart-python)
- [Cosmos DB Best Practices](https://learn.microsoft.com/en-us/azure/cosmos-db/best-practice-python)
- [Local Emulator Setup](https://learn.microsoft.com/en-us/azure/cosmos-db/local-emulator)
- [Partition Key Design](https://learn.microsoft.com/en-us/azure/cosmos-db/partitioning-overview)

