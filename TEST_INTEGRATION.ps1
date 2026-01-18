#!/usr/bin/env powershell
<#
.SYNOPSIS
KraftdIntel Integration Testing & Verification Script
.DESCRIPTION
Comprehensive testing of backend API, frontend connectivity, and end-to-end flows
#>

param(
    [string]$ApiUrl = "https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1",
    [string]$TestEmail = "test-integration@example.com",
    [securestring]$TestPassword = (ConvertTo-SecureString "TestPass123!" -AsPlainText -Force)
)

Write-Host ""
Write-Host "========================================== KRAFTDINTEL INTEGRATION TEST SUITE ==========================================" -ForegroundColor Cyan

# Test Results Tracking
$testResults = @()

function Test-ApiEndpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [hashtable]$Headers = @{},
        [object]$Body = $null
    )
    
    Write-Host "`n  Testing: $Name" -ForegroundColor Yellow
    Write-Host "  URL: $Url" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            TimeoutSec = 10
        }
        
        if ($Body) {
            $params['Body'] = $Body | ConvertTo-Json -Depth 10
            $params['ContentType'] = 'application/json'
        }
        
        $response = Invoke-RestMethod @params -ErrorAction Stop
        
        Write-Host "  [OK] Status: 200" -ForegroundColor Green
        Write-Host "  Response: Success" -ForegroundColor Green
        
        $testResults += @{
            Test = $Name
            Status = "PASS"
            Message = "200 OK"
        }
        
        return $response
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.Value__ 
        Write-Host "  [FAIL] Status: $statusCode" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        
        $testResults += @{
            Test = $Name
            Status = "FAIL"
            Message = "$statusCode - $($_.Exception.Message)"
        }
        
        return $null
    }
}

Write-Host "`n[1/4] BACKEND CONNECTIVITY TEST" -ForegroundColor Cyan
Write-Host "---------------------------------------------------" -ForegroundColor Gray

# Test Health
Write-Host "`n  1. Health Check Endpoint" -ForegroundColor Yellow
$healthUrl = "$ApiUrl/health"
Write-Host "  GET $healthUrl" -ForegroundColor Gray

try {
    $health = Invoke-RestMethod -Uri $healthUrl -Method GET -TimeoutSec 10
    Write-Host "  [OK] Health Check: PASSED" -ForegroundColor Green
    Write-Host "  Status: $($health.status)" -ForegroundColor Green
    Write-Host "  Timestamp: $($health.timestamp)" -ForegroundColor Gray
    
    $testResults += @{
        Test = "Health Check"
        Status = "PASS"
        Message = "Backend responding correctly"
    }
}
catch {
    Write-Host "  [FAIL] Health Check: FAILED" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    
    $testResults += @{
        Test = "Health Check"
        Status = "FAIL"
        Message = $_.Exception.Message
    }
    
    Write-Host "`n  WARNING: Backend is not responding. Please ensure:" -ForegroundColor Yellow
    Write-Host "     1. Backend Container App is running" -ForegroundColor Gray
    Write-Host "     2. Network connectivity to Azure is available" -ForegroundColor Gray
    Write-Host "     3. API URL is correct: $ApiUrl" -ForegroundColor Gray
    exit 1
}

Write-Host "`n[2/4] AUTHENTICATION FLOW TEST" -ForegroundColor Cyan
Write-Host "---------------------------------------------------" -ForegroundColor Gray

# Register New User
Write-Host "`n  1. User Registration" -ForegroundColor Yellow
$registerUrl = "$ApiUrl/auth/register"
Write-Host "  POST $registerUrl" -ForegroundColor Gray

$registerBody = @{
    email = $TestEmail
    password = $TestPassword
}

$registerResponse = Test-ApiEndpoint -Name "Register" -Url $registerUrl -Method POST -Body $registerBody

if ($registerResponse) {
    $userId = $registerResponse.user_id
    Write-Host "  User ID: $userId" -ForegroundColor Cyan
} else {
    Write-Host "  INFO: Registration may have failed, attempting login..." -ForegroundColor Yellow
}

# Login
Write-Host "`n  2. User Login" -ForegroundColor Yellow
$loginUrl = "$ApiUrl/auth/login"
Write-Host "  POST $loginUrl" -ForegroundColor Gray

$loginBody = @{
    email = $TestEmail
    password = $TestPassword
}

