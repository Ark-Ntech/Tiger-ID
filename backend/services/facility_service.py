"""Service layer for Facility operations.

This service uses FacilityRepository for all database operations,
following the repository pattern for clean separation of concerns.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from backend.database.models import Facility, Tiger
from backend.repositories.facility_repository import FacilityRepository
from backend.repositories.tiger_repository import TigerRepository
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class FacilityService:
    """Service for facility-related operations.

    Uses FacilityRepository for all database access, keeping the service
    layer focused on business logic.
    """

    def __init__(self, session: Session):
        """Initialize service with database session and repositories.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.facility_repo = FacilityRepository(session)
        self.tiger_repo = TigerRepository(session)

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
        """Create a new facility record.

        Args:
            exhibitor_name: Name of the exhibitor/facility
            usda_license: Optional USDA license number
            state: Optional state abbreviation
            city: Optional city name
            address: Optional full address
            tiger_count: Initial tiger count (default 0)
            tiger_capacity: Optional maximum tiger capacity
            social_media_links: Optional dict of social media URLs
            website: Optional website URL
            accreditation_status: Optional accreditation status

        Returns:
            Created Facility object
        """
        # Pass native Python objects - JSONDict TypeDecorator handles serialization
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
        return self.facility_repo.create(facility)

    def get_facility(self, facility_id: UUID) -> Optional[Facility]:
        """Get facility by ID.

        Args:
            facility_id: UUID of the facility

        Returns:
            Facility if found, None otherwise
        """
        return self.facility_repo.get_by_id(facility_id)

    def get_facility_by_license(self, usda_license: str) -> Optional[Facility]:
        """Get facility by USDA license number.

        Args:
            usda_license: USDA license string

        Returns:
            Facility if found, None otherwise
        """
        return self.facility_repo.get_by_usda_license(usda_license)

    def get_facilities(
        self,
        state: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Facility]:
        """Get list of facilities with filters.

        Args:
            state: Optional state filter
            search_query: Optional search string for name/license
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            List of matching Facility objects
        """
        if search_query:
            # Use repository search method for comprehensive search
            page = (offset // limit) + 1 if limit > 0 else 1
            result = self.facility_repo.search(search_query, page=page, page_size=limit)
            facilities = result.items

            # Apply state filter if provided
            if state:
                facilities = [f for f in facilities if f.state == state]
            return facilities

        if state:
            return self.facility_repo.get_by_state(state)

        return self.facility_repo.get_all(limit=limit, offset=offset)

    def update_facility(
        self,
        facility_id: UUID,
        **updates
    ) -> Optional[Facility]:
        """Update facility record.

        Args:
            facility_id: UUID of the facility to update
            **updates: Key-value pairs of fields to update

        Returns:
            Updated Facility or None if not found
        """
        facility = self.facility_repo.get_by_id(facility_id)
        if not facility:
            return None

        for key, value in updates.items():
            if hasattr(facility, key):
                setattr(facility, key, value)

        return self.facility_repo.update(facility)

    def get_facility_tigers(self, facility_id: UUID) -> List[Tiger]:
        """Get all tigers associated with a facility.

        Args:
            facility_id: UUID of the facility

        Returns:
            List of Tiger objects at the facility
        """
        return self.tiger_repo.get_by_facility(facility_id)

    def update_tiger_count(self, facility_id: UUID) -> Optional[Facility]:
        """Update tiger count for a facility based on database.

        Counts tigers in the database and updates the facility's tiger_count field.

        Args:
            facility_id: UUID of the facility

        Returns:
            Updated Facility or None if not found
        """
        facility = self.facility_repo.get_by_id(facility_id)
        if not facility:
            return None

        tigers = self.tiger_repo.get_by_facility(facility_id)
        tiger_count = len(tigers)

        return self.facility_repo.update_tiger_count(facility_id, tiger_count)
    
    def bulk_import_facilities(
        self,
        facilities_data: List[Dict[str, Any]],
        update_existing: bool = True
    ) -> Dict[str, Any]:
        """Bulk import facilities from Excel data.

        Args:
            facilities_data: List of facility data dictionaries
            update_existing: If True, update existing facilities; if False, skip them

        Returns:
            Dictionary with import statistics including created, updated, skipped counts
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

                # Check if facility exists by license
                existing_facility = None
                if usda_license:
                    existing_facility = self.facility_repo.get_by_usda_license(usda_license)

                if not existing_facility:
                    # Try to find by exact name match
                    existing_facility = self.facility_repo.get_by_exhibitor_name(exhibitor_name)

                if existing_facility:
                    if update_existing:
                        # Update existing facility
                        for key, value in facility_data.items():
                            if key != 'facility_id' and hasattr(existing_facility, key):
                                setattr(existing_facility, key, value)
                        self.facility_repo.update(existing_facility)
                        stats['updated'] += 1
                    else:
                        stats['skipped'] += 1
                else:
                    # Create new facility using repository
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
                    self.facility_repo.create(facility)
                    stats['created'] += 1

            except Exception as e:
                logger.error(
                    f"Error importing facility {facility_data.get('exhibitor_name', 'unknown')}: {e}",
                    exc_info=True
                )
                stats['errors'].append({
                    'facility': facility_data.get('exhibitor_name', 'unknown'),
                    'error': str(e)
                })
                self.session.rollback()

        return stats

