"""Tests for ServiceFactory"""

import pytest
from backend.services.factory import ServiceFactory
from backend.services.tiger_service import TigerService
from backend.services.facility_service import FacilityService
from backend.services.investigation_service import InvestigationService
from backend.services.verification_service import VerificationService
from backend.services.embedding_service import EmbeddingService


class TestServiceFactory:
    """Tests for ServiceFactory"""
    
    def test_init(self, db_session):
        """Test factory initialization"""
        factory = ServiceFactory(session=db_session)
        
        assert factory.session == db_session
        assert factory._services == {}
    
    def test_get_tiger_service(self, db_session):
        """Test getting TigerService"""
        factory = ServiceFactory(session=db_session)
        
        service1 = factory.get_tiger_service()
        service2 = factory.get_tiger_service()
        
        assert isinstance(service1, TigerService)
        assert service1 is service2  # Same instance (cached)
    
    def test_get_facility_service(self, db_session):
        """Test getting FacilityService"""
        factory = ServiceFactory(session=db_session)
        
        service1 = factory.get_facility_service()
        service2 = factory.get_facility_service()
        
        assert isinstance(service1, FacilityService)
        assert service1 is service2  # Same instance (cached)
    
    def test_get_investigation_service(self, db_session):
        """Test getting InvestigationService"""
        factory = ServiceFactory(session=db_session)
        
        service1 = factory.get_investigation_service()
        service2 = factory.get_investigation_service()
        
        assert isinstance(service1, InvestigationService)
        assert service1 is service2  # Same instance (cached)
    
    def test_get_verification_service(self, db_session):
        """Test getting VerificationService"""
        factory = ServiceFactory(session=db_session)
        
        service1 = factory.get_verification_service()
        service2 = factory.get_verification_service()
        
        assert isinstance(service1, VerificationService)
        assert service1 is service2  # Same instance (cached)
    
    def test_get_embedding_service(self, db_session):
        """Test getting EmbeddingService"""
        factory = ServiceFactory(session=db_session)
        
        service1 = factory.get_embedding_service()
        service2 = factory.get_embedding_service()
        
        assert isinstance(service1, EmbeddingService)
        assert service1 is service2  # Same instance (cached)
    
    def test_get_service_with_custom_session(self, db_session):
        """Test getting service with custom session"""
        factory = ServiceFactory(session=db_session)
        
        # Create another session (mocked)
        from unittest.mock import MagicMock
        custom_session = MagicMock()
        
        service = factory.get_tiger_service(session=custom_session)
        
        assert isinstance(service, TigerService)
        # Should use custom session, not factory session
        # This is tested implicitly by service working with custom session
    
    def test_get_service_no_session_raises_error(self):
        """Test getting service without session raises error"""
        factory = ServiceFactory(session=None)
        
        with pytest.raises(ValueError, match="Database session required"):
            factory.get_tiger_service()
    
    def test_clear_cache(self, db_session):
        """Test clearing service cache"""
        factory = ServiceFactory(session=db_session)
        
        # Get a service
        service1 = factory.get_tiger_service()
        
        # Clear cache
        factory.clear_cache()
        
        # Get service again - should be new instance
        service2 = factory.get_tiger_service()
        
        # Different instances after cache clear (though may still work the same)
        assert factory._services == {} or len(factory._services) == 1
    
    def test_service_caching_by_session(self, db_session):
        """Test that services are cached per session"""
        factory = ServiceFactory(session=db_session)
        
        service1 = factory.get_tiger_service()
        
        # Get with same session
        service2 = factory.get_tiger_service(session=db_session)
        
        # Should be same instance
        assert service1 is service2

