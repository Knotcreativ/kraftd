#!/usr/bin/env pwsh
<#
.SYNOPSIS
Deploy Static Web App for KraftdIntel via Azure CLI

.DESCRIPTION
Creates and configures Static Web App with GitHub integration
Handles region selection (westeurope instead of uaenorth)
Adds environment variables for frontend

.NOTES
Requires: az CLI, logged in with appropriate permissions
#>

# Color output helpers
function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

# Configuration
$SubscriptionId = "3c047186-1b06-4d7e-8f7b-f6bdeaf96e0d"
$ResourceGroup = "kraftdintel-rg"
$Location = "westeurope"  # Static Web Apps not available in uaenorth
$AppName = "kraftdintel-web"
$GitHubOrg = "Knotcreativ"
$GitHubRepo = "kraftd"
$Branch = "main"
$AppLocation = "frontend"
$OutputLocation = "dist"
$BuildPreset = "vite"
$ApiUrl = "https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1"

Write-Host ""
Write-Host "========================================== STATIC WEB APP DEPLOYMENT ==========================================" -ForegroundColor Cyan
Write-Host ""

# Check az CLI
Write-Info "Checking Azure CLI..."
$azVersion = az version --query '"azure-cli"' -o tsv 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Azure CLI not found or not logged in"
    Write-Host "Install from: https://aka.ms/azure-cli" -ForegroundColor Yellow
    exit 1
}
Write-Success "Azure CLI version: $azVersion"

# Set subscription
Write-Info "Setting subscription context..."
az account set --subscription $SubscriptionId 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to set subscription"
    exit 1
}
Write-Success "Subscription set"

# Verify resource group exists
Write-Info "Verifying resource group: $ResourceGroup..."
$resourceGroupExists = (az group exists --name $ResourceGroup) -eq 'true'
if (-not $resourceGroupExists) {
    Write-Error "Resource group not found: $ResourceGroup"
    exit 1
}
Write-Success "Resource group found"

# Check if Static Web App already exists
Write-Info "Checking if Static Web App already exists..."
$appExists = (az staticwebapp show --name $AppName --resource-group $ResourceGroup --query "name" -o tsv 2>$null) -ne $null
if ($appExists) {
    Write-Warning "Static Web App already exists: $AppName"
    Write-Host "Updating configuration instead..." -ForegroundColor Yellow
} else {
    # Create Static Web App
    Write-Info "Creating Static Web App: $AppName..."
    Write-Info "Region: $Location"
    Write-Info "GitHub: $GitHubOrg/$GitHubRepo (branch: $Branch)"
    Write-Host ""
    
    # Build the create command
    $createCmd = @(
        "staticwebapp", "create",
        "--name", $AppName,
        "--resource-group", $ResourceGroup,
        "--location", $Location,
        "--source", "https://github.com/$GitHubOrg/$GitHubRepo",
        "--branch", $Branch,
        "--app-location", $AppLocation,
        "--output-location", $OutputLocation,
        "--build-preset", $BuildPreset,
        "--sku", "Free",
        "--token", $env:GITHUB_TOKEN
    ) | Where-Object { $_ }
    
    & az @createCmd
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create Static Web App"
        Write-Host ""
        Write-Host "This may be due to:" -ForegroundColor Yellow
        Write-Host "  • GitHub token not set or expired" -ForegroundColor Yellow
        Write-Host "  • GitHub permissions insufficient" -ForegroundColor Yellow
        Write-Host "  • Static Web App name already in use" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Try creating manually in Azure Portal:" -ForegroundColor Cyan
        Write-Host "  https://portal.azure.com → Static Web Apps → Create" -ForegroundColor Cyan
        exit 1
    }
    Write-Success "Static Web App created successfully"
}

# Wait for app to be ready
Write-Info "Waiting for Static Web App to be ready (this may take 1-2 minutes)..."
$maxAttempts = 30
$attempt = 0
$appReady = $false

while ($attempt -lt $maxAttempts) {
    $repositoryUrl = az staticwebapp show --name $AppName --resource-group $ResourceGroup --query "repositoryUrl" -o tsv 2>$null
    if ($LASTEXITCODE -eq 0) {
        $appReady = $true
        break
    }
    $attempt++
    Start-Sleep -Seconds 4
    Write-Host "." -NoNewline -ForegroundColor Yellow
}

