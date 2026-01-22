# Kraftd Static Web App - Environment Configuration

## Current Deployment Status
- ✅ Backend API: LIVE at https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io
- ✅ Database: Cosmos DB operational (UAE North)
- ✅ Monitoring: Application Insights active
- ✅ Frontend Code: Built and pushed to GitHub
- ✅ Documentation: Complete (19 documents, 100% QA verified)
- ⏳ Static Web App: Verification in progress

## Required Configuration

### Static Web App Details
- **Name:** kraftdintel-web
- **Resource Group:** kraftdintel-rg
- **Location:** West Europe (SWA availability constraint)
- **Repository:** https://github.com/Knotcreativ/kraftd (main branch)
- **Build Configuration:**
  - App Location: `frontend`
  - Output Location: `dist`
  - Build Preset: `vite`

### Environment Variable to Configure
```powershell
# Azure CLI command to set environment variable:
az staticwebapp appsettings set `
    --name kraftdintel-web `
    --resource-group kraftdintel-rg `
    --setting-names VITE_API_URL="https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1"
```

**Purpose:** Connects frontend React app to backend FastAPI server

### Manual Configuration (If CLI Fails)
1. Go to Azure Portal
2. Navigate to Static Web Apps → kraftdintel-web
3. Settings → Configuration
4. Click "+ Add" under Application settings
5. Name: `VITE_API_URL`
6. Value: `https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1`
7. Click "Save"

## Deployment Flow After Configuration

1. **Environment Variable Set** (↓ 30 seconds)
   - Portal saves configuration
   - GitHub Actions receives webhook notification

2. **GitHub Actions Build Triggered** (↓ 2-5 minutes)
   - React frontend builds with Vite
   - Environment variable injected into build
   - Assets compiled and optimized

3. **Build Completes**
   - Static assets deployed to SWA CDN
   - Frontend URL available: https://kraftdintel-web.azurestaticapps.net

4. **Smoke Test**
   - Access frontend at SWA URL
   - Verify login page loads
   - Test API connectivity (Dashboard loads → calls GET /documents)
   - Confirm health endpoint responds

## Expected Outcome

**Frontend will be accessible at:**
```
https://kraftdintel-web.azurestaticapps.net
```

**Connected to Backend API:**
```
https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1
```

## Testing Checklist

- [ ] Frontend URL loads (homepage/login)
- [ ] Can register new account
- [ ] Can login with test account
- [ ] Dashboard loads (API call successful)
- [ ] Can navigate to upload page
- [ ] Health endpoint returns 200 (GET /health)
- [ ] Application Insights shows frontend traffic
- [ ] Can upload test document
- [ ] Processing pipeline executes
- [ ] Results display correctly

## Post-Deployment

Once verified, share these documentation links with stakeholders:

- **USER_FLOW.md** - Complete 10-step user journey with processing pipeline details
- **QUICK_REFERENCE.md** - Visual guide with 26 API endpoints, system architecture, data flow examples
- **API_CONTRACT_v1.0.md** - Full endpoint specification with examples
- **DEPLOYMENT_STATUS.md** - Current architecture overview
- **GETTING_STARTED.md** - Developer setup guide

## Support Resources

- **Backend Health:** GET /health
- **API Documentation:** GET /docs (Swagger UI)
- **Logs:** Azure Monitor → Application Insights
- **GitHub Repo:** https://github.com/Knotcreativ/kraftd (main branch)
- **Discord/Teams:** [Team communication channel]

---
**Status:** 95% Complete - One configuration step remaining
**Time to Completion:** ~15 minutes from environment variable configuration
