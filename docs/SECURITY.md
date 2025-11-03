# Security Policy

## Supported Versions

We actively support the latest version of Tiger ID. Security updates are applied to:

- **Current version**: Latest release
- **Previous major version**: For critical security fixes only

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via:
- **Email**: security@your-domain.com (replace with your contact)
- **Private disclosure**: Contact repository maintainers directly

### What to Include

When reporting a security vulnerability, please include:

1. **Description**: Clear description of the vulnerability
2. **Impact**: Potential impact and severity
3. **Steps to Reproduce**: Detailed steps to reproduce
4. **Proof of Concept**: If possible, a minimal PoC (do not exploit on production systems)
5. **Suggested Fix**: If you have ideas for fixing it

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity, typically:
  - **Critical**: 24-48 hours
  - **High**: 3-7 days
  - **Medium**: 1-2 weeks
  - **Low**: Next release cycle

### Recognition

Security researchers who responsibly disclose vulnerabilities will be:
- Credited in security advisories (if desired)
- Added to the Security Hall of Fame (if desired)
- Thanked in release notes

## Security Features

### Authentication & Authorization

- **JWT Authentication**: Token-based authentication with expiration
- **Password Hashing**: bcrypt with appropriate cost factor
- **Role-Based Access Control (RBAC)**: User roles (investigator, analyst, supervisor, admin)
- **Session Management**: Secure session handling with expiration
- **Password Reset**: Secure token-based password reset flow

### API Security

- **Rate Limiting**: 60 requests per minute per IP address
- **CSRF Protection**: Optional CSRF token validation (enabled via `ENABLE_CSRF` env var)
- **Input Validation**: Pydantic models for all inputs
- **Input Sanitization**: String sanitization for user inputs
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **XSS Prevention**: Input sanitization and output encoding

### Data Security

- **Encryption at Rest**: Database encryption (configure at database level)
- **Encryption in Transit**: HTTPS/TLS for all network communication
- **Sensitive Data Protection**: Passwords never stored in plain text
- **Audit Logging**: Comprehensive audit trail for all system actions
- **Data Backups**: Regular encrypted backups

### Infrastructure Security

- **Secure Headers**: Security headers configured in FastAPI middleware
- **CORS Configuration**: Configurable CORS settings
- **Environment Variables**: Sensitive configuration via environment variables
- **Secrets Management**: Recommendations for production secrets management
- **Docker Security**: Secure container configurations

## Security Best Practices

### For Administrators

1. **Change Default Credentials**: Immediately change any default passwords
2. **Enable HTTPS**: Always use HTTPS in production
3. **Keep Dependencies Updated**: Regularly update dependencies for security patches
4. **Enable CSRF Protection**: Set `ENABLE_CSRF=true` in production
5. **Configure Secrets**: Use secure secret management (e.g., HashiCorp Vault)
6. **Enable Audit Logging**: Review audit logs regularly
7. **Regular Backups**: Maintain encrypted backups
8. **Monitor Logs**: Set up log monitoring and alerting
9. **Restrict Database Access**: Limit database access to application containers
10. **Enable Error Tracking**: Configure Sentry or similar for error monitoring

### For Developers

1. **Never Commit Secrets**: Never commit API keys, passwords, or tokens
2. **Use Environment Variables**: Store sensitive configuration in environment variables
3. **Input Validation**: Always validate and sanitize user inputs
4. **Parameterized Queries**: Always use ORM or parameterized queries
5. **Error Handling**: Never expose sensitive information in error messages
6. **Dependency Updates**: Regularly update dependencies
7. **Security Headers**: Ensure security headers are configured
8. **Rate Limiting**: Respect rate limits in API design
9. **Audit Logging**: Log security-relevant actions
10. **Security Testing**: Include security tests in test suite

## Known Security Considerations

### Current Limitations

1. **CSRF Protection**: Optional, must be explicitly enabled via environment variable
2. **Rate Limiting**: Basic IP-based rate limiting (consider user-based in future)
3. **Session Storage**: Currently in-memory/Redis (consider secure session storage in future)

### Planned Security Enhancements

1. **Multi-Factor Authentication (MFA)**: Planned for future release
2. **API Key Management**: Enhanced API key management system
3. **Advanced Rate Limiting**: User-based and more sophisticated rate limiting
4. **Security Audit Dashboard**: Admin dashboard for security monitoring
5. **Penetration Testing**: Regular security audits

## Dependency Security

### Regular Updates

We regularly update dependencies for security patches. Check `requirements.txt` for versions.

### Security Scanning

Consider using security scanning tools:
- `safety check` - Check Python dependencies for known vulnerabilities
- `pip-audit` - Audit dependencies for known vulnerabilities
- `bandit` - Security linter for Python code

```bash
# Install security scanning tools
pip install safety pip-audit bandit

# Scan dependencies
safety check
pip-audit

# Scan code
bandit -r backend/ app/
```

## Security Configuration

### Environment Variables

**Required Security Variables:**
```bash
# Secret keys (generate strong random keys)
SECRET_KEY=<strong-random-key>
JWT_SECRET_KEY=<strong-random-key>

# Database (use strong credentials)
DATABASE_URL=postgresql://user:password@host:5432/db

# CSRF (enable in production)
ENABLE_CSRF=true
CSRF_SECRET_KEY=<strong-random-key>

# Sentry (error tracking)
SENTRY_DSN=<your-sentry-dsn>
```

**Security-Related Optional Variables:**
```bash
# Rate limiting
RATE_LIMIT_PER_MINUTE=60

# JWT settings
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS (restrict in production)
CORS_ORIGINS=https://your-domain.com
```

### Production Checklist

- [ ] Changed all default passwords
- [ ] Generated strong secret keys
- [ ] Enabled HTTPS/TLS
- [ ] Configured CORS appropriately
- [ ] Enabled CSRF protection
- [ ] Set up error tracking (Sentry)
- [ ] Configured audit logging
- [ ] Set up database encryption
- [ ] Configured secure session storage
- [ ] Set up regular backups
- [ ] Enabled rate limiting
- [ ] Restricted database access
- [ ] Set up log monitoring
- [ ] Updated all dependencies
- [ ] Ran security scans
- [ ] Reviewed audit logs regularly

## Security Disclosure

### Security Advisories

Security advisories will be published:
- On GitHub Security Advisories
- In release notes
- Via email notifications (if subscribed)

### CVE Assignments

For critical vulnerabilities, we will:
- Request CVE assignments when appropriate
- Follow responsible disclosure timelines
- Provide patches in a timely manner

## Contact

For security-related questions or concerns:
- **Email**: security@your-domain.com
- **GitHub**: Open a private security advisory

## License

This security policy is part of the project documentation and is subject to the same license (Apache License 2.0).

