@description('Prefix for resource names')
param prefix string = 'kraftd'

resource communication 'Microsoft.Communication/communicationServices@2023-03-31' = {
  name: '${prefix}-comm'
  location: 'global'
  properties: {
    dataLocation: 'UnitedStates'
  }
}

output communicationServiceName string = communication.name
