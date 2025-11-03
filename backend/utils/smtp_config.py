"""SMTP email configuration"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from jinja2 import Template

from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)


class SMTPConfig:
    """SMTP email configuration and client"""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ):
        """
        Initialize SMTP configuration
        
        Args:
            host: SMTP host (defaults to settings)
            port: SMTP port (defaults to settings)
            username: SMTP username (defaults to settings)
            password: SMTP password (defaults to settings)
            use_tls: Use TLS encryption
            from_email: From email address (defaults to settings)
            from_name: From name (defaults to settings)
        """
        settings = get_settings()
        self.host = host or settings.smtp.host
        self.port = port or settings.smtp.port
        self.username = username or settings.smtp.username
        self.password = password or settings.smtp.password
        self.use_tls = use_tls if use_tls is not None else settings.smtp.use_tls
        self.from_email = from_email or settings.smtp.from_email or self.username
        self.from_name = from_name or settings.smtp.from_name
        
        self._smtp_client = None
    
    def _get_smtp_client(self):
        """Get or create SMTP client"""
        if self._smtp_client is None:
            self._smtp_client = smtplib.SMTP(self.host, self.port)
            if self.use_tls:
                self._smtp_client.starttls()
            if self.username and self.password:
                self._smtp_client.login(self.username, self.password)
        return self._smtp_client
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: Optional[str] = None,
        text_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (required if html_body not provided)
            cc: CC recipients
            bcc: BCC recipients
        
        Returns:
            True if sent successfully
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            
            if cc:
                msg["Cc"] = ", ".join(cc)
            
            # Add body
            if html_body:
                html_part = MIMEText(html_body, "html")
                msg.attach(html_part)
            
            if text_body:
                text_part = MIMEText(text_body, "plain")
                msg.attach(text_part)
            elif not html_body:
                raise ValueError("Either html_body or text_body must be provided")
            
            # Send email
            smtp = self._get_smtp_client()
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            smtp.sendmail(self.from_email, recipients, msg.as_string())
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
            return False
    
    def send_password_reset_email(
        self,
        to_email: str,
        username: str,
        reset_token: str,
        reset_url: str
    ) -> bool:
        """
        Send password reset email
        
        Args:
            to_email: Recipient email
            username: Username
            reset_token: Password reset token
            reset_url: Password reset URL
        
        Returns:
            True if sent successfully
        """
        subject = "Password Reset Request - Tiger ID"
        
        html_body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hello {username},</p>
            <p>You have requested to reset your password for Tiger ID.</p>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you did not request this password reset, please ignore this email.</p>
            <p>Best regards,<br>Tiger ID</p>
        </body>
        </html>
        """
        
        text_body = f"""
        Password Reset Request
        
        Hello {username},
        
        You have requested to reset your password for Tiger ID.
        
        Click the link below to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you did not request this password reset, please ignore this email.
        
        Best regards,
        Tiger ID
        """
        
        return self.send_email(to_email, subject, html_body=html_body, text_body=text_body)
    
    def close(self):
        """Close SMTP connection"""
        if self._smtp_client:
            try:
                self._smtp_client.quit()
            except:
                pass
            finally:
                self._smtp_client = None


# Global SMTP config instance
_smtp_config: Optional[SMTPConfig] = None


def get_smtp_config() -> SMTPConfig:
    """Get SMTP config instance (singleton)"""
    global _smtp_config
    
    if _smtp_config is None:
        _smtp_config = SMTPConfig()
    
    return _smtp_config

