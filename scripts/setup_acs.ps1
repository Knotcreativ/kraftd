param(
    [string]$ResourceGroup = "kraftdintel-rg",
    [string]$Prefix = "kraftd",
    [string]$Location = "uaenorth",
    [string]$ContainerAppName = "kraftdintel-app"
)

set -e

Write-Host "Starting ACS setup for resource group '$ResourceGroup' with prefix '$Prefix' in location '$Location'"

# Deploy the infra (main.bicep contains the communication resource with location='global')
Write-Host "Deploying Bicep template (this will be incremental and idempotent)"
az deployment group create -g $ResourceGroup -f "infrastructure/azure/main.bicep" --parameters prefix=$Prefix location=$Location --no-wait

# Wait for deployment to complete (poll until finished)
Write-Host "Waiting for deployment to finish..."
az deployment group wait -g $ResourceGroup --name "$(Get-Date -Format o)" --created --interval 5 --timeout 1800 2>$null || Write-Host "Deployment triggered; ensure it completes in the portal if the waiter times out."

# Fetch ACS connection string
$subscriptionId = az account show --query id -o tsv
$commName = "$Prefix-comm"
Write-Host "Fetching ACS primary connection string for '$commName'"
$resp = az rest -m post -u "https://management.azure.com/subscriptions/$subscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Communication/communicationServices/$commName/listKeys?api-version=2021-10-01" -o json | ConvertFrom-Json
if (-not $resp.primaryConnectionString) {
    Write-Error "Failed to fetch ACS connection string. Check that the Communication resource exists and that your account has permissions."
    exit 1
}
$connectionString = $resp.primaryConnectionString

Write-Host "Connection string retrieved (sanitized):" ($connectionString.Substring(0,80) + "...")

# Set GH secret (requires gh CLI and that you're authenticated)
try {
    Write-Host "Setting GitHub secret 'AZURE_COMMUNICATION_CONNECTION_STRING'"
    gh secret set AZURE_COMMUNICATION_CONNECTION_STRING --body "$connectionString" --repo "$(git -C . rev-parse --show-toplevel | Split-Path -Leaf)" 2>$null
    Write-Host "GitHub secret set"
} catch {
    Write-Warning "gh CLI not available or failed to set repo secret. Please run:\n gh secret set AZURE_COMMUNICATION_CONNECTION_STRING --body \"$connectionString\""
}

# Set Container App secret and restart app
Write-Host "Setting Container App secret and restarting app"
az containerapp secret set --name $ContainerAppName -g $ResourceGroup --secrets azureCommConn="$connectionString"
az containerapp restart -n $ContainerAppName -g $ResourceGroup

Write-Host "ACS setup complete. Verify email capabilities and adjust app config as needed."
