"""Email service for sending verification emails via SendGrid."""

import os
import logging
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails. Chooses provider based on environment.

    - If `AZURE_COMMUNICATION_CONNECTION_STRING` is set, uses ACS adapter
    - Otherwise, uses SendGrid as previously
    """

    def __init__(self):
        # Prefer ACS if configured
        acs_conn = os.getenv("AZURE_COMMUNICATION_CONNECTION_STRING")
        if acs_conn:
            try:
                from services.email_acs import ACSEmailService
                self._impl = ACSEmailService()
                logger.info("Using Azure Communication Services for email")
                return
            except Exception:
                logger.warning("Failed to initialize ACSEmailService; falling back to SendGrid")

        # Fallback to SendGrid
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@kraftdintel.com")
        self.verification_url = os.getenv("VERIFICATION_URL", "http://localhost:3000/verify-email")
        
        if not self.api_key:
            logger.warning("SENDGRID_API_KEY not configured. Email service will use mock mode.")
        
        self.client = SendGridAPIClient(self.api_key) if self.api_key else None
        self._impl = None
    
    async def send_verification_email(
        self, 
        to_email: str, 
        verification_token: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send email verification link to user
        
        Args:
            to_email: Recipient email address
            verification_token: Token for verifying email
            user_name: Optional user name for personalization
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Build verification link
            verification_link = f"{self.verification_url}?token={verification_token}"
            
            # Use name in greeting if available
            name_text = user_name or to_email.split('@')[0]
            
            # Create email content
            subject = "Verify Your Email - KraftdIntel"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h1 style="color: #667eea;">Welcome to KraftdIntel, {name_text}!</h1>
                        
                        <p>Thank you for registering. To complete your account setup and verify your email address, please click the button below:</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{verification_link}" style="
                                background-color: #667eea;
                                color: white;
                                padding: 12px 30px;
                                text-decoration: none;
                                border-radius: 5px;
                                font-weight: bold;
                                display: inline-block;
                            ">Verify Email Address</a>
                        </div>
                        
                        <p>Or copy and paste this link in your browser:</p>
                        <p style="word-break: break-all; background-color: #f5f5f5; padding: 10px; border-radius: 5px;">
                            {verification_link}
                        </p>
                        
                        <p style="color: #999; font-size: 12px; margin-top: 30px;">
                            This link will expire in 24 hours. If you did not create this account, please ignore this email.
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                        <p style="color: #999; font-size: 12px;">
                            KraftdIntel Team<br>
                            © 2026 KraftdIntel. All rights reserved.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            # If an underlying implementation exists (ACS), delegate
            if self._impl:
                return await self._impl.send_verification_email(to_email, verification_token, user_name)

            # If no API key, just log (development mode)
            if not self.client:
                logger.info(f"[MOCK EMAIL] Verification email to {to_email}")
                logger.info(f"[MOCK EMAIL] Token: {verification_token}")
                logger.info(f"[MOCK EMAIL] Link: {verification_link}")
                return True
            
            # Send via SendGrid
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Verification email sent to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            return False
    
    async def send_resend_verification_email(
        self,
        to_email: str,
        verification_token: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Resend verification email (same as send_verification_email)
        
        Args:
            to_email: Recipient email address
            verification_token: Token for verifying email
            user_name: Optional user name for personalization
            
        Returns:
            True if email sent successfully, False otherwise
        """
        return await self.send_verification_email(to_email, verification_token, user_name)    
    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send password reset email to user
        
        Args:
            to_email: Recipient email address
            reset_token: Token for resetting password
            user_name: Optional user name for personalization
            
        Returns:
            True if email sent successfully, False otherwise
        """
        # Delegate to ACS impl if present
        if self._impl:
            return await self._impl.send_password_reset_email(to_email, reset_token, user_name)

        try:
            # Build reset link
            reset_url = os.getenv("RESET_PASSWORD_URL", "http://localhost:3000/reset-password")
            reset_link = f"{reset_url}?token={reset_token}"
            
            # Use name in greeting if available
            name_text = user_name or to_email.split('@')[0]
            
            # Create email content
            subject = "Reset Your Password - KraftdIntel"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h1 style="color: #667eea;">Password Reset Request</h1>
                        
                        <p>Hi {name_text},</p>
                        
                        <p>We received a request to reset your password. If you didn't make this request, you can ignore this email.</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_link}" style="
                                background-color: #667eea;
                                color: white;
                                padding: 12px 30px;
                                text-decoration: none;
                                border-radius: 4px;
                                display: inline-block;
                                font-weight: bold;
                            ">Reset Your Password</a>
                        </div>
                        
                        <p>Or copy and paste this link in your browser:</p>
                        <p style="word-break: break-all; color: #666;">{reset_link}</p>
                        
                        <p style="color: #999; font-size: 12px;">This link will expire in 24 hours.</p>
                        
                        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                        <p style="color: #999; font-size: 12px;">
                            © 2026 KraftdIntel. All rights reserved.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            # Mock mode - log to console
            if not self.client:
                logger.info(f"[MOCK EMAIL] Password Reset Email to {to_email}")
                logger.info(f"[MOCK EMAIL] Token: {reset_token}")
                logger.info(f"[MOCK EMAIL] Reset Link: {reset_link}")
                return True
            
            # Real mode - send via SendGrid
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Password reset email sent to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            return False