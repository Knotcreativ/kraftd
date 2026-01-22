# ⚡ PRE-FLIGHT VERIFICATION - RUN NOW (Jan 20, Evening)

**Run these commands tonight to confirm everything works before 02:00 AM tomorrow.**

---

## 🔍 QUICK VERIFICATION (10 minutes)

### Step 1: Azure Access
```powershell
az login
# Should show your subscription immediately
```

✅ **Expected:** Account information displayed  
❌ **If fails:** Fix Azure credentials before sleeping

---

### Step 2: Resource Group
```powershell
az group show --name "kraftd-rg"
```

✅ **Expected:** Resource group details (location, created date, etc.)  
❌ **If fails:** Check resource group name in portal

---

### Step 3: Container App
```powershell
az containerapp list --resource-group "kraftd-rg" --query "[].name" -o table
```

✅ **Expected:** See "kraftd-backend" listed  
❌ **If fails:** Verify container app exists in portal

---

### Step 4: Static Web App
```powershell
az staticwebapp list --resource-group "kraftd-rg" --query "[].name" -o table
```

✅ **Expected:** See "kraftd-frontend" listed  
❌ **If fails:** Verify static web app exists in portal

---

### Step 5: Cosmos DB
```powershell
az cosmosdb show --name "kraftd-cosmosdb" --resource-group "kraftd-rg" --query "name" -o tsv
```

✅ **Expected:** "kraftd-cosmosdb" returned  
❌ **If fails:** Verify Cosmos DB account exists

---

### Step 6: Frontend Build Exists
```powershell
Test-Path "c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel\frontend\dist\index.html"
```

✅ **Expected:** True  
❌ **If fails:** Need to run `npm run build` in frontend folder

---

### Step 7: Backend Docker Image
```powershell
az acr repository list --name "kraftdacr" --output table
```

✅ **Expected:** "kraftd-backend" repository listed  
❌ **If fails:** Image needs to be pushed to registry

---

## ✅ ALL PASS?

If all 7 checks pass, you're 100% ready. Sleep well.

If any fail, fix it now before sleeping. Nothing complicated - just verify resources exist.

---

## 🚀 AFTER VERIFICATION

**Tomorrow:**
- 01:00 AM: Read FINAL_PRE_LAUNCH_BRIEF.md
- 02:00 AM: Start Phase 4 with PHASE_4_PRACTICAL_EXECUTION_GUIDE.md
- 04:00 AM: Phase 4 complete
- 05:00 AM: Phase 5 go-live
- 05:30 AM: KRAFTD LIVE

**That's it. Simple. You're ready.**
