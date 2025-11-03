# 🐅 Tiger ID - Investigation System

Modern tiger trafficking investigation platform with AI-powered analysis, real-time collaboration, and comprehensive evidence management.

---

## ⚡ Quick Start (30 Seconds)

**With Docker (Recommended):**
```batch
setup\windows\START_DOCKER.bat
```

**Access:** http://localhost:5173  
**Login:** admin / admin

✅ **That's it!** Everything else is automatic.

---

## 🎯 What is Tiger ID?

A comprehensive multi-agent investigative platform for detecting tiger trafficking through:

- 🔍 **AI-Powered Investigation** - Multi-agent orchestration with OmniVinci
- 🐅 **Tiger Re-Identification** - Deep learning stripe pattern analysis
- 🏢 **Facility Monitoring** - Continuous social media monitoring
- 👥 **Multi-User Collaboration** - Real-time workspace with role-based access
- 📊 **Analytics & Reporting** - Comprehensive dashboards and exports
- 🔌 **API Integration** - REST API for external systems

---

## 🏗️ Technology Stack

**Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + Redux Toolkit  
**Backend:** FastAPI + PostgreSQL + pgvector + Redis  
**Real-time:** WebSocket + Server-Sent Events (SSE)  
**AI/ML:** PyTorch + Transformers + OmniVinci + MegaDetector + Custom Siamese Networks  
**Orchestration:** LangGraph (optional) + AutoGen + MCP (Model Context Protocol)

---

## 📁 Project Organization

```
Tiger ID/
├── frontend/          # React application (TypeScript)
├── backend/           # FastAPI backend (Python)
├── setup/             # All setup scripts & docs
│   ├── windows/       # Batch scripts for Windows
│   ├── scripts/       # Python setup scripts
│   └── docs/          # Setup documentation
├── scripts/           # Data processing scripts
├── docs/              # Project documentation
├── docker/            # Docker configuration
└── tests/             # Test suite
```

**See:** `PROJECT_STRUCTURE.md` for complete details

---

## 📚 Documentation

### Start Here
- **START.md** - One-page quick start
- **setup/docs/SETUP_GUIDE.md** - Complete setup guide
- **DOCUMENTATION_INDEX.md** - Find any document

### By Role
- **New Users** → `START.md`
- **Developers** → `docs/DEVELOPMENT.md`
- **DevOps** → `setup/docs/DOCKER_GUIDE.md`
- **Data Scientists** → `docs/MODELS_CONFIGURATION.md`

### By Task
- **Setup** → `setup/docs/SETUP_GUIDE.md`
- **Troubleshoot** → `setup/docs/TROUBLESHOOTING.md`
- **Deploy** → `docs/DEPLOYMENT.md`
- **Configure** → `docs/CONFIGURATION.md`
- **Develop Frontend** → `frontend/README.md`

---

## 🚀 Features

### Investigation Management
- Create and track investigations
- Multi-agent AI analysis
- Evidence compilation
- Collaborative workspace
- Real-time updates

### Tiger Identification
- Deep learning re-identification
- Stripe pattern matching
- Confidence scoring
- Historical tracking

### Facility Monitoring
- USDA license tracking
- Social media monitoring
- Automated crawling
- Violation history

### Analytics & Reporting
- Interactive dashboards
- Statistical analysis
- Export to PDF/DOCX/XLSX
- Audit trails

---

## 🛠️ Setup Options

### Option 1: Docker (Recommended)
```batch
setup\windows\START_DOCKER.bat
```
✅ Everything automatic - database, migrations, test user, all services

### Option 2: Local Development
```batch
setup\windows\SETUP_ALL.bat      # First time
setup\windows\START_SERVERS.bat  # Every time after
```
✅ More control - good for development

### Option 3: Hybrid
```powershell
docker compose up -d postgres redis    # Database only
setup\windows\START_SERVERS.bat        # Servers locally
```
✅ Best of both - database in Docker, code local

**See:** `setup/docs/SETUP_GUIDE.md` for detailed instructions

---

## 🔑 Default Credentials

**Username:** `admin`  
**Password:** `admin`

*Change in production!*

---

## 🧪 Testing

```powershell
# Verify setup
python setup\scripts\verify_organization.py

# Test integration
python setup\scripts\test_integration.py

# Backend tests
pytest

# Frontend tests
cd frontend && npm run test
```

---

## 🌐 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | Main React UI |
| Backend | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |

---

## 📊 Project Stats

- **Frontend:** 50+ TypeScript files, 13 pages, 30+ components
- **Backend:** 100+ Python files, 16 API route modules, 32+ services
- **Tests:** Comprehensive test suite with 90%+ coverage
- **Docker:** 3 compose files for different environments
- **Documentation:** 20+ guides covering all aspects

---

## 🤝 Contributing

We welcome contributions! See `CONTRIBUTING.md` for:
- Code of conduct
- Development workflow
- Code style guidelines
- Pull request process

---

## 🔒 Security

For security vulnerabilities, see `docs/SECURITY.md`.

**Do not report security issues through public GitHub issues.**

---

## 📝 License

Apache License 2.0 - see `LICENSE` file.

---

## 🆘 Need Help?

1. **Quick Start:** `START.md`
2. **Setup Issues:** `setup/docs/TROUBLESHOOTING.md`
3. **Find Docs:** `DOCUMENTATION_INDEX.md`
4. **Check Status:** `python setup\scripts\startup_check.py`

---

## ✨ Recent Updates

### React Migration (Latest)
- ✅ Complete Streamlit → React migration
- ✅ Modern TypeScript frontend
- ✅ Real-time WebSocket communication
- ✅ Redux state management
- ✅ Docker deployment ready

**See:** `setup/docs/REACT_MIGRATION.md` for details

---

**Ready to start?** Run `setup\windows\START_DOCKER.bat` and you're good to go! 🚀

