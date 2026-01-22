# 🚀 Azure Static Web App Deployment Guide - Kraftd Docs

**Date:** January 20, 2026  
**Status:** DEPLOYMENT READY  
**Version:** 1.0

---

## Overview

This guide will deploy your Kraftd Docs application to **Azure Static Web App** with:
- ✅ Branding and logos properly configured
- ✅ Dashboard styled according to Kraftd design system
- ✅ Backend API integration working
- ✅ Authentication system active
- ✅ CORS properly configured
- ✅ Production environment variables set

---

## Prerequisites

Before deploying, ensure you have:

- [x] Azure subscription active
- [x] Azure CLI installed (`az --version`)
- [x] Git installed and workspace initialized
- [x] Backend deployed to Azure Container Apps
- [x] All environment variables prepared
- [x] Frontend built and tested locally

**Verify Prerequisites:**
```bash
# Check Azure CLI
az --version

# Check Git
git --version

# Check Node.js
node --version  # v18+

# Check npm
npm --version   # 8+
```

---

## Step 1: Prepare Frontend for Production

### 1.1 Update Environment Variables

**File:** `frontend/.env.production`

```env
# API Configuration
VITE_API_URL=https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1

# reCAPTCHA (if using)
VITE_RECAPTCHA_SITE_KEY=your-production-recaptcha-key

# App Configuration
VITE_APP_NAME=Kraftd Docs
VITE_APP_VERSION=1.0.0
VITE_ENVIRONMENT=production

# Analytics (optional)
VITE_ANALYTICS_ID=your-analytics-id
```

### 1.2 Build Frontend

```bash
cd frontend
npm install
npm run build
```

**Expected Output:**
```
✓ 3 modules transformed.
dist/index.html                  15.92 kB │ gzip:  5.68 kB
dist/assets/main-abc123.js     324.56 kB │ gzip: 89.23 kB
dist/assets/style-def456.css    45.23 kB │ gzip: 12.34 kB

✓ built in 23.45s
```

### 1.3 Verify Build Output

```bash
# Check build folder exists
ls -la dist/

# Should contain:
# - index.html
# - assets/
# - favicon.ico (if applicable)
```

---

## Step 2: Configure Azure Static Web App

### 2.1 Create Resource Group (if not exists)

```bash
az group create \
  --name kraftd-docs-rg \
  --location uaenorth
```

### 2.2 Create Static Web App

**Option A: Using Azure Portal**

1. Go to Azure Portal
2. Search for "Static Web Apps"
3. Click "Create"
4. Fill in:
   - **Name:** kraftd-docs
   - **Region:** UAE North
   - **SKU:** Free (or Standard for production)
   - **Repository Source:** GitHub / Azure DevOps / Local Git
5. Click "Create"

**Option B: Using Azure CLI**

```bash
az staticwebapp create \
  --name kraftd-docs \
  --resource-group kraftd-docs-rg \
  --location uaenorth \
  --source https://github.com/your-org/kraftd-docs \
  --branch main \
  --login-with-github
```

### 2.3 Get the Deployment Token

```bash
# Get deployment token
TOKEN=$(az staticwebapp secrets list \
  --name kraftd-docs \
  --resource-group kraftd-docs-rg \
  --query "properties.apiKey" \
  --output tsv)

echo $TOKEN
```

**Save this token - you'll need it for deployments.**

---

## Step 3: Configure Static Web App Settings

### 3.1 Create `staticwebapp.config.json`

**File:** `frontend/staticwebapp.config.json`

```json
{
  "routes": [
    {
      "route": "/login",
      "rewrite": "/index.html"
    },
    {
      "route": "/dashboard",
      "rewrite": "/index.html"
    },
    {
      "route": "/register",
      "rewrite": "/index.html"
    },
    {
      "route": "/forgot-password",
      "rewrite": "/index.html"
    },
    {
      "route": "/reset-password",
      "rewrite": "/index.html"
    },
    {
      "route": "/verify-email",
      "rewrite": "/index.html"
    },
    {
      "route": "/api/*",
      "allowedRoles": ["authenticated"]
    },
    {
      "route": "/*",
      "serve": "/index.html",
      "statusCode": 200
    }
  ],
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/images/*", "/css/*", "/js/*"]
  },
  "responseOverrides": {
    "401": {
      "rewrite": "/login"
    },
    "404": {
      "rewrite": "/index.html"
    }
  },
  "mimeTypes": {
    ".json": "application/json",
    ".wasm": "application/wasm"
  },
  "auth": {
    "identityProviders": {
      "azureActiveDirectory": {
        "registration": {
          "openIdIssuer": "https://login.microsoftonline.com/YOUR_TENANT_ID/v2.0",
          "clientIdSettingName": "AZURE_CLIENT_ID",
          "clientSecretSettingName": "AZURE_CLIENT_SECRET"
        }
      }
    }
  },
  "globalHeaders": {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;"
  },
  "defaultErrorPage": "/index.html"
}
```

