"""Tests for email utilities"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

from backend.utils.email import EmailService, get_email_service


class TestEmailService:
    """Tests for EmailService"""
    
    @patch('backend.utils.email.get_settings')
    @patch('backend.utils.email.logger')
    def test_init_disabled(self, mock_logger, mock_get_settings):
        """Test EmailService initialization with email disabled"""
        from unittest.mock import Mock
        
        # Create mock settings with email disabled
        mock_settings = Mock()
        mock_settings.smtp = Mock()
        mock_settings.smtp.enabled = False
        mock_settings.smtp.host = "smtp.test.com"
        mock_settings.smtp.port = 587
        mock_settings.smtp.username = None
        mock_settings.smtp.password = None
        mock_settings.smtp.from_email = "test@example.com"
        mock_get_settings.return_value = mock_settings
        
        service = EmailService()
        
        assert service.enabled is False
    
    @patch('backend.utils.email.get_settings')
    def test_init_enabled(self, mock_get_settings):
        """Test EmailService initialization with email enabled"""
        from unittest.mock import Mock
        
        # Create mock settings with email enabled
        mock_settings = Mock()
        mock_settings.smtp = Mock()
        mock_settings.smtp.enabled = True
        mock_settings.smtp.host = "smtp.test.com"
        mock_settings.smtp.port = 587
        mock_settings.smtp.username = "user"
        mock_settings.smtp.password = "pass"
        mock_settings.smtp.from_email = "test@example.com"
        mock_get_settings.return_value = mock_settings
        
        service = EmailService()
        
        assert service.enabled is True
        assert service.smtp_host == "smtp.test.com"
        assert service.smtp_port == 587
    
    @patch('backend.utils.email.get_settings')
    @patch('backend.utils.email.logger')
    def test_send_email_disabled(self, mock_logger, mock_get_settings):
        """Test send_email when email is disabled"""
        from unittest.mock import Mock
        
        # Mock settings with email disabled
        mock_settings = Mock()
        mock_settings.smtp = Mock()
        mock_settings.smtp.enabled = False
        mock_settings.smtp.host = "smtp.test.com"
        mock_settings.smtp.port = 587
        mock_settings.smtp.username = None
        mock_settings.smtp.password = None
        mock_settings.smtp.from_email = "test@example.com"
        mock_get_settings.return_value = mock_settings
        
        service = EmailService()
        
        result = service.send_email(
            "test@example.com",
            "Test Subject",
            "Test Body"
        )
        
        assert result is True  # Returns True in dev mode
        mock_logger.info.assert_called()
    
    @patch('backend.utils.email.get_settings')
    @patch('backend.utils.email.smtplib.SMTP')
    @patch('backend.utils.email.logger')
    def test_send_email_success(self, mock_logger, mock_smtp, mock_get_settings):
        """Test successful email sending"""
        from unittest.mock import Mock
        
        # Mock settings with email enabled
        mock_settings = Mock()
        mock_settings.smtp = Mock()
        mock_settings.smtp.enabled = True
        mock_settings.smtp.host = "smtp.test.com"
        mock_settings.smtp.port = 587
        mock_settings.smtp.username = "user"
        mock_settings.smtp.password = "pass"
        mock_settings.smtp.from_email = "test@example.com"
        mock_settings.smtp.use_tls = True
        mock_get_settings.return_value = mock_settings
        
        service = EmailService()
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = service.send_email(
            "test@example.com",
            "Test Subject",
            "Test Body"
        )
        
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user", "pass")
        mock_server.send_message.assert_called_once()
    
    @patch('backend.utils.email.get_settings')
    @patch('backend.utils.email.smtplib.SMTP')
    @patch('backend.utils.email.logger')
    def test_send_email_with_html(self, mock_logger, mock_smtp, mock_get_settings):
        """Test email sending with HTML body"""
        from unittest.mock import Mock
        
        # Mock settings with email enabled
        mock_settings = Mock()
        mock_settings.smtp = Mock()
        mock_settings.smtp.enabled = True
        mock_settings.smtp.host = "smtp.test.com"
        mock_settings.smtp.port = 587
        mock_settings.smtp.username = "user"
        mock_settings.smtp.password = "pass"
        mock_settings.smtp.from_email = "test@example.com"
        mock_settings.smtp.use_tls = True
        mock_get_settings.return_value = mock_settings
        
        service = EmailService()
        
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = service.send_email(
            "test@example.com",
            "Test Subject",
            "Plain Body",
            html_body="<html><body>HTML Body</body></html>"
        )
        
        assert result is True
        mock_server.send_message.assert_called_once()
    
    @patch('backend.utils.email.get_settings')
    @patch('backend.utils.email.smtplib.SMTP')
    @patch('backend.utils.email.logger')
    def test_send_email_failure(self, mock_logger, mock_smtp, mock_get_settings):
        """Test email sending failure"""
        from unittest.mock import Mock
        
        # Mock settings with email enabled
        mock_settings = Mock()
        mock_settings.smtp = Mock()
        mock_settings.smtp.enabled = True
        mock_settings.smtp.host = "smtp.test.com"
        mock_settings.smtp.port = 587
        mock_settings.smtp.username = "user"
        mock_settings.smtp.password = "pass"
        mock_settings.smtp.from_email = "test@example.com"
        mock_settings.smtp.use_tls = True
        mock_get_settings.return_value = mock_settings
        
        service = EmailService()
        
        # Mock SMTP to raise exception
        mock_smtp.side_effect = Exception("SMTP Error")
        
        result = service.send_email(
            "test@example.com",
            "Test Subject",
            "Test Body"
        )
        
        assert result is False
        mock_logger.error.assert_called_once()
    
    @patch('backend.utils.email.get_settings')
    @patch('backend.utils.email.smtplib.SMTP')
    @patch('backend.utils.email.logger')
    def test_send_password_reset_email(self, mock_logger, mock_smtp, mock_get_settings):
        """Test password reset email sending"""
        from unittest.mock import Mock
        
        # Mock settings with email enabled
        mock_settings = Mock()
        mock_settings.smtp = Mock()
        mock_settings.smtp.enabled = True
        mock_settings.smtp.host = "smtp.test.com"
        mock_settings.smtp.port = 587
        mock_settings.smtp.username = "user"
        mock_settings.smtp.password = "pass"
        mock_settings.smtp.from_email = "test@example.com"
        mock_settings.smtp.use_tls = True
        mock_get_settings.return_value = mock_settings
        
        service = EmailService()
        
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = service.send_password_reset_email(
            "test@example.com",
            "reset_token_123",
            "https://example.com/reset?token=reset_token_123"
        )
        
        assert result is True
        # Verify email was sent
        mock_server.send_message.assert_called_once()
        # Check that reset URL is in the message
        sent_message = mock_server.send_message.call_args[0][0]
        assert "reset_token_123" in str(sent_message)


class TestGetEmailService:
    """Tests for get_email_service function"""
    
    def test_get_email_service_singleton(self):
        """Test get_email_service returns singleton"""
        # Clear any existing instance
        import backend.utils.email as email_module
        email_module._email_service = None
        
        service1 = get_email_service()
        service2 = get_email_service()
        
        assert service1 is service2
    
    @patch('backend.utils.email.EmailService')
    def test_get_email_service_creates_once(self, mock_email_service_class):
        """Test get_email_service creates service only once"""
        import backend.utils.email as email_module
        email_module._email_service = None
        
        mock_instance = MagicMock()
        mock_email_service_class.return_value = mock_instance
        
        service1 = get_email_service()
        service2 = get_email_service()
        
        assert service1 is service2
        # EmailService should only be instantiated once
        assert mock_email_service_class.call_count == 1

