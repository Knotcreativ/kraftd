# KraftdIntel Deployment Execution Plan

**Status:** Ready to Deploy  
**Date:** January 15, 2026  
**Environment:** Production (Azure Cloud)  
**Auth Status:** ✅ Authenticated (kraftdfuture@outlook.com)

---

## Pre-Deployment Checklist

✅ **Azure CLI**: Installed (2.80.0)  
✅ **Azure Authentication**: Active (Azure subscription 1)  
✅ **Subscription**: Enabled  
✅ **Deploy Script**: Present (scripts/deploy.ps1)  
✅ **Infrastructure Templates**: Present (Bicep files)  
✅ **Docker Build Script**: Present (scripts/build-docker.ps1)  

---

## Deployment Sequence

### Phase 1: Prepare Infrastructure (10 minutes)

**Step 1.1: Create Resource Group**
```powershell
$resourceGroup = "kraftdintel-rg"
$location = "eastus"
az group create --name $resourceGroup --location $location
```

**Step 1.2: Create Container Registry**
```powershell
$registryName = "kraftdintelreg"
az acr create --resource-group $resourceGroup --name $registryName --sku Basic
```

**Step 1.3: Build Docker Image**
```powershell
cd c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel
& scripts/build-docker.ps1 -ImageTag "v1.0.0"
```

### Phase 2: Deploy Infrastructure (15 minutes)

**Step 2.1: Deploy Bicep Templates (App Service + Cosmos DB)**
```powershell
az deployment group create `
  --resource-group $resourceGroup `
  --template-file infrastructure/main.bicep `
  --parameters `
    appName=kraftdintel-api `
    environment=prod `
    imageName="kraftdintel:v1.0.0"
```

**Step 2.2: Deploy Cosmos DB**
```powershell
az deployment group create `
  --resource-group $resourceGroup `
  --template-file infrastructure/cosmos-db.bicep `
  --parameters `
    accountName=kraftdintel-cosmosdb `
    databaseName=kraftdintel `
    containerName=documents `
    partitionKey="/owner_email"
```

### Phase 3: Configure Secrets (10 minutes)

**Step 3.1: Create Key Vault**
```powershell
az keyvault create --resource-group $resourceGroup --name kraftdintel-kv
```

**Step 3.2: Store Secrets**
```powershell
# JWT Secret
az keyvault secret set --vault-name kraftdintel-kv --name jwt-secret-key --value "your-secure-jwt-key"

# Cosmos DB Connection String
az keyvault secret set --vault-name kraftdintel-kv --name cosmos-db-endpoint --value "https://..."
az keyvault secret set --vault-name kraftdintel-kv --name cosmos-db-key --value "..."

# Container Registry Credentials
az keyvault secret set --vault-name kraftdintel-kv --name registry-username --value "..."
az keyvault secret set --vault-name kraftdintel-kv --name registry-password --value "..."
```

### Phase 4: Deploy Application (20 minutes)

**Step 4.1: Run Main Deployment Script**
```powershell
$imageName = "kraftdintelreg.azurecr.io/kraftdintel:v1.0.0"

cd c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel

# Deploy to Dev first (test)
& scripts/deploy.ps1 -Environment "dev" -ImageTag "v1.0.0"

# Deploy to Staging (pre-production validation)
& scripts/deploy.ps1 -Environment "staging" -ImageTag "v1.0.0"

# Deploy to Production (final)
& scripts/deploy.ps1 -Environment "prod" -ImageTag "v1.0.0"
```

### Phase 5: Setup Monitoring (10 minutes)

**Step 5.1: Deploy Application Insights**
```powershell
& scripts/setup-monitoring.ps1 -Environment prod
```

**Step 5.2: Create Alert Rules**
```powershell
# Alert rules auto-created by setup-monitoring.ps1
# Includes: Offline, Error Rate, Response Time, CPU, Memory
```

---

## Deployment Timeline

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| 1 | Prepare Infrastructure | 10 min | Ready |
| 2 | Deploy Bicep Templates | 15 min | Ready |
| 3 | Configure Secrets | 10 min | Ready |
| 4 | Deploy Application | 20 min | Ready |
| 5 | Setup Monitoring | 10 min | Ready |
| **Total** | **Full Deployment** | **65 min (~1 hour)** | **Ready** |

---

## Post-Deployment Validation

### ✓ Verify Infrastructure
```powershell
# Check resources created
az resource list --resource-group kraftdintel-rg --output table

# Verify App Service
az webapp show --resource-group kraftdintel-rg --name kraftdintel-prod

# Verify Cosmos DB
az cosmosdb show --resource-group kraftdintel-rg --name kraftdintel-cosmosdb
```

### ✓ Test API Endpoints
```powershell
# Health check
curl "https://kraftdintel-prod.azurewebsites.net/health"

# Test authentication
curl -X POST "https://kraftdintel-prod.azurewebsites.net/api/v1/auth/register" `
  -H "Content-Type: application/json" `
  -d '{"email":"test@example.com","password":"test123"}'
```

### ✓ Verify Monitoring
- Open Azure Portal → Application Insights
- Check if metrics are flowing
- Verify alerts are active
- Review dashboard

---

## Rollback Procedure (If Needed)

```powershell
# Stop current deployment
az webapp deployment slot swap --resource-group kraftdintel-rg `
  --name kraftdintel-prod --slot staging

# Or redeploy previous image
& scripts/deploy.ps1 -Environment "prod" -ImageTag "v0.9.0"
```

---

## Success Criteria

✅ All 21+ endpoints responsive  
✅ Database operations working  
✅ Authentication functional  
✅ Monitoring receiving data  
✅ Alerts configured  
✅ Logs appearing in Application Insights  
✅ Health check passing  
✅ No 5xx errors in logs  

---

## Next Steps After Deployment

1. **Week 1:** Monitor baseline performance
   - Collect 7 days of production metrics
   - Adjust alert thresholds
   - Document behavior patterns

2. **Week 2:** Begin frontend development
   - Use API_USAGE_EXAMPLES.md as reference
   - Integrate with live API
   - Build React/Vue.js frontend

3. **Week 3+:** Feature development
   - Add search functionality
   - Implement batch operations
   - Advanced integrations

---

## Support Resources

- **Deployment Guide**: [PRIORITY_4_DEPLOYMENT_GUIDE.md](PRIORITY_4_DEPLOYMENT_GUIDE.md)
- **Monitoring Guide**: [MONITORING_IMPLEMENTATION_GUIDE.md](MONITORING_IMPLEMENTATION_GUIDE.md)
- **API Documentation**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Troubleshooting**: See PRIORITY_4_DEPLOYMENT_GUIDE.md § Troubleshooting

---

**Ready to execute. Confirm to proceed with Phase 1.**
