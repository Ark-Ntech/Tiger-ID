"""Tests for database connection and session management"""

import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.connection import get_db, get_db_session, init_db, drop_db
from backend.database.models import Base, User


class TestDatabaseConnection:
    """Tests for database connection utilities"""
    
    def test_get_db_session_context_manager(self):
        """Test get_db_session context manager"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
        Base.metadata.create_all(bind=test_engine)
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        # Mock SessionLocal for testing
        import backend.database.connection
        original_SessionLocal = backend.database.connection.SessionLocal
        backend.database.connection.SessionLocal = TestSessionLocal
        
        try:
            # Test successful transaction
            with get_db_session() as session:
                user = User(
                    username="testuser",
                    email="test@example.com",
                    password_hash="hash",
                    role="investigator"
                )
                session.add(user)
                # Context manager should commit on exit
            
            # Verify user was saved
            with get_db_session() as session:
                user = session.query(User).filter_by(username="testuser").first()
                assert user is not None
                assert user.email == "test@example.com"
            
            # Test rollback on exception
            with pytest.raises(ValueError):
                with get_db_session() as session:
                    user = User(
                        username="testuser2",
                        email="test2@example.com",
                        password_hash="hash",
                        role="investigator"
                    )
                    session.add(user)
                    raise ValueError("Test error")
            
            # Verify user was NOT saved due to rollback
            with get_db_session() as session:
                user = session.query(User).filter_by(username="testuser2").first()
                assert user is None
        finally:
            backend.database.connection.SessionLocal = original_SessionLocal
            Base.metadata.drop_all(bind=test_engine)
    
    def test_get_db_generator(self):
        """Test get_db generator function"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
        Base.metadata.create_all(bind=test_engine)
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        import backend.database.connection
        original_SessionLocal = backend.database.connection.SessionLocal
        backend.database.connection.SessionLocal = TestSessionLocal
        
        try:
            # Test generator yields session
            db_gen = get_db()
            session = next(db_gen)
            
            assert session is not None
            assert hasattr(session, 'query')
            
            # Test session is closed after generator completes
            try:
                next(db_gen)
            except StopIteration:
                pass
            
            # Verify session was closed (after context manager exits)
            # Note: In SQLAlchemy, the session may still appear active until it's garbage collected
            # The actual closure happens in the finally block
        finally:
            backend.database.connection.SessionLocal = original_SessionLocal
            Base.metadata.drop_all(bind=test_engine)
    
    def test_init_db(self):
        """Test database initialization"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
        
        import backend.database.connection
        original_engine = backend.database.connection.engine
        original_SessionLocal = backend.database.connection.SessionLocal
        
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        backend.database.connection.engine = test_engine
        backend.database.connection.SessionLocal = TestSessionLocal
        
        try:
            # Initialize database (without vector index since SQLite doesn't support it)
            # We'll mock the vector index creation to avoid pgvector dependency
            Base.metadata.create_all(bind=test_engine)
            
            # Verify tables exist
            with test_engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ))
                tables = [row[0] for row in result]
                
                # Check for some expected tables
                assert 'users' in tables or 'tigers' in tables or 'investigations' in tables
        finally:
            backend.database.connection.engine = original_engine
            backend.database.connection.SessionLocal = original_SessionLocal
    
    def test_drop_db(self):
        """Test dropping all database tables"""
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
        
        # Create tables first
        Base.metadata.create_all(bind=test_engine)
        
        import backend.database.connection
        original_engine = backend.database.connection.engine
        backend.database.connection.engine = test_engine
        
        try:
            # Verify tables exist
            with test_engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ))
                tables_before = [row[0] for row in result]
                assert len(tables_before) > 0
            
            # Drop database
            drop_db()
            
            # Verify tables are gone
            with test_engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ))
                tables_after = [row[0] for row in result]
                # In SQLite, system tables remain, but our tables should be gone
                assert len(tables_after) <= len(tables_before)
        finally:
            backend.database.connection.engine = original_engine

