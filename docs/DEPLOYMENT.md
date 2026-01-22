# Kraftd Docs Backend - Docker & Azure Deployment Guide

## 📦 Docker Setup (Local Development)

### Prerequisites:
- Docker Desktop installed
- Docker Compose installed
- 2GB+ RAM available

### Build and Run Locally:

```bash
# Navigate to backend directory
cd backend

# Build the Docker image
docker build -t kraftd-backend:latest .

# Or use docker-compose for easier management
docker-compose up -d
```

### Test Local Container:

```bash
# Check container is running
docker ps | grep kraftd

# Test health endpoint
curl http://localhost:8000/health

# View logs
docker logs kraftd-backend

# Stop container
docker-compose down
```

### Troubleshooting Local Container:

```bash
# View detailed logs
docker logs -f kraftd-backend

# Rebuild without cache
docker-compose build --no-cache

# Clean up everything
docker-compose down -v
```

---

## ☁️ Azure Deployment

### Option 1: Azure Container Instances (Simple, Quick)

#### Prerequisites:
```bash
# Install Azure CLI
# Windows: https://aka.ms/installazurecliwindows
# Or via PowerShell:
powershell -Command "Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile .\AzureCLI.msi; Start-Process msiexec.exe -Wait -ArgumentList '/I AzureCLI.msi /quiet'"

# Login to Azure
az login

# Set subscription
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

#### Deploy Steps:

```bash
# 1. Create Resource Group
az group create \
  --name kraftd-rg \
  --location eastus

# 2. Create Azure Container Registry
az acr create \
  --resource-group kraftd-rg \
  --name kraftdregistry \
  --sku Basic

# 3. Login to ACR
az acr login --name kraftdregistry

# 4. Build and push image
az acr build \
  --registry kraftdregistry \
  --image kraftd-backend:latest \
  .

# 5. Deploy to Container Instances
az container create \
  --resource-group kraftd-rg \
  --name kraftd-backend \
  --image kraftdregistry.azurecr.io/kraftd-backend:latest \
  --cpu 1 \
  --memory 1.5 \
  --registry-login-server kraftdregistry.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --ports 8000 \
  --protocol TCP \
  --environment-variables \
    PYTHONUNBUFFERED=1 \
    REQUEST_TIMEOUT=30 \
    RATE_LIMIT_ENABLED=true \
    METRICS_ENABLED=true \
  --restart-policy OnFailure

# 6. Get container IP
az container show \
  --resource-group kraftd-rg \
  --name kraftd-backend \
  --query ipAddress.ip
```

---

### Option 2: Azure App Service (Production-Grade)

#### Prerequisites:
```bash
# Same as above - Azure CLI and login
```

#### Deployment Steps:

```bash
# 1. Create App Service Plan
az appservice plan create \
  --name kraftd-plan \
  --resource-group kraftd-rg \
  --sku B2 \
  --is-linux

# 2. Create Web App
az webapp create \
  --resource-group kraftd-rg \
  --plan kraftd-plan \
  --name kraftd-backend \
  --deployment-container-image-name kraft

dregistry.azurecr.io/kraftd-backend:latest

# 3. Configure container settings
az webapp config container set \
  --name kraftd-backend \
  --resource-group kraftd-rg \
  --docker-custom-image-name kraftdregistry.azurecr.io/kraftd-backend:latest \
  --docker-registry-server-url https://kraftdregistry.azurecr.io \
  --docker-registry-server-user <username> \
  --docker-registry-server-password <password>

# 4. Configure app settings
az webapp config appsettings set \
  --resource-group kraftd-rg \
  --name kraftd-backend \
  --settings \
    PYTHONUNBUFFERED=1 \
    REQUEST_TIMEOUT=30 \
    RATE_LIMIT_ENABLED=true \
    METRICS_ENABLED=true \
    DOCUMENTINTELLIGENCE_ENDPOINT="https://your-instance.cognitiveservices.azure.com/" \
    DOCUMENTINTELLIGENCE_API_KEY="your-key" \
    AZURE_OPENAI_ENDPOINT="https://your-instance.openai.azure.com/" \
    AZURE_OPENAI_API_KEY="your-key" \
    AZURE_OPENAI_DEPLOYMENT="gpt-4"

# 5. Enable logging
az webapp log config \
  --resource-group kraftd-rg \
  --name kraftd-backend \
  --web-server-logging filesystem \
  --level verbose

# 6. Get app URL
az webapp show \
  --resource-group kraftd-rg \
  --name kraftd-backend \
  --query defaultHostName
```

---

## 🔍 Verify Deployment

```bash
# Test health endpoint
curl https://your-app.azurewebsites.net/health

# Test metrics endpoint
curl https://your-app.azurewebsites.net/metrics

# View logs in Azure
az webapp log tail \
  --resource-group kraftd-rg \
  --name kraftd-backend
```

---

## 📊 Monitoring & Alerts

### Enable Application Insights:

```bash
# Create Application Insights
az monitor app-insights component create \
  --app kraftd-backend-insights \
  --location eastus \
  --resource-group kraftd-rg \
  --application-type web

# Configure in App Service
az webapp config appsettings set \
  --resource-group kraftd-rg \
  --name kraftd-backend \
  --settings \
    APPLICATIONINSIGHTS_CONNECTION_STRING="<connection-string>"
```

---

## 🧹 Cleanup

```bash
# Delete everything
az group delete \
  --name kraftd-rg \
  --yes --no-wait
```

---

## 📝 Environment Variables for Deployment

| Variable | Description | Example |
|----------|-------------|---------|
| `REQUEST_TIMEOUT` | Overall request timeout (seconds) | `30` |
| `DOCUMENT_PROCESSING_TIMEOUT` | Document processing timeout | `25` |
| `FILE_PARSE_TIMEOUT` | File parsing timeout | `20` |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | Rate limit per minute | `60` |
| `RATE_LIMIT_REQUESTS_PER_HOUR` | Rate limit per hour | `1000` |
| `METRICS_ENABLED` | Enable metrics collection | `true` |
| `ENVIRONMENT` | Environment type | `production` |
| `DOCUMENTINTELLIGENCE_ENDPOINT` | Azure Document Intelligence endpoint | `https://xxx.cognitiveservices.azure.com/` |
| `DOCUMENTINTELLIGENCE_API_KEY` | Document Intelligence API key | `your-key` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | `https://xxx.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | `your-key` |
| `AZURE_OPENAI_DEPLOYMENT` | OpenAI deployment name | `gpt-4` |

---

## 🚀 Recommended Production Setup

```
Azure Infrastructure:
├─ Container Registry (ACR) - Store images
├─ App Service Plan (B2) - Host the app
├─ App Service - The application
├─ Application Insights - Monitoring
├─ Key Vault - Secrets management
└─ Cosmos DB (optional) - Document storage
```

---

## 📞 Support & Troubleshooting

If deployment fails:
1. Check Azure CLI installation: `az --version`
2. Verify authentication: `az account show`
3. Check resource group: `az group list`
4. View app logs: `az webapp log tail --resource-group kraftd-rg --name kraftd-backend`
