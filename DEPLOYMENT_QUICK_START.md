# 🚀 Kraftd Docs Backend - Phase 3 Deployment

## Overview

Your backend is now ready for containerization and cloud deployment! Here's what's included:

```
✅ Dockerfile - Multi-stage optimized image
✅ docker-compose.yml - Local development setup
✅ app.yaml - Azure App Service configuration
✅ build-deploy.ps1 - Deployment automation script
✅ DEPLOYMENT.md - Complete step-by-step guide
```

---

## Quick Start (Local Testing)

### Prerequisites:
1. **Docker Desktop** installed ([Download](https://www.docker.com/products/docker-desktop))
2. **Windows PowerShell** or PowerShell Core

### Option A: Using docker-compose (Easiest)

```powershell
cd backend

# Start the application
docker-compose up -d

# Wait for startup
Start-Sleep -Seconds 3

# Test health check
curl http://localhost:8000/health

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option B: Using build script

```powershell
cd backend

# Make script executable (one time)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Build and run
.\build-deploy.ps1 -Command run

# Stop
.\build-deploy.ps1 -Command stop
```

---

## Azure Deployment (Production)

### Step 1: Install Azure CLI

```powershell
# Download and install Azure CLI
# https://aka.ms/installazurecliwindows

# Or use PowerShell:
powershell -Command "Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile .\AzureCLI.msi; Start-Process msiexec.exe -Wait -ArgumentList '/I AzureCLI.msi /quiet'"

# Verify installation
az --version
```

### Step 2: Login to Azure

```powershell
# Login to your Azure account
az login

# Set default subscription (optional)
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Verify login
az account show
```

### Step 3: Create Resources

```powershell
# Create Resource Group
az group create `
  --name kraftd-rg `
  --location eastus

# Create Container Registry
az acr create `
  --resource-group kraftd-rg `
  --name kraftdregistry `
  --sku Basic

# Login to ACR
az acr login --name kraftdregistry
```

### Step 4: Build and Push Image

```powershell
cd backend

# Option A: Using build script
.\build-deploy.ps1 -Command push -RegistryName kraftdregistry

# Option B: Using Azure CLI directly
az acr build `
  --registry kraftdregistry `
  --image kraftd-backend:latest `
  .
```

### Step 5: Deploy to Azure Container Instances (Simple)

```powershell
# Get ACR credentials
$acrPassword = az acr credential show `
  --resource-group kraftd-rg `
  --name kraftdregistry `
  --query passwords[0].value -o tsv

# Deploy to Container Instances
az container create `
  --resource-group kraftd-rg `
  --name kraftd-backend `
  --image kraftdregistry.azurecr.io/kraftd-backend:latest `
  --cpu 1 --memory 1.5 `
  --registry-login-server kraftdregistry.azurecr.io `
  --registry-username kraftdregistry `
  --registry-password $acrPassword `
  --ports 8000 `
  --protocol TCP `
  --environment-variables `
    PYTHONUNBUFFERED=1 `
    REQUEST_TIMEOUT=30 `
    RATE_LIMIT_ENABLED=true `
    METRICS_ENABLED=true

# Get the IP address
az container show `
  --resource-group kraftd-rg `
  --name kraftd-backend `
  --query ipAddress.ip
```

### Step 6: Deploy to Azure App Service (Production-Grade)

```powershell
# Create App Service Plan
az appservice plan create `
  --name kraftd-plan `
  --resource-group kraftd-rg `
  --sku B2 `
  --is-linux

# Create Web App
az webapp create `
  --resource-group kraftd-rg `
  --plan kraftd-plan `
  --name kraftd-backend-app `
  --deployment-container-image-name kraftd-backend:latest

# Configure container
az webapp config container set `
  --name kraftd-backend-app `
  --resource-group kraftd-rg `
  --docker-custom-image-name kraftdregistry.azurecr.io/kraftd-backend:latest `
  --docker-registry-server-url https://kraftdregistry.azurecr.io `
  --docker-registry-server-user kraftdregistry `
  --docker-registry-server-password $acrPassword

# Get app URL
az webapp show `
  --resource-group kraftd-rg `
  --name kraftd-backend-app `
  --query defaultHostName
```

---

## Verify Deployment

```powershell
# Test health endpoint
$url = "https://kraftd-backend-app.azurewebsites.net/health"
Invoke-WebRequest -Uri $url -UseBasicParsing

# Test metrics endpoint
$url = "https://kraftd-backend-app.azurewebsites.net/metrics"
Invoke-WebRequest -Uri $url -UseBasicParsing

# View logs
az webapp log tail `
  --resource-group kraftd-rg `
  --name kraftd-backend-app
```

---

## Configure Azure Services (Optional but Recommended)

### Add Document Intelligence

```powershell
# Create Key Vault
az keyvault create `
  --resource-group kraftd-rg `
  --name kraftd-vault

# Add secret
az keyvault secret set `
  --vault-name kraftd-vault `
  --name documentintelligence-endpoint `
  --value "https://your-instance.cognitiveservices.azure.com/"

az keyvault secret set `
  --vault-name kraftd-vault `
  --name documentintelligence-api-key `
  --value "your-api-key"

# Update app settings
az webapp config appsettings set `
  --resource-group kraftd-rg `
  --name kraftd-backend-app `
  --settings `
    "@keyvault(secretUri=https://kraftd-vault.vault.azure.net/secrets/documentintelligence-endpoint/)"
```

### Add Azure OpenAI

```powershell
# Add OpenAI secrets
az keyvault secret set `
  --vault-name kraftd-vault `
  --name azure-openai-endpoint `
  --value "https://your-instance.openai.azure.com/"

az keyvault secret set `
  --vault-name kraftd-vault `
  --name azure-openai-api-key `
  --value "your-api-key"

# Update app settings
az webapp config appsettings set `
  --resource-group kraftd-rg `
  --name kraftd-backend-app `
  --settings `
    AZURE_OPENAI_DEPLOYMENT="gpt-4" `
    "@keyvault(secretUri=https://kraftd-vault.vault.azure.net/secrets/azure-openai-endpoint/)" `
    "@keyvault(secretUri=https://kraftd-vault.vault.azure.net/secrets/azure-openai-api-key/)"
```

---

## 📊 Monitoring & Alerts

```powershell
# Enable Application Insights
az monitor app-insights component create `
  --app kraftd-backend-insights `
  --location eastus `
  --resource-group kraftd-rg `
  --application-type web

# Configure in App Service
az webapp config appsettings set `
  --resource-group kraftd-rg `
  --name kraftd-backend-app `
  --settings `
    APPLICATIONINSIGHTS_CONNECTION_STRING="<connection-string>"
```

---

## 🧹 Cleanup

```powershell
# Delete everything (CAREFUL!)
az group delete `
  --name kraftd-rg `
  --yes `
  --no-wait

# Or delete individually
docker-compose down -v
docker rmi kraftd-backend:latest
```

---

## 📋 Docker Commands Cheat Sheet

```powershell
# Build image
docker build -t kraftd-backend:latest .

# Run container
docker run -p 8000:8000 kraftd-backend:latest

# Docker Compose commands
docker-compose up -d          # Start
docker-compose down           # Stop
docker-compose logs -f        # View logs
docker-compose ps            # List containers

# Docker image commands
docker images                 # List images
docker rmi <image-id>        # Remove image
docker tag <old> <new>       # Rename image
docker push <image>          # Push to registry
```

---

## 🔧 Troubleshooting

### Container won't start
```powershell
# Check logs
docker logs kraftd-backend

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Health check failing
```powershell
# Test endpoint manually
curl http://localhost:8000/health

# Check port
netstat -ano | findstr :8000
```

### Azure deployment issues
```powershell
# Check resource status
az container show --resource-group kraftd-rg --name kraftd-backend

# View logs
az container logs --resource-group kraftd-rg --name kraftd-backend

# Get detailed diagnostics
az webapp deployment slot list --resource-group kraftd-rg --name kraftd-backend-app
```

---

## ✅ Deployment Checklist

- [ ] Docker Desktop installed
- [ ] Azure CLI installed and logged in
- [ ] Resource Group created
- [ ] Container Registry created
- [ ] Docker image built and pushed
- [ ] App Service deployed
- [ ] Health endpoint working
- [ ] Metrics endpoint accessible
- [ ] Azure services configured (optional)
- [ ] Monitoring enabled
- [ ] Custom domain configured (optional)

---

## 📞 Support

For detailed troubleshooting, see [DEPLOYMENT.md](DEPLOYMENT.md)

Need help? Check Azure documentation:
- [Azure App Service](https://docs.microsoft.com/azure/app-service/)
- [Azure Container Registry](https://docs.microsoft.com/azure/container-registry/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
