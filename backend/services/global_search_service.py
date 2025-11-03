"""Global search service for unified search across all entities"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from backend.database.models import Investigation, Evidence, Facility, Tiger, InvestigationStep
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class GlobalSearchService:
    """Service for unified search across all entities"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def search(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 50,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Perform global search across all entities
        
        Args:
            query: Search query string
            entity_types: Filter by entity types (investigations, evidence, facilities, tigers)
            limit: Maximum results per entity type
            user_id: Optional user ID to filter by permissions
        
        Returns:
            Search results grouped by entity type
        """
        results = {
            "query": query,
            "total_results": 0,
            "investigations": [],
            "evidence": [],
            "facilities": [],
            "tigers": [],
            "steps": []
        }
        
        search_terms = query.lower().split()
        
        # Search investigations
        if not entity_types or "investigations" in entity_types:
            inv_results = self._search_investigations(search_terms, limit, user_id)
            results["investigations"] = inv_results
            results["total_results"] += len(inv_results)
        
        # Search evidence
        if not entity_types or "evidence" in entity_types:
            ev_results = self._search_evidence(search_terms, limit, user_id)
            results["evidence"] = ev_results
            results["total_results"] += len(ev_results)
        
        # Search facilities
        if not entity_types or "facilities" in entity_types:
            fac_results = self._search_facilities(search_terms, limit)
            results["facilities"] = fac_results
            results["total_results"] += len(fac_results)
        
        # Search tigers
        if not entity_types or "tigers" in entity_types:
            tiger_results = self._search_tigers(search_terms, limit)
            results["tigers"] = tiger_results
            results["total_results"] += len(tiger_results)
        
        # Search investigation steps
        if not entity_types or "steps" in entity_types:
            step_results = self._search_steps(search_terms, limit, user_id)
            results["steps"] = step_results
            results["total_results"] += len(step_results)
        
        return results
    
    def _search_investigations(
        self,
        search_terms: List[str],
        limit: int,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Search investigations"""
        query = self.session.query(Investigation)
        
        # Filter by user if provided
        if user_id:
            query = query.filter(Investigation.created_by == user_id)
        
        # Build search conditions
        conditions = []
        for term in search_terms:
            conditions.append(
                or_(
                    Investigation.title.ilike(f"%{term}%"),
                    Investigation.description.ilike(f"%{term}%")
                )
            )
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        investigations = query.limit(limit).all()
        
        return [
            {
                "entity_type": "investigation",
                "entity_id": str(inv.investigation_id),
                "title": inv.title,
                "description": inv.description or "",
                "status": inv.status,
                "priority": inv.priority,
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
                "match_score": 1.0  # Could implement scoring
            }
            for inv in investigations
        ]
    
    def _search_evidence(
        self,
        search_terms: List[str],
        limit: int,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Search evidence"""
        query = self.session.query(Evidence)
        
        # Build search conditions
        conditions = []
        for term in search_terms:
            conditions.append(
                or_(
                    Evidence.source_url.ilike(f"%{term}%"),
                    Evidence.extracted_text.ilike(f"%{term}%")
                )
            )
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        evidence_items = query.limit(limit).all()
        
        return [
            {
                "entity_type": "evidence",
                "entity_id": str(ev.evidence_id),
                "investigation_id": str(ev.investigation_id) if ev.investigation_id else None,
                "source_type": ev.source_type,
                "source_url": ev.source_url or "",
                "extracted_text": (ev.extracted_text or "")[:200],
                "relevance_score": ev.relevance_score or 0.0,
                "created_at": ev.created_at.isoformat() if ev.created_at else None,
                "match_score": ev.relevance_score or 0.5
            }
            for ev in evidence_items
        ]
    
    def _search_facilities(
        self,
        search_terms: List[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search facilities"""
        query = self.session.query(Facility)
        
        # Build search conditions
        conditions = []
        for term in search_terms:
            conditions.append(
                or_(
                    Facility.exhibitor_name.ilike(f"%{term}%"),
                    Facility.city.ilike(f"%{term}%"),
                    Facility.state.ilike(f"%{term}%"),
                    Facility.usda_license.ilike(f"%{term}%")
                )
            )
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        facilities = query.limit(limit).all()
        
        return [
            {
                "entity_type": "facility",
                "entity_id": str(f.facility_id),
                "name": f.exhibitor_name,
                "city": f.city or "",
                "state": f.state or "",
                "usda_license": f.usda_license or "",
                "tiger_count": f.tiger_count or 0,
                "is_reference": f.is_reference_facility if hasattr(f, 'is_reference_facility') else False,
                "match_score": 1.0
            }
            for f in facilities
        ]
    
    def _search_tigers(
        self,
        search_terms: List[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search tigers"""
        query = self.session.query(Tiger)
        
        # Build search conditions
        conditions = []
        for term in search_terms:
            # Only search on string fields, not UUIDs (which can't use LIKE)
            name_conditions = []
            if hasattr(Tiger, 'name') and Tiger.name is not None:
                name_conditions.append(Tiger.name.ilike(f"%{term}%"))
            if hasattr(Tiger, 'alias') and Tiger.alias is not None:
                name_conditions.append(Tiger.alias.ilike(f"%{term}%"))
            
            if name_conditions:
                conditions.append(or_(*name_conditions))
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        tigers = query.limit(limit).all()
        
        return [
            {
                "entity_type": "tiger",
                "entity_id": str(t.tiger_id) if hasattr(t, 'tiger_id') else str(t.id),
                "name": t.name if hasattr(t, 'name') else None,
                "facility_id": str(t.facility_id) if hasattr(t, 'facility_id') else None,
                "status": t.status if hasattr(t, 'status') else None,
                "match_score": 1.0
            }
            for t in tigers
        ]
    
    def _search_steps(
        self,
        search_terms: List[str],
        limit: int,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Search investigation steps"""
        query = self.session.query(InvestigationStep).join(Investigation)
        
        # Filter by user if provided
        if user_id:
            query = query.filter(Investigation.created_by == user_id)
        
        # Build search conditions
        conditions = []
        for term in search_terms:
            conditions.append(
                or_(
                    InvestigationStep.step_type.ilike(f"%{term}%"),
                    InvestigationStep.agent_name.ilike(f"%{term}%")
                )
            )
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        steps = query.limit(limit).all()
        
        return [
            {
                "entity_type": "step",
                "entity_id": str(step.step_id),
                "investigation_id": str(step.investigation_id),
                "step_type": step.step_type,
                "agent_name": step.agent_name or "",
                "status": step.status,
                "timestamp": step.timestamp.isoformat() if step.timestamp else None,
                "match_score": 1.0
            }
            for step in steps
        ]


def get_global_search_service(session: Session) -> GlobalSearchService:
    """Get global search service instance"""
    return GlobalSearchService(session)

