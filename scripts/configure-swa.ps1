#!/usr/bin/env powershell
<#
.SYNOPSIS
Configure Kraftd Static Web App with environment variables
.DESCRIPTION
Sets up VITE_API_URL environment variable for frontend to connect to backend API
#>

param(
    [string]$AppName = "kraftdintel-web",
    [string]$ResourceGroup = "kraftdintel-rg",
    [string]$ApiUrl = "https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1"
)

$ErrorActionPreference = 'Continue'

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "               Kraftd Static Web App - Environment Configuration" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify SWA exists
Write-Host "Step 1: Checking if Static Web App exists..." -ForegroundColor Yellow
try {
    $app = az staticwebapp show --name $AppName --resource-group $ResourceGroup --query "{name:name, status:status, defaultHostname:defaultHostname}" 2>$null | ConvertFrom-Json -ErrorAction Stop
    
    if ($app) {
        Write-Host "✅ Static Web App found!" -ForegroundColor Green
        Write-Host "   Name: $($app.name)"
        Write-Host "   Status: $($app.status)"
        Write-Host "   URL: https://$($app.defaultHostname)"
        Write-Host ""
    } else {
        Write-Host "⚠️  Static Web App not responding. It may still be creating..." -ForegroundColor Yellow
        Write-Host "   Please wait 2-3 minutes and try again." -ForegroundColor Yellow
        Write-Host ""
        exit 0
    }
} catch {
    Write-Host "⚠️  Could not query Static Web App. It may be creating..." -ForegroundColor Yellow
    Write-Host "   Please wait 2-3 minutes and try again." -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

# Step 2: Configure environment variables
Write-Host "Step 2: Configuring environment variables..." -ForegroundColor Yellow
Write-Host "   Setting VITE_API_URL = $ApiUrl" -ForegroundColor Cyan
Write-Host ""

try {
    # Try setting via appsettings
    $result = az staticwebapp appsettings set `
        --name $AppName `
        --resource-group $ResourceGroup `
        --setting-names VITE_API_URL="$ApiUrl" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Environment variable configured successfully!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  CLI method failed, using alternative..." -ForegroundColor Yellow
        
        # Alternative: Use portal configuration
        Write-Host ""
        Write-Host "📋 MANUAL CONFIGURATION REQUIRED:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "1. Go to Azure Portal: https://portal.azure.com" -ForegroundColor Cyan
        Write-Host "2. Navigate to: Static Web Apps → $AppName" -ForegroundColor Cyan
        Write-Host "3. Click: Settings → Configuration" -ForegroundColor Cyan
        Write-Host "4. Click: + Add Application setting" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "5. Enter:" -ForegroundColor Gray
        Write-Host "   Name:  VITE_API_URL" -ForegroundColor Cyan
        Write-Host "   Value: $ApiUrl" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "6. Click: Save" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "GitHub Actions will auto-rebuild with the new environment variable." -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Error during configuration: $($_)" -ForegroundColor Yellow
}

Write-Host ""

# Step 3: Verify configuration
Write-Host "Step 3: Verifying configuration..." -ForegroundColor Yellow

try {
    $settings = az staticwebapp appsettings list --name $AppName --resource-group $ResourceGroup 2>$null
    
    if ($settings) {
        $parsed = $settings | ConvertFrom-Json
        Write-Host "✅ Current application settings:" -ForegroundColor Green
        $parsed | ForEach-Object {
            Write-Host "   - $($_.name) = $($_.value)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "⚠️  Could not retrieve settings (portal configuration may be needed)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not verify settings" -ForegroundColor Yellow
}

Write-Host ""

# Step 4: Display summary
Write-Host "═══════════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                              NEXT STEPS" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "1️⃣  GitHub Actions Build (2-5 minutes)" -ForegroundColor Yellow
Write-Host "   Monitor: https://github.com/Knotcreativ/kraftd/actions" -ForegroundColor Cyan
Write-Host ""
Write-Host "2️⃣  Access Your Application" -ForegroundColor Yellow
Write-Host "   Frontend: https://$($app.defaultHostname)" -ForegroundColor Cyan
Write-Host "   Backend:  $ApiUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "3️⃣  Verify Connection" -ForegroundColor Yellow
Write-Host "   - Login page should load" -ForegroundColor Cyan
Write-Host "   - Dashboard should show API response" -ForegroundColor Cyan
Write-Host "   - Check Application Insights for traffic" -ForegroundColor Cyan
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
