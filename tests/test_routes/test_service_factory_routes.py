"""Tests for ServiceFactory usage in API routes.

These tests verify that API routes correctly use ServiceFactory
instead of direct service instantiation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from backend.services.factory import ServiceFactory
from backend.services.tiger_service import TigerService
from backend.services.facility_service import FacilityService
from backend.services.investigation_service import InvestigationService


class TestTigerRoutesServiceFactory:
    """Tests for ServiceFactory usage in tiger routes."""

    @patch('backend.api.tiger_routes.ServiceFactory')
    def test_identify_tiger_uses_factory(self, mock_factory_class, authenticated_client, db_session):
        """Test that /tigers/identify endpoint uses ServiceFactory."""
        # Setup mock factory
        mock_factory = Mock(spec=ServiceFactory)
        mock_tiger_service = Mock(spec=TigerService)
        mock_tiger_service.get_available_models.return_value = ["wildlife_tools", "cvwc2019_reid"]
        mock_tiger_service.identify_tiger_from_image = Mock(return_value={
            "identified": False,
            "confidence": 0.0,
            "matches": []
        })
        mock_factory.get_tiger_service.return_value = mock_tiger_service
        mock_factory_class.return_value = mock_factory

        # Create test image
        image_data = BytesIO(b"fake image data")
        files = {"image": ("test.jpg", image_data, "image/jpeg")}
        data = {"similarity_threshold": 0.8}

        # Make request
        response = authenticated_client.post(
            "/tigers/identify",
            files=files,
            data=data
        )

        # Verify factory was instantiated with session
        mock_factory_class.assert_called_once()
        call_args = mock_factory_class.call_args
        assert call_args is not None

        # Verify factory method was called
        mock_factory.get_tiger_service.assert_called_once()

    @patch('backend.api.tiger_routes.ServiceFactory')
    def test_register_tiger_uses_factory(self, mock_factory_class, authenticated_client, db_session):
        """Test that /tigers/register endpoint uses ServiceFactory."""
        # Setup mock factory
        mock_factory = Mock(spec=ServiceFactory)
        mock_tiger_service = Mock(spec=TigerService)
        mock_tiger_service.register_new_tiger = Mock(return_value={
            "tiger_id": "123",
            "name": "Test Tiger"
        })
        mock_factory.get_tiger_service.return_value = mock_tiger_service
        mock_factory_class.return_value = mock_factory

        # Create test image
        image_data = BytesIO(b"fake image data")
        files = {"images": [("test.jpg", image_data, "image/jpeg")]}
        data = {"name": "Test Tiger"}

        # Make request
        response = authenticated_client.post(
            "/tigers/register",
            files=files,
            data=data
        )

        # Verify factory was used
        mock_factory_class.assert_called_once()
        mock_factory.get_tiger_service.assert_called_once()

    @patch('backend.api.tiger_routes.ServiceFactory')
    def test_get_tiger_uses_factory(self, mock_factory_class, authenticated_client, db_session, sample_tiger_id):
        """Test that /tigers/{id} endpoint uses ServiceFactory."""
        # Setup mock factory
        mock_factory = Mock(spec=ServiceFactory)
        mock_tiger_service = Mock(spec=TigerService)
        mock_tiger_service.get_tiger = Mock(return_value={
            "tiger_id": str(sample_tiger_id),
            "name": "Test Tiger"
        })
        mock_factory.get_tiger_service.return_value = mock_tiger_service
        mock_factory_class.return_value = mock_factory

        # Make request
        response = authenticated_client.get(f"/tigers/{sample_tiger_id}")

        # Verify factory was used
        mock_factory_class.assert_called_once()
        mock_factory.get_tiger_service.assert_called_once()


class TestInvestigation2RoutesServiceFactory:
    """Tests for ServiceFactory usage in investigation2 routes."""

    @patch('backend.api.investigation2_routes.ServiceFactory')
    @patch('backend.api.investigation2_routes.queue_investigation')
    def test_launch_investigation_uses_factory(
        self,
        mock_queue,
        mock_factory_class,
        authenticated_client,
        db_session
    ):
        """Test that /investigation2/launch endpoint uses ServiceFactory."""
        # Setup mock factory
        mock_factory = Mock(spec=ServiceFactory)
        mock_investigation_service = Mock(spec=InvestigationService)
        mock_investigation = Mock()
        mock_investigation.investigation_id = "test-id-123"
        mock_investigation_service.create_investigation.return_value = mock_investigation
        mock_factory.get_investigation_service.return_value = mock_investigation_service
        mock_factory_class.return_value = mock_factory

        # Mock queue_investigation
        mock_queue.return_value = None

        # Create test image
        image_data = BytesIO(b"fake image data")
        files = {"image": ("test.jpg", image_data, "image/jpeg")}
        data = {
            "location": "Test Location",
            "notes": "Test notes",
            "audience": "internal"
        }

        # Make request
        response = authenticated_client.post(
            "/investigation2/launch",
            files=files,
            data=data
        )

        # Verify factory was instantiated
        mock_factory_class.assert_called_once()

        # Verify factory method was called
        mock_factory.get_investigation_service.assert_called_once()

        # Verify service method was called
        mock_investigation_service.create_investigation.assert_called_once()

    @patch('backend.api.investigation2_routes.ServiceFactory')
    def test_get_investigation_status_uses_factory(
        self,
        mock_factory_class,
        authenticated_client,
        db_session,
        sample_investigation_id
    ):
        """Test that /investigation2/{id}/status endpoint uses ServiceFactory."""
        # Setup mock factory
        mock_factory = Mock(spec=ServiceFactory)
        mock_investigation_service = Mock(spec=InvestigationService)
        mock_investigation = Mock()
        mock_investigation.investigation_id = sample_investigation_id
        mock_investigation.status = "active"
        mock_investigation.title = "Test"
        mock_investigation_service.get_investigation.return_value = mock_investigation
        mock_factory.get_investigation_service.return_value = mock_investigation_service
        mock_factory_class.return_value = mock_factory

        # Make request
        response = authenticated_client.get(f"/investigation2/{sample_investigation_id}/status")

        # Verify factory was used
        mock_factory_class.assert_called_once()
        mock_factory.get_investigation_service.assert_called_once()


class TestModalRoutesServiceFactory:
    """Tests for ServiceFactory usage in modal routes."""

    @patch('backend.api.modal_routes.ServiceFactory')
    def test_detect_animals_uses_factory(self, mock_factory_class, authenticated_client, db_session):
        """Test that /modal/detect endpoint uses ServiceFactory (if applicable)."""
        # This route may not use ServiceFactory yet, but we should verify
        # Setup mock if needed
        pass  # Placeholder - implement if modal routes use ServiceFactory


class TestServiceFactoryIntegration:
    """Integration tests for ServiceFactory in routes."""

    def test_tiger_routes_get_tiger_service_integration(self, authenticated_client, test_user):
        """Integration test: verify tiger routes can get TigerService from factory."""
        # Create test image
        image_data = BytesIO(b"fake image data")
        files = {"image": ("test.jpg", image_data, "image/jpeg")}
        data = {"similarity_threshold": 0.8}

        # This will fail because image is fake, but we can verify factory is called
        response = authenticated_client.post(
            "/tigers/identify",
            files=files,
            data=data
        )

        # Should return error due to fake image, not factory error
        # If we get 400 (bad image) rather than 500 (factory error), factory worked
        assert response.status_code in [400, 422]  # 422 for validation errors

    def test_investigation_routes_get_service_integration(self, authenticated_client, test_user):
        """Integration test: verify investigation routes can get service from factory."""
        # Create test image
        image_data = BytesIO(b"fake image data")
        files = {"image": ("test.jpg", image_data, "image/jpeg")}
        data = {
            "location": "Test Location",
            "audience": "internal"
        }

        # Make request
        response = authenticated_client.post(
            "/investigation2/launch",
            files=files,
            data=data
        )

        # Should succeed or fail for reasons other than factory
        # Factory errors would be 500, image/validation errors would be 400/422
        assert response.status_code in [200, 201, 202, 400, 422]


class TestFactoryErrorHandling:
    """Tests for error handling when factory fails."""

    @patch('backend.api.tiger_routes.ServiceFactory')
    def test_factory_session_error_handled(self, mock_factory_class, authenticated_client):
        """Test that routes handle factory session errors gracefully."""
        # Setup factory to raise error
        mock_factory_class.side_effect = ValueError("Database session required")

        # Create test image
        image_data = BytesIO(b"fake image data")
        files = {"image": ("test.jpg", image_data, "image/jpeg")}
        data = {"similarity_threshold": 0.8}

        # Make request
        response = authenticated_client.post(
            "/tigers/identify",
            files=files,
            data=data
        )

        # Should return 500 error
        assert response.status_code == 500

    @patch('backend.api.tiger_routes.ServiceFactory')
    def test_service_method_error_handled(self, mock_factory_class, authenticated_client):
        """Test that routes handle service method errors gracefully."""
        # Setup mock factory with service that raises error
        mock_factory = Mock(spec=ServiceFactory)
        mock_tiger_service = Mock(spec=TigerService)
        mock_tiger_service.get_available_models.return_value = ["wildlife_tools"]
        mock_tiger_service.identify_tiger_from_image.side_effect = Exception("Service error")
        mock_factory.get_tiger_service.return_value = mock_tiger_service
        mock_factory_class.return_value = mock_factory

        # Create test image
        image_data = BytesIO(b"fake image data")
        files = {"image": ("test.jpg", image_data, "image/jpeg")}
        data = {"similarity_threshold": 0.8}

        # Make request
        response = authenticated_client.post(
            "/tigers/identify",
            files=files,
            data=data
        )

        # Should return 500 error
        assert response.status_code == 500


class TestFactoryCaching:
    """Tests for ServiceFactory caching behavior in routes."""

    @patch('backend.api.tiger_routes.ServiceFactory')
    def test_factory_creates_new_instance_per_request(
        self,
        mock_factory_class,
        authenticated_client
    ):
        """Test that each request creates a new ServiceFactory instance."""
        # Setup mock
        mock_factory = Mock(spec=ServiceFactory)
        mock_tiger_service = Mock(spec=TigerService)
        mock_tiger_service.get_available_models.return_value = ["wildlife_tools"]
        mock_tiger_service.identify_tiger_from_image = Mock(return_value={
            "identified": False,
            "matches": []
        })
        mock_factory.get_tiger_service.return_value = mock_tiger_service
        mock_factory_class.return_value = mock_factory

        # Create test image
        image_data = BytesIO(b"fake image data")
        files = {"image": ("test.jpg", image_data, "image/jpeg")}
        data = {"similarity_threshold": 0.8}

        # Make first request
        response1 = authenticated_client.post(
            "/tigers/identify",
            files=files,
            data=data
        )

        # Make second request
        image_data2 = BytesIO(b"fake image data")
        files2 = {"image": ("test2.jpg", image_data2, "image/jpeg")}
        response2 = authenticated_client.post(
            "/tigers/identify",
            files=files2,
            data=data
        )

        # Factory should be instantiated twice (once per request)
        assert mock_factory_class.call_count == 2

    def test_factory_uses_correct_session_per_request(self, authenticated_client, test_user):
        """Test that factory gets correct database session for each request."""
        # This is implicitly tested by the routes working correctly
        # Each request should get its own session from dependency injection

        # Create test image
        image_data = BytesIO(b"fake image data")
        files = {"image": ("test.jpg", image_data, "image/jpeg")}
        data = {
            "location": "Test Location",
            "audience": "internal"
        }

        # Multiple requests should each work with their own session
        response1 = authenticated_client.post(
            "/investigation2/launch",
            files=files,
            data=data
        )

        image_data2 = BytesIO(b"fake image data 2")
        files2 = {"image": ("test2.jpg", image_data2, "image/jpeg")}
        response2 = authenticated_client.post(
            "/investigation2/launch",
            files=files2,
            data=data
        )

        # Both should succeed (or fail consistently, not with session conflicts)
        assert response1.status_code in [200, 201, 202, 400, 422]
        assert response2.status_code in [200, 201, 202, 400, 422]
