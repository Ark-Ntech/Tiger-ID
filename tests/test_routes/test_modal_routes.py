"""Tests for Modal routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_modal_client():
    """Create mock Modal client."""
    client = MagicMock()
    client.get_status = AsyncMock(return_value={
        "healthy": True,
        "models_loaded": ["wildlife_tools", "cvwc2019_reid"]
    })
    client.list_models = MagicMock(return_value=[
        {"name": "wildlife_tools", "status": "ready"},
        {"name": "cvwc2019_reid", "status": "ready"}
    ])
    client.get_queue_status = MagicMock(return_value={
        "pending": 5,
        "processing": 2,
        "completed": 100
    })
    return client


@pytest.fixture
def mock_model_registry():
    """Create mock model registry."""
    registry = MagicMock()
    registry.get_all_models = MagicMock(return_value=[
        {"id": "wildlife_tools", "name": "Wildlife Tools", "weight": 0.40},
        {"id": "cvwc2019_reid", "name": "CVWC2019", "weight": 0.30}
    ])
    registry.get_model = MagicMock(return_value={
        "id": "wildlife_tools",
        "name": "Wildlife Tools",
        "weight": 0.40,
        "embedding_dim": 1536
    })
    return registry


class TestModalStatus:
    """Tests for Modal status endpoint."""

    def test_get_modal_status(self, authenticated_client, mock_modal_client):
        """Test getting Modal status."""
        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.get("/api/modal/status")

            assert response.status_code == 200
            data = response.json()
            assert "healthy" in data

    def test_get_modal_status_unhealthy(self, authenticated_client, mock_modal_client):
        """Test getting unhealthy Modal status."""
        mock_modal_client.get_status.return_value = {
            "healthy": False,
            "error": "Connection timeout"
        }

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.get("/api/modal/status")

            assert response.status_code == 200
            data = response.json()
            assert data["healthy"] is False

    def test_get_modal_status_connection_error(self, authenticated_client, mock_modal_client):
        """Test Modal status when connection fails."""
        mock_modal_client.get_status.side_effect = Exception("Connection refused")

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.get("/api/modal/status")

            assert response.status_code in [500, 503]


class TestModalModels:
    """Tests for Modal models endpoint."""

    def test_list_models(self, authenticated_client, mock_modal_client):
        """Test listing available models."""
        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.get("/api/modal/models")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "wildlife_tools"

    def test_get_model_details(self, authenticated_client, mock_model_registry):
        """Test getting model details."""
        with patch('backend.api.modal_routes.model_registry', mock_model_registry):
            response = authenticated_client.get("/api/modal/models/wildlife_tools")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "wildlife_tools"
            assert data["weight"] == 0.40

    def test_get_model_not_found(self, authenticated_client, mock_model_registry):
        """Test getting non-existent model."""
        mock_model_registry.get_model.return_value = None

        with patch('backend.api.modal_routes.model_registry', mock_model_registry):
            response = authenticated_client.get("/api/modal/models/non_existent")

            assert response.status_code == 404


class TestModalQueue:
    """Tests for Modal queue endpoints."""

    def test_get_queue_status(self, authenticated_client, mock_modal_client):
        """Test getting queue status."""
        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.get("/api/modal/queue")

            assert response.status_code == 200
            data = response.json()
            assert data["pending"] == 5
            assert data["processing"] == 2

    def test_get_queue_items(self, authenticated_client, mock_modal_client):
        """Test getting queue items."""
        mock_modal_client.get_queue_items = MagicMock(return_value=[
            {"id": "task_1", "model": "wildlife_tools", "status": "pending"},
            {"id": "task_2", "model": "cvwc2019_reid", "status": "processing"}
        ])

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.get("/api/modal/queue/items")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

    def test_clear_queue(self, authenticated_client, mock_modal_client):
        """Test clearing the queue."""
        mock_modal_client.clear_queue = AsyncMock()

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.post("/api/modal/queue/clear")

            assert response.status_code == 200
            mock_modal_client.clear_queue.assert_called_once()

    def test_cancel_queue_item(self, authenticated_client, mock_modal_client):
        """Test canceling a queue item."""
        mock_modal_client.cancel_task = AsyncMock(return_value=True)

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.delete("/api/modal/queue/task_123")

            assert response.status_code == 200


class TestModalInference:
    """Tests for Modal inference endpoints."""

    def test_run_inference(self, authenticated_client, mock_modal_client):
        """Test running inference."""
        mock_modal_client.run_inference = AsyncMock(return_value={
            "embeddings": [[0.1] * 1536],
            "processing_time": 0.5
        })

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.post(
                "/api/modal/inference",
                json={
                    "model": "wildlife_tools",
                    "image_data": "base64_encoded_image"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "embeddings" in data

    def test_run_inference_invalid_model(self, authenticated_client, mock_modal_client):
        """Test inference with invalid model."""
        mock_modal_client.run_inference = AsyncMock(
            side_effect=ValueError("Unknown model: invalid")
        )

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.post(
                "/api/modal/inference",
                json={
                    "model": "invalid",
                    "image_data": "base64_encoded_image"
                }
            )

            assert response.status_code in [400, 500]

    def test_run_batch_inference(self, authenticated_client, mock_modal_client):
        """Test running batch inference."""
        mock_modal_client.run_batch_inference = AsyncMock(return_value={
            "results": [
                {"embeddings": [[0.1] * 1536]},
                {"embeddings": [[0.2] * 1536]}
            ],
            "processing_time": 1.2
        })

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.post(
                "/api/modal/inference/batch",
                json={
                    "model": "wildlife_tools",
                    "images": ["image1_base64", "image2_base64"]
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 2


class TestModalHealth:
    """Tests for Modal health endpoints."""

    def test_health_check(self, authenticated_client, mock_modal_client):
        """Test health check."""
        mock_modal_client.health_check = AsyncMock(return_value=True)

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.get("/api/modal/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    def test_health_check_unhealthy(self, authenticated_client, mock_modal_client):
        """Test health check when unhealthy."""
        mock_modal_client.health_check = AsyncMock(return_value=False)

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.get("/api/modal/health")

            assert response.status_code in [200, 503]

    def test_warmup_models(self, authenticated_client, mock_modal_client):
        """Test warming up models."""
        mock_modal_client.warmup = AsyncMock()

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.post("/api/modal/warmup")

            assert response.status_code == 200
            mock_modal_client.warmup.assert_called_once()

    def test_warmup_specific_model(self, authenticated_client, mock_modal_client):
        """Test warming up specific model."""
        mock_modal_client.warmup_model = AsyncMock()

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.post(
                "/api/modal/warmup/wildlife_tools"
            )

            assert response.status_code == 200


class TestModalMetrics:
    """Tests for Modal metrics endpoints."""

    def test_get_metrics(self, authenticated_client, mock_modal_client):
        """Test getting Modal metrics."""
        mock_modal_client.get_metrics = MagicMock(return_value={
            "total_inferences": 1000,
            "average_latency_ms": 150,
            "error_rate": 0.02,
            "gpu_utilization": 0.75
        })

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.get("/api/modal/metrics")

            assert response.status_code == 200
            data = response.json()
            assert data["total_inferences"] == 1000

    def test_get_model_metrics(self, authenticated_client, mock_modal_client):
        """Test getting metrics for specific model."""
        mock_modal_client.get_model_metrics = MagicMock(return_value={
            "model": "wildlife_tools",
            "inferences": 500,
            "average_latency_ms": 120
        })

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.get("/api/modal/metrics/wildlife_tools")

            assert response.status_code == 200
            data = response.json()
            assert data["model"] == "wildlife_tools"


class TestModalConfiguration:
    """Tests for Modal configuration endpoints."""

    def test_get_config(self, authenticated_client):
        """Test getting Modal configuration."""
        with patch('backend.api.modal_routes.get_modal_config') as mock_config:
            mock_config.return_value = {
                "workspace": "ark-ntech",
                "app_name": "tiger-id-models",
                "gpu_type": "T4"
            }

            response = authenticated_client.get("/api/modal/config")

            assert response.status_code == 200
            data = response.json()
            assert data["workspace"] == "ark-ntech"

    def test_update_config(self, authenticated_client):
        """Test updating Modal configuration."""
        with patch('backend.api.modal_routes.update_modal_config') as mock_update:
            mock_update.return_value = True

            response = authenticated_client.patch(
                "/api/modal/config",
                json={"gpu_type": "A10G"}
            )

            assert response.status_code == 200

    def test_update_config_invalid(self, authenticated_client):
        """Test updating with invalid configuration."""
        with patch('backend.api.modal_routes.update_modal_config') as mock_update:
            mock_update.side_effect = ValueError("Invalid GPU type")

            response = authenticated_client.patch(
                "/api/modal/config",
                json={"gpu_type": "invalid"}
            )

            assert response.status_code in [400, 500]


class TestModalDeployment:
    """Tests for Modal deployment endpoints."""

    def test_get_deployment_status(self, authenticated_client, mock_modal_client):
        """Test getting deployment status."""
        mock_modal_client.get_deployment_status = MagicMock(return_value={
            "deployed": True,
            "version": "1.2.3",
            "last_deployed": "2024-01-01T12:00:00Z"
        })

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.get("/api/modal/deployment")

            assert response.status_code == 200
            data = response.json()
            assert data["deployed"] is True

    def test_trigger_deployment(self, authenticated_client, mock_modal_client):
        """Test triggering deployment."""
        mock_modal_client.deploy = AsyncMock(return_value={
            "success": True,
            "deployment_id": "dep_123"
        })

        with patch('backend.api.modal_routes.modal_client', mock_modal_client):
            response = authenticated_client.post("/api/modal/deploy")

            assert response.status_code == 200
