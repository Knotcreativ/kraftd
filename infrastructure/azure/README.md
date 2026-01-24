# Infra: Azure deployment for automated document processing

This folder contains a Bicep template and a PowerShell deployment script to provision the minimal infra needed to run the Azure Functions event-driven pipeline:

- `main.bicep` - Bicep template that provisions:
  - Storage Account + `documents` container
  - Service Bus Namespace + `documents-processing` queue
  - Application Insights
  - App Service Plan + Function App (Python) with system-assigned managed identity

- `deploy_function_infra.ps1` - PowerShell script to deploy the Bicep template and wire up role assignments and Event Grid subscription.

Quick start (PowerShell):

1. Login and select subscription:
   ```powershell
   az login
   az account set --subscription <SUBSCRIPTION_ID>
   ```

2. Run deployment script (adjust resource group & location if needed):
   ```powershell
   ./deploy_function_infra.ps1 -rgName kraftd-rg -location eastus2 -prefix kraftd
   ```

3. Post-deploy checks & manual steps:
   - Confirm managed identity roles were created:
     - `Storage Blob Data Reader` on the storage account
     - `Azure Service Bus Data Sender` and `Azure Service Bus Data Receiver` on the Service Bus namespace
   - If you prefer to use connection strings instead of Managed Identity for Service Bus, set `SERVICEBUS_CONNECTION` in Function App settings (but prefer MI + RBAC).
   - In the Function App, ensure `blob_event_handler` and `servicebus_worker` functions are deployed and working (zip deploy or CI pipeline).

4. Test flow:
   - Upload a file to the `documents` container and verify:
     - Event Grid triggers `blob_event_handler` which enqueues a Service Bus message
     - `servicebus_worker` picks up the message and calls the `ExtractionPipeline`
     - Document status is updated in Cosmos DB (processing->completed)

Notes:
- Use Key Vault references for production secrets (Service Bus connection string, Cosmos DB keys) and set appropriate access policies.
- Consider Durable Functions if you need orchestration, long-running processing, or async status endpoints.
- The bicep template sets app settings such as `SERVICE_BUS_FQDN` and `AzureWebJobsStorage` directly; consider using Key Vault references for production.

