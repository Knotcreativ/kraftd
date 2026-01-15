#!/usr/bin/env powershell
# Kraftd Backend Docker Build and Deploy Script

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('build', 'run', 'push', 'deploy', 'stop', 'clean')]
    [string]$Command = 'build',
    
    [Parameter(Mandatory=$false)]
    [string]$ImageTag = 'kraftd-backend:latest',
    
    [Parameter(Mandatory=$false)]
    [string]$RegistryName = 'kraftdregistry'
)

function Build-Image {
    Write-Host "🔨 Building Docker image: $ImageTag" -ForegroundColor Cyan
    docker build -t $ImageTag .
    if ($?) {
        Write-Host "✅ Docker image built successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Docker build failed" -ForegroundColor Red
        exit 1
    }
}

function Run-Locally {
    Write-Host "🚀 Running container locally..." -ForegroundColor Cyan
    docker-compose up -d
    Start-Sleep -Seconds 3
    
    # Test health endpoint
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
        Write-Host "✅ Container running: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "📊 Access at: http://localhost:8000" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Container started, but health check failed. Check logs:" -ForegroundColor Yellow
        docker logs kraftd-backend
    }
}

function Push-ToRegistry {
    param([string]$Registry)
    
    Write-Host "📤 Pushing image to Azure Container Registry: $Registry" -ForegroundColor Cyan
    Write-Host "Note: Make sure you're logged in to Azure ACR first" -ForegroundColor Yellow
    
    $imageName = "$Registry.azurecr.io/$ImageTag"
    docker tag $ImageTag $imageName
    docker push $imageName
    
    if ($?) {
        Write-Host "✅ Image pushed successfully: $imageName" -ForegroundColor Green
    } else {
        Write-Host "❌ Push failed" -ForegroundColor Red
        exit 1
    }
}

function Deploy-ToAzure {
    Write-Host "☁️ Deploying to Azure..." -ForegroundColor Cyan
    Write-Host "Use the commands in DEPLOYMENT.md to deploy to Azure" -ForegroundColor Yellow
    Write-Host "`nQuick start:" -ForegroundColor Green
    Write-Host "  az login" -ForegroundColor Gray
    Write-Host "  az group create --name kraftd-rg --location eastus" -ForegroundColor Gray
}

function Stop-Container {
    Write-Host "🛑 Stopping Docker container..." -ForegroundColor Cyan
    docker-compose down
    Write-Host "✅ Container stopped" -ForegroundColor Green
}

function Clean-Docker {
    Write-Host "🧹 Cleaning Docker resources..." -ForegroundColor Cyan
    docker-compose down -v
    docker rmi $ImageTag -f
    Write-Host "✅ Cleanup complete" -ForegroundColor Green
}

# Main execution
switch ($Command) {
    'build' { Build-Image }
    'run' { Build-Image; Run-Locally }
    'push' { Push-ToRegistry -Registry $RegistryName }
    'deploy' { Deploy-ToAzure }
    'stop' { Stop-Container }
    'clean' { Clean-Docker }
    default { Write-Host "Unknown command: $Command" }
}
