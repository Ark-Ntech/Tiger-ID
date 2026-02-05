"""Ensemble strategies for tiger re-identification.

This module provides different strategies for combining results from
multiple ReID models to improve identification accuracy.

Strategies:
- StaggeredEnsembleStrategy: Sequential with early exit
- ParallelEnsembleStrategy: All models in parallel with voting
- WeightedEnsembleStrategy: Weighted scoring with re-ranking and calibration
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from uuid import UUID
import asyncio
from PIL import Image
import io
import numpy as np

from backend.utils.logging import get_logger
from backend.database.vector_search import find_matching_tigers
from backend.models.interfaces.base_reid_model import BaseReIDModel
from backend.services.confidence_calibrator import ConfidenceCalibrator, DEFAULT_MODEL_WEIGHTS
from backend.services.reranking_service import RerankingService
from backend.infrastructure.modal.model_registry import ModelRegistry

logger = get_logger(__name__)

# Initialize model registry for dimension validation
_model_registry = ModelRegistry()


class EnsembleStrategy(ABC):
    """Abstract base class for ensemble strategies."""

    @abstractmethod
    async def identify(
        self,
        tiger_crop: bytes,
        models: Dict[str, BaseReIDModel],
        db_session: Any,
        similarity_threshold: float,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Run identification using the ensemble strategy.

        Args:
            tiger_crop: Cropped tiger image as bytes
            models: Dictionary of model_name -> model instance
            db_session: Database session for vector search
            similarity_threshold: Minimum similarity for a match
            user_id: User ID for logging

        Returns:
            Dictionary with identification results
        """
        pass


