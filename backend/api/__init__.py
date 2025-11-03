"""REST API endpoints"""

# Import integration endpoints
try:
    from backend.api.integration_endpoints import router as integration_router
except ImportError:
    integration_router = None

# Import app creation
from backend.api.app import create_app, app

__all__ = [
    "integration_router",
    "create_app",
    "app",
]
