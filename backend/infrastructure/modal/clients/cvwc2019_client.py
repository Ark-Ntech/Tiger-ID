"""CVWC2019 ReID Modal client."""

from typing import Dict, Any

from backend.infrastructure.modal.clients.base_client import (
    EmbeddingModalClient,
    create_singleton_getter,
)
from backend.infrastructure.modal.mock_provider import MockResponseProvider


class CVWC2019Client(EmbeddingModalClient):
    """Client for CVWC2019 ReID model on Modal.

    CVWC2019 uses a ResNet152 backbone trained on the CVWC 2019
    tiger re-identification challenge dataset.
    """

    EMBEDDING_DIM = 2048  # ResNet152 global stream output

    @property
    def app_name(self) -> str:
        return "tiger-id-models"

    @property
    def class_name(self) -> str:
        return "CVWC2019ReIDModel"

    def _get_mock_response(self) -> Dict[str, Any]:
        return MockResponseProvider.cvwc2019_embedding(self.EMBEDDING_DIM)


# Singleton getter
get_cvwc2019_client = create_singleton_getter(CVWC2019Client, "CVWC2019")
