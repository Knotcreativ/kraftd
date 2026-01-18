# Deployment Guide

**Version:** 1.0  
**Status:** Production  
**Last Updated:** 2026-01-17

## Overview

KraftdIntel is deployed on Azure with:
- **Frontend:** Azure Static Web App (West Europe)
- **Backend:** Azure Container Apps (UAE North)  
- **Database:** Cosmos DB (MongoDB API)
- **Monitoring:** Application Insights + Log Analytics

---

## Current Deployment Status

✅ **LIVE AND OPERATIONAL**

| Component | Service | Region | Status |
|-----------|---------|--------|--------|
| Frontend | Static Web App | West Europe | ✅ Running |
| Backend | Container Apps | UAE North | ✅ Running |
| Database | Cosmos DB | Automatic | ✅ Running |
| Monitoring | App Insights | West Europe | ✅ Active |

**Frontend URL:** https://jolly-coast-03a4f4d03.4.azurestaticapps.net  
**Backend URL:** https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io  

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   PRODUCTION DEPLOYMENT                  │
└─────────────────────────────────────────────────────────┘

                      GitHub (Main Branch)
                              |
                              ↓
            ┌─────────────────────────────────┐
            │   GitHub Actions (CI/CD)       │
            │   - Build React (Vite)         │
            │   - Run Tests                  │
            │   - Deploy to SWA              │
            └─────────────────────────────────┘
                              |
                    ┌─────────┴────────┐
                    ↓                  ↓
        ┌──────────────────┐  ┌──────────────────┐
        │ Static Web App   │  │ Container Apps   │
        │ (Frontend React) │  │ (FastAPI Backend)│
        │ West Europe      │  │ UAE North        │
        │ LIVE ✅          │  │ RUNNING ✅       │
        └──────────────────┘  └──────────────────┘
                    |                  |
                    └─────────┬────────┘
                              ↓
                    ┌──────────────────┐
                    │   Cosmos DB      │
                    │ MongoDB API      │
                    │ OPERATIONAL ✅   │
                    └──────────────────┘
                              |
                              ↓
                    ┌──────────────────┐
                    │ App Insights     │
                    │ Log Analytics    │
                    │ MONITORING ✅    │
                    └──────────────────┘
```

---

## Frontend Deployment (Static Web App)

### How It Works

1. **Code Push** - Push to `main` branch on GitHub
2. **GitHub Actions** - Automatic build triggered
   - Install dependencies: `npm install`
   - Build: `npm run build` (outputs to `dist/`)
   - Deploy: Upload to Azure
3. **Static Web App** - Serves built files (4-5 minutes)

### Configuration

**File:** `.github/workflows/deploy-frontend.yml`

```yaml
- App location: frontend/
- Build output: dist/
- Environment variables:
  - VITE_API_URL: https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1
```

### Deployment Secret

**Name:** `AZURE_STATIC_WEB_APPS_API_TOKEN`  
**Status:** ✅ Configured  
**Value:** Available in Azure Portal → Static Web App → Deployment

### Check Status

```bash
# List deployments
az staticwebapp environment list \
  --name kraftdintel-web \
  --resource-group kraftdintel-rg

# Expected output: status = "Ready"
```

---

## Backend Deployment (Container Apps)

### How It Works

1. **Image Built** - Docker image created with FastAPI app
2. **Pushed to Registry** - Stored in Azure Container Registry
3. **Container Apps** - Pulls and runs latest image
4. **Auto-scaled** - Scales based on CPU/memory

### Configuration

**Resource Group:** `kraftdintel-rg`  
**Container App:** `kraftdintel-app`  
**Region:** UAE North  
**Image:** Pre-built Docker image  

### Access Backend

```bash
# Health check
curl https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/health

# API docs
https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/docs
```

### Check Status

```bash
# Get container app status
az containerapp show \
  --name kraftdintel-app \
  --resource-group kraftdintel-rg \
  --query "{provisioning: properties.provisioningState, status: properties.runningStatus}"

# Expected: provisioning = "Succeeded", status = "Running"
```

---

## Database Deployment (Cosmos DB)

### Configuration

**Resource:** `kraftdintel-cosmos`  
**API:** MongoDB API  
**Status:** ✅ Operational  

### Connection

**Connection String:** Set in environment variables  
**Database Name:** `kraftdintel`  
**Collections:** Auto-created by application

### Check Status

```bash
# Get Cosmos DB info
az cosmosdb show \
  --name kraftdintel-cosmos \
  --resource-group kraftdintel-rg \
  --query "{status: properties.publicNetworkAccess, endpoints: properties.documentEndpoint}"
