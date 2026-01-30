"""Tiger service module - decomposed from the original monolithic TigerService.

This module provides focused services for tiger identification, registration,
querying, and ensemble strategies.
"""

from backend.services.tiger.identification_service import TigerIdentificationService
from backend.services.tiger.registration_service import TigerRegistrationService
from backend.services.tiger.query_service import TigerQueryService
from backend.services.tiger.ensemble_strategy import (
    EnsembleStrategy,
    StaggeredEnsembleStrategy,
    ParallelEnsembleStrategy,
)

__all__ = [
    "TigerIdentificationService",
    "TigerRegistrationService",
    "TigerQueryService",
    "EnsembleStrategy",
    "StaggeredEnsembleStrategy",
    "ParallelEnsembleStrategy",
]
