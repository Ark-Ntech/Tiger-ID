# Email Service Configuration Guide

This document explains how to configure SMTP email service for the Tiger ID application.

## Purpose

Email service is used for:
- Password reset emails
- Investigation notifications
- Verification task alerts
- System alerts

## SMTP Configuration

### Gmail (Recommended for Development)

**Configuration:**
```env
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME=Tiger ID
```

**Getting Gmail App Password:**
1. Enable 2-Step Verification on your Google Account
2. Go to: https://myaccount.google.com/apppasswords
3. Generate app password for "Mail"
4. Use the 16-character password (not your regular password)

### Outlook/Office 365

**Configuration:**
```env
EMAIL_ENABLED=true
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your_email@outlook.com
SMTP_PASSWORD=your_password
SMTP_FROM_EMAIL=your_email@outlook.com
SMTP_FROM_NAME=Tiger ID
```

### Custom SMTP Server

**Configuration:**
```env
EMAIL_ENABLED=true
SMTP_HOST=smtp.yourdomain.com
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=Tiger ID
```

**Common SMTP Ports:**
- **587** - TLS/STARTTLS (recommended)
- **465** - SSL/TLS
- **25** - Plain (often blocked by ISPs)

## Testing Email Configuration

### Method 1: Health Check
Check the `/health` endpoint to verify email service status:
```bash
curl http://localhost:8000/health
```

### Method 2: Password Reset
1. Go to login page
2. Click "Forgot Password"
3. Enter your email
4. Check inbox for reset email

### Method 3: Test Endpoint (if available)
```bash
curl -X POST http://localhost:8000/api/v1/test-email \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to": "test@example.com", "subject": "Test", "body": "Test email"}'
```

## Email Templates

Email templates are stored in:
- `backend/templates/emails/` (if implemented)

Common templates:
- `password_reset.html` - Password reset email
- `investigation_notification.html` - Investigation updates
- `verification_alert.html` - Verification task alerts

## Production Recommendations

### Use Transactional Email Services

For production, consider using:
- **SendGrid** - https://sendgrid.com
- **Mailgun** - https://www.mailgun.com
- **Amazon SES** - https://aws.amazon.com/ses/
- **Postmark** - https://postmarkapp.com

**SendGrid Example:**
```env
EMAIL_ENABLED=true
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_sendgrid_api_key
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=Tiger ID
```

### SPF/DKIM/DMARC Setup

For better deliverability:
1. Set up SPF record in DNS
2. Configure DKIM signing
3. Set up DMARC policy

## Troubleshooting

### "Connection refused" error
- Check SMTP host and port
- Verify firewall allows outbound connections
- Test with telnet: `telnet smtp.gmail.com 587`

### "Authentication failed" error
- Verify username and password
- For Gmail, use App Password (not regular password)
- Check if 2FA is enabled (required for Gmail App Passwords)

### "Email not received"
- Check spam folder
- Verify FROM email address
- Check SMTP logs for errors
- Verify recipient email is valid

### "Timeout" error
- Check network connectivity
- Verify SMTP port is correct
- Try alternative port (465 for SSL)

## Security Notes

- **Never commit SMTP passwords to version control**
- Use environment variables (`.env` file)
- Use App Passwords for Gmail (not regular passwords)
- Rotate passwords regularly
- Use separate email accounts for dev/staging/prod

## Disabling Email Service

If email is not needed:
```env
EMAIL_ENABLED=false
```

The application will continue to work, but email notifications will be disabled.

