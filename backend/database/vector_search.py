"""Vector similarity search using sqlite-vec

Tiger ID uses sqlite-vec extension for fast approximate nearest neighbor search
on tiger embeddings. This provides efficient vector similarity queries for
tiger re-identification.
"""

import json
import logging
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
import numpy as np

logger = logging.getLogger(__name__)

# Verify sqlite-vec is available
try:
    import sqlite_vec
    SQLITE_VEC_AVAILABLE = True
except ImportError:
    SQLITE_VEC_AVAILABLE = False
    logger.warning("sqlite-vec not installed. Vector search will use slower Python fallback.")


# Valid embedding dimensions for tiger ReID models
VALID_EMBEDDING_DIMS = {768, 1024, 1536, 2048}


def find_matching_tigers(
    session: Session,
    query_embedding: np.ndarray,
    tiger_id: Optional[str] = None,
    side_view: Optional[str] = None,
    limit: int = 5,
    similarity_threshold: float = 0.8
) -> List[dict]:
    """
    Find matching tigers based on embedding similarity using sqlite-vec.

    Args:
        session: Database session
        query_embedding: Query embedding vector (numpy array with valid dimension)
        tiger_id: Optional tiger_id to exclude from results
        side_view: Optional side view filter (left/right)
        limit: Maximum number of results
        similarity_threshold: Minimum similarity score (0-1)

    Returns:
        List of matching tiger records with similarity scores

    Raises:
        ValueError: If embedding is invalid (wrong type, shape, or all zeros)
    """
    # Validate embedding
    if not isinstance(query_embedding, np.ndarray):
        raise ValueError(f"Embedding must be numpy array, got {type(query_embedding)}")

    if query_embedding.ndim != 1:
        raise ValueError(f"Embedding must be 1-dimensional, got shape {query_embedding.shape}")

    embedding_dim = query_embedding.shape[0]
    if embedding_dim not in VALID_EMBEDDING_DIMS:
        logger.warning(
            f"Unexpected embedding dimension {embedding_dim}. "
            f"Valid dimensions are: {sorted(VALID_EMBEDDING_DIMS)}"
        )

    if np.allclose(query_embedding, 0):
        raise ValueError("Embedding cannot be all zeros")

    if SQLITE_VEC_AVAILABLE:
        try:
            return _find_matching_tigers_sqlite_vec(
                session, query_embedding, tiger_id, side_view, limit, similarity_threshold
            )
        except Exception as e:
            logger.warning(f"sqlite-vec search failed, using fallback: {e}")

    # Fallback to Python-based similarity calculation
    return _find_matching_tigers_python_fallback(
        session, query_embedding, tiger_id, side_view, limit, similarity_threshold
    )


def _find_matching_tigers_sqlite_vec(
    session: Session,
    query_embedding: np.ndarray,
    tiger_id: Optional[str] = None,
    side_view: Optional[str] = None,
    limit: int = 5,
    similarity_threshold: float = 0.8
) -> List[dict]:
    """SQLite implementation using sqlite-vec extension for fast vector search."""
    # Normalize query embedding for cosine similarity
    query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
    embedding_blob = query_norm.astype(np.float32).tobytes()

    # Build filter conditions
    conditions = []
    params = {"limit": limit * 2, "query_embedding": embedding_blob}

    if tiger_id:
        conditions.append("ti.tiger_id != :tiger_id")
        params["tiger_id"] = tiger_id

    if side_view:
        conditions.append("ti.side_view IN (:side_view, 'both', 'unknown')")
        params["side_view"] = side_view

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Query using sqlite-vec's KNN search with facility info
    # vec_distance_cosine returns distance (0 = identical, 2 = opposite)
    query = text(f"""
        SELECT
            ti.image_id,
            ti.tiger_id,
            ti.image_path,
            ti.side_view,
            t.name as tiger_name,
            t.alias as tiger_alias,
            t.last_seen_location,
            t.last_seen_date,
            f.facility_id,
            f.exhibitor_name as facility_name,
            ve.distance
        FROM vec_embeddings ve
        JOIN tiger_images ti ON ve.image_id = ti.image_id
        LEFT JOIN tigers t ON ti.tiger_id = t.tiger_id
        LEFT JOIN facilities f ON t.origin_facility_id = f.facility_id
        WHERE ve.embedding MATCH :query_embedding
          AND k = :limit
          AND {where_clause}
        ORDER BY ve.distance ASC
    """)

    results = session.execute(query, params)

    matches = []
    for row in results:
        # Convert distance to similarity (cosine distance range is 0-2)
        similarity = 1 - (row.distance / 2)

        if similarity >= similarity_threshold:
            matches.append({
                "image_id": str(row.image_id),
                "tiger_id": str(row.tiger_id) if row.tiger_id else None,
                "tiger_name": row.tiger_name,
                "tiger_alias": row.tiger_alias,
                "image_path": row.image_path,
                "side_view": row.side_view,
                "similarity": float(similarity),
                "facility_id": str(row.facility_id) if row.facility_id else None,
                "facility_name": row.facility_name,
                "last_seen_location": row.last_seen_location,
                "last_seen_date": str(row.last_seen_date) if row.last_seen_date else None
            })

    return matches[:limit]


