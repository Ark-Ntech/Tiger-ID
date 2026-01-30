"""Modal infrastructure module.

Provides a clean interface for interacting with Modal ML inference services.
"""

from backend.infrastructure.modal.base_client import (
    BaseModalClient,
    ModalClientError,
    ModalUnavailableError,
)
from backend.infrastructure.modal.model_registry import ModelRegistry
from backend.infrastructure.modal.mock_provider import MockResponseProvider

__all__ = [
    "BaseModalClient",
    "ModalClientError",
    "ModalUnavailableError",
    "ModelRegistry",
    "MockResponseProvider",
]
