# Docker Setup Guide

## Quick Start

```batch
setup\windows\START_DOCKER.bat
```

That's it! Everything else is automatic.

---

## Docker Compose Files

### `docker-compose.quickstart.yml` (Recommended)

**Use for:** Complete auto-setup in one command

**Features:**
- Auto-runs migrations
- Auto-creates test user (admin/admin)
- Development mode with hot reload
- All services configured

**Start:**
```batch
setup\windows\START_DOCKER.bat
```

**Or manually:**
```powershell
docker compose -f docker-compose.quickstart.yml up -d
```

---

### `docker-compose.dev.yml`

**Use for:** Development with hot reload

**Features:**
- Mounts local code for editing
- Auto-reload on changes
- Separate frontend-dev service

**Start:**
```powershell
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml --profile dev up -d  # Include frontend-dev
```

---

### `docker-compose.yml`

**Use for:** Production deployment

**Features:**
- Production-optimized builds
- No code mounting
- Nginx serving static files

**Start:**
```powershell
docker compose up -d
```

---

## Service Details

| Service | Port | Purpose |
|---------|------|---------|
| postgres | 5432 | PostgreSQL + pgvector |
| redis | 6379 | Cache & Celery broker |
| api | 8000 | FastAPI backend |
| frontend | 80 | Production build |
| frontend-dev | 5173 | Development with HMR |

---

## Common Commands

### Start Everything
```powershell
docker compose -f docker-compose.quickstart.yml up -d
```

### Stop Everything
```powershell
docker compose -f docker-compose.quickstart.yml down
```

### View Logs
```powershell
docker compose -f docker-compose.quickstart.yml logs -f

# Specific service
docker compose logs -f api
docker compose logs -f frontend-dev
```

### Restart Service
```powershell
docker compose restart api
docker compose restart frontend-dev
```

### Rebuild Images
```powershell
docker compose -f docker-compose.quickstart.yml build --no-cache
```

### Execute Commands in Container
```powershell
# Create user
docker compose exec api python setup/scripts/create_test_user.py

# Database shell
docker compose exec postgres psql -U tiger_user -d tiger_investigation

# Redis shell
docker compose exec redis redis-cli
```

---

## Environment Variables

Services use these environment variables (set in docker-compose):

```yaml
DATABASE_URL=postgresql://tiger_user:tiger_password@postgres:5432/tiger_investigation
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=dev-secret-key-change-in-production
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## Volumes

**Persistent data:**
- `postgres_data` - Database files
- `redis_data` - Redis persistence

**Mounted directories:**
- `./data/storage` - Uploaded files
- `./frontend` - Frontend code (dev only)
- `./` - Backend code (dev only)

---

## Health Checks

All services have health checks:

**Check status:**
```powershell
docker compose ps
```

**Healthy services** show "healthy" in STATUS column.

---

## Troubleshooting Docker

### Services Won't Start

```powershell
# Check logs
docker compose logs

# Check individual service
docker compose logs api
```

### Database Issues

```powershell
# Recreate database
docker compose down -v
docker compose up -d postgres
```

### Port Conflicts

```powershell
# Check what's using ports
netstat -ano | findstr :8000
netstat -ano | findstr :5173
netstat -ano | findstr :5432

# Kill process or change port in docker-compose
```

### Clean Start

```powershell
# Remove everything
docker compose -f docker-compose.quickstart.yml down -v

# Remove images
docker system prune -a

# Start fresh
docker compose -f docker-compose.quickstart.yml up -d
```

---

## Production Deployment

For production, use:

```powershell
# Build production images
docker compose build

# Start in production mode
docker compose up -d

# No development mounts, optimized builds
```

Update environment variables for production in `.env`:
- Strong JWT_SECRET_KEY
- Production DATABASE_URL
- Production FRONTEND_URL

---

**Recommended:** Use `docker-compose.quickstart.yml` for development.

