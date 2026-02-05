# Deployment Guide

This document provides instructions for deploying the Tiger Trafficking Investigation System.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local development)
- sqlite-vec extension (`pip install sqlite-vec`)
- Minimum 8GB RAM (16GB recommended for ML models)
- GPU recommended for faster model inference (via Modal)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd "Tiger ID"
cp .env.example .env
# Edit .env with your configuration
```

### 2. Configure Environment

Edit `.env` file with your settings:

```bash
# Database (SQLite - no external server needed)
DATABASE_URL=sqlite:///data/tiger_id.db

# API Keys (required for external integrations)
ANTHROPIC_API_KEY=your-key
FIRECRAWL_API_KEY=your-key
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Or start specific services
docker-compose up -d api frontend
```

### 4. Initialize Database

The database is automatically initialized on first startup. To manually initialize:

```bash
docker-compose exec api python -c "from backend.database import init_db; init_db()"
```

### 5. Access Applications

- **Frontend**: http://localhost:5173 (dev) or http://localhost:80 (production)
- **FastAPI API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Production Deployment

### 1. Environment Configuration

For production, update `.env` with:

- Strong SECRET_KEY and JWT_SECRET_KEY
- Production database credentials
- Valid API keys for external services
- Set `APP_ENV=production`
- Set `DEBUG=False`

### 2. Database Setup

SQLite database is automatically initialized. Ensure the data directory has proper permissions:

```bash
# Create data directory with proper permissions
mkdir -p /var/lib/tiger-id/data
chmod 755 /var/lib/tiger-id/data

# Set DATABASE_URL in production
export DATABASE_URL=sqlite:////var/lib/tiger-id/data/tiger_id.db
```

### 3. Storage Configuration

For production, configure persistent storage:

- **Local Storage**: Set `STORAGE_PATH=/var/lib/tiger-investigation/storage`
- **S3 Storage**: Configure S3 bucket and credentials

### 4. Model Deployment

Download and configure ML models:

```bash
# Download ATRW dataset
python scripts/download_models.py --dataset atrw

# Download MegaDetector
python scripts/download_models.py --model megadetector

# Download Tiger Re-ID model
python scripts/download_models.py --model tiger_reid
```

### 5. Reverse Proxy (Nginx)

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 6. SSL/TLS Configuration

Use Let's Encrypt for SSL certificates:

```bash
certbot --nginx -d your-domain.com
```

## Monitoring and Logging

### Health Checks

- **API Health**: `GET http://localhost:8000/health`
- **Database**: Included in API health check response

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f frontend
```

### Metrics

The system logs metrics to:
- `SystemMetric` table in database
- Application logs (JSON format)

## Backup and Recovery

### Database Backup

```bash
# Create backup (simple file copy)
cp data/tiger_id.db "backups/tiger_id_$(date +%Y%m%d_%H%M%S).db"

# Include WAL files if present
cp data/tiger_id.db-wal "backups/" 2>/dev/null || true
cp data/tiger_id.db-shm "backups/" 2>/dev/null || true

# Restore backup
cp backups/tiger_id_backup.db data/tiger_id.db
```

### Model Backup

Backup model directory:
```bash
tar -czf models_backup.tar.gz data/models/
```

## Scaling

### Horizontal Scaling

- **API**: Single instance recommended with SQLite (use vertical scaling instead)
- **Modal**: ML inference scales automatically on Modal serverless GPUs

### Vertical Scaling

- Increase container memory allocation
- SQLite handles concurrent reads well with WAL mode
- Single-writer constraint makes horizontal API scaling complex

## Troubleshooting

### Database Issues

```bash
# Check database file exists
ls -la data/tiger_id.db

# Test database integrity
sqlite3 data/tiger_id.db "PRAGMA integrity_check;"

# Re-initialize if corrupted
rm data/tiger_id.db*
python -c "from backend.database import init_db; init_db()"
```

### Model Loading Issues

```bash
# Check model files exist
ls -lh data/models/

# Test model loading
python -c "from backend.models.tiger_detection import TigerDetectionModel; import asyncio; asyncio.run(TigerDetectionModel().load_model())"
```

## Discovery Pipeline Deployment

### Playwright Browser Automation

For the continuous tiger discovery pipeline, Playwright must be installed:

```bash
# Install Playwright Python package
pip install playwright>=1.40.0

# Install browser binaries
playwright install chromium

# Or via Docker (add to Dockerfile):
RUN pip install playwright && playwright install chromium --with-deps
```

**Resource Requirements:**
- Additional ~500MB disk for Chromium browser binaries
- Additional ~200-500MB RAM per concurrent browser instance
- Consider running discovery workers on dedicated containers

### Rate Limiting Persistence

The rate limiter tracks per-domain backoff states in memory. For production:

1. **Single-worker deployment**: Backoff state persists in the worker process
2. **Multi-worker deployment**: Consider Redis-backed rate limiting for shared state
3. **Restart behavior**: Backoff state resets on restart (domains get fresh limits)

### Docker Compose Example

```yaml
services:
  discovery_worker:
    build: .
    environment:
      - PLAYWRIGHT_ENABLED=true
      - PLAYWRIGHT_HEADLESS=true
      - RATE_LIMIT_BASE_INTERVAL=2.0
      - RATE_LIMIT_MAX_BACKOFF=60.0
      - IMAGE_DEDUPLICATION_ENABLED=true
    volumes:
      - discovery_data:/app/data/storage/discovered
    deploy:
      resources:
        limits:
          memory: 2G

volumes:
  discovery_data:
```

### Database Schema for Image Deduplication

The discovery system includes image deduplication columns:
- `content_hash` column (VARCHAR(64)) for SHA256 hashes
- `is_duplicate_of` column (UUID FK) for duplicate tracking
- Index on `content_hash` for fast duplicate lookups

Schema is automatically created on startup via `init_db()`.

## Security Considerations

1. **Change default passwords** in production
2. **Enable HTTPS** with valid certificates
3. **Restrict database access** to application containers only
4. **Use secrets management** (e.g., Docker secrets, HashiCorp Vault)
5. **Enable authentication** for API endpoints
6. **Implement rate limiting** for API endpoints (built-in for discovery)
7. **Regular security updates** for dependencies
8. **Respect robots.txt** when using discovery pipeline

## Maintenance

### Updates

```bash
# Pull latest code
git pull

# Rebuild containers
docker-compose build

# Restart services
docker-compose restart
```

### Database Updates

SQLite schema is managed automatically via SQLAlchemy:

```bash
# Re-initialize schema (preserves data if tables exist)
python -c "from backend.database import init_db; init_db()"
```

## Security Checklist

Before deploying to production, ensure:

1. **Change default passwords** - Update all database and admin passwords
2. **Enable HTTPS** - Configure valid SSL/TLS certificates
3. **Restrict database access** - Only allow application containers to connect
4. **Use secrets management** - Docker secrets, HashiCorp Vault, or similar
5. **Enable authentication** - Require auth for all API endpoints
6. **Implement rate limiting** - Built-in for discovery; configure for API

## Support

For issues or questions:
- Check logs: `docker-compose logs`
- Review documentation in `docs/`
- Open an issue on GitHub

## Additional Resources

- [Architecture Documentation](docs/ARCHITECTURE.md) - System architecture details
- [API Documentation](docs/API.md) - Complete API reference
- [Modal GPU Infrastructure](docs/MODAL.md) - GPU deployment guide
- [Discovery Pipeline](docs/DISCOVERY_PIPELINE.md) - Continuous tiger discovery
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Common issues and solutions

