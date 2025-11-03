"""Vector similarity search functions using pgvector"""

from typing import List, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session
from pgvector.sqlalchemy import Vector
import numpy as np

from backend.database.models import TigerImage, Base


def create_vector_index(session: Session, table_name: str = "tiger_images", column_name: str = "embedding"):
    """Create HNSW index for vector similarity search"""
    index_name = f"idx_{table_name}_{column_name}_hnsw"
    
    # Drop index if exists
    session.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
    
    # Create HNSW index
    session.execute(text(
        f"""
        CREATE INDEX {index_name}
        ON {table_name} USING hnsw ({column_name} vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    ))
    session.commit()


def search_similar_embeddings(
    session: Session,
    query_embedding: np.ndarray,
    table_name: str = "tiger_images",
    limit: int = 10,
    similarity_threshold: float = 0.8
) -> List[Tuple[str, float, Optional[str]]]:
    """
    Search for similar embeddings using cosine similarity
    
    Args:
        session: Database session
        query_embedding: Query embedding vector (numpy array)
        table_name: Table name to search
        limit: Maximum number of results
        similarity_threshold: Minimum similarity score
    
    Returns:
        List of (image_id, similarity_score, tiger_id) tuples
    """
    # Convert numpy array to PostgreSQL vector format
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
    
    query = text(f"""
        SELECT image_id, tiger_id, 
               1 - (embedding <=> :query_embedding::vector) AS similarity
        FROM {table_name}
        WHERE embedding IS NOT NULL
          AND 1 - (embedding <=> :query_embedding::vector) >= :threshold
        ORDER BY embedding <=> :query_embedding::vector
        LIMIT :limit
    """)
    
    results = session.execute(
        query,
        {
            "query_embedding": embedding_str,
            "threshold": similarity_threshold,
            "limit": limit
        }
    )
    
    return [(str(row.image_id), row.similarity, str(row.tiger_id) if row.tiger_id else None) 
            for row in results]


def find_matching_tigers(
    session: Session,
    query_embedding: np.ndarray,
    tiger_id: Optional[str] = None,
    side_view: Optional[str] = None,
    limit: int = 5,
    similarity_threshold: float = 0.8
) -> List[dict]:
    """
    Find matching tigers based on embedding similarity
    
    Args:
        session: Database session
        query_embedding: Query embedding vector
        tiger_id: Optional tiger_id to exclude from results
        side_view: Optional side view filter (left/right)
        limit: Maximum number of results
        similarity_threshold: Minimum similarity score
    
    Returns:
        List of matching tiger records with similarity scores
    """
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
    
    conditions = ["embedding IS NOT NULL"]
    params = {
        "query_embedding": embedding_str,
        "threshold": similarity_threshold,
        "limit": limit
    }
    
    if tiger_id:
        conditions.append("tiger_id != :tiger_id")
        params["tiger_id"] = tiger_id
    
    if side_view:
        conditions.append("side_view IN (:side_view, 'both', 'unknown')")
        params["side_view"] = side_view
    
    where_clause = " AND ".join(conditions)
    
    query = text(f"""
        SELECT 
            ti.image_id,
            ti.tiger_id,
            ti.image_path,
            ti.side_view,
            t.name as tiger_name,
            t.alias as tiger_alias,
            1 - (ti.embedding <=> :query_embedding::vector) AS similarity
        FROM tiger_images ti
        LEFT JOIN tigers t ON ti.tiger_id = t.tiger_id
        WHERE {where_clause}
          AND 1 - (ti.embedding <=> :query_embedding::vector) >= :threshold
        ORDER BY ti.embedding <=> :query_embedding::vector
        LIMIT :limit
    """)
    
    results = session.execute(query, params)
    
    return [
        {
            "image_id": str(row.image_id),
            "tiger_id": str(row.tiger_id) if row.tiger_id else None,
            "tiger_name": row.tiger_name,
            "tiger_alias": row.tiger_alias,
            "image_path": row.image_path,
            "side_view": row.side_view,
            "similarity": float(row.similarity)
        }
        for row in results
    ]


def store_embedding(
    session: Session,
    image_id: str,
    embedding: np.ndarray
) -> bool:
    """
    Store embedding vector for an image
    
    Args:
        session: Database session
        image_id: Image UUID
        embedding: Embedding vector (numpy array)
    
    Returns:
        True if successful
    """
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
    
    query = text("""
        UPDATE tiger_images
        SET embedding = :embedding::vector
        WHERE image_id = :image_id
    """)
    
    session.execute(
        query,
        {
            "image_id": image_id,
            "embedding": embedding_str
        }
    )
    session.commit()
    
    return True

