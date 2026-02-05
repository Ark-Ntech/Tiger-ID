"""WildlifeTools Modal client."""

from typing import Dict, Any

from backend.infrastructure.modal.clients.base_client import (
    EmbeddingModalClient,
    create_singleton_getter,
)
from backend.infrastructure.modal.mock_provider import MockResponseProvider


class WildlifeToolsClient(EmbeddingModalClient):
    """Client for WildlifeTools model on Modal.

    WildlifeTools uses MegaDescriptor-L-384 with a Swin-Large backbone
    trained on diverse wildlife species for re-identification.
    """

    EMBEDDING_DIM = 1536  # MegaDescriptor-L-384 Swin-Large output

    @property
    def app_name(self) -> str:
        return "tiger-id-models"

    @property
    def class_name(self) -> str:
        return "WildlifeToolsModel"

    def _get_mock_response(self) -> Dict[str, Any]:
        return MockResponseProvider.wildlife_tools_embedding(self.EMBEDDING_DIM)


# Singleton getter
get_wildlife_tools_client = create_singleton_getter(WildlifeToolsClient, "WildlifeTools")
