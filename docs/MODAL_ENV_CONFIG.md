# Modal Environment Configuration

## Quick Setup

Create a `.env` file in your project root with these settings:

```env
# ============================================
# MODAL CONFIGURATION (Required)
# ============================================
MODAL_ENABLED=true
MODAL_MAX_RETRIES=3
MODAL_RETRY_DELAY=1.0
MODAL_TIMEOUT=120
MODAL_QUEUE_MAX_SIZE=100
MODAL_FALLBACK_TO_QUEUE=true

# ============================================
# APPLICATION BASICS
# ============================================
APP_ENV=development
DEBUG=false
SECRET_KEY=your-secret-key-here-change-this
JWT_SECRET_KEY=your-jwt-secret-here-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# ============================================
# DATABASE CONFIGURATION
# ============================================
# SQLite (default - recommended for development)
SQLITE_DB_PATH=data/production.db
USE_SQLITE_DEMO=false
USE_POSTGRESQL=false

# PostgreSQL (optional - for production)
# DATABASE_URL=postgresql://user:password@localhost:5432/tiger_id
# USE_POSTGRESQL=true

# ============================================
# REDIS & CELERY (Optional)
# ============================================
# REDIS_URL=redis://localhost:6379/0
# CELERY_BROKER_URL=redis://localhost:6379/0
# CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ============================================
# MODEL SETTINGS
# ============================================
MODEL_DEVICE=cuda
MODEL_PRELOAD_ON_STARTUP=false
BATCH_SIZE=32
MODEL_CACHE_TTL=3600

# ============================================
# LOGGING & MONITORING
# ============================================
LOG_LEVEL=INFO
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# ============================================
# STORAGE
# ============================================
STORAGE_TYPE=local
STORAGE_PATH=./data/storage

# S3 Storage (optional)
# STORAGE_TYPE=s3
# S3_BUCKET=your-bucket-name
# S3_REGION=us-east-1

# ============================================
# EXTERNAL APIs (All Optional)
# ============================================
# YouTube API (for social media intelligence)
# YOUTUBE_API_KEY=your-youtube-api-key

# Meta/Facebook API (for social media intelligence)  
# META_ACCESS_TOKEN=your-meta-token
# META_APP_ID=your-app-id
# META_APP_SECRET=your-app-secret

# Firecrawl (for web crawling)
# FIRECRAWL_API_KEY=your-firecrawl-key

# USDA, CITES, USFWS APIs (for compliance checking)
# USDA_API_KEY=your-usda-key
# CITES_API_KEY=your-cites-key
# USFWS_API_KEY=your-usfws-key
```

## Minimal Configuration

If you just want to test Modal integration, here's the absolute minimum:

```env
MODAL_ENABLED=true
SECRET_KEY=test-secret-key-change-in-production
JWT_SECRET_KEY=test-jwt-secret-change-in-production
```

## Configuration Notes

### Modal Settings Explained

- `MODAL_ENABLED`: Set to `true` to use Modal for model inference
- `MODAL_MAX_RETRIES`: Number of retry attempts for failed Modal requests (default: 3)
- `MODAL_RETRY_DELAY`: Initial delay between retries in seconds (default: 1.0)
- `MODAL_TIMEOUT`: Timeout for Modal requests in seconds (default: 120)
- `MODAL_QUEUE_MAX_SIZE`: Max number of requests to queue when Modal is unavailable (default: 100)
- `MODAL_FALLBACK_TO_QUEUE`: Whether to queue requests when Modal is down (default: true)

### Security Notes

⚠️ **IMPORTANT**: Change the default secret keys before deploying to production!

Generate secure keys using:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### External APIs

All external APIs are optional. The Tiger ID system works without them:

- **YouTube/Meta**: For social media monitoring (optional)
- **Firecrawl**: For web crawling (optional)
- **USDA/CITES/USFWS**: For regulatory compliance checks (optional)

You can add API keys later as needed.

## Next Steps

1. **Create your .env file**: Copy the configuration above and save as `.env` in project root
2. **Update secret keys**: Generate and replace the default keys
3. **Test the configuration**: Run `python -m pytest tests/test_modal_integration.py -v`

---

**Ready to proceed?** Your `.env` file should now be configured for Modal!

