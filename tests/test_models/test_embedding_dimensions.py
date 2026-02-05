"""Tests to verify model wrapper embedding dimensions match model_registry.

This test suite ensures that all ReID model wrappers have embedding_dim properties
that exactly match the values defined in the model registry. This prevents runtime
errors where embedding dimensions mismatch between model outputs and storage/comparison.

Each test verifies:
1. Model wrapper instantiates correctly
2. Model has an embedding_dim property
3. The embedding_dim matches the registry value exactly
"""

import pytest
from unittest.mock import MagicMock, patch

from backend.infrastructure.modal.model_registry import get_model_registry


class TestEmbeddingDimensionsMatchRegistry:
    """Test that all model wrapper embedding_dim properties match the registry."""

    @pytest.fixture
    def registry(self):
        """Get the model registry instance."""
        return get_model_registry()

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for model initialization."""
        settings = MagicMock()
        # Wildlife tools settings
        settings.models.wildlife_tools.similarity_threshold = 0.85
        # CVWC2019 settings
        settings.models.cvwc2019.path = "/path/to/model"
        settings.models.cvwc2019.similarity_threshold = 0.80
        # Tiger ReID settings
        settings.models.reid_path = "/path/to/reid"
        settings.models.reid_embedding_dim = 2048
        # RAPID settings
        settings.models.rapid.path = "/path/to/rapid"
        settings.models.rapid.similarity_threshold = 0.80
        return settings

    @pytest.fixture
    def mock_modal_client(self):
        """Mock Modal client."""
        return MagicMock()

    def test_wildlife_tools_embedding_dim(self, registry, mock_settings, mock_modal_client):
        """Verify WildlifeToolsReIDModel.embedding_dim matches registry (1536)."""
        from backend.models.wildlife_tools import WildlifeToolsReIDModel

        expected_dim = registry.get_embedding_dim('wildlife_tools')
        assert expected_dim == 1536, "Registry should define wildlife_tools as 1536-dim"

        with patch('backend.models.wildlife_tools.get_settings', return_value=mock_settings), \
             patch('backend.models.wildlife_tools.get_modal_client', return_value=mock_modal_client):
            model = WildlifeToolsReIDModel()

        assert hasattr(model, 'embedding_dim'), "Model must have embedding_dim property"
        assert model.embedding_dim == expected_dim, (
            f"WildlifeToolsReIDModel.embedding_dim ({model.embedding_dim}) "
            f"must match registry value ({expected_dim})"
        )

    def test_cvwc2019_embedding_dim(self, registry, mock_settings, mock_modal_client):
        """Verify CVWC2019ReIDModel.embedding_dim matches registry (2048)."""
        from backend.models.cvwc2019_reid import CVWC2019ReIDModel

        expected_dim = registry.get_embedding_dim('cvwc2019_reid')
        assert expected_dim == 2048, "Registry should define cvwc2019_reid as 2048-dim"

        with patch('backend.models.cvwc2019_reid.get_settings', return_value=mock_settings), \
             patch('backend.models.cvwc2019_reid.get_modal_client', return_value=mock_modal_client):
            model = CVWC2019ReIDModel()

        assert hasattr(model, 'embedding_dim'), "Model must have embedding_dim property"
        assert model.embedding_dim == expected_dim, (
            f"CVWC2019ReIDModel.embedding_dim ({model.embedding_dim}) "
            f"must match registry value ({expected_dim})"
        )

    def test_tiger_reid_embedding_dim(self, registry, mock_settings, mock_modal_client):
        """Verify TigerReIDModel.embedding_dim matches registry (2048)."""
        from backend.models.reid import TigerReIDModel

        expected_dim = registry.get_embedding_dim('tiger_reid')
        assert expected_dim == 2048, "Registry should define tiger_reid as 2048-dim"

        with patch('backend.models.reid.get_settings', return_value=mock_settings), \
             patch('backend.models.reid.get_modal_client', return_value=mock_modal_client):
            model = TigerReIDModel()

        assert hasattr(model, 'embedding_dim'), "Model must have embedding_dim property"
        assert model.embedding_dim == expected_dim, (
            f"TigerReIDModel.embedding_dim ({model.embedding_dim}) "
            f"must match registry value ({expected_dim})"
        )

    def test_transreid_embedding_dim(self, registry):
        """Verify TransReIDModel.embedding_dim matches registry (768)."""
        from backend.models.transreid import TransReIDModel

        expected_dim = registry.get_embedding_dim('transreid')
        assert expected_dim == 768, "Registry should define transreid as 768-dim"

        model = TransReIDModel()

        assert hasattr(model, 'embedding_dim'), "Model must have embedding_dim property"
        assert model.embedding_dim == expected_dim, (
            f"TransReIDModel.embedding_dim ({model.embedding_dim}) "
            f"must match registry value ({expected_dim})"
        )

    def test_megadescriptor_b_embedding_dim(self, registry, mock_settings, mock_modal_client):
        """Verify MegaDescriptorBReIDModel.embedding_dim matches registry (1024)."""
        from backend.models.megadescriptor_b import MegaDescriptorBReIDModel

        expected_dim = registry.get_embedding_dim('megadescriptor_b')
        assert expected_dim == 1024, "Registry should define megadescriptor_b as 1024-dim"

        with patch('backend.models.megadescriptor_b.get_settings', return_value=mock_settings), \
             patch('backend.models.megadescriptor_b.get_modal_client', return_value=mock_modal_client):
            model = MegaDescriptorBReIDModel()

        assert hasattr(model, 'embedding_dim'), "Model must have embedding_dim property"
        assert model.embedding_dim == expected_dim, (
            f"MegaDescriptorBReIDModel.embedding_dim ({model.embedding_dim}) "
            f"must match registry value ({expected_dim})"
        )

    def test_rapid_reid_embedding_dim(self, registry, mock_settings, mock_modal_client):
        """Verify RAPIDReIDModel.embedding_dim matches registry (2048)."""
        from backend.models.rapid_reid import RAPIDReIDModel

        expected_dim = registry.get_embedding_dim('rapid_reid')
        assert expected_dim == 2048, "Registry should define rapid_reid as 2048-dim"

        with patch('backend.models.rapid_reid.get_settings', return_value=mock_settings), \
             patch('backend.models.rapid_reid.get_modal_client', return_value=mock_modal_client):
            model = RAPIDReIDModel()

        assert hasattr(model, 'embedding_dim'), "Model must have embedding_dim property"
        assert model.embedding_dim == expected_dim, (
            f"RAPIDReIDModel.embedding_dim ({model.embedding_dim}) "
            f"must match registry value ({expected_dim})"
        )


class TestRegistryCompleteness:
    """Test that the registry contains all expected ReID models."""

    def test_all_reid_models_present(self):
        """Verify registry contains all expected ReID models."""
        registry = get_model_registry()
        reid_models = registry.list_reid_models()

        expected_models = {
            'wildlife_tools',
            'cvwc2019_reid',
            'tiger_reid',
            'transreid',
            'megadescriptor_b',
            'rapid_reid'
        }

        missing_models = expected_models - set(reid_models)
        assert not missing_models, f"Registry missing ReID models: {missing_models}"

    def test_all_reid_models_have_dimensions(self):
        """Verify all ReID models have non-None embedding dimensions."""
        registry = get_model_registry()
        reid_models = registry.list_reid_models()

        for model_name in reid_models:
            embedding_dim = registry.get_embedding_dim(model_name)
            assert embedding_dim is not None, f"Model {model_name} must have embedding_dim"
            assert isinstance(embedding_dim, int), f"Model {model_name} embedding_dim must be int"
            assert embedding_dim > 0, f"Model {model_name} embedding_dim must be positive"


class TestEmbeddingDimensionValues:
    """Test that embedding dimensions have expected values."""

    @pytest.fixture
    def registry(self):
        """Get the model registry instance."""
        return get_model_registry()

    def test_wildlife_tools_dimension_value(self, registry):
        """Verify wildlife_tools uses 1536 dimensions (MegaDescriptor-L-384 with Swin-Large)."""
        assert registry.get_embedding_dim('wildlife_tools') == 1536

    def test_cvwc2019_dimension_value(self, registry):
        """Verify cvwc2019_reid uses 2048 dimensions (global stream output)."""
        assert registry.get_embedding_dim('cvwc2019_reid') == 2048

    def test_tiger_reid_dimension_value(self, registry):
        """Verify tiger_reid uses 2048 dimensions (ResNet50 base)."""
        assert registry.get_embedding_dim('tiger_reid') == 2048

    def test_transreid_dimension_value(self, registry):
        """Verify transreid uses 768 dimensions (ViT-Base)."""
        assert registry.get_embedding_dim('transreid') == 768

    def test_megadescriptor_b_dimension_value(self, registry):
        """Verify megadescriptor_b uses 1024 dimensions (Swin-Base)."""
        assert registry.get_embedding_dim('megadescriptor_b') == 1024

    def test_rapid_reid_dimension_value(self, registry):
        """Verify rapid_reid uses 2048 dimensions."""
        assert registry.get_embedding_dim('rapid_reid') == 2048


class TestConsistencyAcrossEnsemble:
    """Test that ensemble can handle models with different embedding dimensions."""

    def test_embedding_dimensions_are_diverse(self):
        """Verify ensemble uses models with diverse embedding dimensions."""
        registry = get_model_registry()

        dimensions = {
            registry.get_embedding_dim('wildlife_tools'),
            registry.get_embedding_dim('cvwc2019_reid'),
            registry.get_embedding_dim('tiger_reid'),
            registry.get_embedding_dim('transreid'),
            registry.get_embedding_dim('megadescriptor_b'),
            registry.get_embedding_dim('rapid_reid')
        }

        # We should have at least 3 different embedding dimensions in the ensemble
        # This diversity helps the ensemble capture different feature representations
        assert len(dimensions) >= 3, (
            f"Ensemble should use models with diverse embedding dimensions, "
            f"but only found {len(dimensions)} unique dimensions: {sorted(dimensions)}"
        )

    def test_registry_config_consistency(self):
        """Verify registry config structure is consistent for all ReID models."""
        registry = get_model_registry()
        reid_models = registry.list_reid_models()

        for model_name in reid_models:
            config = registry.get_config(model_name)

            # All ReID models should have these attributes
            assert hasattr(config, 'app_name'), f"{model_name} config missing app_name"
            assert hasattr(config, 'class_name'), f"{model_name} config missing class_name"
            assert hasattr(config, 'embedding_dim'), f"{model_name} config missing embedding_dim"
            assert hasattr(config, 'description'), f"{model_name} config missing description"

            # ReID models should use the 'reid' app
            assert config.app_name == 'reid', f"{model_name} should use 'reid' app"

            # Descriptions should be non-empty
            assert config.description, f"{model_name} should have a description"
