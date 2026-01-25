@echo off
REM KRAFTD INFRASTRUCTURE VALIDATION SCRIPT
REM Validates all 7 critical areas before making changes

echo 🔍 KRAFTD INFRASTRUCTURE VALIDATION
echo ==================================
echo.

REM Configuration
set RESOURCE_GROUP=KraftdRG
set LOCATION=uaenorth
set APP_NAME=kraftd-api
set ACS_NAME=kraftd-comm
set COSMOS_NAME=kraftd-cosmos
set APP_INSIGHTS_NAME=kraftd-api-insights

echo 📍 Resource Group: %RESOURCE_GROUP%
echo 📍 Location: %LOCATION%
echo.

REM 1. ACS IDENTITY VALIDATION
echo 1. AZURE COMMUNICATION SERVICES (ACS) VALIDATION
echo ------------------------------------------------
echo Checking ACS service...
az communication list --resource-group %RESOURCE_GROUP%
echo.
echo Checking ACS identity...
az communication show --name %ACS_NAME% --resource-group %RESOURCE_GROUP% --query identity
echo.
echo Checking ACS email domains...
az communication email list-domains --name %ACS_NAME% --resource-group %RESOURCE_GROUP%
echo.
echo Checking ACS sender usernames...
az communication email list-sender-usernames --name %ACS_NAME% --resource-group %RESOURCE_GROUP%

REM 2. RBAC VALIDATION
echo.
echo 2. ROLE-BASED ACCESS CONTROL (RBAC) VALIDATION
echo ----------------------------------------------
echo Checking RBAC assignments...
az role assignment list --resource-group %RESOURCE_GROUP%
echo.
echo Checking managed identity assignments...
az containerapp identity show --name %APP_NAME% --resource-group %RESOURCE_GROUP%

REM 3. DOMAIN LINKING VALIDATION
echo.
echo 3. DOMAIN LINKING VALIDATION
echo ----------------------------
echo Checking custom domains for Container App...
az containerapp hostname list --name %APP_NAME% --resource-group %RESOURCE_GROUP%

REM 4. AUTHENTICATION VALIDATION
echo.
echo 4. AUTHENTICATION VALIDATION
echo ----------------------------
echo Checking Container App authentication settings...
az containerapp auth show --name %APP_NAME% --resource-group %RESOURCE_GROUP%
echo.
echo Checking environment variables...
az containerapp show --name %APP_NAME% --resource-group %RESOURCE_GROUP% --query properties.template.containers[0].env

REM 5. CORS VALIDATION
echo.
echo 5. CORS CONFIGURATION VALIDATION
echo ---------------------------------
echo Checking CORS settings...
az containerapp show --name %APP_NAME% --resource-group %RESOURCE_GROUP% --query properties.configuration.ingress.corsPolicy

REM 6. MONITORING VALIDATION
echo.
echo 6. MONITORING and APPLICATION INSIGHTS VALIDATION
echo ------------------------------------------------
echo Checking Application Insights configuration...
az monitor app-insights component show --app %APP_INSIGHTS_NAME% --resource-group %RESOURCE_GROUP%

REM 7. LOAD TESTING VALIDATION
echo.
echo 7. LOAD TESTING CAPABILITIES VALIDATION
echo ---------------------------------------
echo Checking Container App scaling configuration...
az containerapp show --name %APP_NAME% --resource-group %RESOURCE_GROUP% --query properties.template.scale
echo.
echo Checking resource limits and requests...
az containerapp show --name %APP_NAME% --resource-group %RESOURCE_GROUP% --query properties.template.containers[0].resources

echo.
echo ✅ INFRASTRUCTURE VALIDATION COMPLETE
echo ====================================
echo.
echo 📋 SUMMARY:
echo - ACS: Service exists, check identity and domain verification above
echo - RBAC: Check role assignments listed above
echo - Domain: Check custom domain configuration above
echo - Auth: Check authentication settings and env vars above
echo - CORS: Check CORS policy configuration above
echo - Monitoring: Check App Insights and env vars above
echo - Load Testing: Check scaling and resource config above
echo.
echo 🔧 If any issues found, address them before making code changes.
echo 📝 Document any discrepancies between code and Azure configuration.
echo.
pause