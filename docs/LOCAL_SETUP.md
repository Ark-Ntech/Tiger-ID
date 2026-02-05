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

- **api**: FastAPI backend service (port 8000) with SQLite database
- **frontend**: React frontend (port 80, or 5173 for dev)

### Background Processing

Background tasks are handled via:
- **Modal** - Serverless GPU functions for ML inference
- **LangGraph** - Async investigation workflows
- **Threading** - Non-blocking database operations

## Configuration

### Environment Variables

All configuration is managed through the `.env` file. Key variables:

#### Required
- `DATABASE_URL`: SQLite database path (default: `sqlite:///data/tiger_id.db`)
- `SECRET_KEY`: Application secret key (auto-generated for dev)
- `JWT_SECRET_KEY`: JWT signing key (auto-generated for dev)

#### Optional (External APIs)
These are disabled by default for local development:
- `ANTHROPIC_API_KEY`: Anthropic Claude API key (required for report generation)
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

### Database Initialization

The database schema is automatically initialized on first startup. To manually initialize:

```bash
docker-compose exec api python -c "from backend.database import init_db; init_db()"
```

### Access Database

```bash
# Using sqlite3 CLI
sqlite3 data/tiger_id.db

# Or from within Docker
docker-compose exec api sqlite3 /app/data/tiger_id.db
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
   - Port 8000 (API)
   - Port 5173 (Frontend dev server)
   - Port 80 (Frontend production)

3. **Check logs**:
   ```bash
   docker-compose logs
   ```

### Database Errors

1. **Check sqlite-vec is installed**:
   ```bash
   pip show sqlite-vec
   ```

2. **Verify database file exists**:
   ```bash
   ls -la data/tiger_id.db
   ```

3. **Re-initialize if needed**:
   ```bash
   python -c "from backend.database import init_db; init_db()"
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
# {"status":"healthy","database":"healthy","models":"available",...}
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

### Reinitialize Database

```bash
# Database schema is auto-initialized; to force reinitialize:
docker-compose exec api python -c "from backend.database import init_db; init_db()"
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
docker-compose restart api
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

