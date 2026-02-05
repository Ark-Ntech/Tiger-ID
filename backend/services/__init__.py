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
    "RerankingService",
    "ConfidenceCalibrator",
    "ModelComparisonService",
    "FacilityCrawlerService",
    "ImagePipelineService",
    "DiscoveryScheduler",
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
    elif name == "RerankingService":
        from backend.services.reranking_service import RerankingService
        return RerankingService
    elif name == "ConfidenceCalibrator":
        from backend.services.confidence_calibrator import ConfidenceCalibrator
        return ConfidenceCalibrator
    elif name == "ModelComparisonService":
        from backend.services.model_comparison_service import ModelComparisonService
        return ModelComparisonService
    elif name == "FacilityCrawlerService":
        from backend.services.facility_crawler_service import FacilityCrawlerService
        return FacilityCrawlerService
    elif name == "ImagePipelineService":
        from backend.services.image_pipeline_service import ImagePipelineService
        return ImagePipelineService
    elif name == "DiscoveryScheduler":
        from backend.services.discovery_scheduler import DiscoveryScheduler
        return DiscoveryScheduler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
