# 🚀 Tiger ID - Quick Start

## 🎯 Start the Application

### ⭐ npm (Simplest - Recommended!)
```bash
npm start
```
**One command starts everything:**
- ✅ Backend API (http://localhost:8000)
- ✅ Frontend (http://localhost:5173)
- ✅ ML models on Modal serverless GPUs
- ✅ Colored output with live logs

**Alternative npm commands:**
```bash
npm run dev              # Same as npm start
npm run start:backend    # Backend only
npm run start:frontend   # Frontend only
npm run deploy:modal     # Deploy to Modal
npm run modal:status     # Check Modal deployment
npm run modal:logs       # View Modal logs
npm test                 # Run Modal integration tests
```

### Docker (Alternative - Full Stack)
```batch
setup\windows\START_DOCKER.bat
```
**Everything runs automatically:** Database, migrations, backend, frontend, test user

### Scripts (Alternative - Windows-Specific)
```batch
START_MODAL.bat          # Windows batch
.\START_MODAL.ps1        # PowerShell
setup\windows\START_SERVERS.bat  # Quick restart
```

---

## 🌐 Access

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 🔑 Login

- **Username:** `admin`
- **Password:** `admin`

---

## 📚 Documentation

### Modal Integration
- **Modal Guide:** `docs/MODAL.md` - Complete Modal documentation
- **Troubleshooting:** `docs/TROUBLESHOOTING.md` - Common issues and solutions

### Application Documentation
- **Complete Setup Guide:** `setup/docs/SETUP_GUIDE.md`
- **React Migration Details:** `setup/docs/REACT_MIGRATION.md`
- **Setup Scripts:** `setup/README.md`
- **Frontend Docs:** `frontend/README.md`

---

## 🆘 First Time Setup

If starting from scratch:

### Step 1: Install Dependencies
```bash
npm run setup
```
Or manually:
```bash
pip install -r requirements.txt
cd frontend && npm install
```

### Step 2: Deploy to Modal
```bash
npm run deploy:modal
```
Or manually:
```bash
python -m modal deploy backend/modal_app.py
```

### Step 3: Start Application
```bash
npm start
```

**That's it!** Much simpler than batch scripts. 🚀

---

**Questions?** See `setup/docs/SETUP_GUIDE.md` for troubleshooting and detailed instructions.

