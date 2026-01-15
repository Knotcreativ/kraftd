metadata:
  description: 'Deploy KraftdIntel infrastructure and application to Azure'
  template: '@jinja'

parameters:
  appServiceName:
    type: string
    metadata:
      description: 'Name of the App Service'
    minLength: 3
    maxLength: 24

  environment:
    type: string
    defaultValue: 'dev'
    allowedValues:
      - 'dev'
      - 'staging'
      - 'prod'
    metadata:
      description: 'Deployment environment'

  sku:
    type: string
    defaultValue: 'B1'
    allowedValues:
      - 'B1'
      - 'S1'
      - 'P1V2'
    metadata:
      description: 'App Service plan SKU'

  location:
    type: string
    defaultValue: '[resourceGroup().location]'
    metadata:
      description: 'Azure region for resources'

  registryServer:
    type: string
    metadata:
      description: 'Container registry server address'

  dockerImageTag:
    type: string
    defaultValue: 'latest'
    metadata:
      description: 'Docker image tag'

  cosmosDbAccountName:
    type: string
    metadata:
      description: 'Cosmos DB account name'
    minLength: 3
    maxLength: 44

  cosmosDbDatabaseName:
    type: string
    defaultValue: 'kraftdintel'
    metadata:
      description: 'Cosmos DB database name'

  keyVaultName:
    type: string
    metadata:
      description: 'Key Vault name'
    minLength: 3
    maxLength: 24

variables:
  appServicePlanName: '[concat(parameters(''appServiceName''), ''-plan'')]'
  appInsightsName: '[concat(parameters(''appServiceName''), ''-insights'')]'
  storageAccountName: '[concat(replace(parameters(''appServiceName''), ''-'', ''''), ''storage'')]'

resources:
  # Storage Account
  - type: Microsoft.Storage/storageAccounts
    apiVersion: '2021-06-01'
    name: '[variables(''storageAccountName'')]'
    location: '[parameters(''location'')]'
    kind: StorageV2
    sku:
      name: Standard_LRS
    properties:
      accessTier: Hot
      minimumTlsVersion: TLS1_2
    tags:
      environment: '[parameters(''environment'')]'

  # App Service Plan
  - type: Microsoft.Web/serverfarms
    apiVersion: '2021-02-01'
    name: '[variables(''appServicePlanName'')]'
    location: '[parameters(''location'')]'
    sku:
      name: '[parameters(''sku'')]'
      capacity: 1
    kind: linux
    properties:
      reserved: true
    tags:
      environment: '[parameters(''environment'')]'

  # Application Insights
  - type: Microsoft.Insights/components
    apiVersion: '2020-02-02'
    name: '[variables(''appInsightsName'')]'
    location: '[parameters(''location'')]'
    kind: web
    properties:
      Application_Type: web
      RetentionInDays: 30
      publicNetworkAccessForIngestion: Enabled
      publicNetworkAccessForQuery: Enabled
    tags:
      environment: '[parameters(''environment'')]'

  # App Service
  - type: Microsoft.Web/sites
    apiVersion: '2021-02-01'
    name: '[parameters(''appServiceName'')]'
    location: '[parameters(''location'')]'
    identity:
      type: SystemAssigned
    properties:
      serverFarmId: '[resourceId(''Microsoft.Web/serverfarms'', variables(''appServicePlanName''))]'
      siteConfig:
        linuxFxVersion: '[concat(''DOCKER|'', parameters(''registryServer''), ''/kraftdintel:'', parameters(''dockerImageTag''))]'
        alwaysOn: true
        http20Enabled: true
        minTlsVersion: '1.2'
        ftpsState: Disabled
        appSettings:
          - name: WEBSITES_ENABLE_APP_SERVICE_STORAGE
            value: 'false'
          - name: DOCKER_REGISTRY_SERVER_URL
            value: '[concat(''https://'', parameters(''registryServer''))]'
          - name: DOCKER_REGISTRY_SERVER_USERNAME
            value: '[parameters(''registryServer'')]'
          - name: DOCKER_REGISTRY_SERVER_PASSWORD
            value: '@Microsoft.KeyVault(VaultName=parameters(''keyVaultName'');SecretName=registry-password)'
          - name: APPINSIGHTS_INSTRUMENTATIONKEY
            value: '[reference(resourceId(''Microsoft.Insights/components'', variables(''appInsightsName'')), ''2020-02-02'').InstrumentationKey]'
          - name: ApplicationInsightsAgent_EXTENSION_VERSION
            value: ~3
          - name: XDT_MicrosoftApplicationInsights_Mode
            value: recommended
        connectionStrings:
          - name: DefaultConnection
            connectionString: '[concat(''AccountEndpoint=https://'', parameters(''cosmosDbAccountName''), ''.documents.azure.com:443/;AccountKey='', listKeys(resourceId(''Microsoft.DocumentDB/databaseAccounts'', parameters(''cosmosDbAccountName'')), ''2021-06-15'').primaryMasterKey)]'
            type: Custom
    dependsOn:
      - '[resourceId(''Microsoft.Web/serverfarms'', variables(''appServicePlanName''))]'
      - '[resourceId(''Microsoft.Insights/components'', variables(''appInsightsName''))]'
    tags:
      environment: '[parameters(''environment'')]'

  # App Service Configuration
  - type: Microsoft.Web/sites/config
    apiVersion: '2021-02-01'
    name: '[concat(parameters(''appServiceName''), ''/web'')]'
    properties:
      numberOfWorkers: 1
      defaultDocuments: []
      netFrameworkVersion: v4.0
      requestTracingEnabled: false
      remoteDebuggingEnabled: false
      httpLoggingEnabled: true
      detailedErrorLoggingEnabled: true
      publishingUsername: '[concat(''$'', parameters(''appServiceName''))]'
    dependsOn:
      - '[resourceId(''Microsoft.Web/sites'', parameters(''appServiceName''))]'

  # App Service Diagnostic Settings
  - type: Microsoft.Web/sites/providers/diagnosticSettings
    apiVersion: '2017-05-01-preview'
    name: '[concat(parameters(''appServiceName''), ''/Microsoft.Insights/default'')]'
    properties:
      logs:
        - category: AppServiceHTTPLogs
          enabled: true
          retentionPolicy:
            enabled: true
            days: 7
        - category: AppServiceConsoleLogs
          enabled: true
          retentionPolicy:
            enabled: true
            days: 7
      metrics:
        - category: AllMetrics
          enabled: true
          retentionPolicy:
            enabled: true
            days: 7
      workspaceId: '[resourceId(''Microsoft.OperationalInsights/workspaces'', concat(parameters(''appServiceName''), ''-workspace''))]'
    dependsOn:
      - '[resourceId(''Microsoft.Web/sites'', parameters(''appServiceName''))]'

outputs:
  appServiceUrl:
    type: string
    value: '[concat(''https://'', reference(resourceId(''Microsoft.Web/sites'', parameters(''appServiceName'')), ''2021-02-01'').defaultHostName)]'
    metadata:
      description: 'URL of the deployed App Service'

  appServiceName:
    type: string
    value: '[parameters(''appServiceName'')]'
    metadata:
      description: 'Name of the App Service'

  appInsightsKey:
    type: string
    value: '[reference(resourceId(''Microsoft.Insights/components'', variables(''appInsightsName'')), ''2020-02-02'').InstrumentationKey]'
    metadata:
      description: 'Application Insights instrumentation key'
