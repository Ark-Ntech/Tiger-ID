"""Centralized model loader for tiger ReID models.

This module provides a singleton ModelLoader class that handles the initialization
and management of all available ReID models. This eliminates code duplication
across tiger_service.py, identification_service.py, and registration_service.py.
"""

from typing import Dict, Type, Optional, List
import threading

from backend.utils.logging import get_logger
from backend.models.interfaces.base_reid_model import BaseReIDModel

logger = get_logger(__name__)


class ModelLoader:
    """Singleton class for loading and managing ReID models.

    This class centralizes model initialization logic that was previously
    duplicated across multiple services. It provides thread-safe lazy loading
    of model classes and caches model instances.

    Usage:
        loader = ModelLoader.get_instance()
        available = loader.get_available_models()
        model = loader.get_model('wildlife_tools')
    """

    _instance: Optional['ModelLoader'] = None
    _lock = threading.Lock()

    def __init__(self):
        """Initialize ModelLoader. Use get_instance() instead of direct instantiation."""
        self._available_models: Dict[str, Type[BaseReIDModel]] = {}
        self._model_instances: Dict[str, BaseReIDModel] = {}
        self._initialized = False

    @classmethod
    def get_instance(cls) -> 'ModelLoader':
        """Get the singleton ModelLoader instance.

        Returns:
            The singleton ModelLoader instance
        """
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking pattern
                if cls._instance is None:
                    cls._instance = ModelLoader()
                    cls._instance._initialize_models()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance. Useful for testing."""
        with cls._lock:
            cls._instance = None

    def _initialize_models(self) -> None:
        """Initialize all available RE-ID models.

        This method attempts to import each model class and registers it
        if available. Models that fail to import (e.g., due to missing
        dependencies) are logged and skipped.
        """
        if self._initialized:
            return

        # Start with the base TigerReIDModel which should always be available
        try:
            from backend.models.reid import TigerReIDModel
            self._available_models['tiger_reid'] = TigerReIDModel
            logger.info("TigerReIDModel (base) available")
        except ImportError as e:
            logger.warning(f"Base TigerReIDModel not available: {e}")

        # Load optional models that run on Modal
        self._try_load_model(
            'wildlife_tools',
            'backend.models.wildlife_tools',
            'WildlifeToolsReIDModel',
            'WildlifeTools model available (Modal)'
        )

        self._try_load_model(
            'cvwc2019',
            'backend.models.cvwc2019_reid',
            'CVWC2019ReIDModel',
            'CVWC2019 model available (Modal)'
        )

        self._try_load_model(
            'rapid',
            'backend.models.rapid_reid',
            'RAPIDReIDModel',
            'RAPID model available (Modal)'
        )

        self._try_load_model(
            'transreid',
            'backend.models.transreid',
            'TransReIDModel',
            'TransReID model available (Modal)'
        )

        self._try_load_model(
            'megadescriptor_b',
            'backend.models.megadescriptor_b',
            'MegaDescriptorBReIDModel',
            'MegaDescriptor-B model available (Modal)'
        )

        self._initialized = True
        logger.info(
            f"ModelLoader initialized with {len(self._available_models)} models: "
            f"{list(self._available_models.keys())}"
        )

    def _try_load_model(
        self,
        model_key: str,
        module_path: str,
        class_name: str,
        success_message: str
    ) -> bool:
        """Attempt to load a model class from the specified module.

        Args:
            model_key: Key to register the model under
            module_path: Full module path (e.g., 'backend.models.wildlife_tools')
            class_name: Name of the model class
            success_message: Message to log on successful load

        Returns:
            True if model was loaded successfully, False otherwise
        """
        try:
            import importlib
            module = importlib.import_module(module_path)
            model_class = getattr(module, class_name)
            self._available_models[model_key] = model_class
            logger.info(success_message)
            return True
        except ImportError as e:
            logger.debug(f"{class_name} not available: {e}")
            return False
        except AttributeError as e:
            logger.debug(f"{class_name} not found in {module_path}: {e}")
            return False

    def get_available_models(self) -> Dict[str, Type[BaseReIDModel]]:
        """Get dictionary of all available model classes.

        Returns:
            Dictionary mapping model names to their classes
        """
        return self._available_models.copy()

    def get_available_model_names(self) -> List[str]:
        """Get list of available model names.

        Returns:
            List of model name strings
        """
        return list(self._available_models.keys())

    def is_model_available(self, model_name: str) -> bool:
        """Check if a model is available.

        Args:
            model_name: Name of the model to check

        Returns:
            True if model is available, False otherwise
        """
        return model_name in self._available_models

    def get_model_class(self, model_name: str) -> Type[BaseReIDModel]:
        """Get a model class by name.

        Args:
            model_name: Name of the model

        Returns:
            The model class

        Raises:
            ValueError: If model is not available
        """
        if model_name not in self._available_models:
            raise ValueError(
                f"Model '{model_name}' not available. "
                f"Available models: {self.get_available_model_names()}"
            )
        return self._available_models[model_name]

    def get_model(
        self,
        model_name: Optional[str] = None,
        use_cache: bool = True
    ) -> BaseReIDModel:
        """Get a model instance by name.

        Args:
            model_name: Name of the model (defaults to 'wildlife_tools')
            use_cache: If True, return cached instance if available

        Returns:
            Model instance

        Raises:
            ValueError: If model is not available
        """
        if model_name is None:
            model_name = 'wildlife_tools'  # Default model

        if model_name not in self._available_models:
            raise ValueError(
                f"Model '{model_name}' not available. "
                f"Available models: {self.get_available_model_names()}"
            )

        # Return cached instance if available and caching is enabled
        if use_cache and model_name in self._model_instances:
            return self._model_instances[model_name]

        # Create new instance
        model_class = self._available_models[model_name]
        instance = model_class()

        # Cache if enabled
        if use_cache:
            self._model_instances[model_name] = instance

        return instance

    def get_all_model_instances(self) -> Dict[str, BaseReIDModel]:
        """Get instances of all available models.

        Creates and caches instances for any models not yet instantiated.

        Returns:
            Dictionary mapping model names to their instances
        """
        for model_name in self._available_models:
            if model_name not in self._model_instances:
                model_class = self._available_models[model_name]
                self._model_instances[model_name] = model_class()
        return self._model_instances.copy()

    def clear_instance_cache(self) -> None:
        """Clear the model instance cache.

        This forces new instances to be created on next access.
        Useful for testing or when models need to be reinitialized.
        """
        self._model_instances.clear()
        logger.debug("Model instance cache cleared")


# Convenience function for getting the singleton instance
def get_model_loader() -> ModelLoader:
    """Get the singleton ModelLoader instance.

    This is a convenience function equivalent to ModelLoader.get_instance().

    Returns:
        The singleton ModelLoader instance
    """
    return ModelLoader.get_instance()
