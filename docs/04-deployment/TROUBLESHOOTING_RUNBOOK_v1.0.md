# Troubleshooting Runbook

**Version:** 1.0  
**Status:** APPROVED  
**Severity Levels:** P0=Critical, P1=High, P2=Medium, P3=Low  
**Last Updated:** 2026-01-17

---

## Common Issues & Solutions

### Frontend Issues

#### Issue: "Blank white page" or "Cannot read property of undefined"

**Severity:** P1 (High)
**Likely Cause:** API not reachable, React initialization error

**Diagnostic Steps:**
1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Check Network tab - verify API calls
4. Check if backend is running (http://localhost:8000)

**Solution:**
```bash
# 1. Verify API URL in .env
cat frontend/.env
# Should show: VITE_API_URL=http://localhost:8000

# 2. Restart frontend dev server
cd frontend
npm run dev

# 3. Clear browser cache
# - Ctrl+Shift+Delete (Windows/Linux)
# - Cmd+Shift+Delete (macOS)
# - or: Settings > Clear browsing data

# 4. If still broken, check backend
curl -i http://localhost:8000/health
# Should return 200 OK
```

**Related Documents:**
- [SETUP_GUIDE_v1.0.md](../03-development/SETUP_GUIDE_v1.0.md)

---

#### Issue: "404 Not Found" when clicking document link

**Severity:** P2 (Medium)
**Likely Cause:** Document deleted, incorrect ID format

**Diagnostic Steps:**
1. Check URL in browser address bar
2. Verify document ID format: `doc_abc123`
3. Check console for API error details

**Solution:**
```bash
# 1. Verify document exists in Cosmos DB
# Using MongoDB CLI:
mongosh "connection-string"
use kraftdintel
db.documents.findOne({ document_id: "doc_abc123" })

# 2. If not found, document was deleted
# Check soft delete recovery (30-day window)
db.documents.find({ 
  document_id: "doc_abc123",
  status: "deleted"
})

# 3. Check API logs for details
docker logs <container-id>
```

---

#### Issue: "CORS error" - "Access to XMLHttpRequest blocked"

**Severity:** P2 (Medium)
**Likely Cause:** Frontend URL not in CORS whitelist

**Diagnostic Steps:**
1. Check console error - shows which origin is blocked
2. Verify frontend URL matches CORS configuration

**Solution:**
```python
# In backend/middleware.py
# Check CORS configuration:
allow_origins = [
    "https://jolly-coast-03a4f4d03.4.azurestaticapps.net",
    "http://localhost:5173"  # For local dev
]

# Update if needed and restart backend
```

---

#### Issue: "File upload stuck" or "Upload progress frozen"

**Severity:** P2 (Medium)
**Likely Cause:** Network timeout, file too large

**Diagnostic Steps:**
1. Check Network tab - see upload size
2. Check file size: should be < 5 MB
3. Look for timeout errors in console

**Solution:**
```bash
# 1. Check file size
ls -lh your-file.pdf
# Should be < 5MB

# 2. Try uploading smaller test file
# Use: test_data/RFQ_Sample.pdf

# 3. Check network timeout in .env
VITE_API_TIMEOUT=30000  # 30 seconds

# 4. Verify backend is accepting uploads
curl -X POST http://localhost:8000/health
# Should return 200
```

---

### Backend Issues

#### Issue: "Module not found" or "ImportError: No module named..."

**Severity:** P1 (High)
**Likely Cause:** Missing dependencies, wrong Python environment

**Diagnostic Steps:**
1. Check if virtual environment activated
2. Verify requirements installed
3. Check Python version (3.13+)

**Solution:**
```bash
# 1. Activate virtual environment
cd backend
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\Activate.ps1  # Windows

# 2. Check Python version
python --version
# Should output: Python 3.13.x

# 3. Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# 4. Verify installation
python -c "import fastapi; print(fastapi.__version__)"
# Should output version without error
```

---

#### Issue: "Connection refused" when connecting to Cosmos DB

**Severity:** P1 (Critical)
**Likely Cause:** Connection string invalid, database down

**Diagnostic Steps:**
1. Check connection string format
2. Verify network connectivity
3. Check if database is running

**Solution:**
```bash
# 1. Verify connection string in .env
grep COSMOS_CONNECTION_STRING backend/.env

# 2. Test connection with MongoDB CLI
mongosh "mongodb+srv://user:pass@cluster.mongo.cosmos.azure.com:10255"

# 3. Check Azure portal
# - Go to Cosmos DB resource
# - Verify "Status" = "Running"
# - Check "Firewall" settings

# 4. For local emulator:
docker run -p 8081:8081 \
  -e AZURE_COSMOS_EMULATOR=true \
  mcr.microsoft.com/cosmosdb/emulator:latest

# 5. Update connection string
COSMOS_CONNECTION_STRING=mongodb://localhost:27017
```

**Related Documents:**
- [DATABASE_SCHEMA_v1.0.md](../02-architecture/DATABASE_SCHEMA_v1.0.md)

---

#### Issue: "Document extraction fails" with 400 or 500 error

**Severity:** P2 (Medium)
**Likely Cause:** Azure Document Intelligence error, invalid file

**Diagnostic Steps:**
1. Check backend logs for detailed error
2. Verify document uploaded correctly
3. Check Azure DI status

**Solution:**
```bash
# 1. Check backend logs
docker logs <backend-container-id> | grep extraction

# 2. Verify Azure Document Intelligence is configured
grep DOCUMENT_INTELLIGENCE backend/.env

# 3. Test extraction with curl
curl -X POST http://localhost:8000/api/v1/documents/123/extract \
  -H "Authorization: Bearer <token>"

# 4. Check Azure DI in Azure Portal
# - Go to Document Intelligence resource
# - Verify status = "Available"
# - Check quotas not exceeded

# 5. Verify file is valid PDF
file your-file.pdf
# Should output: PDF document, version 1.x
```

---

#### Issue: "JWT token invalid" or "401 Unauthorized"

**Severity:** P2 (Medium)
**Likely Cause:** Token expired, wrong secret, malformed token

**Diagnostic Steps:**
1. Check token expiration time
2. Verify JWT secret matches
3. Check token format

**Solution:**
```bash
# 1. Check JWT expiration setting
grep JWT_EXPIRATION backend/.env
# Default: 24 hours

# 2. Verify JWT secret in Key Vault
az keyvault secret show \
  --vault-name <vault-name> \
  --name JWT-SECRET-KEY

# 3. Re-login to get new token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass"}'

# 4. Check token structure (decode at jwt.io)
# Token should have header.payload.signature
```

---

#### Issue: "Rate limit exceeded" - 429 Too Many Requests

**Severity:** P3 (Low)
**Likely Cause:** Making too many requests too quickly

**Diagnostic Steps:**
1. Check X-RateLimit headers in response
2. Count requests in last minute
3. Check for retry loops

**Solution:**
```bash
# 1. Check rate limit headers
curl -i http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer <token>"
# Look for: X-RateLimit-Remaining

# 2. Implement backoff in client
# Wait for X-RateLimit-Reset seconds

# 3. To temporarily disable rate limiting (dev only)
# Edit backend/middleware.py and comment out rate limiter

# 4. Check for stuck retry loops
ps aux | grep python
# Look for multiple requests to same endpoint
```

---

### Database Issues

#### Issue: "Cosmos DB quota exceeded" or slow queries

**Severity:** P2 (Medium)
**Likely Cause:** RU (Request Units) exceeded, missing indexes

**Diagnostic Steps:**
1. Check RU consumption in Azure Portal
2. Review slow query logs
3. Check indexes

**Solution:**
```bash
# 1. View RU consumption
# Azure Portal > Cosmos DB > Insights > Request Units

# 2. Identify expensive queries
mongosh <connection-string>
db.setProfilingLevel(1)  # Enable profiling
db.system.profile.find().limit(5).sort({ts: -1}).pretty()

# 3. Add missing indexes
db.documents.createIndex({ user_id: 1, created_at: -1 })
db.workflows.createIndex({ document_id: 1 })

# 4. Increase RU capacity
# Azure Portal > Cosmos DB > Scale > Edit
# Increase to 400+ RU/s for production
```

---

#### Issue: "Document not found" or empty results

**Severity:** P2 (Medium)
**Likely Cause:** Query filter incorrect, document in different partition

**Diagnostic Steps:**
1. Query directly with MongoDB CLI
2. Check partition key value
3. Verify data exists

**Solution:**
```bash
# 1. Query directly
mongosh <connection-string>
use kraftdintel
db.documents.find({ user_id: "usr_abc123" })

# 2. Check all databases/collections
db.listCollections()

# 3. If no results, data might be in wrong partition
# Verify partition key: user_id + company_id
db.documents.find({ user_id: "usr_abc123", company_id: "comp_123" })

# 4. Check document count by user
db.documents.aggregate([
  { $group: { _id: "$user_id", count: { $sum: 1 } } }
])
```

---

### Deployment Issues

#### Issue: "GitHub Actions build fails"

**Severity:** P1 (Critical)
**Likely Cause:** Missing secrets, build error

**Diagnostic Steps:**
1. Check GitHub Actions logs
2. Verify secrets are set
3. Check for compilation errors

**Solution:**
```bash
# 1. View GitHub Actions logs
# GitHub > Actions > Failed Workflow > See logs

# 2. Verify secrets are set
# GitHub > Settings > Secrets > Check all vars

# 3. Required secrets:
# - AZURE_STATIC_WEB_APPS_API_TOKEN
# - AZURE_CLIENT_ID
# - AZURE_TENANT_ID
# - AZURE_CLIENT_SECRET
# - AZURE_SUBSCRIPTION_ID
# - DOCKER_USERNAME
# - DOCKER_PASSWORD
#
# Note: `AZURE_CREDENTIALS` (full SP JSON) is deprecated — prefer the separate `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`, and `AZURE_SUBSCRIPTION_ID` secrets. See `docs/SECRETS_AZURE.md` for validation and troubleshooting steps.

# 4. Re-run workflow
# GitHub > Actions > Workflow > Re-run jobs

# 5. Check local build works first
cd frontend && npm run build
cd backend && docker build .
```

---

#### Issue: "Azure Container Apps not starting"

**Severity:** P1 (Critical)
**Likely Cause:** Image not found, environment variables missing

**Diagnostic Steps:**
1. Check container logs in Azure Portal
2. Verify image exists in registry
3. Check environment variables

**Solution:**
```bash
# 1. Check Azure Container Apps logs
az containerapp logs show \
  --name kraftdintel-backend \
  --resource-group <rg> \
  --follow

# 2. Verify container image exists
az acr repository list --name <registry>

# 3. Check environment variables
az containerapp show \
  --name kraftdintel-backend \
  --resource-group <rg>

# 4. Redeploy container
az containerapp update \
  --name kraftdintel-backend \
  --resource-group <rg> \
  --image <image:tag>

# 5. Check Key Vault permissions
az keyvault show-deleted \
  --name <vault-name>
```

---

## Performance Issues

### Issue: "Slow API response" or "Dashboard takes 10+ seconds to load"

**Severity:** P2 (Medium)
**Likely Cause:** Slow database query, network latency

**Diagnostic Steps:**
1. Check Network tab for slow requests
2. Check database query performance
3. Check backend logs for slow endpoints

**Solution:**
```bash
# 1. Identify slow endpoint
# Browser DevTools > Network > Sort by Duration

# 2. Add backend logging
# backend/main.py
import logging
logging.basicConfig(level=logging.DEBUG)

# 3. Check database indexes exist
mongosh <connection-string>
db.documents.getIndexes()

# 4. Enable caching for frequent queries
# backend/services/document_service.py
@cache(ttl=300)  # 5 minute cache
async def get_documents(user_id):
    ...

# 5. Enable compression
# backend/main.py
from fastapi.middleware.gzip import GZIPMiddleware
app.add_middleware(GZIPMiddleware, minimum_size=1000)
```

---

## Monitoring & Alerting

### Checking System Health

```bash
# Check all services running
# Frontend
curl -i http://localhost:5173
# Should return HTML page (200)

# Backend
curl -i http://localhost:8000/health
# Should return { "status": "healthy" } (200)

# Database
mongosh <connection-string> --eval "db.adminCommand('ping')"
# Should return { ok: 1 }
```

### Viewing Logs

```bash
# Frontend logs (dev console)
Browser > F12 > Console tab

# Backend logs (Docker)
docker logs <container-id>
docker logs <container-id> --follow

# Azure logs (Production)
az container logs --resource-group <rg> --name <container>
```

---

## Escalation Path

**For P0 (Critical) Issues:**
1. Check status page: https://status.azure.com
2. Alert on-call engineer
3. Check recent deployments (might be cause)
4. Prepare rollback if needed
5. Post-incident review within 24 hours

**For P1 (High) Issues:**
1. Investigate within 1 hour
2. Document findings
3. Test fix in dev first
4. Deploy fix during business hours
5. Monitor for 1 hour after fix

---

**Reference:** `/docs/04-deployment/TROUBLESHOOTING_RUNBOOK_v1.0.md`
