"""Abstract interfaces for ML models.

This module defines the contracts that all ML models must implement,
ensuring consistency across different model implementations.
"""

from backend.models.interfaces.base_reid_model import BaseReIDModel
from backend.models.interfaces.base_detection_model import BaseDetectionModel

__all__ = [
    "BaseReIDModel",
    "BaseDetectionModel",
]
