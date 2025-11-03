# Development Guide

## Setup

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Database Setup

```bash
# Start database and Redis
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Initialize database
python scripts/init_db.py
```

### 3. Running Locally

```bash
# Run API server
uvicorn backend.api.app:create_app --reload --port 8000

# Run frontend (from frontend/ directory)
cd frontend
npm install
npm run dev

# Run Celery worker
celery -A backend.jobs.celery_app worker --loglevel=info
```

## Development Workflow

### Code Structure

```
backend/
  agents/          # AI agents (Research, Analysis, Validation, Reporting, Orchestrator)
  api/            # FastAPI endpoints
  database/       # Database models, migrations, connection
  jobs/           # Celery background jobs
  mcp_servers/    # MCP server implementations
  models/         # ML models (detection, re-identification)
  services/       # Business logic services
  utils/          # Utility functions

frontend/         # React/TypeScript frontend
  src/
    components/   # Reusable UI components
    pages/         # Page components
    features/     # Feature modules
    utils/        # Frontend utilities

scripts/         # Utility scripts
tests/           # Test suite
config/          # Configuration files
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run with coverage
pytest --cov=backend tests/
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy backend/
```

## Adding New Features

### 1. Database Changes

```bash
# Create migration
alembic revision --autogenerate -m "add new table"

# Review generated migration
# Edit if needed

# Apply migration
alembic upgrade head
```

### 2. Adding New Agent

1. Create agent in `backend/agents/`
2. Add to orchestrator in `backend/agents/orchestrator.py`
3. Update agent prompts in `config/agent_prompts.yaml`
4. Add tests in `tests/test_agents.py`

### 3. Adding New MCP Server

1. Create server in `backend/mcp_servers/`
2. Extend `MCPServerBase`
3. Register tools
4. Add to orchestrator
5. Add tests

### 4. Adding New Service

1. Create service in `backend/services/`
2. Implement CRUD operations
3. Add to service exports
4. Add tests

## Debugging

### Debugging Agents

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use IPython debugger
from IPython import embed; embed()
```

### Database Debugging

```bash
# Connect to database
docker-compose exec postgres psql -U tiger_user -d tiger_investigation

# View tables
\dt

# Query data
SELECT * FROM tigers LIMIT 10;
```

### Model Debugging

```python
# Test model loading
from backend.models.tiger_detection import TigerDetectionModel
import asyncio

model = TigerDetectionModel()
asyncio.run(model.load_model())

# Test inference
result = asyncio.run(model.detect(image_bytes))
```

## Common Issues

### Import Errors

- Ensure virtual environment is activated
- Check PYTHONPATH includes project root
- Verify all dependencies installed

### Database Connection

- Verify PostgreSQL is running: `docker-compose ps postgres`
- Check connection string in `.env`
- Ensure migrations are applied

### Model Loading

- Check model files exist in `data/models/`
- Verify sufficient disk space
- Check model file permissions

## Git Workflow

1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and commit
3. Run tests: `pytest`
4. Push branch: `git push origin feature/new-feature`
5. Create pull request

## Documentation

- Update `README.md` for user-facing changes
- Update `docs/ARCHITECTURE.md` for architectural changes
- Update `docs/API.md` if API endpoints change
- Add docstrings to new functions/classes
- Update completion status in `docs/COMPLETION_STATUS.md` for new features

