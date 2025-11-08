"""
API routes for investigation approval management.
"""

from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.auth import get_current_user
from backend.database import get_db, User
from backend.services.approval_service import get_approval_service
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


class ApprovalSubmission(BaseModel):
    """Approval submission request"""
    approved: bool
    modifications: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


@router.get("/pending")
async def get_pending_approvals(
    investigation_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pending approval requests"""
    try:
        approval_service = get_approval_service(db)
        pending = approval_service.get_pending_approvals(investigation_id)
        
        return {
            "success": True,
            "data": {
                "approvals": pending,
                "count": len(pending)
            }
        }
    except Exception as e:
        logger.error(f"Error getting pending approvals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{approval_id}/submit")
async def submit_approval(
    approval_id: str,
    submission: ApprovalSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit approval response"""
    try:
        approval_service = get_approval_service(db)
        
        success = approval_service.submit_approval(
            approval_id=approval_id,
            approved=submission.approved,
            modifications=submission.modifications,
            message=submission.message
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Approval request not found")
        
        return {
            "success": True,
            "data": {
                "approval_id": approval_id,
                "approved": submission.approved
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting approval: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{approval_id}/cancel")
async def cancel_approval(
    approval_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a pending approval request"""
    try:
        approval_service = get_approval_service(db)
        
        success = approval_service.cancel_approval(approval_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Approval request not found")
        
        return {
            "success": True,
            "data": {
                "approval_id": approval_id,
                "cancelled": True
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling approval: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

