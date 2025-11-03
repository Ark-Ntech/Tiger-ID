"""Database helper utilities"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session

from backend.database import SessionLocal, get_db_session


@contextmanager
def with_db_session() -> Generator[Session, None, None]:
    """
    Database session context manager for Celery tasks and other sync contexts
    
    Usage:
        with with_db_session() as session:
            # Use session
            pass
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

