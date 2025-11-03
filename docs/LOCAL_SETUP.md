# Local Development Setup Guide

This guide will help you set up and run the Tiger ID system locally using Docker Compose.

## Prerequisites

- **Docker Desktop** (Windows/Mac) or Docker Engine + Docker Compose (Linux)
- **Git** for cloning the repository
- At least **8GB RAM** available for Docker
- At least **20GB free disk space** for models and data

## Quick Start

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone <repository-url>
   cd tiger-investigation
   ```

2. **Set up environment variables**:
   - Copy `.env.example` to `.env`:
     ```bash
   cp .env.example .env
   ```
   - The `.env` file is already configured with development-safe defaults
   - Edit `.env` if you need to customize settings (API keys, etc.)

3. **Start all services**:
   ```bash
   docker-compose up -d
   ```

4. **Check service status**:
   ```bash
   docker-compose ps
   ```

5. **View logs**:
   ```bash
   # All services
   docker-compose logs -f
   
   # Specific service
   docker-compose logs -f api
   ```

6. **Access the application**:
   - **API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs
   - **Frontend**: http://localhost:5173 (React dev server)

## Services

The Docker Compose setup includes the following services:

### Core Services

- **postgres**: PostgreSQL database with pgvector extension
- **redis**: Redis cache and message broker
- **api**: FastAPI backend service (port 8000)
- **frontend**: React frontend (port 80, or 5173 for dev)

### Background Workers

- **celery_worker**: Celery worker for async tasks
- **celery_beat**: Celery beat scheduler for periodic tasks

## Configuration

### Environment Variables

All configuration is managed through the `.env` file. Key variables:

#### Required
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Application secret key (auto-generated for dev)
- `JWT_SECRET_KEY`: JWT signing key (auto-generated for dev)

#### Optional (External APIs)
These are disabled by default for local development:
- `OMNIVINCI_API_KEY`: NVIDIA OmniVinci API key
- `FIRECRAWL_API_KEY`: Firecrawl web scraping API key
- `YOUTUBE_API_KEY`: YouTube Data API v3 key
- `META_ACCESS_TOKEN`: Meta/Facebook Graph API access token
- `USDA_API_KEY`, `CITES_API_KEY`, `USFWS_API_KEY`: Government API keys

#### Optional (Models)
- `MEGADETECTOR_MODEL_PATH`: Path to MegaDetector model
- `REID_MODEL_PATH`: Path to Tiger Re-ID model
- Other model paths are configured but models are optional

### Model Downloads

Models are automatically downloaded on first startup via the `init_models.py` script:

- **MegaDetector v5**: Required for tiger detection (~500MB)
- **OmniVinci**: Optional, only if `OMNIVINCI_USE_LOCAL=true` (~18GB)

Models are stored in `./data/models/` and persist across container restarts.

## Common Tasks

### Reset Everything

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (deletes database and Redis data)
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

### Database Migrations

The database schema is automatically initialized on first startup. To manually run migrations:

```bash
docker-compose exec api python -c "from backend.database.connection import init_db; init_db()"
```

### Access Database

```bash
# Using psql
docker-compose exec postgres psql -U tiger_user -d tiger_investigation

# Or connect from host
psql postgresql://tiger_user:tiger_password@localhost:5432/tiger_investigation
```

### Access Redis

```bash
docker-compose exec redis redis-cli
```

### View API Logs

```bash
# Real-time logs
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api
```

### Restart a Service

```bash
# Restart API
docker-compose restart api

# Restart all services
docker-compose restart
```

### Run Tests

```bash
# Run tests in API container
docker-compose exec api pytest

# Run specific test file
docker-compose exec api pytest backend/tests/test_auth.py
```

## Troubleshooting

### Services Won't Start

1. **Check Docker is running**:
   ```bash
   docker ps
   ```

2. **Check ports are available**:
   - Port 5432 (PostgreSQL)
   - Port 6379 (Redis)
   - Port 8000 (API)
   - Port 5173 (Frontend dev server)
   - Port 80 (Frontend production)

3. **Check logs**:
   ```bash
   docker-compose logs
   ```

### Database Connection Errors

1. **Wait for database to be ready**:
   ```bash
   docker-compose logs postgres | grep "ready to accept connections"
   ```

2. **Check database health**:
   ```bash
   docker-compose exec postgres pg_isready -U tiger_user
   ```

### Model Download Fails

Models are downloaded automatically on startup. If download fails:

1. **Check disk space**:
   ```bash
   docker system df
   ```

2. **Manually download models**:
   ```bash
   docker-compose exec api python scripts/init_models.py
   ```

3. **Check network connectivity** (for downloading from external sources)

### API Health Check Fails

```bash
# Check API health endpoint
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","database":"healthy","redis":"healthy","version":"1.0.0"}
```

### "Permission Denied" Errors

On Windows, ensure Docker Desktop has proper file permissions. On Linux/Mac:

```bash
# Ensure entrypoint script is executable
chmod +x docker/entrypoint.sh
```

### Out of Memory

If containers crash due to memory:

1. **Increase Docker memory limit** in Docker Desktop settings
2. **Reduce batch sizes** in `.env`:
   ```
   BATCH_SIZE=16
   ```

### Slow Startup

First startup can be slow due to:
- Docker image pulls
- Model downloads
- Database initialization

Subsequent startups should be faster. Check logs to see what's happening:

```bash
docker-compose logs -f api
```

## Development Workflow

### Making Code Changes

Code changes are automatically reflected in containers due to volume mounts:
- `.:/app` - Mounts entire codebase
- Changes to Python files trigger auto-reload (FastAPI)
- Frontend changes are handled by Vite's hot module replacement

### Running Migrations

```bash
# Create migration (if using Alembic)
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head
```

### Adding Dependencies

1. Add to `requirements.txt` or `requirements-dev.txt`
2. Rebuild container:
   ```bash
   docker-compose build api
   docker-compose up -d api
   ```

### Debugging

1. **Attach to running container**:
   ```bash
   docker-compose exec api bash
   ```

2. **Run Python interactively**:
   ```bash
   docker-compose exec api python
   ```

3. **Check environment variables**:
   ```bash
   docker-compose exec api env | grep DATABASE_URL
   ```

## Optional Features

### Enable External APIs

Edit `.env` and add your API keys:

```env
# Enable YouTube
YOUTUBE_API_KEY=your-key-here
YOUTUBE_ENABLED=true

# Enable Firecrawl
FIRECRAWL_API_KEY=your-key-here
FIRECRAWL_SEARCH_ENABLED=true
```

Then restart services:
```bash
docker-compose restart api celery_worker
```

### Enable Local OmniVinci Model

**Warning**: OmniVinci model is ~18GB and requires significant GPU memory.

```env
OMNIVINCI_USE_LOCAL=true
OMNIVINCI_MODEL_PATH=./data/models/omnivinci/omnivinci
```

The model will be downloaded automatically on next startup (this may take hours).

### Enable Dataset Ingestion

```env
INGEST_DATASETS_ON_STARTUP=true
```

This will start background ingestion of reference datasets on startup.

## Next Steps

- See `docs/API.md` for API documentation
- See `docs/ARCHITECTURE.md` for system architecture
- See `docs/CONFIGURATION.md` for detailed configuration guide

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Check health endpoint: `curl http://localhost:8000/health`
3. Review this guide's troubleshooting section
4. Check GitHub issues

