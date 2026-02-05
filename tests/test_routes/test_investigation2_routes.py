"""Tests for Investigation 2.0 routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import io


@pytest.fixture
def mock_investigation_service():
    """Create mock investigation service."""
    service = MagicMock()
    service.create_investigation = AsyncMock(return_value={
        "id": "inv_123",
        "status": "created",
        "created_at": "2024-01-01T12:00:00Z"
    })
    service.get_investigation = MagicMock(return_value={
        "id": "inv_123",
        "status": "in_progress",
        "phase": "stripe_analysis"
    })
    service.list_investigations = MagicMock(return_value=[])
    return service


@pytest.fixture
def mock_workflow_runner():
    """Create mock workflow runner."""
    runner = MagicMock()
    runner.run = AsyncMock(return_value={
        "success": True,
        "investigation_id": "inv_123"
    })
    runner.get_status = MagicMock(return_value="running")
    return runner


@pytest.fixture
def sample_image_file():
    """Create sample image file for upload."""
    # Create a minimal valid PNG file
    png_header = b'\x89PNG\r\n\x1a\n'
    png_data = png_header + b'\x00' * 100
    return io.BytesIO(png_data)


class TestInvestigation2Launch:
    """Tests for investigation launch endpoint."""

    def test_launch_investigation(self, authenticated_client, mock_investigation_service, sample_image_file):
        """Test launching new investigation."""
        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.post(
                "/api/v1/investigations2/launch",
                files={"image": ("tiger.png", sample_image_file, "image/png")}
            )

            assert response.status_code == 200
            data = response.json()
            assert "id" in data

    def test_launch_investigation_no_image(self, authenticated_client):
        """Test launch fails without image."""
        response = authenticated_client.post("/api/v1/investigations2/launch")

        assert response.status_code == 422

    def test_launch_investigation_invalid_image(self, authenticated_client):
        """Test launch fails with invalid image."""
        invalid_file = io.BytesIO(b"not an image")

        response = authenticated_client.post(
            "/api/v1/investigations2/launch",
            files={"image": ("test.txt", invalid_file, "text/plain")}
        )

        assert response.status_code in [400, 422]

    def test_launch_investigation_with_metadata(self, authenticated_client, mock_investigation_service, sample_image_file):
        """Test launch with additional metadata."""
        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.post(
                "/api/v1/investigations2/launch",
                files={"image": ("tiger.png", sample_image_file, "image/png")},
                data={
                    "notes": "Tiger spotted near facility",
                    "source": "Field report",
                    "priority": "high"
                }
            )

            assert response.status_code == 200


class TestInvestigation2Status:
    """Tests for investigation status endpoint."""

    def test_get_investigation_status(self, authenticated_client, mock_investigation_service):
        """Test getting investigation status."""
        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.get("/api/v1/investigations2/inv_123/status")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "inv_123"
            assert "phase" in data

    def test_get_investigation_not_found(self, authenticated_client, mock_investigation_service):
        """Test getting non-existent investigation."""
        mock_investigation_service.get_investigation.return_value = None

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.get("/api/v1/investigations2/non_existent/status")

            assert response.status_code == 404

    def test_get_investigation_detailed_status(self, authenticated_client, mock_investigation_service):
        """Test getting detailed investigation status."""
        mock_investigation_service.get_investigation.return_value = {
            "id": "inv_123",
            "status": "in_progress",
            "phase": "stripe_analysis",
            "progress": 0.6,
            "phases_completed": ["upload", "detection"],
            "current_model": "wildlife_tools"
        }

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.get("/api/v1/investigations2/inv_123/status")

            assert response.status_code == 200
            data = response.json()
            assert data["progress"] == 0.6


class TestInvestigation2Results:
    """Tests for investigation results endpoint."""

    def test_get_results(self, authenticated_client, mock_investigation_service):
        """Test getting investigation results."""
        mock_investigation_service.get_results = MagicMock(return_value={
            "investigation_id": "inv_123",
            "matches": [
                {"tiger_id": "t1", "tiger_name": "Raja", "similarity": 0.92},
                {"tiger_id": "t2", "tiger_name": "Sher", "similarity": 0.85}
            ],
            "verified_candidates": [],
            "confidence": 0.88
        })

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.get("/api/v1/investigations2/inv_123/results")

            assert response.status_code == 200
            data = response.json()
            assert len(data["matches"]) == 2

    def test_get_results_not_ready(self, authenticated_client, mock_investigation_service):
        """Test getting results when not ready."""
        mock_investigation_service.get_results = MagicMock(return_value=None)
        mock_investigation_service.get_investigation.return_value = {
            "id": "inv_123",
            "status": "in_progress"
        }

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.get("/api/v1/investigations2/inv_123/results")

            # Should indicate results not ready
            assert response.status_code in [202, 404]


class TestInvestigation2Report:
    """Tests for report generation endpoint."""

    def test_generate_report(self, authenticated_client, mock_investigation_service):
        """Test generating investigation report."""
        mock_investigation_service.generate_report = AsyncMock(return_value={
            "report_id": "rep_123",
            "format": "pdf",
            "url": "/reports/rep_123.pdf"
        })

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.post(
                "/api/v1/investigations2/inv_123/report",
                json={"format": "pdf", "audience": "law_enforcement"}
            )

            assert response.status_code == 200

    def test_generate_report_multiple_formats(self, authenticated_client, mock_investigation_service):
        """Test generating reports in different formats."""
        mock_investigation_service.generate_report = AsyncMock(return_value={
            "report_id": "rep_123",
            "format": "docx"
        })

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            for format_type in ["pdf", "docx", "json"]:
                response = authenticated_client.post(
                    "/api/v1/investigations2/inv_123/report",
                    json={"format": format_type}
                )

                assert response.status_code == 200

    def test_generate_report_different_audiences(self, authenticated_client, mock_investigation_service):
        """Test generating reports for different audiences."""
        mock_investigation_service.generate_report = AsyncMock(return_value={
            "report_id": "rep_123"
        })

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            for audience in ["law_enforcement", "conservation", "internal", "public"]:
                response = authenticated_client.post(
                    "/api/v1/investigations2/inv_123/report",
                    json={"format": "pdf", "audience": audience}
                )

                assert response.status_code == 200


class TestInvestigation2List:
    """Tests for investigation list endpoint."""

    def test_list_investigations(self, authenticated_client, mock_investigation_service):
        """Test listing investigations."""
        mock_investigation_service.list_investigations.return_value = [
            {"id": "inv_1", "status": "complete", "created_at": "2024-01-01"},
            {"id": "inv_2", "status": "in_progress", "created_at": "2024-01-02"}
        ]

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.get("/api/v1/investigations2/list")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

    def test_list_investigations_with_filters(self, authenticated_client, mock_investigation_service):
        """Test listing with filters."""
        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.get(
                "/api/v1/investigations2/list",
                params={
                    "status": "complete",
                    "limit": 10,
                    "offset": 0
                }
            )

            assert response.status_code == 200

    def test_list_investigations_pagination(self, authenticated_client, mock_investigation_service):
        """Test pagination in list."""
        mock_investigation_service.list_investigations.return_value = [
            {"id": f"inv_{i}"} for i in range(10)
        ]

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.get(
                "/api/v1/investigations2/list",
                params={"limit": 5, "offset": 5}
            )

            assert response.status_code == 200


class TestInvestigation2Methodology:
    """Tests for methodology endpoint."""

    def test_get_methodology(self, authenticated_client, mock_investigation_service):
        """Test getting investigation methodology."""
        mock_investigation_service.get_methodology = MagicMock(return_value={
            "phases": [
                {"name": "upload", "status": "complete", "duration_ms": 500},
                {"name": "detection", "status": "complete", "duration_ms": 2000},
                {"name": "stripe_analysis", "status": "in_progress", "duration_ms": None}
            ],
            "models_used": ["wildlife_tools", "cvwc2019_reid"],
            "ensemble_strategy": "weighted"
        })

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.get("/api/v1/investigations2/inv_123/methodology")

            assert response.status_code == 200
            data = response.json()
            assert "phases" in data
            assert "models_used" in data


class TestInvestigation2Cancel:
    """Tests for cancel investigation endpoint."""

    def test_cancel_investigation(self, authenticated_client, mock_investigation_service):
        """Test canceling investigation."""
        mock_investigation_service.cancel = AsyncMock(return_value=True)

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.post("/api/v1/investigations2/inv_123/cancel")

            assert response.status_code == 200

    def test_cancel_completed_investigation(self, authenticated_client, mock_investigation_service):
        """Test canceling already completed investigation."""
        mock_investigation_service.cancel = AsyncMock(
            side_effect=ValueError("Cannot cancel completed investigation")
        )

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.post("/api/v1/investigations2/inv_123/cancel")

            assert response.status_code in [400, 500]


class TestInvestigation2WebSocket:
    """Tests for investigation WebSocket endpoint."""

    def test_websocket_connection_info(self, authenticated_client, mock_investigation_service):
        """Test getting WebSocket connection info."""
        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.get("/api/v1/investigations2/inv_123/ws-info")

            assert response.status_code == 200
            data = response.json()
            assert "ws_url" in data or "websocket_url" in data


class TestInvestigation2Verification:
    """Tests for verification endpoint."""

    def test_verify_match(self, authenticated_client, mock_investigation_service):
        """Test verifying a match."""
        mock_investigation_service.verify_match = AsyncMock(return_value={
            "verified": True,
            "keypoint_matches": 45,
            "confidence": 0.92
        })

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.post(
                "/api/v1/investigations2/inv_123/verify",
                json={"tiger_id": "t1"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["verified"] is True

    def test_verify_multiple_matches(self, authenticated_client, mock_investigation_service):
        """Test verifying multiple matches."""
        mock_investigation_service.verify_matches = AsyncMock(return_value=[
            {"tiger_id": "t1", "verified": True, "confidence": 0.92},
            {"tiger_id": "t2", "verified": True, "confidence": 0.85}
        ])

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.post(
                "/api/v1/investigations2/inv_123/verify-batch",
                json={"tiger_ids": ["t1", "t2"]}
            )

            assert response.status_code == 200


class TestInvestigation2ImageQuality:
    """Tests for image quality endpoint."""

    def test_get_image_quality(self, authenticated_client, mock_investigation_service):
        """Test getting image quality assessment."""
        mock_investigation_service.get_image_quality = MagicMock(return_value={
            "overall_score": 0.85,
            "resolution_score": 0.9,
            "blur_score": 0.8,
            "stripe_visibility": 0.85,
            "issues": [],
            "recommendations": []
        })

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.get("/api/v1/investigations2/inv_123/image-quality")

            assert response.status_code == 200
            data = response.json()
            assert data["overall_score"] == 0.85


class TestInvestigation2EnsembleDetails:
    """Tests for ensemble details endpoint."""

    def test_get_ensemble_details(self, authenticated_client, mock_investigation_service):
        """Test getting ensemble details."""
        mock_investigation_service.get_ensemble_details = MagicMock(return_value={
            "strategy": "weighted",
            "models": [
                {"model": "wildlife_tools", "weight": 0.40, "similarity": 0.92},
                {"model": "cvwc2019_reid", "weight": 0.30, "similarity": 0.88}
            ],
            "weighted_score": 0.90
        })

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.get(
                "/api/v1/investigations2/inv_123/ensemble",
                params={"tiger_id": "t1"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["strategy"] == "weighted"


class TestInvestigation2Delete:
    """Tests for delete investigation endpoint."""

    def test_delete_investigation(self, authenticated_client, mock_investigation_service):
        """Test deleting investigation."""
        mock_investigation_service.delete = AsyncMock(return_value=True)

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.delete("/api/v1/investigations2/inv_123")

            assert response.status_code == 200

    def test_delete_investigation_not_found(self, authenticated_client, mock_investigation_service):
        """Test deleting non-existent investigation."""
        mock_investigation_service.delete = AsyncMock(
            side_effect=ValueError("Investigation not found")
        )

        with patch('backend.api.investigation2_routes.InvestigationService', mock_investigation_service):
            response = authenticated_client.delete("/api/v1/investigations2/non_existent")

            assert response.status_code in [404, 400, 500]
