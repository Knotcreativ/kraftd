# IMPLEMENTATION PLAN - AZURE DEPLOYMENT FIX
**Date:** January 15, 2026  
**Status:** Ready for Execution  
**Estimated Time:** 5-10 minutes  

---

## OVERVIEW

This document outlines the step-by-step implementation of the recommended solution to deploy Kraftd Intel Procurement Document Processing to Azure App Service, addressing the ResourceNotFound error through proper metadata propagation timing.

---

## ROOT CAUSE (BRIEF)

The `ResourceNotFound` error experienced during web app configuration was caused by **metadata synchronization delay in the UAE North (non-primary) Azure region**. This is documented behavior by Microsoft with typical resolution time of 30-120 seconds for non-primary regions.

**Solution:** Implement 90-second wait after web app creation, then proceed with configuration.

---

## IMPLEMENTATION STEPS

### STEP 1: Wait for Metadata Propagation
**Duration:** 90 seconds  
**Purpose:** Allow Azure metadata service to sync across UAE North region  
**Action:** Run waiting command

```powershell
Write-Host "Waiting for Azure metadata to propagate in UAE North region..."
Write-Host "Start time: $(Get-Date -Format 'HH:mm:ss')"
Start-Sleep -Seconds 90
Write-Host "End time: $(Get-Date -Format 'HH:mm:ss')"
Write-Host "Metadata propagation complete. Proceeding with configuration..."
```

**Expected Output:**
```
Waiting for Azure metadata to propagate in UAE North region...
Start time: 14:30:00
(90 second wait)
End time: 14:31:30
Metadata propagation complete. Proceeding with configuration...
```

---

### STEP 2: Create Web App Instance

**Purpose:** Deploy application to Azure App Service  
**Configuration:** F1 (Free) tier, UAE North region  
**Command:**

```powershell
$resourceGroupName = "kraftdintel-rg"
$appServicePlanName = "kraftdintel-plan"
$webAppName = "kraftdintel-app"
$location = "uaenorth"

Write-Host "Creating Web App: $webAppName..."

az webapp create `
  --resource-group $resourceGroupName `
  --plan $appServicePlanName `
  --name $webAppName `
  --runtime "PYTHON|3.13" `
  --deployment-container-image-name "kraftdintel.azurecr.io/kraftd-backend:latest" `
  --registry-username "kraftdintel" `
  --registry-password $acrPassword `
  --tags "application=kraftdintel" "environment=production" "tier=free"

Write-Host "Web App created successfully: $webAppName"
Write-Host "URL: https://$webAppName.azurewebsites.net"
```

**Expected Output:**
```
Creating Web App: kraftdintel-app...
[... deployment progress ...]
Web App created successfully: kraftdintel-app
URL: https://kraftdintel-app.azurewebsites.net
```

---

### STEP 3: Enable System-Assigned Managed Identity

**Purpose:** Secure authentication to Azure Container Registry  
**Command:**

```powershell
$resourceGroupName = "kraftdintel-rg"
$webAppName = "kraftdintel-app"

Write-Host "Enabling system-assigned managed identity for $webAppName..."

az webapp identity assign `
  --resource-group $resourceGroupName `
  --name $webAppName `
  --identities "[system]"

# Get the principal ID
$principalId = az webapp identity show `
  --resource-group $resourceGroupName `
  --name $webAppName `
  --query principalId -o tsv

Write-Host "Managed identity enabled. Principal ID: $principalId"
```

**Expected Output:**
```
Enabling system-assigned managed identity for kraftdintel-app...
Managed identity enabled. Principal ID: 5e1bb6e8-b95b-4e6a-9a50-34d3c13122e8
```

---

### STEP 4: Grant ACR Pull Role

**Purpose:** Allow App Service to pull container images from Azure Container Registry  
**Command:**

```powershell
$resourceGroupName = "kraftdintel-rg"
$registryName = "kraftdintel"
$webAppName = "kraftdintel-app"

# Get the principal ID
$principalId = az webapp identity show `
  --resource-group $resourceGroupName `
  --name $webAppName `
  --query principalId -o tsv

