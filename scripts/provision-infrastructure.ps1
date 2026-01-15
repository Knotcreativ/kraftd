param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "eastus"
)

function Write-Success($message) { Write-Host "✓ $message" -ForegroundColor Green }
function Write-Info($message) { Write-Host "ℹ $message" -ForegroundColor Cyan }
function Write-Error($message) { Write-Host "✗ $message" -ForegroundColor Red }

Write-Info "Provisioning Azure infrastructure for KraftdIntel"
Write-Info "Resource Group: $ResourceGroup"
Write-Info "Location: $Location"

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI is required. Please install it first."
    exit 1
}

# Create resource group if it doesn't exist
$rg = az group exists --name $ResourceGroup | ConvertFrom-Json
if (-not $rg) {
    Write-Info "Creating resource group..."
    az group create --name $ResourceGroup --location $Location
    Write-Success "Resource group created"
}
else {
    Write-Success "Resource group already exists"
}

# Deploy infrastructure
Write-Info "Deploying infrastructure components..."
az deployment group create `
    --name "kraftdintel-infra-$(Get-Date -Format 'yyyyMMddHHmmss')" `
    --resource-group $ResourceGroup `
    --template-file "infrastructure\main.bicep" `
    --parameters location=$Location

Write-Success "Infrastructure provisioned successfully!"

# Get outputs
Write-Info "Infrastructure Details:"
$deployment = az deployment group show `
    --name (az deployment group list --resource-group $ResourceGroup --query "[0].name" -o tsv) `
    --resource-group $ResourceGroup

Write-Host $deployment | ConvertFrom-Json | Select-Object -ExpandProperty properties | Select-Object -ExpandProperty outputs
