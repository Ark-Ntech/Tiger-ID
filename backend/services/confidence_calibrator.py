"""
Confidence Calibration Service for Tiger ReID.

Different models output similarity scores with different distributions.
Temperature scaling normalizes these scores for better ensemble fusion.

For example:
- WildlifeTools MegaDescriptor outputs well-calibrated cosine similarities
- CVWC2019 may output higher similarity scores on average
- TransReID may output lower similarity scores

This service calibrates all scores to a common scale.
"""

from typing import Dict, Optional, List, Tuple
import numpy as np
from backend.utils.logging import get_logger

logger = get_logger(__name__)


# Temperature bounds to prevent extreme calibration
MIN_TEMPERATURE = 0.1   # Prevent extreme score spreading
MAX_TEMPERATURE = 5.0   # Prevent extreme score compression

# Default calibration temperatures for each model
# Temperature < 1.0: Makes scores more extreme (spreads distribution)
# Temperature > 1.0: Makes scores less extreme (compresses distribution)
# Temperature = 1.0: No change (reference model)
DEFAULT_CALIBRATION_TEMPS = {
    "wildlife_tools": 1.0,      # Reference model (best performer, MegaDescriptor-L-384)
    "cvwc2019_reid": 0.85,      # Tends to output higher scores (ResNet152 backbone)
    "transreid": 1.1,           # Tends to output lower scores (ViT-Base)
    "tiger_reid": 0.9,          # Baseline ResNet50
    "rapid_reid": 0.95,         # Edge-optimized model
    "megadescriptor_b": 1.0,    # Similar to MegaDescriptor-L (MegaDescriptor-B-224)
}

# Default ensemble weights based on expected accuracy
# Weights are normalized when computing ensemble scores
DEFAULT_MODEL_WEIGHTS = {
    "wildlife_tools": 0.40,      # Best individual performer (MegaDescriptor-L-384)
    "cvwc2019_reid": 0.30,       # Part-based features with ResNet152 backbone
    "transreid": 0.20,           # ViT features (good for diverse poses)
    "tiger_reid": 0.10,          # Baseline ResNet50
    "rapid_reid": 0.05,          # Edge model (lower accuracy but fast)
    "megadescriptor_b": 0.15,    # Faster MegaDescriptor variant
}


def calibrate_similarity(
    similarity: float,
    model_name: str,
    temperature: Optional[float] = None
) -> float:
    """
    Calibrate a similarity score using temperature scaling.

    Args:
        similarity: Raw similarity score from model
        model_name: Name of the model
        temperature: Optional custom temperature. If None, uses default.

    Returns:
        Calibrated similarity score
    """
    if temperature is None:
        temperature = DEFAULT_CALIBRATION_TEMPS.get(model_name, 1.0)

    if temperature <= 0:
        raise ValueError(f"Temperature must be positive, got {temperature}")

    # Clamp temperature to valid bounds to prevent extreme calibration
    temperature = max(MIN_TEMPERATURE, min(MAX_TEMPERATURE, temperature))

    # Apply temperature scaling
    # For similarity scores, we divide by temperature
    calibrated = similarity / temperature

    # Clip to valid range [0, 1] for cosine similarities
    calibrated = np.clip(calibrated, 0.0, 1.0)

    return float(calibrated)


def calibrate_similarities_batch(
    similarities: np.ndarray,
    model_name: str,
    temperature: Optional[float] = None
) -> np.ndarray:
    """
    Calibrate a batch of similarity scores.

    Args:
        similarities: Array of similarity scores
        model_name: Name of the model
        temperature: Optional custom temperature

    Returns:
        Calibrated similarity scores
    """
    if temperature is None:
        temperature = DEFAULT_CALIBRATION_TEMPS.get(model_name, 1.0)

    # Clamp temperature to valid bounds
    temperature = max(MIN_TEMPERATURE, min(MAX_TEMPERATURE, temperature))

    calibrated = similarities / temperature
    calibrated = np.clip(calibrated, 0.0, 1.0)

    return calibrated


