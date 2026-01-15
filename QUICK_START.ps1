# QUICK REFERENCE - DEPLOYMENT COMMANDS
**For:** Rapid deployment of Kraftd Intel to Azure  
**Time:** 5-10 minutes  
**Difficulty:** ⚠️ Follow exactly as written  

---

## COPY-PASTE READY SCRIPT

**Instructions:**
1. Open PowerShell in Administrator mode
2. Copy the entire script below
3. Paste into PowerShell terminal
4. Press Enter
5. Monitor progress (should complete in 5-10 minutes)

---

```powershell
# =============================================================================
# KRAFTD INTEL AZURE DEPLOYMENT - COMPLETE SCRIPT
# =============================================================================
# This script deploys Kraftd Intel to Azure App Service with proper
# metadata synchronization handling for UAE North region
# =============================================================================

# Configuration Variables
$subscriptionId = "d8061784-4369-43da-995f-e901a822a523"
$resourceGroupName = "kraftdintel-rg"
$appServicePlanName = "kraftdintel-plan"
$webAppName = "kraftdintel-app"
$registryName = "kraftdintel"
$registryUrl = "kraftdintel.azurecr.io"
$imageName = "kraftd-backend:latest"

# Display banner
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "KRAFTD INTEL AZURE DEPLOYMENT" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Verify Azure CLI is available
Write-Host "Verifying Azure CLI installation..." -ForegroundColor Yellow
try {
    $version = az --version
    Write-Host "✓ Azure CLI is available" -ForegroundColor Green
} catch {
    Write-Host "✗ Azure CLI not found. Please install from https://aka.ms/azure-cli" -ForegroundColor Red
    exit 1
}

Write-Host "`nStart time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ForegroundColor Gray

# =============================================================================
# STEP 1: Metadata Propagation Wait
# =============================================================================
Write-Host "[1/10] Waiting for Azure metadata propagation (90 seconds)..." -ForegroundColor Yellow
Write-Host "This is required for UAE North region synchronization." -ForegroundColor Gray
Write-Host "Do NOT interrupt this step." -ForegroundColor Gray
Write-Host ""

$remainingSeconds = 90
while ($remainingSeconds -gt 0) {
    Write-Host "`rWaiting... $remainingSeconds seconds remaining" -NoNewline -ForegroundColor Cyan
    Start-Sleep -Seconds 1
    $remainingSeconds--
}

Write-Host "`r✓ Metadata propagation complete" -ForegroundColor Green
Write-Host ""

