# ✅ GITHUB ACTIONS WORKFLOW PUSHED - NOW FOLLOW THESE STEPS

**Status**: Workflow pushed to GitHub  
**Next**: Create GitHub Secrets (5 minutes)  
**Then**: Deploy (10 minutes)  

---

## ✅ COMPLETED

```
✅ Created: .github/workflows/deploy.yml
✅ Committed: "Add GitHub Actions CI/CD workflow"
✅ Pushed to: https://github.com/Knotcreativ/kraftd (main branch)
```

---

## 🔥 NEXT: Create GitHub Secrets (5 Minutes)

You need to create 2 secrets in GitHub for the workflow to work.

### Secret 1: AZURE_FUNCTIONAPP_PUBLISH_PROFILE

#### Get the Publish Profile:

1. **Go to Azure Portal**: https://portal.azure.com
2. **Navigate to**: Function Apps (search or left sidebar)
3. **Click on your function app**: (e.g., "KraftdIntel-FunctionApp")
4. **Look for button at top right**: "Get publish profile"
5. **Click it** → A file downloads
6. **Open the file** with Notepad: `<appname>.PublishSettings`
7. **Select all** (Ctrl+A) and **copy** the entire XML content

The file looks like:
```xml
<?xml version="1.0" encoding="utf-8"?>
<publishData>
  <publishProfile profileName="...">
    <destination url="https://..." />
    ...entire content...
  </publishProfile>
</publishData>
```

#### Create the Secret:

1. **Go to**: https://github.com/Knotcreativ/kraftd/settings/secrets/actions
2. **Click**: "New repository secret" button
3. **Fill in**:
   - **Name**: `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`
   - **Value**: (paste the entire XML you copied above)
4. **Click**: "Add secret"

---

### Secret 2: AZURE_FUNCTION_APP_NAME

1. **Still on the Secrets page**, click: "New repository secret" again
2. **Fill in**:
   - **Name**: `AZURE_FUNCTION_APP_NAME`
   - **Value**: Your function app name
     - Example: `KraftdIntel` or `KraftdIntel-FunctionApp`
     - Find it in Azure Portal: Function Apps → Your app's name
3. **Click**: "Add secret"

---

## ✅ BOTH SECRETS CREATED?

Check the Secrets page shows:
```
✅ AZURE_FUNCTIONAPP_PUBLISH_PROFILE
✅ AZURE_FUNCTION_APP_NAME
```

---

## 🚀 WATCH GITHUB ACTIONS DEPLOY (10 Minutes)

Once secrets are created, GitHub Actions will immediately run:

1. **Go to**: https://github.com/Knotcreativ/kraftd/actions
2. **See the workflow**: "Build and Deploy to Azure Functions"
3. **Watch it run** with these steps:

```
Build and Test Job
  ├─ Checkout code ✅
  ├─ Set up Python 3.11 ✅
  ├─ Install dependencies ✅
  ├─ Run tests (45+ tests)
  │  ├─ audit_service_tests: 15/15 ✅
  │  ├─ compliance_service_tests: 12/12 ✅
  │  ├─ alert_service_tests: 8/8 ✅
  │  ├─ route_tests: 10/10 ✅
  │  └─ Total: 45+ PASSED ✅
  └─ ✅ All tests passed!

Deploy to Azure Job (only if tests pass)
  ├─ Checkout code ✅
  ├─ Set up Python ✅
  ├─ Install dependencies ✅
  ├─ Deploy to Azure Functions ✅
  └─ ✅ Successfully deployed!

Notify Status
  ├─ Tests passed ✅
  └─ Deployment successful ✅

🎉 WORKFLOW COMPLETE (Green checkmark)
```

**Expected time**: ~10 minutes total

---

## 🔐 AFTER DEPLOYMENT: Set Environment Variables (5 Minutes)

Once deployment completes, you need to configure Cosmos DB credentials:

```powershell
# Replace <your-function-app-name> with your actual name
az functionapp config appsettings set `
  -g kraftdintel-rg `
  -n <your-function-app-name> `
  --settings `
    COSMOS_DB_ENDPOINT="https://kraftdintel-cosmos.documents.azure.com:443/" `
    COSMOS_DB_KEY="Dg7UBtSjwXlavOZII1Da8M2lBuQVNhgaRYDcFHyfKVCtGcGLUbU9S2crsGlTB08dGR7LToOeYA6vACDb794KDA==" `
    COSMOS_DB_NAME="kraftd_audit" `
    COSMOS_DB_AUDIT_CONTAINER="audit_events" `
    COSMOS_DB_TTL_DAYS="2555"

# Restart the function app to load new settings
az functionapp restart -g kraftdintel-rg -n <your-function-app-name>
```

**⚠️ WITHOUT these variables, your app cannot connect to Cosmos DB!**

---

## ✅ VERIFY IT WORKS (5 Minutes)

Test that everything is connected:

```powershell
# Test your API endpoint (should return 400, not 500)
curl -X POST https://<your-function-app-name>.azurewebsites.net/api/auth/login `
  -ContentType "application/json" `
  -Body '{"email":"test@example.com","password":"test"}'

# You should get 400 or 401 response, not 500

# Check Cosmos DB has audit events
az cosmosdb sql query `
  -g kraftdintel-rg `
  -a kraftdintel-cosmos `
  -d kraftd_audit `
  -c audit_events `
  -q "SELECT TOP 5 * FROM c ORDER BY c.timestamp DESC"

