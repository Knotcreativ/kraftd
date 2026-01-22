#!/bin/bash

# KRAFTD Azure Deployment Script
# This script automates the deployment process to Azure Container Apps

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="KraftdRG"
REGISTRY_NAME="kraftdregistry"
LOCATION="eastus"
ENVIRONMENT_NAME="kraftd-env"
APP_NAME="kraftd-api"
IMAGE_TAG="latest"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  KRAFTD Azure Container Apps Deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Step 1: Validate prerequisites
echo -e "\n${BLUE}[1/8]${NC} Validating prerequisites..."
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found. Install from: https://aka.ms/azure-cli${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Azure CLI installed${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Install from: https://www.docker.com${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker installed${NC}"

# Step 2: Verify Azure login
echo -e "\n${BLUE}[2/8]${NC} Checking Azure authentication..."
if ! az account show &> /dev/null; then
    echo -e "${RED}❌ Not logged in to Azure${NC}"
    echo "Run: az login"
    exit 1
fi
CURRENT_USER=$(az account show --query user.name -o tsv)
echo -e "${GREEN}✅ Logged in as: $CURRENT_USER${NC}"

# Step 3: Create or verify resource group
echo -e "\n${BLUE}[3/8]${NC} Setting up resource group..."
if az group exists --name $RESOURCE_GROUP | grep -q true; then
    echo -e "${GREEN}✅ Resource group exists: $RESOURCE_GROUP${NC}"
else
    echo "Creating resource group..."
    az group create --name $RESOURCE_GROUP --location $LOCATION
    echo -e "${GREEN}✅ Resource group created: $RESOURCE_GROUP${NC}"
fi

# Step 4: Create or verify container registry
echo -e "\n${BLUE}[4/8]${NC} Setting up Azure Container Registry..."
if az acr show --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME &> /dev/null; then
    echo -e "${GREEN}✅ Container registry exists: $REGISTRY_NAME${NC}"
else
    echo "Creating container registry (this may take a few minutes)..."
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $REGISTRY_NAME \
        --sku Basic \
        --admin-enabled true
    echo -e "${GREEN}✅ Container registry created: $REGISTRY_NAME${NC}"
fi

REGISTRY_URL=$(az acr show --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME --query loginServer -o tsv)
echo -e "${GREEN}✅ Registry URL: $REGISTRY_URL${NC}"

# Step 5: Build and push Docker image
echo -e "\n${BLUE}[5/8]${NC} Building and pushing Docker image..."
echo "Building image in registry (this may take 5-10 minutes)..."

if az acr build \
    --registry $REGISTRY_NAME \
    --image kraftd-backend:$IMAGE_TAG \
    --file backend/Dockerfile \
    ./backend; then
    echo -e "${GREEN}✅ Image built and pushed: $REGISTRY_URL/kraftd-backend:$IMAGE_TAG${NC}"
else
    echo -e "${RED}❌ Failed to build image${NC}"
    exit 1
fi

# Step 6: Create container app environment
echo -e "\n${BLUE}[6/8]${NC} Setting up Container Apps environment..."
if az containerapp env show --name $ENVIRONMENT_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo -e "${GREEN}✅ Environment exists: $ENVIRONMENT_NAME${NC}"
else
    echo "Creating environment (this may take a few minutes)..."
    az containerapp env create \
        --name $ENVIRONMENT_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION
    echo -e "${GREEN}✅ Environment created: $ENVIRONMENT_NAME${NC}"
fi

# Step 7: Get credentials for registry
echo -e "\n${BLUE}[7/8]${NC} Preparing registry authentication..."
REGISTRY_USERNAME=$(az acr credential show -n $REGISTRY_NAME --query username -o tsv)
REGISTRY_PASSWORD=$(az acr credential show -n $REGISTRY_NAME --query 'passwords[0].value' -o tsv)
echo -e "${GREEN}✅ Registry credentials obtained${NC}"

# Step 8: Load environment variables
echo -e "\n${BLUE}[8/8]${NC} Loading environment configuration..."

if [ ! -f "backend/.env" ]; then
    echo -e "${RED}❌ backend/.env file not found${NC}"
    echo "Please create backend/.env first:"
    echo "  cd backend"
    echo "  cp .env.example .env"
    echo "  # Edit .env with your values"
    exit 1
fi

# Source the environment variables
set -a
source backend/.env
set +a

echo -e "${GREEN}✅ Configuration loaded${NC}"

# Deploy or update container app
echo -e "\n${BLUE}Deploying Container App...${NC}"

if az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "Updating existing container app..."
    az containerapp update \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $REGISTRY_URL/kraftd-backend:$IMAGE_TAG \
        --env-vars \
            COSMOS_ENDPOINT="$COSMOS_ENDPOINT" \
            COSMOS_KEY="$COSMOS_KEY" \
            COSMOS_DATABASE="$COSMOS_DATABASE" \
            JWT_SECRET="$JWT_SECRET" \
            JWT_ALGORITHM="$JWT_ALGORITHM" \
            ENVIRONMENT="production" \
            LOG_LEVEL="$LOG_LEVEL" \
            CORS_ORIGINS="$CORS_ORIGINS" \
            ENABLE_QUOTA_ENFORCEMENT="$ENABLE_QUOTA_ENFORCEMENT"
    echo -e "${GREEN}✅ Container app updated${NC}"
else
    echo "Creating new container app..."
    az containerapp create \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $ENVIRONMENT_NAME \
        --image $REGISTRY_URL/kraftd-backend:$IMAGE_TAG \
        --target-port 8000 \
        --ingress external \
        --cpu 0.5 \
        --memory 1.0Gi \
        --min-replicas 2 \
        --max-replicas 10 \
        --env-vars \
            COSMOS_ENDPOINT="$COSMOS_ENDPOINT" \
            COSMOS_KEY="$COSMOS_KEY" \
            COSMOS_DATABASE="$COSMOS_DATABASE" \
            JWT_SECRET="$JWT_SECRET" \
            JWT_ALGORITHM="$JWT_ALGORITHM" \
            ENVIRONMENT="production" \
            LOG_LEVEL="$LOG_LEVEL" \
            CORS_ORIGINS="$CORS_ORIGINS" \
            ENABLE_QUOTA_ENFORCEMENT="$ENABLE_QUOTA_ENFORCEMENT" \
        --registry-server $REGISTRY_URL \
        --registry-username $REGISTRY_USERNAME \
        --registry-password $REGISTRY_PASSWORD
    echo -e "${GREEN}✅ Container app created${NC}"
fi

# Get application URL
APP_URL=$(az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Application URL: ${GREEN}https://$APP_URL${NC}"
echo ""
echo "Next steps:"
echo "1. Verify health check:"
echo "   curl https://$APP_URL/api/v1/health"
echo ""
echo "2. Run E2E tests:"
echo "   python KRAFTD_E2E_TEST.py \"\$TOKEN\" --base-url \"https://$APP_URL/api/v1\""
echo ""
echo "3. View logs:"
echo "   az containerapp logs show --name $APP_NAME --resource-group $RESOURCE_GROUP --follow"
echo ""
echo "4. Update CORS_ORIGINS when you have your frontend URL"
echo ""
