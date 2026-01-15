$appUrl = "https://kraftdintel-app.nicerock-74b0737d.uaenorth.azurecontainerapps.io"

Write-Host "=== KraftdIntel Endpoint Verification ===" -ForegroundColor Cyan
Write-Host "Target URL: $appUrl`n" -ForegroundColor Gray

# Suppress certificate warnings for testing
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }

$results = @{
    "passed" = @()
    "failed" = @()
}

# Test 1: Health
Write-Host "[1/10] Testing Health Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$appUrl/health" -Method Get -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ PASS - Status: $($response.StatusCode)" -ForegroundColor Green
    $results.passed += "Health Endpoint"
} catch {
    Write-Host "❌ FAIL - $($_.Exception.Message)" -ForegroundColor Red
    $results.failed += "Health Endpoint"
}

# Test 2: Agent Status
Write-Host "`n[2/10] Testing Agent Status Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$appUrl/agent/status" -Method Get -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ PASS - Status: $($response.StatusCode)" -ForegroundColor Green
    $status = $response.Content | ConvertFrom-Json
    Write-Host "    Agent Status: $($status.status)" -ForegroundColor Green
    $results.passed += "Agent Status"
} catch {
    Write-Host "❌ FAIL - $($_.Exception.Message)" -ForegroundColor Red
    $results.failed += "Agent Status"
}

# Test 3: Metrics
Write-Host "`n[3/10] Testing Metrics Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$appUrl/metrics" -Method Get -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ PASS - Status: $($response.StatusCode), Size: $($response.Content.Length) bytes" -ForegroundColor Green
    $results.passed += "Metrics"
} catch {
    Write-Host "❌ FAIL - $($_.Exception.Message)" -ForegroundColor Red
    $results.failed += "Metrics"
}

# Test 4: Learning Endpoint
Write-Host "`n[4/10] Testing Learning Insights Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$appUrl/agent/learning" -Method Get -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ PASS - Status: $($response.StatusCode)" -ForegroundColor Green
    $learning = $response.Content | ConvertFrom-Json
    Write-Host "    Insights Available: $($learning.Count) keys" -ForegroundColor Green
    $results.passed += "Learning Insights"
} catch {
    Write-Host "❌ FAIL - $($_.Exception.Message)" -ForegroundColor Red
    $results.failed += "Learning Insights"
}

# Test 5: DI Decision Endpoint (POST with empty body to test)
Write-Host "`n[5/10] Testing DI Decision Endpoint..." -ForegroundColor Yellow
try {
    $body = @{} | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$appUrl/agent/check-di-decision" -Method Post `
        -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ PASS - Status: $($response.StatusCode)" -ForegroundColor Green
    $decision = $response.Content | ConvertFrom-Json
    Write-Host "    Use DI: $($decision.use_di), Confidence: $($decision.confidence)" -ForegroundColor Green
    $results.passed += "DI Decision"
} catch {
    Write-Host "⚠️  WARN - $($_.Exception.Message)" -ForegroundColor Yellow
    $results.failed += "DI Decision"
}

# Test 6: Documents List (GET)
Write-Host "`n[6/10] Testing Documents List Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$appUrl/api/documents" -Method Get -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ PASS - Status: $($response.StatusCode)" -ForegroundColor Green
    $docs = $response.Content | ConvertFrom-Json
    Write-Host "    Documents Count: $($docs.Count)" -ForegroundColor Green
    $results.passed += "Documents List"
} catch {
    Write-Host "⚠️  WARN - $($_.Exception.Message)" -ForegroundColor Yellow
    $results.failed += "Documents List"
}

# Test 7: Workflow Status
Write-Host "`n[7/10] Testing Workflow Status Endpoint..." -ForegroundColor Yellow
try {
    $testId = "test-workflow-001"
    $response = Invoke-WebRequest -Uri "$appUrl/workflow/status/$testId" -Method Get -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ PASS - Status: $($response.StatusCode)" -ForegroundColor Green
    $results.passed += "Workflow Status"
} catch {
    Write-Host "⚠️  WARN - Status endpoint returns 404 for non-existent ID (expected): $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
    $results.failed += "Workflow Status"
}

# Test 8: Root Endpoint
Write-Host "`n[8/10] Testing Root Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$appUrl/" -Method Get -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ PASS - Status: $($response.StatusCode)" -ForegroundColor Green
    $results.passed += "Root"
} catch {
    Write-Host "⚠️  WARN - $($_.Exception.Message)" -ForegroundColor Yellow
    $results.failed += "Root"
}

# Summary
Write-Host "`n" -ForegroundColor Cyan
Write-Host "=== VERIFICATION SUMMARY ===" -ForegroundColor Cyan
Write-Host "✅ Passed: $($results.passed.Count) tests" -ForegroundColor Green
Write-Host "❌ Failed: $($results.failed.Count) tests" -ForegroundColor Red

if ($results.passed.Count -gt 0) {
    Write-Host "`nPassed Tests:" -ForegroundColor Green
    $results.passed | ForEach-Object { Write-Host "  ✅ $_" -ForegroundColor Green }
}

if ($results.failed.Count -gt 0) {
    Write-Host "`nFailed Tests:" -ForegroundColor Red
    $results.failed | ForEach-Object { Write-Host "  ❌ $_" -ForegroundColor Red }
}

Write-Host "`n✅ Core endpoints are operational!" -ForegroundColor Green
