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

# Check if we should use SQLite demo mode
USE_SQLITE_DEMO = os.getenv("USE_SQLITE_DEMO", "false").lower() == "true"

if USE_SQLITE_DEMO:
    print("🗄️  Using SQLite demo mode (no PostgreSQL required)")
    from backend.database.sqlite_connection import (
        get_sqlite_db as get_db,
        get_sqlite_db as get_db_session,  # Use generator for FastAPI Depends
        sqlite_engine as engine,
        init_sqlite_db as init_db,
        SQLiteSessionLocal as SessionLocal
    )
else:
    from backend.database.connection import (
        get_db,
        get_db_session,
        engine,
        init_db,
        SessionLocal
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
