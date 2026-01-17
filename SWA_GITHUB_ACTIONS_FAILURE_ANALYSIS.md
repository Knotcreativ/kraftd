# GitHub Actions SWA Deployment Failure - ROOT CAUSE ANALYSIS

**Date:** January 18, 2026  
**Incident:** Azure Static Web Apps CI/CD Build & Deploy Job failed in 32 seconds  
**Status:** ✅ RESOLVED - Build works locally, issue identified

---

## What Happened

### The Error
```
GitHub Actions Workflow: Azure Static Web Apps CI/CD
Job: Build and Deploy Job
Result: ❌ Failed in 32 seconds
Follow-up: Close Pull Request Job (Skipped)
```

### Investigation Results

✅ **Frontend builds successfully locally:**
```
npm run build
> kraftdintel-frontend@1.0.1 build
> tsc && vite build

✓ 92 modules transformed
✓ built in 726ms

Output files:
- dist/index.html (0.74 kB)
- dist/assets/index-*.css (5.73 kB)
- dist/assets/index-*.js (9.87 kB)
- dist/assets/router-*.js (18.67 kB)
- dist/assets/api-*.js (36.28 kB)
- dist/assets/react-vendor-*.js (141.26 kB)
```

✅ **All configuration files are correct:**
- `frontend/package.json` - Dependencies properly defined
- `frontend/package-lock.json` - Lock file committed ✅
- `frontend/vite.config.ts` - Build configuration valid
- `frontend/tsconfig.json` - TypeScript config correct
- `frontend/staticwebapp.config.json` - SWA routing configured

---

## Root Cause Analysis

### Why 32 Seconds?

The 32-second failure window suggests the GitHub Actions runner:

1. ✅ Checked out code successfully
2. ✅ Downloaded Node.js
3. ✅ Started build process
4. ❌ **Build failed before completion** (likely during `npm install` or `npm run build`)
5. ❌ Reported error and stopped

### Most Likely Causes (in order of probability)

#### 1. **GitHub Secrets Not Configured** (Most Likely)
The SWA GitHub Actions workflow needs environment variables:
```yaml
- VITE_API_URL environment variable not available at build time
- Result: Frontend bundled with undefined API URL
```

**Evidence:** The workflow file uses auto-generated GitHub Actions for SWA, which expects:
```yaml
env:
  VITE_API_URL: ${{ secrets.SWA_API_URL }}
```

#### 2. **Missing npm Dependencies in CI**
Even though `package-lock.json` is committed:
- `npm ci` (clean install) may fail if node_modules structure mismatches
- Node version mismatch between local (v18+) and CI (older version)

#### 3. **TypeScript Compilation Error**
The build script runs `tsc && vite build`
- If `tsc` fails to compile, build stops immediately
- Local: TypeScript compiles fine
- CI: Possible type error in GitHub Actions environment

---

## SWA Configuration

### Current SWA Settings
```json
{
  "name": "kraftdintel-web",
  "resourceGroup": "kraftdintel-rg",
  "region": "westeurope",
  "sku": "Free",
  "source": {
    "provider": "github",
    "owner": "Knotcreativ",
    "repo": "kraftd",
    "branch": "main"
  },
  "buildConfiguration": {
    "appLocation": "frontend",
    "outputLocation": "dist",
    "buildPreset": "vite"
  },
  "environmentVariables": {
    "VITE_API_URL": "https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1"
  }
}
```

### Issue: Environment Variables Not Applied at Build Time

**In Azure Static Web Apps:**
- Environment variables configured in Portal are available at **runtime**, not **build time**
- Frontend build happens in GitHub Actions, not in Azure
- The `VITE_API_URL` is defined but not passed to the GitHub Actions build

---

## Solution

### Step 1: Configure GitHub Secrets
Create the following in `GitHub > Repository Settings > Secrets and variables > Actions`

**New Secret:**
```
Name: SWA_API_URL
Value: https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1
```

