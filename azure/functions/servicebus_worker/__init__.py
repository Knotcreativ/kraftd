import logging
import json
import os
import asyncio

import azure.functions as func
from azure.servicebus.aio import ServiceBusClient
from azure.identity.aio import DefaultAzureCredential

# Import the orchestrator/pipeline
try:
    from backend.document_processing.orchestrator import ExtractionPipeline
except Exception as e:
    ExtractionPipeline = None
    logging.warning(f"ExtractionPipeline import failed: {e}")

async def main(msg: func.ServiceBusMessage):
    logging.info("Service Bus message received for document processing")
    body = msg.get_body().decode('utf-8')
    payload = json.loads(body)

    blob_url = payload.get('blob_url')

    if not blob_url:
        logging.error("No blob_url in message; skipping")
        return

    # Download blob or pass blob_url to extraction service
    # For a simple start, call the existing ExtractionPipeline with text retrieved by a small helper.
    if ExtractionPipeline is None:
        logging.error("ExtractionPipeline is not available. Ensure backend package is importable in Function App.")
        return

    try:
        # Placeholder: implement blob fetch -> text extraction logic or call a service endpoint
        # For now we simulate by giving the pipeline minimal input
        pipeline = ExtractionPipeline()
        # run in a thread to avoid blocking
        result = await asyncio.to_thread(pipeline.process_document, "[placeholder text from blob]", blob_url)

        logging.info(f"Pipeline result success={result.success}, stage_failed={result.stage_failed}")

        # TODO: Update Cosmos DB document metadata (processing_started_at / completed_at / status)

    except Exception as e:
        logging.exception(f"Processing failed for blob {blob_url}: {e}")
