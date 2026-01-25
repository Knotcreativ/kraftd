# KRAFTD INFRASTRUCTURE VALIDATION SCRIPT
# Validates all 7 critical areas before making changes

Write-Host "🔍 KRAFTD INFRASTRUCTURE VALIDATION" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# Configuration
$RESOURCE_GROUP = "kraftd-rg"
$LOCATION = "uaenorth"
$APP_NAME = "kraftd-api"
$ACS_NAME = "kraftd-comm"
$COSMOS_NAME = "kraftd-cosmos"
$APP_INSIGHTS_NAME = "kraftd-api-insights"

Write-Host "📍 Resource Group: $RESOURCE_GROUP"
Write-Host "📍 Location: $LOCATION"
Write-Host ""

# 1. ACS IDENTITY VALIDATION
Write-Host "1️⃣ AZURE COMMUNICATION SERVICES (ACS) VALIDATION" -ForegroundColor Yellow
Write-Host "------------------------------------------------"
Write-Host "Checking ACS service..."
az communication list --resource-group $RESOURCE_GROUP --query "[].{name:name, location:location, dataLocation:dataLocation}" -o table

Write-Host ""
Write-Host "Checking ACS identity..."
az communication show --name $ACS_NAME --resource-group $RESOURCE_GROUP --query "identity" -o json

Write-Host ""
Write-Host "Checking ACS email domains..."
az communication email list-domains --name $ACS_NAME --resource-group $RESOURCE_GROUP --query "[].{domain:domain, verificationState:verificationState, verificationRecords:verificationRecords}" -o json

Write-Host ""
Write-Host "Checking ACS sender usernames..."
az communication email list-sender-usernames --name $ACS_NAME --resource-group $RESOURCE_GROUP -o json

# 2. RBAC VALIDATION
Write-Host ""
Write-Host "2️⃣ ROLE-BASED ACCESS CONTROL (RBAC) VALIDATION" -ForegroundColor Yellow
Write-Host "----------------------------------------------"
Write-Host "Checking RBAC assignments for ACS..."
az role assignment list --resource-group $RESOURCE_GROUP --query "[?contains(scope, '$ACS_NAME')].{principal:principalName, role:roleDefinitionName, scope:scope}" -o table

Write-Host ""
Write-Host "Checking RBAC assignments for Cosmos DB..."
az role assignment list --resource-group $RESOURCE_GROUP --query "[?contains(scope, '$COSMOS_NAME')].{principal:principalName, role:roleDefinitionName, scope:scope}" -o table

Write-Host ""
Write-Host "Checking managed identity assignments..."
az containerapp identity show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "principalId" -o tsv

# 3. DOMAIN LINKING VALIDATION
Write-Host ""
Write-Host "3️⃣ DOMAIN LINKING VALIDATION" -ForegroundColor Yellow
Write-Host "----------------------------"
Write-Host "Checking custom domains for Container App..."
az containerapp hostname list --name $APP_NAME --resource-group $RESOURCE_GROUP -o table

Write-Host ""
Write-Host "Checking domain verification status..."
az containerapp hostname list --name $APP_NAME --resource-group $RESOURCE_GROUP --query "[].{domain:domain, validationState:validationState}" -o json

# 4. AUTHENTICATION VALIDATION
Write-Host ""
Write-Host "4️⃣ AUTHENTICATION VALIDATION" -ForegroundColor Yellow
Write-Host "----------------------------"
Write-Host "Checking Container App authentication settings..."
az containerapp auth show --name $APP_NAME --resource-group $RESOURCE_GROUP -o json

Write-Host ""
Write-Host "Checking environment variables (authentication related)..."
az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].env[?contains(name, 'JWT') || contains(name, 'AUTH') || contains(name, 'SECRET')].{name:name, value:value}" -o json

# 5. CORS VALIDATION
Write-Host ""
Write-Host "5️⃣ CORS CONFIGURATION VALIDATION" -ForegroundColor Yellow
Write-Host "---------------------------------"
Write-Host "Checking CORS settings..."
az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.corsPolicy" -o json

# 6. MONITORING VALIDATION
Write-Host ""
Write-Host "6️⃣ MONITORING & APPLICATION INSIGHTS VALIDATION" -ForegroundColor Yellow
Write-Host "------------------------------------------------"
Write-Host "Checking Application Insights configuration..."
az monitor app-insights component show --app $APP_INSIGHTS_NAME --resource-group $RESOURCE_GROUP --query "{name:name, instrumentationKey:instrumentationKey, provisioningState:provisioningState}" -o json

Write-Host ""
Write-Host "Checking Container App monitoring integration..."
az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].env[?contains(name, 'APPINSIGHTS') || contains(name, 'MONITORING')].{name:name, value:value}" -o json

# 7. LOAD TESTING VALIDATION
Write-Host ""
Write-Host "7️⃣ LOAD TESTING CAPABILITIES VALIDATION" -ForegroundColor Yellow
Write-Host "---------------------------------------"
Write-Host "Checking Container App scaling configuration..."
az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.scale" -o json

Write-Host ""
Write-Host "Checking resource limits and requests..."
az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].resources" -o json

Write-Host ""
Write-Host "✅ INFRASTRUCTURE VALIDATION COMPLETE" -ForegroundColor Green
Write-Host "===================================="
Write-Host ""
Write-Host "📋 SUMMARY:" -ForegroundColor Cyan
Write-Host "- ACS: Service exists, check identity and domain verification above"
Write-Host "- RBAC: Check role assignments listed above"
Write-Host "- Domain: Check custom domain configuration above"
Write-Host "- Auth: Check authentication settings and env vars above"
Write-Host "- CORS: Check CORS policy configuration above"
Write-Host "- Monitoring: Check App Insights and env vars above"
Write-Host "- Load Testing: Check scaling and resource config above"
Write-Host ""
Write-Host "🔧 If any issues found, address them before making code changes." -ForegroundColor Yellow
Write-Host "📝 Document any discrepancies between code and Azure configuration." -ForegroundColor Yellow