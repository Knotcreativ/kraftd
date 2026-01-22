@echo off
REM KRAFTD Azure Deployment Script for Windows
REM This script automates the deployment process to Azure Container Apps

setlocal enabledelayedexpansion

REM Configuration
set RESOURCE_GROUP=KraftdRG
set REGISTRY_NAME=kraftdregistry
set LOCATION=eastus
set ENVIRONMENT_NAME=kraftd-env
set APP_NAME=kraftd-api
set IMAGE_TAG=latest

echo.
echo ===============================================================
echo   KRAFTD Azure Container Apps Deployment (Windows)
echo ===============================================================
echo.

REM Step 1: Validate prerequisites
echo [1/8] Validating prerequisites...
where az >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Azure CLI not found. Install from: https://aka.ms/azure-cli
    exit /b 1
)
echo [OK] Azure CLI installed

where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker not found. Install from: https://www.docker.com
    exit /b 1
)
echo [OK] Docker installed

REM Step 2: Verify Azure login
echo.
echo [2/8] Checking Azure authentication...
az account show >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Not logged in to Azure
    echo Run: az login
    exit /b 1
)
for /f "delims=" %%i in ('az account show --query user.name -o tsv') do set CURRENT_USER=%%i
echo [OK] Logged in as: %CURRENT_USER%

REM Step 3: Create or verify resource group
echo.
echo [3/8] Setting up resource group...
for /f "delims=" %%i in ('az group exists --name %RESOURCE_GROUP%') do set GROUP_EXISTS=%%i
if "%GROUP_EXISTS%"=="true" (
    echo [OK] Resource group exists: %RESOURCE_GROUP%
) else (
    echo Creating resource group...
    call az group create --name %RESOURCE_GROUP% --location %LOCATION%
    echo [OK] Resource group created: %RESOURCE_GROUP%
)

REM Step 4: Create or verify container registry
echo.
echo [4/8] Setting up Azure Container Registry...
az acr show --resource-group %RESOURCE_GROUP% --name %REGISTRY_NAME% >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Container registry exists: %REGISTRY_NAME%
) else (
    echo Creating container registry (this may take a few minutes)...
    call az acr create ^
        --resource-group %RESOURCE_GROUP% ^
        --name %REGISTRY_NAME% ^
        --sku Basic ^
        --admin-enabled true
    echo [OK] Container registry created: %REGISTRY_NAME%
)

for /f "delims=" %%i in ('az acr show --resource-group %RESOURCE_GROUP% --name %REGISTRY_NAME% --query loginServer -o tsv') do set REGISTRY_URL=%%i
echo [OK] Registry URL: %REGISTRY_URL%

REM Step 5: Build and push Docker image
echo.
echo [5/8] Building and pushing Docker image...
echo Building image in registry (this may take 5-10 minutes)...

call az acr build ^
    --registry %REGISTRY_NAME% ^
    --image kraftd-backend:%IMAGE_TAG% ^
    --file backend/Dockerfile ^
    ./backend

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to build image
    exit /b 1
)
echo [OK] Image built and pushed: %REGISTRY_URL%/kraftd-backend:%IMAGE_TAG%

REM Step 6: Create container app environment
echo.
echo [6/8] Setting up Container Apps environment...
az containerapp env show --name %ENVIRONMENT_NAME% --resource-group %RESOURCE_GROUP% >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Environment exists: %ENVIRONMENT_NAME%
) else (
    echo Creating environment (this may take a few minutes)...
    call az containerapp env create ^
        --name %ENVIRONMENT_NAME% ^
        --resource-group %RESOURCE_GROUP% ^
        --location %LOCATION%
    echo [OK] Environment created: %ENVIRONMENT_NAME%
)

REM Step 7: Get credentials for registry
echo.
echo [7/8] Preparing registry authentication...
for /f "delims=" %%i in ('az acr credential show -n %REGISTRY_NAME% --query username -o tsv') do set REGISTRY_USERNAME=%%i
for /f "delims=" %%i in ('az acr credential show -n %REGISTRY_NAME% --query "passwords[0].value" -o tsv') do set REGISTRY_PASSWORD=%%i
echo [OK] Registry credentials obtained

REM Step 8: Load environment variables
echo.
echo [8/8] Loading environment configuration...

if not exist "backend\.env" (
    echo [ERROR] backend\.env file not found
    echo Please create backend\.env first:
    echo   cd backend
    echo   copy .env.example .env
    echo   REM Edit .env with your values
    exit /b 1
)

