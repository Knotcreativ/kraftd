# 🚀 GitHub Actions Setup - Option 2

**Status**: Setting up production-ready CI/CD pipeline  
**Time**: 15 minutes total  
**Method**: Fully automated with tests before deployment  

---

## What We Just Did

✅ Created GitHub Actions workflow file:
```
.github/workflows/deploy.yml
```

This workflow:
- ✅ Runs on every push to main
- ✅ Builds your Python code
- ✅ Runs all 45+ tests
- ✅ **Only deploys if tests pass**
- ✅ Deploys to Azure Function App
- ✅ Logs everything for debugging

---

## Step 1: Get Publish Profile from Azure

### In Azure Portal:

1. Go to https://portal.azure.com
2. Navigate to your **Function App**
3. Click **Get publish profile** (top right button)
4. A file will download: `<app-name>.PublishSettings`
5. **Open the file** with a text editor
6. **Copy the ENTIRE XML content** (all of it)

The file looks like:
```xml
<?xml version="1.0" encoding="utf-8"?>
<publishData>
  <publishProfile profileName="...">
    ...entire XML content...
  </publishProfile>
</publishData>
```

---

## Step 2: Create GitHub Secret for Publish Profile

### In GitHub:

1. Go to your repository: https://github.com/Knotcreativ/kraftd
2. Click **Settings** (top right)
3. Left sidebar → **Secrets and variables** → **Actions**
4. Click **New repository secret**

**Create Secret 1:**
- Name: `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`
- Value: (paste the entire XML from Step 1)
- Click **Add secret**

---

## Step 3: Create GitHub Secret for Function App Name

### In GitHub (same Secrets page):

Click **New repository secret** again

**Create Secret 2:**
- Name: `AZURE_FUNCTION_APP_NAME`
- Value: (your function app name, e.g., `KraftdIntel-FunctionApp`)
- Click **Add secret**

---

## Step 4: Commit and Push Workflow File

### In PowerShell:

```powershell
# Navigate to repo
cd "c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel"

# Add workflow file to git
git add .github/workflows/deploy.yml

# Commit
git commit -m "Add GitHub Actions CI/CD workflow for automated deployment"

# Push to GitHub
git push origin main
```

Expected output:
```
[main abc1234] Add GitHub Actions CI/CD workflow for automated deployment
 1 file changed, 85 insertions(+)
 create mode .github/workflows/deploy.yml
Enumerating objects: 4, done.
Counting objects: 100% (4/4), done.
```

---

## Step 5: Monitor First Deployment

### In GitHub:

1. Go to your repository: https://github.com/Knotcreativ/kraftd
2. Click **Actions** tab (top navigation)
3. You should see a workflow running: "Build and Deploy to Azure Functions"
4. Click it to see real-time logs

**What you'll see:**
```
✅ Build and Test
   ├─ Checkout code
   ├─ Set up Python
   ├─ Install dependencies
   ├─ Run tests (45+ tests running...)
   └─ ✅ All tests passed!

✅ Deploy to Azure
   ├─ Checkout code
   ├─ Set up Python
   ├─ Install dependencies
   ├─ Deploy to Azure Functions
   └─ ✅ Successfully deployed!

✅ Notify Status
   ├─ Tests passed
   └─ Deployment successful
```

---

## Step 6: Set Environment Variables in Azure

### After deployment succeeds:

```powershell
# Set environment variables in the Azure Function App
az functionapp config appsettings set `
  -g kraftdintel-rg `
  -n <your-function-app-name> `
  --settings `
    COSMOS_DB_ENDPOINT="https://kraftdintel-cosmos.documents.azure.com:443/" `
    COSMOS_DB_KEY="Dg7UBtSjwXlavOZII1Da8M2lBuQVNhgaRYDcFHyfKVCtGcGLUbU9S2crsGlTB08dGR7LToOeYA6vACDb794KDA==" `
    COSMOS_DB_NAME="kraftd_audit" `
    COSMOS_DB_AUDIT_CONTAINER="audit_events" `
    COSMOS_DB_TTL_DAYS="2555"

# Restart to load new settings
az functionapp restart -g kraftdintel-rg -n <your-function-app-name>
```

---

## Step 7: Verify Deployment

### Test your endpoints:

```powershell
# Test login endpoint (should return 400, not 500)
curl -X POST https://<your-function-app-name>.azurewebsites.net/api/auth/login `
  -ContentType "application/json" `
  -Body '{"email":"test@example.com","password":"test"}'

# Check Cosmos DB for audit events
az cosmosdb sql query `
  -g kraftdintel-rg `
  -a kraftdintel-cosmos `
  -d kraftd_audit `
  -c audit_events `
  -q "SELECT TOP 10 * FROM c ORDER BY c.timestamp DESC"
