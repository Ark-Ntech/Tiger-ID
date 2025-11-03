"""Service layer for Investigation operations"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database.models import (
    Investigation, InvestigationStep, Evidence, 
    VerificationQueue, InvestigationComment
)


class InvestigationService:
    """Service for investigation-related operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_investigation(
        self,
        title: str,
        created_by: UUID,
        description: Optional[str] = None,
        priority: str = "medium",
        tags: Optional[List[str]] = None,
        assigned_to: Optional[List[UUID]] = None
    ) -> Investigation:
        """Create a new investigation"""
        investigation = Investigation(
            title=title,
            description=description,
            created_by=created_by,
            status="draft",
            priority=priority,
            tags=tags or [],
            assigned_to=[str(uuid) for uuid in (assigned_to or [])]
        )
        self.session.add(investigation)
        self.session.commit()
        self.session.refresh(investigation)
        return investigation
    
    def get_investigation(self, investigation_id: UUID) -> Optional[Investigation]:
        """Get investigation by ID"""
        return self.session.query(Investigation).filter(
            Investigation.investigation_id == investigation_id
        ).first()
    
    def get_investigations(
        self,
        status: Optional[str] = None,
        created_by: Optional[UUID] = None,
        assigned_to: Optional[UUID] = None,
        priority: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Investigation]:
        """Get list of investigations with filters"""
        query = self.session.query(Investigation)
        
        if status:
            query = query.filter(Investigation.status == status)
        
        if created_by:
            query = query.filter(Investigation.created_by == created_by)
        
        if assigned_to:
            query = query.filter(
                Investigation.assigned_to.contains([str(assigned_to)])
            )
        
        if priority:
            query = query.filter(Investigation.priority == priority)
        
        return query.order_by(Investigation.created_at.desc()).limit(limit).offset(offset).all()
    
    def update_investigation(
        self,
        investigation_id: UUID,
        **updates
    ) -> Optional[Investigation]:
        """Update investigation record"""
        investigation = self.get_investigation(investigation_id)
        if not investigation:
            return None
        
        for key, value in updates.items():
            if hasattr(investigation, key):
                setattr(investigation, key, value)
        
        self.session.commit()
        self.session.refresh(investigation)
        return investigation
    
    def start_investigation(self, investigation_id: UUID) -> Optional[Investigation]:
        """Start an investigation"""
        investigation = self.get_investigation(investigation_id)
        if not investigation:
            return None
        
        investigation.status = "active"
        investigation.started_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(investigation)
        return investigation
    
    def pause_investigation(self, investigation_id: UUID) -> Optional[Investigation]:
        """Pause an investigation"""
        investigation = self.get_investigation(investigation_id)
        if not investigation:
            return None
        
        if investigation.status not in ["active", "in_progress"]:
            raise ValueError(f"Cannot pause investigation with status: {investigation.status}")
        
        investigation.status = "paused"
        self.session.commit()
        self.session.refresh(investigation)
        return investigation
    
    def resume_investigation(self, investigation_id: UUID) -> Optional[Investigation]:
        """Resume a paused investigation"""
        investigation = self.get_investigation(investigation_id)
        if not investigation:
            return None
        
        if investigation.status != "paused":
            raise ValueError(f"Cannot resume investigation with status: {investigation.status}")
        
        investigation.status = "in_progress"
        self.session.commit()
        self.session.refresh(investigation)
        return investigation
    
    def cancel_investigation(self, investigation_id: UUID, reason: Optional[str] = None) -> Optional[Investigation]:
        """Cancel an investigation"""
        investigation = self.get_investigation(investigation_id)
        if not investigation:
            return None
        
        if investigation.status in ["completed", "cancelled"]:
            raise ValueError(f"Cannot cancel investigation with status: {investigation.status}")
        
        investigation.status = "cancelled"
        if reason:
            if not investigation.summary:
                investigation.summary = {}
            investigation.summary["cancellation_reason"] = reason
        
        self.session.commit()
        self.session.refresh(investigation)
        return investigation
    
    def complete_investigation(
        self,
        investigation_id: UUID,
        summary: Optional[Dict[str, Any]] = None
    ) -> Optional[Investigation]:
        """Complete an investigation"""
        investigation = self.get_investigation(investigation_id)
        if not investigation:
            return None
        
        investigation.status = "completed"
        investigation.completed_at = datetime.utcnow()
        if summary:
            investigation.summary = summary
        
        self.session.commit()
        self.session.refresh(investigation)
        return investigation
    
    def add_investigation_step(
        self,
        investigation_id: UUID,
        step_type: str,
        agent_name: Optional[str] = None,
        status: str = "pending",
        result: Optional[Dict[str, Any]] = None,
        parent_step_id: Optional[UUID] = None
    ) -> InvestigationStep:
        """Add a step to an investigation"""
        step = InvestigationStep(
            investigation_id=investigation_id,
            step_type=step_type,
            agent_name=agent_name,
            status=status,
            result=result or {},
            parent_step_id=parent_step_id
        )
        self.session.add(step)
        self.session.commit()
        self.session.refresh(step)
        return step
    
    def add_evidence(
        self,
        investigation_id: UUID,
        source_type: str,
        source_url: Optional[str] = None,
        content: Optional[Dict[str, Any]] = None,
        extracted_text: Optional[str] = None,
        relevance_score: Optional[float] = None
    ) -> Evidence:
        """Add evidence to an investigation"""
        evidence = Evidence(
            investigation_id=investigation_id,
            source_type=source_type,
            source_url=source_url,
            content=content or {},
            extracted_text=extracted_text,
            relevance_score=relevance_score
        )
        self.session.add(evidence)
        self.session.commit()
        self.session.refresh(evidence)
        return evidence
    
    def get_investigation_steps(self, investigation_id: UUID) -> List[InvestigationStep]:
        """Get all steps for an investigation"""
        return self.session.query(InvestigationStep).filter(
            InvestigationStep.investigation_id == investigation_id
        ).order_by(InvestigationStep.timestamp).all()
    
    def get_investigation_evidence(self, investigation_id: UUID) -> List[Evidence]:
        """Get all evidence for an investigation"""
        return self.session.query(Evidence).filter(
            Evidence.investigation_id == investigation_id
        ).order_by(Evidence.created_at).all()
    
    async def launch_investigation(
        self,
        investigation_id: UUID,
        user_input: str,
        files: List[Any],
        user_id: UUID
    ) -> Dict[str, Any]:
        """Launch an investigation with user input and files"""
        from backend.agents import OrchestratorAgent
        
        # Update investigation status
        investigation = self.get_investigation(investigation_id)
        if not investigation:
            raise ValueError("Investigation not found")
        
        # Check if investigation is paused or cancelled
        if investigation.status == "paused":
            raise ValueError("Cannot launch paused investigation. Please resume it first.")
        if investigation.status == "cancelled":
            raise ValueError("Cannot launch cancelled investigation.")
        
        investigation = self.start_investigation(investigation_id)
        
        # Status is already set to 'active' by start_investigation
        # No need to change it again
        self.session.commit()
        self.session.refresh(investigation)
        
        # Process files
        file_data = []
        for file in files:
            file_data.append({
                "name": getattr(file, "filename", "unknown"),
                "type": getattr(file, "content_type", "unknown"),
            })
        
        # Use orchestrator to process request
        from backend.database import get_db_session
        
        try:
            with get_db_session() as session:
                orchestrator = OrchestratorAgent(db=session)
                result = await orchestrator.launch_investigation(
                    investigation_id=investigation_id,
                    user_inputs={
                        "text": user_input,
                        "query": user_input,
                        "files": file_data,
                        "images": [f for f in file_data if f.get("type", "").startswith("image/")]
                    },
                    context={"user_id": str(user_id)}
                )
        except Exception as e:
            # If error occurs, mark investigation as failed
            investigation.status = "failed"
            if not investigation.summary:
                investigation.summary = {}
            investigation.summary["error"] = str(e)
            self.session.commit()
            raise
        
        # Log investigation step
        step = self.add_investigation_step(
            investigation_id=investigation_id,
            step_type="orchestrator_processing",
            agent_name="orchestrator",
            status="completed",
            result=result
        )
        
        # Extract evidence from result
        evidence_items = result.get("evidence", [])
        if isinstance(evidence_items, list):
            evidence_count = len(evidence_items)
        else:
            # If evidence is nested in research_results
            research_results = result.get("research_results", {})
            evidence_items = research_results.get("evidence", [])
            evidence_count = len(evidence_items) if isinstance(evidence_items, list) else 0
        
        # Get report summary if available
        report = result.get("report", {})
        response_message = report.get("summary", "Investigation launched successfully")
        
        return {
            "investigation_id": str(investigation_id),
            "response": response_message,
            "next_steps": result.get("next_steps", []),
            "evidence_count": evidence_count,
            "status": "in_progress"
        }
