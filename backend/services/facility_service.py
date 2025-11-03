"""Service layer for Facility operations"""

from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database.models import Facility, Tiger


class FacilityService:
    """Service for facility-related operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_facility(
        self,
        exhibitor_name: str,
        usda_license: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        address: Optional[str] = None,
        tiger_count: int = 0,
        tiger_capacity: Optional[int] = None,
        social_media_links: Optional[Dict] = None,
        website: Optional[str] = None,
        accreditation_status: Optional[str] = None
    ) -> Facility:
        """Create a new facility record"""
        facility = Facility(
            exhibitor_name=exhibitor_name,
            usda_license=usda_license,
            state=state,
            city=city,
            address=address,
            tiger_count=tiger_count,
            tiger_capacity=tiger_capacity,
            social_media_links=social_media_links or {},
            website=website,
            accreditation_status=accreditation_status
        )
        self.session.add(facility)
        self.session.commit()
        self.session.refresh(facility)
        return facility
    
    def get_facility(self, facility_id: UUID) -> Optional[Facility]:
        """Get facility by ID"""
        return self.session.query(Facility).filter(
            Facility.facility_id == facility_id
        ).first()
    
    def get_facility_by_license(self, usda_license: str) -> Optional[Facility]:
        """Get facility by USDA license number"""
        return self.session.query(Facility).filter(
            Facility.usda_license == usda_license
        ).first()
    
    def get_facilities(
        self,
        state: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Facility]:
        """Get list of facilities with filters"""
        query = self.session.query(Facility)
        
        if state:
            query = query.filter(Facility.state == state)
        
        if search_query:
            query = query.filter(
                or_(
                    Facility.exhibitor_name.ilike(f"%{search_query}%"),
                    Facility.usda_license.ilike(f"%{search_query}%")
                )
            )
        
        return query.limit(limit).offset(offset).all()
    
    def update_facility(
        self,
        facility_id: UUID,
        **updates
    ) -> Optional[Facility]:
        """Update facility record"""
        facility = self.get_facility(facility_id)
        if not facility:
            return None
        
        for key, value in updates.items():
            if hasattr(facility, key):
                setattr(facility, key, value)
        
        self.session.commit()
        self.session.refresh(facility)
        return facility
    
    def get_facility_tigers(self, facility_id: UUID) -> List[Tiger]:
        """Get all tigers associated with a facility"""
        return self.session.query(Tiger).filter(
            Tiger.origin_facility_id == facility_id
        ).all()
    
    def update_tiger_count(self, facility_id: UUID) -> Optional[Facility]:
        """Update tiger count for a facility based on database"""
        facility = self.get_facility(facility_id)
        if not facility:
            return None
        
        tiger_count = self.session.query(Tiger).filter(
            Tiger.origin_facility_id == facility_id
        ).count()
        
        facility.tiger_count = tiger_count
        self.session.commit()
        self.session.refresh(facility)
        return facility

