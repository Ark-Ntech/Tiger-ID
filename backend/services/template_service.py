"""Service for managing investigation templates"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.models import InvestigationTemplate
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class TemplateService:
    """Service for investigation templates"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_template(
        self,
        name: str,
        description: Optional[str],
        workflow_steps: List[Dict[str, Any]],
        default_agents: List[str],
        created_by: UUID
    ) -> InvestigationTemplate:
        """
        Create a new investigation template
        
        Args:
            name: Template name
            description: Template description
            workflow_steps: List of workflow steps
            default_agents: List of default agents to use
            created_by: User ID who created the template
        
        Returns:
            Created template
        """
        template = InvestigationTemplate(
            name=name,
            description=description,
            workflow_steps=workflow_steps or [],
            default_agents=default_agents or [],
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        
        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)
        
        return template
    
    def get_template(self, template_id: UUID) -> Optional[InvestigationTemplate]:
        """Get template by ID"""
        return self.session.query(InvestigationTemplate).filter(
            InvestigationTemplate.template_id == template_id
        ).first()
    
    def get_templates(
        self,
        created_by: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[InvestigationTemplate]:
        """
        Get templates with filters
        
        Args:
            created_by: Filter by creator
            limit: Maximum results
            offset: Pagination offset
        
        Returns:
            List of templates
        """
        query = self.session.query(InvestigationTemplate)
        
        if created_by:
            query = query.filter(InvestigationTemplate.created_by == created_by)
        
        query = query.order_by(desc(InvestigationTemplate.created_at))
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def update_template(
        self,
        template_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        workflow_steps: Optional[List[Dict[str, Any]]] = None,
        default_agents: Optional[List[str]] = None
    ) -> Optional[InvestigationTemplate]:
        """Update template"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if workflow_steps is not None:
            template.workflow_steps = workflow_steps
        if default_agents is not None:
            template.default_agents = default_agents
        
        self.session.commit()
        self.session.refresh(template)
        
        return template
    
    def delete_template(self, template_id: UUID) -> bool:
        """Delete template"""
        template = self.get_template(template_id)
        if not template:
            return False
        
        self.session.delete(template)
        self.session.commit()
        
        return True
    
    def apply_template(
        self,
        template_id: UUID,
        investigation_id: UUID
    ) -> Dict[str, Any]:
        """
        Apply template to investigation
        
        Args:
            template_id: Template ID
            investigation_id: Investigation ID
        
        Returns:
            Application results
        """
        template = self.get_template(template_id)
        if not template:
            return {"success": False, "error": "Template not found"}
        
        # This would integrate with InvestigationService to apply workflow steps
        # For now, return template structure
        return {
            "success": True,
            "template_id": str(template_id),
            "workflow_steps": template.workflow_steps,
            "default_agents": template.default_agents
        }


def get_template_service(session: Session) -> TemplateService:
    """Get template service instance"""
    return TemplateService(session)

