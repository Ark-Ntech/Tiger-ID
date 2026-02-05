"""Specialized Modal clients for different ML models."""

from backend.infrastructure.modal.clients.base_client import (
    EmbeddingModalClient,
    create_singleton_getter,
)
from backend.infrastructure.modal.clients.tiger_reid_client import TigerReIDClient
from backend.infrastructure.modal.clients.megadetector_client import MegaDetectorClient
from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient
from backend.infrastructure.modal.clients.rapid_reid_client import RAPIDReIDClient
from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client
from backend.infrastructure.modal.clients.transreid_client import TransReIDClient
from backend.infrastructure.modal.clients.megadescriptor_b_client import MegaDescriptorBClient
from backend.infrastructure.modal.clients.matchanything_client import MatchAnythingClient

__all__ = [
    # Base class
    "EmbeddingModalClient",
    "create_singleton_getter",
    # Model clients
    "TigerReIDClient",
    "MegaDetectorClient",
    "WildlifeToolsClient",
    "RAPIDReIDClient",
    "CVWC2019Client",
    "TransReIDClient",
    "MegaDescriptorBClient",
    "MatchAnythingClient",
]
