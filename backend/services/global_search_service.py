"""Global search service for unified search across all entities"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from backend.database.models import Investigation, Evidence, Facility, Tiger, TigerImage, InvestigationStep
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
        Perform global search across all entities.

        Returns results in the format expected by the frontend GlobalSearchResponse:
        {
            "query": str,
            "results": {
                "investigations": [...],
                "tigers": [...],
                "facilities": [...],
                "evidence": [...]
            },
            "counts": {
                "investigations": int,
                "tigers": int,
                "facilities": int,
                "evidence": int
            },
            "total_results": int
        }

        Args:
            query: Search query string
            entity_types: Filter by entity types (investigations, evidence, facilities, tigers)
            limit: Maximum results per entity type
            user_id: Optional user ID to filter by permissions

        Returns:
            Search results grouped by entity type under a "results" key
        """
        inv_results = []
        ev_results = []
        fac_results = []
        tiger_results = []

        search_terms = query.lower().split()

        # Search investigations
        if not entity_types or "investigations" in entity_types:
            inv_results = self._search_investigations(search_terms, limit, user_id)

        # Search evidence
        if not entity_types or "evidence" in entity_types:
            ev_results = self._search_evidence(search_terms, limit, user_id)

        # Search facilities
        if not entity_types or "facilities" in entity_types:
            fac_results = self._search_facilities(search_terms, limit)

        # Search tigers
        if not entity_types or "tigers" in entity_types:
            tiger_results = self._search_tigers(search_terms, limit)

        total = len(inv_results) + len(ev_results) + len(fac_results) + len(tiger_results)

        return {
            "query": query,
            "results": {
                "investigations": inv_results,
                "tigers": tiger_results,
                "facilities": fac_results,
                "evidence": ev_results,
            },
            "counts": {
                "investigations": len(inv_results),
                "tigers": len(tiger_results),
                "facilities": len(fac_results),
                "evidence": len(ev_results),
            },
            "total_results": total,
        }
    
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
                "id": str(inv.investigation_id),
                "entity_type": "investigation",
                "title": inv.title,
                "description": inv.description or "",
                "status": inv.status.value if hasattr(inv.status, 'value') else inv.status,
                "priority": inv.priority.value if hasattr(inv.priority, 'value') else inv.priority,
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
                "id": str(ev.evidence_id),
                "entity_type": "evidence",
                "investigation_id": str(ev.investigation_id) if ev.investigation_id else None,
                "title": (ev.extracted_text or "")[:100],
                "description": (ev.extracted_text or "")[:200],
                "source_type": ev.source_type.value if hasattr(ev.source_type, 'value') else ev.source_type,
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
                "id": str(f.facility_id),
                "entity_type": "facility",
                "name": f.exhibitor_name,
                "exhibitor_name": f.exhibitor_name,
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
        """Search tigers by name, alias, notes, and status"""
        from sqlalchemy.orm import joinedload

        query = self.session.query(Tiger).options(joinedload(Tiger.images))

        # Build search conditions
        conditions = []
        for term in search_terms:
            term_conditions = []
            if Tiger.name is not None:
                term_conditions.append(Tiger.name.ilike(f"%{term}%"))
            if Tiger.alias is not None:
                term_conditions.append(Tiger.alias.ilike(f"%{term}%"))
            if Tiger.notes is not None:
                term_conditions.append(Tiger.notes.ilike(f"%{term}%"))
            if Tiger.status is not None:
                term_conditions.append(Tiger.status.ilike(f"%{term}%"))

            if term_conditions:
                conditions.append(or_(*term_conditions))

        if conditions:
            query = query.filter(and_(*conditions))

        tigers = query.limit(limit).all()

        return [
            {
                "id": str(t.tiger_id),
                "entity_type": "tiger",
                "name": t.name,
                "alias": t.alias,
                "facility_id": str(t.origin_facility_id) if t.origin_facility_id else None,
                "status": t.status,
                "images": [img.image_path for img in t.images] if t.images else [],
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
                "id": str(step.step_id),
                "entity_type": "step",
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

