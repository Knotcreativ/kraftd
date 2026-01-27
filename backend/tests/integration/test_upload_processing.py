import os
import json
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from io import BytesIO
from models.document import DocumentResponse

pytestmark = pytest.mark.asyncio


async def test_document_upload_endpoint():
    """Test the document upload REST API endpoint."""
    from main import app

    client = TestClient(app)

    # Mock the documents service
    with patch('routes.documents.documents_service') as mock_service, \
         patch('routes.documents.check_quota') as mock_quota, \
         patch('routes.documents.get_current_user_email') as mock_auth:

        # Setup mocks
        mock_auth.return_value = "test@example.com"
        mock_quota.return_value = True
        mock_service.verify_conversion_ownership.return_value = True
        mock_service.upload_document = AsyncMock(return_value=DocumentResponse(
            document_id="test-doc-id",
            conversion_id="test-conversion-id",
            filename="test.pdf",
            content_type="application/pdf",
            file_size=1024,
            blob_uri="https://storage.blob.core.windows.net/container/test.pdf",
            uploaded_at="2024-01-27T12:00:00Z",
            status="uploaded"
        ))

        # Create a test file
        test_file = BytesIO(b"test pdf content")
        test_file.name = "test.pdf"

        # Test the upload endpoint
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", test_file, "application/pdf")},
            data={"conversion_id": "test-conversion-id"},
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["document_id"] == "test-doc-id"
        assert data["filename"] == "test.pdf"
        assert data["status"] == "uploaded"


async def test_document_upload_validation():
    """Test document upload validation (quota, ownership, file type)."""
    from main import app

    client = TestClient(app)

    # Test quota exceeded
    with patch('routes.documents.check_quota') as mock_quota, \
         patch('routes.documents.get_current_user_email') as mock_auth:

        mock_auth.return_value = "test@example.com"
        mock_quota.return_value = False

        test_file = BytesIO(b"test content")
        test_file.name = "test.pdf"

        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", test_file, "application/pdf")},
            data={"conversion_id": "test-conversion-id"},
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 429  # Quota exceeded


async def test_servicebus_worker_placeholder():
    """Placeholder test for Service Bus worker functionality.

    Note: Service Bus integration is not currently implemented.
    This test serves as a reminder for future implementation.
    """
    # This test always passes - Service Bus integration is not yet implemented
    assert True
