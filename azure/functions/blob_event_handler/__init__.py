import logging
import os
import json

import azure.functions as func
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
from azure.identity.aio import DefaultAzureCredential

# Environment variables (set in Function App configuration)
SERVICE_BUS_FQDN = os.environ.get("SERVICE_BUS_FQDN")  # e.g. <namespace>.servicebus.windows.net
SERVICE_BUS_QUEUE = os.environ.get("SERVICE_BUS_QUEUE", "documents-processing")

async def main(event: func.EventGridEvent):
    logging.info("Blob event received")
    data = event.get_json()

    # Basic validation
    event_type = event.event_type
    subject = event.subject

    logging.info(f"Event type: {event_type}, subject: {subject}")

    if event_type not in ("Microsoft.Storage.BlobCreated", "Microsoft.Storage.BlobCreatedV2"):
        logging.warning("Ignoring non-blob-create event")
        return

    # Extract useful fields
    blob_url = data.get("url") or data.get("data", {}).get("url")
    if not blob_url:
        logging.error("No blob url found in event payload")
        return

    # Build message payload; add more fields as needed
    message_payload = {
        "blob_url": blob_url,
        "subject": subject,
        "event_id": event.id
    }

    # Send message to Service Bus queue using Managed Identity (DefaultAzureCredential)
    if not SERVICE_BUS_FQDN:
        logging.error("SERVICE_BUS_FQDN not configured. Skipping enqueue.")
        return

    try:
        credential = DefaultAzureCredential()
        async with ServiceBusClient(fully_qualified_namespace=SERVICE_BUS_FQDN, credential=credential) as client:
            async with client.get_queue_sender(queue_name=SERVICE_BUS_QUEUE) as sender:
                msg = ServiceBusMessage(json.dumps(message_payload))
                await sender.send_messages(msg)
                logging.info(f"Enqueued message to {SERVICE_BUS_QUEUE}: {message_payload}")
        await credential.close()
    except Exception as e:
        logging.exception(f"Failed to enqueue message to Service Bus: {e}")
