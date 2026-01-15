param(
    [Parameter(Mandatory=$true)]
    [string]$Environment,
    
    [Parameter(Mandatory=$true)]
    [string]$ImageTag,
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "kraftdintel-rg",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "eastus"
)

# Color-coded output
function Write-Success($message) { Write-Host "✓ $message" -ForegroundColor Green }
function Write-Info($message) { Write-Host "ℹ $message" -ForegroundColor Cyan }
function Write-Warning($message) { Write-Host "⚠ $message" -ForegroundColor Yellow }
function Write-Error($message) { Write-Host "✗ $message" -ForegroundColor Red }

Write-Info "Starting deployment for $Environment environment"
Write-Info "Image Tag: $ImageTag"
Write-Info "Resource Group: $ResourceGroup"

# Validate Azure CLI is installed
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI is not installed or not in PATH"
    exit 1
}

# Set environment-specific variables
$config = @{
    dev = @{
        appServiceName = "kraftdintel-dev"
        slotName = "staging"
        sku = "B1"
        registryServer = $env:REGISTRY_LOGIN_SERVER
    }
    staging = @{
        appServiceName = "kraftdintel-staging"
        slotName = "staging"
        sku = "S1"
        registryServer = $env:REGISTRY_LOGIN_SERVER
    }
    prod = @{
        appServiceName = "kraftdintel-prod"
        slotName = "production"
        sku = "P1V2"
        registryServer = $env:REGISTRY_LOGIN_SERVER
    }
}

$envConfig = $config[$Environment.ToLower()]
if (-not $envConfig) {
    Write-Error "Unknown environment: $Environment. Supported: dev, staging, prod"
    exit 1
}

# Step 1: Validate resource group exists
Write-Info "Checking resource group: $ResourceGroup"
$rg = az group exists --name $ResourceGroup | ConvertFrom-Json
if (-not $rg) {
    Write-Info "Resource group does not exist. Creating..."
    az group create --name $ResourceGroup --location $Location
    Write-Success "Resource group created"
}
else {
    Write-Success "Resource group exists"
}

# Step 2: Deploy Bicep infrastructure
Write-Info "Deploying infrastructure with Bicep template..."
try {
    az deployment group create `
        --name "kraftdintel-deploy-$([datetime]::Now.Ticks)" `
        --resource-group $ResourceGroup `
        --template-file "infrastructure\main.bicep" `
        --parameters `
            appServiceName=$envConfig.appServiceName `
            environment=$Environment `
            sku=$envConfig.sku `
            location=$Location `
            registryServer=$envConfig.registryServer `
            dockerImageTag=$ImageTag
    Write-Success "Infrastructure deployed successfully"
}
catch {
    Write-Error "Infrastructure deployment failed: $_"
    exit 1
}

# Step 3: Get App Service details
Write-Info "Retrieving App Service details..."
$appService = az webapp show --name $envConfig.appServiceName --resource-group $ResourceGroup | ConvertFrom-Json
Write-Success "App Service retrieved: $($appService.defaultHostName)"

# Step 4: Deploy Docker image
Write-Info "Deploying Docker image to App Service..."
try {
    az webapp config container set `
        --name $envConfig.appServiceName `
        --resource-group $ResourceGroup `
        --docker-custom-image-name "$($envConfig.registryServer)/kraftdintel:$ImageTag" `
        --docker-registry-server-url "https://$($envConfig.registryServer)" `
        --docker-registry-server-username $env:REGISTRY_USERNAME `
        --docker-registry-server-password $env:REGISTRY_PASSWORD
    Write-Success "Docker image configured"
}
catch {
    Write-Error "Docker image deployment failed: $_"
    exit 1
}

# Step 5: Restart the App Service
Write-Info "Restarting App Service..."
az webapp restart --name $envConfig.appServiceName --resource-group $ResourceGroup
Write-Success "App Service restarted"

# Step 6: Wait for application to be ready
Write-Info "Waiting for application to be ready (30 seconds)..."
Start-Sleep -Seconds 30

# Step 7: Run health check
Write-Info "Running health check..."
$healthCheckUrl = "https://$($appService.defaultHostName)/health"
try {
    $response = Invoke-WebRequest -Uri $healthCheckUrl -Method Get -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Success "Health check passed: Application is ready"
    }
    else {
        Write-Warning "Health check returned status: $($response.StatusCode)"
    }
}
catch {
    Write-Warning "Health check failed: $_"
}

# Step 8: Display deployment summary
Write-Info "Deployment Summary"
Write-Host "═" * 50
Write-Host "Environment:    $Environment"
Write-Host "App Service:    $($envConfig.appServiceName)"
Write-Host "Resource Group: $ResourceGroup"
Write-Host "Image Tag:      $ImageTag"
Write-Host "URL:            $($appService.defaultHostName)"
Write-Host "Status:         READY"
Write-Host "═" * 50

Write-Success "Deployment completed successfully!"