```

---

## Environment Variables

### Static Web App (Frontend)

```bash
VITE_API_URL=https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1
```

**Set In:** Azure Portal → Static Web App → Configuration → Application settings

### Container Apps (Backend)

Environment variables are pre-configured. Backend can access:
- Connection strings
- API keys
- Azure credentials (via Managed Identity)

---

## Monitoring & Logs

### Application Insights

**Resource:** `workspace-kraftdintelrgc0kT`  
**Status:** ✅ Active  

View metrics:
```bash
# Open in browser
https://portal.azure.com
# Navigate: Application Insights → Your Instance → Performance
```

### Container App Logs

```bash
# View recent logs
az containerapp logs show \
  --name kraftdintel-app \
  --resource-group kraftdintel-rg \
  --container-name kraftdintel-app \
  --follow
```

### Static Web App Logs

Access via Azure Portal:
- **Build logs:** Static Web App → Builds
- **Runtime logs:** Application Insights → Logs

---

## Post-Deployment Checklist

After deployment, verify:

- [ ] **Frontend loads** - https://jolly-coast-03a4f4d03.4.azurestaticapps.net
- [ ] **API responds** - Check `/health` endpoint
- [ ] **Database connects** - Verify collections exist
- [ ] **Monitoring active** - Check Application Insights
- [ ] **Environment variables set** - All configs in place
- [ ] **CORS enabled** - Frontend can call backend
- [ ] **SSL certificates** - HTTPS working

---

## Rollback Procedure

### If Frontend Needs Rollback

```bash
# Check previous deployments
az staticwebapp environment list --name kraftdintel-web

# Redeploy specific build
az staticwebapp environment show \
  --name kraftdintel-web \
  --environment-name <previous-build-id>
```

### If Backend Needs Rollback

```bash
# Container Apps has auto-versioning
# Redeploy latest image:
az containerapp up \
  --name kraftdintel-app \
  --resource-group kraftdintel-rg \
  --image <previous-image-tag>
```

---

## Manual Redeployment

### Frontend Redeploy

```bash
# Trigger GitHub Actions manually
# Option 1: Push change to main branch (any change triggers build)
git push origin main

# Option 2: Manually trigger in GitHub
# Go to: GitHub → Actions → Workflow → Run workflow
```

### Backend Redeploy

```bash
# Rebuild and push Docker image
docker build -t kraftdintel-backend .
docker tag kraftdintel-backend:latest kraftdintel.azurecr.io/kraftdintel-backend:latest
docker push kraftdintel.azurecr.io/kraftdintel-backend:latest

# Container Apps will auto-update (may take 2-5 minutes)
```

---

## Troubleshooting Deployments

### Frontend Not Updating

1. Check GitHub Actions build status
   - GitHub → Actions → Latest workflow
   - Look for errors in build logs

2. Clear browser cache
   ```
   Ctrl+Shift+Delete (delete cached files)
   ```

3. Check SWA configuration
   ```bash
   az staticwebapp appsettings list \
     --name kraftdintel-web \
     --resource-group kraftdintel-rg
   ```

### Backend Not Responding

1. Check Container App status
   ```bash
   az containerapp show --name kraftdintel-app \
     --resource-group kraftdintel-rg
   ```

2. View logs
   ```bash
   az containerapp logs show --name kraftdintel-app \
     --resource-group kraftdintel-rg
   ```

3. Restart container
   ```bash
   az containerapp up --name kraftdintel-app \
     --resource-group kraftdintel-rg
   ```

---

## Performance Metrics

### Response Times

| Endpoint | Typical Time |
|----------|-------------|
| Static assets | < 500ms |
| API calls | 100-500ms |
| Database queries | 50-200ms |
| Health check | < 100ms |

### Scaling

- **Frontend:** Unlimited (CDN backed)
- **Backend:** Auto-scales 0-10 instances
- **Database:** Shared capacity (can increase)

---

## Cost Optimization

**Monthly Costs (~USD):**
- Static Web App: Free tier
- Container Apps: ~$15-30
- Cosmos DB: ~$20-50
- Application Insights: ~$5-10
- **Total: ~$40-90/month**

**Ways to reduce:**
- Use free tier for low traffic
- Archive old logs
- Optimize query patterns
- Set auto-scale limits

---

## Next Steps

1. ✅ Deployment verified
2. ⏳ Configure custom domain (optional)
3. ⏳ Set up CD/CI improvements
4. ⏳ Performance tuning
5. ⏳ Cost optimization

---

**Maintained In:** `/docs/04-deployment/DEPLOYMENT_GUIDE_v1.0.md`

For latest deployment information, always check `/docs/04-deployment/` folder.
