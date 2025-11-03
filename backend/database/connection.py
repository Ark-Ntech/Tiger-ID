"""Database connection and session management"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator

from backend.database.models import Base
from backend.config.settings import get_settings

# Get settings once at module level
settings = get_settings()

# Database URL from settings
DATABASE_URL = settings.database.url

# Create engine with optimized connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=settings.debug
)

# Add query optimization hooks (deferred to avoid circular imports during module load)
# This will be called after all modules are loaded
def _setup_optimization_hooks():
    """Setup query optimization hooks - call this after all modules are loaded"""
    try:
        from backend.services.db_optimization import add_query_optimization_hooks
        add_query_optimization_hooks(engine)
    except ImportError:
        # If services aren't loaded yet, skip
        pass

# Don't call at module load - will be called later or can be called explicitly

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    
    # Create vector indexes
    with get_db_session() as session:
        from backend.database.vector_search import create_vector_index
        create_vector_index(session, "tiger_images", "embedding")


def drop_db():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)

