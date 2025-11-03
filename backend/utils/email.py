"""Email utility for sending emails (password reset, notifications, etc.)"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)


class EmailService:
    """Email service for sending emails"""
    
    def __init__(self):
        """Initialize email service"""
        settings = get_settings()
        self.smtp_host = settings.smtp.host
        self.smtp_port = settings.smtp.port
        self.smtp_user = settings.smtp.username or ""
        self.smtp_password = settings.smtp.password or ""
        self.from_email = settings.smtp.from_email or "noreply@tiger-investigation.com"
        self.enabled = settings.smtp.enabled
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info("Email disabled, skipping send", to_email=to_email, subject=subject)
            # In development, log email content instead of sending
            logger.debug(f"Email would be sent to {to_email}:\nSubject: {subject}\nBody: {body}")
            return True  # Return True for development
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add plain text and HTML versions
            part1 = MIMEText(body, 'plain')
            msg.attach(part1)
            
            if html_body:
                part2 = MIMEText(html_body, 'html')
                msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info("Email sent successfully", to_email=to_email, subject=subject)
            return True
            
        except Exception as e:
            logger.error("Failed to send email", error=str(e), to_email=to_email)
            return False
    
    def send_password_reset_email(self, to_email: str, reset_token: str, reset_url: str) -> bool:
        """
        Send password reset email
        
        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            reset_url: Password reset URL
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "Password Reset Request - Tiger ID"
        body = f"""
Hello,

You have requested to reset your password for Tiger ID.

To reset your password, please click on the following link:
{reset_url}

If you did not request this password reset, please ignore this email.

This link will expire in 1 hour.

Best regards,
Tiger ID Team
"""
        html_body = f"""
<html>
<head></head>
<body>
    <h2>Password Reset Request</h2>
    <p>Hello,</p>
    <p>You have requested to reset your password for Tiger ID.</p>
    <p>To reset your password, please click on the following link:</p>
    <p><a href="{reset_url}">{reset_url}</a></p>
    <p>If you did not request this password reset, please ignore this email.</p>
    <p>This link will expire in 1 hour.</p>
    <br>
    <p>Best regards,<br>Tiger ID Team</p>
</body>
</html>
"""
        return self.send_email(to_email, subject, body, html_body)


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get email service instance (singleton)"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

