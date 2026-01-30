"""API routes for Investigation 2.0"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from datetime import datetime
import json

from backend.database import get_db_session
from backend.database.models import User
from backend.auth.auth import get_current_user
from backend.agents.investigation2_workflow import Investigation2Workflow
from backend.services.investigation_service import InvestigationService
from backend.services.event_service import get_event_service
from backend.services.investigation2_task_runner import queue_investigation
from backend.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/launch")
async def launch_investigation2(
    image: UploadFile = File(...),
    location: Optional[str] = Form(None),
    date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Launch Investigation 2.0 workflow
    
    Args:
        image: Uploaded tiger image
        location: Location context (optional)
        date: Date context (optional)
        notes: Additional notes (optional)
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Investigation ID and status
    """
    try:
        # Validate image
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image bytes
        image_bytes = await image.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Image file is empty")
        
        if len(image_bytes) > 20 * 1024 * 1024:  # 20 MB limit
            raise HTTPException(status_code=400, detail="Image file too large (max 20 MB)")
        
        # Create investigation
        investigation_service = InvestigationService(db)
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to launch investigation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to launch investigation: {str(e)}")


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
            db_gen = get_db_session()
            db = next(db_gen)
            
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
    db: Session = Depends(get_db_session),
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
    try:
        investigation_service = InvestigationService(db)
        investigation = investigation_service.get_investigation(investigation_id)
        
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        # Check permissions (user should own the investigation or be admin)
        if investigation.created_by != current_user.user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")
        
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
        
        return JSONResponse(status_code=200, content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get investigation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get investigation: {str(e)}")


@router.websocket("/ws/{investigation_id}")
async def investigation2_websocket(
    websocket: WebSocket,
    investigation_id: str
):
    """
    WebSocket endpoint for real-time investigation progress updates
    
    Args:
        websocket: WebSocket connection
        investigation_id: Investigation ID
    """
    await websocket.accept()
    
    try:
        logger.info(f"WebSocket connected for investigation {investigation_id}")
        
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
    db: Session = Depends(get_db_session),
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
    try:
        investigation_service = InvestigationService(db)
        investigation = investigation_service.get_investigation(investigation_id)
        
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        # Check permissions
        if investigation.created_by != current_user.user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get report from summary
        report = investigation.summary if investigation.summary else {}
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not yet generated")
        
        return JSONResponse(status_code=200, content={"report": report})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@router.get("/{investigation_id}/matches")
async def get_investigation2_matches(
    investigation_id: UUID,
    db: Session = Depends(get_db_session),
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
    try:
        investigation_service = InvestigationService(db)
        investigation = investigation_service.get_investigation(investigation_id)
        
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        # Check permissions
        if investigation.created_by != current_user.user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Extract matches from summary/steps
        matches = []
        if investigation.summary and isinstance(investigation.summary, dict):
            matches = investigation.summary.get("top_matches", [])
        
        return JSONResponse(status_code=200, content={"matches": matches})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get matches: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get matches: {str(e)}")


@router.get("/{investigation_id}/enhanced")
async def get_enhanced_investigation_results(
    investigation_id: UUID,
    db: Session = Depends(get_db_session),
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
    try:
        investigation_service = InvestigationService(db)
        investigation = investigation_service.get_investigation(investigation_id)

        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")

        # Check permissions
        if investigation.created_by != current_user.user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get report data
        report = investigation.summary if investigation.summary else {}

        if not report:
            raise HTTPException(status_code=404, detail="Investigation not yet completed")

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get enhanced results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get enhanced results: {str(e)}")

