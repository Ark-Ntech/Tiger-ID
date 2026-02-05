"""API routes for Investigation 2.0"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from datetime import datetime
import json

from backend.database import get_db_session
from backend.database.models import User
from backend.auth.auth import get_current_user, get_current_user_ws
from backend.agents.investigation2_workflow import Investigation2Workflow
from backend.services.factory import ServiceFactory
from backend.services.event_service import get_event_service
from backend.services.investigation2_task_runner import queue_investigation
from backend.mcp_servers import get_report_generation_server
from backend.utils.logging import get_logger
from backend.database import get_db  # FastAPI dependency (generator)
from backend.api.error_handlers import (
    ValidationError,
    NotFoundError,
    AuthorizationError,
    BadRequestError,
    ServiceUnavailableError,
)

logger = get_logger(__name__)

# Valid report audiences
VALID_AUDIENCES = {"law_enforcement", "conservation", "internal", "public"}
router = APIRouter()


@router.post("/launch")
async def launch_investigation2(
    image: UploadFile = File(...),
    location: Optional[str] = Form(None),
    date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    audience: Optional[str] = Form("internal"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Launch Investigation 2.0 workflow

    Args:
        image: Uploaded tiger image
        location: Location context (optional)
        date: Date context (optional)
        notes: Additional notes (optional)
        audience: Target report audience (law_enforcement, conservation, internal, public)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Investigation ID and status
    """
    # Validate image
    if not image.content_type.startswith('image/'):
        raise ValidationError("File must be an image")

    # Validate audience
    if audience and audience not in VALID_AUDIENCES:
        raise ValidationError(f"Invalid audience. Must be one of: {', '.join(VALID_AUDIENCES)}")

    # Read image bytes
    image_bytes = await image.read()
    if len(image_bytes) == 0:
        raise ValidationError("Image file is empty")

    if len(image_bytes) > 20 * 1024 * 1024:  # 20 MB limit
        raise ValidationError("Image file too large (max 20 MB)")

    # Create investigation
    factory = ServiceFactory(db)
    investigation_service = factory.get_investigation_service()

    investigation_title = f"Investigation 2.0 - {location or 'Unknown Location'}"
    investigation_description = f"Tiger identification investigation using advanced workflow"

    investigation_data = {
        "title": investigation_title,
        "description": investigation_description,
        "priority": "high"
    }

    investigation = investigation_service.create_investigation(
        title=investigation_data["title"],
        description=investigation_data["description"],
        priority=investigation_data["priority"],
        created_by=current_user.user_id
    )

    investigation_id = investigation.investigation_id

    logger.info(f"Created investigation {investigation_id} for user {current_user.user_id}")

    # Prepare context
    context = {
        "location": location,
        "date": date,
        "notes": notes,
        "audience": audience or "internal",
        "uploaded_by": str(current_user.user_id),
        "uploaded_at": datetime.utcnow().isoformat()
    }

    # Queue investigation for background processing using task runner
    logger.info(f"[LAUNCH] Queuing investigation {investigation_id} for background processing")
    logger.info(f"Queuing investigation {investigation_id} for background processing")

    queue_investigation(
        investigation_id=investigation_id,
        image_bytes=image_bytes,
        context=context
    )

    logger.info(f"[LAUNCH] Investigation queued successfully")
    logger.info(f"Investigation {investigation_id} queued for processing")

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "investigation_id": str(investigation_id),
            "message": "Investigation 2.0 launched successfully",
            "websocket_url": f"/api/v1/investigations2/ws/{investigation_id}"
        }
    )


