# 🐅 Tiger ID - Complete Setup Guide

## Quick Start (Choose One Method)

### 🐳 Method 1: Docker (Recommended)

**Easiest - Everything automatic!**

```batch
setup\windows\START_DOCKER.bat
```

**Access:** http://localhost:5173  
**Login:** admin / admin

**To stop:**
```batch
setup\windows\STOP_DOCKER.bat
```

---

### 💻 Method 2: Local Development

**First time setup:**
```batch
setup\windows\SETUP_ALL.bat
```

**Every time after:**
```batch
setup\windows\START_SERVERS.bat
```

**Access:** http://localhost:5173  
**Login:** admin / admin

---

## 📁 Setup Files Organization

```
setup/
├── windows/              # Windows batch scripts
│   ├── START_DOCKER.bat      # Start everything with Docker
│   ├── STOP_DOCKER.bat       # Stop Docker services
│   ├── START_SERVERS.bat     # Start backend + frontend locally
│   ├── SETUP_ALL.bat         # Complete first-time setup
│   └── SETUP_DATABASE.bat    # Database setup only
├── scripts/              # Python setup scripts
│   ├── setup_all.py          # Complete setup script
│   ├── setup_database.py     # Database migrations + user
│   └── create_test_user.py   # Create/update admin user
└── docs/                 # Setup documentation
    └── SETUP_GUIDE.md        # This file
```

---

## 🛠️ Detailed Setup Instructions

### Prerequisites

**For Docker method:**
- Docker Desktop

**For local development:**
- Python 3.10+
- Node.js 18+
- PostgreSQL 15+ with pgvector
- Redis (optional)

---

### Docker Setup (Detailed)

1. **Install Docker Desktop**
   - Download from https://www.docker.com/products/docker-desktop

2. **Start everything:**
   ```batch
   setup\windows\START_DOCKER.bat
   ```

3. **Wait 1-2 minutes** for first-time image builds

4. **Access application:**
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
   - API Docs: http://localhost:8000/docs

5. **Login:** admin / admin

**What happens automatically:**
- ✅ PostgreSQL database created
- ✅ pgvector extension enabled
- ✅ Database migrations run
- ✅ Admin user created (admin/admin)
- ✅ Backend API started
- ✅ Frontend dev server started

---

### Local Development Setup (Detailed)

#### Step 1: Install Dependencies

**Backend:**
```powershell
pip install -r requirements.txt
```

**Frontend:**
```powershell
cd frontend
npm install --legacy-peer-deps
cd ..
```

Or use the batch file:
```batch
setup\windows\SETUP_ALL.bat
```

#### Step 2: Start Database

**Option A - Docker (easiest):**
```powershell
docker compose up -d postgres redis
```

**Option B - Local installation:**
- Install PostgreSQL 15+ from https://www.postgresql.org/download/windows/
- Install Redis (optional)
- Update `DATABASE_URL` in `.env` if needed

#### Step 3: Setup Database

```batch
setup\windows\SETUP_DATABASE.bat
```

Or manually:
```powershell
# Run migrations
cd backend\database
alembic upgrade head
cd ..\..

# Create user
python setup\scripts\create_test_user.py
```

#### Step 4: Start Servers

```batch
setup\windows\START_SERVERS.bat
```

This opens two windows:
- Backend API on port 8000
- Frontend on port 5173

---

## 🧪 Verify Setup

```powershell
# Test integration
python scripts\test_integration.py

# Check system
python scripts\startup_check.py
```

---

## 🔑 Login Credentials

**Default admin user:**
- Username: `admin`
- Password: `admin`

**To create custom user:**
```powershell
python setup\scripts\create_test_user.py --username myuser --password mypass
```

---

## 🐛 Troubleshooting

### Can't login / 401 Error
```powershell
# Create test user
python setup\scripts\create_test_user.py
```

### Database connection failed
```powershell
# Start database
docker compose up -d postgres redis

# Wait 10 seconds, then:
python setup\scripts\setup_database.py
```

### Frontend won't compile
```powershell
cd frontend
rm -r node_modules
npm install --legacy-peer-deps
```

### Backend "uvicorn not found"
```powershell
pip install -r requirements.txt
```

### Port already in use
```powershell
# Check what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# Kill process (replace PID)
taskkill /PID <PID> /F
```

---

## 📊 Service Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 5173 | http://localhost:5173 |
| Backend API | 8000 | http://localhost:8000 |
| API Docs | 8000 | http://localhost:8000/docs |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |

---

## 🚀 Development Workflow

1. **Start servers:** `setup\windows\START_SERVERS.bat`
2. **Make changes** to code
3. **See updates** automatically (hot reload)
4. **Test:** `npm run test` in frontend/
5. **Commit** changes

---

## 📚 Additional Documentation

- Main README: `README.md`
- Frontend README: `frontend/README.md`
- Architecture: `docs/ARCHITECTURE.md`
- API Documentation: `docs/API.md`
- Deployment: `docs/DEPLOYMENT.md`

---

## ✨ What You Get

- ✅ Modern React frontend with TypeScript
- ✅ Real-time WebSocket communication
- ✅ Complete authentication system
- ✅ Dashboard with analytics
- ✅ Investigation management
- ✅ Tiger identification
- ✅ Facility monitoring
- ✅ All 14 functional pages

---

**Ready to start!** Choose a method above and begin exploring. 🎉

