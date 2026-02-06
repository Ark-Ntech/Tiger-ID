"""Repository for Tiger and TigerImage data access."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from backend.database.models import Tiger, TigerImage, TigerStatus
from backend.repositories.base import BaseRepository, PaginatedResult, FilterCriteria


class TigerImageRepository(BaseRepository[TigerImage]):
    """Repository for TigerImage data access."""

    def __init__(self, db: Session):
        super().__init__(db, TigerImage)

    def get_by_tiger_id(self, tiger_id: UUID) -> List[TigerImage]:
        """Get all images for a tiger.

        Args:
            tiger_id: UUID of the tiger

        Returns:
            List of TigerImage objects
        """
        return (
            self.db.query(TigerImage)
            .filter(TigerImage.tiger_id == str(tiger_id))
            .all()
        )

    def get_verified_images(self, tiger_id: UUID) -> List[TigerImage]:
        """Get only verified images for a tiger.

        Args:
            tiger_id: UUID of the tiger

        Returns:
            List of verified TigerImage objects
        """
        return (
            self.db.query(TigerImage)
            .filter(
                and_(
                    TigerImage.tiger_id == str(tiger_id),
                    TigerImage.verified == True
                )
            )
            .all()
        )

    def get_reference_images(self) -> List[TigerImage]:
        """Get all reference images (ATRW dataset).

        Returns:
            List of reference TigerImage objects
        """
        return (
            self.db.query(TigerImage)
            .filter(TigerImage.is_reference == True)
            .all()
        )

    def get_by_investigation_id(self, investigation_id: UUID) -> List[TigerImage]:
        """Get images discovered by a specific investigation.

        Args:
            investigation_id: UUID of the investigation

        Returns:
            List of TigerImage objects
        """
        return (
            self.db.query(TigerImage)
            .filter(TigerImage.discovered_by_investigation_id == str(investigation_id))
            .all()
        )


class TigerRepository(BaseRepository[Tiger]):
    """Repository for Tiger data access."""

    def __init__(self, db: Session):
        super().__init__(db, Tiger)
        self.image_repo = TigerImageRepository(db)

    def get_by_id(self, tiger_id: UUID) -> Optional[Tiger]:
        """Get tiger by ID.

        Args:
            tiger_id: UUID of the tiger

        Returns:
            Tiger if found, None otherwise
        """
        return (
            self.db.query(Tiger)
            .filter(Tiger.tiger_id == str(tiger_id))
            .first()
        )

    def get_by_name(self, name: str) -> Optional[Tiger]:
        """Get tiger by name.

        Args:
            name: Name of the tiger

        Returns:
            Tiger if found, None otherwise
        """
        return (
            self.db.query(Tiger)
            .filter(Tiger.name == name)
            .first()
        )

    def get_by_alias(self, alias: str) -> Optional[Tiger]:
        """Get tiger by alias.

        Args:
            alias: Alias of the tiger

        Returns:
            Tiger if found, None otherwise
        """
        return (
            self.db.query(Tiger)
            .filter(Tiger.alias == alias)
            .first()
        )

    def get_by_facility(self, facility_id: UUID) -> List[Tiger]:
        """Get all tigers at a facility.

        Args:
            facility_id: UUID of the facility

        Returns:
            List of Tiger objects
        """
        return (
            self.db.query(Tiger)
            .filter(Tiger.origin_facility_id == str(facility_id))
            .all()
        )

    def get_by_status(self, status: TigerStatus) -> List[Tiger]:
        """Get all tigers with a specific status.

        Args:
            status: TigerStatus enum value

        Returns:
            List of Tiger objects
        """
        # Convert enum to its string value for SQLite compatibility
        status_value = status.value if hasattr(status, 'value') else status
        return (
            self.db.query(Tiger)
            .filter(Tiger.status == status_value)
            .all()
        )

    def get_reference_tigers(self) -> List[Tiger]:
        """Get all reference tigers (ATRW dataset).

        Returns:
            List of reference Tiger objects
        """
        return (
            self.db.query(Tiger)
            .filter(Tiger.is_reference == True)
            .all()
        )

    def get_discovered_tigers(self) -> List[Tiger]:
        """Get all tigers discovered through investigations.

        Returns:
            List of discovered Tiger objects
        """
        return (
            self.db.query(Tiger)
            .filter(Tiger.is_reference == False)
            .all()
        )

    def get_recently_seen(self, limit: int = 10) -> List[Tiger]:
        """Get tigers ordered by last seen date.

        Args:
            limit: Maximum number of results

        Returns:
            List of Tiger objects
        """
        return (
            self.db.query(Tiger)
            .filter(Tiger.last_seen_date.isnot(None))
            .order_by(desc(Tiger.last_seen_date))
            .limit(limit)
            .all()
        )

    def get_with_images(self, tiger_id: UUID) -> Optional[Dict[str, Any]]:
        """Get tiger with all associated images.

        Args:
            tiger_id: UUID of the tiger

        Returns:
            Dictionary with tiger and images, or None if not found
        """
        tiger = self.get_by_id(tiger_id)
        if not tiger:
            return None

        images = self.image_repo.get_by_tiger_id(tiger_id)
        return {
            "tiger": tiger,
            "images": images,
            "image_count": len(images)
        }

    def get_related_tigers(
        self,
        tiger_id: UUID,
        limit: int = 5
    ) -> List[Tiger]:
        """Get tigers related to another tiger (same facility).

        Args:
            tiger_id: UUID of the tiger
            limit: Maximum number of results

        Returns:
            List of related Tiger objects
        """
        tiger = self.get_by_id(tiger_id)
        if not tiger or not tiger.origin_facility_id:
            return []

        return (
            self.db.query(Tiger)
            .filter(
                and_(
                    Tiger.origin_facility_id == tiger.origin_facility_id,
                    Tiger.tiger_id != str(tiger_id)
                )
            )
            .limit(limit)
            .all()
        )

    def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResult[Tiger]:
        """Search tigers by name or alias.

        Args:
            query: Search query string
            page: Page number
            page_size: Results per page

        Returns:
            PaginatedResult with matching tigers
        """
        search_filter = FilterCriteria("name", "ilike", query)
        return self.get_paginated(
            page=page,
            page_size=page_size,
            sort_by="created_at",
            sort_order="desc",
            filters=[search_filter]
        )

    def get_paginated_with_filters(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[TigerStatus] = None,
        facility_id: Optional[UUID] = None,
        is_reference: Optional[bool] = None
    ) -> PaginatedResult[Tiger]:
        """Get paginated tigers with common filters.

        Args:
            page: Page number
            page_size: Results per page
            status: Optional status filter
            facility_id: Optional facility filter
            is_reference: Optional reference filter

        Returns:
            PaginatedResult with filtered tigers
        """
        filters = []
        if status:
            filters.append(FilterCriteria("status", "eq", status))
        if facility_id:
            filters.append(FilterCriteria("origin_facility_id", "eq", facility_id))
        if is_reference is not None:
            filters.append(FilterCriteria("is_reference", "eq", is_reference))

        return self.get_paginated(
            page=page,
            page_size=page_size,
            sort_by="created_at",
            sort_order="desc",
            filters=filters if filters else None
        )

    def update_last_seen(
        self,
        tiger_id: UUID,
        location: str,
        seen_date: Any
    ) -> Optional[Tiger]:
        """Update tiger's last seen information.

        Args:
            tiger_id: UUID of the tiger
            location: Last seen location
            seen_date: Date last seen

        Returns:
            Updated Tiger or None if not found
        """
        tiger = self.get_by_id(tiger_id)
        if not tiger:
            return None

        tiger.last_seen_location = location
        tiger.last_seen_date = seen_date
        return self.update(tiger)

    # Image-related methods that delegate to image repository

    def get_images(self, tiger_id: UUID) -> List[TigerImage]:
        """Get all images for a tiger.

        Args:
            tiger_id: UUID of the tiger

        Returns:
            List of TigerImage objects
        """
        return self.image_repo.get_by_tiger_id(tiger_id)

    def add_image(self, image: TigerImage) -> TigerImage:
        """Add an image to a tiger.

        Args:
            image: TigerImage to add

        Returns:
            Created TigerImage
        """
        return self.image_repo.create(image)
