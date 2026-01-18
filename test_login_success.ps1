# LOGIN SUCCESS FEATURE - AUTOMATED TEST SCRIPT
# Tests registration, login, token validation, and error handling

$ErrorActionPreference = "Stop"
$baseUrl = "http://127.0.0.1:8000/api/v1"
$testEmail = "testuser$(Get-Random -Minimum 1000 -Maximum 9999)@example.com"
$testPassword = "SecurePass123"
$testName = "Test User"

Write-Host "`n========================================"
Write-Host "LOGIN SUCCESS FEATURE - AUTOMATED TEST"
Write-Host "========================================`n"

Write-Host "Backend URL: $baseUrl"
Write-Host "Test Email:  $testEmail"
Write-Host "Test Pass:   $testPassword`n"

# PHASE 1: TEST REGISTRATION
Write-Host "[1/5] TESTING REGISTRATION ENDPOINT"
Write-Host "-----------------------------------"

try {
    $registerPayload = @{
        email = $testEmail
        password = $testPassword
        name = $testName
        acceptTerms = $true
        acceptPrivacy = $true
    } | ConvertTo-Json

    Write-Host "Sending registration request..." -ForegroundColor Gray
    Write-Host "  Email: $testEmail" -ForegroundColor Gray
    Write-Host "  Password: $testPassword" -ForegroundColor Gray
    Write-Host "  Name: $testName" -ForegroundColor Gray

    $registerResponse = Invoke-WebRequest `
        -Uri "$baseUrl/auth/register" `
        -Method POST `
        -ContentType "application/json" `
        -Body $registerPayload

    $registerData = $registerResponse.Content | ConvertFrom-Json

    Write-Host "[OK] Registration Successful!" -ForegroundColor Green
    Write-Host "     Status: $($registerResponse.StatusCode)"
    Write-Host "     Access Token: $($registerData.access_token.Substring(0, 20))..."
    Write-Host "     Token Type: $($registerData.token_type)"
    Write-Host "     Expires In: $($registerData.expires_in) seconds`n"

    if (-not $registerData.access_token) {
        throw "No access token returned"
    }

    if (-not $registerData.refresh_token) {
        throw "No refresh token returned"
    }

    $accessToken = $registerData.access_token
    $refreshToken = $registerData.refresh_token

} catch {
    Write-Host "[FAIL] Registration Test FAILED" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# ============================================================================
# PHASE 2: TEST LOGIN
# ============================================================================

Write-Host "`n[2/5] TESTING LOGIN ENDPOINT" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow

try {
    $loginPayload = @{
        email = $testEmail
        password = $testPassword
    } | ConvertTo-Json

    Write-Host "Sending login request..." -ForegroundColor Gray
    Write-Host "  Email: $testEmail" -ForegroundColor Gray
    Write-Host "  Password: $testPassword" -ForegroundColor Gray

    $loginResponse = Invoke-WebRequest `
        -Uri "$baseUrl/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body $loginPayload

    $loginData = $loginResponse.Content | ConvertFrom-Json

    Write-Host "`n✓ Login Successful!" -ForegroundColor Green
    Write-Host "  Status: $($loginResponse.StatusCode)" -ForegroundColor Green
    Write-Host "  Response:" -ForegroundColor Green
    Write-Host "    - Access Token: $($loginData.access_token.Substring(0, 20))..." -ForegroundColor Green
    Write-Host "    - Token Type: $($loginData.token_type)" -ForegroundColor Green
    Write-Host "    - Expires In: $($loginData.expires_in) seconds" -ForegroundColor Green
    Write-Host "    - User Email: $($loginData.email)" -ForegroundColor Green

    if (-not $loginData.access_token) {
        throw "❌ Login failed: No access token returned"
    }

    if ($loginData.token_type -ne "bearer") {
        throw "❌ Login failed: Invalid token type (expected 'bearer', got '$($loginData.token_type)')"
    }

    $loginAccessToken = $loginData.access_token

} catch {
    Write-Host "`n❌ Login Test FAILED" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# ============================================================================
# PHASE 3: TEST TOKEN VALIDATION
# ============================================================================

Write-Host "`n[3/5] TESTING TOKEN VALIDITY" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow

try {
    Write-Host "Verifying login tokens are valid..." -ForegroundColor Gray

    # Check tokens are different for each login
    if ($accessToken -eq $loginAccessToken) {
        Write-Host "⚠ Warning: Login token is same as registration token (might be using same session)" -ForegroundColor Yellow
    } else {
        Write-Host "✓ Login token is different from registration token" -ForegroundColor Green
    }

    # Both tokens should be JWT format (3 parts separated by dots)
    $loginTokenParts = $loginAccessToken.Split('.')
    if ($loginTokenParts.Length -ne 3) {
        throw "❌ Invalid token format: Expected 3 parts, got $($loginTokenParts.Length)"
    }

    Write-Host "✓ Token format is valid (JWT with 3 parts)" -ForegroundColor Green

} catch {
    Write-Host "`n❌ Token Validation Test FAILED" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# ============================================================================
# PHASE 4: TEST PROFILE ENDPOINT (PROTECTED)
# ============================================================================

Write-Host "`n[4/5] TESTING PROTECTED ENDPOINT (Profile)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow

try {
    Write-Host "Accessing profile with login token..." -ForegroundColor Gray

    $profileResponse = Invoke-WebRequest `
        -Uri "$baseUrl/auth/profile" `
        -Method GET `
        -Headers @{
            "Authorization" = "Bearer $loginAccessToken"
        }

    $profileData = $profileResponse.Content | ConvertFrom-Json

    Write-Host "`n✓ Profile Access Successful!" -ForegroundColor Green
    Write-Host "  Status: $($profileResponse.StatusCode)" -ForegroundColor Green
    Write-Host "  Profile:" -ForegroundColor Green
    Write-Host "    - Email: $($profileData.email)" -ForegroundColor Green
    Write-Host "    - Name: $($profileData.name)" -ForegroundColor Green
    Write-Host "    - Created: $($profileData.created_at)" -ForegroundColor Green

    if ($profileData.email -ne $testEmail) {
        throw "❌ Profile email doesn't match login email"
    }

} catch {
    Write-Host "`n❌ Protected Endpoint Test FAILED" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# ============================================================================
# PHASE 5: TEST ERROR HANDLING (Wrong Password)
# ============================================================================

Write-Host "`n[5/5] TESTING ERROR HANDLING (Wrong Password)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow

try {
    Write-Host "Attempting login with wrong password..." -ForegroundColor Gray

    $wrongPasswordPayload = @{
        email = $testEmail
        password = "WrongPassword123"
    } | ConvertTo-Json

    try {
        $wrongLoginResponse = Invoke-WebRequest `
            -Uri "$baseUrl/auth/login" `
            -Method POST `
            -ContentType "application/json" `
            -Body $wrongPasswordPayload `
            -ErrorAction Stop

        throw "❌ Wrong password should have failed but succeeded!"
    } catch {
        if ($_.Exception.Response.StatusCode -eq 401 -or $_.Exception.Response.StatusCode -eq 400) {
            Write-Host "✓ Wrong password correctly rejected" -ForegroundColor Green
            Write-Host "  Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Green
            
            $errorResponse = $_.Exception.Response.Content.ReadAsStream()
            $reader = New-Object System.IO.StreamReader($errorResponse)
            $errorBody = $reader.ReadToEnd()
            $errorData = $errorBody | ConvertFrom-Json
            
            Write-Host "  Error Message: $($errorData.detail)" -ForegroundColor Green
        } else {
            throw $_
        }
    }

} catch {
    Write-Host "`n❌ Error Handling Test FAILED" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# ============================================================================
# ALL TESTS PASSED
# ============================================================================

Write-Host @"
╔════════════════════════════════════════════════════════════════════════════╗
║                    ✅ ALL TESTS PASSED SUCCESSFULLY!                      ║
╚════════════════════════════════════════════════════════════════════════════╝

Test Results:
  [✓] Phase 1: Registration endpoint works correctly
  [✓] Phase 2: Login endpoint returns tokens
  [✓] Phase 3: Tokens are in valid JWT format
  [✓] Phase 4: Protected endpoints accept login tokens
  [✓] Phase 5: Error handling works (wrong password rejected)

Login Success Feature: ✅ VERIFIED

Summary:
  ✓ User can register with email, password, and accept terms
  ✓ User can login with email and password
  ✓ Backend returns access token and refresh token
  ✓ Tokens are valid JWT format
  ✓ Tokens can be used to access protected endpoints
  ✓ Invalid credentials are properly rejected

The login success feature is working correctly!

Next: Test the frontend UI to verify:
  1. Success screen appears after login
  2. Spinner animates
  3. Auto-redirect to dashboard works

"@ -ForegroundColor Green

exit 0
