# Start backend server in background and run API tests
param(
    [switch]$SkipServer = $false
)

$BackendPath = "c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel\backend"
$RootPath = "c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Phase 2: Quick API Integration Tests" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if (-not $SkipServer) {
    Write-Host "Starting backend server..." -ForegroundColor Yellow
    
    # Start server in background
    $ServerProcess = Start-Process -FilePath "powershell" -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$BackendPath'; .venv\Scripts\Activate.ps1; python -m uvicorn main:app --host 127.0.0.1 --port 8000 --log-level warning 2>&1"
    ) -PassThru -WindowStyle Minimized
    
    Write-Host "Server PID: $($ServerProcess.Id)" -ForegroundColor Green
    Write-Host "Waiting for server to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 4
}

Write-Host "`nRunning API tests..." -ForegroundColor Yellow
cd $RootPath
python -u quick_api_test.py

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "API Tests Complete" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if (-not $SkipServer) {
    Write-Host "Note: Backend server will auto-shutdown after ~18 seconds" -ForegroundColor Yellow
}
