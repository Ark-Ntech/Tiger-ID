# Windows Batch Scripts

Quick reference for Windows users.

## Primary Scripts

### START_DOCKER.bat ⭐
**Use this for easiest setup!**

Starts everything with Docker:
- PostgreSQL + Redis
- Backend API (with auto-setup)
- Frontend dev server
- Automatically creates test user

### STOP_DOCKER.bat
Stops all Docker services.

### START_SERVERS.bat
Starts backend + frontend locally (requires PostgreSQL running separately).

### SETUP_ALL.bat
Complete first-time setup:
- Installs Python dependencies
- Installs Node.js dependencies
- Sets up database
- Creates test user

### SETUP_DATABASE.bat
Database setup only:
- Runs migrations
- Creates test user

---

## Usage

All scripts can be run by double-clicking or from PowerShell:

```powershell
.\setup\windows\START_DOCKER.bat
```

---

## What Each Script Does

| Script | Database | Backend | Frontend | Auto-Setup |
|--------|----------|---------|----------|------------|
| START_DOCKER.bat | ✅ Starts | ✅ Starts | ✅ Starts | ✅ Yes |
| START_SERVERS.bat | ❌ Manual | ✅ Starts | ✅ Starts | ❌ No |
| SETUP_ALL.bat | ✅ Setup | ✅ Install | ✅ Install | ✅ Yes |
| SETUP_DATABASE.bat | ✅ Setup | ❌ No | ❌ No | ✅ Yes |
| STOP_DOCKER.bat | ✅ Stops | ✅ Stops | ✅ Stops | N/A |

---

**Recommended:** Use `START_DOCKER.bat` for hassle-free setup.

