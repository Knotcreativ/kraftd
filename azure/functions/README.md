# Azure Functions: Blob Event Enqueuer & Service Bus Worker

This folder contains starter Azure Functions to implement the automated upload -> process flow:

- `blob_event_handler` — Event Grid/Blob event handler that enqueues a message into Service Bus
- `servicebus_worker` — Service Bus queue triggered worker that calls the extraction pipeline

Environment variables (Function App configuration):
- `SERVICE_BUS_FQDN` — Service Bus namespace FQDN (e.g. myns.servicebus.windows.net)
- `SERVICE_BUS_QUEUE` — queue name (default: `documents-processing`)
- `SERVICEBUS_CONNECTION` — Service Bus connection string (if not using Managed Identity)

Deployment notes:
- Use Managed Identity + RBAC where possible (DefaultAzureCredential) for secure auth.
- Add Application Insights to the Function App for telemetry and alerting.
- Ensure the Function App has network access to Blob storage and Cosmos DB (VNet rules / service endpoints) if required.
