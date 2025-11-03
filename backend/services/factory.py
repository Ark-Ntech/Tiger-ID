"""Service factory for managing service instances"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.services.tiger_service import TigerService
from backend.services.facility_service import FacilityService
from backend.services.investigation_service import InvestigationService
from backend.services.verification_service import VerificationService
from backend.services.embedding_service import EmbeddingService
from backend.services.integration_service import IntegrationService
from backend.services.external_apis.factory import get_api_clients


class ServiceFactory:
    """Factory for creating and managing service instances"""
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize service factory
        
        Args:
            session: Database session (optional)
        """
        self.session = session
        self._services: Dict[str, Any] = {}
    
    def get_tiger_service(self, session: Optional[Session] = None) -> TigerService:
        """Get or create TigerService"""
        session = session or self.session
        if not session:
            raise ValueError("Database session required")
        
        cache_key = f"tiger_service_{id(session)}"
        if cache_key not in self._services:
            self._services[cache_key] = TigerService(session)
        return self._services[cache_key]
    
    def get_facility_service(self, session: Optional[Session] = None) -> FacilityService:
        """Get or create FacilityService"""
        session = session or self.session
        if not session:
            raise ValueError("Database session required")
        
        cache_key = f"facility_service_{id(session)}"
        if cache_key not in self._services:
            self._services[cache_key] = FacilityService(session)
        return self._services[cache_key]
    
    def get_investigation_service(self, session: Optional[Session] = None) -> InvestigationService:
        """Get or create InvestigationService"""
        session = session or self.session
        if not session:
            raise ValueError("Database session required")
        
        cache_key = f"investigation_service_{id(session)}"
        if cache_key not in self._services:
            self._services[cache_key] = InvestigationService(session)
        return self._services[cache_key]
    
    def get_verification_service(self, session: Optional[Session] = None) -> VerificationService:
        """Get or create VerificationService"""
        session = session or self.session
        if not session:
            raise ValueError("Database session required")
        
        cache_key = f"verification_service_{id(session)}"
        if cache_key not in self._services:
            self._services[cache_key] = VerificationService(session)
        return self._services[cache_key]
    
    def get_embedding_service(self, session: Optional[Session] = None) -> EmbeddingService:
        """Get or create EmbeddingService"""
        session = session or self.session
        if not session:
            raise ValueError("Database session required")
        
        cache_key = f"embedding_service_{id(session)}"
        if cache_key not in self._services:
            self._services[cache_key] = EmbeddingService(session)
        return self._services[cache_key]
    
    def get_integration_service(self, session: Optional[Session] = None) -> IntegrationService:
        """Get or create IntegrationService"""
        session = session or self.session
        if not session:
            raise ValueError("Database session required")
        
        cache_key = f"integration_service_{id(session)}"
        if cache_key not in self._services:
            # Get API clients from factory
            clients = get_api_clients()
            
            self._services[cache_key] = IntegrationService(
                session=session,
                usda_client=clients.get("usda"),
                cites_client=clients.get("cites"),
                usfws_client=clients.get("usfws")
            )
        return self._services[cache_key]
    
    def clear_cache(self):
        """Clear service cache"""
        self._services.clear()

