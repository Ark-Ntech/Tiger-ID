# Tiger ID Backend

Python backend for the Tiger ID wildlife re-identification system.

## Directory Structure

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `agents/` | LangGraph investigation workflows | `investigation2_workflow.py` |
| `api/` | FastAPI routes (29 modules) | See `api/README.md` |
| `database/` | SQLAlchemy models, migrations | `models.py`, `migrations/` |
| `infrastructure/` | Modal GPU deployment | `modal/clients/` |
| `mcp_servers/` | MCP tool servers (11 servers) | See `../docs/MCP_SERVERS.md` |
| `models/` | ML model wrappers | Detection, ReID models |
| `services/` | Business logic (43 services) | See `services/README.md` |
| `skills/` | Claude Code skills (5 skills) | See `../docs/SKILLS_SYSTEM.md` |
| `utils/` | Shared utilities | Logging, helpers |

## Quick Start

```bash
cd backend
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000
```

## Key Entry Points

| File | Purpose |
|------|---------|
| `main.py` | FastAPI application entry point |
| `api/app.py` | Route registration and middleware |
| `agents/investigation2_workflow.py` | Main LangGraph investigation workflow |
| `modal_app.py` | Modal GPU deployment configuration |

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## ML Models on Modal

All ML inference runs on Modal serverless GPUs:

| Model | GPU | Embedding Dim |
|-------|-----|---------------|
| WildlifeTools | A100-40GB | 1536 |
| CVWC2019 | T4 | 2048 |
| TransReID | T4 | 768 |
| MegaDescriptor-B | T4 | 1024 |
| TigerReID | T4 | 2048 |
| RAPID | T4 | 2048 |

Deploy models:
```bash
modal deploy backend/modal_app.py
```

## Related Documentation

- `../docs/ARCHITECTURE.md` - System architecture
- `../docs/API.md` - API reference
- `../docs/MCP_SERVERS.md` - MCP server documentation
- `../docs/SKILLS_SYSTEM.md` - Skills documentation
- `../docs/MODAL.md` - Modal GPU infrastructure
