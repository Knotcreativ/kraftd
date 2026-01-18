#!/usr/bin/env pwsh
# Get Azure Cosmos DB Keys

Write-Host "Checking Azure CLI..." -ForegroundColor Cyan
$azVersion = az --version 2>$null
if (-not $azVersion) {
    Write-Host "ERROR: Azure CLI not installed" -ForegroundColor Red
    exit 1
}

Write-Host "Azure CLI found" -ForegroundColor Green

# Check login
Write-Host "Checking Azure login..." -ForegroundColor Cyan
$account = az account show 2>$null
if (-not $account) {
    Write-Host "Not logged in. Opening browser..." -ForegroundColor Yellow
    az login
}

$account = az account show | ConvertFrom-Json
Write-Host "Logged in as: $($account.user.name)" -ForegroundColor Green

# List accounts
Write-Host "`nFetching Cosmos DB accounts..." -ForegroundColor Cyan
$accountList = az cosmosdb list -o json | ConvertFrom-Json
if ($accountList.Count -eq 0) {
    Write-Host "No Cosmos DB accounts found" -ForegroundColor Yellow
    exit 1
}

# Display options
Write-Host "`nAvailable accounts:" -ForegroundColor Cyan
for ($i = 0; $i -lt $accountList.Count; $i++) {
    Write-Host "  [$($i+1)] $($accountList[$i].name)"
}

# Select
if ($accountList.Count -eq 1) {
    $idx = 0
    Write-Host "`nSelected: $($accountList[0].name)" -ForegroundColor Green
} else {
    Write-Host ""
    $sel = Read-Host "Select (1-$($accountList.Count))"
    $idx = [int]$sel - 1
}

$selected = $accountList[$idx]
Write-Host "Selected: $($selected.name)" -ForegroundColor Green

# Get keys
Write-Host "`nRetrieving keys..." -ForegroundColor Cyan
$accountJson = az cosmosdb show --resource-group $selected.resourceGroup --name $selected.name -o json
$account = $accountJson | ConvertFrom-Json

$keysJson = az cosmosdb keys list --resource-group $selected.resourceGroup --name $selected.name -o json
$keys = $keysJson | ConvertFrom-Json

$endpoint = $account.documentEndpoint
$key = $keys.primaryMasterKey

# Show
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Cosmos DB Credentials" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Account: $($selected.name)" -ForegroundColor Cyan
Write-Host "Endpoint: $endpoint" -ForegroundColor White
Write-Host "Key: $($key.Substring(0, 20))..." -ForegroundColor White
Write-Host ""

# Save .env
Write-Host "Saving to .env..." -ForegroundColor Cyan
$envContent = "COSMOS_ENDPOINT=$endpoint`nCOSMOS_KEY=$key`nENVIRONMENT=production`nCOSMOS_MAX_RETRIES=5`nCOSMOS_TIMEOUT=60"
Set-Content -Path ".env" -Value $envContent -Encoding UTF8
Write-Host "Saved to: $(Get-Location)\.env" -ForegroundColor Green

# Init?
Write-Host ""
Write-Host "Initialize containers? (y/n): " -NoNewline
$init = Read-Host
if ($init -eq 'y') {
    Write-Host "Running init..." -ForegroundColor Cyan
    python scripts/init_cosmos.py --production
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
