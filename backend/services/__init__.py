"""Business logic services"""

# Lazy imports to avoid circular dependencies
# Import services directly where needed instead of from this module

__all__ = [
    "InvestigationService",
    "TigerService",
    "FacilityService",
    "VerificationService",
    "EmbeddingService",
    "IntegrationService",
    "ServiceFactory",
]


def __getattr__(name):
    """Lazy import services to avoid circular dependencies"""
    if name == "InvestigationService":
        from backend.services.investigation_service import InvestigationService
        return InvestigationService
    elif name == "TigerService":
        from backend.services.tiger_service import TigerService
        return TigerService
    elif name == "FacilityService":
        from backend.services.facility_service import FacilityService
        return FacilityService
    elif name == "VerificationService":
        from backend.services.verification_service import VerificationService
        return VerificationService
    elif name == "EmbeddingService":
        from backend.services.embedding_service import EmbeddingService
        return EmbeddingService
    elif name == "IntegrationService":
        from backend.services.integration_service import IntegrationService
        return IntegrationService
    elif name == "ServiceFactory":
        from backend.services.factory import ServiceFactory
        return ServiceFactory
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