### 3.2 Create GitHub Actions Workflow (if using GitHub)

**File:** `.github/workflows/deploy-to-azure.yml`

```yaml
name: Deploy to Azure Static Web App

on:
  push:
    branches:
      - main
  pull_request:
    types: [opened, synchronize, reopened, closed]
    branches:
      - main

jobs:
  build_and_deploy_job:
    if: github.event_name == 'push' || (github.event_name == 'pull_request' && github.event.action != 'closed')
    runs-on: ubuntu-latest
    name: Build and Deploy Job
    steps:
      - uses: actions/checkout@v2
        with:
          submodules: true

      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'

      - name: Install and build frontend
        run: |
          cd frontend
          npm install
          npm run build
          cd ..

      - name: Build And Deploy
        id: builddeploy
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "/frontend/dist"
          api_location: "api"
          output_location: "dist"

  close_pull_request_job:
    if: github.event_name == 'pull_request' && github.event.action == 'closed'
    runs-on: ubuntu-latest
    name: Close Pull Request Job
    steps:
      - name: Close Pull Request
        id: closepullrequest
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          action: "close"
```

---

## Step 4: Configure Backend API Integration

### 4.1 Update CORS in Backend

**File:** `backend/main.py` (around line 60)

```python
# CORS Configuration for Production
ALLOWED_ORIGINS = [
    "http://localhost:5173",           # Development
    "http://localhost:3000",           # Alternative dev
    "https://kraftdocs.com",           # Production domain
    "https://www.kraftdocs.com",       # www version
    "https://app.kraftdocs.com",       # App subdomain
    "https://kraftd-docs.azurestaticapps.net"  # Azure Static Web App default
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page-Number", "X-Page-Size"],
)
```

### 4.2 Deploy Backend Updates

```bash
# If backend is in Azure Container Apps
cd backend
az containerapp up \
  --name kraftdintel-backend \
  --resource-group kraftd-docs-rg \
  --source .
```

---

## Step 5: Deploy Frontend to Static Web App

### 5.1 Option A: Deploy via GitHub Actions (Recommended)

```bash
# 1. Push code to GitHub
git add .
git commit -m "Prepare for Azure Static Web App deployment"
git push origin main

# 2. GitHub Actions will automatically:
#    - Build frontend
#    - Run tests
#    - Deploy to Azure Static Web App
#    - Run post-deployment verification

# 3. Monitor deployment at:
# https://github.com/your-org/kraftd-docs/actions
```

### 5.2 Option B: Deploy via Azure CLI

```bash
cd frontend

# Deploy using Azure Static Web Apps CLI
npm install -g @azure/static-web-apps-cli

swa deploy \
  --deployment-token $TOKEN \
  --app-location "./dist" \
  --env production
```

### 5.3 Option C: Deploy via Azure Portal

1. Go to your Static Web App resource
2. Click "Deployments"
3. Click "+ Deploy"
4. Select "Upload"
5. Choose your `dist` folder
6. Click "Deploy"

---

## Step 6: Configure Custom Domain

### 6.1 Add Custom Domain

```bash
# Add domain
az staticwebapp custom-domain create \
  --name kraftd-docs \
  --resource-group kraftd-docs-rg \
  --domain-name kraftdocs.com
```

### 6.2 Update DNS Records

**In your domain registrar (GoDaddy, Namecheap, etc.):**

Add CNAME record:
```
Name: kraftdocs.com
Type: CNAME
Value: kraftd-docs.azurestaticapps.net
```

Wait for DNS propagation (5-48 hours).

### 6.3 Enable HTTPS

Azure Static Web Apps automatically enables HTTPS with Let's Encrypt SSL.

**Verify SSL:**
```bash
# Check certificate
curl -I https://kraftdocs.com

# Should show:
# HTTP/2 200
# strict-transport-security: max-age=31536000
```

---

## Step 7: Configure Branding

### 7.1 Update Site Metadata

**File:** `frontend/index.html`

