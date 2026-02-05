"""Tests for tiger identification API routes."""

import pytest
from io import BytesIO
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from uuid import uuid4

from backend.database.models import Base, User, UserRole, Tiger, TigerImage, TigerStatus
from backend.auth.auth import hash_password, create_access_token
from datetime import timedelta


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a database session for testing."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_client(db_session):
    """Create a FastAPI test client."""
    from backend.api.app import create_app

    with patch('backend.api.app.AuditMiddleware'):
        app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    from backend.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    app.user_middleware = []

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("TestPass123!"),
        role=UserRole.investigator.value,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers."""
    token = create_access_token(
        data={"sub": test_user.username, "role": test_user.role},
        expires_delta=timedelta(hours=1)
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_tiger(db_session):
    """Create a sample tiger in the database."""
    tiger = Tiger(
        name="Test Tiger",
        alias="TT001",
        status=TigerStatus.active.value,
        is_reference=False
    )
    db_session.add(tiger)
    db_session.commit()
    db_session.refresh(tiger)
    return tiger


@pytest.fixture
def sample_tiger_image(db_session, sample_tiger):
    """Create a sample tiger image."""
    image = TigerImage(
        tiger_id=sample_tiger.tiger_id,
        image_path="data/storage/test_image.jpg",
        verified=True,
        is_reference=False
    )
    db_session.add(image)
    db_session.commit()
    db_session.refresh(image)
    return image


@pytest.fixture
def mock_image():
    """Create a mock image file."""
    # Create a minimal valid JPEG image (1x1 pixel)
    jpeg_bytes = (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
        b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
        b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9teletext<teletext:\x1c'
        b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
        b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
        b'\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}'
        b'\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1'
        b'\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZ'
        b'cdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a'
        b'\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4'
        b'\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6'
        b'\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa'
        b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd5\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\xff\xd9'
    )
    return BytesIO(jpeg_bytes)


class TestIdentifyTiger:
    """Tests for tiger identification endpoint."""

    @patch('backend.services.factory.ServiceFactory')
    def test_identify_tiger_success(self, mock_factory_class, test_client, auth_headers, mock_image):
        """Test successful tiger identification."""
        # Create mock tiger service
        mock_tiger_service = Mock()
        mock_tiger_service.identify_tiger_from_image = AsyncMock(return_value={
            "matches": [
                {"tiger_id": str(uuid4()), "confidence": 0.95, "name": "Test Tiger"}
            ],
            "processing_time": 1.5
        })
        mock_tiger_service.get_available_models = Mock(return_value=["wildlife_tools", "cvwc2019_reid"])

        # Create mock factory that returns the mock tiger service
        mock_factory = Mock()
        mock_factory.get_tiger_service = Mock(return_value=mock_tiger_service)
        mock_factory_class.return_value = mock_factory

        response = test_client.post(
            "/api/v1/tigers/identify",
            files={"image": ("tiger.jpg", mock_image, "image/jpeg")},
            data={"similarity_threshold": "0.8"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_identify_tiger_no_auth(self, test_client, mock_image):
        """Test identification without authentication."""
        response = test_client.post(
            "/api/v1/tigers/identify",
            files={"image": ("tiger.jpg", mock_image, "image/jpeg")}
        )

        assert response.status_code in [401, 403]

    @patch('backend.services.tiger_service.TigerService')
    def test_identify_tiger_invalid_file_type(self, mock_service_class, test_client, auth_headers):
        """Test identification with invalid file type."""
        text_file = BytesIO(b"This is not an image")

        response = test_client.post(
            "/api/v1/tigers/identify",
            files={"image": ("text.txt", text_file, "text/plain")},
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    @patch('backend.services.tiger_service.TigerService')
    def test_identify_tiger_invalid_threshold(self, mock_service_class, test_client, auth_headers, mock_image):
        """Test identification with invalid similarity threshold."""
        response = test_client.post(
            "/api/v1/tigers/identify",
            files={"image": ("tiger.jpg", mock_image, "image/jpeg")},
            data={"similarity_threshold": "1.5"},  # Out of range
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "similarity_threshold" in response.json()["detail"]

    @patch('backend.services.tiger_service.TigerService')
    def test_identify_tiger_invalid_model(self, mock_service_class, test_client, auth_headers, mock_image):
        """Test identification with invalid model name."""
        mock_service = Mock()
        mock_service.get_available_models = Mock(return_value=["wildlife_tools", "cvwc2019_reid"])
        mock_service_class.return_value = mock_service

        response = test_client.post(
            "/api/v1/tigers/identify",
            files={"image": ("tiger.jpg", mock_image, "image/jpeg")},
            data={"model_name": "nonexistent_model"},
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "not available" in response.json()["detail"]

    @patch('backend.services.tiger_service.TigerService')
    def test_identify_tiger_invalid_ensemble_mode(self, mock_service_class, test_client, auth_headers, mock_image):
        """Test identification with invalid ensemble mode."""
        mock_service = Mock()
        mock_service.get_available_models = Mock(return_value=["wildlife_tools"])
        mock_service_class.return_value = mock_service

        response = test_client.post(
            "/api/v1/tigers/identify",
            files={"image": ("tiger.jpg", mock_image, "image/jpeg")},
            data={"ensemble_mode": "invalid_mode"},
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "Invalid ensemble_mode" in response.json()["detail"]


class TestIdentifyTigersBatch:
    """Tests for batch tiger identification endpoint."""

    @patch('backend.services.tiger_service.TigerService')
    def test_batch_identify_success(self, mock_service_class, test_client, auth_headers, mock_image):
        """Test successful batch identification."""
        mock_service = Mock()
        mock_service.identify_tigers_batch = AsyncMock(return_value=[
            {"tiger_id": str(uuid4()), "confidence": 0.95}
        ])
        mock_service.get_available_models = Mock(return_value=["wildlife_tools"])
        mock_service_class.return_value = mock_service

        # Create multiple mock images
        mock_image.seek(0)
        images = [("images", ("tiger1.jpg", mock_image, "image/jpeg"))]

        response = test_client.post(
            "/api/v1/tigers/identify/batch",
            files=images,
            data={"similarity_threshold": "0.8"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_batch_identify_no_images(self, test_client, auth_headers):
        """Test batch identification with no images."""
        response = test_client.post(
            "/api/v1/tigers/identify/batch",
            data={"similarity_threshold": "0.8"},
            headers=auth_headers
        )

        # Should fail validation - no images provided
        assert response.status_code == 422


class TestGetTigers:
    """Tests for getting tigers list."""

    def test_get_tigers_success(self, test_client, auth_headers, sample_tiger):
        """Test getting list of tigers."""
        response = test_client.get(
            "/api/v1/tigers",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_tigers_no_auth(self, test_client):
        """Test getting tigers without authentication."""
        response = test_client.get("/api/v1/tigers")

        assert response.status_code in [401, 403]

    def test_get_tigers_pagination(self, test_client, auth_headers, db_session):
        """Test pagination of tigers list."""
        # Create multiple tigers
        for i in range(15):
            tiger = Tiger(
                name=f"Tiger {i}",
                status=TigerStatus.active.value
            )
            db_session.add(tiger)
        db_session.commit()

        # Get first page
        response = test_client.get(
            "/api/v1/tigers?page=1&page_size=5",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestGetAvailableModels:
    """Tests for getting available models endpoint."""

    @patch('backend.services.tiger_service.TigerService')
    def test_get_models_success(self, mock_service_class, test_client, auth_headers):
        """Test getting available models."""
        mock_service = Mock()
        mock_service.get_available_models = Mock(return_value=[
            "wildlife_tools", "cvwc2019_reid", "transreid"
        ])
        mock_service_class.return_value = mock_service

        response = test_client.get(
            "/api/v1/tigers/models",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "models" in data["data"]

    def test_get_models_no_auth(self, test_client):
        """Test getting models without authentication."""
        response = test_client.get("/api/v1/tigers/models")

        assert response.status_code in [401, 403]


class TestCreateTiger:
    """Tests for creating a new tiger."""

    @patch('backend.services.tiger_service.TigerService')
    def test_create_tiger_success(self, mock_service_class, test_client, auth_headers, mock_image):
        """Test successful tiger creation."""
        mock_service = Mock()
        mock_service.register_new_tiger = AsyncMock(return_value={
            "tiger_id": str(uuid4()),
            "name": "New Tiger",
            "images_count": 1
        })
        mock_service_class.return_value = mock_service

        response = test_client.post(
            "/api/v1/tigers",
            files=[("images", ("tiger.jpg", mock_image, "image/jpeg"))],
            data={"name": "New Tiger"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_create_tiger_no_auth(self, test_client, mock_image):
        """Test creating tiger without authentication."""
        response = test_client.post(
            "/api/v1/tigers",
            files=[("images", ("tiger.jpg", mock_image, "image/jpeg"))],
            data={"name": "New Tiger"}
        )

        assert response.status_code in [401, 403]

    def test_create_tiger_no_images(self, test_client, auth_headers):
        """Test creating tiger without images."""
        response = test_client.post(
            "/api/v1/tigers",
            data={"name": "New Tiger"},
            headers=auth_headers
        )

        # Should fail - no images provided
        assert response.status_code == 422


class TestGetTiger:
    """Tests for getting a specific tiger."""

    def test_get_tiger_success(self, test_client, auth_headers, sample_tiger):
        """Test getting a tiger by ID."""
        # Mock the service to avoid complex service logic
        with patch('backend.services.tiger_service.TigerService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_tiger = AsyncMock(return_value={
                "tiger_id": str(sample_tiger.tiger_id),
                "name": "Test Tiger"
            })
            mock_service_class.return_value = mock_service

            response = test_client.get(
                f"/api/v1/tigers/{sample_tiger.tiger_id}",
                headers=auth_headers
            )

            assert response.status_code == 200

    def test_get_tiger_not_found(self, test_client, auth_headers):
        """Test getting a non-existent tiger."""
        with patch('backend.services.tiger_service.TigerService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_tiger = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            response = test_client.get(
                f"/api/v1/tigers/{uuid4()}",
                headers=auth_headers
            )

            assert response.status_code == 404

    def test_get_tiger_no_auth(self, test_client, sample_tiger):
        """Test getting tiger without authentication."""
        response = test_client.get(f"/api/v1/tigers/{sample_tiger.tiger_id}")

        assert response.status_code in [401, 403]


class TestLaunchInvestigation:
    """Tests for launching investigation from tiger."""

    @patch('backend.services.tiger_service.TigerService')
    @patch('backend.services.investigation_service.InvestigationService')
    def test_launch_investigation_success(
        self, mock_inv_service_class, mock_tiger_service_class,
        test_client, auth_headers, sample_tiger
    ):
        """Test launching investigation from tiger."""
        mock_tiger_service = Mock()
        mock_tiger_service.get_tiger = AsyncMock(return_value={
            "tiger_id": str(sample_tiger.tiger_id),
            "name": "Test Tiger"
        })
        mock_tiger_service_class.return_value = mock_tiger_service

        mock_inv_service = Mock()
        mock_investigation = Mock()
        mock_investigation.investigation_id = uuid4()
        mock_investigation.related_tigers = []
        mock_inv_service.create_investigation = Mock(return_value=mock_investigation)
        mock_inv_service.launch_investigation = AsyncMock(return_value={
            "response": "Investigation launched"
        })
        mock_inv_service_class.return_value = mock_inv_service

        with patch('backend.api.mcp_tools_routes.list_mcp_tools', new=AsyncMock(return_value={"data": {}})):
            response = test_client.post(
                f"/api/v1/tigers/{sample_tiger.tiger_id}/launch-investigation",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "investigation_id" in data["data"]

    @patch('backend.services.tiger_service.TigerService')
    def test_launch_investigation_tiger_not_found(
        self, mock_tiger_service_class, test_client, auth_headers
    ):
        """Test launching investigation for non-existent tiger."""
        mock_service = Mock()
        mock_service.get_tiger = AsyncMock(return_value=None)
        mock_tiger_service_class.return_value = mock_service

        response = test_client.post(
            f"/api/v1/tigers/{uuid4()}/launch-investigation",
            headers=auth_headers
        )

        assert response.status_code == 404


class TestGetTigerImage:
    """Tests for getting tiger images."""

    def test_get_tiger_image_not_found(self, test_client, auth_headers, sample_tiger):
        """Test getting non-existent image."""
        response = test_client.get(
            f"/api/v1/tigers/{sample_tiger.tiger_id}/images/{uuid4()}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_get_tiger_image_no_auth(self, test_client, sample_tiger, sample_tiger_image):
        """Test getting image without authentication."""
        response = test_client.get(
            f"/api/v1/tigers/{sample_tiger.tiger_id}/images/{sample_tiger_image.image_id}"
        )

        assert response.status_code in [401, 403]
