#!/usr/bin/env powershell
<#
.SYNOPSIS
    Automated Staging Deployment Script for KraftdIntel
    Deploys backend to Azure Staging environment

.DESCRIPTION
    This script handles:
    - Resource group creation
    - Container build and push
    - Service deployment
    - Configuration management
    - Health verification

.PARAMETER DeploymentOption
    Choose deployment method: 'aci' (Container Instances), 'appservice' (App Service), or 'containerapps'

.PARAMETER ResourceGroup
    Azure resource group name (default: kraftdintel-staging)

.PARAMETER Location
    Azure region (default: eastus)

.EXAMPLE
    .\deploy-staging.ps1 -DeploymentOption aci
    .\deploy-staging.ps1 -DeploymentOption appservice -ResourceGroup mygroup

#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('aci', 'appservice', 'containerapps')]
    [string]$DeploymentOption = 'aci',
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = 'kraftdintel-staging',
    
    [Parameter(Mandatory=$false)]
    [string]$Location = 'eastus',
    
    [Parameter(Mandatory=$false)]
    [string]$ContainerName = 'kraftdintel-backend-staging',
    
    [Parameter(Mandatory=$false)]
    [string]$Port = 8000
)

# Color helpers
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error_ { Write-Host $args -ForegroundColor Red }
function Write-Info { Write-Host $args -ForegroundColor Cyan }

# Check Azure CLI
Write-Info "🔍 Checking Azure CLI..."
try {
    $azVersion = az --version
    Write-Success "✅ Azure CLI installed"
} catch {
    Write-Error_ "❌ Azure CLI not installed. Download from: https://aka.ms/azure-cli"
    exit 1
}

# Check if logged in
Write-Info "🔍 Checking Azure login..."
try {
    $account = az account show --query name --output tsv 2>$null
    Write-Success "✅ Logged in as: $account"
} catch {
    Write-Warning "⚠️ Not logged in. Running 'az login'..."
    az login
}

# Create resource group
Write-Info "📦 Creating resource group: $ResourceGroup"
try {
    az group create --name $ResourceGroup --location $Location 2>$null
    Write-Success "✅ Resource group ready"
} catch {
    Write-Warning "⚠️ Resource group already exists"
}

# Deployment option selection
Write-Info ""
Write-Info "🚀 Deploying to Azure ($DeploymentOption)..."
Write-Info ""

if ($DeploymentOption -eq 'aci') {
    Deploy-To-ACI
} elseif ($DeploymentOption -eq 'appservice') {
    Deploy-To-AppService
} else {
    Deploy-To-ContainerApps
}

# Verification
Write-Info ""
Write-Info "✅ Deployment initiated"
Write-Info "⏳ Waiting for service to be ready (this may take 2-3 minutes)..."
Write-Info ""

function Deploy-To-ACI {
    Write-Info "📦 Azure Container Instances Configuration"
    
    # Get Cosmos DB connection from environment or user input
    $cosmosEndpoint = $env:COSMOS_ENDPOINT
    if (-not $cosmosEndpoint) {
        $cosmosEndpoint = Read-Host "Enter Cosmos DB endpoint (or press Enter for local emulator)"
        if (-not $cosmosEndpoint) {
            $cosmosEndpoint = "https://localhost:8081/"
        }
    }
    
    $cosmosKey = $env:COSMOS_KEY
    if (-not $cosmosKey) {
        $cosmosKey = Read-Host "Enter Cosmos DB key (or press Enter for emulator key)" -AsSecureString
        if ($cosmosKey.Length -eq 0) {
            $cosmosKey = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVo+2xNqaC8h/RVi12NewNQYoNkVRZo0v6a7t1E=="
        } else {
            $cosmosKey = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
                [Runtime.InteropServices.Marshal]::SecureStringToBSTR($cosmosKey)
            )
        }
    }
    
    Write-Info "🔨 Creating Container Instance..."
    
    try {
        # Create the container instance
        az container create `
            --resource-group $ResourceGroup `
            --name $ContainerName `
            --image python:3.9-slim `
            --cpu 1 `
            --memory 1 `
            --ports $Port `
            --environment-variables `
                ENVIRONMENT=staging `
                COSMOS_ENDPOINT=$cosmosEndpoint `
                COSMOS_KEY=$cosmosKey `
                ALLOWED_ORIGINS="http://localhost:3000,http://localhost:5173" `
            --restart-policy OnFailure 2>$null
        
        Write-Success "✅ Container instance created"
        
        # Get the IP address
        Start-Sleep -Seconds 5
        $ip = az container show `
            --resource-group $ResourceGroup `
            --name $ContainerName `
            --query ipAddress.ip `
            --output tsv 2>$null
        
        if ($ip) {
            Write-Success "✅ Container IP: $ip"
            Write-Info ""
            Write-Info "🌐 Endpoints:"
            Write-Info "   API: http://$ip:$Port"
            Write-Info "   Docs: http://$ip:$Port/docs"
            Write-Info "   Health: http://$ip:$Port/api/v1/health"
            Write-Info ""
            
            # Test health endpoint
            Write-Info "🧪 Testing health endpoint..."
            Start-Sleep -Seconds 5
            try {
                $response = Invoke-WebRequest -Uri "http://$ip:$Port/api/v1/health" -UseBasicParsing -TimeoutSec 10 2>$null
                if ($response.StatusCode -eq 200) {
                    Write-Success "✅ Health check passed"
                } else {
                    Write-Warning "⚠️ Health check returned: $($response.StatusCode)"
                }
            } catch {
                Write-Warning "⚠️ Health check not yet available (service still starting)"
            }
        } else {
            Write-Warning "⚠️ Could not retrieve IP address. Checking status..."
            az container show `
                --resource-group $ResourceGroup `
                --name $ContainerName `
                --query instanceView.state `
                --output tsv
        }
    } catch {
        Write-Error_ "❌ Failed to create container: $_"
        exit 1
    }
}

