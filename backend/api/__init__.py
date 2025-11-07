"""REST API endpoints"""

# Lazy import for integration endpoints to avoid memory issues
integration_router = None

def get_integration_router():
    """Lazy load integration router"""
    global integration_router
    if integration_router is None:
        try:
            from backend.api.integration_endpoints import router
            integration_router = router
        except ImportError as e:
            import logging
            logging.warning(f"Integration endpoints not available: {e}")
            integration_router = False
    return integration_router if integration_router is not False else None

# Import app creation
from backend.api.app import create_app, app

__all__ = [
    "get_integration_router",
    "create_app",
    "app",
]
