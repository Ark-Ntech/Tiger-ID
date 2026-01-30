"""Abstract base class for Re-ID models.

All tiger re-identification models must implement this interface
to ensure consistent behavior across different model backends.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
import numpy as np
from PIL import Image


class BaseReIDModel(ABC):
    """Abstract base class for Re-ID (Re-Identification) models.

    This interface defines the contract for all tiger re-identification models,
    whether they run locally, on Modal, or any other backend.

    Attributes:
        embedding_dim: Dimension of the embedding vectors produced by this model
        model_name: Human-readable name of the model
        similarity_threshold: Default similarity threshold for matching
    """

    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """Get the embedding dimension for this model.

        Returns:
            Integer dimension of embedding vectors (e.g., 2048, 3072)
        """
        pass

    @property
    def model_name(self) -> str:
        """Get the model name.

        Returns:
            Human-readable model name
        """
        return self.__class__.__name__

    @property
    def similarity_threshold(self) -> float:
        """Get the default similarity threshold.

        Returns:
            Default threshold for considering a match (0.0 to 1.0)
        """
        return 0.8

    @abstractmethod
    async def load_model(self) -> None:
        """Load the model weights and prepare for inference.

        This method should be idempotent - calling it multiple times
        should not cause issues.

        For Modal-backed models, this may be a no-op since the model
        is loaded on the remote container.
        """
        pass

    @abstractmethod
    async def generate_embedding(self, image: Image.Image) -> np.ndarray:
        """Generate an embedding vector for a PIL Image.

        Args:
            image: PIL Image object containing a tiger

        Returns:
            Normalized embedding vector as numpy array

        Raises:
            RuntimeError: If embedding generation fails
        """
        pass

    async def generate_embedding_from_bytes(self, image_bytes: bytes) -> np.ndarray:
        """Generate an embedding vector from image bytes.

        This is a convenience method that converts bytes to PIL Image
        and delegates to generate_embedding.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Normalized embedding vector as numpy array

        Raises:
            RuntimeError: If embedding generation fails
        """
        import io
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return await self.generate_embedding(image)

    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Ensure embeddings are 1D
        if embedding1.ndim > 1:
            embedding1 = embedding1.flatten()
        if embedding2.ndim > 1:
            embedding2 = embedding2.flatten()

        # Compute cosine similarity
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(similarity)

    def normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """Normalize an embedding to unit length.

        Args:
            embedding: Embedding vector

        Returns:
            Normalized embedding vector
        """
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return embedding
        return embedding / norm

    def identify(
        self,
        query_embedding: np.ndarray,
        database_embeddings: List[np.ndarray],
        database_labels: List[str],
        k: int = 1,
        threshold: Optional[float] = None
    ) -> Tuple[Optional[str], float, List[Tuple[str, float]]]:
        """Identify a query against a database of embeddings.

        Args:
            query_embedding: Query embedding vector
            database_embeddings: List of database embedding vectors
            database_labels: Labels corresponding to database embeddings
            k: Number of top matches to return
            threshold: Minimum similarity threshold (uses default if None)

        Returns:
            Tuple of:
                - Best matching label (or None if no match above threshold)
                - Best similarity score
                - List of top-k (label, score) tuples
        """
        if len(database_embeddings) != len(database_labels):
            raise ValueError("Embeddings and labels must have same length")

        threshold = threshold or self.similarity_threshold

        # Compute similarities
        similarities = [
            (label, self.compute_similarity(query_embedding, db_emb))
            for label, db_emb in zip(database_labels, database_embeddings)
        ]

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Get top-k
        top_k = similarities[:k]

        # Determine best match
        if top_k and top_k[0][1] >= threshold:
            return top_k[0][0], top_k[0][1], top_k
        else:
            return None, top_k[0][1] if top_k else 0.0, top_k

    async def batch_generate_embeddings(
        self,
        images: List[Image.Image]
    ) -> List[np.ndarray]:
        """Generate embeddings for multiple images.

        Default implementation processes images sequentially.
        Subclasses may override for batch optimization.

        Args:
            images: List of PIL Image objects

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for image in images:
            embedding = await self.generate_embedding(image)
            embeddings.append(embedding)
        return embeddings
