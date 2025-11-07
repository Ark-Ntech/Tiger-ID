"""Computer vision models"""

from backend.models.detection import TigerDetectionModel
from backend.models.reid import TigerReIDModel
from backend.models.rapid_reid import RAPIDReIDModel
from backend.models.wildlife_tools import WildlifeToolsReIDModel
from backend.models.cvwc2019_reid import CVWC2019ReIDModel
from backend.models.omnivinci import OmniVinciModel

__all__ = [
    "TigerDetectionModel",
    "TigerReIDModel",
    "RAPIDReIDModel",
    "WildlifeToolsReIDModel",
    "CVWC2019ReIDModel",
    "OmniVinciModel",
]
