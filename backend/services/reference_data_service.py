"""Service for querying and managing reference facility data"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.database import Facility
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ReferenceDataService:
    """Service for managing reference facility data"""
    
    def __init__(self, session: Session):
        """
        Initialize Reference Data Service
        
        Args:
            session: Database session
        """
        self.session = session
    
    def is_reference_facility(self, facility_id: UUID) -> bool:
        """
        Check if a facility is in the reference dataset
        
        Args:
            facility_id: Facility ID to check
            
        Returns:
            True if facility is a reference facility, False otherwise
        """
        facility = self.session.query(Facility).filter(
            and_(
                Facility.facility_id == facility_id,
                Facility.is_reference_facility == True
            )
        ).first()
        
        return facility is not None
    
    def get_reference_facilities(
        self,
        state: Optional[str] = None,
        data_source: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Facility]:
        """
        Get all reference facilities, optionally filtered
        
        Args:
            state: Filter by state
            data_source: Filter by data source (e.g., 'tpc_reference')
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of reference facilities
        """
        query = self.session.query(Facility).filter(
            Facility.is_reference_facility == True
        )
        
        if state:
            query = query.filter(Facility.state == state)
        
        if data_source:
            query = query.filter(Facility.data_source == data_source)
        
        return query.order_by(Facility.exhibitor_name).limit(limit).offset(offset).all()
    
    def match_facility_by_name(
        self,
        name: str,
        threshold: float = 0.8
    ) -> Optional[Facility]:
        """
        Match a facility by name (fuzzy match)
        
        Args:
            name: Facility name to match
            threshold: Similarity threshold (not used in current implementation)
            
        Returns:
            Matching facility if found, None otherwise
        """
        if not name or not name.strip():
            return None
        
        name_lower = name.lower().strip()
        
        # Try exact match first
        facility = self.session.query(Facility).filter(
            and_(
                Facility.is_reference_facility == True,
                Facility.exhibitor_name.ilike(name_lower)
            )
        ).first()
        
        if facility:
            return facility
        
        # Try case-insensitive partial match
        facility = self.session.query(Facility).filter(
            and_(
                Facility.is_reference_facility == True,
                Facility.exhibitor_name.ilike(f"%{name_lower}%")
            )
        ).first()
        
        return facility
    
    def match_facility_by_license(
        self,
        usda_license: str
    ) -> Optional[Facility]:
        """
        Match a facility by USDA license number
        
        Args:
            usda_license: USDA license number
            
        Returns:
            Matching facility if found, None otherwise
        """
        if not usda_license or not usda_license.strip():
            return None
        
        facility = self.session.query(Facility).filter(
            and_(
                Facility.is_reference_facility == True,
                Facility.usda_license == usda_license.strip()
            )
        ).first()
        
        return facility
    
    def match_facility_by_location(
        self,
        state: Optional[str] = None,
        city: Optional[str] = None,
        address: Optional[str] = None
    ) -> List[Facility]:
        """
        Match facilities by location
        
        Args:
            state: State name
            city: City name
            address: Address string
            
        Returns:
            List of matching facilities
        """
        query = self.session.query(Facility).filter(
            Facility.is_reference_facility == True
        )
        
        conditions = []
        
        if state:
            conditions.append(Facility.state.ilike(f"%{state}%"))
        
        if city:
            conditions.append(Facility.city.ilike(f"%{city}%"))
        
        if address:
            conditions.append(Facility.address.ilike(f"%{address}%"))
        
        if conditions:
            query = query.filter(or_(*conditions))
        
        return query.all()
    
    def match_facility_by_social_media(
        self,
        url: str
    ) -> Optional[Facility]:
        """
        Match facility by social media URL or website
        
        Args:
            url: Social media URL or website URL
            
        Returns:
            Matching facility if found, None otherwise
        """
        if not url or not url.strip():
            return None
        
        url_lower = url.lower().strip()
        
        # Search in social_media_links JSON field
        # PostgreSQL JSONB query for reference facilities
        facilities = self.session.query(Facility).filter(
            Facility.is_reference_facility == True
        ).all()
        
        for facility in facilities:
            # Check website
            if facility.website and url_lower in facility.website.lower():
                return facility
            
            # Check social media links
            if facility.social_media_links:
                for platform, link_url in facility.social_media_links.items():
                    if link_url and url_lower in str(link_url).lower():
                        return facility
        
        return None
    
    def find_matching_facilities(
        self,
        name: Optional[str] = None,
        usda_license: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        url: Optional[str] = None
    ) -> List[Facility]:
        """
        Find matching reference facilities using multiple criteria
        
        Args:
            name: Facility name
            usda_license: USDA license number
            state: State location
            city: City location
            url: Website or social media URL
            
        Returns:
            List of matching facilities (can be multiple if partial matches)
        """
        matches = set()
        
        # Try by USDA license (most specific)
        if usda_license:
            facility = self.match_facility_by_license(usda_license)
            if facility:
                matches.add(facility)
        
        # Try by name
        if name:
            facility = self.match_facility_by_name(name)
            if facility:
                matches.add(facility)
        
        # Try by URL
        if url:
            facility = self.match_facility_by_social_media(url)
            if facility:
                matches.add(facility)
        
        # Try by location
        if state or city:
            location_matches = self.match_facility_by_location(
                state=state,
                city=city
            )
            matches.update(location_matches)
        
        return list(matches)
    
    def get_reference_facility_count(
        self,
        state: Optional[str] = None,
        data_source: Optional[str] = None
    ) -> int:
        """
        Get count of reference facilities
        
        Args:
            state: Filter by state
            data_source: Filter by data source
            
        Returns:
            Count of reference facilities
        """
        query = self.session.query(Facility).filter(
            Facility.is_reference_facility == True
        )
        
        if state:
            query = query.filter(Facility.state == state)
        
        if data_source:
            query = query.filter(Facility.data_source == data_source)
        
        return query.count()
    
    def get_reference_facilities_by_state(self) -> Dict[str, int]:
        """
        Get count of reference facilities grouped by state
        
        Returns:
            Dictionary mapping state names to facility counts
        """
        facilities = self.session.query(Facility).filter(
            Facility.is_reference_facility == True
        ).all()
        
        state_counts = {}
        for facility in facilities:
            state = facility.state or 'Unknown'
            state_counts[state] = state_counts.get(state, 0) + 1
        
        return state_counts
    
    def boost_priority_for_reference_facilities(
        self,
        facility_ids: List[UUID]
    ) -> Dict[UUID, float]:
        """
        Calculate priority boost for facilities if they are reference facilities
        
        Args:
            facility_ids: List of facility IDs
            
        Returns:
            Dictionary mapping facility_id to priority boost (0.0 to 1.0)
        """
        priority_boosts = {fid: 0.0 for fid in facility_ids}
        
        if not facility_ids:
            return priority_boosts
        
        reference_facilities = self.session.query(Facility).filter(
            and_(
                Facility.facility_id.in_(facility_ids),
                Facility.is_reference_facility == True
            )
        ).all()
        
        # Boost priority for reference facilities
        for facility in reference_facilities:
            priority_boosts[facility.facility_id] = 0.5  # 50% priority boost
        
        return priority_boosts

