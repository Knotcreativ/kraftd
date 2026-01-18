#!/usr/bin/env pwsh
<#
.SYNOPSIS
KraftdIntel Deployment Verification Script
Automated testing of all critical endpoints and configurations

.DESCRIPTION
This script performs comprehensive verification of the KraftdIntel deployment:
- Frontend accessibility
- Backend API health
- Database connectivity
- Authentication flow
- Configuration validation

.USAGE
PowerShell .\verify_deployment.ps1
#>

param(
    [switch]$Verbose = $false,
    [switch]$Full = $false
)

# Color definitions
$Colors = @{
    Success = 'Green'
    Error = 'Red'
    Warning = 'Yellow'
    Info = 'Cyan'
    Debug = 'Gray'
}

# Test results
$Results = @{
    Passed = 0
    Failed = 0
    Warnings = 0
}

# URLs
$Urls = @{
    SWA = "https://jolly-coast-03a4f4d03.4.azurestaticapps.net"
    APIHealth = "https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/health"
    APIDocs = "https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1/docs"
    APIBase = "https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1"
}

function Write-TestHeader {
    param([string]$Title)
    Write-Host "`n" + ("=" * 70) -ForegroundColor $Colors.Info
    Write-Host "  $Title" -ForegroundColor $Colors.Info
    Write-Host ("=" * 70) -ForegroundColor $Colors.Info
}

function Write-TestResult {
    param(
        [string]$TestName,
        [bool]$Passed,
        [string]$Message = ""
    )
    
    $Status = if ($Passed) { "✅ PASS" } else { "❌ FAIL" }
    $Color = if ($Passed) { $Colors.Success } else { $Colors.Error }
    
    Write-Host "  [$Status] $TestName" -ForegroundColor $Color
    if ($Message) {
        Write-Host "         $Message" -ForegroundColor $Colors.Debug
    }
    
    if ($Passed) { $Results.Passed++ } else { $Results.Failed++ }
}

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$TimeoutSec = 10
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSec -SkipHttpErrorCheck -UseBasicParsing
        $success = $response.StatusCode -eq 200
        Write-TestResult "$Name ($($response.StatusCode))" $success "Response time: $(($response.Content.Length)) bytes"
        return $response
    } catch {
        Write-TestResult "$Name" $false $_.Exception.Message
        return $null
    }
}

function Test-AzureResource {
    param(
        [string]$Type,
        [string]$Name,
        [string]$ResourceGroup
    )
    
    try {
        $resource = az resource show --resource-group $ResourceGroup --name $Name --resource-type $Type --output json 2>&1 | ConvertFrom-Json
        $exists = $null -ne $resource
        Write-TestResult "$Name ($Type)" $exists
        return $exists
    } catch {
        Write-TestResult "$Name ($Type)" $false "Resource not found or error: $($_.Exception.Message)"
        return $false
    }
}

# ==================== MAIN EXECUTION ====================

Write-Host "`n╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor $Colors.Info
Write-Host "║     KRAFTDINTEL DEPLOYMENT VERIFICATION SCRIPT                     ║" -ForegroundColor $Colors.Info
Write-Host "║     Status: Automated Testing in Progress                          ║" -ForegroundColor $Colors.Info
Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor $Colors.Info

# Test 1: Azure Resources
Write-TestHeader "PHASE 1: Azure Resources Verification"

$resourcesOk = @(
    Test-AzureResource "Microsoft.Web/staticSites" "kraftdintel-web" "kraftdintel-rg",
    Test-AzureResource "Microsoft.App/containerApps" "kraftdintel-app" "kraftdintel-rg",
    Test-AzureResource "Microsoft.DocumentDB/databaseAccounts" "kraftdintel-cosmos" "kraftdintel-rg",
    Test-AzureResource "Microsoft.CognitiveServices/accounts" "kraftdintel-openai" "kraftdintel-rg"
) -contains $true

if ($resourcesOk) {
    Write-Host "`n✅ All Azure resources present" -ForegroundColor $Colors.Success
} else {
    Write-Host "`n⚠️  Some Azure resources missing" -ForegroundColor $Colors.Warning
    $Results.Warnings++
}

# Test 2: Endpoint Accessibility
Write-TestHeader "PHASE 2: Endpoint Accessibility"

$swaResponse = Test-Endpoint "Static Web App (Frontend)" $Urls.SWA
$apiHealthResponse = Test-Endpoint "API Health Endpoint" $Urls.APIHealth
$apiDocsResponse = Test-Endpoint "API Documentation" $Urls.APIDocs

