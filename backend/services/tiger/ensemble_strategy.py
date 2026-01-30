"""Ensemble strategies for tiger re-identification.

This module provides different strategies for combining results from
multiple ReID models to improve identification accuracy.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from uuid import UUID
import asyncio
from PIL import Image
import io

from backend.utils.logging import get_logger
from backend.database.vector_search import find_matching_tigers
from backend.models.interfaces.base_reid_model import BaseReIDModel

logger = get_logger(__name__)


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
