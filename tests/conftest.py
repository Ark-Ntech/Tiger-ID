"""Pytest configuration and fixtures for Tiger ID tests"""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import Mock

# Import models and connection utilities
from backend.database.models import Base
from backend.database import SessionLocal, engine


@pytest.fixture(scope="function")
def test_db():
    """Create a test database in memory"""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    yield test_engine
    
    # Cleanup
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """Create a database session for testing"""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db)
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def sample_user_id():
    """Generate a sample user ID for testing"""
    return uuid.uuid4()


@pytest.fixture
def sample_tiger_id():
    """Generate a sample tiger ID for testing"""
    return uuid.uuid4()


@pytest.fixture
def sample_facility_id():
    """Generate a sample facility ID for testing"""
    return uuid.uuid4()


@pytest.fixture
def sample_investigation_id():
    """Generate a sample investigation ID for testing"""
    return uuid.uuid4()


@pytest.fixture
def sample_image_id():
    """Generate a sample image ID for testing"""
    return uuid.uuid4()


@pytest.fixture
def test_client(db_session):
    """Create a FastAPI test client"""
    from backend.api.app import create_app
    from unittest.mock import patch

    # Mock audit middleware to prevent PostgreSQL connection attempts
    with patch('backend.api.app.AuditMiddleware') as mock_audit:
        # Make the middleware a no-op that just calls the next handler
        async def passthrough_middleware(request, call_next):
            return await call_next(request)

        mock_audit.return_value = passthrough_middleware

        app = create_app()

    # Override the get_db dependency to use test database
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    from backend.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    # Remove middleware that cause issues in tests
    app.user_middleware = []  # Clear middleware stack

    client = TestClient(app)
    yield client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database"""
    from backend.database.models import User
    from backend.auth.auth import hash_password
    
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpass"),  # Shorter password to avoid bcrypt 72-byte limit
        role="investigator",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers for testing"""
    from backend.auth.auth import create_access_token
    from datetime import timedelta
    
    # Convert role enum to string for JWT serialization
    role_value = test_user.role.value if hasattr(test_user.role, 'value') else str(test_user.role)
    
    # Create a test token for the real test user
    token = create_access_token(
        data={"sub": test_user.username, "role": role_value},
        expires_delta=timedelta(hours=1)
    )
    
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Agent Fixtures for Langgraph/Orchestrator Tests
# ============================================================================

@pytest.fixture
def mock_research_agent():
    """Mock ResearchAgent without heavyweight dependencies"""
    from unittest.mock import AsyncMock, Mock
    
    agent = Mock()
    agent.research = AsyncMock(return_value={
        "findings": ["Test finding 1", "Test finding 2"],
        "sources": ["Source 1", "Source 2"],
        "confidence": 0.85,
        "completed": True
    })
    agent.close = AsyncMock(return_value=None)
    agent.db = Mock()
    agent.tiger_service = None
    
    return agent


@pytest.fixture
def mock_analysis_agent():
    """Mock AnalysisAgent without heavyweight dependencies"""
    from unittest.mock import AsyncMock, Mock
    
    agent = Mock()
    agent.analyze = AsyncMock(return_value={
        "analysis": "Test analysis results",
        "risk_level": "medium",
        "indicators": ["Indicator 1", "Indicator 2"],
        "confidence": 0.78,
        "completed": True
    })
    agent.close = AsyncMock(return_value=None)
    agent.db = Mock()
    
    return agent


@pytest.fixture
def mock_validation_agent():
    """Mock ValidationAgent without heavyweight dependencies"""
    from unittest.mock import AsyncMock, Mock
    
    agent = Mock()
    agent.validate = AsyncMock(return_value={
        "validation_status": "verified",
        "issues": [],
        "recommendations": ["Recommendation 1"],
        "confidence": 0.92,
        "completed": True
    })
    agent.close = AsyncMock(return_value=None)
    agent.db = Mock()
    
    return agent


@pytest.fixture
def mock_reporting_agent():
    """Mock ReportingAgent without heavyweight dependencies"""
    from unittest.mock import AsyncMock, Mock
    
    agent = Mock()
    agent.generate_report = AsyncMock(return_value={
        "report_content": "Test investigation report",
        "summary": "Test summary",
        "sections": ["Introduction", "Findings", "Conclusion"],
        "completed": True
    })
    agent.close = AsyncMock(return_value=None)
    agent.db = Mock()
    
    return agent


