"""Tests for annotation routes"""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# python-jose is now properly installed in requirements.txt

from backend.api.app import create_app
from backend.database.models import User


class TestAnnotationRoutes:
    """Tests for annotation API routes"""
    
    def test_create_annotation(self, test_client, auth_headers, test_user, db_session):
        """Test creating an annotation"""
        from backend.services.investigation_service import InvestigationService
        
        # Create investigation first
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=test_user.user_id
        )
        
        response = test_client.post(
            "/api/v1/annotations",
            headers=auth_headers,
            json={
                "investigation_id": str(investigation.investigation_id),
                "annotation_type": "comment",
                "notes": "Test annotation"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["annotation_type"] == "comment"
        assert data["notes"] == "Test annotation"
    
    def test_get_annotations(self, test_client, auth_headers, test_user, db_session):
        """Test getting annotations"""
        from backend.services.investigation_service import InvestigationService
        from backend.services.annotation_service import AnnotationService
        
        # Create investigation and annotation
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=test_user.user_id
        )
        
        annotation_service = AnnotationService(db_session)
        annotation_service.create_annotation(
            investigation_id=investigation.investigation_id,
            user_id=test_user.user_id,
            annotation_type="comment",
            notes="Test"
        )
        
        response = test_client.get(
            f"/api/v1/annotations?investigation_id={investigation.investigation_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict) or isinstance(data, list)
    
    def test_update_annotation(self, test_client, auth_headers, test_user, db_session):
        """Test updating an annotation"""
        from backend.services.investigation_service import InvestigationService
        from backend.services.annotation_service import AnnotationService
        
        # Create investigation and annotation
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=test_user.user_id
        )
        
        annotation_service = AnnotationService(db_session)
        annotation = annotation_service.create_annotation(
            investigation_id=investigation.investigation_id,
            user_id=test_user.user_id,
            annotation_type="comment",
            notes="Original notes"
        )
        
        response = test_client.put(
            f"/api/v1/annotations/{annotation.annotation_id}",
            headers=auth_headers,
            json={"notes": "Updated notes"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes"
    
    def test_delete_annotation(self, test_client, auth_headers, test_user, db_session):
        """Test deleting an annotation"""
        from backend.services.investigation_service import InvestigationService
        from backend.services.annotation_service import AnnotationService
        
        # Create investigation and annotation
        inv_service = InvestigationService(db_session)
        investigation = inv_service.create_investigation(
            title="Test Investigation",
            created_by=test_user.user_id
        )
        
        annotation_service = AnnotationService(db_session)
        annotation = annotation_service.create_annotation(
            investigation_id=investigation.investigation_id,
            user_id=test_user.user_id,
            annotation_type="comment",
            notes="To be deleted"
        )
        
        response = test_client.delete(
            f"/api/v1/annotations/{annotation.annotation_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200

