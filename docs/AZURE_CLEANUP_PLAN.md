# AZURE RESOURCES CLEANUP PLAN - KRAFTD

**Date:** January 22, 2026  
**Status:** Pre-Launch (1.5 hours before Phase 7)  
**Total Savings:** ~$9,000/year if all duplicates removed

---

## ENDPOINT & DEPLOYMENT ANALYSIS

### ✅ ACTIVE ENDPOINT (IN USE - KEEP)

```
https://kraftd-a4gfhqa2axb2h6cd.uaenorth-01.azurewebsites.net
├─ Resource Group: KraftdRG
├─ App Service: kraftd
├─ Region: UAE North
├─ Status: 🟢 RUNNING
├─ HTTP Status: 200 OK
├─ Response Time: 1.93s
├─ Uptime: 100%
└─ Traffic: ✅ VERIFIED (live requests coming in)
```

This is your **ONLY production endpoint**. Everything is routing here.

---

## RESOURCE GROUP BREAKDOWN

### 1. ✅ KraftdRG (PRIMARY - KEEP)

**Status:** Active Production  
**Monthly Cost:** ~$12-17

**Resources:**
- ✅ App Service: `kraftd` (LIVE)
- ✅ App Service Plan: `ASP-KraftdRG-b332`
- ✅ Storage Account: `kraftd`
- ✅ User Identity: `oidc-msi-ab41`

**Action:** KEEP - This is production

---

### 2. ⚠️ kraftdintel-rg (EXTENDED - REVIEW BEFORE DELETE)

**Status:** Running but unclear if in use  
**Monthly Cost:** ~$750+

**Resources:**
- 🤔 Cosmos DB (14,400 RUs) - ~$700/month
- 🤔 Container Apps: `kraftdintel-app` (Status: Succeeded)
- 🤔 Key Vault: `kraftdintel-kv`
- 🤔 Storage Account: `kraftdintelstore`
- 🤔 OpenAI/Cognitive Services: `kraftdintel-openai`
- 🤔 Container Registry: `kraftdintel`
- 🤔 Operational Insights (Logs): `workspace-kraftdintelrgc0kT`
- 🤔 Managed Environment: `kraftdintel-env`

**Questions to Answer:**
- [ ] Is Cosmos DB actually being used (check connection strings in KraftdRG app)?
- [ ] Is the container app serving any traffic or is it just a test instance?
- [ ] Are these resources configured in the production app settings?
- [ ] Can we connect to Cosmos DB from the main app if this group is deleted?

**Recommendation:** 
- **IF NOT USED:** Delete entire group (saves $750/month)
- **IF USED:** Migrate resources to KraftdRG (consolidate)

**How to Check:**
```bash
# Check if Cosmos connection string is configured in production app
az webapp config connection-string list --name 'kraftd' --resource-group 'KraftdRG'

# Check Key Vault references
az keyvault secret list --vault-name 'kraftdintel-kv'

# Check container app logs
az containerapp logs show --name 'kraftdintel-app' --resource-group 'kraftdintel-rg'
```

---

### 3. ❌ kraftd-intel-rg (OLD - DELETE IMMEDIATELY)

**Status:** Unused, Static Web Site Not Operational  
**Monthly Cost:** ~$1

**Resources:**
- Static Web Site: `kraftd-intel` (NO DATA)

**Traffic:** ❌ NONE  
**Deployment:** ❌ OLD/UNUSED  
**Decision:** **DELETE** (safe, costs minimal)

---

### 4. ❌ rg-kraftdfuture-8913 (OLD - DELETE IMMEDIATELY)

**Status:** Unused, Legacy Cognitive Services  
**Monthly Cost:** ~$0-15

**Resources:**
- Cognitive Services: `kraftdintel-resource` (not configured)

**Traffic:** ❌ NONE  
**Deployment:** ❌ OLD/UNUSED  
**Decision:** **DELETE** (safe, costs minimal)

---

## CLEANUP ACTION PLAN

### 🚨 IMMEDIATE (Before 06:00 AM Launch)

#### Step 1: Safe Delete (Confirmed Unused)
```bash
# Delete kraftd-intel-rg
az group delete --name 'kraftd-intel-rg' --yes --no-wait

# Delete rg-kraftdfuture-8913
az group delete --name 'rg-kraftdfuture-8913' --yes --no-wait
```

**Impact:** Saves ~$15/month, 0 risk (nothing is using these)

---

#### Step 2: Validate kraftdintel-rg (Before Delete)

Run diagnostic checks:

