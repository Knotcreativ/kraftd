# Expedited Deployment Plan - Cosmos DB Already Ready

**Status**: Cosmos DB account exists - **SKIPPING INFRASTRUCTURE SETUP**
**Timeline**: ~2-3 hours total (reduced from ~4 hours)
**Next Steps**: Configuration → Staging → Production

---

## 🚀 Deployment Timeline (ACCELERATED)

### Phase 1: Cosmos DB Configuration (15 min) ⏱️
**Status**: Can be done in parallel with application preparation

```
☐ Create database 'kraftd_audit'
☐ Create container 'audit_events'
☐ Set partition key: /tenant_id
☐ Configure TTL: 2555 days
☐ Create 3 composite indexes
☐ Get connection string
☐ Set environment variables
☐ Test connection (5 min)
```

**Reference**: [COSMOS_DB_CONFIGURATION.md](COSMOS_DB_CONFIGURATION.md)

### Phase 2: Application Configuration (10 min) ⏱️
**Status**: Prepare application for deployment

```
☐ Set COSMOS_DB_ENDPOINT in environment
☐ Set COSMOS_DB_KEY in environment
☐ Set COSMOS_DB_NAME: kraftd_audit
☐ Set COSMOS_DB_AUDIT_CONTAINER: audit_events
☐ Set COSMOS_DB_THROUGHPUT: 400
☐ Set COSMOS_DB_TTL_DAYS: 2555
☐ Verify all environment variables
```

### Phase 3: Staging Deployment (30 min) ⏱️
**Status**: Deploy and validate in staging

```
☐ Deploy v1.0.0 to staging environment
☐ Verify application starts successfully
☐ Run smoke tests (all 11 endpoints)
☐ Verify Cosmos DB connection
☐ Test audit logging (write test event)
☐ Monitor logs for errors
☐ Get staging validation pass
```

### Phase 4: Production Deployment (20 min) ⏱️
**Status**: Deploy to production

```
☐ Create backup of any existing data
☐ Deploy v1.0.0 to production
☐ Verify application starts
☐ Test critical endpoints
☐ Enable production monitoring
☐ Verify audit logging working
```

### Phase 5: 24-Hour Monitoring (continuous) ⏱️
**Status**: Watch system during first 24 hours

```
☐ Monitor error rate (target: <0.1%)
☐ Monitor latency (target: <1000ms)
☐ Monitor Cosmos DB RU/s usage
☐ Monitor audit events being logged
☐ Check for security alerts
☐ Validate compliance reporting
```

**Total Time**: ~1-2 hours setup + ~2 hours deployment + 24 hours monitoring

---

## 🎯 Quick Setup Instructions

### 1. Configure Cosmos DB (15 minutes)

```powershell
# Use Azure Portal or CLI to:
# 1. Create database: kraftd_audit
# 2. Create container: audit_events (partition key: /tenant_id)
# 3. Set TTL: 2555 days
# 4. Create 3 composite indexes
# 5. Get connection string

# See COSMOS_DB_CONFIGURATION.md for detailed steps
```

### 2. Get Connection Details

```powershell
# Get from Azure Portal: Keys section
# Or use CLI:
az cosmosdb keys list --resource-group <your-rg> --name <your-account> --type connection-strings
```

### 3. Set Environment Variables

```powershell
# For local testing:
$env:COSMOS_DB_ENDPOINT = "https://your-account.documents.azure.com:443/"
$env:COSMOS_DB_KEY = "your-key-here"
$env:COSMOS_DB_NAME = "kraftd_audit"
$env:COSMOS_DB_AUDIT_CONTAINER = "audit_events"
$env:COSMOS_DB_THROUGHPUT = "400"
$env:COSMOS_DB_TTL_DAYS = "2555"

# For production deployment, set in:
# - App Service Configuration
# - Key Vault
# - Docker environment
# - Kubernetes secrets
```

### 4. Test Connection

```powershell
# Create test_cosmos_connection.py (see COSMOS_DB_CONFIGURATION.md)
pip install azure-cosmos
python test_cosmos_connection.py

# Expected: ✅ All Cosmos DB connection tests passed!
```

### 5. Deploy Application

```powershell
# Option A: Local deployment
cd c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel
pip install -r requirements.txt
python -m backend.main

# Option B: Docker deployment
docker build -t kraftdintel:v1.0.0 .
docker run -e COSMOS_DB_ENDPOINT=... -e COSMOS_DB_KEY=... kraftdintel:v1.0.0

# Option C: Azure App Service
az webapp deployment source config-zip --resource-group <rg> --name <app-name> --src deployment.zip
```

### 6. Verify Deployment

```powershell
# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/admin/logs/authorization

# Check logs
# Should see: "Successfully initialized Cosmos DB backend"
# Or fallback message if Cosmos DB not ready

# Monitor in Azure Portal:
# Cosmos DB → Metrics → see audit events being created
```

---

## 📋 Pre-Deployment Checklist

