"""Send a single test email using ACSEmailService (used for smoke tests)."""
import os
import asyncio
import logging
from services.email_acs import ACSEmailService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    recipient = os.getenv("ACS_TEST_RECIPIENT")
    if not recipient:
        logger.error("ACS_TEST_RECIPIENT env var is required for this script")
        raise SystemExit(2)

    svc = ACSEmailService()
    ok = await svc.send_verification_email(recipient, "smoke-test-token", "Smoke Test")
    if not ok:
        logger.error("Failed to send smoke test email via ACS")
        raise SystemExit(1)

    logger.info("Smoke test email send initiated (check recipient inbox)")

if __name__ == '__main__':
    asyncio.run(main())
