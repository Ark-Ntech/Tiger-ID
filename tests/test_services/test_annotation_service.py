"""Tests for AnnotationService"""

import pytest
from uuid import uuid4
from datetime import datetime

from backend.services.annotation_service import AnnotationService
from backend.database.models import InvestigationAnnotation


class TestAnnotationService:
    """Tests for AnnotationService"""
    
    def test_create_annotation(self, db_session, sample_user_id):
        """Test creating an annotation"""
        service = AnnotationService(db_session)
        investigation_id = uuid4()
        
        annotation = service.create_annotation(
            investigation_id=investigation_id,
            user_id=sample_user_id,
            annotation_type="comment",
            notes="Test annotation"
        )
        
        assert annotation.investigation_id == investigation_id
        assert annotation.user_id == sample_user_id
        assert annotation.annotation_type == "comment"
        assert annotation.notes == "Test annotation"
    
    def test_create_annotation_with_evidence(self, db_session, sample_user_id):
        """Test creating annotation with evidence ID"""
        service = AnnotationService(db_session)
        investigation_id = uuid4()
        evidence_id = uuid4()
        
        annotation = service.create_annotation(
            investigation_id=investigation_id,
            user_id=sample_user_id,
            annotation_type="highlight",
            evidence_id=evidence_id,
            notes="Evidence annotation"
        )
        
        assert annotation.evidence_id == evidence_id
    
    def test_create_annotation_with_coordinates(self, db_session, sample_user_id):
        """Test creating annotation with coordinates"""
        service = AnnotationService(db_session)
        investigation_id = uuid4()
        
        coordinates = {"x": 100, "y": 200, "width": 50, "height": 50}
        
        annotation = service.create_annotation(
            investigation_id=investigation_id,
            user_id=sample_user_id,
            annotation_type="marker",
            coordinates=coordinates
        )
        
        assert annotation.coordinates == coordinates
    
    def test_get_annotation(self, db_session, sample_user_id):
        """Test getting annotation by ID"""
        service = AnnotationService(db_session)
        investigation_id = uuid4()
        
        created = service.create_annotation(
            investigation_id=investigation_id,
            user_id=sample_user_id,
            annotation_type="comment",
            notes="Test"
        )
        
        retrieved = service.get_annotation(created.annotation_id)
        
        assert retrieved is not None
        assert retrieved.annotation_id == created.annotation_id
        assert retrieved.notes == "Test"
    
    def test_get_annotations_filtered(self, db_session, sample_user_id):
        """Test getting annotations with filters"""
        service = AnnotationService(db_session)
        investigation_id = uuid4()
        
        # Create multiple annotations
        service.create_annotation(
            investigation_id=investigation_id,
            user_id=sample_user_id,
            annotation_type="comment",
            notes="Comment 1"
        )
        service.create_annotation(
            investigation_id=investigation_id,
            user_id=sample_user_id,
            annotation_type="highlight",
            notes="Highlight 1"
        )
        
        # Filter by type
        comments = service.get_annotations(
            investigation_id=investigation_id,
            annotation_type="comment"
        )
        
        assert len(comments) >= 1
        assert all(a.annotation_type == "comment" for a in comments)
    
    def test_update_annotation(self, db_session, sample_user_id):
        """Test updating annotation"""
        service = AnnotationService(db_session)
        investigation_id = uuid4()
        
        annotation = service.create_annotation(
            investigation_id=investigation_id,
            user_id=sample_user_id,
            annotation_type="comment",
            notes="Original notes"
        )
        
        updated = service.update_annotation(
            annotation.annotation_id,
            notes="Updated notes"
        )
        
        assert updated is not None
        assert updated.notes == "Updated notes"
    
    def test_delete_annotation(self, db_session, sample_user_id):
        """Test deleting annotation"""
        service = AnnotationService(db_session)
        investigation_id = uuid4()
        
        annotation = service.create_annotation(
            investigation_id=investigation_id,
            user_id=sample_user_id,
            annotation_type="comment",
            notes="To be deleted"
        )
        
        annotation_id = annotation.annotation_id
        
        result = service.delete_annotation(annotation_id)
        
        assert result is True
        
        # Verify deleted
        retrieved = service.get_annotation(annotation_id)
        assert retrieved is None
    
    def test_get_annotations_by_evidence(self, db_session, sample_user_id):
        """Test getting annotations for specific evidence"""
        service = AnnotationService(db_session)
        investigation_id = uuid4()
        evidence_id = uuid4()
        
        # Create annotation with evidence
        service.create_annotation(
            investigation_id=investigation_id,
            user_id=sample_user_id,
            annotation_type="comment",
            evidence_id=evidence_id,
            notes="Evidence comment"
        )
        
        annotations = service.get_annotations(evidence_id=evidence_id)
        
        assert len(annotations) >= 1
        assert all(a.evidence_id == evidence_id for a in annotations)

