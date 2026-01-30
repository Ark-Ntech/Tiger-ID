"""FastAPI dependency injection for Tiger ID.

This module provides dependency injection functions for services and repositories,
enabling cleaner route definitions and better testability.
"""

from typing import Generator, Optional
from sqlalchemy.orm import Session
from fastapi import Depends

from backend.database import get_db_session
from backend.repositories import (
    TigerRepository,
    InvestigationRepository,
    FacilityRepository,
    UserRepository,
)
from backend.services.tiger import (
    TigerIdentificationService,
    TigerRegistrationService,
    TigerQueryService,
)
from backend.services.modal_client import ModalClient, get_modal_client
from backend.models.detection import TigerDetectionModel


# ==================== Database Session ====================

def get_db() -> Generator[Session, None, None]:
    """Get database session.

    Yields:
        SQLAlchemy database session
    """
    db = next(get_db_session())
    try:
        yield db
    finally:
        db.close()


# ==================== Repositories ====================

def get_tiger_repository(db: Session = Depends(get_db)) -> TigerRepository:
    """Get tiger repository instance.

    Args:
        db: Database session

    Returns:
        TigerRepository instance
    """
    return TigerRepository(db)


def get_investigation_repository(
    db: Session = Depends(get_db)
) -> InvestigationRepository:
    """Get investigation repository instance.

    Args:
        db: Database session

    Returns:
        InvestigationRepository instance
    """
    return InvestigationRepository(db)


def get_facility_repository(
    db: Session = Depends(get_db)
) -> FacilityRepository:
    """Get facility repository instance.

    Args:
        db: Database session

    Returns:
        FacilityRepository instance
    """
    return FacilityRepository(db)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Get user repository instance.

    Args:
        db: Database session

    Returns:
        UserRepository instance
    """
    return UserRepository(db)


# ==================== Infrastructure ====================

def get_modal() -> ModalClient:
    """Get Modal client instance.

    Returns:
        ModalClient singleton instance
    """
    return get_modal_client()


def get_detection_model() -> TigerDetectionModel:
    """Get tiger detection model instance.

    Returns:
        TigerDetectionModel instance
    """
    return TigerDetectionModel()


# ==================== Tiger Services ====================

def get_tiger_identification_service(
    db: Session = Depends(get_db),
    detection_model: TigerDetectionModel = Depends(get_detection_model)
) -> TigerIdentificationService:
    """Get tiger identification service.

    Args:
        db: Database session
        detection_model: Detection model instance

    Returns:
        TigerIdentificationService instance
    """
    return TigerIdentificationService(db, detection_model)


def get_tiger_registration_service(
    db: Session = Depends(get_db),
    tiger_repo: TigerRepository = Depends(get_tiger_repository),
    detection_model: TigerDetectionModel = Depends(get_detection_model)
) -> TigerRegistrationService:
    """Get tiger registration service.

    Args:
        db: Database session
        tiger_repo: Tiger repository
        detection_model: Detection model instance

    Returns:
        TigerRegistrationService instance
    """
    return TigerRegistrationService(db, tiger_repo, detection_model)


def get_tiger_query_service(
    db: Session = Depends(get_db),
    tiger_repo: TigerRepository = Depends(get_tiger_repository)
) -> TigerQueryService:
    """Get tiger query service.

    Args:
        db: Database session
        tiger_repo: Tiger repository

    Returns:
        TigerQueryService instance
    """
    return TigerQueryService(db, tiger_repo)


# ==================== Compatibility Layer ====================

# These functions provide backwards compatibility with the original TigerService

def get_tiger_service(db: Session = Depends(get_db)):
    """Get legacy TigerService for backwards compatibility.

    This function returns the original TigerService for routes that haven't
    been migrated to the new decomposed services.

    Args:
        db: Database session

    Returns:
        TigerService instance
    """
    from backend.services.tiger_service import TigerService
    return TigerService(db)


def get_investigation_service(db: Session = Depends(get_db)):
    """Get investigation service.

    Args:
        db: Database session

    Returns:
        InvestigationService instance
    """
    from backend.services.investigation_service import InvestigationService
    return InvestigationService(db)


def get_facility_service(db: Session = Depends(get_db)):
    """Get facility service.

    Args:
        db: Database session

    Returns:
        FacilityService instance
    """
    from backend.services.facility_service import FacilityService
    return FacilityService(db)


# ==================== Auth Dependencies ====================

async def get_current_user(
    # This would typically extract user from JWT token
    # Placeholder for auth integration
):
    """Get current authenticated user.

    This is a placeholder that should be integrated with the actual
    auth system.

    Returns:
        Current user or raises HTTPException
    """
    # TODO: Implement actual auth
    pass


async def get_current_active_user(
    # current_user = Depends(get_current_user)
):
    """Get current active user.

    Returns:
        Current active user or raises HTTPException
    """
    # TODO: Implement actual auth
    pass


def require_role(*roles):
    """Decorator/dependency to require specific roles.

    Args:
        *roles: Required role names

    Returns:
        Dependency function
    """
    async def role_checker():
        # TODO: Implement role checking
        pass
    return role_checker
