#!/usr/bin/env bash
set -euo pipefail

# Parameters
RG=${1:-kraftdintel-rg}
NAME=${2:-kraftd-comm}
LOCATION=${3:-uaenorth}

echo "Deploying ACS resource '$NAME' to resource group '$RG' in $LOCATION..."
az deployment group create -g "$RG" -f infrastructure/azure/main.bicep --parameters prefix=kraftd location=$LOCATION --verbose

# Get resource id
RES_ID=$(az resource show -g "$RG" -n "$NAME" --resource-type Microsoft.Communication/communicationServices --query id -o tsv)
if [ -z "$RES_ID" ]; then
  echo "Failed to find ACS resource. Exiting." >&2
  exit 1
fi

echo "Invoking listKeys action to obtain connection string..."
KEY_JSON=$(az resource invoke-action --action listKeys --ids "$RES_ID" --api-version 2021-10-01 -o json)
PRIMARY=$(echo "$KEY_JSON" | jq -r '.primaryConnectionString // empty')
if [ -z "$PRIMARY" ]; then
  echo "Failed to extract primary connection string from the ACS listKeys response:" >&2
  echo "$KEY_JSON" >&2
  exit 1
fi

echo "Updating GitHub secret AZURE_COMMUNICATION_CONNECTION_STRING (value not shown)..."
gh secret set AZURE_COMMUNICATION_CONNECTION_STRING --body "$PRIMARY"

echo "ACS deployed and GH secret updated (AZURE_COMMUNICATION_CONNECTION_STRING)."