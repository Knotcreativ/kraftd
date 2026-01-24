<#
Idempotent script to enable system identity, assign role to system principal (kraftd-comm),
create a sender username on the target Communication Email resource, and log results.

REQUIREMENTS:
- Run in CI/GitHub Action with Azure login via service principal (secrets set in repo)
- Caller must have permission to assign roles (Owner or User Access Administrator) and to update the Communication resource
- Use as a manual, reviewed workflow (workflow_dispatch)
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Required env vars (provided by workflow or secrets)
$subscriptionId = $env:SUBSCRIPTION_ID
$resourceGroup = $env:RESOURCE_GROUP
$commName = $env:COMM_SERVICE_NAME  # kraftd-comm
$emailServiceName = $env:EMAIL_SERVICE_NAME # kraftd-email (scope for role assignment)
$domain = $env:DOMAIN_NAME  # kraftd.io
$senderUsername = $env:SENDER_USERNAME  # connect
$senderDisplay = $env:SENDER_DISPLAY_NAME # Kraftd
$logPath = "role-assign-log.txt"

function Log { param($m) Add-Content -Path $logPath -Value "$(Get-Date -Format o) - $m" }

Log "Script started"

if (-not $subscriptionId -or -not $resourceGroup -or -not $commName -or -not $emailServiceName -or -not $domain -or -not $senderUsername) {
    Write-Error "Missing required environment variables. Ensure SUBSCRIPTION_ID, RESOURCE_GROUP, COMM_SERVICE_NAME, EMAIL_SERVICE_NAME, DOMAIN_NAME, SENDER_USERNAME are set."
}

# 1) Ensure system-assigned identity is enabled on the Communication resource
$commId = "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.Communication/communicationServices/$commName"
Log "Checking identity for $commId"
$identity = az resource show --ids $commId --query identity -o json | ConvertFrom-Json
if (-not $identity) { Log "No identity object returned. Enabling system-assigned identity."; az resource update --ids $commId --set identity.type=SystemAssigned | Out-Null; Start-Sleep -s 5; $identity = az resource show --ids $commId --query identity -o json | ConvertFrom-Json }

if ($identity -and $identity.principalId) {
    $principalId = $identity.principalId
    Log "Found principalId: $principalId"
} else {
    Write-Error "Unable to enable or fetch system-assigned principalId for $commName"; exit 1
}

# 2) Assign Communication & Email Service Owner role to the system principal on the target EmailService
$emailScope = "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.Communication/emailServices/$emailServiceName"
$roleId = "09976791-48a7-449e-bb21-39d1a415f350"

# Check if role assignment exists
$existing = az role assignment list --assignee-object-id $principalId --scope $emailScope -o json | ConvertFrom-Json
if ($existing -and $existing.Count -gt 0) {
    Log "Role assignment already exists for principal $principalId on $emailServiceName"
} else {
    Log "Creating role assignment for principal $principalId on $emailServiceName"
    az role assignment create --assignee-object-id $principalId --assignee-principal-type ServicePrincipal --scope $emailScope --role $roleId | Out-Null
    Log "Role assignment created"
}

# 3) Create sender username on kraftd-comm (idempotent)
try {
    $existingSenders = az communication email domain sender-username list --resource-group $resourceGroup --email-service-name $commName --domain-name $domain -o json | ConvertFrom-Json
} catch {
    Log "Failed to list senders on $commName: $_"
    $existingSenders = @()
}
if ($existingSenders -and ($existingSenders | Where-Object { $_.username -eq $senderUsername })) {
    Log "Sender username '$senderUsername' already exists on $commName"
} else {
    Log "Creating sender username '$senderUsername' on $commName"
    az communication email domain sender-username create --domain-name $domain --email-service-name $commName --sender-username $senderUsername --username $senderUsername --display-name "$senderDisplay" -g $resourceGroup | Out-Null
    Log "Sender username created"
}

Log "Script finished successfully"
Write-Host "Done. Check logs:$logPath"