def run_investigation_workflow(
    investigation_id: UUID,
    image_bytes: bytes,
    context: Dict[str, Any]
):
    """
    Run investigation workflow in background (synchronous wrapper for async workflow)
    
    Args:
        investigation_id: Investigation ID
        image_bytes: Uploaded image bytes
        context: Investigation context
    """
    import asyncio
    
    # Add explicit logging at function entry
    logger.info(f"[WORKFLOW] Starting workflow for {investigation_id}")
    logger.info(f"[WORKFLOW] Starting background workflow for investigation {investigation_id}")
    
    async def _async_workflow():
        db = None
        try:
            logger.info(f"[WORKFLOW] _async_workflow started for {investigation_id}")
            logger.info(f"Running Investigation 2.0 workflow for {investigation_id}")
            
            # Create new database session for background task
            from backend.database import get_db_session
            db = get_db_session()  # Returns Session directly
            
            workflow = Investigation2Workflow(db=db)
            
            final_state = await workflow.run(
                investigation_id=investigation_id,
                uploaded_image=image_bytes,
                context=context
            )
            
            logger.info(f"Investigation {investigation_id} completed with status: {final_state.get('status')}")
            
            # Commit and close session
            try:
                db.commit()
            except Exception:
                pass
            
            return final_state
            
        except Exception as e:
            logger.error(f"Investigation workflow failed for {investigation_id}: {e}", exc_info=True)
            if db:
                try:
                    db.rollback()
                except Exception:
                    pass
            return None
        finally:
            if db:
                try:
                    db.close()
                except Exception:
                    pass
    
    # Run in new event loop
    try:
        logger.info(f"[WORKFLOW] Creating event loop for {investigation_id}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info(f"[WORKFLOW] Running workflow in event loop...")
        result = loop.run_until_complete(_async_workflow())
        loop.close()
        logger.info(f"[WORKFLOW] Workflow completed for {investigation_id}")
        return result
    except Exception as e:
        logger.info(f"[WORKFLOW] ERROR: {e}")
        logger.error(f"Event loop error for investigation {investigation_id}: {e}", exc_info=True)
        return None


@router.get("/{investigation_id}")
async def get_investigation2(
    investigation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Investigation 2.0 results
    
    Args:
        investigation_id: Investigation ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Investigation results and report
    """
    factory = ServiceFactory(db)
    investigation_service = factory.get_investigation_service()
    investigation = investigation_service.get_investigation(investigation_id)

    if not investigation:
        raise NotFoundError("Investigation", str(investigation_id))

    # Check permissions (user should own the investigation or be admin)
    if str(investigation.created_by) != str(current_user.user_id) and not current_user.is_admin:
        raise AuthorizationError("Access denied to this investigation")

    # Get investigation steps
    steps = investigation_service.get_investigation_steps(investigation_id)

    # Format response (convert Enums to strings for JSON serialization)
    response = {
        "investigation_id": str(investigation.investigation_id),
        "title": investigation.title,
        "description": investigation.description,
        "status": str(investigation.status.value) if hasattr(investigation.status, 'value') else str(investigation.status),
        "priority": str(investigation.priority.value) if hasattr(investigation.priority, 'value') else str(investigation.priority),
        "created_at": investigation.created_at.isoformat() if investigation.created_at else None,
        "updated_at": investigation.updated_at.isoformat() if investigation.updated_at else None,
        "completed_at": investigation.completed_at.isoformat() if investigation.completed_at else None,
        "steps": [
            {
                "step_id": str(step.step_id),
                "step_type": step.step_type,
                "agent_name": step.agent_name,
                "status": str(step.status.value) if hasattr(step.status, 'value') else str(step.status),
                "result": step.result,
                "timestamp": step.timestamp.isoformat() if step.timestamp else None,
                "error_message": step.error_message,
                "duration_ms": step.duration_ms
            }
            for step in steps
        ],
        "summary": investigation.summary
    }

    # Wrap in ApiResponse format expected by frontend
    return JSONResponse(status_code=200, content={
        "data": response,
        "success": True,
        "message": "Investigation retrieved successfully"
    })


@router.websocket("/ws/{investigation_id}")
async def investigation2_websocket(
    websocket: WebSocket,
    investigation_id: str,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for real-time investigation progress updates

    Args:
        websocket: WebSocket connection
        investigation_id: Investigation ID
        token: JWT token for authentication (query parameter)
    """
    # Authenticate user via token query parameter
    db = None
    try:
        db = get_db_session()  # Returns Session directly

        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return

        user = await get_current_user_ws(token, db)
        if not user:
            await websocket.close(code=4001, reason="Invalid or expired token")
            return

        # Verify user has access to this investigation
        factory = ServiceFactory(db)
        investigation_service = factory.get_investigation_service()
        investigation = investigation_service.get_investigation(UUID(investigation_id))

        if not investigation:
            await websocket.close(code=4004, reason="Investigation not found")
            return

        if str(investigation.created_by) != str(user.user_id) and not user.is_admin:
            await websocket.close(code=4003, reason="Access denied")
            return

    except Exception as e:
        logger.error(f"WebSocket auth error: {e}")
        await websocket.close(code=4000, reason="Authentication failed")
        return
    finally:
        if db:
            db.close()

    await websocket.accept()

    try:
        logger.info(f"WebSocket connected for investigation {investigation_id} (user: {user.username})")

        # Get event service
        event_service = get_event_service()
        
        # Subscribe to investigation events
        async def event_handler(event_type: str, data: Dict[str, Any], **kwargs):
            """Handle investigation events and send to client"""
            try:
                # Only send events for this investigation
                if kwargs.get("investigation_id") == investigation_id:
                    await websocket.send_json({
                        "event": event_type,
                        "data": data,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
        
        # Subscribe to events
        event_service.subscribe("investigation_started", event_handler)
        event_service.subscribe("phase_started", event_handler)
        event_service.subscribe("phase_completed", event_handler)
        event_service.subscribe("investigation_completed", event_handler)
        
        # Send initial connection confirmation
        await websocket.send_json({
            "event": "connected",
            "data": {"investigation_id": investigation_id},
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive
        while True:
            try:
                # Wait for messages from client (ping/pong)
                message = await websocket.receive_text()
                if message == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for investigation {investigation_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
        
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}", exc_info=True)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@router.get("/{investigation_id}/report")
async def get_investigation2_report(
    investigation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Investigation 2.0 report
    
    Args:
        investigation_id: Investigation ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Investigation report
    """
    factory = ServiceFactory(db)
    investigation_service = factory.get_investigation_service()
    investigation = investigation_service.get_investigation(investigation_id)

    if not investigation:
        raise NotFoundError("Investigation", str(investigation_id))

    # Check permissions
    if str(investigation.created_by) != str(current_user.user_id) and not current_user.is_admin:
        raise AuthorizationError("Access denied to this investigation")

    # Get report from summary
    report = investigation.summary if investigation.summary else {}

    if not report:
        raise NotFoundError("Report", str(investigation_id))

    # Wrap in ApiResponse format expected by frontend
    return JSONResponse(status_code=200, content={
        "data": {"report": report},
        "success": True,
        "message": "Report retrieved successfully"
    })


@router.get("/{investigation_id}/matches")
async def get_investigation2_matches(
    investigation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Investigation 2.0 tiger matches
    
    Args:
        investigation_id: Investigation ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Tiger matches from all models
    """
    factory = ServiceFactory(db)
    investigation_service = factory.get_investigation_service()
    investigation = investigation_service.get_investigation(investigation_id)

    if not investigation:
        raise NotFoundError("Investigation", str(investigation_id))

    # Check permissions
    if str(investigation.created_by) != str(current_user.user_id) and not current_user.is_admin:
        raise AuthorizationError("Access denied to this investigation")

    # Extract matches from summary/steps
    matches = []
    if investigation.summary and isinstance(investigation.summary, dict):
        matches = investigation.summary.get("top_matches", [])

    # Wrap in ApiResponse format expected by frontend
    return JSONResponse(status_code=200, content={
        "data": {"matches": matches},
        "success": True,
        "message": "Matches retrieved successfully"
    })


@router.get("/{investigation_id}/enhanced")
async def get_enhanced_investigation_results(
    investigation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get enhanced Investigation 2.0 results with location, methodology, and detailed matches

    This endpoint provides enriched data for the frontend UI components:
    - Location analysis from multiple sources (EXIF, user context, web intelligence, database matches)
    - Methodology/reasoning chain showing investigation steps
    - Detailed match information with stripe comparisons
    - Citations from web intelligence

    Args:
        investigation_id: Investigation ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Enhanced investigation results
    """
    factory = ServiceFactory(db)
    investigation_service = factory.get_investigation_service()
    investigation = investigation_service.get_investigation(investigation_id)

    if not investigation:
        raise NotFoundError("Investigation", str(investigation_id))

    # Check permissions
    if str(investigation.created_by) != str(current_user.user_id) and not current_user.is_admin:
        raise AuthorizationError("Access denied to this investigation")

    # Get report data
    report = investigation.summary if investigation.summary else {}

    if not report:
        raise NotFoundError("Investigation results", str(investigation_id))

    # Extract enhanced data
    location_analysis = report.get("location_analysis", {
        "primary_location": None,
        "sources": [],
        "alternative_locations": [],
        "total_sources": 0
    })

    methodology = report.get("methodology", [])

    citations = []
    if "web_intelligence" in report:
        web_intel = report["web_intelligence"]
        if isinstance(web_intel, dict):
            citations = web_intel.get("citations", [])

    # Get detailed matches with facility information
    matches_with_details = []
    top_matches = report.get("top_matches", [])

    for match in top_matches:
        tiger_id = match.get("tiger_id")
        if not tiger_id:
            continue

        # Try to get facility information from database
        try:
            from backend.database.models import Tiger, Facility
            tiger = db.query(Tiger).filter(Tiger.tiger_id == UUID(tiger_id)).first()

            facility_info = None
            if tiger and tiger.origin_facility_id:
                facility = db.query(Facility).filter(
                    Facility.facility_id == tiger.origin_facility_id
                ).first()

                if facility:
                    # Parse coordinates if available
                    coords = None
                    if facility.coordinates:
                        try:
                            coords_data = json.loads(facility.coordinates) if isinstance(facility.coordinates, str) else facility.coordinates
                            coords = {
                                "lat": coords_data.get("latitude"),
                                "lon": coords_data.get("longitude")
                            }
                        except Exception:
                            pass

                    facility_info = {
                        "name": facility.exhibitor_name,
                        "location": f"{facility.city}, {facility.state}" if facility.city and facility.state else facility.state or "Unknown",
                        "coordinates": coords,
                        "address": facility.address
                    }

            matches_with_details.append({
                **match,
                "facility": facility_info,
                "confidence_breakdown": {
                    "stripe_similarity": match.get("similarity", 0),
                    "visual_features": 0.8,  # Placeholder - could be calculated from model data
                    "historical_context": 0.7  # Placeholder - could be based on last_seen_date
                }
            })
        except Exception as e:
            logger.warning(f"Failed to get facility for tiger {tiger_id}: {e}")
            matches_with_details.append({
                **match,
                "facility": None,
                "confidence_breakdown": {
                    "stripe_similarity": match.get("similarity", 0),
                    "visual_features": 0.8,
                    "historical_context": 0.7
                }
            })

    # Build enhanced response
    enhanced_results = {
        "investigation_id": str(investigation_id),
        "status": investigation.status.value if hasattr(investigation.status, 'value') else str(investigation.status),
        "location_analysis": location_analysis,
        "matches": matches_with_details,
        "citations": citations,
        "methodology": methodology,
        "report": report.get("summary", ""),
        "detection_count": report.get("detection_count", 0),
        "models_used": report.get("models_used", []),
        "confidence": report.get("confidence", "medium"),
        "created_at": investigation.created_at.isoformat() if investigation.created_at else None,
        "completed_at": investigation.completed_at.isoformat() if investigation.completed_at else None
    }

    return JSONResponse(status_code=200, content=enhanced_results)


@router.post("/{investigation_id}/regenerate-report")
async def regenerate_investigation2_report(
    investigation_id: UUID,
    audience: str = Form("internal"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Regenerate Investigation 2.0 report with a different audience.

    This endpoint allows regenerating the investigation report tailored for
    different audiences (law_enforcement, conservation, internal, public).

    Args:
        investigation_id: Investigation ID
        audience: Target audience for the new report
        db: Database session
        current_user: Current authenticated user

    Returns:
        Regenerated report content
    """
    # Validate audience
    if audience not in VALID_AUDIENCES:
        raise ValidationError(f"Invalid audience. Must be one of: {', '.join(VALID_AUDIENCES)}")

    factory = ServiceFactory(db)
    investigation_service = factory.get_investigation_service()
    investigation = investigation_service.get_investigation(investigation_id)

    if not investigation:
        raise NotFoundError("Investigation", str(investigation_id))

    # Check permissions
    if str(investigation.created_by) != str(current_user.user_id) and not current_user.is_admin:
        raise AuthorizationError("Access denied to this investigation")

    # Check if investigation is completed
    status_value = investigation.status.value if hasattr(investigation.status, 'value') else str(investigation.status)
    if status_value != "completed":
        raise BadRequestError("Cannot regenerate report for incomplete investigation")

    # Get existing report data
    existing_summary = investigation.summary if investigation.summary else {}
    if not existing_summary:
        raise NotFoundError("Report data", str(investigation_id))

    # Build investigation data for report regeneration
    investigation_data = {
        "investigation_id": str(investigation_id),
        "title": investigation.title,
        "description": investigation.description,
        "top_matches": existing_summary.get("top_matches", []),
        "methodology": existing_summary.get("methodology", []),
        "web_intelligence": existing_summary.get("web_intelligence", {}),
        "location_analysis": existing_summary.get("location_analysis", {}),
        "detection_count": existing_summary.get("detection_count", 0),
        "models_used": existing_summary.get("models_used", []),
        "verified_candidates": existing_summary.get("verified_candidates", []),
        "created_at": investigation.created_at.isoformat() if investigation.created_at else None,
        "completed_at": investigation.completed_at.isoformat() if investigation.completed_at else None,
    }

    # Get report generation server
    report_server = get_report_generation_server()

    # Generate new report with specified audience
    logger.info(f"Regenerating report for investigation {investigation_id} with audience: {audience}")

    report_result = await report_server.call_tool(
        "generate_report",
        {
            "investigation_id": str(investigation_id),
            "investigation_data": investigation_data,
            "audience": audience,
            "format": "markdown",
            "classification": "restricted" if audience == "law_enforcement" else "public",
            "include_methodology": True
        }
    )

    if not report_result.get("success"):
        raise ServiceUnavailableError(
            f"Report generation failed: {report_result.get('error', 'Unknown error')}"
        )

    # Extract report content
    new_report = {
        "report_id": report_result.get("report_id"),
        "audience": audience,
        "content": report_result.get("report", ""),
        "metadata": report_result.get("metadata", {}),
        "generated_at": datetime.utcnow().isoformat(),
        "investigation_id": str(investigation_id)
    }

    # Update investigation summary with new report for this audience
    updated_summary = existing_summary.copy()
    if "reports_by_audience" not in updated_summary:
        updated_summary["reports_by_audience"] = {}
    updated_summary["reports_by_audience"][audience] = new_report
    updated_summary["latest_report_audience"] = audience

    # Save to database
    investigation.summary = updated_summary
    db.commit()

    logger.info(f"Successfully regenerated report for investigation {investigation_id}")

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "report": new_report,
            "message": f"Report regenerated successfully for {audience} audience"
        }
    )

