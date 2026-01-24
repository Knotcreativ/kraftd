import os
import json
import pytest
from types import SimpleNamespace

pytestmark = pytest.mark.asyncio


async def test_blob_event_enqueues_message(monkeypatch):
    """Simulate an Event Grid blob-created event and assert we enqueue to Service Bus."""
    messages = []

    class FakeSender:
        async def send_messages(self, msg):
            # Try to extract body if available, else str()
            try:
                body = getattr(msg, 'body', None)
                if body:
                    # body might be a list-like
                    messages.append(json.dumps(body))
                else:
                    messages.append(str(msg))
            except Exception:
                messages.append(str(msg))

    class FakeSenderCtx:
        async def __aenter__(self):
            return FakeSender()

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def get_queue_sender(self, queue_name):
            return FakeSenderCtx()

    # Environment
    monkeypatch.setenv("SERVICE_BUS_FQDN", "fake.servicebus.windows.net")
    monkeypatch.setenv("SERVICE_BUS_QUEUE", "documents-processing")

    # Patch ServiceBusClient to use the fake client
    import azure.servicebus.aio as sbaio

    monkeypatch.setattr(sbaio, "ServiceBusClient", lambda *args, **kwargs: FakeClient())

    # Construct a fake EventGridEvent-like object
    fake_data = {"url": "http://127.0.0.1:10000/devstoreaccount1/container/blob.pdf"}
    fake_event = SimpleNamespace(
        event_type="Microsoft.Storage.BlobCreated",
        subject="/blobServices/default/containers/container/blobs/blob.pdf",
        id="evt-1",
        get_json=lambda: fake_data,
    )

    # Invoke the blob event handler
    from azure.functions.blob_event_handler import main as blob_main

    await blob_main(fake_event)

    # Assert a message was enqueued that contains the blob url
    assert len(messages) == 1, "Expected one Service Bus message to be enqueued"
    assert "blob.pdf" in messages[0] or "http://127.0.0.1" in messages[0]


async def test_servicebus_worker_calls_pipeline(monkeypatch):
    """Simulate a Service Bus message to the worker and assert the ExtractionPipeline is invoked."""

    called = {"invoked": False}

    class DummyResult:
        def __init__(self):
            self.success = True
            self.stage_failed = None

    class DummyPipeline:
        def process_document(self, text, source_file):
            called["invoked"] = True
            return DummyResult()

    # Patch the orchestrator's ExtractionPipeline class
    import backend.document_processing.orchestrator as orch

    monkeypatch.setattr(orch, "ExtractionPipeline", DummyPipeline)

    # Fake ServiceBus message
    class FakeMsg:
        def __init__(self, payload):
            self._payload = payload

        def get_body(self):
            return json.dumps(self._payload).encode("utf-8")

    payload = {"blob_url": "http://example.com/blob.pdf"}
    msg = FakeMsg(payload)

    from azure.functions.servicebus_worker import main as worker_main

    await worker_main(msg)

    assert called["invoked"], "ExtractionPipeline.process_document was not invoked by worker"