$loginResponse = Test-ApiEndpoint -Name "Login" -Url $loginUrl -Method POST -Body $loginBody

if (-not $loginResponse) {
    Write-Host "`n  WARNING: Login failed. Authentication may be misconfigured." -ForegroundColor Yellow
    exit 1
}

$accessToken = $loginResponse.access_token
$refreshToken = $loginResponse.refresh_token

Write-Host "  [OK] Tokens Received" -ForegroundColor Green
Write-Host "     Access Token (first 20 chars): $($accessToken.Substring(0, 20))..." -ForegroundColor Gray
Write-Host "     Refresh Token (first 20 chars): $($refreshToken.Substring(0, 20))..." -ForegroundColor Gray

# Test Token Refresh
Write-Host "`n  3. Token Refresh" -ForegroundColor Yellow
$refreshUrl = "$ApiUrl/auth/refresh"
Write-Host "  POST $refreshUrl" -ForegroundColor Gray

$refreshBody = @{
    refresh_token = $refreshToken
}

$refreshResponse = Test-ApiEndpoint -Name "Token Refresh" -Url $refreshUrl -Method POST -Body $refreshBody

if ($refreshResponse) {
    $newAccessToken = $refreshResponse.access_token
    Write-Host "  [OK] New Access Token Generated" -ForegroundColor Green
    Write-Host "     Token (first 20 chars): $($newAccessToken.Substring(0, 20))..." -ForegroundColor Gray
}

Write-Host "`n[3/4] API ENDPOINTS TEST" -ForegroundColor Cyan
Write-Host "---------------------------------------------------" -ForegroundColor Gray

# Prepare Headers with Auth
$authHeaders = @{
    "Authorization" = "Bearer $accessToken"
    "Content-Type" = "application/json"
}

# List Documents
Write-Host "`n  1. List Documents" -ForegroundColor Yellow
$listUrl = "$ApiUrl/documents"
Write-Host "  GET $listUrl" -ForegroundColor Gray

try {
    $docList = Invoke-RestMethod -Uri $listUrl -Method GET -Headers $authHeaders -TimeoutSec 10
    Write-Host "  [OK] Documents Retrieved: $($docList.Count) items" -ForegroundColor Green
    
    $testResults += @{
        Test = "List Documents"
        Status = "PASS"
        Message = "$($docList.Count) documents found"
    }
}
catch {
    Write-Host "  [FAIL] Failed to list documents" -ForegroundColor Red
    
    $testResults += @{
        Test = "List Documents"
        Status = "FAIL"
        Message = $_.Exception.Message
    }
}

# Get User Profile
Write-Host "`n  2. Get User Profile" -ForegroundColor Yellow
$profileUrl = "$ApiUrl/users/profile"
Write-Host "  GET $profileUrl" -ForegroundColor Gray

try {
    $userProfile = Invoke-RestMethod -Uri $profileUrl -Method GET -Headers $authHeaders -TimeoutSec 10
    Write-Host "  [OK] Profile Retrieved" -ForegroundColor Green
    Write-Host "     Email: $($userProfile.email)" -ForegroundColor Gray
    Write-Host "     User ID: $($userProfile.user_id)" -ForegroundColor Gray
    
    $testResults += @{
        Test = "Get User Profile"
        Status = "PASS"
        Message = "Profile retrieved successfully"
    }
}
catch {
    Write-Host "  [FAIL] Failed to get profile" -ForegroundColor Red
    
    $testResults += @{
        Test = "Get User Profile"
        Status = "FAIL"
        Message = $_.Exception.Message
    }
}

# Test Workflow Endpoints
Write-Host "`n  3. Workflow API" -ForegroundColor Yellow
$workflowUrl = "$ApiUrl/workflows"
Write-Host "  GET $workflowUrl" -ForegroundColor Gray

try {
    $workflows = Invoke-RestMethod -Uri $workflowUrl -Method GET -Headers $authHeaders -TimeoutSec 10
    Write-Host "  [OK] Workflows Retrieved: $($workflows.Count) items" -ForegroundColor Green
    
    $testResults += @{
        Test = "List Workflows"
        Status = "PASS"
        Message = "$($workflows.Count) workflows found"
    }
}
catch {
    Write-Host "  [FAIL] Failed to list workflows" -ForegroundColor Red
    
    $testResults += @{
        Test = "List Workflows"
        Status = "FAIL"
        Message = $_.Exception.Message
    }
}

