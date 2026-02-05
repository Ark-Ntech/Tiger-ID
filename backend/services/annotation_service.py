"""Service for managing investigation annotations"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json

from backend.database.models import InvestigationAnnotation
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class AnnotationService:
    """Service for investigation annotations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_annotation(
        self,
        investigation_id: UUID,
        user_id: UUID,
        annotation_type: str,
        notes: Optional[str] = None,
        evidence_id: Optional[UUID] = None,
        coordinates: Optional[Dict[str, Any]] = None
    ) -> InvestigationAnnotation:
        """
        Create a new annotation
        
        Args:
            investigation_id: Investigation ID
            user_id: User ID who created annotation
            annotation_type: Type of annotation (e.g., 'highlight', 'comment', 'marker')
            notes: Annotation notes
            evidence_id: Optional evidence ID
            coordinates: Optional coordinates for image annotations
        
        Returns:
            Created annotation
        """
        annotation = InvestigationAnnotation(
            investigation_id=str(investigation_id),  # Convert UUID to string
            user_id=str(user_id),  # Convert UUID to string
            annotation_type=annotation_type,
            notes=notes,
            evidence_id=str(evidence_id) if evidence_id else None,  # Convert UUID to string
            coordinates=json.dumps(coordinates or {}),  # Serialize dict to JSON string
            created_at=datetime.utcnow()
        )
        
        self.session.add(annotation)
        self.session.commit()
        self.session.refresh(annotation)
        
        return annotation
    
    def get_annotation(self, annotation_id: UUID) -> Optional[InvestigationAnnotation]:
        """Get annotation by ID"""
        # Convert UUID to string for SQLite comparison
        annotation_id_str = str(annotation_id)
        return self.session.query(InvestigationAnnotation).filter(
            InvestigationAnnotation.annotation_id == annotation_id_str
        ).first()
    
    def get_annotations(
        self,
        investigation_id: Optional[UUID] = None,
        evidence_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        annotation_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[InvestigationAnnotation]:
        """
        Get annotations with filters
        
        Args:
            investigation_id: Filter by investigation
            evidence_id: Filter by evidence
            user_id: Filter by user
            annotation_type: Filter by type
            limit: Maximum results
            offset: Pagination offset
        
        Returns:
            List of annotations
        """
        query = self.session.query(InvestigationAnnotation)

        # Convert UUIDs to strings for SQLite comparison
        if investigation_id:
            query = query.filter(InvestigationAnnotation.investigation_id == str(investigation_id))
        if evidence_id:
            query = query.filter(InvestigationAnnotation.evidence_id == str(evidence_id))
        if user_id:
            query = query.filter(InvestigationAnnotation.user_id == str(user_id))
        if annotation_type:
            query = query.filter(InvestigationAnnotation.annotation_type == annotation_type)
        
        query = query.order_by(desc(InvestigationAnnotation.created_at))
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def update_annotation(
        self,
        annotation_id: UUID,
        notes: Optional[str] = None,
        coordinates: Optional[Dict[str, Any]] = None
    ) -> Optional[InvestigationAnnotation]:
        """Update annotation"""
        annotation = self.get_annotation(annotation_id)
        if not annotation:
            return None
        
        if notes is not None:
            annotation.notes = notes
        if coordinates is not None:
            annotation.coordinates = json.dumps(coordinates)  # Serialize dict to JSON string
        
        self.session.commit()
        self.session.refresh(annotation)
        
        return annotation
    
    def delete_annotation(self, annotation_id: UUID) -> bool:
        """Delete annotation"""
        annotation = self.get_annotation(annotation_id)
        if not annotation:
            return False
        
        self.session.delete(annotation)
        self.session.commit()
        
        return True


def get_annotation_service(session: Session) -> AnnotationService:
    """Get annotation service instance"""
    return AnnotationService(session)

