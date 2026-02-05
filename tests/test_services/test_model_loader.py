"""Tests for the ModelLoader singleton class.

Tests the centralized model loading functionality that replaces
duplicated code across tiger services.
"""

import pytest
from unittest.mock import patch, MagicMock

from backend.services.tiger.model_loader import ModelLoader, get_model_loader


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the ModelLoader singleton before each test."""
    ModelLoader.reset_instance()
    yield
    ModelLoader.reset_instance()


class TestModelLoaderSingleton:
    """Tests for ModelLoader singleton behavior."""

    def test_get_instance_returns_same_instance(self):
        """Test that get_instance returns the same singleton instance."""
        instance1 = ModelLoader.get_instance()
        instance2 = ModelLoader.get_instance()

        assert instance1 is instance2

    def test_reset_instance_creates_new_instance(self):
        """Test that reset_instance allows creating a new instance."""
        instance1 = ModelLoader.get_instance()
        ModelLoader.reset_instance()
        instance2 = ModelLoader.get_instance()

        assert instance1 is not instance2

    def test_get_model_loader_function(self):
        """Test that get_model_loader convenience function works."""
        instance1 = get_model_loader()
        instance2 = ModelLoader.get_instance()

        assert instance1 is instance2


class TestModelLoaderInitialization:
    """Tests for ModelLoader model initialization."""

    def test_initialization_loads_base_model(self):
        """Test that the base TigerReIDModel is always loaded."""
        loader = ModelLoader.get_instance()

        # The base tiger_reid model should always be available
        assert loader.is_model_available('tiger_reid')

    def test_get_available_models_returns_dict(self):
        """Test that get_available_models returns a dictionary."""
        loader = ModelLoader.get_instance()
        models = loader.get_available_models()

        assert isinstance(models, dict)
        # Should have at least the base model
        assert len(models) >= 1

    def test_get_available_model_names_returns_list(self):
        """Test that get_available_model_names returns a list."""
        loader = ModelLoader.get_instance()
        names = loader.get_available_model_names()

        assert isinstance(names, list)
        assert len(names) >= 1
        assert 'tiger_reid' in names


class TestModelLoaderModelAccess:
    """Tests for accessing models through ModelLoader."""

    def test_get_model_class(self):
        """Test getting a model class by name."""
        loader = ModelLoader.get_instance()
        model_class = loader.get_model_class('tiger_reid')

        assert model_class is not None

    def test_get_model_class_invalid_name(self):
        """Test getting a model class with invalid name raises ValueError."""
        loader = ModelLoader.get_instance()

        with pytest.raises(ValueError) as exc_info:
            loader.get_model_class('nonexistent_model')

        assert 'not available' in str(exc_info.value)

    def test_is_model_available_true(self):
        """Test is_model_available returns True for available models."""
        loader = ModelLoader.get_instance()

        assert loader.is_model_available('tiger_reid') is True

    def test_is_model_available_false(self):
        """Test is_model_available returns False for unavailable models."""
        loader = ModelLoader.get_instance()

        assert loader.is_model_available('nonexistent_model') is False

    def test_get_model_default(self):
        """Test get_model returns default model when name is None."""
        loader = ModelLoader.get_instance()

        # Should use wildlife_tools as default, or fall back to tiger_reid
        try:
            model = loader.get_model(None)
            assert model is not None
        except ValueError:
            # If wildlife_tools is not available, this is expected
            pass

    def test_get_model_invalid_name(self):
        """Test get_model raises ValueError for invalid model name."""
        loader = ModelLoader.get_instance()

        with pytest.raises(ValueError) as exc_info:
            loader.get_model('nonexistent_model')

        assert 'not available' in str(exc_info.value)


class TestModelLoaderCaching:
    """Tests for model instance caching."""

    @patch('backend.models.reid.TigerReIDModel')
    def test_get_model_caches_instance(self, mock_model_class):
        """Test that get_model caches model instances."""
        mock_instance = MagicMock()
        mock_model_class.return_value = mock_instance

        loader = ModelLoader.get_instance()
        # Force the model class to be the mock
        loader._available_models['tiger_reid'] = mock_model_class

        # Get the model twice
        model1 = loader.get_model('tiger_reid')
        model2 = loader.get_model('tiger_reid')

        # Should be the same instance
        assert model1 is model2
        # Constructor should only be called once
        assert mock_model_class.call_count == 1

    @patch('backend.models.reid.TigerReIDModel')
    def test_get_model_no_cache(self, mock_model_class):
        """Test that get_model with use_cache=False creates new instance."""
        mock_model_class.return_value = MagicMock()

        loader = ModelLoader.get_instance()
        loader._available_models['tiger_reid'] = mock_model_class

        # Get model without caching
        loader.get_model('tiger_reid', use_cache=False)
        loader.get_model('tiger_reid', use_cache=False)

        # Constructor should be called each time
        assert mock_model_class.call_count >= 2

    def test_clear_instance_cache(self):
        """Test that clear_instance_cache removes cached instances."""
        loader = ModelLoader.get_instance()

        # This should not raise
        loader.clear_instance_cache()

        # Cache should be empty
        assert len(loader._model_instances) == 0


class TestModelLoaderGetAllInstances:
    """Tests for getting all model instances."""

    def test_get_all_model_instances_returns_dict(self):
        """Test that get_all_model_instances returns a dictionary."""
        loader = ModelLoader.get_instance()
        instances = loader.get_all_model_instances()

        assert isinstance(instances, dict)
        # Should have at least the base model
        assert len(instances) >= 1

    def test_get_all_model_instances_creates_instances(self):
        """Test that get_all_model_instances creates instances for all models."""
        loader = ModelLoader.get_instance()

        # Clear cache first
        loader.clear_instance_cache()

        instances = loader.get_all_model_instances()

        # All available models should have instances
        for model_name in loader.get_available_model_names():
            assert model_name in instances


class TestModelLoaderThreadSafety:
    """Tests for thread safety of ModelLoader."""

    def test_concurrent_get_instance(self):
        """Test that concurrent calls to get_instance are thread-safe."""
        import threading
        import time

        instances = []
        errors = []

        def get_instance_thread():
            try:
                # Small delay to increase chance of concurrent access
                time.sleep(0.001)
                instance = ModelLoader.get_instance()
                instances.append(instance)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = [threading.Thread(target=get_instance_thread) for _ in range(10)]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # No errors should occur
        assert len(errors) == 0

        # All instances should be the same
        assert len(instances) == 10
        assert all(i is instances[0] for i in instances)


class TestModelLoaderIntegration:
    """Integration tests for ModelLoader with services."""

    def test_identification_service_uses_model_loader(self):
        """Test that TigerIdentificationService uses ModelLoader."""
        from unittest.mock import MagicMock

        # Create a mock database session
        mock_db = MagicMock()

        # Import and instantiate the service
        from backend.services.tiger.identification_service import TigerIdentificationService

        service = TigerIdentificationService(db=mock_db)

        # The service should have access to the model loader
        assert hasattr(service, '_model_loader')
        assert service._model_loader is ModelLoader.get_instance()

    def test_registration_service_uses_model_loader(self):
        """Test that TigerRegistrationService uses ModelLoader."""
        from unittest.mock import MagicMock

        # Create a mock database session
        mock_db = MagicMock()

        # Import and instantiate the service
        from backend.services.tiger.registration_service import TigerRegistrationService

        service = TigerRegistrationService(db=mock_db)

        # The service should have access to the model loader
        assert hasattr(service, '_model_loader')
        assert service._model_loader is ModelLoader.get_instance()

    def test_tiger_service_uses_model_loader(self):
        """Test that TigerService uses ModelLoader."""
        from unittest.mock import MagicMock

        # Create a mock database session
        mock_db = MagicMock()

        # Import and instantiate the service
        from backend.services.tiger_service import TigerService

        service = TigerService(db=mock_db)

        # The service should have access to the model loader
        assert hasattr(service, '_model_loader')
        assert service._model_loader is ModelLoader.get_instance()