Write-Host "`n[4/4] FRONTEND BUILD VERIFICATION" -ForegroundColor Cyan
Write-Host "---------------------------------------------------" -ForegroundColor Gray

# Check Frontend Build
Write-Host "`n  1. Frontend Distribution Files" -ForegroundColor Yellow

$frontendDist = "frontend/dist"

if (Test-Path $frontendDist) {
    Write-Host "  [OK] dist/ folder exists" -ForegroundColor Green
    
    $files = @(
        "index.html",
        "assets"
    )
    
    foreach ($file in $files) {
        $path = Join-Path $frontendDist $file
        if (Test-Path $path) {
            Write-Host "  [OK] $file present" -ForegroundColor Green
        } else {
            Write-Host "  [FAIL] $file missing" -ForegroundColor Red
        }
    }
    
    $distSize = (Get-ChildItem -Path $frontendDist -Recurse | Measure-Object -Property Length -Sum).Sum
    $distSizeMB = [math]::Round($distSize / 1MB, 2)
    Write-Host "  Build Size: $distSizeMB MB" -ForegroundColor Gray
    
    $testResults += @{
        Test = "Frontend Build"
        Status = "PASS"
        Message = "Build files present, size: $distSizeMB MB"
    }
} else {
    Write-Host "  [FAIL] dist/ folder not found" -ForegroundColor Red
    Write-Host "  Run: npm run build" -ForegroundColor Yellow
    
    $testResults += @{
        Test = "Frontend Build"
        Status = "FAIL"
        Message = "dist/ folder not found"
    }
}

# Check GitHub Workflow
Write-Host "`n  2. GitHub Actions Configuration" -ForegroundColor Yellow

$workflowFile = ".github/workflows/deploy-frontend.yml"

if (Test-Path $workflowFile) {
    Write-Host "  [OK] GitHub Actions workflow configured" -ForegroundColor Green
    
    $testResults += @{
        Test = "GitHub Actions"
        Status = "PASS"
        Message = "Workflow file present"
    }
} else {
    Write-Host "  [FAIL] Workflow file not found" -ForegroundColor Red
    
    $testResults += @{
        Test = "GitHub Actions"
        Status = "FAIL"
        Message = "Workflow file missing"
    }
}

# Summary
Write-Host "`n"
Write-Host "========================================== TEST RESULTS SUMMARY ==========================================" -ForegroundColor Cyan

$passCount = ($testResults | Where-Object { $_.Status -eq "PASS" }).Count
$failCount = ($testResults | Where-Object { $_.Status -eq "FAIL" }).Count
$totalCount = $testResults.Count

Write-Host ""
Write-Host "  Total Tests: $totalCount" -ForegroundColor White
Write-Host "  Passed: $passCount" -ForegroundColor Green
Write-Host "  Failed: $failCount" -ForegroundColor Red
Write-Host ""

Write-Host "  Test Details:" -ForegroundColor White
foreach ($result in $testResults) {
    $statusColor = if ($result.Status -eq "PASS") { "Green" } else { "Red" }
    $statusText = if ($result.Status -eq "PASS") { "[PASS]" } else { "[FAIL]" }
    Write-Host "    $statusText $($result.Test): $($result.Message)" -ForegroundColor $statusColor
}

Write-Host ""

if ($failCount -eq 0) {
    Write-Host "================================================ ALL TESTS PASSED ================================================" -ForegroundColor Green
    Write-Host "                           READY FOR PRODUCTION DEPLOYMENT" -ForegroundColor Green
    Write-Host "" -ForegroundColor Green
} else {
    Write-Host "================================================ SOME TESTS FAILED ================================================" -ForegroundColor Yellow
    Write-Host "                          REVIEW ERRORS ABOVE AND FIX ISSUES" -ForegroundColor Yellow
    Write-Host "" -ForegroundColor Yellow
}

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Review test results above" -ForegroundColor Gray
Write-Host "  2. Fix any failing tests" -ForegroundColor Gray
Write-Host "  3. Push to GitHub: git push -u origin main" -ForegroundColor Gray
Write-Host "  4. Deploy Static Web App (see DEPLOYMENT_CHECKLIST.md)" -ForegroundColor Gray
Write-Host ""

exit (if ($failCount -eq 0) { 0 } else { 1 })