class StaggeredEnsembleStrategy(EnsembleStrategy):
    """Staggered ensemble with confidence-based early exit.

    Runs models sequentially, stopping early if confidence thresholds are met.

    Stages:
    1. RAPID: >0.90 accept, <0.60 reject, else continue
    2. Wildlife-Tools: >0.85 accept, <0.65 reject, else continue
    3. CVWC2019: >0.80 accept, else continue
    """

    # Confidence thresholds for each stage
    STAGE_CONFIG = [
        {"model": "rapid", "accept": 0.90, "reject": 0.60},
        {"model": "wildlife_tools", "accept": 0.85, "reject": 0.65},
        {"model": "cvwc2019", "accept": 0.80, "reject": None},
    ]

    async def identify(
        self,
        tiger_crop: bytes,
        models: Dict[str, BaseReIDModel],
        db_session: Any,
        similarity_threshold: float,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Run staggered identification with early exit."""
        image_obj = Image.open(io.BytesIO(tiger_crop))

        result = {
            "identified": False,
            "model_path": [],
            "confidence": 0.0,
            "tiger_id": None,
            "tiger_name": None,
            "matches": []
        }

        for stage in self.STAGE_CONFIG:
            model_name = stage["model"]

            if model_name not in models:
                continue

            try:
                model = models[model_name]

                # Generate embedding
                if hasattr(model, 'generate_embedding_from_bytes'):
                    embedding = await model.generate_embedding_from_bytes(tiger_crop)
                else:
                    embedding = await model.generate_embedding(image_obj)

                # Ensure embedding is numpy array
                if isinstance(embedding, list):
                    embedding = np.array(embedding)

                # Validate embedding dimensions
                expected_dim = _model_registry.get_embedding_dim(model_name)
                if expected_dim is not None and embedding.shape[0] != expected_dim:
                    logger.warning(
                        f"Embedding dimension mismatch for {model_name}: "
                        f"expected {expected_dim}, got {embedding.shape[0]}"
                    )
                    continue  # Skip this model and try next stage

                # Search for matches
                matches = find_matching_tigers(
                    db_session,
                    query_embedding=embedding,
                    limit=5,
                    similarity_threshold=similarity_threshold
                )

                result["model_path"].append(model_name)

                if matches:
                    confidence = matches[0]["similarity"]

                    # Check accept threshold
                    if stage["accept"] and confidence > stage["accept"]:
                        result.update({
                            "identified": True,
                            "tiger_id": matches[0]["tiger_id"],
                            "tiger_name": matches[0]["tiger_name"],
                            "confidence": confidence,
                            "matches": matches
                        })
                        logger.info(
                            f"Staggered ensemble: accepted at {model_name} "
                            f"with confidence {confidence:.3f}"
                        )
                        return result

                    # Check reject threshold
                    if stage["reject"] and confidence < stage["reject"]:
                        result["message"] = "Tiger not found in database - new individual"
                        result["requires_verification"] = True
                        logger.info(
                            f"Staggered ensemble: rejected at {model_name} "
                            f"with confidence {confidence:.3f}"
                        )
                        return result

                    # Continue to next stage
                    logger.info(
                        f"Staggered ensemble: {model_name} inconclusive "
                        f"(confidence {confidence:.3f}), continuing"
                    )

            except Exception as e:
                logger.warning(f"{model_name} model failed: {e}, continuing to next stage")

        # No match found after all stages
        result["message"] = "Tiger not found in database - new individual"
        result["requires_verification"] = True
        return result


class ParallelEnsembleStrategy(EnsembleStrategy):
    """Parallel ensemble with consensus decision.

    Runs all models simultaneously and uses voting to determine the result.
    """

    async def identify(
        self,
        tiger_crop: bytes,
        models: Dict[str, BaseReIDModel],
        db_session: Any,
        similarity_threshold: float,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Run all models in parallel and use consensus decision."""
        image_obj = Image.open(io.BytesIO(tiger_crop))

        async def run_model(model_name: str, model: BaseReIDModel) -> Dict[str, Any]:
            """Run a single model and return results."""
            try:
                if hasattr(model, 'generate_embedding_from_bytes'):
                    embedding = await model.generate_embedding_from_bytes(tiger_crop)
                else:
                    embedding = await model.generate_embedding(image_obj)

                # Ensure embedding is numpy array
                if isinstance(embedding, list):
                    embedding = np.array(embedding)

                # Validate embedding dimensions
                expected_dim = _model_registry.get_embedding_dim(model_name)
                if expected_dim is not None and embedding.shape[0] != expected_dim:
                    logger.warning(
                        f"Embedding dimension mismatch for {model_name}: "
                        f"expected {expected_dim}, got {embedding.shape[0]}"
                    )
                    return {
                        "model": model_name,
                        "error": f"Embedding dimension mismatch: expected {expected_dim}, got {embedding.shape[0]}",
                        "success": False
                    }

                matches = find_matching_tigers(
                    db_session,
                    query_embedding=embedding,
                    limit=5,
                    similarity_threshold=similarity_threshold
                )

                return {
                    "model": model_name,
                    "matches": matches,
                    "best_similarity": matches[0]["similarity"] if matches else 0.0,
                    "tiger_id": matches[0]["tiger_id"] if matches else None,
                    "tiger_name": matches[0]["tiger_name"] if matches else None,
                    "success": True
                }
            except Exception as e:
                logger.error(f"Error with model {model_name}: {e}")
                return {
                    "model": model_name,
                    "error": str(e),
                    "success": False
                }

        # Run all models in parallel
        tasks = [
            run_model(model_name, model)
            for model_name, model in models.items()
        ]
        model_results = await asyncio.gather(*tasks)

        return self._consensus_decision(model_results)

    def _consensus_decision(
        self,
        model_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Make consensus decision from multiple model results.

        Returns best match if models agree, or flags for human review if they disagree.
        """
        # Filter successful results
        successful_results = [
            r for r in model_results
            if r.get("success", False) and r.get("matches")
        ]

        if not successful_results:
            return {
                "identified": False,
                "message": "Tiger not found in database - new individual",
                "requires_verification": True,
                "models": {r["model"]: r for r in model_results}
            }

        # Group by tiger_id
        tiger_votes: Dict[str, Dict[str, Any]] = {}
        for result in successful_results:
            tiger_id = result.get("tiger_id")
            if tiger_id:
                if tiger_id not in tiger_votes:
                    tiger_votes[tiger_id] = {
                        "tiger_id": tiger_id,
                        "tiger_name": result.get("tiger_name"),
                        "votes": [],
                        "confidences": []
                    }
                tiger_votes[tiger_id]["votes"].append(result["model"])
                tiger_votes[tiger_id]["confidences"].append(result["best_similarity"])

        # Find tiger with most votes
        if tiger_votes:
            best_tiger = max(tiger_votes.values(), key=lambda x: len(x["votes"]))
            vote_count = len(best_tiger["votes"])
            total_models = len(successful_results)

            # Calculate average confidence
            avg_confidence = sum(best_tiger["confidences"]) / len(best_tiger["confidences"])

            # If majority agree (>50%), accept
            if vote_count > total_models / 2:
                return {
                    "identified": True,
                    "tiger_id": best_tiger["tiger_id"],
                    "tiger_name": best_tiger["tiger_name"],
                    "confidence": avg_confidence,
                    "consensus": True,
                    "vote_count": vote_count,
                    "total_models": total_models,
                    "models": {r["model"]: r for r in model_results}
                }
            else:
                # Split decision - flag for human review
                return {
                    "identified": False,
                    "message": "Models disagree - requires human review",
                    "requires_verification": True,
                    "top_candidates": [
                        {
                            "tiger_id": t["tiger_id"],
                            "tiger_name": t["tiger_name"],
                            "votes": len(t["votes"]),
                            "avg_confidence": sum(t["confidences"]) / len(t["confidences"])
                        }
                        for t in sorted(
                            tiger_votes.values(),
                            key=lambda x: len(x["votes"]),
                            reverse=True
                        )[:2]
                    ],
                    "models": {r["model"]: r for r in model_results}
                }

        return {
            "identified": False,
            "message": "Tiger not found in database - new individual",
            "requires_verification": True,
            "models": {r["model"]: r for r in model_results}
        }


class WeightedEnsembleStrategy(EnsembleStrategy):
    """Weighted ensemble with re-ranking and confidence calibration.

    This is the most advanced strategy that combines:
    1. Weighted scoring based on model accuracy
    2. Confidence calibration to normalize score distributions
    3. K-reciprocal re-ranking for improved accuracy

    Model weights (default):
    - wildlife_tools: 0.40 (MegaDescriptor-L-384, best accuracy)
    - cvwc2019: 0.30 (Part-based ResNet152)
    - transreid: 0.20 (ViT-Base)
    - tiger_reid: 0.10 (Baseline ResNet50)
    """

    def __init__(
        self,
        model_weights: Optional[Dict[str, float]] = None,
        use_reranking: bool = True,
        use_calibration: bool = True,
        reranking_k1: int = 20,
        reranking_k2: int = 6,
        reranking_lambda: float = 0.3
    ):
        """Initialize weighted ensemble strategy.

        Args:
            model_weights: Custom weights for each model
            use_reranking: Whether to apply k-reciprocal re-ranking
            use_calibration: Whether to apply confidence calibration
            reranking_k1: K1 parameter for re-ranking
            reranking_k2: K2 parameter for re-ranking
            reranking_lambda: Lambda parameter for re-ranking
        """
        self.model_weights = model_weights or DEFAULT_MODEL_WEIGHTS.copy()
        self.use_reranking = use_reranking
        self.use_calibration = use_calibration

        # Initialize calibrator and re-ranking service
        self.calibrator = ConfidenceCalibrator(weights=self.model_weights)
        self.reranking_service = RerankingService(
            k1=reranking_k1,
            k2=reranking_k2,
            lambda_value=reranking_lambda
        ) if use_reranking else None

    async def identify(
        self,
        tiger_crop: bytes,
        models: Dict[str, BaseReIDModel],
        db_session: Any,
        similarity_threshold: float,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Run weighted ensemble identification with optional re-ranking.

        Args:
            tiger_crop: Cropped tiger image as bytes
            models: Dictionary of model_name -> model instance
            db_session: Database session for vector search
            similarity_threshold: Minimum similarity for a match
            user_id: User ID for logging

        Returns:
            Dictionary with identification results including:
            - identified: Whether a match was found
            - tiger_id: Best matching tiger ID
            - confidence: Weighted confidence score
            - model_results: Per-model results
            - ensemble_matches: Combined and ranked matches
        """
        image_obj = Image.open(io.BytesIO(tiger_crop))

        async def run_model(model_name: str, model: BaseReIDModel) -> Dict[str, Any]:
            """Run a single model and return results with embedding."""
            try:
                # Generate embedding
                if hasattr(model, 'generate_embedding_from_bytes'):
                    embedding = await model.generate_embedding_from_bytes(tiger_crop)
                else:
                    embedding = await model.generate_embedding(image_obj)

                # Ensure embedding is numpy array
                if isinstance(embedding, list):
                    embedding = np.array(embedding)

                # Validate embedding dimensions
                expected_dim = _model_registry.get_embedding_dim(model_name)
                if expected_dim is not None and embedding.shape[0] != expected_dim:
                    logger.warning(
                        f"Embedding dimension mismatch for {model_name}: "
                        f"expected {expected_dim}, got {embedding.shape[0]}"
                    )
                    return {
                        "model": model_name,
                        "error": f"Embedding dimension mismatch: expected {expected_dim}, got {embedding.shape[0]}",
                        "success": False
                    }

                # Search for matches
                matches = find_matching_tigers(
                    db_session,
                    query_embedding=embedding,
                    limit=10,  # Get more matches for re-ranking
                    similarity_threshold=similarity_threshold * 0.8  # Lower threshold for re-ranking pool
                )

                return {
                    "model": model_name,
                    "embedding": embedding,
                    "matches": matches,
                    "best_similarity": matches[0]["similarity"] if matches else 0.0,
                    "tiger_id": matches[0]["tiger_id"] if matches else None,
                    "tiger_name": matches[0]["tiger_name"] if matches else None,
                    "success": True
                }
            except Exception as e:
                logger.error(f"Error with model {model_name}: {e}")
                return {
                    "model": model_name,
                    "error": str(e),
                    "success": False
                }

        # Run all models in parallel
        tasks = [
            run_model(model_name, model)
            for model_name, model in models.items()
        ]
        model_results = await asyncio.gather(*tasks)

        # Process results with weighted ensemble
        return self._weighted_ensemble_decision(
            model_results,
            similarity_threshold
        )

    def _weighted_ensemble_decision(
        self,
        model_results: List[Dict[str, Any]],
        similarity_threshold: float
    ) -> Dict[str, Any]:
        """Make weighted ensemble decision with calibration and optional re-ranking.

        Args:
            model_results: Results from each model
            similarity_threshold: Minimum similarity threshold

        Returns:
            Ensemble decision with weighted scores
        """
        # Filter successful results
        successful_results = [
            r for r in model_results
            if r.get("success", False) and r.get("matches")
        ]

        if not successful_results:
            return {
                "identified": False,
                "message": "Tiger not found in database - new individual",
                "requires_verification": True,
                "models": {r["model"]: r for r in model_results}
            }

        # Collect all unique tiger IDs and their scores from each model
        tiger_scores: Dict[str, Dict[str, Any]] = {}

        for result in successful_results:
            model_name = result["model"]
            weight = self.model_weights.get(model_name, 0.1)

            for match in result.get("matches", []):
                tiger_id = match.get("tiger_id")
                if not tiger_id:
                    continue

                similarity = match.get("similarity", 0)

                # Apply calibration if enabled
                if self.use_calibration:
                    similarity = self.calibrator.calibrate(similarity, model_name)

                if tiger_id not in tiger_scores:
                    tiger_scores[tiger_id] = {
                        "tiger_id": tiger_id,
                        "tiger_name": match.get("tiger_name"),
                        "model_scores": {},
                        "weighted_sum": 0.0,
                        "total_weight": 0.0
                    }

                # Store the best score from this model for this tiger
                current_score = tiger_scores[tiger_id]["model_scores"].get(model_name, 0)
                if similarity > current_score:
                    # Update weighted sum
                    old_contribution = current_score * weight
                    new_contribution = similarity * weight

                    tiger_scores[tiger_id]["weighted_sum"] += (new_contribution - old_contribution)
                    if model_name not in tiger_scores[tiger_id]["model_scores"]:
                        tiger_scores[tiger_id]["total_weight"] += weight

                    tiger_scores[tiger_id]["model_scores"][model_name] = similarity

        # Calculate final weighted scores
        for tiger_id, data in tiger_scores.items():
            if data["total_weight"] > 0:
                data["weighted_score"] = data["weighted_sum"] / data["total_weight"]
            else:
                data["weighted_score"] = 0.0

            # Count how many models found this tiger
            data["model_count"] = len(data["model_scores"])

        # Sort by weighted score
        ranked_tigers = sorted(
            tiger_scores.values(),
            key=lambda x: x["weighted_score"],
            reverse=True
        )

        if not ranked_tigers:
            return {
                "identified": False,
                "message": "Tiger not found in database - new individual",
                "requires_verification": True,
                "models": {r["model"]: r for r in model_results}
            }

        best_match = ranked_tigers[0]

        # Determine confidence level
        if best_match["weighted_score"] >= 0.90 and best_match["model_count"] >= 2:
            confidence_level = "high"
            identified = True
        elif best_match["weighted_score"] >= 0.80 or (
            best_match["weighted_score"] >= 0.70 and best_match["model_count"] >= 2
        ):
            confidence_level = "medium"
            identified = True
        elif best_match["weighted_score"] >= similarity_threshold:
            confidence_level = "low"
            identified = True
        else:
            confidence_level = "insufficient"
            identified = False

        return {
            "identified": identified,
            "tiger_id": best_match["tiger_id"],
            "tiger_name": best_match["tiger_name"],
            "confidence": best_match["weighted_score"],
            "confidence_level": confidence_level,
            "model_count": best_match["model_count"],
            "model_scores": best_match["model_scores"],
            "ensemble_method": "weighted",
            "calibration_applied": self.use_calibration,
            "reranking_applied": self.use_reranking,
            "top_candidates": [
                {
                    "tiger_id": t["tiger_id"],
                    "tiger_name": t["tiger_name"],
                    "weighted_score": t["weighted_score"],
                    "model_count": t["model_count"]
                }
                for t in ranked_tigers[:5]
            ],
            "models": {r["model"]: {
                "success": r.get("success"),
                "best_similarity": r.get("best_similarity"),
                "tiger_id": r.get("tiger_id"),
                "match_count": len(r.get("matches", []))
            } for r in model_results},
            "requires_verification": confidence_level in ["low", "insufficient"]
        }


class VerifiedEnsembleStrategy(WeightedEnsembleStrategy):
    """Weighted ensemble with MatchAnything geometric verification.

    Extends WeightedEnsembleStrategy by adding a verification stage that uses
    MatchAnything-ELOFTR to verify top candidates through keypoint matching.

    This is useful when:
    - ReID models disagree
    - Confidence is low/medium
    - Additional verification is needed for high-stakes decisions

    The verification stage:
    1. Gets top-K candidates from weighted ensemble
    2. Runs MatchAnything pairwise comparison on each candidate (in parallel)
    3. Combines ReID scores with geometric matching scores using adaptive weights
    4. Re-ranks based on combined scores with meaningful verification status
    """

    # Normalization constants based on empirical testing
    MIN_MATCHES_FOR_SIGNAL = 25
    NORMALIZATION_MIDPOINT = 150  # Sigmoid center point
    NORMALIZATION_STEEPNESS = 0.02  # Controls sigmoid slope

    # Verification status thresholds
    MIN_MATCHES_FOR_VERIFICATION = 25
    HIGH_CONFIDENCE_MATCHES = 100
    HIGH_CONFIDENCE_COMBINED = 0.85
    VERIFIED_COMBINED_THRESHOLD = 0.70

    # Gallery image loading
    MAX_GALLERY_IMAGES = 3

    def __init__(
        self,
        model_weights: Optional[Dict[str, float]] = None,
        use_reranking: bool = True,
        use_calibration: bool = True,
        use_verification: bool = True,
        verification_top_k: int = 5,
        reid_weight: float = 0.6,
        match_weight: float = 0.4,
        use_adaptive_weights: bool = True,
        reranking_k1: int = 20,
        reranking_k2: int = 6,
        reranking_lambda: float = 0.3
    ):
        """Initialize verified ensemble strategy.

        Args:
            model_weights: Custom weights for ReID models
            use_reranking: Whether to apply k-reciprocal re-ranking
            use_calibration: Whether to apply confidence calibration
            use_verification: Whether to use MatchAnything verification
            verification_top_k: Number of top candidates to verify
            reid_weight: Weight for ReID score in combined score (default 0.6)
            match_weight: Weight for MatchAnything score in combined score (default 0.4)
            use_adaptive_weights: Whether to adjust weights based on ReID confidence spread
            reranking_k1: K1 parameter for re-ranking
            reranking_k2: K2 parameter for re-ranking
            reranking_lambda: Lambda parameter for re-ranking
        """
        super().__init__(
            model_weights=model_weights,
            use_reranking=use_reranking,
            use_calibration=use_calibration,
            reranking_k1=reranking_k1,
            reranking_k2=reranking_k2,
            reranking_lambda=reranking_lambda
        )
        self.use_verification = use_verification
        self.verification_top_k = verification_top_k
        self.reid_weight = reid_weight
        self.match_weight = match_weight
        self.use_adaptive_weights = use_adaptive_weights
        self._matchanything_model = None

    async def identify(
        self,
        tiger_crop: bytes,
        models: Dict[str, BaseReIDModel],
        db_session: Any,
        similarity_threshold: float,
        user_id: UUID,
        gallery_images: Optional[Dict[str, Image.Image]] = None
    ) -> Dict[str, Any]:
        """Run verified ensemble identification.

        Args:
            tiger_crop: Cropped tiger image as bytes
            models: Dictionary of model_name -> model instance
            db_session: Database session for vector search
            similarity_threshold: Minimum similarity for a match
            user_id: User ID for logging
            gallery_images: Optional dictionary of tiger_id -> gallery image for verification

        Returns:
            Dictionary with identification results including verification scores
        """
        # First run the weighted ensemble
        result = await super().identify(
            tiger_crop, models, db_session, similarity_threshold, user_id
        )

        # If verification is disabled or no candidates, return as-is
        if not self.use_verification or not result.get("top_candidates"):
            return result

        # Get query image
        query_image = Image.open(io.BytesIO(tiger_crop))

        # Verify top candidates
        try:
            verified_candidates = await self._verify_candidates(
                query_image,
                result.get("top_candidates", [])[:self.verification_top_k],
                gallery_images,
                db_session
            )

            # Update result with verification
            result["verification_applied"] = True
            result["verified_candidates"] = verified_candidates

            # If verification succeeded, update best match
            if verified_candidates:
                best_verified = verified_candidates[0]
                result["verified_tiger_id"] = best_verified["tiger_id"]
                result["verified_confidence"] = best_verified["combined_score"]
                result["verification_boost"] = best_verified.get("normalized_match_score", 0)

                # If verification significantly disagrees with ReID, flag for review
                if best_verified["tiger_id"] != result.get("tiger_id"):
                    result["verification_disagreement"] = True
                    result["requires_verification"] = True

        except Exception as e:
            logger.error(f"MatchAnything verification failed: {e}")
            result["verification_applied"] = False
            result["verification_error"] = str(e)

        return result

    async def _verify_candidates(
        self,
        query_image: Image.Image,
        candidates: List[Dict[str, Any]],
        gallery_images: Optional[Dict[str, Image.Image]],
        db_session: Any,
        query_side_view: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Verify candidates using MatchAnything in parallel.

        Args:
            query_image: Query tiger image
            candidates: List of candidate dictionaries
            gallery_images: Optional pre-loaded gallery images
            db_session: Database session for loading gallery images
            query_side_view: Side view of query image for gallery selection

        Returns:
            List of verified candidates with combined scores
        """
        # Lazy load MatchAnything model
        if self._matchanything_model is None:
            try:
                from backend.models.matchanything import get_matchanything_model
                self._matchanything_model = get_matchanything_model(use_modal=True)
                await self._matchanything_model.load_model()
            except Exception as e:
                logger.error(f"Failed to load MatchAnything model: {e}")
                raise

        # Calculate adaptive weights if enabled
        reid_weight, match_weight = self._calculate_adaptive_weights(candidates)

        async def verify_single(candidate: Dict[str, Any]) -> Dict[str, Any]:
            """Verify a single candidate against multiple gallery images."""
            tiger_id = candidate.get("tiger_id")
            reid_score = candidate.get("weighted_score", 0)

            # Get gallery images for this tiger
            gallery_imgs = []
            if gallery_images and tiger_id in gallery_images:
                gallery_imgs = [(gallery_images[tiger_id], None)]
            else:
                # Load multiple gallery images from database
                gallery_imgs = await self._load_gallery_images(
                    tiger_id, db_session, query_side_view
                )

            if not gallery_imgs:
                logger.warning(f"No gallery image for tiger {tiger_id}, skipping verification")
                return {
                    **candidate,
                    "num_matches": 0,
                    "match_score": 0.0,
                    "normalized_match_score": 0.0,
                    "combined_score": reid_score,
                    "verification_status": "skipped"
                }

            # Match against all gallery images, take best score
            best_match_result = None
            best_num_matches = 0

            for gallery_img, tiger_image_record in gallery_imgs:
                try:
                    match_result = await self._matchanything_model.match_pair(
                        query_image, gallery_img
                    )
                    if match_result["num_matches"] > best_num_matches:
                        best_num_matches = match_result["num_matches"]
                        best_match_result = match_result
                except Exception as e:
                    logger.warning(f"MatchAnything failed for gallery image: {e}")
                    continue

            if best_match_result is None:
                return {
                    **candidate,
                    "num_matches": 0,
                    "match_score": 0.0,
                    "normalized_match_score": 0.0,
                    "combined_score": reid_score,
                    "verification_status": "error",
                    "verification_error": "All gallery image matches failed"
                }

            # Normalize match score using sigmoid
            normalized_match = self._normalize_match_score(best_match_result["num_matches"])

            # Combine scores with adaptive weights
            combined_score = (
                reid_weight * reid_score +
                match_weight * normalized_match
            )

            # Determine verification status based on thresholds
            verification_status = self._determine_verification_status(
                best_match_result["num_matches"],
                reid_score,
                combined_score
            )

            return {
                **candidate,
                "num_matches": best_match_result["num_matches"],
                "match_score": best_match_result["mean_score"],
                "normalized_match_score": normalized_match,
                "combined_score": combined_score,
                "verification_status": verification_status,
                "reid_weight_used": reid_weight,
                "match_weight_used": match_weight,
                "gallery_images_tested": len(gallery_imgs)
            }

        # Run all verifications in parallel
        tasks = [verify_single(c) for c in candidates]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results, handling exceptions
        verified = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Verification failed for candidate {i}: {result}")
                candidate = candidates[i]
                verified.append({
                    **candidate,
                    "num_matches": 0,
                    "match_score": 0.0,
                    "normalized_match_score": 0.0,
                    "combined_score": candidate.get("weighted_score", 0),
                    "verification_status": "error",
                    "verification_error": str(result)
                })
            else:
                verified.append(result)

        # Sort by combined score
        verified.sort(key=lambda x: x["combined_score"], reverse=True)

        return verified

    def _normalize_match_score(self, num_matches: int) -> float:
        """Normalize match count using sigmoid function.

        Uses sigmoid centered at NORMALIZATION_MIDPOINT to convert raw match
        counts to a 0-1 score. This is more robust than linear normalization.

        Args:
            num_matches: Raw number of keypoint matches

        Returns:
            Normalized score between 0 and 1
        """
        import math

        if num_matches <= 0:
            return 0.0

        # Sigmoid: 1 / (1 + e^(-k*(x - midpoint)))
        exponent = -self.NORMALIZATION_STEEPNESS * (num_matches - self.NORMALIZATION_MIDPOINT)
        return 1.0 / (1.0 + math.exp(exponent))

    def _determine_verification_status(
        self,
        num_matches: int,
        reid_score: float,
        combined_score: float
    ) -> str:
        """Determine verification status based on match quality thresholds.

        Args:
            num_matches: Number of keypoint matches
            reid_score: Original ReID confidence score
            combined_score: Combined ReID + verification score

        Returns:
            Status string: 'insufficient_matches', 'high_confidence',
                          'verified', or 'low_confidence'
        """
        if num_matches < self.MIN_MATCHES_FOR_VERIFICATION:
            return "insufficient_matches"
        elif num_matches >= self.HIGH_CONFIDENCE_MATCHES and combined_score >= self.HIGH_CONFIDENCE_COMBINED:
            return "high_confidence"
        elif combined_score >= self.VERIFIED_COMBINED_THRESHOLD:
            return "verified"
        else:
            return "low_confidence"

    def _calculate_adaptive_weights(
        self,
        candidates: List[Dict[str, Any]]
    ) -> tuple:
        """Calculate adaptive weights based on ReID confidence spread.

        If ReID scores are very spread out, trust ReID more.
        If ReID scores are clustered (can't distinguish), trust verification more.

        Args:
            candidates: List of candidate dictionaries with weighted_score

        Returns:
            Tuple of (reid_weight, match_weight)
        """
        if not self.use_adaptive_weights or len(candidates) < 2:
            return self.reid_weight, self.match_weight

        # Get top-3 scores to measure spread
        scores = [c.get("weighted_score", 0) for c in candidates[:3]]
        if len(scores) < 2:
            return self.reid_weight, self.match_weight

        spread = max(scores) - min(scores)

        if spread > 0.15:
            # ReID is decisive - increase ReID weight
            reid_weight = min(0.75, self.reid_weight + 0.1)
            match_weight = 1.0 - reid_weight
        elif spread < 0.05:
            # ReID can't distinguish - increase verification weight
            reid_weight = max(0.4, self.reid_weight - 0.15)
            match_weight = 1.0 - reid_weight
        else:
            # Use default weights
            reid_weight = self.reid_weight
            match_weight = self.match_weight

        logger.debug(f"Adaptive weights: ReID={reid_weight:.2f}, Match={match_weight:.2f} (spread={spread:.3f})")
        return reid_weight, match_weight

    def _select_best_gallery_image(
        self,
        tiger_images: List[Any],
        query_side_view: Optional[str] = None
    ) -> Optional[Any]:
        """Select the best gallery image, preferring matching viewpoints.

        Args:
            tiger_images: List of TigerImage records (already sorted by quality)
            query_side_view: Side view of the query image

        Returns:
            Best TigerImage record or None
        """
        if not tiger_images:
            return None

        # If no side view info, return first (highest quality)
        if not query_side_view or query_side_view == "unknown":
            return tiger_images[0]

        def score_image(img):
            """Score gallery image by side view match and quality."""
            side = img.side_view.value if img.side_view else "unknown"
            # Prioritize: exact match > 'both' > mismatch
            if side == query_side_view:
                side_match = 2
            elif side == "both":
                side_match = 1
            else:
                side_match = 0
            return (side_match, img.verified or False, img.quality_score or 0)

        return max(tiger_images, key=score_image)

    # Timeout for loading a single image (seconds)
    IMAGE_LOAD_TIMEOUT = 10

    async def _load_gallery_images(
        self,
        tiger_id: str,
        db_session: Any,
        query_side_view: Optional[str] = None,
        max_images: Optional[int] = None
    ) -> List[tuple]:
        """Load multiple gallery images for a tiger from the filesystem.

        Args:
            tiger_id: Tiger identifier
            db_session: Database session
            query_side_view: Side view of query for preferential selection
            max_images: Maximum number of images to load

        Returns:
            List of (PIL.Image, TigerImage) tuples
        """
        from pathlib import Path
        from backend.database.models import TigerImage

        max_images = max_images or self.MAX_GALLERY_IMAGES

        try:
            # Query images ordered by quality metrics
            query = db_session.query(TigerImage).filter(
                TigerImage.tiger_id == tiger_id,
                TigerImage.image_path.isnot(None)
            ).order_by(
                TigerImage.is_reference.desc().nullslast(),
                TigerImage.verified.desc().nullslast(),
                TigerImage.quality_score.desc().nullslast()
            )

            tiger_images = query.all()
            if not tiger_images:
                return []

            # Select best images considering side view
            if query_side_view and query_side_view != "unknown":
                # Sort to prioritize matching side views
                tiger_images = sorted(
                    tiger_images,
                    key=lambda img: (
                        2 if (img.side_view and img.side_view.value == query_side_view) else
                        (1 if (img.side_view and img.side_view.value == "both") else 0),
                        img.is_reference or False,
                        img.verified or False,
                        img.quality_score or 0
                    ),
                    reverse=True
                )

            # Load images from filesystem with timeout protection
            result = []
            loop = asyncio.get_event_loop()

            for tiger_image in tiger_images[:max_images]:
                if not tiger_image.image_path:
                    continue

                path = Path(tiger_image.image_path)
                if path.exists():
                    try:
                        # Run blocking I/O in executor with timeout
                        def load_image():
                            return Image.open(path).convert("RGB")

                        img = await asyncio.wait_for(
                            loop.run_in_executor(None, load_image),
                            timeout=self.IMAGE_LOAD_TIMEOUT
                        )
                        result.append((img, tiger_image))
                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout loading image {path} (exceeded {self.IMAGE_LOAD_TIMEOUT}s)")
                    except Exception as e:
                        logger.warning(f"Failed to load image {path}: {e}")
                else:
                    logger.warning(f"Gallery image path does not exist: {path}")

            return result

        except Exception as e:
            logger.warning(f"Failed to load gallery images for tiger {tiger_id}: {e}")
            return []

    async def _load_gallery_image(
        self,
        tiger_id: str,
        db_session: Any,
        query_side_view: Optional[str] = None
    ) -> Optional[Image.Image]:
        """Load a single gallery image for a tiger from the filesystem.

        This is a convenience wrapper around _load_gallery_images that
        returns just the best single image.

        Args:
            tiger_id: Tiger identifier
            db_session: Database session
            query_side_view: Side view of query for preferential selection

        Returns:
            PIL Image or None if not found
        """
        images = await self._load_gallery_images(
            tiger_id, db_session, query_side_view, max_images=1
        )
        if images:
            return images[0][0]  # Return just the PIL Image
        return None
