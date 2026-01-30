"""Repository layer for Tiger ID data access.

This module provides a clean abstraction layer between the service layer
and the database, following the Repository Pattern.
"""

from backend.repositories.base import BaseRepository
from backend.repositories.tiger_repository import TigerRepository
from backend.repositories.investigation_repository import InvestigationRepository
from backend.repositories.facility_repository import FacilityRepository
from backend.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "TigerRepository",
    "InvestigationRepository",
    "FacilityRepository",
    "UserRepository",
]