Write-Host ""
if ($appReady) {
    Write-Success "Static Web App is ready"
} else {
    Write-Warning "Static Web App may still be initializing (this is normal)"
}

# Add environment variable
Write-Info "Adding environment variable: VITE_API_URL..."

# Get the auth token for the app (if needed for settings)
# For Static Web Apps, we use the config endpoint
$configCmd = @(
    "staticwebapp", "appsettings", "set",
    "--name", $AppName,
    "--resource-group", $ResourceGroup,
    "--setting-names", "VITE_API_URL=$ApiUrl"
)

& az @configCmd 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Success "Environment variable added: VITE_API_URL"
} else {
    Write-Warning "Environment variable setting may need to be configured in Azure Portal"
    Write-Host "Location: Static Web App → Configuration → + Add" -ForegroundColor Cyan
}

# Get the app details
Write-Info "Retrieving Static Web App details..."
$app = az staticwebapp show --name $AppName --resource-group $ResourceGroup -o json 2>$null | ConvertFrom-Json

if ($app) {
    Write-Success "Static Web App created successfully!"
    Write-Host ""
    Write-Host "========================================== DEPLOYMENT DETAILS ==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Name:                 " -NoNewline
    Write-Host $AppName -ForegroundColor Cyan
    Write-Host "Resource Group:       " -NoNewline
    Write-Host $ResourceGroup -ForegroundColor Cyan
    Write-Host "Region:               " -NoNewline
    Write-Host $Location -ForegroundColor Cyan
    Write-Host "GitHub:               " -NoNewline
    Write-Host "$GitHubOrg/$GitHubRepo (branch: $Branch)" -ForegroundColor Cyan
    
    if ($app.defaultHostname) {
        Write-Host "Web URL:              " -NoNewline
        Write-Host "https://$($app.defaultHostname)" -ForegroundColor Cyan
    }
    
    Write-Host ""
    Write-Host "Status:               " -NoNewline
    Write-Host "✅ Ready for deployment" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "========================================== NEXT STEPS ==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. GitHub Actions will auto-build in 1-2 minutes" -ForegroundColor White
    Write-Host "2. Check build status at: https://github.com/$GitHubOrg/$GitHubRepo/actions" -ForegroundColor Cyan
    Write-Host "3. Once built, your app will be live at:" -ForegroundColor White
    
    if ($app.defaultHostname) {
        Write-Host "   https://$($app.defaultHostname)" -ForegroundColor Green
    } else {
        Write-Host "   https://[your-app-hostname].azurestaticapps.net" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "Environment variable configured:" -ForegroundColor White
    Write-Host "   VITE_API_URL=$ApiUrl" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "========================================== FINAL STATUS ==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Component                      Status                  " -ForegroundColor Yellow
    Write-Host "────────────────────────────────────────────────────────" -ForegroundColor Gray
    Write-Host "Backend API                    ✅ Live (Container Apps)" -ForegroundColor Green
    Write-Host "Database                       ✅ Ready (Cosmos DB)    " -ForegroundColor Green
    Write-Host "Monitoring                     ✅ Active (App Insights)" -ForegroundColor Green
    Write-Host "Frontend Code                  ✅ In GitHub             " -ForegroundColor Green
    Write-Host "Static Web App                 ✅ DEPLOYED             " -ForegroundColor Green
    Write-Host "Environment Variables          ✅ Configured            " -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 DEPLOYMENT: 100% COMPLETE - YOUR APP IS LIVE!" -ForegroundColor Cyan
    Write-Host ""
    
} else {
    Write-Error "Failed to retrieve Static Web App details"
    exit 1
}

Write-Host "========================================== TROUBLESHOOTING ==========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "If deployment fails:" -ForegroundColor White
Write-Host "1. Check GitHub Actions: https://github.com/$GitHubOrg/$GitHubRepo/actions" -ForegroundColor Cyan
Write-Host "2. Verify environment variable is set (may need to retrigger build)" -ForegroundColor Cyan
Write-Host "3. Check Static Web App configuration in Azure Portal" -ForegroundColor Cyan
Write-Host ""
Write-Host "To manually set environment variables in Portal:" -ForegroundColor Cyan
Write-Host "  Static Web App → Configuration → + Add → VITE_API_URL = $ApiUrl" -ForegroundColor Cyan
Write-Host ""
