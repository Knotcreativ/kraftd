#!/usr/bin/env powershell
<#
.SYNOPSIS
Deploy KraftdIntel Frontend to Azure Static Web App
#>

Write-Host "`n================================ DEPLOYMENT START ================================`n" -ForegroundColor Green

Write-Host "[1/4] Checking Prerequisites..." -ForegroundColor Cyan

# Check Node
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  [OK] Node.js: $nodeVersion" -ForegroundColor Green
}
catch {
    Write-Host "  [FAIL] Node.js not installed" -ForegroundColor Red
    exit 1
}

# Check npm
try {
    $npmVersion = npm --version 2>&1
    Write-Host "  [OK] npm: $npmVersion" -ForegroundColor Green
}
catch {
    Write-Host "  [FAIL] npm not installed" -ForegroundColor Red
    exit 1
}

# Check Git
try {
    $gitVersion = git --version 2>&1
    Write-Host "  [OK] Git installed" -ForegroundColor Green
}
catch {
    Write-Host "  [FAIL] Git not installed" -ForegroundColor Red
    exit 1
}

# Check Azure CLI
try {
    $azVersion = az --version 2>&1 | Select-Object -First 1
    Write-Host "  [OK] Azure CLI installed" -ForegroundColor Green
}
catch {
    Write-Host "  [FAIL] Azure CLI not installed" -ForegroundColor Red
    exit 1
}

Write-Host "`n[2/4] Preparing Frontend Build..." -ForegroundColor Cyan

if (Test-Path "frontend") {
    Write-Host "  [OK] frontend/ folder exists" -ForegroundColor Green
    
    Push-Location frontend
    
    if (-not (Test-Path "node_modules")) {
        Write-Host "  [*] Installing npm dependencies..." -ForegroundColor Yellow
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [FAIL] npm install failed" -ForegroundColor Red
            Pop-Location
            exit 1
        }
    }
    
    Write-Host "  [*] Building frontend..." -ForegroundColor Yellow
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [FAIL] Build failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Write-Host "  [OK] Build successful - dist/ folder ready" -ForegroundColor Green
    Pop-Location
} else {
    Write-Host "  [FAIL] frontend/ folder not found" -ForegroundColor Red
    exit 1
}

Write-Host "`n[3/4] GitHub Repository Setup..." -ForegroundColor Cyan

$repoUrl = Read-Host "Enter your GitHub repository URL"

if ($repoUrl -like "https://github.com/*") {
    Write-Host "  [OK] GitHub repository: $repoUrl" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Invalid GitHub URL" -ForegroundColor Red
    exit 1
}

Write-Host "`n[4/4] Azure Static Web App Configuration..." -ForegroundColor Cyan

Write-Host "  Please follow these steps in Azure Portal:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Step 1: Create Static Web App" -ForegroundColor White
Write-Host "    - Go to https://portal.azure.com" -ForegroundColor Gray
Write-Host "    - Search for 'Static Web Apps'" -ForegroundColor Gray
Write-Host "    - Click Create" -ForegroundColor Gray
Write-Host ""
Write-Host "  Step 2: Fill in details" -ForegroundColor White
Write-Host "    - Name: kraftdintel-web" -ForegroundColor Cyan
Write-Host "    - Resource group: kraftdintel-rg" -ForegroundColor Cyan
Write-Host "    - Region: UAE North" -ForegroundColor Cyan
Write-Host "    - Repository: $repoUrl" -ForegroundColor Cyan
Write-Host "    - Branch: main" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Step 3: Build Details" -ForegroundColor White
Write-Host "    - Build preset: React" -ForegroundColor Cyan
Write-Host "    - App location: frontend" -ForegroundColor Cyan
Write-Host "    - Output location: dist" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Step 4: Configure Environment" -ForegroundColor White
Write-Host "    - Go to Configuration in Static Web App" -ForegroundColor Gray
Write-Host "    - Add application setting:" -ForegroundColor Gray
Write-Host "      Name:  VITE_API_URL" -ForegroundColor Cyan
Write-Host "      Value: https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1" -ForegroundColor Cyan
Write-Host ""

Write-Host "`n================================ READY TO DEPLOY ================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your frontend is built and ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Create Static Web App in Azure Portal (using info above)" -ForegroundColor Gray
Write-Host "  2. Push frontend code to GitHub main branch" -ForegroundColor Gray
Write-Host "  3. GitHub Actions will automatically build and deploy" -ForegroundColor Gray
Write-Host "  4. Check deployment status in GitHub Actions tab" -ForegroundColor Gray
Write-Host ""
Write-Host "Documentation: See FRONTEND_SETUP_GUIDE.md for more details" -ForegroundColor Cyan
Write-Host ""
