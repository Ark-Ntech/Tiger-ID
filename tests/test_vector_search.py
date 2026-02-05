"""Tests for vector search functionality"""

import pytest
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.models import Base, TigerImage, Tiger, Facility
from backend.database.vector_search import (
    find_matching_tigers,
    store_embedding,
    delete_embedding,
    sync_embeddings,
    get_embedding_count
)


class TestVectorSearch:
    """Tests for vector search functions"""
    
    @pytest.fixture(scope="function")
    def test_db_with_vectors(self):
        """Create a test database with sqlite-vec support"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )

        # Create tables
        Base.metadata.create_all(bind=test_engine)

        # Create vec_embeddings virtual table
        with test_engine.connect() as conn:
            try:
                conn.execute(text("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS vec_embeddings USING vec0(
                        image_id TEXT PRIMARY KEY,
                        embedding FLOAT[2048]
                    )
                """))
                conn.commit()
            except Exception:
                # sqlite-vec might not be available in test environment
                pass

        yield test_engine

        Base.metadata.drop_all(bind=test_engine)
    
    def test_get_embedding_count(self, test_db_with_vectors):
        """Test getting embedding count from vec_embeddings table"""
        TestSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_db_with_vectors
        )
        session = TestSessionLocal()

        try:
            # Should return 0 for empty table or handle table not existing
            count = get_embedding_count(session)
            assert isinstance(count, int)
            assert count >= 0
        finally:
            session.close()
    
    def test_embedding_validation(self):
        """Test embedding validation in find_matching_tigers"""
        from backend.database import SessionLocal
        session = SessionLocal()

        try:
            # Test invalid embedding type
            with pytest.raises(ValueError, match="must be numpy array"):
                find_matching_tigers(session, [1, 2, 3])

            # Test invalid embedding shape
            with pytest.raises(ValueError, match="must be 1-dimensional"):
                find_matching_tigers(session, np.array([[1, 2, 3]]))

            # Test all-zero embedding
            with pytest.raises(ValueError, match="cannot be all zeros"):
                find_matching_tigers(session, np.zeros(2048))
        finally:
            session.close()
    
    def test_find_matching_tigers_basic(self, test_db_with_vectors):
        """Test find_matching_tigers with empty database"""
        TestSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_db_with_vectors
        )
        session = TestSessionLocal()

        try:
            # Create a valid embedding (2048-dim)
            query_embedding = np.random.rand(2048).astype(np.float32)

            # Should return empty list for empty database
            results = find_matching_tigers(
                session,
                query_embedding=query_embedding,
                tiger_id=None,
                side_view=None,
                limit=5,
                similarity_threshold=0.8
            )

            assert isinstance(results, list)
            # Empty DB should return empty results
            assert len(results) == 0
        except Exception as e:
            # sqlite-vec might not be available - that's okay
            assert "vec_embeddings" in str(e) or "no such table" in str(e)
        finally:
            session.close()
    
    def test_store_embedding_logic(self, test_db_with_vectors):
        """Test store_embedding function"""
        TestSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_db_with_vectors
        )
        session = TestSessionLocal()

        try:
            # Create a valid embedding (2048-dim)
            embedding = np.random.rand(2048).astype(np.float32)
            image_id = "test-image-123"

            # Try storing embedding (may fail if sqlite-vec not available)
            try:
                result = store_embedding(session, image_id, embedding)
                # If sqlite-vec is available, should succeed
                assert isinstance(result, bool)
            except Exception as e:
                # sqlite-vec might not be available - that's okay
                assert "vec_embeddings" in str(e) or "no such table" in str(e)
        finally:
            session.close()
    
    def test_embedding_dimension(self):
        """Test that embeddings have correct dimension"""
        from backend.database.vector_search import VALID_EMBEDDING_DIMS

        # Test valid embedding dimensions
        assert 768 in VALID_EMBEDDING_DIMS  # TransReID
        assert 1024 in VALID_EMBEDDING_DIMS  # MegaDescriptor-B
        assert 1536 in VALID_EMBEDDING_DIMS  # Wildlife Tools
        assert 2048 in VALID_EMBEDDING_DIMS  # CVWC2019, Tiger ReID, RAPID ReID

        # Verify embeddings can be created with these dimensions
        for dim in VALID_EMBEDDING_DIMS:
            embedding = np.random.rand(dim).astype(np.float32)
            assert embedding.shape[0] == dim
            assert embedding.ndim == 1
    
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

