# 🐅 Tiger ID - Investigation System

Modern tiger trafficking investigation platform with AI-powered analysis, real-time collaboration, and comprehensive evidence management.

---

## ⚡ Quick Start (30 Seconds)

### Option 1: npm (Simplest - Recommended!)

```bash
npm start
```

### Option 2: Docker (Recommended for Production)

```batch
setup\windows\START_DOCKER.bat
```

**Access:** http://localhost:5173  
**Login:** admin / admin

✅ **That's it!** Everything else is automatic.

---

## 🎯 What is Tiger ID?

A comprehensive multi-agent investigative platform for detecting tiger trafficking through:

- 🔍 **AI-Powered Investigation** - Gemini-powered agent orchestration with Search Grounding
- 🐅 **Tiger Re-Identification** - Deep learning stripe pattern analysis with 4+ models
- 🌐 **Web Intelligence** - Real-time search with citations via Gemini Search Grounding
- 🏢 **Facility Monitoring** - Continuous social media and USDA license tracking
- 👥 **Multi-User Collaboration** - Real-time workspace with role-based access
- 📊 **Analytics & Reporting** - Comprehensive dashboards and exports
- 🔌 **API Integration** - REST API with streamlined investigation workflow
- 🤖 **MCP Integration** - Model Context Protocol for external tool integration

---

## 🏗️ Technology Stack

**Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + Redux Toolkit
**Backend:** FastAPI + SQLite/PostgreSQL + pgvector + Redis
**Real-time:** WebSocket + Server-Sent Events (SSE)
**AI/ML:** PyTorch + Transformers + OmniVinci + MegaDetector + Custom Siamese Networks
**LLM:** Google Gemini 2.5 (Flash + Pro) with Search Grounding
**Orchestration:** LangGraph + AutoGen + MCP (Model Context Protocol)
**ML Infrastructure:** Modal (Serverless GPU compute for all models)

---

## 📁 Project Organization