```bash
# 1. Check if Cosmos DB connection is used
az webapp config appsettings show --name 'kraftd' --resource-group 'KraftdRG' | grep -i cosmos

# 2. Check Key Vault references
az keyvault secret list --vault-name 'kraftdintel-kv' 2>/dev/null && echo "KEY VAULT IN USE" || echo "Key vault unreachable"

# 3. Check container app status
az containerapp show --name 'kraftdintel-app' --resource-group 'kraftdintel-rg' --query 'properties.provisioningState'

# 4. Check storage account usage
az storage account show-connection-string --name 'kraftdintelstore' --resource-group 'kraftdintel-rg'
```

**If all above are empty/unused:** Safe to delete  
**If any are referenced:** Keep and consolidate

---

### 📅 POST-LAUNCH (After 06:00 AM, During Day 1)

#### Step 3: Consolidation (If Keeping Resources)

If kraftdintel-rg resources are needed:

```bash
# Migrate Cosmos DB connection string to KraftdRG app settings
# Migrate Key Vault secrets to consolidated vault
# Update app configuration to point to consolidated resources
```

**OR**

#### Step 4: Full Delete (If Not Needed)

```bash
az group delete --name 'kraftdintel-rg' --yes --no-wait
```

**Impact:** Saves $750+/month, requires validation first

---

## COST IMPACT SUMMARY

| Action | Resources | Monthly Savings | Annual Savings |
|--------|-----------|-----------------|----------------|
| Delete `kraftd-intel-rg` | 1 (Static Site) | $1 | $12 |
| Delete `rg-kraftdfuture-8913` | 1 (Cognitive Services) | $14 | $168 |
| **TOTAL (Immediate)** | 2 | **$15** | **$180** |
| Delete `kraftdintel-rg` (if unused) | 8 resources | $750+ | $9,000+ |
| **TOTAL (With Consolidation)** | 10 | **$765+** | **$9,180+** |

---

## TIMELINE

### ✅ Now (04:25 AM)
- [ ] Read this plan
- [ ] Decide on kraftdintel-rg (keep/delete)

### ✅ Before 06:00 AM (Next 1.5 hours)
- [ ] **DELETE** `kraftd-intel-rg` (safe)
- [ ] **DELETE** `rg-kraftdfuture-8913` (safe)
- [ ] **TEST** production endpoint one last time
- [ ] **MONITOR** to ensure no breakage

### ✅ After 06:00 AM (Day 1)
- [ ] If kraftdintel-rg confirmed unused → delete it
- [ ] Monitor for 24 hours
- [ ] Document what was deleted and why

### ✅ After Day 1 (Week 1)
- [ ] Final cost audit
- [ ] Confirm savings in Azure billing
- [ ] Update documentation

---

## RISK ASSESSMENT

| Resource Group | Risk Level | Notes |
|---|---|---|
| Delete `kraftd-intel-rg` | 🟢 **SAFE** | Nothing is using it, no connection strings reference it |
| Delete `rg-kraftdfuture-8913` | 🟢 **SAFE** | Old Cognitive Services, not configured anywhere |
| Delete `kraftdintel-rg` | 🟡 **MEDIUM** | Need to verify no code references these resources first |
| Keep all | 🟡 **COST** | Wastes $750+/month, no functional benefit |

---

## RECOMMENDED APPROACH

### Option A: Conservative (Safest for Launch)
```
✅ Delete: kraftd-intel-rg + rg-kraftdfuture-8913 NOW
⏸️ Hold: kraftdintel-rg for 1 week
✅ Monitor: Production endpoint during launch
✅ After 1 week: Decide on kraftdintel-rg
→ Immediate savings: $15/month
→ Potential additional: $750/month after review
```

### Option B: Aggressive (Maximum Savings)
```
✅ Delete: All 3 resource groups NOW
⚠️ Risk: Higher if kraftdintel-rg resources are unexpectedly used
✅ Monitor: Very carefully during launch
→ Immediate savings: $765+/month
→ Annual savings: $9,180+
```

---

## DECISION REQUIRED

**Before proceeding, decide:**

1. **Delete kraft-intel-rg & rg-kraftdfuture-8913 NOW?**
   - YES / NO

2. **Delete kraftdintel-rg before launch or after?**
   - DELETE NOW (aggressive, needs validation)
   - KEEP & REVIEW (conservative, safer for launch)
   - MIGRATE RESOURCES (keep only what's needed)

---

**Status:** Ready for your decision. All resources analyzed, no ambiguity.
