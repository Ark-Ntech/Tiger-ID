"""Main API routes and endpoint handlers"""

import json
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
from backend.utils.logging import get_logger
from pydantic import BaseModel, validator, field_validator

logger = get_logger(__name__)

router = APIRouter(tags=["api"])  # Prefix added when including in app.py


def _parse_facility_coordinates(facility) -> tuple:
    """Parse latitude/longitude from facility.coordinates JSON text field.

    Returns:
        (latitude, longitude) tuple, with None values if not available.
    """
    lat, lon = None, None
    if facility.coordinates:
        try:
            coords_data = json.loads(facility.coordinates) if isinstance(facility.coordinates, str) else facility.coordinates
            if coords_data:
                lat = coords_data.get("latitude")
                lon = coords_data.get("longitude")
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass
    return lat, lon


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
    latitude: Optional[float] = None
    longitude: Optional[float] = None
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


# NOTE: /investigations/{investigation_id} route moved to investigation_routes.py
# to avoid conflicts with /mcp-tools route. The investigation_router is registered
# before the main router, so specific routes like /mcp-tools match first.


@router.post("/investigations/{investigation_id}/launch")
async def launch_investigation(
    investigation_id: UUID,
    user_input: Optional[str] = Form(None),
    selected_tools: Optional[List[str]] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    tiger_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Launch an investigation with user input, files, and selected tools"""
    from fastapi import UploadFile, File, Form
    from backend.utils.logging import get_logger
    
    logger = get_logger(__name__)
    
    logger.info(
        f"Launch investigation request: investigation_id={investigation_id}, "
        f"user_input={user_input[:50] if user_input else None}, "
        f"selected_tools={selected_tools}, tiger_id={tiger_id}"
    )
    
    try:
        service = InvestigationService(db)
        
        # Convert files to list if single file
        file_list = files if isinstance(files, list) else ([files] if files else [])
        
        logger.info(f"Launching investigation with {len(file_list)} files and {len(selected_tools) if selected_tools else 0} selected tools")
        
        # Launch investigation with selected tools
        result = await service.launch_investigation(
            investigation_id=investigation_id,
            user_input=user_input or "Launch investigation",
            files=file_list,
            user_id=current_user.user_id,
            selected_tools=selected_tools or [],
            tiger_id=tiger_id
        )
        
        logger.info(f"Investigation launched successfully. Response: {result.get('response', '')[:100]}")
        
        return {
            "success": True,
            "data": {
                "id": str(investigation_id),
                "response": result.get("response", "Investigation launched successfully"),
                "next_steps": result.get("next_steps", []),
                "evidence_count": result.get("evidence_count", 0),
                "status": result.get("status", "in_progress"),
                "tiger_id": result.get("tiger_id"),
                "tiger_metadata": result.get("tiger_metadata")
            }
        }
    except Exception as e:
        logger.error(f"Error launching investigation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to launch investigation: {str(e)}")


# Tigers endpoints - Moved to tiger_routes.py to avoid conflicts
# The tiger_router handles all /tigers/* routes with better functionality


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
        # Parse reference_metadata from JSON string to dict if needed
        # (reference_metadata is a plain Text column, not JSONEncodedValue)
        ref_meta = facility.reference_metadata or {}
        if isinstance(ref_meta, str):
            try:
                ref_meta = json.loads(ref_meta)
            except (json.JSONDecodeError, TypeError):
                ref_meta = {}

        # Parse lat/lng from coordinates JSON field
        lat, lon = _parse_facility_coordinates(facility)

        facility_data.append({
            "id": str(facility.facility_id),
            "name": facility.exhibitor_name,
            "exhibitor_name": facility.exhibitor_name,
            "license_number": facility.usda_license,
            "usda_license": facility.usda_license,
            "facility_type": "Zoo",  # Add if available
            "address": facility.address or "",
            "city": facility.city or "",
            "state": facility.state or "",
            "country": "USA",  # Add if available
            "latitude": lat,
            "longitude": lon,
            "status": "active",  # Add if available
            "verified": True,  # Add if available
            "tiger_count": facility.tiger_count or 0,
            "tiger_capacity": facility.tiger_capacity,
            "accreditation_status": facility.accreditation_status or "Unknown",
            "ir_date": facility.ir_date.isoformat() if facility.ir_date else None,
            "last_inspection_date": facility.last_inspection_date.isoformat() if facility.last_inspection_date else None,
            "website": facility.website,
            "social_media_links": facility.social_media_links or {},
            "is_reference_facility": facility.is_reference_facility or False,
            "data_source": facility.data_source,
            "reference_metadata": ref_meta,
            "created_at": facility.created_at.isoformat() if facility.created_at else None,
            "updated_at": facility.updated_at.isoformat() if facility.updated_at else None,
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
    # Convert UUID to string for SQLite String(36) column comparison
    facility = db.query(Facility).filter(Facility.facility_id == str(facility_id)).first()

    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    # Parse reference_metadata from JSON string to dict if needed
    # (reference_metadata is a plain Text column, not JSONEncodedValue)
    reference_metadata = facility.reference_metadata or {}
    if isinstance(reference_metadata, str):
        try:
            reference_metadata = json.loads(reference_metadata)
        except (json.JSONDecodeError, TypeError):
            reference_metadata = {}

    # Parse lat/lng from coordinates JSON field
    lat, lon = _parse_facility_coordinates(facility)

    return {
        "success": True,
        "data": {
            "id": str(facility.facility_id),
            "name": facility.exhibitor_name,
            "exhibitor_name": facility.exhibitor_name,
            "license_number": facility.usda_license,
            "usda_license": facility.usda_license,
            "address": facility.address,
            "city": facility.city,
            "state": facility.state,
            "country": "USA",
            "latitude": lat,
            "longitude": lon,
            "tiger_count": facility.tiger_count or 0,
            "tiger_capacity": facility.tiger_capacity,
            "accreditation_status": facility.accreditation_status,
            "ir_date": facility.ir_date.isoformat() if facility.ir_date else None,
            "last_inspection_date": facility.last_inspection_date.isoformat() if facility.last_inspection_date else None,
            "website": facility.website,
            "social_media_links": facility.social_media_links or {},
            "is_reference_facility": facility.is_reference_facility or False,
            "data_source": facility.data_source,
            "reference_metadata": reference_metadata,
            "created_at": facility.created_at.isoformat() if facility.created_at else None,
            "updated_at": facility.updated_at.isoformat() if facility.updated_at else None,
        }
    }


@router.post("/facilities/import-excel")
async def import_facilities_excel(
    file: UploadFile = File(...),
    update_existing: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import facilities from Excel file"""
    from pathlib import Path
    import tempfile
    from scripts.parse_tpc_facilities_excel import parse_excel_file
    from backend.services.facility_service import FacilityService
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only Excel files (.xlsx, .xls) are supported."
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = Path(tmp_file.name)
    
    try:
        # Parse Excel file
        facilities_data = parse_excel_file(tmp_path)
        
        if not facilities_data:
            raise HTTPException(
                status_code=400,
                detail="No facility data found in Excel file"
            )
        
        # Import facilities
        facility_service = FacilityService(db)
        stats = facility_service.bulk_import_facilities(
            facilities_data,
            update_existing=update_existing
        )
        
        return {
            "success": True,
            "data": {
                "message": f"Imported {stats['created']} facilities, updated {stats['updated']}, skipped {stats['skipped']}",
                "stats": stats
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error importing facilities: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        if tmp_path.exists():
            tmp_path.unlink()


# Dashboard stats endpoint
@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics"""
    from backend.database.models import Investigation, InvestigationStatus
    
    total_investigations = db.query(Investigation).count()
    active_investigations = db.query(Investigation).filter(
        Investigation.status == InvestigationStatus.active.value
    ).count()
    completed_investigations = db.query(Investigation).filter(
        Investigation.status == InvestigationStatus.completed.value
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