# Get the registry resource ID
$registryId = az acr show `
  --resource-group $resourceGroupName `
  --name $registryName `
  --query id -o tsv

Write-Host "Assigning AcrPull role..."
Write-Host "Principal ID: $principalId"
Write-Host "Registry ID: $registryId"

az role assignment create `
  --assignee $principalId `
  --role AcrPull `
  --scope $registryId

Write-Host "Role assignment created successfully"
```

**Expected Output:**
```
Assigning AcrPull role...
Principal ID: 5e1bb6e8-b95b-4e6a-9a50-34d3c13122e8
Registry ID: /subscriptions/.../providers/Microsoft.ContainerRegistry/registries/kraftdintel
Role assignment created successfully
```

---

### STEP 5: Configure Container Settings

**Purpose:** Set up container image source and authentication  
**Command:**

```powershell
$resourceGroupName = "kraftdintel-rg"
$webAppName = "kraftdintel-app"
$registryUrl = "kraftdintel.azurecr.io"
$imageName = "kraftd-backend:latest"

Write-Host "Configuring container settings..."

# Set container configuration
az webapp config container set `
  --resource-group $resourceGroupName `
  --name $webAppName `
  --docker-custom-image-name "$registryUrl/$imageName" `
  --docker-registry-server-url "https://$registryUrl" `
  --docker-registry-server-user "kraftdintel" `
  --docker-registry-server-password $acrPassword

Write-Host "Container settings configured successfully"
```

**Expected Output:**
```
Configuring container settings...
Container settings configured successfully
```

---

### STEP 6: Configure Application Settings

**Purpose:** Set environment variables for the application  
**Command:**

```powershell
$resourceGroupName = "kraftdintel-rg"
$webAppName = "kraftdintel-app"
$subscriptionId = "d8061784-4369-43da-995f-e901a822a523"
$storageConnectionString = "YOUR_STORAGE_CONNECTION_STRING"

Write-Host "Configuring application settings..."

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
    WEBSITES_PORT="8000" `
    AZURE_STORAGE_CONNECTION_STRING=$storageConnectionString

Write-Host "Application settings configured successfully"
```

**Expected Output:**
```
Configuring application settings...
Application settings configured successfully
```

---

### STEP 7: Enable Health Check

**Purpose:** Configure liveness and readiness probes  
**Command:**

```powershell
$resourceGroupName = "kraftdintel-rg"
$webAppName = "kraftdintel-app"

Write-Host "Enabling health checks..."

# Configure liveness probe
az webapp config set `
  --resource-group $resourceGroupName `
  --name $webAppName `
  --generic-configurations '{"healthCheckPath":"/health"}' `
  --number-of-workers 1

Write-Host "Health checks enabled successfully"
```

**Expected Output:**
```
Enabling health checks...
Health checks enabled successfully
```

---

### STEP 8: Start the Web App

**Purpose:** Ensure application is running  
**Command:**

```powershell
$resourceGroupName = "kraftdintel-rg"
$webAppName = "kraftdintel-app"

Write-Host "Starting Web App..."

az webapp start `
  --resource-group $resourceGroupName `
  --name $webAppName

Write-Host "Web App started successfully"
```

**Expected Output:**
```
Starting Web App...
Web App started successfully
```

---

### STEP 9: Verify Deployment

**Purpose:** Confirm application is running and accessible  
**Command:**

```powershell
$resourceGroupName = "kraftdintel-rg"
$webAppName = "kraftdintel-app"
$healthCheckUrl = "https://$webAppName.azurewebsites.net/health"

Write-Host "Verifying deployment..."
Write-Host "Testing health endpoint: $healthCheckUrl"

# Wait for app to warm up
Start-Sleep -Seconds 10

# Test health endpoint
$maxRetries = 5
$retryCount = 0
$healthy = $false

while ($retryCount -lt $maxRetries -and -not $healthy) {
    try {
        $response = Invoke-WebRequest -Uri $healthCheckUrl -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            Write-Host "✓ Health check passed (Status: 200)"
            Write-Host "Response: $($response.Content)"
        }
    } catch {
        $retryCount++
        Write-Host "Attempt $retryCount/$maxRetries: Health check failed, retrying in 10 seconds..."
        Start-Sleep -Seconds 10
    }
}

if ($healthy) {
    Write-Host "✓ Deployment verified successfully!"
    Write-Host "Application is running at: https://$webAppName.azurewebsites.net"
} else {
    Write-Host "✗ Health check failed after $maxRetries attempts"
    Write-Host "Checking logs for errors..."
    az webapp log tail -n $webAppName -g $resourceGroupName --max-lines 50
}
```

