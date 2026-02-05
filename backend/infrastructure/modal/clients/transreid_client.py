"""TransReID Modal client."""

from typing import Dict, Any

from backend.infrastructure.modal.clients.base_client import (
    EmbeddingModalClient,
    create_singleton_getter,
)
from backend.infrastructure.modal.mock_provider import MockResponseProvider


class TransReIDClient(EmbeddingModalClient):
    """Client for TransReID model on Modal.

    TransReID uses Vision Transformer (ViT-Base) architecture
    with jigsaw patch shuffling for robust re-identification.
    Outputs 768-dimensional embeddings.
    """

    EMBEDDING_DIM = 768  # ViT-Base output

    @property
    def app_name(self) -> str:
        return "tiger-id-models"

    @property
    def class_name(self) -> str:
        return "TransReIDModel"

    def _get_mock_response(self) -> Dict[str, Any]:
        return MockResponseProvider.transreid_embedding()


# Singleton getter
get_transreid_client = create_singleton_getter(TransReIDClient, "TransReID")
