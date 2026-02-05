"""
Verification Queue API routes.

Endpoints for managing verification items including tigers and facilities
pending human review after auto-discovery or user upload.
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from backend.database import get_db
from backend.database.models import (
    User,
    VerificationQueue,
    VerificationStatus,
    Priority,
    EntityType,
    Tiger,
    Facility,
    Investigation,
)
from backend.auth.auth import get_current_user
from backend.utils.pagination import PaginatedResponse, paginate_query
from backend.utils.response_models import SuccessResponse
from backend.utils.logging import get_logger
from backend.api.error_handlers import (
    ValidationError,
    NotFoundError,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/verification", tags=["verification"])


# Pydantic models for request/response schemas
class VerificationQueueItemResponse(BaseModel):
    """Response schema for a verification queue item"""
    queue_id: str
    entity_type: str
    entity_id: str
    priority: str
    status: str
    requires_human_review: bool
    source: Optional[str] = None
    investigation_id: Optional[str] = None
    assigned_to: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    # Related entity details
    entity_name: Optional[str] = None
    entity_details: Optional[dict] = None

    class Config:
        from_attributes = True


class VerificationStatusUpdate(BaseModel):
    """Request schema for updating verification status"""
    status: str = Field(..., description="New status: approved or rejected")
    review_notes: Optional[str] = Field(None, description="Optional review notes")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "approved",
                "review_notes": "Identity confirmed via stripe pattern match"
            }
        }


class VerificationStatsResponse(BaseModel):
    """Response schema for verification statistics"""
    by_status: dict
    by_source: dict
    by_priority: dict
    by_entity_type: dict
    recent_activity: dict
    total_pending: int
    total_approved_24h: int
    total_rejected_24h: int


@router.get("/queue")
async def get_verification_queue(
    entity_type: Optional[str] = Query(None, description="Filter by entity type: tiger, facility"),
    source: Optional[str] = Query(None, description="Filter by source: auto_discovery, user_upload"),
    priority: Optional[str] = Query(None, description="Filter by priority: high, medium, low"),
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected, in_review"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List pending verification items with filtering and pagination.

    Returns a paginated list of verification queue items with optional filtering
    by entity type, source, priority, and status.
    """
    # Build query with filters
    query = db.query(VerificationQueue)

    # Apply filters
    if entity_type:
        # Validate entity_type
        valid_entity_types = [e.value for e in EntityType]
        if entity_type not in valid_entity_types:
            raise ValidationError(f"Invalid entity_type. Must be one of: {', '.join(valid_entity_types)}")
        query = query.filter(VerificationQueue.entity_type == entity_type)

    if source:
        valid_sources = ["auto_discovery", "user_upload"]
        if source not in valid_sources:
            raise ValidationError(f"Invalid source. Must be one of: {', '.join(valid_sources)}")
        query = query.filter(VerificationQueue.source == source)

    if priority:
        valid_priorities = [p.value for p in Priority]
        if priority not in valid_priorities:
            raise ValidationError(f"Invalid priority. Must be one of: {', '.join(valid_priorities)}")
        query = query.filter(VerificationQueue.priority == priority)

    if status:
        valid_statuses = [s.value for s in VerificationStatus]
        if status not in valid_statuses:
            raise ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        query = query.filter(VerificationQueue.status == status)

    # Get total count before pagination
    total = query.count()

    # Order by priority (critical > high > medium > low) and created_at desc
    priority_order = {
        Priority.critical.value: 0,
        Priority.high.value: 1,
        Priority.medium.value: 2,
        Priority.low.value: 3
    }
    query = query.order_by(
        # SQLite doesn't support CASE in ORDER BY easily, so order by created_at desc
        VerificationQueue.created_at.desc()
    )

    # Apply pagination
    items = query.offset(offset).limit(limit).all()

    # Enrich items with entity details
    enriched_items = []
    for item in items:
        item_dict = {
            "queue_id": str(item.queue_id),
            "entity_type": item.entity_type,
            "entity_id": str(item.entity_id),
            "priority": item.priority,
            "status": item.status,
            "requires_human_review": item.requires_human_review,
            "source": item.source,
            "investigation_id": str(item.investigation_id) if item.investigation_id else None,
            "assigned_to": str(item.assigned_to) if item.assigned_to else None,
            "reviewed_by": str(item.reviewed_by) if item.reviewed_by else None,
            "review_notes": item.review_notes,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
            "entity_name": None,
            "entity_details": None
        }

        # Get related entity details
        try:
            if item.entity_type == EntityType.tiger.value:
                tiger = db.query(Tiger).filter(Tiger.tiger_id == item.entity_id).first()
                if tiger:
                    item_dict["entity_name"] = tiger.name or f"Tiger {str(tiger.tiger_id)[:8]}"
                    item_dict["entity_details"] = {
                        "name": tiger.name,
                        "alias": tiger.alias,
                        "status": tiger.status,
                        "last_seen_location": tiger.last_seen_location,
                        "last_seen_date": tiger.last_seen_date.isoformat() if tiger.last_seen_date else None
                    }
            elif item.entity_type == EntityType.facility.value:
                facility = db.query(Facility).filter(Facility.facility_id == item.entity_id).first()
                if facility:
                    item_dict["entity_name"] = facility.exhibitor_name or f"Facility {str(facility.facility_id)[:8]}"
                    item_dict["entity_details"] = {
                        "exhibitor_name": facility.exhibitor_name,
                        "usda_license": facility.usda_license,
                        "city": facility.city,
                        "state": facility.state,
                        "tiger_count": facility.tiger_count,
                        "website": facility.website
                    }
        except Exception as e:
            logger.warning(f"Failed to get entity details for {item.entity_type}/{item.entity_id}: {e}")

        enriched_items.append(item_dict)

    # Build paginated response
    paginated = PaginatedResponse.create(
        data=enriched_items,
        total=total,
        page=(offset // limit) + 1 if limit > 0 else 1,
        page_size=limit
    )

    return SuccessResponse(
        message="Verification queue retrieved successfully",
        data=paginated.model_dump()
    )


@router.get("/queue/{queue_id}")
async def get_verification_item(
    queue_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single verification queue item with full details.

    Includes related entity details (tiger name, facility name, etc.)
    and investigation context if available.
    """
    # Get the verification item
    item = db.query(VerificationQueue).filter(
        VerificationQueue.queue_id == str(queue_id)
    ).first()

    if not item:
        raise NotFoundError("Verification item", str(queue_id))

    # Build response with entity details
    response = {
        "queue_id": str(item.queue_id),
        "entity_type": item.entity_type,
        "entity_id": str(item.entity_id),
        "priority": item.priority,
        "status": item.status,
        "requires_human_review": item.requires_human_review,
        "source": item.source,
        "investigation_id": str(item.investigation_id) if item.investigation_id else None,
        "assigned_to": str(item.assigned_to) if item.assigned_to else None,
        "reviewed_by": str(item.reviewed_by) if item.reviewed_by else None,
        "review_notes": item.review_notes,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
        "entity": None,
        "investigation": None
    }

    # Get related entity
    if item.entity_type == EntityType.tiger.value:
        tiger = db.query(Tiger).filter(Tiger.tiger_id == item.entity_id).first()
        if tiger:
            # Get facility info if available
            facility_info = None
            if tiger.origin_facility_id:
                facility = db.query(Facility).filter(
                    Facility.facility_id == tiger.origin_facility_id
                ).first()
                if facility:
                    facility_info = {
                        "facility_id": str(facility.facility_id),
                        "exhibitor_name": facility.exhibitor_name,
                        "city": facility.city,
                        "state": facility.state
                    }

            response["entity"] = {
                "type": "tiger",
                "tiger_id": str(tiger.tiger_id),
                "name": tiger.name,
                "alias": tiger.alias,
                "status": tiger.status,
                "last_seen_location": tiger.last_seen_location,
                "last_seen_date": tiger.last_seen_date.isoformat() if tiger.last_seen_date else None,
                "notes": tiger.notes,
                "tags": tiger.tags,
                "is_reference": tiger.is_reference,
                "discovery_confidence": tiger.discovery_confidence,
                "created_at": tiger.created_at.isoformat() if tiger.created_at else None,
                "facility": facility_info
            }

    elif item.entity_type == EntityType.facility.value:
        facility = db.query(Facility).filter(Facility.facility_id == item.entity_id).first()
        if facility:
            response["entity"] = {
                "type": "facility",
                "facility_id": str(facility.facility_id),
                "exhibitor_name": facility.exhibitor_name,
                "usda_license": facility.usda_license,
                "city": facility.city,
                "state": facility.state,
                "address": facility.address,
                "tiger_count": facility.tiger_count,
                "tiger_capacity": facility.tiger_capacity,
                "website": facility.website,
                "accreditation_status": facility.accreditation_status,
                "last_inspection_date": facility.last_inspection_date.isoformat() if facility.last_inspection_date else None,
                "last_crawled_at": facility.last_crawled_at.isoformat() if facility.last_crawled_at else None,
                "is_reference_facility": facility.is_reference_facility,
                "data_source": facility.data_source,
                "created_at": facility.created_at.isoformat() if facility.created_at else None
            }

    # Get related investigation if available
    if item.investigation_id:
        investigation = db.query(Investigation).filter(
            Investigation.investigation_id == item.investigation_id
        ).first()
        if investigation:
            response["investigation"] = {
                "investigation_id": str(investigation.investigation_id),
                "title": investigation.title,
                "description": investigation.description,
                "status": investigation.status,
                "priority": investigation.priority,
                "created_at": investigation.created_at.isoformat() if investigation.created_at else None,
                "completed_at": investigation.completed_at.isoformat() if investigation.completed_at else None
            }

    return SuccessResponse(
        message="Verification item retrieved successfully",
        data=response
    )


@router.patch("/queue/{queue_id}")
async def update_verification_status(
    queue_id: UUID,
    update: VerificationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update the verification status of a queue item.

    Sets the status to approved or rejected, records the reviewer,
    review timestamp, and optional review notes.
    """
    # Validate status
    valid_statuses = ["approved", "rejected", "in_review"]
    if update.status not in valid_statuses:
        raise ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    # Get the verification item
    item = db.query(VerificationQueue).filter(
        VerificationQueue.queue_id == str(queue_id)
    ).first()

    if not item:
        raise NotFoundError("Verification item", str(queue_id))

    # Update fields
    item.status = update.status
    item.review_notes = update.review_notes
    item.reviewed_by = str(current_user.user_id)
    item.reviewed_at = datetime.utcnow()

    # If approved, update the related entity
    if update.status == "approved":
        try:
            if item.entity_type == EntityType.tiger.value:
                tiger = db.query(Tiger).filter(Tiger.tiger_id == item.entity_id).first()
                if tiger:
                    # Mark as verified (no longer just reference data)
                    tiger.is_reference = False
                    logger.info(f"Tiger {tiger.tiger_id} verified and marked as non-reference")

            elif item.entity_type == EntityType.facility.value:
                facility = db.query(Facility).filter(Facility.facility_id == item.entity_id).first()
                if facility:
                    facility.is_reference_facility = False
                    logger.info(f"Facility {facility.facility_id} verified and marked as non-reference")
        except Exception as e:
            logger.warning(f"Failed to update entity after approval: {e}")

    db.commit()

    logger.info(
        f"Verification item {queue_id} updated to {update.status} by user {current_user.user_id}"
    )

    return SuccessResponse(
        message=f"Verification status updated to {update.status}",
        data={
            "queue_id": str(item.queue_id),
            "status": item.status,
            "reviewed_by": str(item.reviewed_by),
            "reviewed_at": item.reviewed_at.isoformat(),
            "review_notes": item.review_notes
        }
    )


@router.get("/stats")
async def get_verification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard statistics for verification queue.

    Returns counts by status, source, priority, and entity type,
    as well as recent activity (approvals/rejections in last 24 hours).
    """
    # Calculate time threshold for recent activity
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)

    # Count by status
    status_counts = {}
    for status in VerificationStatus:
        count = db.query(VerificationQueue).filter(
            VerificationQueue.status == status.value
        ).count()
        status_counts[status.value] = count

    # Count by source
    source_counts = {}
    for source in ["auto_discovery", "user_upload"]:
        count = db.query(VerificationQueue).filter(
            VerificationQueue.source == source
        ).count()
        source_counts[source] = count
    # Add count for items without source
    null_source_count = db.query(VerificationQueue).filter(
        VerificationQueue.source.is_(None)
    ).count()
    if null_source_count > 0:
        source_counts["unknown"] = null_source_count

    # Count by priority
    priority_counts = {}
    for priority_item in Priority:
        count = db.query(VerificationQueue).filter(
            VerificationQueue.priority == priority_item.value
        ).count()
        priority_counts[priority_item.value] = count

    # Count by entity type
    entity_type_counts = {}
    for entity_type_item in EntityType:
        count = db.query(VerificationQueue).filter(
            VerificationQueue.entity_type == entity_type_item.value
        ).count()
        if count > 0:
            entity_type_counts[entity_type_item.value] = count

    # Recent activity (last 24 hours)
    approved_24h = db.query(VerificationQueue).filter(
        and_(
            VerificationQueue.status == VerificationStatus.approved.value,
            VerificationQueue.reviewed_at >= last_24h
        )
    ).count()

    rejected_24h = db.query(VerificationQueue).filter(
        and_(
            VerificationQueue.status == VerificationStatus.rejected.value,
            VerificationQueue.reviewed_at >= last_24h
        )
    ).count()

    # Total pending
    total_pending = db.query(VerificationQueue).filter(
        VerificationQueue.status == VerificationStatus.pending.value
    ).count()

    # Recent activity breakdown by hour (last 24 hours)
    hourly_activity = []
    for i in range(24):
        hour_start = now - timedelta(hours=i+1)
        hour_end = now - timedelta(hours=i)

        approved = db.query(VerificationQueue).filter(
            and_(
                VerificationQueue.status == VerificationStatus.approved.value,
                VerificationQueue.reviewed_at >= hour_start,
                VerificationQueue.reviewed_at < hour_end
            )
        ).count()

        rejected = db.query(VerificationQueue).filter(
            and_(
                VerificationQueue.status == VerificationStatus.rejected.value,
                VerificationQueue.reviewed_at >= hour_start,
                VerificationQueue.reviewed_at < hour_end
            )
        ).count()

        if approved > 0 or rejected > 0:
            hourly_activity.append({
                "hour": hour_end.isoformat(),
                "approved": approved,
                "rejected": rejected
            })

    stats = {
        "by_status": status_counts,
        "by_source": source_counts,
        "by_priority": priority_counts,
        "by_entity_type": entity_type_counts,
        "recent_activity": {
            "approved_24h": approved_24h,
            "rejected_24h": rejected_24h,
            "hourly_breakdown": hourly_activity
        },
        "total_pending": total_pending,
        "total_approved_24h": approved_24h,
        "total_rejected_24h": rejected_24h,
        "total_items": sum(status_counts.values()),
        "timestamp": now.isoformat()
    }

    return SuccessResponse(
        message="Verification statistics retrieved successfully",
        data=stats
    )


# Legacy endpoint for backward compatibility
@router.get("/tasks")
async def get_verification_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Legacy endpoint for verification tasks.

    Redirects to the new /queue endpoint for backward compatibility.
    """
    # Convert page/page_size to offset/limit
    offset = (page - 1) * page_size

    return await get_verification_queue(
        entity_type=None,
        source=None,
        priority=None,
        status=status,
        limit=page_size,
        offset=offset,
        db=db,
        current_user=current_user
    )
