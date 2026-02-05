# API Routes

FastAPI route modules for Tiger ID.

## Route Organization

### Core API

| Module | Prefix | Description |
|--------|--------|-------------|
| `routes.py` | `/` | Base routes, health check |
| `auth_routes.py` | `/auth` | Authentication, JWT tokens |
| `tiger_routes.py` | `/tigers` | Tiger CRUD, identification |
| `facility_routes.py` | `/facilities` | Facility management |

### Investigation

| Module | Prefix | Description |
|--------|--------|-------------|
| `investigation2_routes.py` | `/investigations` | Investigation 2.0 workflow |
| `evidence_routes.py` | `/evidence` | Evidence management |
| `relationship_routes.py` | `/relationships` | Entity relationships |

### Model & ML

| Module | Prefix | Description |
|--------|--------|-------------|
| `modal_routes.py` | `/modal` | Modal deployment status |
| `model_testing_routes.py` | `/models/testing` | Model testing endpoints |
| `finetuning_routes.py` | `/finetuning` | Fine-tuning interface |
| `model_performance_routes.py` | `/models/performance` | Performance metrics |
| `model_version_routes.py` | `/models/versions` | Model versioning |

### Integration

| Module | Prefix | Description |
|--------|--------|-------------|
| `integration_endpoints.py` | `/integrations` | External API integrations |
| `mcp_tools_routes.py` | `/mcp` | MCP server access |
| `discovery_routes.py` | `/discovery` | Tiger discovery pipeline |

### Data & Export

| Module | Prefix | Description |
|--------|--------|-------------|
| `search_routes.py` | `/search` | Global search |
| `analytics_routes.py` | `/analytics` | Analytics endpoints |
| `export_routes.py` | `/export` | Data export (PDF, CSV, etc.) |
| `import_routes.py` | `/import` | Data import |

### Admin & System

| Module | Prefix | Description |
|--------|--------|-------------|
| `audit_routes.py` | `/audit` | Audit logs (admin) |
| `notification_routes.py` | `/notifications` | User notifications |
| `verification_routes.py` | `/verification` | Verification queue |
| `approval_routes.py` | `/approvals` | Approval workflows |

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Authentication

Most endpoints require JWT authentication:

```bash
# Get token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Use token
curl http://localhost:8000/tigers \
  -H "Authorization: Bearer <token>"
```

## Related Documentation

- `../../docs/API.md` - Complete API reference
- `../../docs/API_INTEGRATION.md` - Integration guide
