# Deployment Guide

This document provides instructions for deploying the Tiger Trafficking Investigation System.

## Prerequisites

- Docker and Docker Compose installed
- PostgreSQL 16+ with pgvector extension
- Redis 7.2+
- Python 3.11+ (for local development)
- Minimum 16GB RAM (for ML models)
- GPU recommended for faster model inference

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
# Database
DATABASE_URL=postgresql://tiger_user:tiger_password@postgres:5432/tiger_investigation

# Redis
REDIS_URL=redis://redis:6379/0

# API Keys (required for external integrations)
OMNIVINCI_API_KEY=your-key
FIRECRAWL_API_KEY=your-key
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Or start specific services
docker-compose up -d postgres redis
docker-compose up -d api frontend
docker-compose up -d celery_worker celery_beat
```

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Or manually
alembic upgrade head
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

```bash
# Create production database
createdb tiger_investigation_prod

# Run migrations
alembic upgrade head

# Initialize pgvector extension
psql -d tiger_investigation_prod -c "CREATE EXTENSION IF NOT EXISTS vector;"
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

- **API Health**: `GET http://localhost:8000/api/health`
- **Database**: Check Docker health status
- **Redis**: `redis-cli ping`

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f celery_worker
```

### Metrics

The system logs metrics to:
- `SystemMetric` table in database
- Application logs (JSON format)

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U tiger_user tiger_investigation > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U tiger_user tiger_investigation < backup.sql
```

### Model Backup

Backup model directory:
```bash
tar -czf models_backup.tar.gz data/models/
```

## Scaling

### Horizontal Scaling

- **API**: Run multiple API instances behind load balancer
- **Celery Workers**: Scale workers: `docker-compose up -d --scale celery_worker=4`

### Vertical Scaling

- Increase database memory: `shared_buffers = 4GB`
- Configure Redis memory limits
- Allocate sufficient RAM for ML models

## Troubleshooting

### Database Connection Issues

```bash
# Check database is running
docker-compose ps postgres

# Check connection
docker-compose exec postgres psql -U tiger_user -d tiger_investigation
```

### Migration Issues

```bash
# Check current revision
alembic current

# Show migration history
alembic history

# Rollback if needed
alembic downgrade -1
```

### Model Loading Issues

```bash
# Check model files exist
ls -lh data/models/

# Test model loading
python -c "from backend.models.tiger_detection import TigerDetectionModel; import asyncio; asyncio.run(TigerDetectionModel().load_model())"
```

## Security Considerations

1. **Change default passwords** in production
2. **Enable HTTPS** with valid certificates
3. **Restrict database access** to application containers only
4. **Use secrets management** (e.g., Docker secrets, HashiCorp Vault)
5. **Enable authentication** for API endpoints
6. **Implement rate limiting** for API endpoints
7. **Regular security updates** for dependencies

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

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Review migration
cat backend/database/migrations/versions/XXX_description.py

# Apply migration
alembic upgrade head
```

## Support

For issues or questions:
- Check logs: `docker-compose logs`
- Review documentation in `docs/`
- Check [Security Policy](docs/SECURITY.md) for security-related issues
- Open an issue on GitHub

## Additional Resources

- [Architecture Documentation](docs/ARCHITECTURE.md) - System architecture details
- [API Documentation](docs/API.md) - Complete API reference
- [Development Guide](docs/DEVELOPMENT.md) - Development setup and workflow
- [Security Guide](docs/SECURITY.md) - Security best practices