# ============================================================================
# Service Fixtures for Langgraph/Orchestrator Tests
# ============================================================================

@pytest.fixture
def mock_investigation_service():
    """Mock InvestigationService with typical operations"""
    from unittest.mock import Mock, AsyncMock
    
    service = Mock()
    service.add_investigation_step = Mock(return_value=None)
    service.update_investigation_status = Mock(return_value=None)
    service.get_investigation = Mock(return_value=Mock(
        investigation_id=uuid.uuid4(),
        title="Test Investigation",
        status="running"
    ))
    
    return service


@pytest.fixture
def mock_event_service():
    """Mock event service"""
    from unittest.mock import AsyncMock, Mock
    
    service = Mock()
    service.emit = AsyncMock(return_value=None)
    service.subscribe = Mock(return_value=None)
    
    return service


@pytest.fixture
def mock_notification_service():
    """Mock notification service"""
    from unittest.mock import Mock
    
    service = Mock()
    service.create_notification = Mock(return_value=None)
    service.send_notification = Mock(return_value=None)
    
    return service


@pytest.fixture
def mock_mcp_servers():
    """Mock all MCP servers (Firecrawl, Database, TigerID, YouTube, Meta)"""
    from unittest.mock import Mock, AsyncMock

    servers = Mock()

    # Firecrawl Server
    servers.firecrawl = Mock()
    servers.firecrawl.crawl = AsyncMock(return_value={"content": "Test content"})
    servers.firecrawl.call_tool = AsyncMock(return_value={"content": "Test content"})
    servers.firecrawl.client = Mock()
    servers.firecrawl.client.aclose = AsyncMock(return_value=None)

    # Database Server
    servers.database = Mock()
    servers.database.query_tigers = AsyncMock(return_value={"tigers": []})
    servers.database.call_tool = AsyncMock(return_value={"tigers": []})
    servers.database.client = None  # No client to close

    # TigerID Server
    servers.tiger_id = Mock()
    servers.tiger_id.identify = AsyncMock(return_value={"tiger_id": str(uuid.uuid4())})
    servers.tiger_id.call_tool = AsyncMock(return_value={"tiger_id": str(uuid.uuid4())})
    servers.tiger_id.client = None  # No client to close

    # YouTube Server
    servers.youtube = Mock()
    servers.youtube.search = AsyncMock(return_value={"videos": []})
    servers.youtube.call_tool = AsyncMock(return_value={"videos": []})
    servers.youtube.client = None  # No client to close

    # Meta Server
    servers.meta = Mock()
    servers.meta.search = AsyncMock(return_value={"posts": []})
    servers.meta.call_tool = AsyncMock(return_value={"posts": []})
    servers.meta.client = None  # No client to close

    return servers


@pytest.fixture
def authenticated_client(test_client, test_user, auth_headers):
    """Create an authenticated test client with headers pre-set"""
    # Set default headers for authenticated requests
    test_client.headers.update(auth_headers)
    return test_client


@pytest.fixture
def mock_deep_research():
    """Mock deep research service for discovery routes"""
    from unittest.mock import AsyncMock, MagicMock

    service = MagicMock()
    service.research = AsyncMock(return_value={
        "findings": [],
        "confidence": 0.8
    })
    return service


@pytest.fixture
def mock_discovery_scheduler():
    """Mock discovery scheduler for discovery routes"""
    from unittest.mock import AsyncMock, MagicMock

    scheduler = MagicMock()
    scheduler.get_status = MagicMock(return_value={
        "is_running": True,
        "current_facility": "Zoo A",
        "progress": 0.5
    })
    scheduler.start = AsyncMock()
    scheduler.stop = AsyncMock()
    scheduler.get_queue = MagicMock(return_value=[])
    return scheduler


@pytest.fixture
def mock_facility_crawler():
    """Mock facility crawler for discovery routes"""
    from unittest.mock import AsyncMock, MagicMock

    crawler = MagicMock()
    crawler.crawl_facility = AsyncMock(return_value={
        "images_found": 10,
        "new_tigers": 3
    })
    crawler.get_crawl_history = MagicMock(return_value=[])
    return crawler


@pytest.fixture
def client(test_client):
    """Create an unauthenticated test client (alias for test_client for backward compatibility)"""
    return test_client

