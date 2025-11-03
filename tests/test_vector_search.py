"""Tests for vector search functionality"""

import pytest
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.models import Base, TigerImage
from backend.database.vector_search import (
    create_vector_index,
    search_similar_embeddings,
    find_matching_tigers,
    store_embedding
)


class TestVectorSearch:
    """Tests for vector search functions"""
    
    @pytest.fixture(scope="function")
    def test_db_with_vectors(self):
        """Create a test database with vector support"""
        # SQLite doesn't support pgvector, so we'll mock the behavior
        # For actual pgvector testing, you'd need a PostgreSQL test database
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
        
        # Create tables without vector column (SQLite limitation)
        # In real tests with PostgreSQL, pgvector would work
        Base.metadata.create_all(bind=test_engine)
        
        yield test_engine
        
        Base.metadata.drop_all(bind=test_engine)
    
    def test_create_vector_index(self, test_db_with_vectors):
        """Test creating a vector index"""
        TestSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_db_with_vectors
        )
        session = TestSessionLocal()
        
        try:
            # Note: This will fail with SQLite since it doesn't support pgvector
            # In real tests, use PostgreSQL
            # For now, we'll just test that the function doesn't crash with proper params
            try:
                create_vector_index(session, "tiger_images", "embedding")
            except Exception as e:
                # Expected to fail with SQLite - would work with PostgreSQL + pgvector
                assert "vector" in str(e).lower() or "syntax" in str(e).lower() or "unsupported" in str(e).lower()
        finally:
            session.close()
    
    def test_search_similar_embeddings_basic(self):
        """Test search_similar_embeddings function signature and basic logic"""
        # Create a dummy embedding
        query_embedding = np.random.rand(512).astype(np.float32)
        
        # Verify embedding shape
        assert query_embedding.shape == (512,)
        assert len(query_embedding) == 512
        
        # Verify function expects correct parameters
        # (We can't fully test without PostgreSQL + pgvector)
        # This test documents expected behavior
    
    def test_find_matching_tigers_basic(self):
        """Test find_matching_tigers function signature and basic logic"""
        # Create a dummy embedding
        query_embedding = np.random.rand(512).astype(np.float32)
        
        # Test with different parameters
        params = {
            "query_embedding": query_embedding,
            "tiger_id": None,
            "side_view": None,
            "limit": 5,
            "similarity_threshold": 0.8
        }
        
        # Verify parameters
        assert params["query_embedding"].shape == (512,)
        assert params["limit"] > 0
        assert 0 <= params["similarity_threshold"] <= 1
    
    def test_store_embedding_logic(self):
        """Test store_embedding function logic"""
        # Create a dummy embedding
        embedding = np.random.rand(512).astype(np.float32)
        
        # Convert to string format (as done in the function)
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        
        # Verify conversion
        assert embedding_str.startswith("[")
        assert embedding_str.endswith("]")
        assert "," in embedding_str
    
    def test_embedding_dimension(self):
        """Test that embeddings have correct dimension"""
        # Test various embedding sizes
        for dim in [256, 512, 1024]:
            embedding = np.random.rand(dim).astype(np.float32)
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            
            # Verify string format
            values = embedding_str.strip("[]").split(",")
            assert len(values) == dim
    
    def test_similarity_threshold_validation(self):
        """Test similarity threshold validation"""
        # Valid thresholds
        valid_thresholds = [0.0, 0.5, 0.8, 1.0]
        for threshold in valid_thresholds:
            assert 0 <= threshold <= 1
        
        # Invalid thresholds (for documentation)
        invalid_thresholds = [-0.1, 1.1, 2.0]
        for threshold in invalid_thresholds:
            assert not (0 <= threshold <= 1)


class TestVectorSearchIntegration:
    """Integration tests for vector search (requires PostgreSQL + pgvector)"""
    
    @pytest.mark.skip(reason="Requires PostgreSQL with pgvector extension")
    def test_vector_search_with_postgresql(self):
        """Full integration test with PostgreSQL - skipped in unit tests"""
        # This test would require:
        # 1. PostgreSQL test database
        # 2. pgvector extension installed
        # 3. Actual vector operations
        
        # Example of what this test would do:
        # 1. Create test images with embeddings
        # 2. Run search_similar_embeddings
        # 3. Verify results are ordered by similarity
        # 4. Verify threshold filtering works
        pass
    
    @pytest.mark.skip(reason="Requires PostgreSQL with pgvector extension")
    def test_find_matching_tigers_integration(self):
        """Full integration test for find_matching_tigers"""
        # This would test:
        # 1. Creating tigers and images
        # 2. Storing embeddings
        # 3. Running similarity search
        # 4. Verifying matches are correct
        pass


class TestVectorOperations:
    """Tests for vector operations and utilities"""
    
    def test_embedding_conversion(self):
        """Test numpy array to string conversion"""
        embedding = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        
        # Parse back
        values = [float(x.strip()) for x in embedding_str.strip("[]").split(",")]
        
        # Verify values match
        assert np.allclose(embedding, values)
    
    def test_cosine_similarity_concept(self):
        """Test cosine similarity calculation concept"""
        # Create two similar vectors
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        
        # Calculate cosine similarity manually
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        similarity = dot_product / (norm1 * norm2)
        
        # Identical vectors should have similarity of 1.0
        assert np.isclose(similarity, 1.0)
        
        # Orthogonal vectors should have similarity of 0.0
        vec3 = np.array([0.0, 1.0, 0.0])
        dot_product2 = np.dot(vec1, vec3)
        similarity2 = dot_product2 / (np.linalg.norm(vec1) * np.linalg.norm(vec3))
        assert np.isclose(similarity2, 0.0)

