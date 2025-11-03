"""Main API routes and endpoint handlers"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from backend.database import get_db, User, Tiger, Facility, Investigation, TigerImage
from backend.auth.auth import get_current_user
from backend.utils.pagination import PaginatedResponse, paginate_query
from backend.utils.response_models import SuccessResponse
from backend.services.investigation_service import InvestigationService
from pydantic import BaseModel, validator, field_validator

router = APIRouter(tags=["api"])  # Prefix added when including in app.py


# Response models
class TigerResponse(BaseModel):
    id: str
    name: Optional[str]
    estimated_age: Optional[int]
    sex: Optional[str]
    first_seen: str
    last_seen: str
    confidence_score: float
    
    class Config:
        from_attributes = True


class FacilityResponse(BaseModel):
    id: str
    name: str
    license_number: Optional[str]
    facility_type: str
    address: str
    city: str
    state: str
    country: str
    status: str
    verified: bool
    
    class Config:
        from_attributes = True


class CreateInvestigationRequest(BaseModel):
    """Create investigation request model"""
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    tags: Optional[List[str]] = []
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate investigation title"""
        if not v or len(v.strip()) < 3:
            raise ValueError("Title must be at least 3 characters long")
        if len(v) > 200:
            raise ValueError("Title must not exceed 200 characters")
        # Sanitize HTML/XSS
        import re
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', v, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'<[^>]+>', '', sanitized)
        return sanitized.strip()
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate priority"""
        valid_priorities = ['low', 'medium', 'high', 'critical']
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v


class InvestigationResponse(BaseModel):
    """Investigation response model"""
    investigation_id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    created_by: str
    created_at: str
    
    class Config:
        from_attributes = True


# Investigation CRUD endpoints
@router.get("/investigations")
async def get_investigations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of investigations"""
    query = db.query(Investigation)
    
    # Filter by status if provided
    if status:
        query = query.filter(Investigation.status == status)
    
    # Order by most recent
    query = query.order_by(Investigation.created_at.desc())
    
    investigations, total = paginate_query(query, page, page_size)
    
    # Convert to response format
    investigation_data = []
    for inv in investigations:
        investigation_data.append({
            "id": str(inv.investigation_id),
            "title": inv.title,
            "description": inv.description,
            "status": inv.status.value if hasattr(inv.status, 'value') else str(inv.status),
            "priority": inv.priority.value if hasattr(inv.priority, 'value') else str(inv.priority),
            "created_by": str(inv.created_by),
            "tags": inv.tags or [],
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "updated_at": inv.updated_at.isoformat() if inv.updated_at else None,
        })
    
    paginated = PaginatedResponse.create(
        data=investigation_data,
        total=total,
        page=page,
        page_size=page_size
    )
    
    return {
        "success": True,
        "data": paginated.model_dump()
    }