def _find_matching_tigers_python_fallback(
    session: Session,
    query_embedding: np.ndarray,
    tiger_id: Optional[str] = None,
    side_view: Optional[str] = None,
    limit: int = 5,
    similarity_threshold: float = 0.8
) -> List[dict]:
    """Python fallback using scipy for cosine similarity (slower, O(n))."""
    from scipy.spatial.distance import cosine

    # Build WHERE conditions
    conditions = []
    params = {}

    if tiger_id:
        conditions.append("ti.tiger_id != :tiger_id")
        params["tiger_id"] = tiger_id

    if side_view:
        conditions.append("ti.side_view IN (:side_view, 'both', 'unknown')")
        params["side_view"] = side_view

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Get all embeddings from vec_embeddings table with facility info
    query = text(f"""
        SELECT
            ti.image_id,
            ti.tiger_id,
            ti.image_path,
            ti.side_view,
            t.name as tiger_name,
            t.alias as tiger_alias,
            t.last_seen_location,
            t.last_seen_date,
            f.facility_id,
            f.exhibitor_name as facility_name,
            ve.embedding
        FROM vec_embeddings ve
        JOIN tiger_images ti ON ve.image_id = ti.image_id
        LEFT JOIN tigers t ON ti.tiger_id = t.tiger_id
        LEFT JOIN facilities f ON t.origin_facility_id = f.facility_id
        WHERE {where_clause}
    """)

    results = session.execute(query, params)

    # Calculate similarity in Python
    matches = []
    for row in results:
        if not row.embedding:
            continue

        try:
            # Parse embedding from blob
            if isinstance(row.embedding, bytes):
                db_embedding = np.frombuffer(row.embedding, dtype=np.float32)
            else:
                continue

            # Ensure same shape
            if db_embedding.shape[0] != query_embedding.shape[0]:
                continue

            # Calculate cosine similarity
            cos_dist = cosine(query_embedding.flatten(), db_embedding.flatten())
            similarity = 1 - cos_dist

            if similarity >= similarity_threshold:
                matches.append({
                    "image_id": str(row.image_id),
                    "tiger_id": str(row.tiger_id) if row.tiger_id else None,
                    "tiger_name": row.tiger_name,
                    "tiger_alias": row.tiger_alias,
                    "image_path": row.image_path,
                    "side_view": row.side_view,
                    "similarity": float(similarity),
                    "facility_id": str(row.facility_id) if row.facility_id else None,
                    "facility_name": row.facility_name,
                    "last_seen_location": row.last_seen_location,
                    "last_seen_date": str(row.last_seen_date) if row.last_seen_date else None
                })

        except Exception as e:
            logger.debug(f"Skipping invalid embedding: {e}")
            continue

    # Sort by similarity (highest first) and limit
    matches.sort(key=lambda x: x["similarity"], reverse=True)
    return matches[:limit]


def store_embedding(
    session: Session,
    image_id: str,
    embedding: np.ndarray
) -> bool:
    """
    Store embedding vector for an image in sqlite-vec virtual table.

    Args:
        session: Database session
        image_id: Image UUID (string)
        embedding: Embedding vector (2048-dim numpy array)

    Returns:
        True if successful
    """
    # Normalize embedding for cosine similarity
    embedding_norm = embedding / (np.linalg.norm(embedding) + 1e-10)
    embedding_blob = embedding_norm.astype(np.float32).tobytes()

    try:
        # Insert or replace in vec_embeddings
        session.execute(
            text("""
                INSERT OR REPLACE INTO vec_embeddings(image_id, embedding)
                VALUES (:image_id, :embedding)
            """),
            {"image_id": image_id, "embedding": embedding_blob}
        )
        session.commit()
        logger.debug(f"Stored embedding for image {image_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to store embedding: {e}")
        session.rollback()
        return False


def delete_embedding(session: Session, image_id: str) -> bool:
    """
    Delete embedding for an image from sqlite-vec virtual table.

    Args:
        session: Database session
        image_id: Image UUID (string)

    Returns:
        True if successful
    """
    try:
        session.execute(
            text("DELETE FROM vec_embeddings WHERE image_id = :image_id"),
            {"image_id": image_id}
        )
        session.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to delete embedding: {e}")
        session.rollback()
        return False


def sync_embeddings(session: Session) -> int:
    """
    Sync all embeddings from tiger_images to vec_embeddings virtual table.

    This is useful when migrating data or rebuilding the vector index.

    Returns:
        Number of embeddings synced
    """
    # This function would need to read embeddings from wherever they're stored
    # and insert them into the vec_embeddings virtual table
    logger.info("Syncing embeddings to vec_embeddings table...")

    # Count existing entries
    result = session.execute(text("SELECT COUNT(*) FROM vec_embeddings")).fetchone()
    count = result[0] if result else 0

    logger.info(f"vec_embeddings contains {count} entries")
    return count


def get_embedding_count(session: Session) -> int:
    """Get the number of embeddings in the vec_embeddings table."""
    try:
        result = session.execute(text("SELECT COUNT(*) FROM vec_embeddings")).fetchone()
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Failed to count embeddings: {e}")
        return 0
