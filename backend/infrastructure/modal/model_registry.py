"""Model registry for Modal function references."""

from typing import Dict, Tuple, Optional
from dataclasses import dataclass

from backend.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a Modal model.

    Attributes:
        app_name: Modal app name
        class_name: Modal class name
        embedding_dim: Embedding dimension (for ReID models)
        description: Human-readable description
    """
    app_name: str
    class_name: str
    embedding_dim: Optional[int] = None
    description: str = ""


class ModelRegistry:
    """Registry of available Modal models.

    Provides a centralized place to manage model configurations
    and discover available models.
    """

    # Default model configurations
    _MODELS: Dict[str, ModelConfig] = {
        "tiger_reid": ModelConfig(
            app_name="tiger-id-models",
            class_name="TigerReIDModel",
            embedding_dim=2048,
            description="Base tiger ReID model using ResNet50"
        ),
        "megadetector": ModelConfig(
            app_name="tiger-id-models",
            class_name="MegaDetectorModel",
            description="MegaDetector v5 for animal detection"
        ),
        "wildlife_tools": ModelConfig(
            app_name="tiger-id-models",
            class_name="WildlifeToolsModel",
            embedding_dim=2048,
            description="WildlifeTools MegaDescriptor for wildlife ReID"
        ),
        "rapid_reid": ModelConfig(
            app_name="tiger-id-models",
            class_name="RAPIDReIDModel",
            embedding_dim=2048,
            description="RAPID real-time animal pattern ReID"
        ),
        "cvwc2019_reid": ModelConfig(
            app_name="tiger-id-models",
            class_name="CVWC2019ReIDModel",
            embedding_dim=3072,
            description="CVWC2019 part-pose guided tiger ReID"
        ),
        "omnivinci": ModelConfig(
            app_name="tiger-id-models",
            class_name="OmniVinciModel",
            description="OmniVinci omni-modal visual understanding"
        ),
    }

    def __init__(self):
        """Initialize the model registry."""
        self._models = self._MODELS.copy()
        self._custom_models: Dict[str, ModelConfig] = {}

    def get_config(self, model_name: str) -> ModelConfig:
        """Get configuration for a model.

        Args:
            model_name: Name of the model

        Returns:
            ModelConfig for the model

        Raises:
            ValueError: If model not found
        """
        if model_name in self._models:
            return self._models[model_name]
        if model_name in self._custom_models:
            return self._custom_models[model_name]
        raise ValueError(
            f"Unknown model: {model_name}. "
            f"Available: {self.list_models()}"
        )

    def get_app_and_class(self, model_name: str) -> Tuple[str, str]:
        """Get app name and class name for a model.

        Args:
            model_name: Name of the model

        Returns:
            Tuple of (app_name, class_name)
        """
        config = self.get_config(model_name)
        return config.app_name, config.class_name

    def list_models(self) -> list:
        """Get list of all available model names.

        Returns:
            List of model names
        """
        return list(self._models.keys()) + list(self._custom_models.keys())

    def list_reid_models(self) -> list:
        """Get list of ReID model names (models with embedding_dim).

        Returns:
            List of ReID model names
        """
        return [
            name for name, config in {**self._models, **self._custom_models}.items()
            if config.embedding_dim is not None
        ]

    def get_embedding_dim(self, model_name: str) -> Optional[int]:
        """Get embedding dimension for a model.

        Args:
            model_name: Name of the model

        Returns:
            Embedding dimension or None if not a ReID model
        """
        config = self.get_config(model_name)
        return config.embedding_dim

    def register_model(self, model_name: str, config: ModelConfig) -> None:
        """Register a custom model.

        Args:
            model_name: Name to register the model under
            config: Model configuration
        """
        if model_name in self._models:
            logger.warning(
                f"Overriding built-in model '{model_name}' with custom config"
            )
        self._custom_models[model_name] = config
        logger.info(f"Registered custom model: {model_name}")

    def unregister_model(self, model_name: str) -> bool:
        """Unregister a custom model.

        Args:
            model_name: Name of the model to unregister

        Returns:
            True if model was unregistered, False if not found
        """
        if model_name in self._custom_models:
            del self._custom_models[model_name]
            logger.info(f"Unregistered custom model: {model_name}")
            return True
        return False

    def is_reid_model(self, model_name: str) -> bool:
        """Check if a model is a ReID model.

        Args:
            model_name: Name of the model

        Returns:
            True if model is a ReID model
        """
        config = self.get_config(model_name)
        return config.embedding_dim is not None


# Singleton instance
_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """Get the singleton model registry instance.

    Returns:
        ModelRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
