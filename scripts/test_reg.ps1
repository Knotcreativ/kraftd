#!/usr/bin/env powershell

$output = @()

try {
    $testPayload = @{
        email = "test-$(Get-Random)@example.com"
        password = "TestPass123"
        acceptTerms = $true
        acceptPrivacy = $true
        name = "Test User"
        marketingOptIn = $false
    } | ConvertTo-Json

    $output += "Testing registration endpoint..."
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/register" `
        -Method POST -Headers @{"Content-Type"="application/json"} -Body $testPayload

    $output += "Response type: $($response.GetType().Name)"
    $output += "Response Keys: $(($response | Get-Member -MemberType NoteProperty).Name -join ', ')"
    $output += "Full Response: $($response | ConvertTo-Json)"
    
} catch {
    $output += "ERROR: $($_.Exception.Message)"
    $output += "Full error: $_"
}

$output | Out-File -FilePath "c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel\test_output.txt"
Write-Host "Test output saved to test_output.txt"
