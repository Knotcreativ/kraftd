@description('Location for all resources')
param location string = resourceGroup().location
param prefix string = 'kraftd'

var storageAccountName = toLower('${prefix}storage${uniqueString(resourceGroup().id)}')
var serviceBusNamespace = '${prefix}-sb-${uniqueString(resourceGroup().id)}'
var serviceBusQueue = 'documents-processing'
var appServicePlanName = '${prefix}-plan'
var functionAppName = '${prefix}-functions'
var appInsightsName = '${prefix}-ai'

// Storage Account
resource storage 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

// Blob container for documents
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2022-09-01' = {
  name: '${storage.name}/default'
}

resource documentsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2022-09-01' = {
  name: '${storage.name}/default/documents'
  properties: {
    publicAccess: 'None'
  }
  dependsOn: [blobService]
}

// Service Bus Namespace
resource sbNamespace 'Microsoft.ServiceBus/namespaces@2021-11-01' = {
  name: serviceBusNamespace
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {}
}

resource sbQueue 'Microsoft.ServiceBus/namespaces/queues@2021-11-01' = {
  name: '${sbNamespace.name}/${serviceBusQueue}'
  properties: {
    enablePartitioning: false
    lockDuration: 'PT30S'
  }
  dependsOn: [sbNamespace]
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}

// App Service Plan (Linux, Consumption plan for Functions should use ElasticPremium or Consumption via kind='functionapp' later)
resource plan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: appServicePlanName
  location: location
  sku: {
    // For production, consider ElasticPremium or PremiumV3. For simplicity we use EP1.
    name: 'EP1'
    tier: 'ElasticPremium'
    capacity: 1
  }
}

// Function App with system-assigned identity
resource functionApp 'Microsoft.Web/sites@2022-03-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: plan.id
    siteConfig: {
      appSettings: [
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        {
          name: 'AzureWebJobsStorage'
          value: storage.listKeys().keys[0].value
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'SERVICE_BUS_QUEUE'
          value: serviceBusQueue
        }
        {
          name: 'SERVICE_BUS_FQDN'
          value: '${sbNamespace.name}.servicebus.windows.net'
        }
      ]
    }
  }
  dependsOn: [plan, appInsights, storage]
}

// Azure Communication Services (Email)
resource communication 'Microsoft.Communication/communicationServices@2021-10-01' = {
  name: '${prefix}-comm'
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {}
}

output functionAppName string = functionApp.name
output functionPrincipalId string = functionApp.identity.principalId
output storageAccountName string = storage.name
output serviceBusNamespace string = sbNamespace.name
output serviceBusQueue string = sbQueue.name
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output communicationServiceName string = communication.name
