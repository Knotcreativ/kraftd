@description('Prefix for resource names')
param prefix string = 'kraftd'

resource communication 'Microsoft.Communication/communicationServices@2023-04-01' = {
  name: '${prefix}-comm'
  location: 'global'
  sku: {
    name: 'Standard'
  }
  properties: {}
}

output communicationServiceName string = communication.name
