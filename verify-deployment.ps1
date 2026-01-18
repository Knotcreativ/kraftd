#!/usr/bin/env powershell
<#
.SYNOPSIS
Verify and configure Kraftd Static Web App deployment
.DESCRIPTION
Checks if Static Web App exists, gets details, and configures environment variables
#>

$ErrorActionPreference = 'Continue'

Write-Host ""
Write-Host "=========================================== KRAFTD SWA VERIFICATION ==========================================" -ForegroundColor Cyan
Write-Host ""

# Variables
$AppName = "kraftdintel-web"
$ResourceGroup = "kraftdintel-rg"
$ApiUrl = "https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1"

# Step 1: Check account
Write-Host "Step 1: Checking Azure authentication..." -ForegroundColor Yellow
$account = az account show --query "user.name" -o tsv 2>$null
if ($account) {
    Write-Host "✅ Logged in as: $account" -ForegroundColor Green
} else {
    Write-Host "❌ Not logged in. Attempting device code login..." -ForegroundColor Red
    Write-Host ""
    Write-Host "Opening browser for authentication..." -ForegroundColor Cyan
    Write-Host "You will see a device code. Copy it and paste in the browser window that opens." -ForegroundColor Gray
    Write-Host ""
    az login --use-device-code
    Write-Host ""
}

# Step 2: Check if Static Web App exists
Write-Host "Step 2: Checking Static Web App '$AppName'..." -ForegroundColor Yellow
$app = az staticwebapp show --name $AppName --resource-group $ResourceGroup --query "{name:name, status:status, defaultHostname:defaultHostname, location:location}" 2>$null | ConvertFrom-Json

if ($app) {
    Write-Host "✅ Static Web App found!" -ForegroundColor Green
    Write-Host "   Name: $($app.name)"
    Write-Host "   Status: $($app.status)"
    Write-Host "   URL: https://$($app.defaultHostname)"
    Write-Host "   Region: $($app.location)"
} else {
    Write-Host "❌ Static Web App not found. Creating..." -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Creating Static Web App (this may take 2-3 minutes)..." -ForegroundColor Cyan
    az staticwebapp create `
        --name $AppName `
        --resource-group $ResourceGroup `
        --location westeurope `
        --source https://github.com/Knotcreativ/kraftd `
        --branch main `
        --app-location frontend `
        --output-location dist `
        --build-preset vite `
        --sku Free
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Static Web App created successfully!" -ForegroundColor Green
        $app = az staticwebapp show --name $AppName --resource-group $ResourceGroup --query "{name:name, defaultHostname:defaultHostname}" 2>$null | ConvertFrom-Json
        Write-Host "   URL: https://$($app.defaultHostname)"
    } else {
        Write-Host "❌ Failed to create Static Web App" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Step 3: Configure environment variables
Write-Host "Step 3: Configuring environment variables..." -ForegroundColor Yellow

Write-Host "Setting VITE_API_URL to: $ApiUrl" -ForegroundColor Cyan

az staticwebapp appsettings set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --setting-names VITE_API_URL="$ApiUrl" 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Environment variable set successfully!" -ForegroundColor Green
} else {
    Write-Host "⚠️ Could not set via appsettings, will be set via Portal configuration" -ForegroundColor Yellow
}

Write-Host ""

# Step 4: Verify settings
Write-Host "Step 4: Verifying configuration..." -ForegroundColor Yellow

$settings = az staticwebapp appsettings list --name $AppName --resource-group $ResourceGroup 2>$null | ConvertFrom-Json
if ($settings) {
    Write-Host "✅ Application settings:" -ForegroundColor Green
    $settings | ForEach-Object {
        Write-Host "   - $($_.name) = $($_.value)" -ForegroundColor Cyan
    }
} else {
    Write-Host "⚠️ Could not retrieve settings (may need to configure in Portal)" -ForegroundColor Yellow
}

Write-Host ""

# Step 5: Get final details
Write-Host "Step 5: Final deployment status..." -ForegroundColor Yellow

$appDetails = az staticwebapp show --name $AppName --resource-group $ResourceGroup --query "{name:name, status:status, defaultHostname:defaultHostname, repositoryUrl:repositoryUrl, buildId:buildId}" 2>$null | ConvertFrom-Json

if ($appDetails) {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                    DEPLOYMENT COMPLETE                    ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Static Web App Details:" -ForegroundColor Green
    Write-Host "  Name:           $($appDetails.name)"
    Write-Host "  Status:         $($appDetails.status)"
    Write-Host "  Frontend URL:   https://$($appDetails.defaultHostname)"
    Write-Host "  Repository:     $($appDetails.repositoryUrl)"
    Write-Host ""
    Write-Host "Backend API:" -ForegroundColor Green
    Write-Host "  URL:            $ApiUrl"
    Write-Host "  Health Check:   /health"
    Write-Host ""
    Write-Host "What's Next:" -ForegroundColor Yellow
    Write-Host "  1. Wait for GitHub Actions build (2-5 minutes)"
    Write-Host "  2. Visit: https://$($appDetails.defaultHostname)"
    Write-Host "  3. Test login with email: test@example.com"
    Write-Host "  4. Upload a document to test the flow"
    Write-Host ""
} else {
    Write-Host "❌ Could not retrieve final status" -ForegroundColor Red
}

Write-Host ""
Write-Host "=========================================== END VERIFICATION ==========================================" -ForegroundColor Cyan
Write-Host ""