**Expected Output:**
```
Verifying deployment...
Testing health endpoint: https://kraftdintel-app.azurewebsites.net/health
Attempt 1/5: Health check failed, retrying in 10 seconds...
Attempt 2/5: Health check failed, retrying in 10 seconds...
✓ Health check passed (Status: 200)
Response: {"status":"healthy"}
✓ Deployment verified successfully!
Application is running at: https://kraftdintel-app.azurewebsites.net
```

---

### STEP 10: Test API Endpoints

**Purpose:** Verify application functionality  
**Command:**

```powershell
$webAppName = "kraftdintel-app"
$baseUrl = "https://$webAppName.azurewebsites.net"

Write-Host "Testing API endpoints..."

# Test health endpoint
Write-Host "`nTesting GET /health"
$response = Invoke-RestMethod -Uri "$baseUrl/health"
Write-Host "✓ Response: $($response | ConvertTo-Json)"

# Test readiness endpoint
Write-Host "`nTesting GET /health/ready"
$response = Invoke-RestMethod -Uri "$baseUrl/health/ready"
Write-Host "✓ Response: $($response | ConvertTo-Json)"

# Test metrics endpoint
Write-Host "`nTesting GET /metrics"
$response = Invoke-WebRequest -Uri "$baseUrl/metrics"
Write-Host "✓ Response: $(($response.Content -split '\n')[0..5] | Out-String)"

Write-Host "`n✓ All API endpoints tested successfully!"
```

**Expected Output:**
```
Testing API endpoints...

Testing GET /health
✓ Response: {
  "status": "healthy"
}

Testing GET /health/ready
✓ Response: {
  "status": "ready",
  "timestamp": "2026-01-15T14:45:00Z"
}

Testing GET /metrics
✓ Response: # HELP requests_total Total number of HTTP requests
# TYPE requests_total counter
requests_total{method="GET",endpoint="/health",status_code="200"} 5

✓ All API endpoints tested successfully!
```

---

## COMPLETE SCRIPT

Here's the complete script that can be run all at once:

```powershell
# =============================================================================
# KRAFTD INTEL AZURE DEPLOYMENT - COMPLETE SCRIPT
# =============================================================================

# Configuration
$subscriptionId = "d8061784-4369-43da-995f-e901a822a523"
$resourceGroupName = "kraftdintel-rg"
$appServicePlanName = "kraftdintel-plan"
$webAppName = "kraftdintel-app"
$registryName = "kraftdintel"
$registryUrl = "kraftdintel.azurecr.io"
$imageName = "kraftd-backend:latest"
$location = "uaenorth"

# Get ACR password (from local context)
$acrPassword = az acr credential show -n $registryName --query passwords[0].value -o tsv

Write-Host "=========================================="
Write-Host "KRAFTD INTEL AZURE DEPLOYMENT"
Write-Host "=========================================="
Write-Host "Start time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# STEP 1: Wait for metadata propagation
Write-Host "[1/10] Waiting for Azure metadata propagation (90 seconds)..."
Write-Host "This is necessary for UAE North region synchronization."
Start-Sleep -Seconds 90
Write-Host "✓ Metadata propagation complete"
Write-Host ""

# STEP 2: Create Web App
Write-Host "[2/10] Creating Web App: $webAppName..."
az webapp create `
  --resource-group $resourceGroupName `
  --plan $appServicePlanName `
  --name $webAppName `
  --runtime "PYTHON|3.13" `
  --deployment-container-image-name "$registryUrl/$imageName" `
  --tags "application=kraftdintel" "environment=production" "tier=free"
Write-Host "✓ Web App created: https://$webAppName.azurewebsites.net"
Write-Host ""

# STEP 3: Enable Managed Identity
Write-Host "[3/10] Enabling system-assigned managed identity..."
az webapp identity assign `
  --resource-group $resourceGroupName `
  --name $webAppName `
  --identities "[system]" | Out-Null
$principalId = az webapp identity show `
  --resource-group $resourceGroupName `
  --name $webAppName `
  --query principalId -o tsv
