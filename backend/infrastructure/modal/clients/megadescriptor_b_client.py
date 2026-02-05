"""MegaDescriptor-B Modal client."""

from typing import Dict, Any

from backend.infrastructure.modal.clients.base_client import (
    EmbeddingModalClient,
    create_singleton_getter,
)
from backend.infrastructure.modal.mock_provider import MockResponseProvider


class MegaDescriptorBClient(EmbeddingModalClient):
    """Client for MegaDescriptor-B model on Modal.

    MegaDescriptor-B-224 is a faster variant using Swin-Base backbone
    with 224x224 input (vs 384x384 for MegaDescriptor-L).
    Outputs 1024-dimensional embeddings.
    """

    EMBEDDING_DIM = 1024  # Swin-Base output

    @property
    def app_name(self) -> str:
        return "tiger-id-models"

    @property
    def class_name(self) -> str:
        return "MegaDescriptorBModel"

    def _get_mock_response(self) -> Dict[str, Any]:
        return MockResponseProvider.megadescriptor_b_embedding(self.EMBEDDING_DIM)


# Singleton getter
get_megadescriptor_b_client = create_singleton_getter(MegaDescriptorBClient, "MegaDescriptor-B")
