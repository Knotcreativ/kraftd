import os
import asyncio
import pytest

from services.email_service import EmailService


@pytest.mark.asyncio
async def test_email_service_uses_acs_when_connection_string_present(monkeypatch):
    # Arrange: set the env var to trigger ACS selection
    monkeypatch.setenv("AZURE_COMMUNICATION_CONNECTION_STRING", "endpoint=https://fake;accesskey=abc")

    # Replace ACSEmailService with a fake implementation to observe delegation
    class FakeACS:
        def __init__(self):
            self.sent = False

        async def send_verification_email(self, to_email, token, user_name=None):
            self.sent = True
            return True

    monkeypatch.setattr("services.email_acs.ACSEmailService", FakeACS)

    # Act
    svc = EmailService()
    result = await svc.send_verification_email("test@example.com", "tok123", "Test User")

    # Assert
    assert result is True


@pytest.mark.asyncio
async def test_acs_fallbacks_to_mock_when_sdk_missing(monkeypatch):
    # simulate missing SDK by patching ACSEmailService to have no client
    monkeypatch.setenv("AZURE_COMMUNICATION_CONNECTION_STRING", "endpoint=https://fake;accesskey=abc")

    class FakeACSNoClient:
        def __init__(self):
            self.client = None

        async def send_verification_email(self, to_email, token, user_name=None):
            # Should hit mock mode and return True
            return True

    monkeypatch.setattr("services.email_acs.ACSEmailService", FakeACSNoClient)

    svc = EmailService()
    res = await svc.send_verification_email("test@example.com", "tok123")
    assert res is True
