"""Specialized Modal clients for different ML models."""

from backend.infrastructure.modal.clients.tiger_reid_client import TigerReIDClient
from backend.infrastructure.modal.clients.megadetector_client import MegaDetectorClient
from backend.infrastructure.modal.clients.wildlife_tools_client import WildlifeToolsClient
from backend.infrastructure.modal.clients.rapid_reid_client import RAPIDReIDClient
from backend.infrastructure.modal.clients.cvwc2019_client import CVWC2019Client
from backend.infrastructure.modal.clients.omnivinci_client import OmniVinciClient

__all__ = [
    "TigerReIDClient",
    "MegaDetectorClient",
    "WildlifeToolsClient",
    "RAPIDReIDClient",
    "CVWC2019Client",
    "OmniVinciClient",
]
