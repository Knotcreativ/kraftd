#!/bin/bash
# KRAFTD INFRASTRUCTURE VALIDATION SCRIPT
# Validates all 7 critical areas before making changes

echo "🔍 KRAFTD INFRASTRUCTURE VALIDATION"
echo "=================================="

# Configuration
RESOURCE_GROUP="kraftd-rg"
LOCATION="uaenorth"
APP_NAME="kraftd-api"
ACS_NAME="kraftd-comm"
COSMOS_NAME="kraftd-cosmos"
APP_INSIGHTS_NAME="kraftd-api-insights"

echo "📍 Resource Group: $RESOURCE_GROUP"
echo "📍 Location: $LOCATION"
echo ""

# 1. ACS IDENTITY VALIDATION
echo "1️⃣ AZURE COMMUNICATION SERVICES (ACS) VALIDATION"
echo "------------------------------------------------"
echo "Checking ACS service..."
az communication list --resource-group $RESOURCE_GROUP --query "[].{name:name, location:location, dataLocation:dataLocation}" -o table

echo ""
echo "Checking ACS identity..."
az communication show --name $ACS_NAME --resource-group $RESOURCE_GROUP --query "identity" -o json

echo ""
echo "Checking ACS email domains..."
az communication email list-domains --name $ACS_NAME --resource-group $RESOURCE_GROUP --query "[].{domain:domain, verificationState:verificationState, verificationRecords:verificationRecords}" -o json

echo ""
echo "Checking ACS sender usernames..."
az communication email list-sender-usernames --name $ACS_NAME --resource-group $RESOURCE_GROUP -o json

# 2. RBAC VALIDATION
echo ""
echo "2️⃣ ROLE-BASED ACCESS CONTROL (RBAC) VALIDATION"
echo "----------------------------------------------"
echo "Checking RBAC assignments for ACS..."
az role assignment list --resource-group $RESOURCE_GROUP --query "[?contains(scope, '$ACS_NAME')].{principal:principalName, role:roleDefinitionName, scope:scope}" -o table

echo ""
echo "Checking RBAC assignments for Cosmos DB..."
az role assignment list --resource-group $RESOURCE_GROUP --query "[?contains(scope, '$COSMOS_NAME')].{principal:principalName, role:roleDefinitionName, scope:scope}" -o table

echo ""
echo "Checking managed identity assignments..."
az containerapp identity show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "principalId" -o tsv

# 3. DOMAIN LINKING VALIDATION
echo ""
echo "3️⃣ DOMAIN LINKING VALIDATION"
echo "----------------------------"
echo "Checking custom domains for Container App..."
az containerapp hostname list --name $APP_NAME --resource-group $RESOURCE_GROUP -o table

echo ""
echo "Checking domain verification status..."
az containerapp hostname list --name $APP_NAME --resource-group $RESOURCE_GROUP --query "[].{domain:domain, validationState:validationState}" -o json

# 4. AUTHENTICATION VALIDATION
echo ""
echo "4️⃣ AUTHENTICATION VALIDATION"
echo "----------------------------"
echo "Checking Container App authentication settings..."
az containerapp auth show --name $APP_NAME --resource-group $RESOURCE_GROUP -o json

echo ""
echo "Checking environment variables (authentication related)..."
az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].env[?contains(name, 'JWT') || contains(name, 'AUTH') || contains(name, 'SECRET')].{name:name, value:value}" -o json

# 5. CORS VALIDATION
echo ""
echo "5️⃣ CORS CONFIGURATION VALIDATION"
echo "---------------------------------"
echo "Checking CORS settings..."
az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.corsPolicy" -o json

# 6. MONITORING VALIDATION
echo ""
echo "6️⃣ MONITORING & APPLICATION INSIGHTS VALIDATION"
echo "------------------------------------------------"
echo "Checking Application Insights configuration..."
az monitor app-insights component show --app $APP_INSIGHTS_NAME --resource-group $RESOURCE_GROUP --query "{name:name, instrumentationKey:instrumentationKey, provisioningState:provisioningState}" -o json

echo ""
echo "Checking Container App monitoring integration..."
az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].env[?contains(name, 'APPINSIGHTS') || contains(name, 'MONITORING')].{name:name, value:value}" -o json

# 7. LOAD TESTING VALIDATION
echo ""
echo "7️⃣ LOAD TESTING CAPABILITIES VALIDATION"
echo "---------------------------------------"
echo "Checking Container App scaling configuration..."
az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.scale" -o json

echo ""
echo "Checking resource limits and requests..."
az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].resources" -o json

echo ""
echo "✅ INFRASTRUCTURE VALIDATION COMPLETE"
echo "===================================="
echo ""
echo "📋 SUMMARY:"
echo "- ACS: Service exists, check identity and domain verification above"
echo "- RBAC: Check role assignments listed above"
echo "- Domain: Check custom domain configuration above"
echo "- Auth: Check authentication settings and env vars above"
echo "- CORS: Check CORS policy configuration above"
echo "- Monitoring: Check App Insights and env vars above"
echo "- Load Testing: Check scaling and resource config above"
echo ""
echo "🔧 If any issues found, address them before making code changes."
echo "📝 Document any discrepancies between code and Azure configuration."</content>
<parameter name="filePath">c:\Users\1R6\OneDrive\Project Catalyst\KraftdIntel\validate_infrastructure.sh