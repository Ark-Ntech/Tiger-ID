# Troubleshooting Guide

This document consolidates common issues and solutions for the Tiger ID system.

---

## Table of Contents

- [Database Issues](#database-issues)
- [Modal & GPU Issues](#modal--gpu-issues)
- [Model Loading Issues](#model-loading-issues)
- [Frontend Issues](#frontend-issues)
- [API Issues](#api-issues)
- [Discovery Pipeline Issues](#discovery-pipeline-issues)
- [Common Errors](#common-errors)

---

## Database Issues

### Database Connection Failed

**Error:**
```
sqlalchemy.exc.OperationalError: unable to open database file
```

**Solutions:**

1. **Check database file path:**
   ```bash
   ls -la data/tiger_id.db
   ```

2. **Verify DATABASE_URL format:**
   ```env
   DATABASE_URL=sqlite:///data/tiger_id.db
   ```

3. **Create data directory if missing:**
   ```bash
   mkdir -p data
   ```

### Database Integrity Issues

**Check database integrity:**
```bash
sqlite3 data/tiger_id.db "PRAGMA integrity_check;"
```

**Re-initialize if corrupted:**
```bash
rm data/tiger_id.db*
python -c "from backend.database import init_db; init_db()"
```

### sqlite-vec Not Found

**Error:**
```
sqlite-vec extension is required for vector search
```

**Solution:**
```bash
pip install sqlite-vec>=0.1.6
python -c "import sqlite_vec; print('OK')"
```

### Database Locked

**Error:**
```
database is locked
```

**Solutions:**

1. **Ensure single writer:** SQLite allows only one writer at a time
2. **Check for long transactions:** Close any open database connections
3. **Restart the application:** Clear any stale locks

---

## Modal & GPU Issues

### Modal App Not Found

**Error:**
```
ModalUnavailableError: Modal app not deployed
```

**Solution:**
```bash
modal deploy backend/modal_app.py
```

### Deployment Fails

**Check logs:**
```bash
modal app logs tiger-id-models --tail
```

**Common causes:**
- Missing dependencies in requirements
- Container build timeout
- Insufficient Modal credits

**Retry deployment:**
```bash
modal deploy backend/modal_app.py
```

### Request Timeout

**Error:**
```
asyncio.TimeoutError: Request timeout
```

**Solutions:**

1. Increase timeout in `.env`:
   ```env
   MODAL_TIMEOUT=180
   ```

2. Check Modal service status at https://modal.com/status

3. Verify model is deployed:
   ```bash
   modal app list
   ```

### Gateway Timeout (502/504)

The Modal client has total timeout tracking (default: 90s) to prevent gateway timeouts:

**If you see gateway timeouts:**
1. Check if operation is too complex (multiple retries exhausted)
2. The client aborts retries when approaching the 90s limit
3. Consider breaking up large batch operations

**Adjust if needed:**
```python
# In backend/services/modal_client.py
MAX_TOTAL_TIMEOUT = 90  # Adjust based on your gateway configuration
```

### Queue Full

**Error:**
```
ModalClientError: Request queue is full
```

**Solutions:**

1. Increase queue size:
   ```env
   MODAL_QUEUE_MAX_SIZE=200
   ```

2. Wait for queued requests to process

3. Check for Modal unavailability

### Cold Start Latency

**Symptom:** First requests take 5-15 seconds

**Explanation:** Normal behavior. Modal containers spin up on-demand.

**Mitigation:** Use warm-up requests after deployment.

---

## Model Loading Issues

### Model Weights Not Found

**Error:**
```
FileNotFoundError: data/models/tiger_reid_model.pth not found
```

**Solution:**
```bash
python scripts/download_models.py --model all
```

### CUDA Out of Memory

**Error:**
```
RuntimeError: CUDA out of memory
```

**Solutions:**

1. Reduce batch size:
   ```env
   BATCH_SIZE=16
   ```

2. Use smaller GPU tier in Modal

3. Process images sequentially

### Wrong Embedding Dimensions

**Error:**
```
ValueError: dimension mismatch
```

**Check model registry:**
```python
from backend.infrastructure.modal.model_registry import MODEL_REGISTRY
print(MODEL_REGISTRY['wildlife_tools']['embedding_dim'])  # Should be 1536
```

**Verify database embeddings match model dimensions.**

### Model Not Loading

**Check model files exist:**
```bash
ls -lh data/models/
```

**Test model loading:**
```python
python -c "from backend.models.detection import MegaDetectorModel; import asyncio; asyncio.run(MegaDetectorModel().load_model())"
```

---

## Frontend Issues

### Build Fails

**TypeScript errors:**
```bash
cd frontend && npx tsc --noEmit
```

**Fix common issues:**
- Check import paths
- Verify type definitions
- Update dependencies

### API Connection Failed

**Error in browser console:**
```
CORS error / Network error
```

**Solutions:**

1. Verify backend is running on port 8000

2. Check VITE_API_URL in `.env`:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

3. Verify CORS is configured in backend

### WebSocket Not Connecting

**Check WebSocket URL:**
```env
VITE_WS_URL=ws://localhost:8000
```

**Verify backend WebSocket endpoint is active.**

### WebSocket Disconnects

The frontend implements automatic reconnection with exponential backoff:

- Up to 5 reconnection attempts
- Base delay: 1 second
- Maximum delay: 30 seconds
- Exponential backoff: delay doubles each attempt

**If reconnection fails:**
1. Check backend is running
2. Verify WebSocket endpoint responds
3. Check for network issues
4. Refresh the page to reset connection state

### WebSocket Error Messages

Error messages from WebSocket connections are sanitized to prevent information disclosure. Users see friendly messages like:
- "The ML service is temporarily unavailable. Please try again later."
- "Your session has expired. Please reconnect."
- "An unexpected error occurred. Please try again."

**For detailed errors:** Check backend logs at `docker-compose logs api`

### Hot Reload Not Working

```bash
# Restart Vite dev server
cd frontend
npm run dev
```

---

## API Issues

### Authentication Failed

**Error:**
```
401 Unauthorized
```

**Solutions:**

1. Check JWT token validity
2. Verify SECRET_KEY and JWT_SECRET_KEY in `.env`
3. Token may be expired - re-login

### Rate Limited

**Error:**
```
429 Too Many Requests
```

**Default:** 60 requests/minute per IP

**Solution:** Wait and retry, or increase limit in settings.

### Health Check Failing

**Check endpoint:**
```bash
curl http://localhost:8000/api/health
```

**Expected response:**
```json
{"status": "healthy", "database": "connected"}
```

---

## Discovery Pipeline Issues

### Playwright Not Working

**Error:**
```
playwright._impl._errors.BrowserNotInstalled
```

**Solution:**
```bash
pip install playwright
playwright install chromium --with-deps
```

### Rate Limiting Too Aggressive

**Adjust settings:**
```env
RATE_LIMIT_BASE_INTERVAL=1.0
RATE_LIMIT_MAX_BACKOFF=30.0
```

### Images Not Being Discovered

1. Check facility URL is accessible
2. Verify JavaScript rendering works
3. Check rate limiter isn't blocking
4. Review crawler logs

### Duplicate Detection Not Working

**Check `content_hash` column exists:**
```bash
sqlite3 data/tiger_id.db ".schema tiger_images" | grep content_hash
```

**Re-initialize schema if missing:**
```bash
python -c "from backend.database import init_db; init_db()"
```

---

## Common Errors

### Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'backend'
```

**Solution:** Run from project root or set PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Environment Variables Not Loading

**Check `.env` file exists and has correct format:**
```bash
cat .env | head -10
```

**Verify python-dotenv is installed:**
```bash
pip install python-dotenv
```

### Anthropic API Errors

**Error:**
```
anthropic.AuthenticationError: Invalid API key
```

**Solution:** Verify ANTHROPIC_API_KEY in `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-...
```

### Memory Errors

**Symptom:** Backend crashes during model inference

**Solutions:**

1. Use Modal for GPU inference (offloads memory)
2. Reduce batch size
3. Process images sequentially
4. Increase system RAM

### Permission Denied

**Error:**
```
PermissionError: [Errno 13] Permission denied
```

**Solutions:**

1. Check file/directory permissions
2. Run with appropriate user
3. Verify Docker volume mounts

---

## Diagnostic Commands

### System Health Check

```bash
# Backend health
curl http://localhost:8000/api/health

# Database connection
docker-compose exec postgres pg_isready

# Redis connection
docker-compose exec redis redis-cli ping

# Modal status
modal app list
```

### Log Locations

| Component | Log Command |
|-----------|-------------|
| Backend | `docker-compose logs api` |
| Frontend | Browser DevTools Console |
| Modal | `modal app logs tiger-id-models` |
| Database | `docker-compose logs postgres` |

### Reset Everything

```bash
# Stop all services
docker-compose down -v

# Remove data
rm -rf data/storage/*
rm -rf data/*.db

# Restart fresh
docker-compose up -d
python -c "from backend.database import init_db; init_db()"
python scripts/init_db.py
```

---

## Getting Help

1. Check this troubleshooting guide
2. Review relevant documentation in `docs/`
3. Check Modal status: https://modal.com/status
4. Open an issue on GitHub with:
   - Error message
   - Steps to reproduce
   - Environment details (OS, Python version)
   - Relevant logs

---

*Last Updated: February 2026*