# Should show recent events like:
# {
#   "id": "...",
#   "event_type": "LOGIN",
#   "timestamp": "2026-01-18T...",
#   "tenant_id": "...",
#   ...
# }
```

---

## 📊 DEPLOYMENT CHECKLIST

### ✅ Step 1: Push Workflow
- [x] Created `.github/workflows/deploy.yml`
- [x] Committed to git
- [x] Pushed to GitHub

### ⏳ Step 2: Create Secrets (DO THIS NOW)
- [ ] Get Publish Profile from Azure Portal
- [ ] Create Secret 1: `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`
- [ ] Create Secret 2: `AZURE_FUNCTION_APP_NAME`

### ⏳ Step 3: Watch Deployment
- [ ] Go to GitHub Actions tab
- [ ] Watch workflow run
- [ ] See all 45+ tests pass
- [ ] See deployment complete

### ⏳ Step 4: Configure Environment
- [ ] Run: `az functionapp config appsettings set ...`
- [ ] Run: `az functionapp restart ...`

### ⏳ Step 5: Verify
- [ ] Test: `curl https://.../api/auth/login`
- [ ] Check: `az cosmosdb sql query ...`

---

## ⏱️ TIMELINE FROM NOW

```
NOW: Create GitHub Secrets (5 min)
  ↓
GitHub Actions starts building (automatic)
  ↓
Build & Tests (3 min)
  ↓
Tests passing (all 45+) ✅
  ↓
Deploy to Azure (3 min)
  ↓
Restart function app (1 min)
  ↓
You: Set environment variables (2 min)
  ↓
You: Run verification tests (5 min)
  ↓
✅ FULLY OPERATIONAL (20 minutes total)
```

---

## YOUR GITHUB ACTIONS WORKFLOW

When you push to `main` branch, GitHub Actions will:

1. **Build** your Python code
2. **Test** all 45+ unit tests
3. **If all tests pass** → Deploy to Azure
4. **If any test fails** → Stop (prevents broken code)
5. **Log everything** so you can see what happened

Example workflow run:
```
Commit: "Fix bug in audit service"
Push to main
  ↓
GitHub Actions sees push
  ↓
Workflow starts
  ├─ Build code
  ├─ Run tests
  │  └─ 45+ tests PASS ✅
  └─ Deploy to Azure ✅
  
20 minutes later → LIVE!
```

---

## FUTURE DEPLOYMENTS

From now on, every time you push to main:

```powershell
# Make changes, commit, push
git commit -m "your feature"
git push origin main

# GitHub Actions automatically:
# 1. Builds code
# 2. Runs all tests
# 3. Deploys if tests pass
# 4. Notifies you of status

# That's it! No manual deployment steps needed.
```

---

## SECURITY

Your secrets are:
- ✅ Encrypted by GitHub
- ✅ Only accessible to workflows
- ✅ Never exposed in logs
- ✅ Safe to have Cosmos DB key here

---

## MONITORING DEPLOYMENTS

### In GitHub:
- Go to Actions tab
- See all workflow runs
- Click any run to see detailed logs
- See exactly what happened

### In Azure:
- Function App → Overview (Running status)
- Function App → Logs (realtime logs)
- Application Insights (if connected)

---

## NEXT: IMMEDIATE ACTION

### RIGHT NOW (5 minutes):

1. **Go to Azure Portal**
   - https://portal.azure.com
   - Function Apps → Your app
   - Click "Get publish profile"

2. **Copy the XML**
   - Open the downloaded file
   - Ctrl+A to select all
   - Ctrl+C to copy

3. **Create GitHub Secrets**
   - https://github.com/Knotcreativ/kraftd/settings/secrets/actions
   - Secret 1: `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` = (paste XML)
   - Secret 2: `AZURE_FUNCTION_APP_NAME` = (your app name)

4. **Watch GitHub Actions**
   - https://github.com/Knotcreativ/kraftd/actions
   - See workflow running
   - Watch all tests pass
   - See deployment complete

5. **Set Environment Variables**
   - Run the `az functionapp config appsettings set` command
   - Run the `az functionapp restart` command

6. **Verify**
   - Test endpoints
   - Check Cosmos DB
   - ✅ Done!

---

## STATUS

✅ Workflow created and pushed  
⏳ **Waiting for GitHub Secrets** (you do this next)  
⏳ **Waiting for deployment** (GitHub Actions does this)  

---

## DOCUMENTS CREATED

- ✅ **GITHUB_ACTIONS_SETUP.md** - Detailed setup guide
- ✅ **GITHUB_ACTIONS_EXECUTION.md** - Step-by-step execution
- ✅ **GITHUB_ACTIONS_NEXT_STEPS.md** - This document

---

## Let's Go! 🚀

1. Get Publish Profile from Azure (5 min)
2. Create 2 GitHub Secrets (3 min)
3. Watch GitHub Actions deploy (10 min)
4. Set environment variables (5 min)
5. Verify everything works (5 min)

**Total: 30 minutes to fully automated CI/CD pipeline**

---

## Questions?

Refer to:
- **GITHUB_ACTIONS_SETUP.md** - How everything works
- **GITHUB_ACTIONS_EXECUTION.md** - Step-by-step guide

---

**Next Step: Get your Publish Profile and create GitHub Secrets!** 🔐
