"""API routes for investigation annotations"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from backend.auth.auth import get_current_user
from backend.database import get_db, User
from backend.services.annotation_service import get_annotation_service
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/annotations", tags=["annotations"])


class AnnotationCreate(BaseModel):
    """Annotation creation model"""
    investigation_id: UUID
    annotation_type: str = Field(..., description="Type: highlight, comment, marker, etc.")
    notes: Optional[str] = None
    evidence_id: Optional[UUID] = None
    coordinates: Optional[Dict[str, Any]] = Field(None, description="Coordinates for image annotations")


class AnnotationUpdate(BaseModel):
    """Annotation update model"""
    notes: Optional[str] = None
    coordinates: Optional[Dict[str, Any]] = None


@router.post("")
async def create_annotation(
    annotation_data: AnnotationCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Create a new annotation"""
    service = get_annotation_service(db)
    annotation = service.create_annotation(
        investigation_id=annotation_data.investigation_id,
        user_id=current_user.user_id,
        annotation_type=annotation_data.annotation_type,
        notes=annotation_data.notes,
        evidence_id=annotation_data.evidence_id,
        coordinates=annotation_data.coordinates
    )
    
    return {
        "annotation_id": str(annotation.annotation_id),
        "investigation_id": str(annotation.investigation_id),
        "evidence_id": str(annotation.evidence_id) if annotation.evidence_id else None,
        "user_id": str(annotation.user_id),
        "annotation_type": annotation.annotation_type,
        "notes": annotation.notes,
        "coordinates": annotation.coordinates,
        "created_at": annotation.created_at.isoformat() if annotation.created_at else None
    }


@router.get("")
async def get_annotations(
    investigation_id: Optional[UUID] = Query(None),
    evidence_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None),
    annotation_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get annotations with filters"""
    service = get_annotation_service(db)
    
    # Default to current user if not admin
    user_filter = current_user.user_id if user_id is None and current_user.role != "admin" else user_id
    
    annotations = service.get_annotations(
        investigation_id=investigation_id,
        evidence_id=evidence_id,
        user_id=user_filter,
        annotation_type=annotation_type,
        limit=limit,
        offset=offset
    )
    
    return {
        "annotations": [
            {
                "annotation_id": str(a.annotation_id),
                "investigation_id": str(a.investigation_id),
                "evidence_id": str(a.evidence_id) if a.evidence_id else None,
                "user_id": str(a.user_id),
                "annotation_type": a.annotation_type,
                "notes": a.notes,
                "coordinates": a.coordinates,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in annotations
        ],
        "count": len(annotations)
    }


@router.get("/{annotation_id}")
async def get_annotation(
    annotation_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get annotation by ID"""
    service = get_annotation_service(db)
    annotation = service.get_annotation(annotation_id)
    
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    # Check permissions (user can only see their own or admin can see all)
    if annotation.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "annotation_id": str(annotation.annotation_id),
        "investigation_id": str(annotation.investigation_id),
        "evidence_id": str(annotation.evidence_id) if annotation.evidence_id else None,
        "user_id": str(annotation.user_id),
        "annotation_type": annotation.annotation_type,
        "notes": annotation.notes,
        "coordinates": annotation.coordinates,
        "created_at": annotation.created_at.isoformat() if annotation.created_at else None
    }


@router.put("/{annotation_id}")
async def update_annotation(
    annotation_id: UUID,
    annotation_data: AnnotationUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update annotation"""
    service = get_annotation_service(db)
    annotation = service.get_annotation(annotation_id)
    
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    # Check permissions
    if annotation.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated = service.update_annotation(
        annotation_id=annotation_id,
        notes=annotation_data.notes,
        coordinates=annotation_data.coordinates
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    return {
        "annotation_id": str(updated.annotation_id),
        "notes": updated.notes,
        "coordinates": updated.coordinates
    }


@router.delete("/{annotation_id}")
async def delete_annotation(
    annotation_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Delete annotation"""
    service = get_annotation_service(db)
    annotation = service.get_annotation(annotation_id)
    
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    # Check permissions
    if annotation.user_id != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = service.delete_annotation(annotation_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    return {"message": "Annotation deleted successfully"}

