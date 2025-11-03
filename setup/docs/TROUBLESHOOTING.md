# Troubleshooting Guide

## Common Issues & Solutions

### 🔴 Can't Login / 401 Unauthorized

**Cause:** Test user doesn't exist in database

**Solution:**
```powershell
python setup\scripts\create_test_user.py
```

---

### 🔴 Database Connection Failed

**Cause:** PostgreSQL not running

**Solutions:**

**With Docker:**
```powershell
docker compose up -d postgres redis
```

**Without Docker:**
- Ensure PostgreSQL 15+ is installed and running
- Check DATABASE_URL in `.env`
- Verify connection: `psql -U tiger_user -d tiger_investigation`

---

### 🔴 Frontend Won't Start / CSS Errors

**Solution 1 - Reinstall dependencies:**
```powershell
cd frontend
rm -r node_modules package-lock.json
npm install --legacy-peer-deps
```

**Solution 2 - Clear cache:**
```powershell
cd frontend
rm -r .vite dist
npm run dev
```

---

### 🔴 Backend "uvicorn not found"

**Cause:** Dependencies not installed

**Solution:**
```powershell
pip install -r requirements.txt
```

Or use:
```powershell
python -m uvicorn backend.api.app:app --reload
```

---

### 🔴 Port Already in Use

**Check what's using the port:**
```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :5173
```

**Kill the process:**
```powershell
taskkill /PID <PID> /F
```

---

### 🔴 CORS Errors in Browser

**Cause:** Backend CORS not configured properly

**Check:** Backend should be on port 8000, frontend on 5173

**Verify:** `backend/api/app.py` has:
```python
allow_origins=["http://localhost:5173", ...]
```

---

### 🔴 WebSocket Won't Connect

**Causes:**
- Token expired
- Backend not running
- Wrong WebSocket URL

**Solutions:**
1. Clear localStorage and re-login
2. Check backend is running on port 8000
3. Verify VITE_WS_URL in `frontend/.env`

---

### 🔴 Docker Build Fails

**Clear Docker cache:**
```powershell
docker system prune -a
docker compose -f docker-compose.quickstart.yml build --no-cache
```

---

### 🔴 Migrations Fail

**Manual migration:**
```powershell
cd backend\database
alembic upgrade head
```

**Or create tables directly:**
```powershell
python -c "from backend.database.connection import init_db; init_db()"
```

---

### 🔴 "Module not found" Errors

**Backend:**
```powershell
pip install -r requirements.txt
```

**Frontend:**
```powershell
cd frontend
npm install --legacy-peer-deps
```

---

## 🔍 Debugging Commands

### Check Services Status

```powershell
# Docker services
docker compose ps

# Check if API is running
curl http://localhost:8000/api/v1/health

# Check if frontend is running
curl http://localhost:5173
```

### View Logs

**Docker:**
```powershell
docker compose -f docker-compose.quickstart.yml logs -f
docker compose logs -f api
docker compose logs -f frontend-dev
```

**Local:**
- Check terminal windows for errors
- Browser console (F12) for frontend errors

### Database Shell

```powershell
# Docker
docker compose exec postgres psql -U tiger_user -d tiger_investigation

# Local
psql -U tiger_user -d tiger_investigation
```

### Redis Shell

```powershell
# Docker
docker compose exec redis redis-cli

# Local
redis-cli
```

---

## ✅ Validation Scripts

Run these to check system health:

```powershell
# System check
python setup\scripts\startup_check.py

# Integration test
python setup\scripts\test_integration.py
```

---

## 🆘 Still Having Issues?

1. **Check logs** in terminal windows
2. **Run validation:** `python setup\scripts\startup_check.py`
3. **Try Docker method:** `setup\windows\START_DOCKER.bat`
4. **Check browser console** (F12) for JavaScript errors
5. **Review:** `setup/docs/SETUP_GUIDE.md`

---

## 💡 Pro Tips

- Use Docker for easiest setup
- Keep terminal windows open to see errors
- Check browser console for frontend errors
- API docs at http://localhost:8000/docs are interactive
- Clear browser cache if UI looks broken

---

**Most common fix:** Close everything and run `setup\windows\START_DOCKER.bat`

