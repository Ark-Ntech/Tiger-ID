"""Repository for Investigation data access."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from backend.database.models import (
    Investigation,
    InvestigationStep,
    InvestigationStatus,
    Priority,
    Evidence,
    InvestigationComment,
)
from backend.repositories.base import BaseRepository, PaginatedResult, FilterCriteria


class InvestigationStepRepository(BaseRepository[InvestigationStep]):
    """Repository for InvestigationStep data access."""

    def __init__(self, db: Session):
        super().__init__(db, InvestigationStep)

    def get_by_investigation_id(
        self,
        investigation_id: UUID,
        order_by_timestamp: bool = True
    ) -> List[InvestigationStep]:
        """Get all steps for an investigation.

        Args:
            investigation_id: UUID of the investigation
            order_by_timestamp: Whether to order by timestamp

        Returns:
            List of InvestigationStep objects
        """
        query = (
            self.db.query(InvestigationStep)
            .filter(InvestigationStep.investigation_id == investigation_id)
        )
        if order_by_timestamp:
            query = query.order_by(InvestigationStep.timestamp)
        return query.all()

    def get_by_step_type(
        self,
        investigation_id: UUID,
        step_type: str
    ) -> Optional[InvestigationStep]:
        """Get a specific step type for an investigation.

        Args:
            investigation_id: UUID of the investigation
            step_type: Type of step to find

        Returns:
            InvestigationStep if found, None otherwise
        """
        return (
            self.db.query(InvestigationStep)
            .filter(
                and_(
                    InvestigationStep.investigation_id == investigation_id,
                    InvestigationStep.step_type == step_type
                )
            )
            .first()
        )

    def get_latest_step(
        self,
        investigation_id: UUID
    ) -> Optional[InvestigationStep]:
        """Get the latest step for an investigation.

        Args:
            investigation_id: UUID of the investigation

        Returns:
            Latest InvestigationStep or None
        """
        return (
            self.db.query(InvestigationStep)
            .filter(InvestigationStep.investigation_id == investigation_id)
            .order_by(desc(InvestigationStep.timestamp))
            .first()
        )


class EvidenceRepository(BaseRepository[Evidence]):
    """Repository for Evidence data access."""

    def __init__(self, db: Session):
        super().__init__(db, Evidence)

    def get_by_investigation_id(
        self,
        investigation_id: UUID
    ) -> List[Evidence]:
        """Get all evidence for an investigation.

        Args:
            investigation_id: UUID of the investigation

        Returns:
            List of Evidence objects
        """
        return (
            self.db.query(Evidence)
            .filter(Evidence.investigation_id == investigation_id)
            .all()
        )

    def get_verified_evidence(
        self,
        investigation_id: UUID
    ) -> List[Evidence]:
        """Get only verified evidence for an investigation.

        Args:
            investigation_id: UUID of the investigation

        Returns:
            List of verified Evidence objects
        """
        return (
            self.db.query(Evidence)
            .filter(
                and_(
                    Evidence.investigation_id == investigation_id,
                    Evidence.verified == True
                )
            )
            .all()
        )


class InvestigationRepository(BaseRepository[Investigation]):
    """Repository for Investigation data access."""

    def __init__(self, db: Session):
        super().__init__(db, Investigation)
        self.step_repo = InvestigationStepRepository(db)
        self.evidence_repo = EvidenceRepository(db)

    def get_by_id(self, investigation_id: UUID) -> Optional[Investigation]:
        """Get investigation by ID.

        Args:
            investigation_id: UUID of the investigation

        Returns:
            Investigation if found, None otherwise
        """
        return (
            self.db.query(Investigation)
            .filter(Investigation.investigation_id == investigation_id)
            .first()
        )

    def get_by_creator(self, user_id: UUID) -> List[Investigation]:
        """Get all investigations created by a user.

        Args:
            user_id: UUID of the user

        Returns:
            List of Investigation objects
        """
        return (
            self.db.query(Investigation)
            .filter(Investigation.created_by == user_id)
            .order_by(desc(Investigation.created_at))
            .all()
        )

    def get_by_status(self, status: InvestigationStatus) -> List[Investigation]:
        """Get all investigations with a specific status.

        Args:
            status: InvestigationStatus enum value

        Returns:
            List of Investigation objects
        """
        return (
            self.db.query(Investigation)
            .filter(Investigation.status == status)
            .order_by(desc(Investigation.created_at))
            .all()
        )

    def get_active_investigations(self) -> List[Investigation]:
        """Get all active (non-archived, non-completed) investigations.

        Returns:
            List of active Investigation objects
        """
        return (
            self.db.query(Investigation)
            .filter(
                Investigation.status.in_([
                    InvestigationStatus.draft,
                    InvestigationStatus.active,
                    InvestigationStatus.pending_verification
                ])
            )
            .order_by(desc(Investigation.updated_at))
            .all()
        )

    def get_by_priority(self, priority: Priority) -> List[Investigation]:
        """Get all investigations with a specific priority.

        Args:
            priority: Priority enum value

        Returns:
            List of Investigation objects
        """
        return (
            self.db.query(Investigation)
            .filter(Investigation.priority == priority)
            .order_by(desc(Investigation.created_at))
            .all()
        )

    def get_high_priority(self) -> List[Investigation]:
        """Get all high and critical priority investigations.

        Returns:
            List of high-priority Investigation objects
        """
        return (
            self.db.query(Investigation)
            .filter(
                Investigation.priority.in_([Priority.high, Priority.critical])
            )
            .order_by(desc(Investigation.updated_at))
            .all()
        )

    def get_by_tag(self, tag: str) -> List[Investigation]:
        """Get investigations containing a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of Investigation objects
        """
        # JSON array contains - depends on database backend
        return (
            self.db.query(Investigation)
            .filter(Investigation.tags.contains([tag]))
            .all()
        )

    def get_by_tiger(self, tiger_id: UUID) -> List[Investigation]:
        """Get investigations related to a specific tiger.

        Args:
            tiger_id: UUID of the tiger

        Returns:
            List of Investigation objects
        """
        tiger_id_str = str(tiger_id)
        return (
            self.db.query(Investigation)
            .filter(Investigation.related_tigers.contains([tiger_id_str]))
            .all()
        )

    def get_by_facility(self, facility_id: UUID) -> List[Investigation]:
        """Get investigations related to a specific facility.

        Args:
            facility_id: UUID of the facility

        Returns:
            List of Investigation objects
        """
        facility_id_str = str(facility_id)
        return (
            self.db.query(Investigation)
            .filter(Investigation.related_facilities.contains([facility_id_str]))
            .all()
        )

    def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResult[Investigation]:
        """Search investigations by title or description.

        Args:
            query: Search query string
            page: Page number
            page_size: Results per page

        Returns:
            PaginatedResult with matching investigations
        """
        base_query = self.db.query(Investigation).filter(
            or_(
                Investigation.title.ilike(f"%{query}%"),
                Investigation.description.ilike(f"%{query}%")
            )
        )

        total = base_query.count()
        offset = (page - 1) * page_size
        items = base_query.order_by(desc(Investigation.created_at)).limit(page_size).offset(offset).all()

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
        status: Optional[InvestigationStatus] = None,
        priority: Optional[Priority] = None,
        created_by: Optional[UUID] = None
    ) -> PaginatedResult[Investigation]:
        """Get paginated investigations with common filters.

        Args:
            page: Page number
            page_size: Results per page
            status: Optional status filter
            priority: Optional priority filter
            created_by: Optional creator filter

        Returns:
            PaginatedResult with filtered investigations
        """
        filters = []
        if status:
            filters.append(FilterCriteria("status", "eq", status))
        if priority:
            filters.append(FilterCriteria("priority", "eq", priority))
        if created_by:
            filters.append(FilterCriteria("created_by", "eq", created_by))

        return self.get_paginated(
            page=page,
            page_size=page_size,
            sort_by="created_at",
            sort_order="desc",
            filters=filters if filters else None
        )

    def update_status(
        self,
        investigation_id: UUID,
        status: InvestigationStatus
    ) -> Optional[Investigation]:
        """Update investigation status.

        Args:
            investigation_id: UUID of the investigation
            status: New status

        Returns:
            Updated Investigation or None if not found
        """
        investigation = self.get_by_id(investigation_id)
        if not investigation:
            return None

        investigation.status = status

        # Set timestamps based on status
        if status == InvestigationStatus.active:
            if not investigation.started_at:
                investigation.started_at = datetime.utcnow()
        elif status == InvestigationStatus.completed:
            investigation.completed_at = datetime.utcnow()

        return self.update(investigation)

    def add_tiger(
        self,
        investigation_id: UUID,
        tiger_id: UUID
    ) -> Optional[Investigation]:
        """Add a tiger to investigation's related tigers.

        Args:
            investigation_id: UUID of the investigation
            tiger_id: UUID of the tiger

        Returns:
            Updated Investigation or None if not found
        """
        investigation = self.get_by_id(investigation_id)
        if not investigation:
            return None

        related = investigation.related_tigers or []
        tiger_id_str = str(tiger_id)
        if tiger_id_str not in related:
            related.append(tiger_id_str)
            investigation.related_tigers = related
            return self.update(investigation)

        return investigation

    def add_facility(
        self,
        investigation_id: UUID,
        facility_id: UUID
    ) -> Optional[Investigation]:
        """Add a facility to investigation's related facilities.

        Args:
            investigation_id: UUID of the investigation
            facility_id: UUID of the facility

        Returns:
            Updated Investigation or None if not found
        """
        investigation = self.get_by_id(investigation_id)
        if not investigation:
            return None

        related = investigation.related_facilities or []
        facility_id_str = str(facility_id)
        if facility_id_str not in related:
            related.append(facility_id_str)
            investigation.related_facilities = related
            return self.update(investigation)

        return investigation

    # Delegate to step repository

    def get_steps(self, investigation_id: UUID) -> List[InvestigationStep]:
        """Get all steps for an investigation.

        Args:
            investigation_id: UUID of the investigation

        Returns:
            List of InvestigationStep objects
        """
        return self.step_repo.get_by_investigation_id(investigation_id)

    def add_step(self, step: InvestigationStep) -> InvestigationStep:
        """Add a step to an investigation.

        Args:
            step: InvestigationStep to add

        Returns:
            Created InvestigationStep
        """
        return self.step_repo.create(step)

    # Delegate to evidence repository

    def get_evidence(self, investigation_id: UUID) -> List[Evidence]:
        """Get all evidence for an investigation.

        Args:
            investigation_id: UUID of the investigation

        Returns:
            List of Evidence objects
        """
        return self.evidence_repo.get_by_investigation_id(investigation_id)

    def add_evidence(self, evidence: Evidence) -> Evidence:
        """Add evidence to an investigation.

        Args:
            evidence: Evidence to add

        Returns:
            Created Evidence
        """
        return self.evidence_repo.create(evidence)
