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
    
    Automatically detects database type (PostgreSQL vs SQLite) and uses appropriate method:
    - PostgreSQL: pgvector <=> operator (optimized with HNSW index)
    - SQLite: Python-based cosine similarity calculation
    
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
    import os
    import json
    from scipy.spatial.distance import cosine
    
    # Detect database type
    USE_POSTGRESQL = os.getenv("USE_POSTGRESQL", "false").lower() == "true"
    
    if USE_POSTGRESQL:
        # PostgreSQL with pgvector - use optimized vector operations
        return _find_matching_tigers_postgres(
            session, query_embedding, tiger_id, side_view, limit, similarity_threshold
        )
    else:
        # SQLite - use Python-based similarity calculation
        return _find_matching_tigers_sqlite(
            session, query_embedding, tiger_id, side_view, limit, similarity_threshold
        )


def _find_matching_tigers_postgres(
    session: Session,
    query_embedding: np.ndarray,
    tiger_id: Optional[str] = None,
    side_view: Optional[str] = None,
    limit: int = 5,
    similarity_threshold: float = 0.8
) -> List[dict]:
    """PostgreSQL implementation using pgvector <=> operator"""
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


def _find_matching_tigers_sqlite(
    session: Session,
    query_embedding: np.ndarray,
    tiger_id: Optional[str] = None,
    side_view: Optional[str] = None,
    limit: int = 5,
    similarity_threshold: float = 0.8
) -> List[dict]:
    """SQLite implementation using Python-based cosine similarity"""
    import json
    from scipy.spatial.distance import cosine
    
    # Build WHERE conditions
    conditions = ["ti.embedding IS NOT NULL"]
    params = {}
    
    if tiger_id:
        conditions.append("ti.tiger_id != :tiger_id")
        params["tiger_id"] = tiger_id
    
    if side_view:
        conditions.append("ti.side_view IN (:side_view, 'both', 'unknown')")
        params["side_view"] = side_view
    
    where_clause = " AND ".join(conditions)
    
    # Fetch all candidate embeddings from database
    query = text(f"""
        SELECT 
            ti.image_id,
            ti.tiger_id,
            ti.image_path,
            ti.side_view,
            ti.embedding,
            t.name as tiger_name,
            t.alias as tiger_alias
        FROM tiger_images ti
        LEFT JOIN tigers t ON ti.tiger_id = t.tiger_id
        WHERE {where_clause}
    """)
    
    results = session.execute(query, params)
    
    # Calculate similarity in Python
    matches = []
    for row in results:
        if not row.embedding:
            continue
        
        try:
            # Parse embedding from JSON (SQLite stores as JSON string)
            if isinstance(row.embedding, str):
                db_embedding = np.array(json.loads(row.embedding), dtype=np.float32)
            elif isinstance(row.embedding, bytes):
                # Might be stored as bytes
                db_embedding = np.frombuffer(row.embedding, dtype=np.float32)
            else:
                # Already a list/array
                db_embedding = np.array(row.embedding, dtype=np.float32)
            
            # Ensure same shape
            if db_embedding.shape != query_embedding.shape:
                continue
            
            # Calculate cosine similarity
            # Cosine distance ranges from 0 (identical) to 2 (opposite)
            # Cosine similarity = 1 - cosine_distance
            cos_dist = cosine(query_embedding.flatten(), db_embedding.flatten())
            similarity = 1 - cos_dist
            
            # Filter by threshold
            if similarity >= similarity_threshold:
                matches.append({
                    "image_id": str(row.image_id),
                    "tiger_id": str(row.tiger_id) if row.tiger_id else None,
                    "tiger_name": row.tiger_name,
                    "tiger_alias": row.tiger_alias,
                    "image_path": row.image_path,
                    "side_view": row.side_view,
                    "similarity": float(similarity)
                })
        
        except Exception as e:
            # Skip invalid embeddings
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
    Store embedding vector for an image
    
    Args:
        session: Database session
        image_id: Image UUID
        embedding: Embedding vector (numpy array)
    
    Returns:
        True if successful
    """
    import os
    import json
    
    # Check if using SQLite (embeddings stored as JSON) or PostgreSQL (vector type)
    USE_POSTGRESQL = os.getenv("USE_POSTGRESQL", "false").lower() == "true"
    
    if USE_POSTGRESQL:
        # PostgreSQL: use vector type
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
    else:
        # SQLite: store as JSON array
        embedding_list = embedding.tolist()
        embedding_json = json.dumps(embedding_list)
        query = text("""
            UPDATE tiger_images
            SET embedding = :embedding
            WHERE image_id = :image_id
        """)
        session.execute(
            query,
            {
                "image_id": image_id,
                "embedding": embedding_json
            }
        )
    
    session.commit()
    
    return True

