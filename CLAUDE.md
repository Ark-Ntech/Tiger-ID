# Tiger ID

Wildlife identification system for tracking captive tigers using AI/ML re-identification. Used for anti-trafficking investigations.

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, SQLite + sqlite-vec
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS, RTK Query
- **ML**: PyTorch, 6-model ReID ensemble, MegaDetector v5
- **Infrastructure**: Modal (GPU inference), LangGraph (workflows)

## Project Structure

```
backend/
├── agents/                 # LangGraph workflows
│   └── investigation2_workflow.py  # Main investigation workflow
├── api/                    # FastAPI routes
├── database/               # SQLAlchemy models
├── mcp_servers/            # MCP tool servers (11 servers)
├── models/                 # ML model wrappers
├── services/               # Business logic
│   └── tiger/              # Tiger identification services
├── skills/                 # Claude skills (5 skills)
└── modal_app.py            # Modal GPU deployment

frontend/src/
├── components/             # React components
│   └── investigations/     # Investigation UI components
├── pages/                  # Page components
├── app/                    # RTK Query API
└── types/                  # TypeScript types
```

## Development

```bash
# Backend
cd backend && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Type checking
cd frontend && npx tsc --noEmit

# Deploy ML models to Modal (uses ark-ntech workspace, tiger-id-models app)
modal deploy backend/modal_app.py
```

## Key Entry Points

| Component | File |
|-----------|------|
| Backend app | `backend/main.py` |
| Investigation workflow | `backend/agents/investigation2_workflow.py` |
| Tiger ID service | `backend/services/tiger/identification_service.py` |
| Frontend app | `frontend/src/App.tsx` |
| Investigation page | `frontend/src/pages/Investigation2.tsx` |
| API client | `frontend/src/app/api.ts` |

## ML Ensemble

6-model weighted ensemble for tiger re-identification:

| Model | Weight | Embedding Dim | Calibration Temp |
|-------|--------|---------------|------------------|
| wildlife_tools | 0.40 | 1536 | 1.0 |
| cvwc2019_reid | 0.30 | 2048 | 0.85 |
| transreid | 0.20 | 768 | 1.1 |
| megadescriptor_b | 0.15 | 1024 | 1.0 |
| tiger_reid | 0.10 | 2048 | 0.9 |
| rapid_reid | 0.05 | 2048 | 0.95 |

Ensemble modes: `staggered` (early exit), `parallel` (voting), `weighted` (recommended), `verified` (highest confidence)

## MCP Servers

11 MCP servers providing tool integration:

### Core Workflow (Investigation 2.0)
- `sequential_thinking_server.py` - Reasoning chain tracking
- `image_analysis_server.py` - Quality assessment (OpenCV)
- `deep_research_server.py` - DuckDuckGo web research
- `report_generation_server.py` - Multi-audience reports

### Integration Servers
- `database_server.py` - Database operations
- `firecrawl_server.py` - Web scraping via Firecrawl
- `tiger_id_server.py` - Tiger identification operations
- `youtube_server.py` - YouTube data extraction
- `meta_server.py` - Meta/Facebook data

### Browser Automation
- `puppeteer_server.py` - Playwright browser automation
- `puppeteer_mcp_standalone.py` - Standalone Puppeteer MCP

## Skills

- `/synthesize-evidence` - Weighted evidence combination
- `/explain-reasoning` - Chain-of-thought documentation
- `/investigate-facility` - Deep facility research
- `/generate-report` - Audience-specific reports
- `/assess-image` - Image quality feedback

## Investigation Workflow Phases

1. `upload_and_parse` - Image validation, EXIF extraction
2. `reverse_image_search` - Web intelligence
3. `tiger_detection` - MegaDetector bounding boxes
4. `stripe_analysis` - 6 parallel ReID models
5. `report_generation` - Claude-synthesized findings
6. `complete` - Results finalization

## Environment Variables

Required in `.env`:
- `ANTHROPIC_API_KEY` - Claude API access
- `DATABASE_URL` - SQLite database path (default: `sqlite:///data/tiger_id.db`)
- `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET` - Modal deployment

See `.env.example` for full list.

## Database Configuration

Tiger ID uses **SQLite with sqlite-vec** for all data storage and vector similarity search. No external database server required.

### Quick Start
```bash
# Set database path (optional, defaults to data/tiger_id.db)
export DATABASE_URL=sqlite:///data/tiger_id.db

# Start backend
cd backend && uvicorn main:app --reload --port 8000
```

### Initialize Database
```bash
# Initialize database schema and sqlite-vec virtual table
python -c "from backend.database import init_db; init_db()"
```

### Docker Deployment
```bash
# Start API and frontend with Docker
docker compose up -d

# View logs
docker compose logs -f api
```

SQLite with sqlite-vec provides fast approximate nearest neighbor search for tiger re-identification, suitable for galleries up to 10k+ tigers.

## Testing

```bash
# Backend tests
cd backend && pytest

# Frontend type check
cd frontend && npx tsc --noEmit
```

## Documentation

Detailed docs in `docs/`:
- `ARCHITECTURE.md` - System architecture
- `ENSEMBLE_STRATEGIES.md` - ML ensemble details
- `MCP_SERVERS.md` - MCP server documentation
- `SKILLS_SYSTEM.md` - Skills documentation
- `MODELS_RESEARCH.md` - Model research and benchmarks

## Discovery Pipeline

Continuous tiger discovery from facility websites:

- **Rate Limiting**: Per-domain tracking with exponential backoff (2s base, 60s max)
- **Image Deduplication**: SHA256 hashing before ML processing
- **Playwright Crawling**: Auto-detection and rendering of JS-heavy sites

Key services:
- `facility_crawler_service.py` - Web crawling with rate limiting
- `image_pipeline_service.py` - Deduplication and ML processing

## Notes

- GPU inference runs on Modal, everything else local
- No AWS dependencies
- Report audiences: law_enforcement, conservation, internal, public
- Image quality assessed via OpenCV (blur, resolution, stripe visibility)

## Installed Skills (Anthropic OpenSkills)

**IMPORTANT**: When working on frontend UI tasks, ALWAYS load the `frontend-design` skill first by running:
```bash
npx openskills read frontend-design
```

Available skills in `.claude/skills/`:

| Skill | When to Use |
|-------|-------------|
| `frontend-design` | Building React components, pages, dashboards, any web UI |
| `webapp-testing` | Testing web apps with Playwright |
| `mcp-builder` | Creating MCP servers |
| `pdf` | Reading, creating, or manipulating PDF files |
| `docx` | Working with Word documents |
| `xlsx` | Working with spreadsheets |
| `pptx` | Creating or editing presentations |
| `canvas-design` | Creating posters, visual art, static designs |
| `skill-creator` | Building new skills |

### Code Quality Skills (Tiger ID Custom)

| Skill | When to Use |
|-------|-------------|
| `typescript-validator` | After creating/modifying React components - runs `tsc --noEmit` |
| `component-integration-tester` | Verify new components integrate with parent pages |
| `index-file-generator` | Create/update barrel exports (index.ts) after adding components |
| `design-token-auditor` | Scan for hardcoded colors that should use tactical/tiger-orange tokens |
| `import-path-fixer` | Update import paths after moving/renaming files |
| `frontend-verification` | Full verification: render, console errors, responsive, tests |

Load any skill: `npx openskills read <skill-name>`

See `AGENTS.md` for full skill descriptions and trigger conditions.