REM Read .env file (basic approach - reads first matching values)
for /f "tokens=1,* delims==" %%a in ('findstr /v "^#" backend\.env ^| findstr /v "^$"') do (
    if "%%a"=="COSMOS_ENDPOINT" set COSMOS_ENDPOINT=%%b
    if "%%a"=="COSMOS_KEY" set COSMOS_KEY=%%b
    if "%%a"=="COSMOS_DATABASE" set COSMOS_DATABASE=%%b
    if "%%a"=="JWT_SECRET" set JWT_SECRET=%%b
    if "%%a"=="JWT_ALGORITHM" set JWT_ALGORITHM=%%b
    if "%%a"=="LOG_LEVEL" set LOG_LEVEL=%%b
    if "%%a"=="CORS_ORIGINS" set CORS_ORIGINS=%%b
    if "%%a"=="ENABLE_QUOTA_ENFORCEMENT" set ENABLE_QUOTA_ENFORCEMENT=%%b
)

echo [OK] Configuration loaded

REM Deploy or update container app
echo.
echo Deploying Container App...

az containerapp show --name %APP_NAME% --resource-group %RESOURCE_GROUP% >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Updating existing container app...
    call az containerapp update ^
        --name %APP_NAME% ^
        --resource-group %RESOURCE_GROUP% ^
        --image %REGISTRY_URL%/kraftd-backend:%IMAGE_TAG% ^
        --env-vars ^
            COSMOS_ENDPOINT="%COSMOS_ENDPOINT%" ^
            COSMOS_KEY="%COSMOS_KEY%" ^
            COSMOS_DATABASE="%COSMOS_DATABASE%" ^
            JWT_SECRET="%JWT_SECRET%" ^
            JWT_ALGORITHM="%JWT_ALGORITHM%" ^
            ENVIRONMENT="production" ^
            LOG_LEVEL="%LOG_LEVEL%" ^
            CORS_ORIGINS="%CORS_ORIGINS%" ^
            ENABLE_QUOTA_ENFORCEMENT="%ENABLE_QUOTA_ENFORCEMENT%"
    echo [OK] Container app updated
) else (
    echo Creating new container app...
    call az containerapp create ^
        --name %APP_NAME% ^
        --resource-group %RESOURCE_GROUP% ^
        --environment %ENVIRONMENT_NAME% ^
        --image %REGISTRY_URL%/kraftd-backend:%IMAGE_TAG% ^
        --target-port 8000 ^
        --ingress external ^
        --cpu 0.5 ^
        --memory 1.0Gi ^
        --min-replicas 2 ^
        --max-replicas 10 ^
        --env-vars ^
            COSMOS_ENDPOINT="%COSMOS_ENDPOINT%" ^
            COSMOS_KEY="%COSMOS_KEY%" ^
            COSMOS_DATABASE="%COSMOS_DATABASE%" ^
            JWT_SECRET="%JWT_SECRET%" ^
            JWT_ALGORITHM="%JWT_ALGORITHM%" ^
            ENVIRONMENT="production" ^
            LOG_LEVEL="%LOG_LEVEL%" ^
            CORS_ORIGINS="%CORS_ORIGINS%" ^
            ENABLE_QUOTA_ENFORCEMENT="%ENABLE_QUOTA_ENFORCEMENT%" ^
        --registry-server %REGISTRY_URL% ^
        --registry-username %REGISTRY_USERNAME% ^
        --registry-password %REGISTRY_PASSWORD%
    echo [OK] Container app created
)

REM Get application URL
for /f "delims=" %%i in ('az containerapp show --name %APP_NAME% --resource-group %RESOURCE_GROUP% --query properties.configuration.ingress.fqdn -o tsv') do set APP_URL=%%i

echo.
echo ===============================================================
echo   Deployment Complete!
echo ===============================================================
echo.
echo Application URL: https://%APP_URL%
echo.
echo Next steps:
echo 1. Verify health check:
echo    curl https://%APP_URL%/api/v1/health
echo.
echo 2. Run E2E tests:
echo    python KRAFTD_E2E_TEST.py "TOKEN" --base-url "https://%APP_URL%/api/v1"
echo.
echo 3. View logs:
echo    az containerapp logs show --name %APP_NAME% --resource-group %RESOURCE_GROUP% --follow
echo.
echo 4. Update CORS_ORIGINS when you have your frontend URL
echo.