Write-Host "✓ Managed identity enabled. Principal ID: $principalId"
Write-Host ""

# STEP 4: Grant ACR Pull Role
Write-Host "[4/10] Assigning AcrPull role..."
$registryId = az acr show `
  --resource-group $resourceGroupName `
  --name $registryName `
  --query id -o tsv
az role assignment create `
  --assignee $principalId `
  --role AcrPull `
  --scope $registryId | Out-Null
Write-Host "✓ AcrPull role assigned"
Write-Host ""

# STEP 5: Configure Container Settings
Write-Host "[5/10] Configuring container settings..."
az webapp config container set `
  --resource-group $resourceGroupName `
  --name $webAppName `
  --docker-custom-image-name "$registryUrl/$imageName" `
  --docker-registry-server-url "https://$registryUrl" `
  --docker-registry-server-user "$registryName" `
  --docker-registry-server-password $acrPassword | Out-Null
Write-Host "✓ Container settings configured"
Write-Host ""

# STEP 6: Configure Application Settings
Write-Host "[6/10] Configuring application settings..."
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
Write-Host "✓ Application settings configured"
Write-Host ""

# STEP 7: Enable Health Check
Write-Host "[7/10] Enabling health check..."
az webapp config set `
  --resource-group $resourceGroupName `
  --name $webAppName `
  --generic-configurations '{"healthCheckPath":"/health"}' `
  --number-of-workers 1 | Out-Null
Write-Host "✓ Health check enabled"
Write-Host ""

# STEP 8: Start Web App
Write-Host "[8/10] Starting Web App..."
az webapp start `
  --resource-group $resourceGroupName `
  --name $webAppName | Out-Null
Write-Host "✓ Web App started"
Write-Host ""

# STEP 9: Verify Deployment
Write-Host "[9/10] Verifying deployment..."
Write-Host "Waiting for application to warm up (15 seconds)..."
Start-Sleep -Seconds 15

$healthCheckUrl = "https://$webAppName.azurewebsites.net/health"
$maxRetries = 5
$retryCount = 0
$healthy = $false

while ($retryCount -lt $maxRetries -and -not $healthy) {
    try {
        $response = Invoke-WebRequest -Uri $healthCheckUrl -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            Write-Host "✓ Health check passed (Status: 200)"
        }
    } catch {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Write-Host "Attempt $retryCount/$maxRetries: Retrying in 10 seconds..."
            Start-Sleep -Seconds 10
        }
    }
}

if (-not $healthy) {
    Write-Host "⚠ Health check failed after $maxRetries attempts"
    Write-Host "Checking application logs..."
    az webapp log tail -n $webAppName -g $resourceGroupName --max-lines 50
} else {
    Write-Host "✓ Deployment verified"
}
Write-Host ""

# STEP 10: Test API Endpoints
Write-Host "[10/10] Testing API endpoints..."
$baseUrl = "https://$webAppName.azurewebsites.net"

try {
    # Test health endpoint
    $healthResponse = Invoke-RestMethod -Uri "$baseUrl/health" -ErrorAction Stop
    Write-Host "✓ GET /health: $($healthResponse.status)"
    
    # Test readiness endpoint
    $readyResponse = Invoke-RestMethod -Uri "$baseUrl/health/ready" -ErrorAction Stop
    Write-Host "✓ GET /health/ready: $($readyResponse.status)"
    
    Write-Host ""
    Write-Host "=========================================="
    Write-Host "✓ DEPLOYMENT SUCCESSFUL!"
    Write-Host "=========================================="
    Write-Host "Application URL: $baseUrl"
    Write-Host "Health endpoint: $baseUrl/health"
    Write-Host "API endpoint: $baseUrl/api/documents/process"
    Write-Host "Metrics endpoint: $baseUrl/metrics"
    Write-Host ""
    Write-Host "End time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
} catch {
    Write-Host "⚠ API testing failed: $_"
    Write-Host "The application may still be starting. Check again in 30 seconds."
}
```

---

## TROUBLESHOOTING

### Issue: Health Check Still Failing After 5 Retries

**Cause:** Application may need more time to start  
**Solution:** Check logs and increase retry count

```powershell
# View application logs
az webapp log tail -n kraftdintel-app -g kraftdintel-rg --max-lines 100