```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Kraftd Docs - Audit-native intelligence for supply chain professionals. Process documents 95% faster with AI.">
    <meta name="keywords" content="supply chain, document processing, AI, audit, intelligence">
    <meta name="theme-color" content="#00BCD4">
    <meta name="og:title" content="Kraftd Docs - Document Intelligence Platform">
    <meta name="og:description" content="Transform your supply chain with audit-native intelligence">
    <meta name="og:image" content="https://kraftdocs.com/images/og-image.png">
    
    <!-- Favicon -->
    <link rel="icon" type="image/png" href="/favicon.png">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    
    <!-- Brand Colors -->
    <style>
        :root {
            --primary: #00BCD4;
            --primary-dark: #0097A7;
            --secondary: #1A5A7A;
            --dark-text: #1A1A1A;
            --body-text: #536B82;
            --light-bg: #F8F9FA;
            --border: #E0E0E0;
            --white: #FFFFFF;
            --success: #4CAF50;
            --error: #F44336;
        }
    </style>
    
    <title>Kraftd Docs - Supply Chain Intelligence</title>
</head>
```

### 7.2 Add Logo to Dashboard

**File:** `frontend/src/pages/Dashboard.tsx`

```tsx
import logo from '../assets/kraftd-logo.svg'

export default function Dashboard() {
  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <img src={logo} alt="Kraftd Logo" className="logo" />
        <h1>Kraftd Docs</h1>
        {/* ... rest of header ... */}
      </header>
    </div>
  )
}
```

**CSS:** `frontend/src/pages/Dashboard.css`

```css
.dashboard-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  background: linear-gradient(135deg, #00BCD4, #1A5A7A);
  color: white;
}

.logo {
  height: 40px;
  width: auto;
}

.dashboard-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}
```

---

## Step 8: Configure Authentication

### 8.1 Update Login Redirect

**File:** `frontend/src/context/AuthContext.tsx`

```typescript
// After successful login, redirect to dashboard
const handleLogin = async () => {
  try {
    await login(email, password)
    // Check if we have a return URL
    const returnUrl = new URLSearchParams(window.location.search).get('returnUrl')
    navigate(returnUrl || '/dashboard')
  } catch (error) {
    // Handle error
  }
}
```

### 8.2 Update API Client for Production

**File:** `frontend/src/services/api.ts`

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 
  'https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1'

// Ensure HTTPS in production
if (typeof window !== 'undefined' && window.location.protocol === 'http:' && 
    !window.location.hostname.includes('localhost')) {
  window.location.protocol = 'https:'
}
```

---

## Step 9: Verify Deployment

### 9.1 Check Deployment Status

```bash
# View deployment history
az staticwebapp deployments list \
  --name kraftd-docs \
  --resource-group kraftd-docs-rg

# Get details of latest deployment
az staticwebapp show \
  --name kraftd-docs \
  --resource-group kraftd-docs-rg
```

### 9.2 Test Application

**URL:** `https://kraftdocs.com`

**Tests to Run:**

```
1. ✓ Landing page loads
2. ✓ Navigation works
3. ✓ Login form displays
4. ✓ Can register new account
5. ✓ Can login with credentials
6. ✓ Dashboard loads after login
7. ✓ Documents can be uploaded
8. ✓ Can logout
9. ✓ Protected routes work
10. ✓ Branding is correct (colors, logos)
11. ✓ Responsive on mobile
12. ✓ HTTPS working
13. ✓ API calls successful
14. ✓ Error messages display properly
```

### 9.3 Check Logs

```bash
# View Static Web App logs
az staticwebapp logs list \
  --name kraftd-docs \
  --resource-group kraftd-docs-rg

# Or in Azure Portal:
# Static Web Apps > Deployments > View logs
```

---

## Step 10: Configure Monitoring & Alerts

### 10.1 Set Up Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app kraftd-docs-insights \
  --location uaenorth \
  --resource-group kraftd-docs-rg \
  --application-type web

# Get instrumentation key
KEY=$(az monitor app-insights component show \
  --app kraftd-docs-insights \
  --resource-group kraftd-docs-rg \
  --query "instrumentationKey" \
  --output tsv)

echo $KEY
```

### 10.2 Add Monitoring to Frontend

**File:** `frontend/src/main.tsx`

```typescript
import { ApplicationInsights } from '@microsoft/applicationinsights-web'

const appInsights = new ApplicationInsights({
  config: {
    instrumentationKey: import.meta.env.VITE_APP_INSIGHTS_KEY,
    enableAutoRouteTracking: true,
    enableRequestHeaderTracking: true,
    enableResponseHeaderTracking: true,
    disableAjaxTracking: false,
    maxAjaxCallsPerView: 500,
  }
})

