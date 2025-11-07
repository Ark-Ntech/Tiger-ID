"""Database package - auto-selects PostgreSQL or SQLite based on config"""

import os

# Import all models first
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
    # Enums
    UserRole,
    TigerStatus,
    InvestigationStatus,
    Priority,
    EvidenceSourceType,
    VerificationStatus,
    EntityType,
)

# Check if we should use SQLite (demo or production mode)
# Default to SQLite for production (not PostgreSQL)
USE_SQLITE_DEMO = os.getenv("USE_SQLITE_DEMO", "false").lower() == "true"
USE_POSTGRESQL = os.getenv("USE_POSTGRESQL", "false").lower() == "true"

# Use SQLite by default (production mode), unless explicitly using PostgreSQL
if USE_POSTGRESQL:
    try:
        print("Using PostgreSQL database")
    except UnicodeEncodeError:
        print("Using PostgreSQL database")
    from backend.database.connection import (
        get_db,
        get_db_session,
        engine,
        init_db,
        SessionLocal
    )
else:
    if USE_SQLITE_DEMO:
        try:
            print("Using SQLite demo mode (no PostgreSQL required)")
        except UnicodeEncodeError:
            print("Using SQLite demo mode (no PostgreSQL required)")
    else:
        try:
            print("Using SQLite production mode")
        except UnicodeEncodeError:
            print("Using SQLite production mode")
    from backend.database.sqlite_connection import (
        get_sqlite_db as get_db,
        get_sqlite_db as get_db_session,  # Use generator for FastAPI Depends
        sqlite_engine as engine,
        init_sqlite_db as init_db,
        SQLiteSessionLocal as SessionLocal
    )

__all__ = [
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
    # Enums
    'UserRole',
    'TigerStatus',
    'InvestigationStatus',
    'Priority',
    'EvidenceSourceType',
    'VerificationStatus',
    'EntityType',
    # Functions
    'get_db',
    'get_db_session',
    'engine',
    'init_db',
    'SessionLocal',
]
