metadata description = 'Deploy Kraftd Docs - AI-Powered Document Intelligence SaaS to Azure'

@minLength(3)
@maxLength(24)
@metadata({
  description: 'Name of the App Service'
})
param appServiceName string

@allowed([
  'dev'
  'staging'
  'prod'
])
@metadata({
  description: 'Deployment environment'
})
param environment string = 'dev'

@allowed([
  'B1'
  'S1'
  'P1V2'
])
@metadata({
  description: 'App Service plan SKU'
})
param sku string = 'B1'

@metadata({
  description: 'Azure region for resources'
})
param location string = resourceGroup().location

@metadata({
  description: 'Container registry server address'
})
param registryServer string

@metadata({
  description: 'Docker image tag'
})
param dockerImageTag string = 'latest'

// Reserved parameters for future use
// @minLength(3)
// @maxLength(44)
// @metadata({
//   description: 'Cosmos DB account name - reserved for future connection string configuration'
// })
// param cosmosDbAccountName string = 'reserved'

// @metadata({
//   description: 'Cosmos DB database name - reserved for future configuration'
// })
// param cosmosDbDatabaseName string = 'kraftdintel'

// @minLength(3)
// @maxLength(24)
// @metadata({
//   description: 'Key Vault name - reserved for future secret management integration'
// })
// param keyVaultName string = 'reserved' // Currently using managed identity

var appServicePlanName = '${appServiceName}-plan'
var appInsightsName = '${appServiceName}-insights'
var storageAccountName = '${replace(appServiceName, '-', '')}storage'

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2021-06-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
  }
  tags: {
    environment: environment
  }
}

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2021-02-01' = {
  name: appServicePlanName
  location: location
  kind: 'linux'
  sku: {
    name: sku
    capacity: 1
  }
  properties: {
    reserved: true
  }
  tags: {
    environment: environment
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    RetentionInDays: 30
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
  tags: {
    environment: environment
  }
}

// App Service
resource appService 'Microsoft.Web/sites@2021-02-01' = {
  name: appServiceName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'DOCKER|${registryServer}/kraftdintel:${dockerImageTag}'
      alwaysOn: true
      http20Enabled: true
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_URL'
          value: 'https://${registryServer}'
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_USERNAME'
          value: registryServer
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'ApplicationInsightsAgent_EXTENSION_VERSION'
          value: '~3'
        }
        {
          name: 'XDT_MicrosoftApplicationInsights_Mode'
          value: 'recommended'
        }
      ]
    }
  }
  tags: {
    environment: environment
  }
}

// App Service Configuration
resource appServiceConfig 'Microsoft.Web/sites/config@2021-02-01' = {
  parent: appService
  name: 'web'
  properties: {
    numberOfWorkers: 1
    defaultDocuments: []
    netFrameworkVersion: 'v4.0'
    requestTracingEnabled: false
    remoteDebuggingEnabled: false
    httpLoggingEnabled: true
    detailedErrorLoggingEnabled: true
  }
}

// App Service Diagnostic Settings
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2017-05-01-preview' = {
  name: 'app-service-diagnostics'
  scope: appService
  properties: {
    logs: [
      {
        category: 'AppServiceHTTPLogs'
        enabled: true
      }
      {
        category: 'AppServiceConsoleLogs'
        enabled: true
      }
    ]
    workspaceId: ''
  }
}

// Outputs
output appServiceUrl string = 'https://${appService.properties.defaultHostName}'
output appServiceName string = appServiceName
output appInsightsKey string = appInsights.properties.InstrumentationKey
