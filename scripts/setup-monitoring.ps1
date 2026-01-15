param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory=$true)]
    [string]$AppServiceName,
    
    [Parameter(Mandatory=$true)]
    [string]$AppInsightsName,
    
    [Parameter(Mandatory=$false)]
    [string]$EmailAddress = "admin@kraftdintel.com"
)

function Write-Success($message) { Write-Host "✓ $message" -ForegroundColor Green }
function Write-Info($message) { Write-Host "ℹ $message" -ForegroundColor Cyan }
function Write-Error($message) { Write-Host "✗ $message" -ForegroundColor Red }

Write-Info "Setting up monitoring and alerts for KraftdIntel"

# Validate prerequisites
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI not found. Please install it first."
    exit 1
}

# Create action group
Write-Info "Creating action group for alerts..."
$actionGroupName = "$AppServiceName-alerts"
az monitor action-group create `
    --name $actionGroupName `
    --resource-group $ResourceGroup

Write-Success "Action group created: $actionGroupName"

# Add email action
Write-Info "Adding email notification receiver..."
az monitor action-group receiver email add `
    --action-group $actionGroupName `
    --resource-group $ResourceGroup `
    --name "EmailNotification" `
    --email-address $EmailAddress

Write-Success "Email receiver added: $EmailAddress"

# Create alert rule: High error rate
Write-Info "Creating alert rule: High error rate..."
az monitor metrics alert create `
    --name "HighErrorRate" `
    --resource-group $ResourceGroup `
    --scopes /subscriptions/{subscription}/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$AppServiceName `
    --condition "avg Http5xx > 50" `
    --window-size 15m `
    --evaluation-frequency 5m `
    --action $actionGroupName

Write-Success "Alert created: High error rate"

# Create alert rule: High response time
Write-Info "Creating alert rule: High response time..."
az monitor metrics alert create `
    --name "HighResponseTime" `
    --resource-group $ResourceGroup `
    --scopes /subscriptions/{subscription}/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$AppServiceName `
    --condition "avg ResponseTime > 2000" `
    --window-size 15m `
    --evaluation-frequency 5m `
    --action $actionGroupName

Write-Success "Alert created: High response time"

# Create alert rule: High CPU usage
Write-Info "Creating alert rule: High CPU usage..."
az monitor metrics alert create `
    --name "HighCpuUsage" `
    --resource-group $ResourceGroup `
    --scopes /subscriptions/{subscription}/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$AppServiceName `
    --condition "avg CpuTime > 80" `
    --window-size 15m `
    --evaluation-frequency 5m `
    --action $actionGroupName

Write-Success "Alert created: High CPU usage"

# Create alert rule: Application offline
Write-Info "Creating alert rule: Application offline..."
az monitor metrics alert create `
    --name "ApplicationOffline" `
    --resource-group $ResourceGroup `
    --scopes /subscriptions/{subscription}/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$AppServiceName `
    --condition "max HealthStatus < 1" `
    --window-size 5m `
    --evaluation-frequency 1m `
    --action $actionGroupName

Write-Success "Alert created: Application offline"

Write-Info "Creating dashboard..."
# Import dashboard JSON (update {subscription} and {resourceGroup} placeholders)
$dashboardContent = Get-Content -Path "infrastructure/dashboard.json" -Raw
$dashboardContent = $dashboardContent.Replace("{subscription}", (az account show --query id -o tsv))
$dashboardContent = $dashboardContent.Replace("{resourceGroup}", $ResourceGroup)
$dashboardContent = $dashboardContent.Replace("{appInsightsName}", $AppInsightsName)

$dashboardContent | az portal dashboard create `
    --resource-group $ResourceGroup `
    --name "KraftdIntelDashboard" `
    --input-path /dev/stdin

Write-Success "Dashboard created: KraftdIntelDashboard"

Write-Host ""
Write-Host "═" * 50
Write-Success "Monitoring setup complete!"
Write-Host ""
Write-Host "Configuration Summary:"
Write-Host "  Action Group: $actionGroupName"
Write-Host "  Alert Rules: 4 (error rate, response time, CPU, offline)"
Write-Host "  Dashboard: KraftdIntelDashboard"
Write-Host "  Email: $EmailAddress"
Write-Host "═" * 50
