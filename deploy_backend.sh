#!/bin/bash
# Phase 2: Backend Deployment Script
# Deploys FastAPI backend to Azure Container Apps

set -e  # Exit on error

echo "======================================"
echo "Phase 2: Backend Deployment"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REGISTRY_NAME="kraftdintel"
ACR_URL="${REGISTRY_NAME}.azurecr.io"
IMAGE_NAME="${ACR_URL}/kraftdintel:latest"
RESOURCE_GROUP="kraftdintel-rg"
CONTAINER_APP="kraftdintel-app"
CONTAINER_ENV="kraftdintel-env"

echo -e "${CYAN}Configuration:${NC}"
echo "  Registry: ${REGISTRY_NAME}"
echo "  ACR URL: ${ACR_URL}"
echo "  Image: ${IMAGE_NAME}"
echo "  Container App: ${CONTAINER_APP}"
echo "  Resource Group: ${RESOURCE_GROUP}"
echo ""

# Step 1: Login to ACR
echo -e "${CYAN}Step 1: Logging in to Azure Container Registry...${NC}"
az acr login --name ${REGISTRY_NAME}
echo -e "${GREEN}✅ Logged in to ACR${NC}"
echo ""

# Step 2: Build image in Azure (no local Docker required)
echo -e "${CYAN}Step 2: Building Docker image in Azure...${NC}"
echo "This builds the image using Azure cloud compute"
az acr build \
  --registry ${REGISTRY_NAME} \
  --image kraftdintel:latest \
  --file backend/Dockerfile \
  backend/ \
  --quiet

echo -e "${GREEN}✅ Docker image built successfully${NC}"
echo ""

# Step 3: Deploy to Container App
echo -e "${CYAN}Step 3: Deploying to Container App...${NC}"
az containerapp update \
  --resource-group ${RESOURCE_GROUP} \
  --name ${CONTAINER_APP} \
  --image ${IMAGE_NAME} \
  --set-env-vars \
    COSMOS_URL="@keyvaultref(secretUri=https://kraftdintel-kv.vault.azure.net/secrets/cosmos-url/)" \
    COSMOS_KEY="@keyvaultref(secretUri=https://kraftdintel-kv.vault.azure.net/secrets/cosmos-key/)" \
    STORAGE_CONNECTION_STRING="@keyvaultref(secretUri=https://kraftdintel-kv.vault.azure.net/secrets/storage-connection-string/)" \
    OPENAI_API_KEY="@keyvaultref(secretUri=https://kraftdintel-kv.vault.azure.net/secrets/openai-api-key/)" \
    ENVIRONMENT="production"

echo -e "${GREEN}✅ Container App updated with new image${NC}"
echo ""

# Step 4: Verify deployment
echo -e "${CYAN}Step 4: Verifying deployment...${NC}"
sleep 10  # Give it time to start rolling out

STATUS=$(az containerapp show \
  --resource-group ${RESOURCE_GROUP} \
  --name ${CONTAINER_APP} \
  --query "properties.provisioningState" \
  -o tsv)

if [ "$STATUS" == "Succeeded" ]; then
  echo -e "${GREEN}✅ Container App deployed successfully${NC}"
else
  echo -e "${YELLOW}⚠️  Status: ${STATUS}${NC}"
fi

# Get the FQDN
FQDN=$(az containerapp show \
  --resource-group ${RESOURCE_GROUP} \
  --name ${CONTAINER_APP} \
  --query "properties.configuration.ingress.fqdn" \
  -o tsv)

echo ""
echo -e "${GREEN}======================================"
echo "✅ PHASE 2: BACKEND DEPLOYMENT COMPLETE"
echo "======================================${NC}"
echo ""
echo -e "${CYAN}Backend URL:${NC}"
echo "  https://${FQDN}"
echo ""
echo -e "${CYAN}Environment Variables:${NC}"
echo "  ✅ COSMOS_URL (from Key Vault)"
echo "  ✅ COSMOS_KEY (from Key Vault)"
echo "  ✅ STORAGE_CONNECTION_STRING (from Key Vault)"
echo "  ✅ OPENAI_API_KEY (from Key Vault)"
echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo "  1. Wait 2-3 minutes for container to start"
echo "  2. Test backend health: curl https://${FQDN}/health"
echo "  3. Verify frontend-to-backend connectivity"
echo "  4. Proceed to Phase 3: Integration Testing"
echo ""