### Code Ready ✅
- [x] All code compiles (0 errors)
- [x] All tests pass (100%)
- [x] Git tag v1.0.0 created
- [x] Release notes prepared

### Infrastructure Ready ✅
- [x] Cosmos DB account exists
- [ ] Database `kraftd_audit` ready
- [ ] Container `audit_events` ready
- [ ] TTL configured
- [ ] Indexes created
- [ ] Connection string available
- [ ] Environment variables set

### Application Ready
- [x] Configuration prepared
- [ ] Environment variables set
- [ ] Cosmos DB connection tested
- [ ] Ready for staging deployment

### Documentation Ready ✅
- [x] Deployment guide (TASK8_PHASE6_DEPLOYMENT_READINESS.md)
- [x] Cosmos DB setup (COSMOS_DB_CONFIGURATION.md)
- [x] Testing guide (TASK8_PHASE6_TESTING_GUIDE.md)
- [x] Master index (TASK8_MASTER_INDEX.md)

---

## 🔄 Deployment Decision Tree

```
START: Cosmos DB Account Ready ✅
│
├─→ [Configure Cosmos DB] (15 min)
│   ├─→ Database: kraftd_audit
│   ├─→ Container: audit_events
│   ├─→ Partition Key: /tenant_id
│   ├─→ TTL: 2555 days
│   └─→ Indexes: 3 composite indexes
│
├─→ [Test Connection] (5 min)
│   └─→ Run test_cosmos_connection.py
│       └─→ ✅ PASS → Continue
│       └─→ ❌ FAIL → Fix & retry
│
├─→ [Deploy to Staging] (30 min)
│   ├─→ Deploy v1.0.0
│   ├─→ Run smoke tests
│   └─→ ✅ PASS → Continue
│       └─→ ❌ FAIL → Debug & retry
│
├─→ [Deploy to Production] (20 min)
│   ├─→ Deploy v1.0.0
│   ├─→ Verify endpoints
│   └─→ Enable monitoring
│
└─→ [24-Hour Monitoring] (continuous)
    ├─→ Watch error rates
    ├─→ Monitor RU/s usage
    ├─→ Check audit logs
    └─→ Validate compliance
```

---

## ⚡ Quick Commands Reference

### Get Cosmos DB Details
```powershell
# Connection string
az cosmosdb keys list --resource-group <rg> --name <account> --type connection-strings

# Endpoint
az cosmosdb show --resource-group <rg> --name <account> --query documentEndpoint

# Keys
az cosmosdb keys list --resource-group <rg> --name <account> --type keys
```

### Create Database & Container
```powershell
# Database
az cosmosdb database create --resource-group <rg> --account-name <account> --name kraftd_audit

# Container
az cosmosdb collection create \
  --resource-group <rg> \
  --account-name <account> \
  --database-name kraftd_audit \
  --name audit_events \
  --partition-key-path /tenant_id \
  --default-ttl 221280000
```

### Test Connection
```powershell
pip install azure-cosmos
python test_cosmos_connection.py
```

### Deploy Application
```powershell
# Staging
python -m backend.main
# or
docker run -e COSMOS_DB_ENDPOINT=... -e COSMOS_DB_KEY=... app:v1.0.0

# Production
az webapp deployment source config-zip --resource-group <rg> --name <app> --src app.zip
```

---

## 📊 Expected Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Cosmos DB Config | 15 min | Can start now |
| Connection Test | 5 min | Follow configuration |
| App Configuration | 10 min | In parallel |
| Staging Deployment | 30 min | After config complete |
| Staging Testing | 30 min | After deployment |
| Production Deploy | 20 min | After staging pass |
| 24h Monitoring | Continuous | Post-deployment |
| **Total Setup** | **~1.5 hours** | |
| **Total Deployment** | **~2.5 hours** | |
| **Total Project** | **~4 hours** | |

---

## 🎯 Success Criteria

### Configuration Phase ✅
- Database created
- Container created
- TTL configured
- Indexes created
- Connection successful

### Staging Phase ✅
- Application starts
- All endpoints responsive
- Cosmos DB connected
- Audit logging working
- No critical errors

### Production Phase ✅
- Application running
- Audit events logged
- Cosmos DB healthy
- Monitoring active
- Team notified

---

## 📞 Next Steps

1. **Right Now**: Configure Cosmos DB (15 min)
   - Follow [COSMOS_DB_CONFIGURATION.md](COSMOS_DB_CONFIGURATION.md)

2. **Immediately After**: Set Environment Variables (5 min)
   - COSMOS_DB_ENDPOINT
   - COSMOS_DB_KEY
   - Other 4 variables

3. **Next 30 min**: Test Connection
   - Run test script
   - Verify success

4. **Next 60 min**: Deploy to Staging
   - Deploy v1.0.0
   - Run smoke tests

5. **Next 2 hours**: Deploy to Production
   - Deploy v1.0.0
   - Monitor 24 hours

---

**Status**: ✅ **READY TO BEGIN ACCELERATED DEPLOYMENT**

**Your Cosmos DB account is ready. Proceed with configuration and deployment using this guide.**
