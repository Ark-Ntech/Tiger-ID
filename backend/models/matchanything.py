"""
MatchAnything-ELOFTR Model for Tiger Verification.

This model uses keypoint matching to verify tiger identity by comparing
geometric features (stripe patterns) between image pairs.

Unlike ReID models that generate embeddings for single images, MatchAnything
compares image pairs directly and returns correspondence scores.

Integration approach:
1. ReID ensemble finds top-K candidates (fast, O(1) lookup)
2. MatchAnything verifies candidates by pairwise comparison (slow, O(K) calls)
3. Combined scores improve final ranking

Requires: pip install "git+https://github.com/huggingface/transformers@22e89e538529420b2ddae6af70865655bc5c22d8"
"""

from typing import Dict, List, Tuple, Any, Optional
import io
import numpy as np
from PIL import Image

from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Try to import transformers with MatchAnything support
try:
    from transformers import AutoImageProcessor, AutoModelForKeypointMatching
    import torch
    MATCHANYTHING_AVAILABLE = True
except ImportError:
    MATCHANYTHING_AVAILABLE = False
    logger.warning(
        "MatchAnything not available. Install with: "
        'pip install "git+https://github.com/huggingface/transformers@22e89e538529420b2ddae6af70865655bc5c22d8"'
    )


class MatchAnythingModel:
    """
    Feature matching model for tiger verification.

    Uses MatchAnything-ELOFTR to find keypoint correspondences between
    image pairs, providing geometric verification of tiger identity.
    """

    MODEL_NAME = "zju-community/matchanything_eloftr"

    def __init__(
        self,
        device: Optional[str] = None,
        threshold: float = 0.2,
        use_modal: bool = False
    ):
        """
        Initialize MatchAnything model.

        Args:
            device: Device to use ('cuda', 'cpu', or None for auto)
            threshold: Keypoint matching confidence threshold
            use_modal: If True, use Modal client instead of local model
        """
        self.threshold = threshold
        self.use_modal = use_modal
        self._model = None
        self._processor = None
        self._modal_client = None

        # Determine device
        if device is None:
            if MATCHANYTHING_AVAILABLE:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                self.device = "cpu"
        else:
            self.device = device

        logger.info(f"MatchAnythingModel initialized (device={self.device}, use_modal={use_modal})")

    @property
    def is_available(self) -> bool:
        """Check if MatchAnything is available."""
        if self.use_modal:
            return True  # Modal handles availability
        return MATCHANYTHING_AVAILABLE

    async def load_model(self) -> bool:
        """
        Load the MatchAnything model.

        Returns:
            True if model loaded successfully
        """
        if self.use_modal:
            logger.info("Using Modal for MatchAnything - no local model to load")
            return True

        if not MATCHANYTHING_AVAILABLE:
            logger.error("MatchAnything not available - install required transformers version")
            return False

        if self._model is not None:
            logger.info("Model already loaded")
            return True

        try:
            logger.info(f"Loading MatchAnything model: {self.MODEL_NAME}")
            self._processor = AutoImageProcessor.from_pretrained(self.MODEL_NAME)
            self._model = AutoModelForKeypointMatching.from_pretrained(self.MODEL_NAME)
            self._model.to(self.device)
            # Set to inference mode
            self._model.requires_grad_(False)
            logger.info("MatchAnything model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load MatchAnything model: {e}")
            return False

    async def match_pair(
        self,
        img1: Image.Image,
        img2: Image.Image
    ) -> Dict[str, Any]:
        """
        Compare two images and return match quality metrics.

        Args:
            img1: First PIL Image (query)
            img2: Second PIL Image (candidate)

        Returns:
            Dictionary with matching metrics:
            - num_matches: Number of keypoint correspondences
            - mean_score: Average confidence of matches
            - max_score: Maximum match confidence
            - total_score: Sum of all match confidences
        """
        if self.use_modal:
            return await self._match_pair_modal(img1, img2)
        return await self._match_pair_local(img1, img2)

    async def _match_pair_local(
        self,
        img1: Image.Image,
        img2: Image.Image
    ) -> Dict[str, Any]:
        """Run matching locally."""
        if self._model is None:
            await self.load_model()

        if self._model is None:
            logger.error("Model not loaded")
            return self._empty_result()

        try:
            # Ensure RGB
            img1 = img1.convert("RGB")
            img2 = img2.convert("RGB")

            # Prepare inputs
            inputs = self._processor([img1, img2], return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Run inference
            with torch.no_grad():
                outputs = self._model(**inputs)

            # Post-process
            image_sizes = [[(img1.height, img1.width), (img2.height, img2.width)]]
            results = self._processor.post_process_keypoint_matching(
                outputs, image_sizes, threshold=self.threshold
            )

            # Extract metrics
            scores = results[0]["scores"]
            num_matches = len(scores)

            return {
                "num_matches": num_matches,
                "mean_score": float(scores.mean().item()) if num_matches > 0 else 0.0,
                "max_score": float(scores.max().item()) if num_matches > 0 else 0.0,
                "min_score": float(scores.min().item()) if num_matches > 0 else 0.0,
                "total_score": float(scores.sum().item()) if num_matches > 0 else 0.0,
                "success": True
            }

        except Exception as e:
            logger.error(f"Error in match_pair_local: {e}")
            return self._empty_result()

    async def _match_pair_modal(
        self,
        img1: Image.Image,
        img2: Image.Image
    ) -> Dict[str, Any]:
        """Run matching via Modal."""
        if self._modal_client is None:
            from backend.services.modal_client import get_modal_client
            self._modal_client = get_modal_client()

        try:
            # Convert images to bytes
            buffer1 = io.BytesIO()
            img1.save(buffer1, format='JPEG')
            img1_bytes = buffer1.getvalue()

            buffer2 = io.BytesIO()
            img2.save(buffer2, format='JPEG')
            img2_bytes = buffer2.getvalue()

            # Call Modal
            result = await self._modal_client.matchanything_match(
                img1_bytes, img2_bytes, self.threshold
            )
            return result

        except Exception as e:
            logger.error(f"Error in match_pair_modal: {e}")
            return self._empty_result()

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result for error cases."""
        return {
            "num_matches": 0,
            "mean_score": 0.0,
            "max_score": 0.0,
            "min_score": 0.0,
            "total_score": 0.0,
            "success": False
        }

    async def verify_candidates(
        self,
        query_image: Image.Image,
        candidates: List[Dict[str, Any]],
        reid_weight: float = 0.6,
        match_weight: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Verify ReID candidates using geometric matching.

        Args:
            query_image: Query tiger image
            candidates: List of candidate dictionaries with:
                - tiger_id: Tiger identifier
                - image: PIL Image or image path
                - reid_score: Similarity score from ReID model
            reid_weight: Weight for ReID score in combined score
            match_weight: Weight for match score in combined score

        Returns:
            List of candidates with added match metrics and combined scores,
            sorted by combined_score descending
        """
        results = []

        for candidate in candidates:
            # Get candidate image
            candidate_img = candidate.get("image")
            if isinstance(candidate_img, str):
                candidate_img = Image.open(candidate_img)
            elif candidate_img is None:
                logger.warning(f"No image for candidate {candidate.get('tiger_id')}")
                continue

            # Run matching
            match_result = await self.match_pair(query_image, candidate_img)

            # Normalize match score (num_matches / expected_max)
            # Typical matches range from 0-500, normalize to 0-1
            normalized_match = min(match_result["num_matches"] / 200.0, 1.0)

            # Combine scores
            reid_score = candidate.get("reid_score", 0.0)
            combined_score = (
                reid_weight * reid_score +
                match_weight * normalized_match
            )

            results.append({
                "tiger_id": candidate.get("tiger_id"),
                "reid_score": reid_score,
                "num_matches": match_result["num_matches"],
                "mean_match_score": match_result["mean_score"],
                "total_match_score": match_result["total_score"],
                "normalized_match_score": normalized_match,
                "combined_score": combined_score,
                "match_success": match_result.get("success", False)
            })

        # Sort by combined score
        results.sort(key=lambda x: x["combined_score"], reverse=True)

        return results

    async def compute_match_quality(
        self,
        img1: Image.Image,
        img2: Image.Image
    ) -> float:
        """
        Compute a single quality score for the match.

        Higher score indicates more likely same tiger.

        Args:
            img1: First image
            img2: Second image

        Returns:
            Match quality score (0-1)
        """
        result = await self.match_pair(img1, img2)

        # Combine num_matches and mean_score for quality
        # Normalize: assume 200 matches is excellent, 50 is good
        match_factor = min(result["num_matches"] / 200.0, 1.0)
        score_factor = result["mean_score"]  # Already 0-1

        # Weighted combination
        quality = 0.7 * match_factor + 0.3 * score_factor

        return quality


# Singleton instance for convenience
_instance: Optional[MatchAnythingModel] = None


def get_matchanything_model(use_modal: bool = False) -> MatchAnythingModel:
    """
    Get singleton MatchAnything model instance.

    Args:
        use_modal: If True, use Modal for inference

    Returns:
        MatchAnythingModel instance
    """
    global _instance
    if _instance is None:
        _instance = MatchAnythingModel(use_modal=use_modal)
    return _instance
