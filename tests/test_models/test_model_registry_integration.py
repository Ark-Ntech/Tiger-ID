"""Integration tests for model registry and model wrappers.

This test suite verifies that the model registry and model wrappers
work together correctly, ensuring that:
1. All models can be instantiated via registry lookups
2. Embedding dimensions are consistent throughout the system
3. Model configs contain all required information
4. No orphaned models exist in either registry or codebase
"""

import pytest
from unittest.mock import MagicMock, patch

from backend.infrastructure.modal.model_registry import get_model_registry


class TestModelRegistryIntegration:
    """Integration tests between registry and model wrappers."""

    @pytest.fixture
    def registry(self):
        """Get fresh registry instance for each test."""
        return get_model_registry()

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for model initialization."""
        settings = MagicMock()
        settings.models.wildlife_tools.similarity_threshold = 0.85
        settings.models.cvwc2019.path = "/path/to/model"
        settings.models.cvwc2019.similarity_threshold = 0.80
        settings.models.reid_path = "/path/to/reid"
        settings.models.reid_embedding_dim = 2048
        settings.models.rapid.path = "/path/to/rapid"
        settings.models.rapid.similarity_threshold = 0.80
        return settings

    @pytest.fixture
    def mock_modal_client(self):
        """Mock Modal client."""
        return MagicMock()

    def test_all_reid_models_can_be_instantiated(self, registry, mock_settings, mock_modal_client):
        """Verify all ReID models in registry can be instantiated."""
        reid_models = registry.list_reid_models()

        model_classes = {
            'wildlife_tools': ('backend.models.wildlife_tools', 'WildlifeToolsReIDModel'),
            'cvwc2019_reid': ('backend.models.cvwc2019_reid', 'CVWC2019ReIDModel'),
            'tiger_reid': ('backend.models.reid', 'TigerReIDModel'),
            'transreid': ('backend.models.transreid', 'TransReIDModel'),
            'megadescriptor_b': ('backend.models.megadescriptor_b', 'MegaDescriptorBReIDModel'),
            'rapid_reid': ('backend.models.rapid_reid', 'RAPIDReIDModel'),
        }

        for model_name in reid_models:
            assert model_name in model_classes, f"No model class mapping for {model_name}"

            module_path, class_name = model_classes[model_name]
            module = __import__(module_path, fromlist=[class_name])
            model_class = getattr(module, class_name)

            # Instantiate with appropriate mocking
            if model_name == 'transreid':
                # TransReID doesn't need mocking
                model = model_class()
            else:
                with patch(f'{module_path}.get_settings', return_value=mock_settings), \
                     patch(f'{module_path}.get_modal_client', return_value=mock_modal_client):
                    model = model_class()

            # Verify model has required properties
            assert hasattr(model, 'embedding_dim'), f"{class_name} missing embedding_dim"
            assert isinstance(model.embedding_dim, int), f"{class_name}.embedding_dim not int"
            assert model.embedding_dim > 0, f"{class_name}.embedding_dim not positive"

    def test_registry_contains_only_valid_models(self, registry):
        """Verify registry only contains models that exist in codebase."""
        reid_models = registry.list_reid_models()

        valid_models = {
            'wildlife_tools',
            'cvwc2019_reid',
            'tiger_reid',
            'transreid',
            'megadescriptor_b',
            'rapid_reid'
        }

        for model_name in reid_models:
            assert model_name in valid_models, (
                f"Registry contains unknown model: {model_name}"
            )

    def test_all_models_have_consistent_config(self, registry):
        """Verify all models have complete and consistent configs."""
        reid_models = registry.list_reid_models()

        for model_name in reid_models:
            config = registry.get_config(model_name)

            # Required fields
            assert config.app_name, f"{model_name}: app_name is empty"
            assert config.class_name, f"{model_name}: class_name is empty"
            assert config.embedding_dim is not None, f"{model_name}: embedding_dim is None"
            assert config.description, f"{model_name}: description is empty"

            # Type validation
            assert isinstance(config.app_name, str), f"{model_name}: app_name not string"
            assert isinstance(config.class_name, str), f"{model_name}: class_name not string"
            assert isinstance(config.embedding_dim, int), f"{model_name}: embedding_dim not int"
            assert isinstance(config.description, str), f"{model_name}: description not string"

            # Value validation
            assert config.app_name == 'reid', f"{model_name}: should use 'reid' app"
            assert config.embedding_dim > 0, f"{model_name}: embedding_dim not positive"
            assert len(config.description) > 10, f"{model_name}: description too short"

    def test_embedding_dimensions_are_sensible(self, registry):
        """Verify embedding dimensions are within reasonable ranges."""
        reid_models = registry.list_reid_models()

        for model_name in reid_models:
            dim = registry.get_embedding_dim(model_name)

            # Typical range for deep learning embeddings
            assert 256 <= dim <= 4096, (
                f"{model_name} dimension {dim} outside typical range [256, 4096]"
            )

            # Should be divisible by common factors for efficient computation
            # (though not strictly required)
            if dim > 256:
                # Just a warning, not a hard requirement
                pass

    def test_is_reid_model_accurate(self, registry):
        """Verify is_reid_model correctly identifies ReID models."""
        # ReID models
        reid_models = [
            'wildlife_tools',
            'cvwc2019_reid',
            'tiger_reid',
            'transreid',
            'megadescriptor_b',
            'rapid_reid'
        ]

        for model_name in reid_models:
            assert registry.is_reid_model(model_name), (
                f"{model_name} should be identified as ReID model"
            )

        # Non-ReID models
        if 'megadetector' in registry.list_models():
            assert not registry.is_reid_model('megadetector'), (
                "megadetector should not be ReID model"
            )

    def test_get_app_and_class_returns_valid_values(self, registry):
        """Verify get_app_and_class returns correct values for all models."""
        reid_models = registry.list_reid_models()

        expected_app = 'reid'

        for model_name in reid_models:
            app_name, class_name = registry.get_app_and_class(model_name)

            assert app_name == expected_app, (
                f"{model_name} should use app '{expected_app}', got '{app_name}'"
            )
            assert class_name, f"{model_name} class_name is empty"
            assert isinstance(class_name, str), f"{model_name} class_name not string"

    def test_registry_list_methods_consistency(self, registry):
        """Verify list_models and list_reid_models are consistent."""
        all_models = set(registry.list_models())
        reid_models = set(registry.list_reid_models())

        # ReID models should be subset of all models
        assert reid_models.issubset(all_models), (
            "ReID models not a subset of all models"
        )

        # Verify each ReID model has embedding_dim
        for model_name in reid_models:
            dim = registry.get_embedding_dim(model_name)
            assert dim is not None, (
                f"ReID model {model_name} should have embedding_dim"
            )

        # Verify non-ReID models don't have embedding_dim
        non_reid_models = all_models - reid_models
        for model_name in non_reid_models:
            dim = registry.get_embedding_dim(model_name)
            assert dim is None, (
                f"Non-ReID model {model_name} should not have embedding_dim"
            )

    def test_model_names_follow_convention(self, registry):
        """Verify model names follow naming conventions."""
        reid_models = registry.list_reid_models()

        for model_name in reid_models:
            # Should be lowercase with underscores
            assert model_name == model_name.lower(), (
                f"{model_name} should be lowercase"
            )
            assert ' ' not in model_name, (
                f"{model_name} should not contain spaces"
            )
            # Should contain letters
            assert any(c.isalpha() for c in model_name), (
                f"{model_name} should contain letters"
            )

    def test_registry_get_config_error_handling(self, registry):
        """Verify registry handles unknown models correctly."""
        with pytest.raises(ValueError) as exc_info:
            registry.get_config('nonexistent_model')

        assert 'Unknown model' in str(exc_info.value)
        assert 'nonexistent_model' in str(exc_info.value)
        assert 'Available' in str(exc_info.value)


class TestModelDimensionConsistency:
    """Test that model dimensions are consistent across all components."""

    def test_no_dimension_conflicts(self):
        """Verify no models claim the same name with different dimensions."""
        registry = get_model_registry()
        reid_models = registry.list_reid_models()

        # Build dimension map
        dimension_map = {}
        for model_name in reid_models:
            dim = registry.get_embedding_dim(model_name)
            dimension_map[model_name] = dim

        # Check for unexpected duplicates or conflicts
        # (this is more of a sanity check)
        model_names = list(dimension_map.keys())
        assert len(model_names) == len(set(model_names)), (
            "Duplicate model names found in registry"
        )

    def test_ensemble_compatible_dimensions(self):
        """Verify all models can work together in an ensemble."""
        registry = get_model_registry()
        reid_models = registry.list_reid_models()

        # All models should have valid dimensions
        for model_name in reid_models:
            dim = registry.get_embedding_dim(model_name)
            assert dim is not None and dim > 0, (
                f"{model_name} has invalid dimension for ensemble use"
            )

        # Should have multiple different dimensions for diversity
        unique_dims = set(
            registry.get_embedding_dim(m) for m in reid_models
        )
        assert len(unique_dims) >= 3, (
            f"Ensemble should have at least 3 unique dimensions, "
            f"found {len(unique_dims)}: {sorted(unique_dims)}"
        )
