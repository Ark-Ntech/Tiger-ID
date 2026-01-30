"""Tiger query service.

Handles tiger data retrieval and listing operations.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from backend.utils.logging import get_logger
from backend.database.models import Tiger, TigerImage, TigerStatus
from backend.repositories.tiger_repository import TigerRepository
from backend.repositories.base import PaginatedResult

logger = get_logger(__name__)


class TigerQueryService:
    """Service for querying tiger data."""

    def __init__(
        self,
        db: Session,
        tiger_repo: Optional[TigerRepository] = None
    ):
        """Initialize query service.

        Args:
            db: Database session
            tiger_repo: Optional tiger repository (creates default if not provided)
        """
        self.db = db
        self.tiger_repo = tiger_repo or TigerRepository(db)

    async def get_tiger(self, tiger_id: UUID) -> Optional[Dict[str, Any]]:
        """Get tiger details with images.

        Args:
            tiger_id: UUID of the tiger

        Returns:
            Dictionary with tiger details, or None if not found
        """
        tiger = self.tiger_repo.get_by_id(tiger_id)

        if not tiger:
            return None

        images = self.tiger_repo.get_images(tiger_id)

        # Format images for response
        image_list = []
        for img in images:
            image_list.append({
                "id": str(img.image_id),
                "url": (
                    img.image_path if img.image_path.startswith('http')
                    else f"/api/v1/tigers/{tiger_id}/images/{img.image_id}"
                ),
                "path": img.image_path,
                "uploaded_by": str(img.uploaded_by) if img.uploaded_by else None,
                "meta_data": img.meta_data or {}
            })

        # Get related tigers (same facility)
        related_tigers = self.tiger_repo.get_related_tigers(tiger_id, limit=5)
        related_list = [
            {
                "tiger_id": str(related.tiger_id),
                "id": str(related.tiger_id),
                "name": related.name,
                "alias": related.alias,
                "status": (
                    related.status.value
                    if hasattr(related.status, 'value')
                    else str(related.status)
                )
            }
            for related in related_tigers
        ]

        return {
            "tiger_id": str(tiger.tiger_id),
            "id": str(tiger.tiger_id),  # For frontend compatibility
            "name": tiger.name,
            "alias": tiger.alias,
            "status": (
                tiger.status.value
                if hasattr(tiger.status, 'value')
                else str(tiger.status)
            ),
            "last_seen_location": tiger.last_seen_location,
            "last_seen_date": (
                tiger.last_seen_date.isoformat()
                if tiger.last_seen_date
                else None
            ),
            "image_count": len(images),
            "images": image_list,
            "notes": tiger.notes,
            "related_tigers": related_list,
            "origin_facility_id": (
                str(tiger.origin_facility_id)
                if tiger.origin_facility_id
                else None
            )
        }

    async def list_tigers(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        facility_id: Optional[UUID] = None,
        is_reference: Optional[bool] = None
    ) -> Dict[str, Any]:
        """List tigers with pagination and filtering.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            status: Optional status filter
            facility_id: Optional facility filter
            is_reference: Optional reference filter

        Returns:
            Dictionary with paginated tiger list
        """
        # Convert status string to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = TigerStatus(status)
            except ValueError:
                logger.warning(f"Invalid status value: {status}")

        result = self.tiger_repo.get_paginated_with_filters(
            page=page,
            page_size=page_size,
            status=status_enum,
            facility_id=facility_id,
            is_reference=is_reference
        )

        # Format tigers for response
        tigers = []
        for tiger in result.items:
            image_count = len(self.tiger_repo.get_images(tiger.tiger_id))
            tigers.append({
                "tiger_id": str(tiger.tiger_id),
                "id": str(tiger.tiger_id),
                "name": tiger.name,
                "alias": tiger.alias,
                "status": (
                    tiger.status.value
                    if hasattr(tiger.status, 'value')
                    else str(tiger.status)
                ),
                "last_seen_location": tiger.last_seen_location,
                "last_seen_date": (
                    tiger.last_seen_date.isoformat()
                    if tiger.last_seen_date
                    else None
                ),
                "image_count": image_count,
                "origin_facility_id": (
                    str(tiger.origin_facility_id)
                    if tiger.origin_facility_id
                    else None
                )
            })

        return {
            "data": tigers,
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages
        }

    async def search_tigers(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search tigers by name or alias.

        Args:
            query: Search query
            page: Page number
            page_size: Items per page

        Returns:
            Dictionary with search results
        """
        result = self.tiger_repo.search(
            query=query,
            page=page,
            page_size=page_size
        )

        tigers = []
        for tiger in result.items:
            tigers.append({
                "tiger_id": str(tiger.tiger_id),
                "id": str(tiger.tiger_id),
                "name": tiger.name,
                "alias": tiger.alias,
                "status": (
                    tiger.status.value
                    if hasattr(tiger.status, 'value')
                    else str(tiger.status)
                )
            })

        return {
            "data": tigers,
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
            "query": query
        }

    async def get_tiger_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tiger by name.

        Args:
            name: Tiger name

        Returns:
            Tiger dictionary or None
        """
        tiger = self.tiger_repo.get_by_name(name)
        if tiger:
            return await self.get_tiger(tiger.tiger_id)
        return None

    async def get_tigers_by_facility(
        self,
        facility_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get all tigers at a facility.

        Args:
            facility_id: UUID of the facility

        Returns:
            List of tiger dictionaries
        """
        tigers = self.tiger_repo.get_by_facility(facility_id)
        return [
            {
                "tiger_id": str(tiger.tiger_id),
                "id": str(tiger.tiger_id),
                "name": tiger.name,
                "alias": tiger.alias,
                "status": (
                    tiger.status.value
                    if hasattr(tiger.status, 'value')
                    else str(tiger.status)
                )
            }
            for tiger in tigers
        ]

    async def get_recently_seen(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently seen tigers.

        Args:
            limit: Maximum number of results

        Returns:
            List of tiger dictionaries
        """
        tigers = self.tiger_repo.get_recently_seen(limit=limit)
        return [
            {
                "tiger_id": str(tiger.tiger_id),
                "id": str(tiger.tiger_id),
                "name": tiger.name,
                "alias": tiger.alias,
                "last_seen_location": tiger.last_seen_location,
                "last_seen_date": (
                    tiger.last_seen_date.isoformat()
                    if tiger.last_seen_date
                    else None
                )
            }
            for tiger in tigers
        ]

    async def get_tiger_statistics(self) -> Dict[str, Any]:
        """Get overall tiger statistics.

        Returns:
            Dictionary with statistics
        """
        total = self.tiger_repo.count()
        reference = len(self.tiger_repo.get_reference_tigers())
        discovered = len(self.tiger_repo.get_discovered_tigers())

        by_status = {}
        for status in TigerStatus:
            count = len(self.tiger_repo.get_by_status(status))
            by_status[status.value] = count

        return {
            "total": total,
            "reference_tigers": reference,
            "discovered_tigers": discovered,
            "by_status": by_status
        }
