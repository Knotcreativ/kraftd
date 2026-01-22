# 🎯 GitHub Actions Setup - 5 MINUTES TO AUTOMATED DEPLOYMENTS

**Status**: Ready to execute  
**Time**: 5 minutes total  
**Result**: Full CI/CD pipeline activated  

---

## ✅ What's Ready

The GitHub Actions workflow file is created:
```
✅ .github/workflows/deploy.yml
```

This will:
- ✅ Run tests on every push (45+ tests)
- ✅ Deploy only if all tests pass
- ✅ Prevent broken code from going live
- ✅ Keep full audit trail in GitHub

---

## 5 Commands to Execute (Copy & Paste)

### Command 1: Commit the Workflow File
```powershell
cd "c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel"
git add .github/workflows/deploy.yml
```

### Command 2: Commit with message
```powershell
git commit -m "Add GitHub Actions CI/CD workflow - automated build, test, and deploy"
```

### Command 3: Push to GitHub
```powershell
git push origin main
```

This triggers your first automated deployment! ✨

---

## Then: Get Azure Publish Profile

### Go to Azure Portal:

1. Open: https://portal.azure.com
2. Find your **Function App** (the one you're deploying to)
3. Click **Get publish profile** (button at top right)
4. A `.PublishSettings` file will download
5. Open it with Notepad
6. **Select all** (Ctrl+A) and **copy** the entire XML content

---

## Then: Create GitHub Secrets

### Secret 1: Publish Profile

1. Go to: https://github.com/Knotcreativ/kraftd/settings/secrets/actions
2. Click **New repository secret**
3. Fill in:
   - Name: `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`
   - Value: Paste the entire XML you copied
4. Click **Add secret**

### Secret 2: Function App Name

1. Click **New repository secret** again
2. Fill in:
   - Name: `AZURE_FUNCTION_APP_NAME`
   - Value: Your function app name (e.g., `KraftdIntel`)
3. Click **Add secret**

---

## Then: Watch GitHub Actions Deploy

### Go to GitHub Actions:

1. Open: https://github.com/Knotcreativ/kraftd/actions
2. See your workflow running: "Build and Deploy to Azure Functions"
3. Watch in real-time:
   - ✅ Checking out code
   - ✅ Setting up Python
   - ✅ Installing dependencies
   - ✅ Running 45+ tests
   - ✅ All tests passing
   - ✅ Deploying to Azure
   - ✅ Deployment successful

Estimated time: **~10 minutes**

---

## Then: Set Environment Variables

### After deployment succeeds:

```powershell
# IMPORTANT: Set these environment variables
az functionapp config appsettings set `
  -g kraftdintel-rg `
  -n <your-function-app-name> `
  --settings `
    COSMOS_DB_ENDPOINT="https://kraftdintel-cosmos.documents.azure.com:443/" `
    COSMOS_DB_KEY="Dg7UBtSjwXlavOZII1Da8M2lBuQVNhgaRYDcFHyfKVCtGcGLUbU9S2crsGlTB08dGR7LToOeYA6vACDb794KDA==" `
    COSMOS_DB_NAME="kraftd_audit" `
    COSMOS_DB_AUDIT_CONTAINER="audit_events" `
    COSMOS_DB_TTL_DAYS="2555"

# Restart function app to load settings
az functionapp restart -g kraftdintel-rg -n <your-function-app-name>
```

**WITHOUT these, the app cannot connect to Cosmos DB!**

---

## Then: Verify It Works

```powershell
# Test your API endpoint
curl -X POST https://<your-function-app-name>.azurewebsites.net/api/auth/login `
  -ContentType "application/json" `
  -Body '{"email":"test@example.com","password":"test"}'

# Should return 400 (missing fields) or 401 (invalid), NOT 500 or 404

# Check Cosmos DB for events
az cosmosdb sql query `
  -g kraftdintel-rg `
  -a kraftdintel-cosmos `
  -d kraftd_audit `
  -c audit_events `
  -q "SELECT TOP 5 * FROM c ORDER BY c.timestamp DESC"

# Should show recent audit events
```

---

## EXECUTION CHECKLIST

### Step 1: Commit & Push (5 minutes)
- [ ] Run: `git add .github/workflows/deploy.yml`
- [ ] Run: `git commit -m "Add GitHub Actions..."`
- [ ] Run: `git push origin main`
- [ ] Result: Code is on GitHub

### Step 2: Get Publish Profile (3 minutes)
- [ ] Go to Azure Portal
- [ ] Find Function App
- [ ] Click "Get publish profile"
- [ ] Copy the entire XML
- [ ] Result: Have publish profile ready

### Step 3: Create GitHub Secrets (3 minutes)
- [ ] Go to GitHub repo Settings → Secrets
- [ ] Create secret: `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`
- [ ] Create secret: `AZURE_FUNCTION_APP_NAME`
- [ ] Result: Secrets configured

### Step 4: Watch Deployment (10 minutes)
- [ ] Go to GitHub Actions tab
- [ ] Watch workflow run
- [ ] See tests pass
- [ ] See deployment complete
- [ ] Result: App deployed to Azure ✅

### Step 5: Configure Environment (5 minutes)
- [ ] Run: `az functionapp config appsettings set ...`
- [ ] Run: `az functionapp restart ...`
- [ ] Result: Cosmos DB connected

### Step 6: Verify (5 minutes)
- [ ] Test: `curl https://.../api/auth/login`
- [ ] Check: `az cosmosdb sql query ...`
- [ ] Result: All working ✅

---

## Visual Timeline

```
NOW (You are here)
  ↓
[5 min] Push workflow to GitHub
  ↓
[Wait] GitHub Actions starts building
  ↓
[3 min] Tests run (all 45+ should pass)
  ↓
[3 min] Deploy to Azure
  ↓
[1 min] Function app restarts
  ↓
[2 min] Set environment variables
  ↓
[2 min] Verify endpoints
  ↓
✅ LIVE IN PRODUCTION (25 minutes total)
```

---

## What Happens Next Time

After setup is complete, future deployments are **automatic**:

```powershell
git commit -m "your changes"
git push origin main
# ✨ Automatically building, testing, and deploying
```

That's it! No more manual steps. GitHub Actions handles everything:
1. ✅ Builds code
2. ✅ Runs 45+ tests
3. ✅ Deploys if tests pass
4. ✅ Skips deployment if tests fail (safe!)

---

## IMMEDIATE NEXT STEPS

### Right Now (5 minutes):

```powershell
# Go to your repository
cd "c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel"

# Add workflow to git
git add .github/workflows/deploy.yml

# Commit it
git commit -m "Add GitHub Actions CI/CD workflow - automated build, test, and deploy"

# Push to GitHub (this triggers your first deployment!)
git push origin main
```

### Then (3 minutes):

1. Go to: https://portal.azure.com
2. Function App → Get publish profile
3. Copy the XML

### Then (3 minutes):

1. Go to: https://github.com/Knotcreativ/kraftd/settings/secrets/actions
2. Create secret 1: `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` = (paste XML)
3. Create secret 2: `AZURE_FUNCTION_APP_NAME` = (your function app name)

### Then (10 minutes):

1. Go to: https://github.com/Knotcreativ/kraftd/actions
2. Watch the workflow run
3. See deployment complete

### Then (5 minutes):

```powershell
az functionapp config appsettings set \
  -g kraftdintel-rg \
  -n <function-app-name> \
  --settings COSMOS_DB_ENDPOINT="..." COSMOS_DB_KEY="..." ...

az functionapp restart -g kraftdintel-rg -n <function-app-name>
```

### Then (5 minutes):

```powershell
curl -X POST https://<function-app-name>.azurewebsites.net/api/auth/login
```

---

## Success Indicators

✅ **Deployment succeeded when you see:**
- Green checkmark on GitHub Actions
- All tests passed
- "Deploy to Azure Functions" shows success
- Function App status is "Running" in Azure Portal
- Endpoints respond with 400/401 (not 500)

---

## You're Ready!

Everything is set up. Just need to:

1. **Push the workflow** (5 min)
2. **Get publish profile** (3 min)
3. **Create GitHub secrets** (3 min)
4. **Watch deployment** (10 min)
5. **Set environment variables** (5 min)
6. **Verify** (5 min)

**Total: 30 minutes to fully automated CI/CD pipeline** ✨

---

## FAQ

**Q: What if a test fails?**
A: Deployment stops, preventing broken code from going live. You fix the code and push again.

**Q: Will this run on every commit?**
A: Yes! Every push to `main` triggers the workflow.

**Q: Can I disable automatic deployment?**
A: Yes, edit `.github/workflows/deploy.yml` and change the trigger.

**Q: How do I see what happened in a deployment?**
A: Click the workflow in GitHub Actions tab and scroll through logs.

**Q: What if the publish profile is wrong?**
A: Deployment fails. Just get a new profile and update the secret.

---

## Document Created

📄 **GITHUB_ACTIONS_SETUP.md** - Full setup guide  
📄 **GITHUB_ACTIONS_EXECUTION.md** - This file (step-by-step execution)

---

## Status

✅ Workflow file created  
⏳ Ready to push to GitHub  
⏳ Ready to configure secrets  
⏳ Ready to deploy  

---

**Let's do this! 🚀**

Ready? Run these three commands:

```powershell
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Actions CI/CD workflow"
git push origin main
```

Then watch the magic happen in GitHub Actions! ✨
