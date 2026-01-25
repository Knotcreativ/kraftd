# Azure Load Testing Script for KraftdIntel
# This script runs load tests using Azure Load Testing service

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory=$true)]
    [string]$LoadTestName,

    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId = $env:AZURE_SUBSCRIPTION_ID,

    [Parameter(Mandatory=$false)]
    [string]$TestPlanPath = "backend/tests/load_test.jmx",

    [Parameter(Mandatory=$false)]
    [string]$ConfigPath = "backend/tests/azure_load_test_config.yaml",

    [Parameter(Mandatory=$false)]
    [switch]$QuickTest,

    [Parameter(Mandatory=$false)]
    [int]$EngineInstances = 1,

    [Parameter(Mandatory=$false)]
    [switch]$Cleanup
)

# Set subscription
az account set --subscription $SubscriptionId

# Check if load testing resource exists, create if not
$loadTestResource = az load test show --name $LoadTestName --resource-group $ResourceGroup 2>$null
if (!$loadTestResource) {
    Write-Host "Creating Azure Load Testing resource: $LoadTestName"
    az load test create --name $LoadTestName --resource-group $ResourceGroup --location "uaenorth"
}

# Upload test plan
Write-Host "Uploading test plan..."
az load test test create `
    --load-test-name $LoadTestName `
    --resource-group $ResourceGroup `
    --test-id "kraftdintel-api-test" `
    --display-name "KraftdIntel API Load Test" `
    --test-plan $TestPlanPath `
    --engine-instances $EngineInstances

# Run the test
if ($QuickTest) {
    Write-Host "Running quick test..."
    $testRun = az load test run create `
        --load-test-name $LoadTestName `
        --resource-group $ResourceGroup `
        --test-id "kraftdintel-api-test" `
        --test-run-id "quick-test-$(Get-Date -Format 'yyyyMMdd-HHmmss')" `
        --display-name "Quick Load Test" `
        --description "Quick load test for KraftdIntel API"
} else {
    Write-Host "Running full load test..."
    $testRun = az load test run create `
        --load-test-name $LoadTestName `
        --resource-group $ResourceGroup `
        --test-id "kraftdintel-api-test" `
        --test-run-id "full-test-$(Get-Date -Format 'yyyyMMdd-HHmmss')" `
        --display-name "Full Load Test" `
        --description "Comprehensive load test for KraftdIntel API"
}

# Extract test run ID
$testRunId = ($testRun | ConvertFrom-Json).testRunId
Write-Host "Test run started with ID: $testRunId"

# Monitor test progress
Write-Host "Monitoring test progress..."
do {
    $status = az load test run show `
        --load-test-name $LoadTestName `
        --resource-group $ResourceGroup `
        --test-run-id $testRunId `
        --query "status" -o tsv

    Write-Host "Test status: $status"
    if ($status -eq "DONE" -or $status -eq "FAILED" -or $status -eq "STOPPED") {
        break
    }

    Start-Sleep -Seconds 30
} while ($true)

# Get test results
Write-Host "Getting test results..."
az load test run show `
    --load-test-name $LoadTestName `
    --resource-group $ResourceGroup `
    --test-run-id $testRunId

# Download detailed results
Write-Host "Downloading test results..."
az load test run download-files `
    --load-test-name $LoadTestName `
    --resource-group $ResourceGroup `
    --test-run-id $testRunId `
    --path "test-results"

# Check pass/fail criteria
$metrics = az load test run metrics list `
    --load-test-name $LoadTestName `
    --resource-group $ResourceGroup `
    --test-run-id $testRunId

Write-Host "Test metrics:"
$metrics | ConvertFrom-Json | Format-Table

# Cleanup if requested
if ($Cleanup) {
    Write-Host "Cleaning up test resources..."
    az load test test delete `
        --load-test-name $LoadTestName `
        --resource-group $ResourceGroup `
        --test-id "kraftdintel-api-test" `
        --yes
}

Write-Host "Load testing completed!"