"""Service for managing saved searches"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.models import SavedSearch
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class SavedSearchService:
    """Service for saved searches"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_saved_search(
        self,
        user_id: UUID,
        name: str,
        search_criteria: Dict[str, Any],
        alert_enabled: bool = False
    ) -> SavedSearch:
        """
        Create a new saved search
        
        Args:
            user_id: User ID
            name: Search name
            search_criteria: Search criteria dictionary
            alert_enabled: Whether alerts are enabled
        
        Returns:
            Created saved search
        """
        saved_search = SavedSearch(
            user_id=user_id,
            name=name,
            search_criteria=search_criteria or {},
            alert_enabled=alert_enabled,
            last_executed=None,
            created_at=datetime.utcnow()
        )
        
        self.session.add(saved_search)
        self.session.commit()
        self.session.refresh(saved_search)
        
        return saved_search
    
    def get_saved_search(self, search_id: UUID) -> Optional[SavedSearch]:
        """Get saved search by ID"""
        return self.session.query(SavedSearch).filter(
            SavedSearch.search_id == search_id
        ).first()
    
    def get_saved_searches(
        self,
        user_id: Optional[UUID] = None,
        alert_enabled: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SavedSearch]:
        """
        Get saved searches with filters
        
        Args:
            user_id: Filter by user
            alert_enabled: Filter by alert status
            limit: Maximum results
            offset: Pagination offset
        
        Returns:
            List of saved searches
        """
        query = self.session.query(SavedSearch)
        
        if user_id:
            query = query.filter(SavedSearch.user_id == user_id)
        if alert_enabled is not None:
            query = query.filter(SavedSearch.alert_enabled == alert_enabled)
        
        query = query.order_by(desc(SavedSearch.created_at))
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def update_saved_search(
        self,
        search_id: UUID,
        name: Optional[str] = None,
        search_criteria: Optional[Dict[str, Any]] = None,
        alert_enabled: Optional[bool] = None
    ) -> Optional[SavedSearch]:
        """Update saved search"""
        saved_search = self.get_saved_search(search_id)
        if not saved_search:
            return None
        
        if name is not None:
            saved_search.name = name
        if search_criteria is not None:
            saved_search.search_criteria = search_criteria
        if alert_enabled is not None:
            saved_search.alert_enabled = alert_enabled
        
        self.session.commit()
        self.session.refresh(saved_search)
        
        return saved_search
    
    def delete_saved_search(self, search_id: UUID) -> bool:
        """Delete saved search"""
        saved_search = self.get_saved_search(search_id)
        if not saved_search:
            return False
        
        self.session.delete(saved_search)
        self.session.commit()
        
        return True
    
    def execute_saved_search(
        self,
        search_id: UUID
    ) -> Dict[str, Any]:
        """
        Execute a saved search
        
        Args:
            search_id: Saved search ID
        
        Returns:
            Search results
        """
        saved_search = self.get_saved_search(search_id)
        if not saved_search:
            return {"success": False, "error": "Saved search not found"}
        
        # Update last executed time
        saved_search.last_executed = datetime.utcnow()
        self.session.commit()
        
        # Execute search using GlobalSearchService or appropriate service
        # This is a placeholder - actual implementation depends on search type
        return {
            "success": True,
            "search_id": str(search_id),
            "criteria": saved_search.search_criteria,
            "results": []  # Would be populated by actual search execution
        }


def get_saved_search_service(session: Session) -> SavedSearchService:
    """Get saved search service instance"""
    return SavedSearchService(session)