```
Tiger ID/
├── frontend/          # React application (TypeScript)
│   ├── src/
│   │   ├── pages/     # 22 pages
│   │   ├── components/# 47+ components
│   │   ├── app/       # Redux store & API
│   │   └── hooks/     # Custom React hooks
├── backend/           # FastAPI backend (Python)
│   ├── api/           # 27 API route modules
│   ├── services/      # 52 service modules
│   ├── agents/        # 6 agent modules (LangGraph)
│   ├── models/        # 8 ML model implementations
│   ├── mcp_servers/   # 11 MCP server implementations
│   └── database/     # Database models & migrations
├── scripts/           # Data processing & setup scripts
├── docs/              # 23 documentation files
├── docker/            # Docker configuration
└── tests/             # 59 test files
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
- Create and track investigations with multi-phase workflows
- Multi-agent AI analysis (Research, Analysis, Validation, Reporting)
- Evidence compilation and review
- Collaborative workspace with real-time updates
- Approval workflows and status tracking
- Investigation templates and saved searches

### Tiger Identification
- **4+ Re-ID Models** (all on Modal serverless GPUs):
  - **TigerReID** - ResNet50-based tiger re-identification
  - **WildlifeTools** - MegaDescriptor embeddings (A100 GPU)
  - **RAPID** - Real-time Animal Pattern ReID
  - **CVWC2019** - Part-pose guided tiger ReID
- **MegaDetector** - Animal detection v5
- **OmniVinci** - Multi-modal LLM for image understanding
- Ensemble mode support (staggered/parallel)
- Confidence scoring and similarity matching
- Historical tracking and relationship analysis

### Facility Monitoring
- USDA license tracking and validation
- Social media monitoring (Meta, YouTube)
- Automated web crawling and scheduling
- Violation history and compliance tracking
- Reference data integration (CITES, USFWS)

### Analytics & Reporting
- Interactive dashboards with real-time stats
- Statistical analysis across investigations, tigers, facilities
- Export to PDF/DOCX/XLSX/CSV/Markdown/JSON
- Audit trails and activity logs
- Geographic analytics and mapping

### Model Management
- Model versioning and performance tracking
- Fine-tuning interface
- Model testing and evaluation
- Model comparison and benchmarking
- Weight upload and management

### Integration & APIs
- **MCP Servers** - Firecrawl, Puppeteer, YouTube, Meta, Database
- **External APIs** - USDA, CITES, USFWS integration
- REST API with comprehensive endpoints
- WebSocket for real-time communication
- Server-Sent Events for live updates

---

## 🛠️ Setup Options

### Option 1: npm (Simplest - Recommended!)

```bash
npm run setup    # First time only
npm start        # Every time after
```

✅ **Cross-platform** - works on Windows, Mac, Linux  
✅ **Simple** - one command to start everything  
✅ **Modern** - standard npm workflow

### Option 2: Docker (For Production)

```batch
setup\windows\START_DOCKER.bat
```

✅ Everything automatic - database, migrations, test user, all services

**See:** `NPM_COMMANDS.md` for all available commands

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

- **Frontend:** 88 TypeScript/TSX files, 22 pages, 47+ components
- **Backend:** 147+ Python files, 27 API route modules, 52 service modules
- **Agents:** 6 agent modules with LangGraph orchestration
- **Models:** 6 ML models (all on Modal serverless GPUs)
- **MCP Servers:** 11 MCP server implementations
- **Tests:** 59 test files with comprehensive coverage
- **Docker:** 3 compose files for different environments
- **Documentation:** 23 guides covering all aspects

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

### Latest (Nov 2025)
- ✅ Fixed missing mutation exports (`useCreateTigerMutation`, `useLaunchInvestigationFromTigerMutation`)
- ✅ Added `applyTemplate` mutation definition
- ✅ Fixed import errors in investigation and model version routes
- ✅ Added new investigation components (AgentActivityFeed, ApprovalModal, BulkActions, etc.)
- ✅ Added new pages (DatasetManagement, FineTuning, ModelWeights, TigerDetail)
- ✅ Added model management routes and services (approval, finetuning, model performance, model version)

### Modal Integration (Nov 2025)
- ✅ All ML models on Modal serverless GPUs
- ✅ OmniVinci upgraded to fully open source
- ✅ Zero API keys required
- ✅ Simplified startup with npm commands
- ✅ 21/21 tests passing

**See:** `docs/MODAL_INTEGRATION_COMPLETE.md` for Modal deployment details

### React Migration (Complete)
- ✅ Complete Streamlit → React migration
- ✅ Modern TypeScript frontend
- ✅ Real-time WebSocket communication
- ✅ Redux state management
- ✅ Docker deployment ready

**See:** `setup/docs/REACT_MIGRATION.md` for details

---

## 🎯 Key Capabilities

### Multi-Agent Investigation System
- **Research Agent** - Web search, news monitoring, data gathering
- **Analysis Agent** - Evidence analysis, relationship mapping, pattern detection
- **Validation Agent** - Fact-checking, verification, approval workflows
- **Reporting Agent** - Report generation, documentation, export

### Tiger Re-Identification
- Upload single or batch images
- Automatic tiger identification with confidence scores
- Support for 4+ different Re-ID models
- Ensemble mode for improved accuracy
- Historical tracking and relationship analysis

### Investigation Tools
- **Web Search** - Firecrawl-powered web intelligence
- **Reverse Image Search** - Find similar images across the web
- **News Monitoring** - Automated news article tracking
- **Lead Generation** - AI-powered lead discovery
- **Relationship Analysis** - Network graph visualization
- **Evidence Compilation** - Automated evidence gathering and organization

### Model Management
- Model versioning and tracking
- Performance metrics and evaluation
- Fine-tuning interface
- Model testing and comparison
- Weight upload and management

---

**Ready to start?** Just run `npm start` and you're good to go! 🚀
