"""API routes for investigation templates"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from backend.auth.auth import get_current_user
from backend.database import get_db, User
from backend.services.template_service import get_template_service
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


class TemplateCreate(BaseModel):
    """Template creation model"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    workflow_steps: List[Dict[str, Any]] = Field(default_factory=list)
    default_agents: List[str] = Field(default_factory=list)


class TemplateUpdate(BaseModel):
    """Template update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    workflow_steps: Optional[List[Dict[str, Any]]] = None
    default_agents: Optional[List[str]] = None


@router.post("")
async def create_template(
    template_data: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Create a new investigation template"""
    service = get_template_service(db)
    template = service.create_template(
        name=template_data.name,
        description=template_data.description,
        workflow_steps=template_data.workflow_steps,
        default_agents=template_data.default_agents,
        created_by=current_user.user_id
    )
    
    return {
        "template_id": str(template.template_id),
        "name": template.name,
        "description": template.description,
        "workflow_steps": template.workflow_steps,
        "default_agents": template.default_agents,
        "created_at": template.created_at.isoformat() if template.created_at else None
    }


@router.get("")
async def get_templates(
    created_by: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get investigation templates"""
    service = get_template_service(db)
    
    # Filter by current user if not admin
    user_filter = current_user.user_id if current_user.role != "admin" else created_by
    if user_filter:
        templates = service.get_templates(created_by=user_filter, limit=limit, offset=offset)
    else:
        templates = service.get_templates(limit=limit, offset=offset)
    
    return {
        "templates": [
            {
                "template_id": str(t.template_id),
                "name": t.name,
                "description": t.description,
                "workflow_steps": t.workflow_steps,
                "default_agents": t.default_agents,
                "created_by": str(t.created_by) if t.created_by else None,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in templates
        ],
        "count": len(templates)
    }


@router.get("/{template_id}")
async def get_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get template by ID"""
    service = get_template_service(db)
    template = service.get_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check permissions
    if template.created_by != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "template_id": str(template.template_id),
        "name": template.name,
        "description": template.description,
        "workflow_steps": template.workflow_steps,
        "default_agents": template.default_agents,
        "created_by": str(template.created_by) if template.created_by else None,
        "created_at": template.created_at.isoformat() if template.created_at else None
    }


@router.put("/{template_id}")
async def update_template(
    template_id: UUID,
    template_data: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update template"""
    service = get_template_service(db)
    template = service.get_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check permissions
    if template.created_by != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated = service.update_template(
        template_id=template_id,
        name=template_data.name,
        description=template_data.description,
        workflow_steps=template_data.workflow_steps,
        default_agents=template_data.default_agents
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {
        "template_id": str(updated.template_id),
        "name": updated.name,
        "description": updated.description,
        "workflow_steps": updated.workflow_steps,
        "default_agents": updated.default_agents
    }


@router.delete("/{template_id}")
async def delete_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Delete template"""
    service = get_template_service(db)
    template = service.get_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check permissions
    if template.created_by != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = service.delete_template(template_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {"message": "Template deleted successfully"}


@router.post("/{template_id}/apply")
async def apply_template(
    template_id: UUID,
    investigation_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Apply template to investigation"""
    service = get_template_service(db)
    result = service.apply_template(template_id, investigation_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to apply template"))
    
    return result

