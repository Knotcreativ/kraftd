"""Send a single test email using ACSEmailService (used for smoke tests)."""
import os
import asyncio
import logging
import sys
from pathlib import Path

# Ensure script can import backend package when run from workflow or local
try:
    from backend.services.email_acs import ACSEmailService
except Exception:
    repo_root = Path(__file__).resolve().parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    try:
        from backend.services.email_acs import ACSEmailService
    except Exception as e:
        logging.error("Failed to import ACSEmailService: %s", e)
        raise

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
