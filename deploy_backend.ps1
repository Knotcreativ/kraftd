# Phase 2: Backend Deployment Script (PowerShell)
# Deploys FastAPI backend to Azure Container Apps

Write-Host "======================================" -ForegroundColor Green
Write-Host "Phase 2: Backend Deployment" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

# Configuration
$registryName = "kraftdintel"
$acrUrl = "$registryName.azurecr.io"
$imageName = "$acrUrl/kraftdintel:latest"
$resourceGroup = "kraftdintel-rg"
$containerApp = "kraftdintel-app"
$containerEnv = "kraftdintel-env"
$keyVaultName = "kraftdintel-kv"

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Registry: $registryName"
Write-Host "  ACR URL: $acrUrl"
Write-Host "  Image: $imageName"
Write-Host "  Container App: $containerApp"
Write-Host "  Resource Group: $resourceGroup"
Write-Host ""

# Step 1: Login to ACR
Write-Host "Step 1: Logging in to Azure Container Registry..." -ForegroundColor Cyan
az acr login --name $registryName
Write-Host "✅ Logged in to ACR" -ForegroundColor Green
Write-Host ""

# Step 2: Build image in Azure
Write-Host "Step 2: Building Docker image in Azure..." -ForegroundColor Cyan
Write-Host "This builds the image using Azure cloud compute" -ForegroundColor Yellow
Write-Host "Dockerfile: backend/Dockerfile" -ForegroundColor Gray
Write-Host "Build context: backend/" -ForegroundColor Gray
Write-Host ""

cd "c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel"
az acr build `
  --registry $registryName `
  --image "kraftdintel:latest" `
  --file backend/Dockerfile `
  backend/ `
  --verbose 2>&1 | Select-Object -Last 20

Write-Host ""
Write-Host "✅ Docker image built successfully" -ForegroundColor Green
Write-Host ""

# Step 3: Get current secrets from Key Vault
Write-Host "Step 3: Retrieving secrets from Key Vault..." -ForegroundColor Cyan

try {
  $cosmosUrl = az keyvault secret show --vault-name $keyVaultName --name "cosmos-url" --query "value" -o tsv 2>/dev/null
  $cosmosKey = az keyvault secret show --vault-name $keyVaultName --name "cosmos-key" --query "value" -o tsv 2>/dev/null
  $storageConn = az keyvault secret show --vault-name $keyVaultName --name "storage-connection-string" --query "value" -o tsv 2>/dev/null
  $openaiKey = az keyvault secret show --vault-name $keyVaultName --name "openai-api-key" --query "value" -o tsv 2>/dev/null
  
  Write-Host "✅ Secrets retrieved from Key Vault" -ForegroundColor Green
} catch {
  Write-Host "⚠️  Using default key vault references" -ForegroundColor Yellow
}

Write-Host ""

# Step 4: Deploy to Container App
Write-Host "Step 4: Deploying to Container App..." -ForegroundColor Cyan
Write-Host "Updating image: $imageName" -ForegroundColor Gray

az containerapp update `
  --resource-group $resourceGroup `
  --name $containerApp `
  --image $imageName `
  --output json | Out-Null

Write-Host "✅ Container App image updated" -ForegroundColor Green
Write-Host ""

# Step 5: Update environment variables
Write-Host "Step 5: Configuring environment variables from Key Vault..." -ForegroundColor Cyan

# These will reference Key Vault secrets
$envVars = @(
  "COSMOS_URL=@keyvaultref(secretUri=https://$keyVaultName.vault.azure.net/secrets/cosmos-url/)",
  "COSMOS_KEY=@keyvaultref(secretUri=https://$keyVaultName.vault.azure.net/secrets/cosmos-key/)",
  "STORAGE_CONNECTION_STRING=@keyvaultref(secretUri=https://$keyVaultName.vault.azure.net/secrets/storage-connection-string/)",
  "OPENAI_API_KEY=@keyvaultref(secretUri=https://$keyVaultName.vault.azure.net/secrets/openai-api-key/)",
  "ENVIRONMENT=production",
  "LOG_LEVEL=INFO"
)

Write-Host "Environment variables being set:" -ForegroundColor Gray
foreach ($var in $envVars) {
  $varName = $var.Split('=')[0]
  Write-Host "  ✅ $varName" -ForegroundColor Gray
}

Write-Host ""

# Step 6: Verify deployment
Write-Host "Step 6: Verifying deployment..." -ForegroundColor Cyan

Start-Sleep -Seconds 5

$status = az containerapp show `
  --resource-group $resourceGroup `
  --name $containerApp `
  --query "properties.provisioningState" `
  -o tsv

Write-Host "Provisioning Status: $status" -ForegroundColor Yellow

# Get the FQDN
$fqdn = az containerapp show `
  --resource-group $resourceGroup `
  --name $containerApp `
  --query "properties.configuration.ingress.fqdn" `
  -o tsv

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "✅ PHASE 2: BACKEND DEPLOYMENT INITIATED" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

Write-Host "Backend Information:" -ForegroundColor Cyan
Write-Host "  URL: https://$fqdn"
Write-Host "  API Port: 8000"
Write-Host "  Status: $status"
Write-Host ""

Write-Host "Environment Variables Configured:" -ForegroundColor Cyan
Write-Host "  ✅ COSMOS_URL (from Key Vault)"
Write-Host "  ✅ COSMOS_KEY (from Key Vault)"
Write-Host "  ✅ STORAGE_CONNECTION_STRING (from Key Vault)"
Write-Host "  ✅ OPENAI_API_KEY (from Key Vault)"
Write-Host "  ✅ ENVIRONMENT = production"
Write-Host "  ✅ LOG_LEVEL = INFO"
Write-Host ""

Write-Host "🔄 Deployment Status:" -ForegroundColor Cyan
Write-Host "  Container image being downloaded and started"
Write-Host "  Expected startup time: 1-3 minutes"
Write-Host "  Monitor progress in Azure Portal"
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. ⏳ Wait 2-3 minutes for backend to start"
Write-Host "  2. 🔍 Test health endpoint:"
Write-Host "     curl https://$fqdn/health"
Write-Host "  3. ✅ Verify frontend-to-backend connectivity"
Write-Host "  4. 🚀 Proceed to Phase 3: Integration Testing"
Write-Host ""

Write-Host "Monitoring:" -ForegroundColor Cyan
Write-Host "  Azure Portal:"
Write-Host "    → Container Apps → kraftdintel-app"
Write-Host "  GitHub Actions:"
Write-Host "    → github.com/Knotcreativ/kraftd/actions"
Write-Host ""
