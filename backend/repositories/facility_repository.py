"""Repository for Facility data access."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from backend.database.models import Facility
from backend.repositories.base import BaseRepository, PaginatedResult, FilterCriteria


class FacilityRepository(BaseRepository[Facility]):
    """Repository for Facility data access."""

    def __init__(self, db: Session):
        super().__init__(db, Facility)

    def get_by_id(self, facility_id: UUID) -> Optional[Facility]:
        """Get facility by ID.

        Args:
            facility_id: UUID of the facility

        Returns:
            Facility if found, None otherwise
        """
        return (
            self.db.query(Facility)
            .filter(Facility.facility_id == facility_id)
            .first()
        )

    def get_by_usda_license(self, usda_license: str) -> Optional[Facility]:
        """Get facility by USDA license number.

        Args:
            usda_license: USDA license string

        Returns:
            Facility if found, None otherwise
        """
        return (
            self.db.query(Facility)
            .filter(Facility.usda_license == usda_license)
            .first()
        )

    def get_by_exhibitor_name(self, exhibitor_name: str) -> Optional[Facility]:
        """Get facility by exhibitor name.

        Args:
            exhibitor_name: Exhibitor name string

        Returns:
            Facility if found, None otherwise
        """
        return (
            self.db.query(Facility)
            .filter(Facility.exhibitor_name == exhibitor_name)
            .first()
        )

    def get_by_state(self, state: str) -> List[Facility]:
        """Get all facilities in a state.

        Args:
            state: State abbreviation or name

        Returns:
            List of Facility objects
        """
        return (
            self.db.query(Facility)
            .filter(Facility.state == state)
            .all()
        )

    def get_by_city(self, city: str, state: Optional[str] = None) -> List[Facility]:
        """Get all facilities in a city.

        Args:
            city: City name
            state: Optional state filter

        Returns:
            List of Facility objects
        """
        query = self.db.query(Facility).filter(Facility.city == city)
        if state:
            query = query.filter(Facility.state == state)
        return query.all()

    def get_reference_facilities(self) -> List[Facility]:
        """Get all reference facilities.

        Returns:
            List of reference Facility objects
        """
        return (
            self.db.query(Facility)
            .filter(Facility.is_reference_facility == True)
            .all()
        )

    def get_discovered_facilities(self) -> List[Facility]:
        """Get all facilities discovered through investigations.

        Returns:
            List of discovered Facility objects
        """
        return (
            self.db.query(Facility)
            .filter(Facility.discovered_at.isnot(None))
            .all()
        )

    def get_by_discovery_investigation(
        self,
        investigation_id: UUID
    ) -> List[Facility]:
        """Get facilities discovered by a specific investigation.

        Args:
            investigation_id: UUID of the investigation

        Returns:
            List of Facility objects
        """
        return (
            self.db.query(Facility)
            .filter(Facility.discovered_by_investigation_id == investigation_id)
            .all()
        )

    def get_with_tigers(self, min_tiger_count: int = 1) -> List[Facility]:
        """Get facilities with at least a minimum number of tigers.

        Args:
            min_tiger_count: Minimum tiger count

        Returns:
            List of Facility objects
        """
        return (
            self.db.query(Facility)
            .filter(Facility.tiger_count >= min_tiger_count)
            .order_by(desc(Facility.tiger_count))
            .all()
        )

    def get_recently_crawled(self, limit: int = 10) -> List[Facility]:
        """Get recently crawled facilities.

        Args:
            limit: Maximum number of results

        Returns:
            List of Facility objects
        """
        return (
            self.db.query(Facility)
            .filter(Facility.last_crawled_at.isnot(None))
            .order_by(desc(Facility.last_crawled_at))
            .limit(limit)
            .all()
        )

    def get_needing_crawl(
        self,
        days_since_crawl: int = 7,
        limit: int = 50
    ) -> List[Facility]:
        """Get facilities that haven't been crawled recently.

        Args:
            days_since_crawl: Days since last crawl to consider stale
            limit: Maximum number of results

        Returns:
            List of Facility objects needing crawl
        """
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days_since_crawl)

        return (
            self.db.query(Facility)
            .filter(
                or_(
                    Facility.last_crawled_at.is_(None),
                    Facility.last_crawled_at < cutoff
                )
            )
            .order_by(Facility.last_crawled_at.nullsfirst())
            .limit(limit)
            .all()
        )

    def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResult[Facility]:
        """Search facilities by name, license, or location.

        Args:
            query: Search query string
            page: Page number
            page_size: Results per page

        Returns:
            PaginatedResult with matching facilities
        """
        base_query = self.db.query(Facility).filter(
            or_(
                Facility.exhibitor_name.ilike(f"%{query}%"),
                Facility.usda_license.ilike(f"%{query}%"),
                Facility.city.ilike(f"%{query}%"),
                Facility.state.ilike(f"%{query}%"),
                Facility.address.ilike(f"%{query}%")
            )
        )

        total = base_query.count()
        offset = (page - 1) * page_size
        items = base_query.order_by(Facility.exhibitor_name).limit(page_size).offset(offset).all()

        return PaginatedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )

    def get_paginated_with_filters(
        self,
        page: int = 1,
        page_size: int = 20,
        state: Optional[str] = None,
        is_reference: Optional[bool] = None,
        has_tigers: Optional[bool] = None
    ) -> PaginatedResult[Facility]:
        """Get paginated facilities with common filters.

        Args:
            page: Page number
            page_size: Results per page
            state: Optional state filter
            is_reference: Optional reference filter
            has_tigers: Optional tigers filter

        Returns:
            PaginatedResult with filtered facilities
        """
        filters = []
        if state:
            filters.append(FilterCriteria("state", "eq", state))
        if is_reference is not None:
            filters.append(FilterCriteria("is_reference_facility", "eq", is_reference))
        if has_tigers:
            filters.append(FilterCriteria("tiger_count", "gt", 0))

        return self.get_paginated(
            page=page,
            page_size=page_size,
            sort_by="exhibitor_name",
            sort_order="asc",
            filters=filters if filters else None
        )

    def update_tiger_count(
        self,
        facility_id: UUID,
        tiger_count: int
    ) -> Optional[Facility]:
        """Update facility's tiger count.

        Args:
            facility_id: UUID of the facility
            tiger_count: New tiger count

        Returns:
            Updated Facility or None if not found
        """
        facility = self.get_by_id(facility_id)
        if not facility:
            return None

        facility.tiger_count = tiger_count
        return self.update(facility)

    def update_crawl_timestamp(
        self,
        facility_id: UUID
    ) -> Optional[Facility]:
        """Update facility's last crawled timestamp.

        Args:
            facility_id: UUID of the facility

        Returns:
            Updated Facility or None if not found
        """
        facility = self.get_by_id(facility_id)
        if not facility:
            return None

        facility.last_crawled_at = datetime.utcnow()
        return self.update(facility)

    def get_facilities_with_coordinates(self) -> List[Facility]:
        """Get all facilities that have geocoded coordinates.

        Returns:
            List of geocoded Facility objects
        """
        return (
            self.db.query(Facility)
            .filter(Facility.coordinates.isnot(None))
            .all()
        )

    def get_states_with_facilities(self) -> List[str]:
        """Get list of unique states with facilities.

        Returns:
            List of state strings
        """
        results = (
            self.db.query(Facility.state)
            .filter(Facility.state.isnot(None))
            .distinct()
            .order_by(Facility.state)
            .all()
        )
        return [r[0] for r in results]
