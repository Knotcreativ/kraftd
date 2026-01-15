# Environment-specific configurations

## Development Environment (local.settings.json for Azure Functions)
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "",
    "COSMOS_DB_ENDPOINT": "https://localhost:8081/",
    "COSMOS_DB_KEY": "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLMUA7W0/Z0w=",
    "COSMOS_DB_DATABASE": "kraftdintel",
    "COSMOS_DB_CONTAINER": "documents",
    "JWT_SECRET_KEY": "dev-secret-key-change-in-production",
    "ENVIRONMENT": "development",
    "DEBUG": "True",
    "LOG_LEVEL": "DEBUG",
    "APPINSIGHTS_INSTRUMENTATION_KEY": ""
  },
  "ConnectionStrings": {
    "DefaultConnection": "AccountEndpoint=https://localhost:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLMUA7W0/Z0w=;"
  }
}

## Staging Environment Bicep Parameters
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "appServiceName": {
      "value": "kraftdintel-staging"
    },
    "environment": {
      "value": "staging"
    },
    "sku": {
      "value": "S1"
    },
    "location": {
      "value": "eastus"
    },
    "cosmosDbAccountName": {
      "value": "kraftdintel-cosmos-staging"
    },
    "cosmosDbDatabaseName": {
      "value": "kraftdintel"
    },
    "keyVaultName": {
      "value": "kraftdintel-kv-staging"
    },
    "registryServer": {
      "value": "kraftdintelregistry.azurecr.io"
    },
    "dockerImageTag": {
      "value": "latest"
    }
  }
}

## Production Environment Bicep Parameters
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "appServiceName": {
      "value": "kraftdintel-prod"
    },
    "environment": {
      "value": "prod"
    },
    "sku": {
      "value": "P1V2"
    },
    "location": {
      "value": "eastus"
    },
    "cosmosDbAccountName": {
      "value": "kraftdintel-cosmos-prod"
    },
    "cosmosDbDatabaseName": {
      "value": "kraftdintel"
    },
    "keyVaultName": {
      "value": "kraftdintel-kv-prod"
    },
    "registryServer": {
      "value": "kraftdintelregistry.azurecr.io"
    },
    "dockerImageTag": {
      "value": "v1.0.0"
    }
  }
}
