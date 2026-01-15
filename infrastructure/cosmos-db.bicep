metadata:
  description: 'Deploy Cosmos DB for KraftdIntel application'

parameters:
  accountName:
    type: string
    metadata:
      description: 'Cosmos DB account name'
    minLength: 3
    maxLength: 44

  databaseName:
    type: string
    defaultValue: 'kraftdintel'
    metadata:
      description: 'Database name'

  containerName:
    type: string
    defaultValue: 'documents'
    metadata:
      description: 'Container name'

  partitionKeyPath:
    type: string
    defaultValue: '/owner_email'
    metadata:
      description: 'Partition key path'

  location:
    type: string
    defaultValue: '[resourceGroup().location]'
    metadata:
      description: 'Azure region'

  throughput:
    type: int
    defaultValue: 400
    minValue: 400
    maxValue: 1000000
    metadata:
      description: 'Provisioned throughput (RU/s)'

  environment:
    type: string
    defaultValue: 'dev'
    allowedValues:
      - 'dev'
      - 'staging'
      - 'prod'

resources:
  # Cosmos DB Account
  - type: Microsoft.DocumentDB/databaseAccounts
    apiVersion: '2021-10-15'
    name: '[parameters(''accountName'')]'
    location: '[parameters(''location'')]'
    kind: GlobalDocumentDB
    properties:
      databaseAccountOfferType: Standard
      consistencyPolicy:
        defaultConsistencyLevel: Session
        maxIntervalInSeconds: 5
        maxStalenessPrefix: 100
      locations:
        - locationName: '[parameters(''location'')]'
          failoverPriority: 0
          isZoneRedundant: false
      enableMultipleWriteLocations: false
      enableFreeTier: false
      capabilities:
        - name: EnableServerless
    tags:
      environment: '[parameters(''environment'')]'

  # Database
  - type: Microsoft.DocumentDB/databaseAccounts/sqlDatabases
    apiVersion: '2021-10-15'
    name: '[concat(parameters(''accountName''), ''/'', parameters(''databaseName''))]'
    properties:
      resource:
        id: '[parameters(''databaseName'')]'
      options:
        throughput: '[parameters(''throughput'')]'
    dependsOn:
      - '[resourceId(''Microsoft.DocumentDB/databaseAccounts'', parameters(''accountName''))]'

  # Container with TTL and indexes
  - type: Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers
    apiVersion: '2021-10-15'
    name: '[concat(parameters(''accountName''), ''/'', parameters(''databaseName''), ''/'', parameters(''containerName''))]'
    properties:
      resource:
        id: '[parameters(''containerName'')]'
        partitionKey:
          paths:
            - '[parameters(''partitionKeyPath'')]'
          kind: Hash
        indexingPolicy:
          indexingMode: Consistent
          includedPaths:
            - path: /*
              indexes:
                - kind: Range
                  dataType: String
                  precision: -1
                - kind: Range
                  dataType: Number
                  precision: -1
          excludedPaths:
            - path: /''_etag''/?
        defaultTtl: 7776000  # 90 days in seconds
        conflictResolutionPolicy:
          mode: LastWriterWins
          conflictResolutionPath: /_ts
    dependsOn:
      - '[resourceId(''Microsoft.DocumentDB/databaseAccounts/sqlDatabases'', parameters(''accountName''), parameters(''databaseName''))]'

outputs:
  cosmosDbEndpoint:
    type: string
    value: '[reference(resourceId(''Microsoft.DocumentDB/databaseAccounts'', parameters(''accountName'')), ''2021-10-15'').documentEndpoint]'
    metadata:
      description: 'Cosmos DB endpoint URL'

  cosmosDbAccountKey:
    type: string
    value: '[listKeys(resourceId(''Microsoft.DocumentDB/databaseAccounts'', parameters(''accountName'')), ''2021-10-15'').primaryMasterKey]'
    metadata:
      description: 'Cosmos DB primary account key'
