"""
K-Reciprocal Re-ranking Service for Tiger ReID.

Implements k-reciprocal encoding for re-ranking person/animal re-identification
results. Based on CVPR 2017 paper:
"Re-ranking Person Re-identification with k-reciprocal Encoding"
by Zhong et al. (https://arxiv.org/abs/1701.08398)

This improves mAP by 3-5% by using gallery-gallery relationships.
"""

import numpy as np
from typing import Optional, Tuple, List
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def k_reciprocal_rerank(
    query_features: np.ndarray,
    gallery_features: np.ndarray,
    k1: int = 20,
    k2: int = 6,
    lambda_value: float = 0.3,
    use_gpu: bool = False
) -> np.ndarray:
    """
    Re-rank using k-reciprocal nearest neighbors.

    This method improves re-identification results by considering
    gallery-gallery relationships, not just query-gallery similarity.

    Args:
        query_features: Query embeddings, shape (num_queries, embedding_dim)
        gallery_features: Gallery embeddings, shape (num_gallery, embedding_dim)
        k1: K-reciprocal nearest neighbor parameter (default: 20)
        k2: Number of neighbors for query expansion (default: 6)
        lambda_value: Weight for original distance (default: 0.3)
        use_gpu: Whether to use GPU for distance computation

    Returns:
        Re-ranked distance matrix, shape (num_queries, num_gallery)
        Lower values indicate more similar pairs.
    """
    query_num = query_features.shape[0]
    gallery_num = gallery_features.shape[0]
    all_num = query_num + gallery_num

    logger.info(f"K-reciprocal reranking: {query_num} queries, {gallery_num} gallery items")
    logger.info(f"Parameters: k1={k1}, k2={k2}, lambda={lambda_value}")

    # Concatenate query and gallery features
    all_features = np.vstack([query_features, gallery_features])

    # Compute original distance matrix (Euclidean distance squared)
    if use_gpu:
        try:
            import torch
            feat = torch.from_numpy(all_features).cuda()
            dist_sq = torch.pow(feat, 2).sum(dim=1, keepdim=True)
            distmat = dist_sq.expand(all_num, all_num) + dist_sq.t()
            distmat = distmat - 2 * torch.mm(feat, feat.t())
            original_dist = distmat.cpu().numpy()
            del feat, distmat
        except Exception as e:
            logger.warning(f"GPU computation failed, falling back to CPU: {e}")
            original_dist = _compute_euclidean_distance(all_features)
    else:
        original_dist = _compute_euclidean_distance(all_features)

    # Normalize distances
    original_dist = original_dist / np.max(original_dist, axis=0, keepdims=True)
    original_dist = original_dist.T

    # Initialize V (k-reciprocal expansion)
    V = np.zeros((all_num, all_num), dtype=np.float32)

    # Get initial ranking
    initial_rank = np.argsort(original_dist, axis=1).astype(np.int32)

    # Compute k-reciprocal neighbors for each item
    for i in range(all_num):
        # Forward k-nearest neighbors
        forward_k_neigh_index = initial_rank[i, :k1 + 1]

        # Backward k-nearest neighbors of forward neighbors
        backward_k_neigh_index = initial_rank[forward_k_neigh_index, :k1 + 1]

        # Find reciprocal neighbors (mutual k-nearest)
        fi = np.where(backward_k_neigh_index == i)[0]
        k_reciprocal_index = forward_k_neigh_index[fi]
        k_reciprocal_expansion_index = k_reciprocal_index.copy()

        # Expand k-reciprocal neighbors
        for j in range(len(k_reciprocal_index)):
            candidate = k_reciprocal_index[j]
            candidate_forward_k_neigh_index = initial_rank[candidate, :int(np.around(k1 / 2)) + 1]
            candidate_backward_k_neigh_index = initial_rank[
                candidate_forward_k_neigh_index, :int(np.around(k1 / 2)) + 1
            ]
            fi_candidate = np.where(candidate_backward_k_neigh_index == candidate)[0]
            candidate_k_reciprocal_index = candidate_forward_k_neigh_index[fi_candidate]

            # Add candidate's reciprocal neighbors if sufficient overlap
            if len(np.intersect1d(candidate_k_reciprocal_index, k_reciprocal_index)) > \
                    2 / 3 * len(candidate_k_reciprocal_index):
                k_reciprocal_expansion_index = np.append(
                    k_reciprocal_expansion_index, candidate_k_reciprocal_index
                )

        k_reciprocal_expansion_index = np.unique(k_reciprocal_expansion_index)

        # Compute Gaussian kernel weights
        weight = np.exp(-original_dist[i, k_reciprocal_expansion_index])
        V[i, k_reciprocal_expansion_index] = weight / np.sum(weight)

    # Query expansion
    if k2 != 1:
        V_qe = np.zeros_like(V, dtype=np.float32)
        for i in range(all_num):
            V_qe[i, :] = np.mean(V[initial_rank[i, :k2], :], axis=0)
        V = V_qe
        del V_qe

    del initial_rank

    # Compute Jaccard distance
    invIndex = []
    for i in range(all_num):
        invIndex.append(np.where(V[:, i] != 0)[0])

    jaccard_dist = np.zeros((query_num, all_num), dtype=np.float32)

    for i in range(query_num):
        temp_min = np.zeros((1, all_num), dtype=np.float32)
        indNonZero = np.where(V[i, :] != 0)[0]
        indImages = [invIndex[ind] for ind in indNonZero]

        for j in range(len(indNonZero)):
            temp_min[0, indImages[j]] = temp_min[0, indImages[j]] + np.minimum(
                V[i, indNonZero[j]], V[indImages[j], indNonZero[j]]
            )

        jaccard_dist[i] = 1 - temp_min / (2 - temp_min + 1e-10)

    # Final distance: combine Jaccard and original distance
    original_dist_query = original_dist[:query_num, :]
    final_dist = jaccard_dist * (1 - lambda_value) + original_dist_query * lambda_value

    # Return only query-gallery distances
    final_dist = final_dist[:, query_num:]

    # Clean up large intermediate arrays to prevent memory leaks
    del V
    del original_dist
    del original_dist_query
    del jaccard_dist
    del invIndex

    logger.info(f"Re-ranking complete. Output shape: {final_dist.shape}")

    return final_dist