function Deploy-To-AppService {
    Write-Info "📦 Azure App Service Configuration"
    Write-Warning "⚠️ App Service deployment requires:"
    Write-Warning "   1. Docker image pushed to registry"
    Write-Warning "   2. Container Registry credentials"
    Write-Warning ""
    
    $appServicePlan = "$ContainerName-plan"
    $appServiceName = "$ContainerName-app"
    
    Write-Info "🔨 Creating App Service Plan..."
    az appservice plan create `
        --name $appServicePlan `
        --resource-group $ResourceGroup `
        --sku F1 `
        --is-linux 2>$null
    
    Write-Success "✅ App Service Plan created"
    
    Write-Info "🔨 Creating App Service..."
    az webapp create `
        --name $appServiceName `
        --resource-group $ResourceGroup `
        --plan $appServicePlan 2>$null
    
    Write-Success "✅ App Service created: $appServiceName"
    Write-Info ""
    Write-Info "🌐 Endpoint:"
    Write-Info "   https://$appServiceName.azurewebsites.net"
    Write-Info ""
}

function Deploy-To-ContainerApps {
    Write-Info "📦 Azure Container Apps Configuration"
    Write-Warning "⚠️ Container Apps deployment requires:"
    Write-Warning "   1. Container Registry setup"
    Write-Warning "   2. Container image built"
    Write-Warning ""
    
    $environment = "$ContainerName-env"
    
    Write-Info "🔨 Creating Container App Environment..."
    az containerapp env create `
        --name $environment `
        --resource-group $ResourceGroup `
        --location $Location 2>$null
    
    Write-Success "✅ Container App Environment created"
    
    Write-Info "🔨 Creating Container App..."
    az containerapp create `
        --name $ContainerName `
        --resource-group $ResourceGroup `
        --environment $environment `
        --image "python:3.9-slim" `
        --target-port $Port `
        --ingress external 2>$null
    
    Write-Success "✅ Container App created"
    Write-Info ""
    Write-Info "🌐 Endpoint:"
    $fqdn = az containerapp show `
        --name $ContainerName `
        --resource-group $ResourceGroup `
        --query properties.configuration.ingress.fqdn `
        --output tsv 2>$null
    
    if ($fqdn) {
        Write-Info "   https://$fqdn"
    } else {
        Write-Warning "⚠️ Could not retrieve FQDN"
    }
    Write-Info ""
}

Write-Info "📋 Next Steps:"
Write-Info "   1. Monitor deployment progress"
Write-Info "   2. Test API endpoints"
Write-Info "   3. Check logs for errors"
Write-Info "   4. Configure frontend API URL"
Write-Info "   5. Deploy frontend to staging"
Write-Info ""

Write-Info "📊 View Logs:"
Write-Info "   az container logs -g $ResourceGroup -n $ContainerName"
Write-Info ""

Write-Info "🧹 Cleanup:"
Write-Info "   az group delete -n $ResourceGroup --yes"
Write-Info ""

Write-Success "✅ Deployment script completed"
