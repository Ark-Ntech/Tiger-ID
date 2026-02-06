"""FastAPI application setup"""

from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.api.routes import router
from backend.api.auth_routes import router as auth_router
from backend.api.error_handlers import (
    APIError,
    api_error_handler,
    generic_exception_handler,
)
from backend.api.investigation2_routes import router as investigation2_router
from backend.api.mcp_tools_routes import router as mcp_tools_router
from backend.api.sse_routes import router as sse_router
from backend.api.event_routes import router as event_router
from backend.api.notification_routes import router as notification_router
from backend.api.search_routes import router as search_router
from backend.api.export_routes import router as export_router
from backend.api.analytics_routes import router as analytics_router
from backend.api.audit_routes import router as audit_router
from backend.api.template_routes import router as template_router
from backend.api.saved_search_routes import router as saved_search_router
from backend.api.annotation_routes import router as annotation_router
from backend.api.websocket_routes import router as websocket_router
from backend.api.verification_routes import router as verification_router
from backend.api.tiger_routes import router as tiger_router
from backend.api.model_testing_routes import router as model_testing_router
from backend.api.approval_routes import router as approval_router
from backend.api.finetuning_routes import router as finetuning_router
from backend.api.model_performance_routes import router as model_performance_router
from backend.api.model_version_routes import router as model_version_router
from backend.api.discovery_routes import router as discovery_router
from backend.api.middleware import RateLimitMiddleware
from backend.middleware.audit_middleware import AuditMiddleware
from backend.middleware.csrf_middleware import CSRFMiddleware
from backend.utils.sentry_config import initialize_sentry
from backend.config.settings import get_settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events (startup/shutdown)"""
    # Startup
    logger.info("Starting Tiger ID API...")
    settings = get_settings()
    
    # Health checks
    try:
        # Check database connectivity
        from backend.database import engine, init_db
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")

        # Initialize database schema (creates missing tables including audit_logs)
        init_db()
        logger.info("Database schema initialized")

        # Check if database needs data loading
        from backend.database import get_db_session
        from backend.database.models import Facility, Tiger
        with get_db_session() as db:
            facility_count = db.query(Facility).count()
            tiger_count = db.query(Tiger).count()
            
            if facility_count == 0 or tiger_count == 0:
                logger.info("Database is empty, loading data from data/models...")
                # Load data in background (non-blocking)
                import threading
                def load_data():
                    try:
                        from scripts.init_db import load_data_from_models
                        load_data_from_models()
                        logger.info("Data loading completed")
                    except Exception as e:
                        logger.warning(f"Data loading failed: {e}")
                
                thread = threading.Thread(target=load_data, daemon=True)
                thread.start()
            else:
                logger.info(f"Database has {facility_count} facilities and {tiger_count} tigers")
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")
        logger.warning("Continuing startup - database may not be ready yet")
    
    # Initialize models (non-blocking, runs in background)
    try:
        import subprocess
        import sys
        import asyncio
        from pathlib import Path
        
        # Preload models if configured
        settings = get_settings()
        preload_models = getattr(settings.models, 'preload_on_startup', False) if hasattr(settings, 'models') else False
        
        if preload_models:
            logger.info("Preloading models on startup...")
            # Note: Model preloading will happen in background task
            # Cannot use asyncio.create_task here in sync context
            # Models will be loaded on first use
        else:
            # Run model initialization script
            script_path = Path(__file__).parent.parent.parent / "scripts" / "init_models.py"
            if script_path.exists():
                logger.info("Initializing models...")
                # Run in background, don't block startup
                try:
                    result = subprocess.run(
                        [sys.executable, str(script_path)],
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minute timeout
                    )
                    if result.returncode == 0:
                        logger.info("Model initialization completed")
                    else:
                        logger.warning(f"Model initialization had warnings: {result.stderr}")
                except subprocess.TimeoutExpired:
                    logger.warning("Model initialization timed out - continuing anyway")
                except Exception as e:
                    logger.warning(f"Model initialization error: {e}")
            else:
                logger.warning(f"Model initialization script not found at {script_path}")
    except Exception as e:
        logger.warning(f"Error during model initialization: {e}")
    
    # Initialize Sentry if configured
    if settings.sentry.dsn:
        initialize_sentry()

    # Start discovery scheduler if enabled
    discovery_scheduler = None
    try:
        if settings.discovery.enabled:
            from backend.services.discovery_scheduler import get_discovery_scheduler
            discovery_scheduler = get_discovery_scheduler()
            if discovery_scheduler.start():
                logger.info("Continuous tiger discovery scheduler started (FREE tools only)")
            else:
                logger.warning("Discovery scheduler failed to start")
        else:
            logger.info("Discovery scheduler disabled (set DISCOVERY_ENABLED=true to enable)")
    except Exception as e:
        logger.warning(f"Failed to start discovery scheduler: {e}")

    logger.info("API startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Tiger ID API...")

    # Stop discovery scheduler
    if discovery_scheduler:
        discovery_scheduler.stop()
        logger.info("Discovery scheduler stopped")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="Tiger Trafficking Investigation System API",
        version="1.0.0",
        description="""
        REST API for tiger trafficking investigations.
        
        ## Features
        
        * **Multi-Agent AI Orchestration**: Claude AI orchestrator with specialized agents
        * **Tiger Stripe Re-Identification**: Deep learning models for identifying individual tigers
        * **Investigation Workflows**: End-to-end investigation workflows with evidence compilation
        * **Multi-User Collaboration**: Role-based access control and collaborative workspaces
        * **External API Integration**: USDA, CITES, and USFWS data synchronization
        
        ## Authentication
        
        Most endpoints require authentication using JWT tokens. 
        Get your token by logging in at `/api/auth/login`.
        
        ## Rate Limiting
        
        API requests are limited to 60 requests per minute per IP address.
        """,
        contact={
            "name": "Tiger ID",
            "url": "https://github.com/your-org/tiger-investigation",
        },
        license_info={
            "name": "MIT",
        },
        lifespan=lifespan,
    )
    
    # CORS middleware - use environment-based configuration
    import os
    cors_origins = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://localhost:5179,http://localhost:8001"
    ).split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Rate limiting middleware (300 requests per minute per IP)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=300,
        per_ip=True
    )
    
    # CSRF protection middleware (only if enabled)
    settings = get_settings()
    if settings.csrf.enabled:
        app.add_middleware(
            CSRFMiddleware,
            secret_key=settings.csrf.secret_key,
            token_lifetime=settings.csrf.token_lifetime
        )
    
    # Audit logging middleware
    app.add_middleware(AuditMiddleware)

    # Register exception handlers for standardized error responses
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Include routers
    app.include_router(auth_router)  # Auth routes (no prefix, uses /api/auth)
    app.include_router(tiger_router, prefix="/api/v1")  # Tiger identification routes
    app.include_router(mcp_tools_router)  # MCP tools routes
    app.include_router(investigation2_router, prefix="/api/v1/investigations2", tags=["investigations2"])  # Investigation 2.0 routes (Gemini-powered)
    app.include_router(router, prefix="/api/v1", tags=["api"])
    app.include_router(sse_router)  # SSE routes for real-time updates
    app.include_router(event_router)  # Event history routes
    app.include_router(notification_router)  # Notification routes
    app.include_router(search_router)  # Global search routes
    app.include_router(export_router)  # Export routes
    app.include_router(analytics_router)  # Analytics routes
    app.include_router(audit_router)  # Audit log routes
    app.include_router(template_router)  # Template routes
    app.include_router(saved_search_router)  # Saved search routes
    app.include_router(annotation_router)  # Annotation routes
    app.include_router(websocket_router)  # WebSocket routes for real-time communication
    app.include_router(verification_router)  # Verification task routes
    app.include_router(model_testing_router, prefix="/api/v1")  # Model testing routes
    app.include_router(approval_router)  # Approval routes
    app.include_router(finetuning_router)  # Fine-tuning routes
    app.include_router(model_performance_router)  # Model performance monitoring routes
    app.include_router(model_version_router)  # Model version management routes
    app.include_router(discovery_router)  # Continuous tiger discovery routes (FREE tools)

    # Modal routes for model status and management
    try:
        from backend.api.modal_routes import router as modal_router
        app.include_router(modal_router, prefix="/api/v1")  # Modal integration routes
        logger.info("Modal routes registered")
    except ImportError as e:
        logger.warning(f"Modal routes not available: {e}")
    
    # Include integration router if available (lazy load to avoid memory issues)
    try:
        from backend.api import get_integration_router
        integration_router = get_integration_router()
        if integration_router:
            app.include_router(integration_router, tags=["integrations"])
            logger.info("Integration endpoints registered")
    except Exception as e:
        logger.warning(f"Integration endpoints not available: {e}")
    
    # Mount static files for images
    # Serve images from data/models/atrw/images and other dataset directories
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    
    # Mount static directories for images
    if (data_dir / "models" / "atrw" / "images").exists():
        app.mount("/static/images/atrw", StaticFiles(directory=str(data_dir / "models" / "atrw" / "images")), name="atrw_images")
    
    # Also mount a general images endpoint that can serve from any path
    @app.get("/static/images/{image_path:path}")
    async def serve_image(image_path: str):
        """Serve images from dataset directories"""
        from fastapi.responses import FileResponse
        from pathlib import Path
        
        # Try different dataset paths
        project_root = Path(__file__).parent.parent.parent
        possible_paths = [
            project_root / "data" / "models" / "atrw" / "images" / image_path,
            project_root / "data" / "models" / image_path,
            project_root / "data" / "datasets" / image_path,
            Path(image_path)  # Absolute path
        ]
        
        for img_path in possible_paths:
            if img_path.exists() and img_path.is_file():
                return FileResponse(str(img_path))
        
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for Docker/Kubernetes"""
        try:
            # Quick database check
            from backend.database import engine
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_status = "healthy"
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            db_status = "unhealthy"
        
        # Check model availability
        model_status = "unknown"
        try:
            from backend.services.tiger_service import TigerService
            from backend.database import get_db_session
            with get_db_session() as session:
                tiger_service = TigerService(session)
                available_models = tiger_service.get_available_models()
                if available_models:
                    model_status = "available"
                else:
                    model_status = "no_models"
        except Exception as e:
            logger.warning(f"Error checking model status: {e}")
            model_status = "error"
        
        # Check GPU availability
        gpu_status = "unavailable"
        gpu_name = None
        try:
            import torch
            if torch.cuda.is_available():
                gpu_status = "available"
                gpu_name = torch.cuda.get_device_name(0)
        except ImportError:
            logger.debug("PyTorch not installed, GPU check skipped")
        except Exception as e:
            logger.warning(f"GPU availability check failed: {e}")
        
        overall_status = "healthy" if db_status == "healthy" else "degraded"
        
        return JSONResponse({
            "status": overall_status,
            "database": db_status,
            "models": model_status,
            "gpu": gpu_status,
            "gpu_name": gpu_name,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    return app


# Create app instance for uvicorn
app = create_app()