@router.post("/investigations")
async def create_investigation(
    request: CreateInvestigationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new investigation"""
    service = InvestigationService(db)
    investigation = service.create_investigation(
        title=request.title,
        description=request.description,
        created_by=current_user.user_id,
        priority=request.priority
    )
    
    return {
        "success": True,
        "data": {
            "id": str(investigation.investigation_id),
            "title": investigation.title,
            "description": investigation.description,
            "status": investigation.status.value if hasattr(investigation.status, 'value') else str(investigation.status),
            "priority": investigation.priority.value if hasattr(investigation.priority, 'value') else str(investigation.priority),
            "created_by": str(investigation.created_by),
            "created_at": investigation.created_at.isoformat() if investigation.created_at else None
        }
    }


@router.get("/investigations/{investigation_id}")
async def get_investigation(
    investigation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get investigation by ID"""
    service = InvestigationService(db)
    investigation = service.get_investigation(investigation_id)
    
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    return {
        "success": True,
        "data": {
            "id": str(investigation.investigation_id),
            "title": investigation.title,
            "description": investigation.description,
            "status": investigation.status.value if hasattr(investigation.status, 'value') else str(investigation.status),
            "priority": investigation.priority.value if hasattr(investigation.priority, 'value') else str(investigation.priority),
            "created_by": str(investigation.created_by),
            "tags": investigation.tags or [],
            "created_at": investigation.created_at.isoformat() if investigation.created_at else None,
            "updated_at": investigation.updated_at.isoformat() if investigation.updated_at else None,
        }
    }


@router.post("/investigations/{investigation_id}/launch")
async def launch_investigation(
    investigation_id: UUID,
    user_input: Optional[str] = Form(None),
    selected_tools: Optional[List[str]] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Launch an investigation with user input, files, and selected tools"""
    from fastapi import UploadFile, File, Form
    
    service = InvestigationService(db)
    
    # Convert files to list if single file
    file_list = files if isinstance(files, list) else ([files] if files else [])
    
    # Launch investigation
    result = await service.launch_investigation(
        investigation_id=investigation_id,
        user_input=user_input or "Launch investigation",
        files=file_list,
        user_id=current_user.user_id
    )
    
    return {
        "success": True,
        "data": {
            "id": str(investigation_id),
            "response": result.get("response", "Investigation launched successfully"),
            "next_steps": result.get("next_steps", []),
            "evidence_count": result.get("evidence_count", 0),
            "status": result.get("status", "in_progress")
        }
    }


# Tigers endpoints
@router.get("/tigers")
async def get_tigers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of tigers"""
    query = db.query(Tiger)
    tigers, total = paginate_query(query, page, page_size)
    
    # Convert to response format
    tiger_data = []
    for tiger in tigers:
        # Get tiger images
        tiger_images = db.query(TigerImage).filter(TigerImage.tiger_id == tiger.tiger_id).limit(5).all()
        images = []
        for img in tiger_images:
            # Create URL for image - try relative path first
            image_url = None
            if img.image_path:
                # Convert to URL-safe path
                from pathlib import Path
                img_path = Path(img.image_path)
                # If it's relative to project root, make it a static URL
                project_root = Path(__file__).parent.parent.parent
                try:
                    rel_path = img_path.relative_to(project_root)
                    image_url = f"/static/images/{rel_path.as_posix()}"
                except ValueError:
                    # If not relative, use absolute path handling
                    if img_path.exists():
                        rel_path_str = img_path.as_posix().replace(str(project_root), '').lstrip('/').replace('\\', '/')
                        image_url = f"/static/images/{rel_path_str}"
            
            if image_url:
                images.append({
                    "id": str(img.image_id),
                    "url": image_url,
                    "thumbnail_url": image_url,  # Can be optimized later
                    "uploaded_at": img.created_at.isoformat() if img.created_at else None,
                    "source": getattr(img, 'source', None) or "dataset",
                    "metadata": getattr(img, 'metadata', {}) or {}
                })
        
        tiger_data.append({
            "id": str(tiger.tiger_id),
            "name": tiger.name,
            "estimated_age": getattr(tiger, 'estimated_age', None),
            "sex": getattr(tiger, 'sex', None),
            "first_seen": tiger.created_at.isoformat() if tiger.created_at else None,
            "last_seen": tiger.last_seen_date.isoformat() if tiger.last_seen_date else None,
            "confidence_score": getattr(tiger, 'confidence_score', 0.95) or 0.95,
            "images": images,
            "locations": [],
        })
    
    paginated = PaginatedResponse.create(
        data=tiger_data,
        total=total,
        page=page,
        page_size=page_size
    )
    
    return {
        "success": True,
        "data": paginated.model_dump()
    }


@router.get("/tigers/{tiger_id}")
async def get_tiger(
    tiger_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tiger by ID"""
    tiger = db.query(Tiger).filter(Tiger.tiger_id == tiger_id).first()
    
    if not tiger:
        raise HTTPException(status_code=404, detail="Tiger not found")
    
    return {
        "success": True,
        "data": {
            "id": str(tiger.tiger_id),
            "name": tiger.name,
            "last_seen": tiger.last_seen_date.isoformat() if tiger.last_seen_date else None,
            "status": tiger.status.value if tiger.status else "active",
        }
    }


# Facilities endpoints
@router.get("/facilities")
async def get_facilities(
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=1000),  # Allow larger page sizes for map visualization
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of facilities"""
    query = db.query(Facility)
    facilities, total = paginate_query(query, page, page_size)
    
    # Convert to response format
    facility_data = []
    for facility in facilities:
        facility_data.append({
            "id": str(facility.facility_id),
            "name": facility.exhibitor_name,
            "license_number": facility.usda_license,
            "facility_type": "Zoo",  # Add if available
            "address": facility.address or "",
            "city": facility.city or "",
            "state": facility.state or "",
            "country": "USA",  # Add if available
            "status": "active",  # Add if available
            "verified": True,  # Add if available
            "created_at": facility.created_at.isoformat() if facility.created_at else None,
        })
    
    paginated = PaginatedResponse.create(
        data=facility_data,
        total=total,
        page=page,
        page_size=page_size
    )
    
    return {
        "success": True,
        "data": paginated.model_dump()
    }


@router.get("/facilities/{facility_id}")
async def get_facility(
    facility_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get facility by ID"""
    facility = db.query(Facility).filter(Facility.facility_id == facility_id).first()
    
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    
    return {
        "success": True,
        "data": {
            "id": str(facility.facility_id),
            "name": facility.exhibitor_name,
            "license_number": facility.usda_license,
            "state": facility.state,
            "city": facility.city,
        }
    }


# Dashboard stats endpoint
@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics"""
    from backend.database.models import Investigation
    
    total_investigations = db.query(Investigation).count()
    active_investigations = db.query(Investigation).filter(
        Investigation.status == "active"
    ).count()
    completed_investigations = db.query(Investigation).filter(
        Investigation.status == "completed"
    ).count()
    total_tigers = db.query(Tiger).count()
    total_facilities = db.query(Facility).count()
    
    return {
        "success": True,
        "data": {
            "total_investigations": total_investigations,
            "active_investigations": active_investigations,
            "completed_investigations": completed_investigations,
            "total_tigers": total_tigers,
            "total_facilities": total_facilities,
            "pending_verifications": 0,  # Add when verification table is ready
            "recent_activity": [],  # Add when event history is ready
        }
    }


# Health check
@router.get("/health")
async def health_check():
    """API health check"""
    return {"status": "healthy", "message": "API is running"}