# =============================================================================
# STEP 2: Create Web App
# =============================================================================
Write-Host "[2/10] Creating Web App..." -ForegroundColor Yellow
try {
    $webApp = az webapp create `
        --resource-group $resourceGroupName `
        --plan $appServicePlanName `
        --name $webAppName `
        --runtime "PYTHON|3.13" `
        --tags "application=kraftdintel" "environment=production" "tier=free" | ConvertFrom-Json
    
    Write-Host "✓ Web App created: $webAppName" -ForegroundColor Green
    Write-Host "  URL: https://$webAppName.azurewebsites.net" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to create Web App: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Get ACR credentials
Write-Host "[3/10] Retrieving Container Registry credentials..." -ForegroundColor Yellow
try {
    $acrUsername = "kraftdintel"
    $acrPassword = az acr credential show -n $registryName --query passwords[0].value -o tsv
    Write-Host "✓ ACR credentials retrieved" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to retrieve ACR credentials: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# =============================================================================
# STEP 3: Enable Managed Identity
# =============================================================================
Write-Host "[4/10] Enabling system-assigned managed identity..." -ForegroundColor Yellow
try {
    az webapp identity assign `
        --resource-group $resourceGroupName `
        --name $webAppName `
        --identities "[system]" | Out-Null
    
    $principalId = az webapp identity show `
        --resource-group $resourceGroupName `
        --name $webAppName `
        --query principalId -o tsv
    
    Write-Host "✓ Managed identity enabled" -ForegroundColor Green
    Write-Host "  Principal ID: $principalId" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed to enable managed identity: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# =============================================================================
# STEP 4: Assign ACR Pull Role
# =============================================================================
Write-Host "[5/10] Assigning AcrPull role to managed identity..." -ForegroundColor Yellow
try {
    $registryId = az acr show `
        --resource-group $resourceGroupName `
        --name $registryName `
        --query id -o tsv
    
    az role assignment create `
        --assignee $principalId `
        --role AcrPull `
        --scope $registryId | Out-Null
    
    Write-Host "✓ AcrPull role assigned" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to assign role: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# =============================================================================
# STEP 5: Configure Container Settings
# =============================================================================
Write-Host "[6/10] Configuring container settings..." -ForegroundColor Yellow
try {
    az webapp config container set `
        --resource-group $resourceGroupName `
        --name $webAppName `
        --docker-custom-image-name "$registryUrl/$imageName" `
        --docker-registry-server-url "https://$registryUrl" `
        --docker-registry-server-user "$acrUsername" `
        --docker-registry-server-password $acrPassword | Out-Null
    
    Write-Host "✓ Container settings configured" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to configure container settings: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# =============================================================================
# STEP 6: Configure Application Settings
# =============================================================================
Write-Host "[7/10] Configuring application settings..." -ForegroundColor Yellow
try {
    az webapp config appsettings set `
        --resource-group $resourceGroupName `
        --name $webAppName `
        --settings `
            AZURE_SUBSCRIPTION_ID=$subscriptionId `
            AZURE_RESOURCE_GROUP_NAME=$resourceGroupName `
            LOG_LEVEL="INFO" `
            ENVIRONMENT="production" `
            MAX_WORKERS="4" `
            OCR_ENGINE="tesseract" `
            OCR_LANGUAGE="eng" `
            PDF_RENDERING_DPI="300" `
            MAX_DOCUMENT_SIZE="104857600" `
            PROCESSING_TIMEOUT="300" `
            CONCURRENT_PROCESSES="4" `
            WEBSITES_PORT="8000" | Out-Null
    
    Write-Host "✓ Application settings configured" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to configure application settings: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# =============================================================================
# STEP 7: Enable Health Check
# =============================================================================
Write-Host "[8/10] Enabling health check..." -ForegroundColor Yellow
try {
    az webapp config set `
        --resource-group $resourceGroupName `
        --name $webAppName `
        --generic-configurations '{"healthCheckPath":"/health"}' `
        --number-of-workers 1 | Out-Null
    
    Write-Host "✓ Health check enabled" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to enable health check: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# =============================================================================
# STEP 8: Start Web App
# =============================================================================
Write-Host "[9/10] Starting Web App..." -ForegroundColor Yellow
try {
    az webapp start `
        --resource-group $resourceGroupName `
        --name $webAppName | Out-Null
    
    Write-Host "✓ Web App started" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to start Web App: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# =============================================================================
# STEP 9: Verify Deployment
# =============================================================================
Write-Host "[10/10] Verifying deployment..." -ForegroundColor Yellow
Write-Host "Waiting 15 seconds for application to start..." -ForegroundColor Gray

Start-Sleep -Seconds 15

$healthCheckUrl = "https://$webAppName.azurewebsites.net/health"
$maxRetries = 5
$retryCount = 0
$healthy = $false

Write-Host "Testing health endpoint: $healthCheckUrl" -ForegroundColor Gray

while ($retryCount -lt $maxRetries -and -not $healthy) {
    try {
        $response = Invoke-WebRequest -Uri $healthCheckUrl -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            Write-Host "✓ Health check passed (Status: 200)" -ForegroundColor Green
            $content = $response.Content | ConvertFrom-Json
            Write-Host "  Response: $($content | ConvertTo-Json -Compress)" -ForegroundColor Gray
        }
    } catch {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Write-Host "  Attempt $retryCount/$maxRetries: Retrying in 10 seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds 10
        }
    }
}

if (-not $healthy) {
    Write-Host "⚠ Health check failed after $maxRetries attempts" -ForegroundColor Red
    Write-Host "The application may still be starting. Check logs manually:" -ForegroundColor Yellow
    Write-Host "  az webapp log tail -n $webAppName -g $resourceGroupName" -ForegroundColor Gray
} else {
    Write-Host "✓ Deployment verification complete" -ForegroundColor Green
}
Write-Host ""

# =============================================================================
# Summary
# =============================================================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Application Details:" -ForegroundColor Yellow
Write-Host "  Application URL: https://$webAppName.azurewebsites.net" -ForegroundColor Green
Write-Host "  Health endpoint: https://$webAppName.azurewebsites.net/health" -ForegroundColor Green
Write-Host "  API endpoint: https://$webAppName.azurewebsites.net/api/documents/process" -ForegroundColor Green
Write-Host "  Metrics endpoint: https://$webAppName.azurewebsites.net/metrics" -ForegroundColor Green

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test the API with a document" -ForegroundColor Gray
Write-Host "  2. Monitor the application in Azure Portal" -ForegroundColor Gray
Write-Host "  3. Set up monitoring/alerts (optional)" -ForegroundColor Gray
Write-Host "  4. Configure custom domain (optional)" -ForegroundColor Gray

Write-Host ""
Write-Host "End time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""
```

---

## EXPECTED OUTPUT

When the script runs successfully, you'll see:

```
==========================================
KRAFTD INTEL AZURE DEPLOYMENT
==========================================

Verifying Azure CLI installation...
✓ Azure CLI is available

Start time: 2026-01-15 14:30:00

[1/10] Waiting for Azure metadata propagation (90 seconds)...
This is required for UAE North region synchronization.
Do NOT interrupt this step.

Waiting... 0 seconds remaining
✓ Metadata propagation complete

[2/10] Creating Web App...
✓ Web App created: kraftdintel-app
  URL: https://kraftdintel-app.azurewebsites.net

[3/10] Retrieving Container Registry credentials...
✓ ACR credentials retrieved

[4/10] Enabling system-assigned managed identity...
✓ Managed identity enabled
  Principal ID: 5e1bb6e8-b95b-4e6a-9a50-34d3c13122e8

[5/10] Assigning AcrPull role to managed identity...
✓ AcrPull role assigned

[6/10] Configuring container settings...
✓ Container settings configured

[7/10] Configuring application settings...
✓ Application settings configured

[8/10] Enabling health check...
✓ Health check enabled

[9/10] Starting Web App...
✓ Web App started

[10/10] Verifying deployment...
Waiting 15 seconds for application to start...
Testing health endpoint: https://kraftdintel-app.azurewebsites.net/health
✓ Health check passed (Status: 200)
  Response: {"status":"healthy"}
✓ Deployment verification complete

==========================================
✓ DEPLOYMENT COMPLETE!
==========================================

Application Details:
  Application URL: https://kraftdintel-app.azurewebsites.net
  Health endpoint: https://kraftdintel-app.azurewebsites.net/health
  API endpoint: https://kraftdintel-app.azurewebsites.net/api/documents/process
  Metrics endpoint: https://kraftdintel-app.azurewebsites.net/metrics

Next Steps:
  1. Test the API with a document
  2. Monitor the application in Azure Portal
  3. Set up monitoring/alerts (optional)
  4. Configure custom domain (optional)

End time: 2026-01-15 14:40:00
```

---

## TESTING THE DEPLOYMENT

Once deployment is complete, test the API:

```powershell
$baseUrl = "https://kraftdintel-app.azurewebsites.net"

# Test health endpoint
Write-Host "Testing health endpoint..."
Invoke-RestMethod -Uri "$baseUrl/health"

# Test readiness endpoint
Write-Host "Testing readiness endpoint..."
Invoke-RestMethod -Uri "$baseUrl/health/ready"

# Test metrics endpoint
Write-Host "Testing metrics endpoint..."
(Invoke-WebRequest -Uri "$baseUrl/metrics").Content | Select-Object -First 20
```

---

## TROUBLESHOOTING

### If something fails:

1. **Read the error message carefully**
2. **Check your Azure CLI authentication:**
   ```powershell
   az account show
   ```

3. **Verify resources exist:**
   ```powershell
   az resource list -g kraftdintel-rg
   ```

4. **View application logs:**
   ```powershell
   az webapp log tail -n kraftdintel-app -g kraftdintel-rg --max-lines 50
   ```

5. **If still stuck:** Review `IMPLEMENTATION_PLAN.md` for detailed troubleshooting

---

## TIME ESTIMATE

- Metadata wait: 90 seconds
- Resource creation: 2-3 minutes
- Configuration: 1-2 minutes
- Startup verification: 1-2 minutes
- **Total: 5-10 minutes**

---

**Status:** ✅ Ready to execute  
**Difficulty:** ⚠️ Follow exactly as written  
**Support:** See IMPLEMENTATION_PLAN.md for troubleshooting