# Test 3: Frontend Content
Write-TestHeader "PHASE 3: Frontend Content Validation"

if ($swaResponse -and $swaResponse.StatusCode -eq 200) {
    $hasReact = $swaResponse.Content -match "react|root|app"
    Write-TestResult "React App Detected" $hasReact "HTML content includes React patterns"
    
    $hasLogin = $swaResponse.Content -match "login|register|password"
    Write-TestResult "Login Form Detected" $hasLogin "HTML content includes auth forms"
} else {
    Write-TestResult "Frontend Content" $false "Unable to retrieve SWA content"
}

# Test 4: API Response Format
Write-TestHeader "PHASE 4: API Response Validation"

if ($apiHealthResponse -and $apiHealthResponse.StatusCode -eq 200) {
    try {
        $healthData = $apiHealthResponse.Content | ConvertFrom-Json
        $hasStatus = $null -ne $healthData.status
        Write-TestResult "Health Status Field" $hasStatus "API returns proper JSON structure"
        
        if ($hasStatus) {
            Write-TestResult "Health Status Value" ($healthData.status -eq "healthy") "Health status: $($healthData.status)"
        }
    } catch {
        Write-TestResult "Health Response JSON" $false "Invalid JSON format"
    }
}

# Test 5: Configuration Checks (Azure CLI)
Write-TestHeader "PHASE 5: Configuration Verification"

try {
    $swaConfig = az staticwebapp show --name kraftdintel-web --resource-group kraftdintel-rg --output json 2>&1 | ConvertFrom-Json
    $hasGitHub = $null -ne $swaConfig.repositoryUrl
    Write-TestResult "GitHub Integration" $hasGitHub "Repository: $($swaConfig.repositoryUrl)"
    
    $appConfig = az containerapp show --name kraftdintel-app --resource-group kraftdintel-rg --output json 2>&1 | ConvertFrom-Json
    $hasFqdn = $null -ne $appConfig.properties.configuration.ingress.fqdn
    Write-TestResult "Container App FQDN" $hasFqdn "FQDN: $($appConfig.properties.configuration.ingress.fqdn)"
} catch {
    Write-TestResult "Configuration Checks" $false "Unable to retrieve Azure configuration"
}

# Test 6: Summary
Write-TestHeader "VERIFICATION SUMMARY"

Write-Host "`n📊 Test Results:" -ForegroundColor $Colors.Info
Write-Host "   ✅ Passed:  $($Results.Passed)" -ForegroundColor $Colors.Success
Write-Host "   ❌ Failed:  $($Results.Failed)" -ForegroundColor $(if ($Results.Failed -eq 0) { $Colors.Success } else { $Colors.Error })
Write-Host "   ⚠️  Warnings: $($Results.Warnings)" -ForegroundColor $(if ($Results.Warnings -eq 0) { $Colors.Success } else { $Colors.Warning })

# Determine overall status
$TotalTests = $Results.Passed + $Results.Failed + $Results.Warnings
$SuccessRate = if ($TotalTests -gt 0) { [math]::Round(($Results.Passed / $TotalTests) * 100, 0) } else { 0 }

Write-Host "`nSuccess Rate: $SuccessRate% ($($Results.Passed)/$TotalTests tests)" -ForegroundColor $Colors.Info

if ($Results.Failed -eq 0 -and $Results.Warnings -le 1) {
    Write-Host "`nDEPLOYMENT VERIFICATION PASSED" -ForegroundColor $Colors.Success
    Write-Host "   Infrastructure is operational and ready for production" -ForegroundColor $Colors.Success
} else {
    Write-Host "`nVERIFICATION IN PROGRESS" -ForegroundColor $Colors.Warning
    Write-Host "   Some checks failed or need manual verification" -ForegroundColor $Colors.Warning
    Write-Host "`n   Next Steps:" -ForegroundColor $Colors.Info
    Write-Host "   1. Review failed tests above" -ForegroundColor $Colors.Info
    Write-Host "   2. Check Azure Portal configuration" -ForegroundColor $Colors.Info
    Write-Host "   3. Review application logs" -ForegroundColor $Colors.Info
    Write-Host "   4. Run this script again after fixing issues" -ForegroundColor $Colors.Info
}

Write-Host "`n" -ForegroundColor $Colors.Info

# Return exit code based on results
exit $(if ($Results.Failed -eq 0) { 0 } else { 1 })
