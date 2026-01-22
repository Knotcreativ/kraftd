# KraftdIntel Deployment Quick Test
# Run this script to verify critical endpoints

Write-Host "=== KRAFTDINTEL DEPLOYMENT VERIFICATION ===" -ForegroundColor Cyan
Write-Host ""

$passed = 0
$failed = 0

# Test 1: Frontend
Write-Host "[1/4] Testing Frontend (Static Web App)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://jolly-coast-03a4f4d03.4.azurestaticapps.net" -TimeoutSec 10 -SkipHttpErrorCheck -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  OK - Frontend accessible (HTTP 200)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ERROR - Status code: $($response.StatusCode)" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ERROR - $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# Test 2: API Health
Write-Host "[2/4] Testing Backend API Health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/health" -TimeoutSec 10 -SkipHttpErrorCheck -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  OK - API health endpoint responding (HTTP 200)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ERROR - Status code: $($response.StatusCode)" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ERROR - $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# Test 3: API Docs
Write-Host "[3/4] Testing API Documentation..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io/api/v1/docs" -TimeoutSec 10 -SkipHttpErrorCheck -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  OK - API documentation accessible (HTTP 200)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ERROR - Status code: $($response.StatusCode)" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ERROR - $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# Test 4: Azure CLI Check
Write-Host "[4/4] Checking Azure Resources..." -ForegroundColor Yellow
try {
    $result = az resource list --resource-group kraftdintel-rg --query "length(@)" -o tsv 2>$null
    if ($result -ge 8) {
        Write-Host "  OK - $result Azure resources found" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  WARNING - Only $result resources found (expected 8+)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ERROR - Could not query Azure resources" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "=== RESULTS ===" -ForegroundColor Cyan
Write-Host "Passed:  $passed" -ForegroundColor Green
Write-Host "Failed:  $failed" -ForegroundColor Red
Write-Host ""

if ($failed -eq 0) {
    Write-Host "SUCCESS - All critical endpoints are operational!" -ForegroundColor Green
    Write-Host ""
    Write-Host "NEXT STEPS:" -ForegroundColor Cyan
    Write-Host "1. Open Azure Portal: https://portal.azure.com"
    Write-Host "2. Go to Static Web App > Configuration"
    Write-Host "3. Verify VITE_API_URL is set correctly"
    Write-Host "4. Test authentication: Register and login at the frontend URL"
    Write-Host ""
} else {
    Write-Host "ISSUES FOUND - Review errors above" -ForegroundColor Red
    Write-Host "Check the deployment documentation for troubleshooting steps." -ForegroundColor Yellow
}
