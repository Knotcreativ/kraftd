"""Azure Communication Services Email adapter for KraftdIntel."""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from azure.communication.email import EmailClient
    _HAS_ACS = True
except Exception:
    EmailClient = None
    _HAS_ACS = False


class ACSEmailService:
    """Adapter that sends emails using Azure Communication Services Email API."""

    def __init__(self):
        self.connection_string = os.getenv("AZURE_COMMUNICATION_CONNECTION_STRING")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@kraftdintel.com")
        self.verification_url = os.getenv("VERIFICATION_URL", "http://localhost:3000/verify-email")

        if not self.connection_string or not _HAS_ACS:
            logger.warning("AZURE_COMMUNICATION_CONNECTION_STRING not configured or ACS SDK missing. Email service will use mock mode.")
            self.client = None
        else:
            self.client = EmailClient.from_connection_string(self.connection_string)

    async def send_verification_email(self, to_email: str, verification_token: str, user_name: Optional[str] = None) -> bool:
        verification_link = f"{self.verification_url}?token={verification_token}"
        name_text = user_name or to_email.split('@')[0]

        subject = "Verify Your Email - KraftdIntel"
        html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h1 style="color: #667eea;">Welcome to KraftdIntel, {name_text}!</h1>
                        <p>To complete your account setup and verify your email address, click the button below:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{verification_link}" style="background-color: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Verify Email Address</a>
                        </div>
                        <p>Or copy and paste this link in your browser:</p>
                        <p style="word-break: break-all; background-color: #f5f5f5; padding: 10px; border-radius: 5px;">{verification_link}</p>
                    </div>
                </body>
            </html>
        """

        if not self.client:
            logger.info(f"[MOCK ACS EMAIL] Verification email to {to_email}")
            logger.debug(f"[MOCK ACS EMAIL] Link: {verification_link}")
            return True

        try:
            # Build request payload per ACS Email REST shape
            message = {
                "senderAddress": self.from_email,
                "senderDisplayName": os.getenv("ACS_SENDER_DISPLAY_NAME", "Kraftd"),
                "content": {"subject": subject, "html": html_content},
                "recipients": {"to": [{"address": to_email}]}
            }

            poller = self.client.begin_send(message)
            result = poller.result()
            logger.info(f"ACS email send initiated, operation id: {result.id}")
            return True
        except Exception as e:
            logger.error(f"Error sending ACS verification email: {e}")
            return False

    async def send_resend_verification_email(self, to_email: str, verification_token: str, user_name: Optional[str] = None) -> bool:
        return await self.send_verification_email(to_email, verification_token, user_name)

    async def send_password_reset_email(self, to_email: str, reset_token: str, user_name: Optional[str] = None) -> bool:
        reset_url = os.getenv("RESET_PASSWORD_URL", "http://localhost:3000/reset-password")
        reset_link = f"{reset_url}?token={reset_token}"
        name_text = user_name or to_email.split('@')[0]

        subject = "Reset Your Password - KraftdIntel"
        html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h1 style="color: #667eea;">Password Reset Request</h1>
                        <p>Hi {name_text},</p>
                        <p>We received a request to reset your password. If you didn't make this request, you can ignore this email.</p>
                        <div style="text-align: center; margin: 30px 0;"><a href="{reset_link}" style="background-color: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold;">Reset Your Password</a></div>
                        <p>Or copy and paste this link in your browser:</p>
                        <p style="word-break: break-all; color: #666;">{reset_link}</p>
                    </div>
                </body>
            </html>
        """

        if not self.client:
            logger.info(f"[MOCK ACS EMAIL] Password reset to {to_email}")
            logger.debug(f"[MOCK ACS EMAIL] Reset Link: {reset_link}")
            return True

        try:
            message = {
                "senderAddress": self.from_email,
                "senderDisplayName": os.getenv("ACS_SENDER_DISPLAY_NAME", "Kraftd"),
                "content": {"subject": subject, "html": html_content},
                "recipients": {"to": [{"address": to_email}]}
            }
            poller = self.client.begin_send(message)
            result = poller.result()
            logger.info(f"ACS password reset email send initiated, operation id: {result.id}")
            return True
        except Exception as e:
            logger.error(f"Error sending ACS password reset email: {e}")
            return False
