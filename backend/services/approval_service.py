"""
Approval service for managing investigation checkpoints and user approvals.
"""

import asyncio
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.database.models import Investigation
from backend.services.event_service import get_event_service
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ApprovalService:
    """Service for managing investigation approval requests"""
    
    def __init__(self, session: Session):
        """
        Initialize approval service.
        
        Args:
            session: Database session
        """
        self.session = session
        self.event_service = get_event_service()
        
        # In-memory storage for pending approvals
        # In production, this should be in Redis or database
        self._pending_approvals: Dict[str, Dict[str, Any]] = {}
        self._approval_responses: Dict[str, Dict[str, Any]] = {}
    
    async def request_approval(
        self,
        investigation_id: UUID,
        approval_type: str,
        data: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> str:
        """
        Create an approval request.
        
        Args:
            investigation_id: Investigation ID
            approval_type: Type of approval (plan, evidence_review, findings, final)
            data: Approval request data
            timeout: Timeout in seconds (None = indefinite)
            
        Returns:
            Approval request ID
        """
        approval_id = f"{investigation_id}_{approval_type}_{int(datetime.now().timestamp())}"
        
        self._pending_approvals[approval_id] = {
            "investigation_id": str(investigation_id),
            "approval_type": approval_type,
            "data": data,
            "created_at": datetime.now(),
            "timeout": timeout,
            "status": "pending"
        }
        
        logger.info(f"Approval request created: {approval_id} (type: {approval_type})")
        
        # Emit event to frontend
        await self.event_service.emit(
            "approval_required",
            {
                "approval_id": approval_id,
                "investigation_id": str(investigation_id),
                "approval_type": approval_type,
                "data": data,
                "timeout": timeout
            },
            investigation_id=str(investigation_id)
        )
        
        return approval_id
    
    async def wait_for_approval(
        self,
        approval_id: str,
        poll_interval: float = 0.5
    ) -> Dict[str, Any]:
        """
        Wait for user approval response.
        
        Args:
            approval_id: Approval request ID
            poll_interval: Polling interval in seconds
            
        Returns:
            Approval response with approved (bool) and any modifications
        """
        if approval_id not in self._pending_approvals:
            raise ValueError(f"Approval request not found: {approval_id}")
        
        request = self._pending_approvals[approval_id]
        timeout = request.get("timeout")
        start_time = datetime.now()
        
        logger.info(f"Waiting for approval: {approval_id} (timeout: {timeout}s)")
        
        while True:
            # Check if response received
            if approval_id in self._approval_responses:
                response = self._approval_responses[approval_id]
                logger.info(f"Approval received: {approval_id} (approved: {response.get('approved')})")
                
                # Clean up
                del self._pending_approvals[approval_id]
                del self._approval_responses[approval_id]
                
                return response
            
            # Check timeout
            if timeout:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed >= timeout:
                    logger.warning(f"Approval timeout: {approval_id}")
                    
                    # Mark as timed out
                    request["status"] = "timeout"
                    
                    # Emit timeout event
                    await self.event_service.emit(
                        "approval_timeout",
                        {
                            "approval_id": approval_id,
                            "investigation_id": request["investigation_id"]
                        },
                        investigation_id=request["investigation_id"]
                    )
                    
                    # Clean up
                    del self._pending_approvals[approval_id]
                    
                    return {
                        "approved": False,
                        "timeout": True,
                        "message": "Approval request timed out"
                    }
            
            # Wait before polling again
            await asyncio.sleep(poll_interval)
    
    def submit_approval(
        self,
        approval_id: str,
        approved: bool,
        modifications: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None
    ) -> bool:
        """
        Submit approval response.
        
        Args:
            approval_id: Approval request ID
            approved: Whether approved
            modifications: Any modifications to the request
            message: Optional message/reason
            
        Returns:
            True if submission successful
        """
        if approval_id not in self._pending_approvals:
            logger.error(f"Cannot submit approval for unknown request: {approval_id}")
            return False
        
        self._approval_responses[approval_id] = {
            "approved": approved,
            "modifications": modifications or {},
            "message": message,
            "timestamp": datetime.now()
        }
        
        logger.info(f"Approval submitted: {approval_id} (approved: {approved})")
        
        return True
    
    def get_pending_approvals(
        self,
        investigation_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending approval requests.
        
        Args:
            investigation_id: Filter by investigation ID
            
        Returns:
            List of pending approvals
        """
        pending = []
        
        for approval_id, request in self._pending_approvals.items():
            if investigation_id is None or request["investigation_id"] == str(investigation_id):
                pending.append({
                    "approval_id": approval_id,
                    **request
                })
        
        return pending
    
    def cancel_approval(self, approval_id: str) -> bool:
        """
        Cancel a pending approval request.
        
        Args:
            approval_id: Approval request ID
            
        Returns:
            True if cancelled successfully
        """
        if approval_id in self._pending_approvals:
            del self._pending_approvals[approval_id]
            logger.info(f"Approval cancelled: {approval_id}")
            return True
        
        return False


# Singleton instance
_approval_service: Optional[ApprovalService] = None


def get_approval_service(session: Session) -> ApprovalService:
    """
    Get approval service instance.
    
    Args:
        session: Database session
        
    Returns:
        ApprovalService instance
    """
    # Note: Not truly singleton since each session gets its own instance
    # This is intentional for database session management
    return ApprovalService(session)

