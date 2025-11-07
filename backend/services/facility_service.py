"""Service layer for Facility operations"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime

from backend.database.models import Facility, Tiger
from backend.utils.logging import get_logger

logger = get_logger(__name__)


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
    
    def bulk_import_facilities(
        self,
        facilities_data: List[Dict[str, Any]],
        update_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Bulk import facilities from Excel data
        
        Args:
            facilities_data: List of facility data dictionaries
            update_existing: If True, update existing facilities; if False, skip them
            
        Returns:
            Dictionary with import statistics
        """
        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
        
        for facility_data in facilities_data:
            try:
                exhibitor_name = facility_data.get('exhibitor_name')
                if not exhibitor_name:
                    stats['skipped'] += 1
                    continue
                
                usda_license = facility_data.get('usda_license')
                
                # Check if facility exists
                existing_facility = None
                if usda_license:
                    existing_facility = self.get_facility_by_license(usda_license)
                
                if not existing_facility:
                    # Try to find by name
                    facilities = self.get_facilities(
                        search_query=exhibitor_name,
                        limit=10
                    )
                    for fac in facilities:
                        if fac.exhibitor_name.lower() == exhibitor_name.lower():
                            existing_facility = fac
                            break
                
                if existing_facility:
                    if update_existing:
                        # Update existing facility
                        for key, value in facility_data.items():
                            if key != 'facility_id' and hasattr(existing_facility, key):
                                setattr(existing_facility, key, value)
                        stats['updated'] += 1
                    else:
                        stats['skipped'] += 1
                else:
                    # Create new facility
                    facility = Facility(
                        exhibitor_name=facility_data.get('exhibitor_name'),
                        usda_license=facility_data.get('usda_license'),
                        state=facility_data.get('state'),
                        city=facility_data.get('city'),
                        address=facility_data.get('address'),
                        tiger_count=facility_data.get('tiger_count', 0),
                        tiger_capacity=facility_data.get('tiger_capacity'),
                        social_media_links=facility_data.get('social_media_links', {}),
                        website=facility_data.get('website'),
                        ir_date=facility_data.get('ir_date'),
                        accreditation_status=facility_data.get('accreditation_status', 'Non-Accredited'),
                        is_reference_facility=facility_data.get('is_reference_facility', True),
                        data_source=facility_data.get('data_source', 'tpc_non_accredited_facilities'),
                        reference_dataset_version=facility_data.get('reference_dataset_version'),
                        reference_metadata=facility_data.get('reference_metadata', {})
                    )
                    self.session.add(facility)
                    stats['created'] += 1
                
                self.session.commit()
                
            except Exception as e:
                logger.error(f"Error importing facility {facility_data.get('exhibitor_name', 'unknown')}: {e}", exc_info=True)
                stats['errors'].append({
                    'facility': facility_data.get('exhibitor_name', 'unknown'),
                    'error': str(e)
                })
                self.session.rollback()
        
        return stats