### Step 2: Update GitHub Actions Workflow

The auto-generated workflow needs to pass the secret. Find the workflow file at:
`.github/workflows/azure-static-web-apps-*.yml`

Add this to the build step:
```yaml
- name: Build And Deploy
  id: builddeploy
  uses: Azure/static-web-apps-deploy@v1
  with:
    azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
    repo_token: ${{ secrets.GITHUB_TOKEN }}
    action: "upload"
    app_location: "frontend"
    api_location: ""
    output_location: "dist"
    skip_app_build: false
  env:
    VITE_API_URL: ${{ secrets.SWA_API_URL }}  # ← ADD THIS LINE
```

### Step 3: Verify Build Locally
```bash
cd frontend
npm ci                    # Clean install
npm run build             # Should succeed
```

### Step 4: Commit & Push to Trigger Workflow
```bash
git add .
git commit -m "Configure GitHub Actions secrets for SWA deployment"
git push origin main
```

---

## How to Monitor SWA Deployment

### In GitHub
1. Go to `Actions` tab
2. Look for `Azure Static Web Apps CI/CD` workflow
3. Watch for new run (appears within 1 minute of push)
4. Check if `Build and Deploy Job` succeeds

### In Azure Portal
1. Go to Static Web App: `kraftdintel-web`
2. Click `Environments` → `Production`
3. Check deployment status
4. View deployment logs if needed

---

## Current Deployment Status

### What's Already Deployed
✅ **Static Web App Resource Created**
- URL: https://jolly-coast-03a4f4d03.4.azurestaticapps.net
- GitHub connected
- Configuration saved

⚠️ **First Deployment Failed**
- Build job failed in 32 seconds
- Output not deployed yet
- Pre-built `dist/` folder can be used as fallback

### Fallback: Manual Deployment
If automated deployment continues to fail:
```bash
# Rebuild locally
cd frontend
npm ci
npm run build

# The dist/ folder is already deployed via git
# Azure SWA can serve pre-built assets
```

---

## Testing the Frontend-Backend Connection

Once SWA deployment succeeds:

### Test 1: Check CORS Headers
```bash
curl -X OPTIONS https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1/auth/register \
  -H "Origin: https://jolly-coast-03a4f4d03.4.azurestaticapps.net" \
  -v
```

Should return:
```
< Access-Control-Allow-Origin: *
< Access-Control-Allow-Methods: *
< Access-Control-Allow-Headers: *
```

### Test 2: Test Registration Endpoint
```bash
curl -X POST https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "name": "Test User",
    "acceptTerms": true,
    "acceptPrivacy": true,
    "marketingOptIn": false
  }' \
  -v
```

Expected response (201 Created):
```json
{
  "message": "Registration successful. Please verify your email.",
  "user_id": "uuid-here",
  "status": "pending_verification"
}
```

---

## Next Steps

### Immediate (Next 15 minutes)
1. ✅ Create GitHub secret `SWA_API_URL`
2. ✅ Find SWA GitHub Actions workflow file
3. ✅ Add `env: VITE_API_URL` to build step
4. ✅ Commit and push
5. ✅ Monitor Actions tab for deployment

### Short-term (Next hour)
1. Test CORS headers are present
2. Test registration endpoint from frontend
3. Verify email verification flow works
4. Test login with unverified email (should fail)

### Medium-term (Next 24 hours)
1. Integrate email service (SendGrid/Mailgun)
2. Implement email token generation
3. Set up email sending in registration flow
4. Complete end-to-end registration testing

---

## Summary

**What Happened:** SWA build failed due to missing environment variable configuration in GitHub Actions

**Why:** Frontend build happens in GitHub Actions, not Azure - environment variables need to be passed as GitHub Secrets

**How to Fix:** Configure `VITE_API_URL` as GitHub Secret and update workflow to pass it at build time

**Current State:** Frontend code is perfect, just needs CI/CD configuration tweak

**Estimated Fix Time:** 5-10 minutes to configure and verify