class ConfidenceCalibrator:
    """
    Service for calibrating model confidence scores.

    Uses temperature scaling to normalize similarity distributions
    across different models for better ensemble fusion.
    """

    def __init__(
        self,
        temperatures: Optional[Dict[str, float]] = None,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize calibrator with custom temperatures and weights.

        Args:
            temperatures: Dict mapping model names to temperature values.
                         If None, uses defaults.
            weights: Dict mapping model names to ensemble weights.
                    If None, uses defaults.
        """
        self.temperatures = temperatures or DEFAULT_CALIBRATION_TEMPS.copy()
        self.weights = weights or DEFAULT_MODEL_WEIGHTS.copy()
        self.logger = get_logger(__name__)

    def set_temperature(self, model_name: str, temperature: float) -> None:
        """
        Set calibration temperature for a model.

        Args:
            model_name: Model identifier
            temperature: Temperature value (must be between MIN_TEMPERATURE and MAX_TEMPERATURE)

        Raises:
            ValueError: If temperature is outside valid bounds
        """
        if temperature <= 0:
            raise ValueError(f"Temperature must be positive, got {temperature}")
        if temperature < MIN_TEMPERATURE or temperature > MAX_TEMPERATURE:
            raise ValueError(
                f"Temperature must be between {MIN_TEMPERATURE} and {MAX_TEMPERATURE}, got {temperature}"
            )
        self.temperatures[model_name] = temperature
        self.logger.info(f"Set temperature for {model_name}: {temperature}")

    def set_weight(self, model_name: str, weight: float) -> None:
        """
        Set ensemble weight for a model.

        Args:
            model_name: Model identifier
            weight: Weight value (non-negative)
        """
        if weight < 0:
            raise ValueError(f"Weight must be non-negative, got {weight}")
        self.weights[model_name] = weight
        self.logger.info(f"Set weight for {model_name}: {weight}")

    def calibrate(
        self,
        similarity: float,
        model_name: str
    ) -> float:
        """
        Calibrate a single similarity score.

        Args:
            similarity: Raw similarity score
            model_name: Model identifier

        Returns:
            Calibrated similarity score
        """
        temp = self.temperatures.get(model_name, 1.0)
        return calibrate_similarity(similarity, model_name, temp)

    def calibrate_batch(
        self,
        similarities: np.ndarray,
        model_name: str
    ) -> np.ndarray:
        """
        Calibrate a batch of similarity scores.

        Args:
            similarities: Array of similarity scores
            model_name: Model identifier

        Returns:
            Calibrated similarities
        """
        temp = self.temperatures.get(model_name, 1.0)
        return calibrate_similarities_batch(similarities, model_name, temp)

    def get_weight(self, model_name: str) -> float:
        """
        Get ensemble weight for a model.

        Args:
            model_name: Model identifier

        Returns:
            Weight value
        """
        return self.weights.get(model_name, 0.1)

    def fuse_scores(
        self,
        model_scores: Dict[str, float],
        calibrate_first: bool = True
    ) -> float:
        """
        Fuse scores from multiple models using weighted average.

        Args:
            model_scores: Dict mapping model names to similarity scores
            calibrate_first: Whether to calibrate scores before fusion

        Returns:
            Fused similarity score
        """
        if not model_scores:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for model_name, score in model_scores.items():
            weight = self.get_weight(model_name)

            if calibrate_first:
                score = self.calibrate(score, model_name)

            weighted_sum += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def fuse_match_lists(
        self,
        model_matches: Dict[str, List[Tuple[str, float]]],
        calibrate_first: bool = True
    ) -> List[Tuple[str, float]]:
        """
        Fuse match lists from multiple models.

        Each model provides a list of (tiger_id, similarity) tuples.
        This method combines them using weighted averaging.

        Args:
            model_matches: Dict mapping model names to match lists
            calibrate_first: Whether to calibrate scores before fusion

        Returns:
            Fused and sorted list of (tiger_id, similarity) tuples
        """
        if not model_matches:
            return []

        # Aggregate scores by tiger ID
        tiger_scores: Dict[str, Dict[str, float]] = {}

        for model_name, matches in model_matches.items():
            for tiger_id, score in matches:
                if tiger_id not in tiger_scores:
                    tiger_scores[tiger_id] = {}
                tiger_scores[tiger_id][model_name] = score

        # Fuse scores for each tiger
        fused_results = []
        for tiger_id, scores in tiger_scores.items():
            fused_score = self.fuse_scores(scores, calibrate_first)
            fused_results.append((tiger_id, fused_score))

        # Sort by fused score (descending)
        fused_results.sort(key=lambda x: x[1], reverse=True)

        return fused_results

    def learn_temperatures(
        self,
        validation_data: List[Dict],
        optimize_metric: str = "rank1"
    ) -> Dict[str, float]:
        """
        Learn optimal temperatures from validation data.

        This is a placeholder for temperature optimization.
        In practice, you would use held-out validation data to
        optimize temperatures using cross-validation.

        Args:
            validation_data: List of validation examples with
                           ground truth and model predictions
            optimize_metric: Metric to optimize ("rank1" or "map")

        Returns:
            Dict of optimized temperatures
        """
        self.logger.info("Temperature learning not yet implemented - using defaults")
        return self.temperatures.copy()

    def get_model_stats(
        self,
        model_name: str
    ) -> Dict[str, float]:
        """
        Get calibration statistics for a model.

        Args:
            model_name: Model identifier

        Returns:
            Dict with temperature and weight
        """
        return {
            "temperature": self.temperatures.get(model_name, 1.0),
            "weight": self.weights.get(model_name, 0.1)
        }

    def list_models(self) -> List[str]:
        """
        List all models with calibration settings.

        Returns:
            List of model names
        """
        return list(set(list(self.temperatures.keys()) + list(self.weights.keys())))