def _compute_euclidean_distance(features: np.ndarray) -> np.ndarray:
    """
    Compute pairwise Euclidean distance matrix.

    Args:
        features: Feature matrix, shape (n, dim)

    Returns:
        Distance matrix, shape (n, n)
    """
    n = features.shape[0]
    dist_sq = np.sum(features ** 2, axis=1, keepdims=True)
    distmat = dist_sq + dist_sq.T - 2 * np.dot(features, features.T)
    distmat = np.maximum(distmat, 0)  # Numerical stability
    return distmat


def rerank_matches(
    query_embedding: np.ndarray,
    gallery_embeddings: np.ndarray,
    gallery_ids: List[str],
    k1: int = 20,
    k2: int = 6,
    lambda_value: float = 0.3
) -> List[Tuple[str, float]]:
    """
    Re-rank match results using k-reciprocal encoding.

    Convenience wrapper that returns similarity scores instead of distances.

    Args:
        query_embedding: Single query embedding, shape (embedding_dim,)
        gallery_embeddings: Gallery embeddings, shape (num_gallery, embedding_dim)
        gallery_ids: List of gallery tiger IDs
        k1: K-reciprocal parameter (default: 20)
        k2: Query expansion parameter (default: 6)
        lambda_value: Weight for original distance (default: 0.3)

    Returns:
        List of (tiger_id, similarity) tuples, sorted by similarity descending
    """
    if len(gallery_embeddings) == 0:
        return []

    # Ensure query is 2D
    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)

    # Compute reranked distances
    distances = k_reciprocal_rerank(
        query_embedding,
        gallery_embeddings,
        k1=k1,
        k2=k2,
        lambda_value=lambda_value
    )

    # Convert distances to similarities (inverse relationship)
    # Use exponential decay for smoother similarity scores
    similarities = np.exp(-distances[0])

    # Sort by similarity (descending)
    sorted_indices = np.argsort(-similarities)

    results = [
        (gallery_ids[idx], float(similarities[idx]))
        for idx in sorted_indices
    ]

    return results


class RerankingService:
    """Service class for re-ranking ReID results."""

    def __init__(
        self,
        k1: int = 20,
        k2: int = 6,
        lambda_value: float = 0.3,
        use_gpu: bool = False
    ):
        """
        Initialize re-ranking service.

        Args:
            k1: K-reciprocal nearest neighbor parameter
            k2: Query expansion parameter
            lambda_value: Weight for original distance vs Jaccard
            use_gpu: Whether to use GPU for distance computation
        """
        self.k1 = k1
        self.k2 = k2
        self.lambda_value = lambda_value
        self.use_gpu = use_gpu
        self.logger = get_logger(__name__)

    def rerank(
        self,
        query_features: np.ndarray,
        gallery_features: np.ndarray
    ) -> np.ndarray:
        """
        Re-rank query-gallery matches.

        Args:
            query_features: Query embeddings
            gallery_features: Gallery embeddings

        Returns:
            Re-ranked distance matrix
        """
        return k_reciprocal_rerank(
            query_features,
            gallery_features,
            k1=self.k1,
            k2=self.k2,
            lambda_value=self.lambda_value,
            use_gpu=self.use_gpu
        )

    def rerank_with_ids(
        self,
        query_embedding: np.ndarray,
        gallery_embeddings: np.ndarray,
        gallery_ids: List[str]
    ) -> List[Tuple[str, float]]:
        """
        Re-rank matches and return with IDs and similarities.

        Args:
            query_embedding: Single query embedding
            gallery_embeddings: Gallery embeddings
            gallery_ids: Gallery tiger IDs

        Returns:
            List of (tiger_id, similarity) tuples
        """
        return rerank_matches(
            query_embedding,
            gallery_embeddings,
            gallery_ids,
            k1=self.k1,
            k2=self.k2,
            lambda_value=self.lambda_value
        )