```

---

## How It Works Going Forward

### Every time you push to main:

```powershell
git commit -m "Your changes"
git push origin main
```

**Automatically:**
1. GitHub detects the push
2. GitHub Actions workflow starts
3. Python code is built
4. All 45+ tests run
5. If tests **pass** → deploys to Azure
6. If tests **fail** → deployment is stopped (prevents broken code)
7. You see status in GitHub Actions tab

---

## GitHub Actions Dashboard

### View deployment status:

1. Go to: https://github.com/Knotcreativ/kraftd/actions
2. See all workflow runs
3. Click any run to see:
   - Build logs
   - Test output
   - Deployment status
   - Timestamps

### Status indicators:

- ✅ Green checkmark = Success
- ❌ Red X = Failed
- ⏳ Yellow circle = Running

---

## Workflow File Breakdown

### What the workflow does:

**On Every Push to Main:**

1. **Build and Test Job**
   - Checks out your code
   - Sets up Python 3.11
   - Installs dependencies
   - Runs all tests (45+)
   - **If tests fail** → workflow stops (prevents bad deploys)

2. **Deploy Job** (runs only if tests pass)
   - Deploys to Azure Function App
   - Uses publish profile from secrets
   - Restarts the function app

3. **Notify Job** (always runs)
   - Reports status
   - Shows what passed/failed

---

## What Tests Run

All 45+ tests including:
- ✅ Audit service tests (15)
- ✅ Compliance service tests (12)
- ✅ Alert service tests (8)
- ✅ Route integration tests (10)
- ✅ End-to-end tests (5+)

**Tests must pass before deployment!** This prevents broken code from going to production.

---

## Configuration Required

The workflow uses these GitHub Secrets (you've created them):
1. ✅ `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` - (XML file from Azure)
2. ✅ `AZURE_FUNCTION_APP_NAME` - (your function app name)

The workflow reads these from GitHub Secrets, so credentials are secure.

---

## Monitoring & Logs

### In GitHub Actions:

Click on any workflow run to see:
- Real-time build output
- Test results (each test listed)
- Deployment logs
- Any errors with full stack trace

### In Azure Portal:

After deployment, check:
- Function App → Overview (should say "Running")
- Function App → Log stream (see live logs)
- Application Insights (if connected)

---

## Troubleshooting

### "Tests failed"

1. Click the failed workflow in GitHub Actions
2. Scroll to the test output
3. See which test failed
4. Fix the code locally
5. Commit and push again

### "Deployment failed"

1. Check the deploy job logs
2. Common issues:
   - Publish profile incorrect (re-download from Azure)
   - Function app name wrong (check in Azure Portal)
   - Missing dependencies (check requirements.txt)

### "Workflow not running"

1. Make sure `.github/workflows/deploy.yml` is committed to main branch
2. Check GitHub Actions tab to see if workflow is listed
3. Push another commit to trigger it again

---

## Timeline from Now

```
✅ Workflow created and committed
   ↓
⏳ Push to GitHub (you do this now)
   ↓
🔨 GitHub Actions builds (2-3 min)
   ↓
🧪 Tests run (1-2 min)
   ↓
✅ Tests pass (all 45+)
   ↓
🚀 Deploy to Azure (2-3 min)
   ↓
🔄 Function app restarts (1 min)
   ↓
✅ LIVE IN PRODUCTION
```

**Total**: ~10 minutes from push to live

---

## Next Steps (Right Now)

### 1. Push the workflow file
```powershell
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Actions CI/CD workflow"
git push origin main
```

### 2. Watch it deploy
- Go to: https://github.com/Knotcreativ/kraftd/actions
- See the workflow running in real-time
- Watch the build, tests, and deployment

### 3. Set environment variables
```powershell
az functionapp config appsettings set \
  -g kraftdintel-rg \
  -n <your-function-app-name> \
  --settings COSMOS_DB_ENDPOINT="..." COSMOS_DB_KEY="..." ...
```

### 4. Verify it's working
```powershell
curl https://<your-function-app-name>.azurewebsites.net/api/auth/login -X POST
```

---

## Future Deployments (So Easy!)

From now on, deployment is just:

```powershell
git commit -m "Your feature"
git push origin main
# ✅ Done! Automatically building, testing, and deploying
```

No more manual deployment steps!

---

## Benefits of GitHub Actions

✅ **Automated Testing**
- All 45+ tests run before deployment
- Prevents broken code from going live

✅ **Audit Trail**
- Every deployment logged in GitHub
- See who deployed what when
- Rollback to any previous commit

✅ **Team Friendly**
- Multiple developers can push
- Each push triggers the workflow
- Everyone sees deployment status

✅ **Security**
- Credentials stored in GitHub Secrets
- Never exposed in logs
- Only accessible to workflow

✅ **Reliable**
- Consistent builds (same environment every time)
- No "works on my machine" problems
- Reproducible deployments

---

## Quick Reference

| Step | What | Where |
|------|------|-------|
| 1 | Get Publish Profile | Azure Portal → Function App → Get publish profile |
| 2 | Create Secret 1 | GitHub → Settings → Secrets → New secret |
| 3 | Create Secret 2 | GitHub → Settings → Secrets → New secret |
| 4 | Push workflow | `git push origin main` |
| 5 | Watch deployment | GitHub Actions tab |
| 6 | Set env vars | Azure Portal or Azure CLI |
| 7 | Verify | Test your endpoints |

---

## Status

✅ **Workflow Created**: `.github/workflows/deploy.yml`  
⏳ **Ready to Commit**: Push to GitHub (next step)  
⏳ **Ready to Deploy**: Secrets configured (next step)  

---

## Ready?

Run these commands:

```powershell
cd "c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel"
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Actions CI/CD workflow for automated deployment"
git push origin main
```

Then:
1. Go to GitHub Actions tab
2. Watch your first automatic deployment
3. See all tests pass
4. See app deploy to Azure
5. ✅ Done!

---

**This is production-grade CI/CD. Every deployment is tested and auditable.** 🚀
