"""Database package - SQLite with sqlite-vec for vector search

Tiger ID uses SQLite as its database with sqlite-vec extension for
fast approximate nearest neighbor search on tiger embeddings.
"""

import os
import logging
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Import all models
from backend.database.models import (
    Base,
    User,
    Tiger,
    TigerImage,
    Facility,
    Investigation,
    InvestigationStep,
    Evidence,
    InvestigationTemplate,
    SavedSearch,
    InvestigationComment,
    InvestigationAnnotation,
    CrawlHistory,
    UserSession,
    PasswordResetToken,
    Notification,
    VerificationQueue,
    EvidenceLink,
    ModelVersion,
    ModelInference,
    BackgroundJob,
    DataExport,
    SystemMetric,
    Feedback,
    # Enums
    UserRole,
    TigerStatus,
    InvestigationStatus,
    Priority,
    EvidenceSourceType,
    VerificationStatus,
    EntityType,
    SideView,
    ModelType,
    # JSON Types
    JSONEncodedValue,
    JSONList,
    JSONDict,
)

# Import audit models so they're registered with Base
from backend.database.audit_models import AuditLog


def _get_database_url():
    """Get SQLite database URL from environment or default."""
    url = os.getenv("DATABASE_URL", "sqlite:///data/tiger_id.db")

    # Ensure it's a SQLite URL
    if not url.startswith("sqlite://"):
        logger.warning(f"Non-SQLite URL provided, using default SQLite database")
        url = "sqlite:///data/tiger_id.db"

    return url


def _create_engine(database_url: str):
    """Create SQLite engine with sqlite-vec extension loaded."""
    # Extract path from URL for directory creation
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
        db_dir = Path(db_path).parent
        if db_dir and not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")

    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        echo=os.getenv("DB_ECHO", "false").lower() == "true"
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Configure SQLite connection with optimizations and sqlite-vec."""
        cursor = dbapi_conn.cursor()

        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")

        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")

        # Load sqlite-vec extension
        try:
            dbapi_conn.enable_load_extension(True)
            import sqlite_vec
            sqlite_vec.load(dbapi_conn)
            dbapi_conn.enable_load_extension(False)
            logger.debug("sqlite-vec extension loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load sqlite-vec: {e}")

        cursor.close()

    return engine


# Initialize database
_database_url = _get_database_url()
engine = _create_engine(_database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger.info(f"Database initialized: SQLite with sqlite-vec")


def get_db():
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Get a database session (for non-FastAPI use)."""
    return SessionLocal()


def init_db():
    """Initialize database schema and sqlite-vec virtual table."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Create sqlite-vec virtual table for embeddings
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_embeddings USING vec0(
                    image_id TEXT PRIMARY KEY,
                    embedding FLOAT[2048]
                )
            """))
            conn.commit()
            logger.info("vec_embeddings virtual table created")
        except Exception as e:
            logger.warning(f"Failed to create vec_embeddings table: {e}")

    return True


__all__ = [
    # Models
    'Base',
    'User',
    'Tiger',
    'TigerImage',
    'Facility',
    'Investigation',
    'InvestigationStep',
    'Evidence',
    'InvestigationTemplate',
    'SavedSearch',
    'InvestigationComment',
    'InvestigationAnnotation',
    'CrawlHistory',
    'UserSession',
    'PasswordResetToken',
    'Notification',
    'VerificationQueue',
    'EvidenceLink',
    'ModelVersion',
    'ModelInference',
    'BackgroundJob',
    'DataExport',
    'SystemMetric',
    'Feedback',
    'AuditLog',
    # Enums
    'UserRole',
    'TigerStatus',
    'InvestigationStatus',
    'Priority',
    'EvidenceSourceType',
    'VerificationStatus',
    'EntityType',
    'SideView',
    'ModelType',
    # JSON Types
    'JSONEncodedValue',
    'JSONList',
    'JSONDict',
    # Database functions
    'get_db',
    'get_db_session',
    'engine',
    'init_db',
    'SessionLocal',
]
