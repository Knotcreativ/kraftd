#!/usr/bin/env pwsh
# Backend startup script with automatic restart on failure

$backendDir = "c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel\backend"
$maxRestarts = 5
$restartCount = 0

Write-Host "🚀 Starting KraftdIntel Backend Server..." -ForegroundColor Cyan
Write-Host "Location: $backendDir" -ForegroundColor Gray

Set-Location $backendDir

# Activate virtual environment
.venv\Scripts\Activate.ps1

while ($restartCount -lt $maxRestarts) {
    Write-Host "`n📌 Attempt $($restartCount + 1) of $maxRestarts" -ForegroundColor Yellow
    Write-Host "Starting backend..." -ForegroundColor Cyan
    
    # Start the server - capture exit code
    python -m uvicorn main:app --host 127.0.0.1 --port 8000 --log-level info --reload
    
    $exitCode = $LASTEXITCODE
    Write-Host "❌ Backend exited with code: $exitCode" -ForegroundColor Red
    
    if ($exitCode -ne 0) {
        $restartCount++
        if ($restartCount -lt $maxRestarts) {
            Write-Host "⏳ Waiting 5 seconds before restart..." -ForegroundColor Yellow
            Start-Sleep -Seconds 5
        }
    }
}

Write-Host "`n⛔ Max restart attempts reached. Backend failed to stay running." -ForegroundColor Red
Write-Host "Check backend/main.py and logs for errors." -ForegroundColor Red