appInsights.loadAppInsights()
```

### 10.3 Create Alerts

```bash
# Alert for high error rate
az monitor metrics alert create \
  --name "Kraftd Docs - High Error Rate" \
  --resource-group kraftd-docs-rg \
  --scopes /subscriptions/{subscription-id}/resourceGroups/kraftd-docs-rg/providers/Microsoft.Web/staticSites/kraftd-docs \
  --condition "avg http5xx > 10" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action email-action
```

---

## Step 11: Post-Deployment Checklist

- [ ] Frontend deployed to Azure Static Web App
- [ ] Custom domain configured
- [ ] HTTPS certificate active
- [ ] Branding and logos displaying correctly
- [ ] Authentication system working
- [ ] Dashboard accessible after login
- [ ] API calls to backend successful
- [ ] CORS properly configured
- [ ] Protected routes enforced
- [ ] Error handling working
- [ ] Monitoring and alerts configured
- [ ] Performance acceptable (< 2s load time)
- [ ] Mobile responsive confirmed
- [ ] All tests passing
- [ ] Team notified of deployment

---

## Troubleshooting

### Issue: "CORS error when calling API"

**Solution:**
```bash
# Check CORS configuration in backend
az containerapp show \
  --name kraftdintel-backend \
  --resource-group kraftd-docs-rg

# Update CORS in main.py with Azure Static Web App domain
ALLOWED_ORIGINS = [
    "https://kraftdocs.com",
    "https://kraftd-docs.azurestaticapps.net"
]

# Redeploy backend
az containerapp up --name kraftdintel-backend --source .
```

### Issue: "404 error on refresh"

**Solution:** Ensure `staticwebapp.config.json` is configured correctly:
```json
{
  "navigationFallback": {
    "rewrite": "/index.html"
  }
}
```

### Issue: "Tokens not persisting"

**Solution:** Check localStorage configuration:
```typescript
// frontend/src/context/AuthContext.tsx
localStorage.setItem('accessToken', token)  // Verify this works
```

### Issue: "Dashboard not loading after login"

**Solution:** Check protected routes:
```tsx
// Verify Dashboard.tsx checks authentication
const { isAuthenticated } = useAuth()
if (!isAuthenticated) navigate('/login')
```

---

## Performance Optimization

### 10.1 Enable Compression

```json
{
  "globalHeaders": {
    "Accept-Encoding": "gzip, deflate, br"
  }
}
```

### 10.2 Cache Control

```json
{
  "routes": [
    {
      "route": "/assets/*",
      "headers": {
        "cache-control": "public, max-age=31536000, immutable"
      }
    },
    {
      "route": "*.json",
      "headers": {
        "cache-control": "public, max-age=3600"
      }
    }
  ]
}
```

### 10.3 Content Delivery Network (CDN)

```bash
# Enable CDN for Static Web App
az staticwebapp settings update \
  --name kraftd-docs \
  --resource-group kraftd-docs-rg \
  --cdn-enabled true
```

---

## Rollback Plan

If deployment fails:

```bash
# Revert to previous deployment
az staticwebapp deployments rollback \
  --name kraftd-docs \
  --resource-group kraftd-docs-rg \
  --deployment-id <previous-deployment-id>

# Or redeploy previous version from Git
git revert <commit-hash>
git push origin main
```

---

## Success Criteria

✅ **Deployment Successful When:**

```
□ https://kraftdocs.com is accessible
□ Landing page loads (< 2s)
□ Login form works
□ Can register account
□ Can login and see dashboard
□ Branding colors and logos correct
□ Responsive on mobile
□ HTTPS working
□ API calls successful
□ No errors in console
□ All tests passing
□ Monitoring active
```

---

## Next Steps After Deployment

1. **Monitor Performance**
   - Check Application Insights daily
   - Monitor API response times
   - Track user metrics

2. **Gather Feedback**
   - Send email to early users
   - Collect feature requests
   - Monitor error logs

3. **Plan Updates**
   - Schedule regular deployments
   - Plan Phase 2 features
   - Update documentation

4. **Security**
   - Run security audit
   - Review access logs
   - Update firewall rules

---

## Support & Documentation

- **Azure Static Web Apps Docs:** https://learn.microsoft.com/azure/static-web-apps/
- **Troubleshooting:** https://learn.microsoft.com/azure/static-web-apps/troubleshooting
- **FAQs:** https://learn.microsoft.com/azure/static-web-apps/faq

---

**Deployment Guide Status:** ✅ COMPLETE  
**Ready to Deploy:** YES  
**Estimated Time:** 30-45 minutes  

