# Configuration Guide

## Overview

All configuration is managed through environment variables, with support for `.env` files for local development. The application uses Pydantic Settings for type-safe configuration management.

## Quick Start

1. **Copy `.env.example` to `.env`:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your configuration values**

3. **For production, use a secrets management system:**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - Kubernetes Secrets

## Configuration Priority

Configuration is loaded in the following order (highest to lowest priority):

1. **Environment Variables** (system environment)
2. **`.env` file** (project root)
3. **`config/settings.yaml`** (optional defaults)
4. **Pydantic model defaults** (fallback)

## Required Variables

### Development & Production

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite database path | `sqlite:///data/tiger_id.db` |
| `SECRET_KEY` | Application secret key | Must be changed in production, min 32 chars |
| `JWT_SECRET_KEY` | JWT signing key | Must be changed in production, min 32 chars |

**Note:** The application validates that secret keys are changed in production. DATABASE_URL must be a SQLite connection string starting with `sqlite:///`.

## Optional Variables

See `.env.example` for a complete list of all available environment variables. Common optional variables include:

### External API Keys
- `ANTHROPIC_API_KEY` - Anthropic Claude API key
- `FIRECRAWL_API_KEY` - Firecrawl API key
- `YOUTUBE_API_KEY` - YouTube Data API v3 key
- `META_ACCESS_TOKEN` - Meta/Facebook Graph API token

### Feature Flags
- `USE_LANGGRAPH` - Enable Langgraph workflow (default: `false`)
- `MFA_ENABLED` - Enable multi-factor authentication (default: `false`)

### Model Configuration
- `MODEL_DEVICE` - Device to run models on (`cuda` or `cpu`, default: `cuda`)
- `BATCH_SIZE` - Batch size for model inference (default: `32`)

### Modal GPU Infrastructure
- `MODAL_ENABLED` - Enable Modal for GPU inference (default: `true`)
- `MODAL_WORKSPACE` - Modal workspace name (default: `ark-ntech`)
- `MODAL_APP_NAME` - Modal app name (default: `tiger-id-models`)
- `MODAL_MAX_RETRIES` - Max retry attempts for failed requests (default: `3`)
- `MODAL_TIMEOUT` - Request timeout in seconds (default: `120`)
- `MODAL_QUEUE_MAX_SIZE` - Max requests to queue when unavailable (default: `100`)
- `MODAL_FALLBACK_TO_QUEUE` - Queue requests on failure (default: `true`)

### Discovery Pipeline
- `RATE_LIMIT_BASE_INTERVAL` - Base seconds between requests per domain (default: `2.0`)
- `RATE_LIMIT_MAX_BACKOFF` - Maximum backoff time in seconds (default: `60.0`)
- `IMAGE_DEDUPLICATION_ENABLED` - Enable SHA256 deduplication (default: `true`)
- `PLAYWRIGHT_ENABLED` - Enable Playwright for JS-heavy sites (default: `true`)
- `PLAYWRIGHT_HEADLESS` - Run Playwright in headless mode (default: `true`)
- `JS_HEAVY_THRESHOLD` - Number of indicators to trigger Playwright (default: `2`)
- `DISCOVERY_MAX_GALLERY_PAGES` - Max gallery pages per facility (default: `5`)

## Security Best Practices

### 1. Never Commit `.env` Files

Ensure `.env` is in `.gitignore`:
```gitignore
.env
.env.local
.env.*.local
```

### 2. Generate Strong Secrets

For production, generate random keys:
```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32
```

### 3. Validate at Startup

The application validates required variables on startup:
- Secret keys must be at least 32 characters long
- Production environment requires non-default secrets
- Database URL must be a valid SQLite connection string
- sqlite-vec extension must be installed

### 4. Use Secrets Management

For production deployments:
- **AWS**: Use AWS Secrets Manager or Systems Manager Parameter Store
- **Kubernetes**: Use Kubernetes Secrets
- **Docker**: Use Docker Secrets
- **HashiCorp Vault**: Use Vault for secrets management

Example with AWS Secrets Manager:
```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])
```

## Configuration Access

### Using Settings in Code

```python
from backend.config.settings import get_settings

settings = get_settings()

# Access nested settings
db_url = settings.database.url
jwt_secret = settings.authentication.jwt_secret_key
api_key = settings.anthropic.api_key

# Access Modal settings
modal_workspace = settings.modal.workspace
modal_app_name = settings.modal.app_name
deployment_url = settings.modal.deployment_url  # Computed property
```

### Environment Variable Names

Environment variables use uppercase with underscores:
- `DATABASE_URL` → `settings.database.url`
- `JWT_SECRET_KEY` → `settings.authentication.jwt_secret_key`
- `ANTHROPIC_API_KEY` → `settings.anthropic.api_key`

## Troubleshooting

### Validation Errors

If you see validation errors on startup:

1. **Secret key too short:**
   ```
   ValueError: SECRET_KEY must be at least 32 characters long
   ```
   **Solution:** Generate a longer secret key (minimum 32 characters)

2. **Production secrets not changed:**
   ```
   ValueError: SECRET_KEY must be changed in production
   ```
   **Solution:** Set `APP_ENV=production` and ensure secrets are changed from defaults

3. **Invalid database URL:**
   ```
   ValueError: DATABASE_URL must be a SQLite connection string
   ```
   **Solution:** Ensure DATABASE_URL starts with `sqlite:///`

4. **sqlite-vec not installed:**
   ```
   ValueError: sqlite-vec extension is required for vector search
   ```
   **Solution:** Install sqlite-vec: `pip install sqlite-vec`

### Environment Variables Not Loading

1. **Check `.env` file location:**
   - Must be in project root directory
   - Ensure file is named `.env` (not `.env.example`)

2. **Check environment variable names:**
   - Must match exactly (case-insensitive but convention is uppercase)
   - Use underscores, not hyphens

3. **Restart application:**
   - Environment variables are loaded at startup
   - Changes require application restart

## Production Deployment

### Docker

Use environment variables in `docker-compose.yml`:
```yaml
services:
  api:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
    secrets:
      - jwt_secret_key
```

### Kubernetes

Use ConfigMaps and Secrets:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key"
  JWT_SECRET_KEY: "your-jwt-secret"
```

### Environment-Specific Files

For different environments:
- `.env.development` - Development settings
- `.env.test` - Test settings
- `.env.production` - Production settings (use secrets management instead)

Load specific file:
```bash
export ENV_FILE=.env.production
```

## Additional Resources

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/usage/settings/)
- [12-Factor App Config](https://12factor.net/config)
- [Environment Variables Best Practices](https://www.twilio.com/blog/environment-variables-python)

