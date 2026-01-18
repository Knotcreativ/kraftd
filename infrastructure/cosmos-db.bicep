metadata description = 'Deploy Cosmos DB for KraftdIntel application'

@minLength(3)
@maxLength(44)
@metadata({
  description: 'Cosmos DB account name'
})
param accountName string

@metadata({
  description: 'Database name'
})
param databaseName string = 'kraftdintel'

@metadata({
  description: 'Container name'
})
param containerName string = 'documents'

@metadata({
  description: 'Partition key path'
})
param partitionKeyPath string = '/owner_email'

@metadata({
  description: 'Azure region'
})
param location string = resourceGroup().location

@minValue(400)
@maxValue(1000000)
@metadata({
  description: 'Provisioned throughput (RU/s)'
})
param throughput int = 400

@allowed([
  'dev'
  'staging'
  'prod'
])
@metadata({
  description: 'Environment type'
})
param environment string = 'dev'

// Cosmos DB Account
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2021-10-15' = {
  name: accountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
      maxIntervalInSeconds: 5
      maxStalenessPrefix: 100
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    enableMultipleWriteLocations: false
    enableFreeTier: false
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
  }
  tags: {
    environment: environment
  }
}

// Database
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2021-10-15' = {
  parent: cosmosDbAccount
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
    options: {
      throughput: throughput
    }
  }
}

// Container with TTL and indexes
resource container 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2021-10-15' = {
  parent: database
  name: containerName
  properties: {
    resource: {
      id: containerName
      partitionKey: {
        paths: [
          partitionKeyPath
        ]
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'Consistent'
        includedPaths: [
          {
            path: '/*'
            indexes: [
              {
                kind: 'Range'
                dataType: 'String'
                precision: -1
              }
              {
                kind: 'Range'
                dataType: 'Number'
                precision: -1
              }
            ]
          }
        ]
        excludedPaths: [
          {
            path: '/_etag/?'
          }
        ]
      }
      defaultTtl: 7776000
      conflictResolutionPolicy: {
        mode: 'LastWriterWins'
        conflictResolutionPath: '/_ts'
      }
    }
  }
}

@description('Cosmos DB endpoint URL')
output cosmosDbEndpoint string = cosmosDbAccount.properties.documentEndpoint