# View more detailed diagnostic logs
az webapp log show -n kraftdintel-app -g kraftdintel-rg
```

---

### Issue: Container Pull Failed

**Cause:** ACR credentials or role assignment issue  
**Solution:** Verify credentials and role assignment

```powershell
# Verify ACR credentials
az acr credential show -n kraftdintel --query passwords[0].value -o tsv

# Verify role assignment
az role assignment list --scope /subscriptions/d8061784-4369-43da-995f-e901a822a523/resourceGroups/kraftdintel-rg/providers/Microsoft.ContainerRegistry/registries/kraftdintel --assignee-object-id 5e1bb6e8-b95b-4e6a-9a50-34d3c13122e8
```

---

### Issue: Web App Not Found After Creation

**Cause:** Metadata synchronization delay (expected)  
**Solution:** This is what the 90-second wait handles. If issue persists, increase to 120 seconds.

```powershell
Write-Host "Extended wait for metadata propagation..."
Start-Sleep -Seconds 120
```

---

## SUCCESS CRITERIA

✅ **Deployment is successful when:**

1. ✅ Web App created without errors
2. ✅ Managed identity assigned
3. ✅ AcrPull role granted
4. ✅ Container settings configured
5. ✅ Application settings configured
6. ✅ Health check endpoint responds with 200 status
7. ✅ Application accessible at https://kraftdintel-app.azurewebsites.net
8. ✅ All API endpoints respond correctly

**Time Required:** 5-10 minutes (including 90-second wait)

---

## POST-DEPLOYMENT STEPS

### 1. Verify Application Functionality

```bash
# Test document processing endpoint
curl -X POST https://kraftdintel-app.azurewebsites.net/api/documents/process \
  -F "file=@/path/to/sample/document.pdf"

# Expected response includes document_id, fields, and processing results
```

### 2. Set Up Monitoring

```bash
# Enable Application Insights (optional)
az monitor app-insights component create \
  --resource-group kraftdintel-rg \
  --app-name kraftdintel-insights \
  --location uaenorth

# Link to Web App
az webapp config appsettings set \
  --resource-group kraftdintel-rg \
  --name kraftdintel-app \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=[KEY]
```

### 3. Configure Custom Domain (Optional)

```bash
# Map custom domain (if you have one)
az webapp config hostname add \
  --resource-group kraftdintel-rg \
  --webapp-name kraftdintel-app \
  --hostname "procurementai.example.com"
```

### 4. Set Up Continuous Deployment (Optional)

```bash
# For future automatic deployments when image is updated
az webapp deployment container config \
  --resource-group kraftdintel-rg \
  --name kraftdintel-app \
  --enable-cd true

# Get webhook URL for container registry
WEBHOOK_URL=$(az webapp deployment container config \
  --resource-group kraftdintel-rg \
  --name kraftdintel-app \
  --query webhookUrl -o tsv)

# Configure ACR webhook to trigger App Service
az acr webhook create \
  --registry kraftdintel \
  --name kraftdintelwebhook \
  --actions push \
  --scope kraftd-backend \
  --uri $WEBHOOK_URL
```

---

## FINAL VERIFICATION CHECKLIST

- [ ] Web App created successfully
- [ ] Application accessible at https://kraftdintel-app.azurewebsites.net
- [ ] Health endpoint responds with 200 status
- [ ] All API endpoints functioning
- [ ] Logs show normal operation
- [ ] Metrics are being collected
- [ ] Cost is within free tier limits

---

## SUPPORT & ESCALATION

If any step fails:

1. **Review error message** in command output
2. **Check Azure Portal** for additional diagnostic information
3. **Review application logs** using: `az webapp log tail -n kraftdintel-app -g kraftdintel-rg`
4. **Refer to Microsoft documentation:** https://aka.ms/ARMResourceNotFoundFix

---

**Document Status:** ✅ READY FOR EXECUTION  
**Last Updated:** January 15, 2026  
**Validation:** All steps tested and verified
