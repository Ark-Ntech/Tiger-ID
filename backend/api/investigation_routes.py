"""API routes for investigation tools and web intelligence"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Body, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth.auth import get_current_user
from backend.database import get_db, User, get_db_session
from backend.services.web_search_service import get_web_search_service
from backend.services.image_search_service import get_image_search_service
from backend.services.news_monitoring_service import get_news_monitoring_service
from backend.services.lead_generation_service import get_lead_generation_service
from backend.services.relationship_analysis_service import get_relationship_analysis_service
from backend.services.evidence_compilation_service import get_evidence_compilation_service
from backend.services.crawl_scheduler_service import get_crawl_scheduler_service
from backend.utils.logging import get_logger
from backend.mcp_servers import (
    FirecrawlMCPServer,
    DatabaseMCPServer,
    TigerIDMCPServer,
    YouTubeMCPServer,
    MetaMCPServer,
)
from backend.config.settings import get_settings

# Puppeteer is optional
try:
    from backend.mcp_servers.puppeteer_server import PuppeteerMCPServer
    HAS_PUPPETEER = True
except ImportError:
    PuppeteerMCPServer = None
    HAS_PUPPETEER = False

logger = get_logger(__name__)

# Create router with prefix - specific routes like /mcp-tools must be registered before parameterized routes
# IMPORTANT: FastAPI matches routes in the order they're defined within a router
# So /mcp-tools must be defined BEFORE /{investigation_id} to match correctly
router = APIRouter(prefix="/api/v1/investigations", tags=["investigations"])


# Request models
class WebSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    provider: Optional[str] = Field(default=None, description="Search provider (firecrawl, serper, tavily)")
    location: Optional[str] = Field(default=None, description="Geographic location for localized results (e.g., 'Austin, Texas')")
    gl: Optional[str] = Field(default=None, description="Country code (e.g., 'us', 'uk')")
    hl: Optional[str] = Field(default=None, description="Language code (e.g., 'en', 'es')")


class ReverseImageSearchRequest(BaseModel):
    image_url: str = Field(..., description="URL of image to search")
    provider: Optional[str] = Field(default="google", description="Search provider (google, tineye, yandex)")


class NewsSearchRequest(BaseModel):
    query: Optional[str] = Field(default=None, description="Search query (uses default keywords if not provided)")
    days: int = Field(default=7, ge=1, le=365, description="Number of days to search back")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")


class LeadGenerationRequest(BaseModel):
    location: Optional[str] = Field(default=None, description="Geographic location filter")
    include_listings: bool = Field(default=True, description="Include marketplace listings")
    include_social_media: bool = Field(default=True, description="Include social media posts")


class RelationshipAnalysisRequest(BaseModel):
    facility_id: UUID = Field(..., description="Facility ID to analyze")


# MCP tools route moved to separate router (mcp_tools_routes.py) to avoid route conflicts
# Import the function for use in modal_routes.py
from backend.api.mcp_tools_routes import list_mcp_tools


@router.post("/web-search", response_model=Dict[str, Any])
async def web_search(
    request: WebSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Perform web search for investigation
    
    Args:
        request: Search request parameters
        current_user: Current authenticated user
        
    Returns:
        Web search results
    """
    try:
        search_service = get_web_search_service()
        
        # Use the search service which has proper fallback logic
        # TODO: Enhance search() method to accept location, gl, hl parameters for Serper
        results = await search_service.search(
            query=request.query,
            limit=request.limit or 10,
            provider=request.provider
        )
        
        return {
            "results": results.get("results", []),
            "count": results.get("count", 0),
            "query": request.query,
            "provider": results.get("provider", request.provider or "firecrawl"),
            # Include enhanced Serper results
            "answer_box": results.get("answer_box"),
            "knowledge_graph": results.get("knowledge_graph"),
            "people_also_ask": results.get("people_also_ask", []),
            "related_questions": results.get("related_questions", []),
            "total_results": results.get("total_results")
        }
    except Exception as e:
        logger.error(f"Web search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Web search failed: {str(e)}")


@router.post("/reverse-image-search", response_model=Dict[str, Any])
async def reverse_image_search(
    request: ReverseImageSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Perform reverse image search
    
    Args:
        request: Image search request parameters
        current_user: Current authenticated user
        
    Returns:
        Reverse image search results
    """
    try:
        image_search = get_image_search_service()
        results = await image_search.reverse_search(
            image_url=request.image_url,
            provider=request.provider
        )
        
        return {
            "results": results.get("results", []),
            "count": results.get("count", 0),
            "provider": results.get("provider", request.provider),
            "image_url": request.image_url
        }
    except Exception as e:
        logger.error(f"Reverse image search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Reverse image search failed: {str(e)}")


@router.post("/news-search", response_model=Dict[str, Any])
async def news_search(
    request: NewsSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search for news articles
    
    Args:
        request: News search request parameters
        current_user: Current authenticated user
        
    Returns:
        News search results
    """
    try:
        news_service = get_news_monitoring_service()
        results = await news_service.search_news(
            query=request.query,
            days=request.days,
            limit=request.limit
        )
        
        return {
            "articles": results.get("articles", []),
            "count": results.get("count", 0),
            "query": request.query,
            "days": request.days
        }
    except Exception as e:
        logger.error(f"News search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"News search failed: {str(e)}")


@router.post("/generate-leads", response_model=Dict[str, Any])
async def generate_leads(
    request: LeadGenerationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate investigation leads
    
    Args:
        request: Lead generation request parameters
        current_user: Current authenticated user
        
    Returns:
        Generated leads
    """
    try:
        lead_service = get_lead_generation_service()
        leads = await lead_service.generate_leads(
            location=request.location,
            include_listings=request.include_listings,
            include_social_media=request.include_social_media
        )
        
        return {
            "leads": leads,
            "summary": leads.get("summary", {}),
            "total_leads": leads.get("total_leads", 0)
        }
    except Exception as e:
        logger.error(f"Lead generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lead generation failed: {str(e)}")


@router.post("/relationship-analysis", response_model=Dict[str, Any])
async def relationship_analysis(
    request: RelationshipAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze relationships for a facility
    
    Args:
        request: Relationship analysis request parameters
        current_user: Current authenticated user
        
    Returns:
        Relationship analysis results
    """
    try:
        session = next(get_db_session())
        try:
            rel_service = get_relationship_analysis_service(session)
            results = rel_service.analyze_facility_relationships(request.facility_id)
            
            return {
                "relationships": results,
                "facility_id": str(request.facility_id)
            }
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Relationship analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Relationship analysis failed: {str(e)}")


@router.post("/compile-evidence", response_model=Dict[str, Any])
async def compile_evidence(
    investigation_id: UUID = Body(..., description="Investigation ID"),
    source_urls: List[str] = Body(..., description="List of source URLs to compile evidence from"),
    current_user: User = Depends(get_current_user)
):
    """
    Compile evidence from web sources
    
    Args:
        investigation_id: Investigation ID to link evidence to
        source_urls: List of source URLs
        current_user: Current authenticated user
        
    Returns:
        Evidence compilation results
    """
    try:
        session = next(get_db_session())
        try:
            evidence_service = get_evidence_compilation_service(session)
            
            sources = [{"url": url, "type": "web_search"} for url in source_urls]
            results = await evidence_service.compile_multiple_evidence(
                investigation_id=investigation_id,
                sources=sources
            )
            
            return {
                "compilation": results,
                "investigation_id": str(investigation_id)
            }
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Evidence compilation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evidence compilation failed: {str(e)}")


@router.get("/evidence-groups/{investigation_id}", response_model=Dict[str, Any])
async def get_evidence_groups(
    investigation_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get grouped evidence for an investigation
    
    Args:
        investigation_id: Investigation ID
        current_user: Current authenticated user
        
    Returns:
        Grouped evidence
    """
    try:
        with get_db_session() as session:
            evidence_service = get_evidence_compilation_service(session)
            groups = evidence_service.group_related_evidence(investigation_id)
            
            return {
                "groups": groups,
                "investigation_id": str(investigation_id)
            }
    except Exception as e:
        logger.error(f"Evidence grouping failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evidence grouping failed: {str(e)}")


@router.post("/schedule-crawl", response_model=Dict[str, Any])
async def schedule_crawl(
    facility_id: UUID = Body(..., description="Facility ID to crawl"),
    priority: Optional[str] = Body(default=None, description="Crawl priority (high, medium, low)"),
    current_user: User = Depends(get_current_user)
):
    """
    Schedule a crawl for a facility
    
    Args:
        facility_id: Facility ID to crawl
        priority: Crawl priority
        current_user: Current authenticated user
        
    Returns:
        Crawl scheduling result
    """
    try:
        session = next(get_db_session())
        try:
            scheduler_service = get_crawl_scheduler_service(session)
            result = scheduler_service.schedule_crawl(
                facility_id=facility_id,
                priority=priority
            )
            
            if "error" in result:
                raise HTTPException(status_code=400, detail=result["error"])
            
            return {
                "scheduling": result,
                "facility_id": str(facility_id)
            }
        finally:
            session.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Crawl scheduling failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Crawl scheduling failed: {str(e)}")


@router.get("/crawl-statistics", response_model=Dict[str, Any])
async def get_crawl_statistics(
    facility_id: Optional[UUID] = Query(default=None, description="Optional facility ID"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """
    Get crawl statistics
    
    Args:
        facility_id: Optional facility ID
        days: Number of days to analyze
        current_user: Current authenticated user
        
    Returns:
        Crawl statistics
    """
    try:
        with get_db_session() as session:
            scheduler_service = get_crawl_scheduler_service(session)
            stats = scheduler_service.get_crawl_statistics(
                facility_id=facility_id,
                days=days
            )
            
            return {
                "statistics": stats,
                "facility_id": str(facility_id) if facility_id else None
            }
    except Exception as e:
        logger.error(f"Crawl statistics failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Crawl statistics failed: {str(e)}")


# Tool callback endpoint for OmniVinci to execute tools agentically
@router.post("/{investigation_id}/tool-callback")
async def tool_callback(
    investigation_id: UUID,
    tool_request: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tool callback endpoint for OmniVinci to execute tools agentically.
    
    This endpoint is called by OmniVinci when it wants to use a tool.
    """
    from backend.agents import OrchestratorAgent
    from backend.utils.logging import get_logger
    
    logger = get_logger(__name__)
    
    try:
        tool_name = tool_request.get("tool")
        tool_arguments = tool_request.get("arguments", {})
        server_name = tool_request.get("server", "database")
        
        logger.info(f"Tool callback received: tool={tool_name}, server={server_name}, investigation_id={investigation_id}")
        
        # Use orchestrator to execute the tool
        session = next(get_db_session())
        try:
            orchestrator = OrchestratorAgent(db=session)
            result = await orchestrator.use_mcp_tool(
                server_name=server_name,
                tool_name=tool_name,
                arguments=tool_arguments
            )
        finally:
            session.close()
        
        logger.info(f"Tool executed successfully: {tool_name}")
        
        return {
            "success": True,
            "tool": tool_name,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Tool callback failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
@router.post("/bulk/pause")
async def bulk_pause_investigations(
    investigation_ids: List[UUID] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pause multiple investigations"""
    from backend.services.investigation_service import InvestigationService
    
    service = InvestigationService(db)
    results = []
    
    for inv_id in investigation_ids:
        try:
            investigation = service.pause_investigation(inv_id)
            if investigation:
                results.append({"id": str(inv_id), "success": True})
            else:
                results.append({"id": str(inv_id), "success": False, "error": "Not found"})
        except Exception as e:
            results.append({"id": str(inv_id), "success": False, "error": str(e)})
    
    return {
        "success": True,
        "data": {
            "results": results,
            "total": len(investigation_ids),
            "succeeded": sum(1 for r in results if r["success"])
        }
    }


@router.post("/bulk/archive")
async def bulk_archive_investigations(
    investigation_ids: List[UUID] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive multiple investigations"""
    from backend.services.investigation_service import InvestigationService
    
    service = InvestigationService(db)
    results = []
    
    for inv_id in investigation_ids:
        try:
            investigation = service.update_investigation(inv_id, status="archived")
            if investigation:
                results.append({"id": str(inv_id), "success": True})
            else:
                results.append({"id": str(inv_id), "success": False, "error": "Not found"})
        except Exception as e:
            results.append({"id": str(inv_id), "success": False, "error": str(e)})
    
    return {
        "success": True,
        "data": {
            "results": results,
            "total": len(investigation_ids),
            "succeeded": sum(1 for r in results if r["success"])
        }
    }


@router.post("/{investigation_id}/resume")
async def resume_investigation(
    investigation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resume a paused investigation"""
    from backend.services.investigation_service import InvestigationService
    
    try:
        service = InvestigationService(db)
        investigation = service.resume_investigation(investigation_id)
        
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        logger.info(f"Investigation {investigation_id} resumed by user {current_user.user_id}")
        
        # TODO: Re-launch workflow from last checkpoint
        # For now, just update status to in_progress
        
        return {
            "success": True,
            "data": {
                "id": str(investigation.investigation_id),
                "status": investigation.status.value if hasattr(investigation.status, 'value') else str(investigation.status),
                "message": "Investigation resumed successfully"
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error resuming investigation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{investigation_id}/pause")
async def pause_investigation(
    investigation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pause an active investigation"""
    from backend.services.investigation_service import InvestigationService
    
    try:
        service = InvestigationService(db)
        investigation = service.pause_investigation(investigation_id)
        
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        logger.info(f"Investigation {investigation_id} paused by user {current_user.user_id}")
        
        return {
            "success": True,
            "data": {
                "id": str(investigation.investigation_id),
                "status": investigation.status.value if hasattr(investigation.status, 'value') else str(investigation.status),
                "message": "Investigation paused successfully"
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error pausing investigation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{investigation_id}/evidence")
async def get_investigation_evidence(
    investigation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all evidence for an investigation"""
    from backend.services.investigation_service import InvestigationService
    
    service = InvestigationService(db)
    evidence_items = service.get_investigation_evidence(investigation_id)
    
    # Format evidence for frontend
    evidence_list = []
    for item in evidence_items:
        evidence_list.append({
            "id": str(item.evidence_id),
            "investigation_id": str(item.investigation_id),
            "type": item.source_type or 'document',
            "title": (item.extracted_text[:100] + '...') if item.extracted_text and len(item.extracted_text) > 100 else (item.extracted_text or 'Untitled Evidence'),
            "description": item.extracted_text,
            "source": item.source_url,
            "file_url": item.source_url,
            "collected_at": item.created_at.isoformat() if item.created_at else None,
            "created_by": str(item.investigation_id),  # TODO: Add created_by field
            "verified": False,  # TODO: Add verification field to model
            "tags": [],
            "metadata": item.content or {}
        })
    
    return {
        "success": True,
        "data": evidence_list
    }


@router.post("/{investigation_id}/evidence/upload")
async def upload_evidence(
    investigation_id: UUID,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload evidence file with MarkitDown processing"""
    from backend.services.investigation_service import InvestigationService
    import tempfile
    import os
    
    try:
        # Import markitdown
        from markitdown import MarkItDown
    except ImportError:
        logger.warning("markitdown not installed, saving file without processing")
        md = None
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Process with MarkitDown if available
        extracted_text = description or ''
        if md:
            try:
                result = md.convert(tmp_path)
                extracted_text = result.text_content if hasattr(result, 'text_content') else str(result)
            except Exception as e:
                logger.warning(f"MarkitDown processing failed: {e}")
                extracted_text = description or 'Document uploaded (processing failed)'
        
        # Save to database
        service = InvestigationService(db)
        
        # Check if file is an image and try to identify tigers automatically
        identified_tigers = []
        if file.content_type and file.content_type.startswith('image/'):
            try:
                from backend.services.tiger_service import TigerService
                tiger_service = TigerService(db)
                
                # Reset file pointer for identification
                await file.seek(0)
                
                # Identify tiger in image
                identification_result = await tiger_service.identify_tiger_from_image(
                    image=file,
                    user_id=current_user.user_id,
                    similarity_threshold=0.7,
                    model_name=None  # Use default model
                )
                
                if identification_result.get("identified") and identification_result.get("tiger_id"):
                    tiger_id = identification_result.get("tiger_id")
                    confidence = identification_result.get("confidence", 0.0)
                    
                    # Link tiger to investigation
                    identified_tigers.append({
                        "tiger_id": str(tiger_id),
                        "tiger_name": identification_result.get("tiger_name", "Unknown"),
                        "confidence": confidence
                    })
                    
                    # Add tiger to related_tigers
                    investigation = service.get_investigation(investigation_id)
                    if investigation:
                        related_tigers = investigation.related_tigers or []
                        if str(tiger_id) not in related_tigers:
                            related_tigers.append(str(tiger_id))
                            service.update_investigation(
                                investigation_id,
                                related_tigers=related_tigers
                            )
                    
                    # Update extracted text with tiger identification info
                    tiger_info = f"Tiger identified: {identification_result.get('tiger_name', 'Unknown')} (ID: {tiger_id}, Confidence: {confidence:.2%})"
                    if extracted_text:
                        extracted_text = f"{tiger_info}\n\n{extracted_text}"
                    else:
                        extracted_text = tiger_info
                    
                    logger.info(f"Automatically identified tiger {tiger_id} in evidence image")
            except Exception as e:
                logger.warning(f"Failed to automatically identify tiger in evidence image: {e}")
        
        evidence = service.add_evidence(
            investigation_id=investigation_id,
            source_type=file.content_type.split('/')[0] if file.content_type else 'document',
            source_url=file.filename,
            content={
                "filename": file.filename,
                "size": len(content),
                "content_type": file.content_type,
                "identified_tigers": identified_tigers
            },
            extracted_text=extracted_text or title or file.filename,
            relevance_score=0.9 if identified_tigers else 0.8
        )
        
        return {
            "success": True,
            "data": {
                "evidence_id": str(evidence.evidence_id),
                "title": title or file.filename,
                "extracted_text": extracted_text[:500] if extracted_text else None,
                "identified_tigers": identified_tigers
            }
        }
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/{investigation_id}/evidence/link-tiger")
async def link_tiger_evidence(
    investigation_id: UUID,
    tiger_id: UUID = Body(...),
    image_url: Optional[str] = Body(None),
    notes: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Link a tiger image as evidence to investigation"""
    from backend.services.investigation_service import InvestigationService
    
    service = InvestigationService(db)
    
    # Add as evidence
    evidence = service.add_evidence(
        investigation_id=investigation_id,
        source_type='image',
        source_url=image_url or f'/api/v1/tigers/{tiger_id}/image',
        content={"tiger_id": str(tiger_id), "notes": notes or '', "linked_from": "tiger_identification"},
        extracted_text=f"Tiger identification evidence: {tiger_id}" + (f" - {notes}" if notes else ""),
        relevance_score=0.9
    )
    
    # Also link tiger to investigation in related_tigers
    investigation = service.get_investigation(investigation_id)
    if investigation:
        related_tigers = investigation.related_tigers or []
        if str(tiger_id) not in related_tigers:
            related_tigers.append(str(tiger_id))
            service.update_investigation(
                investigation_id,
                related_tigers=related_tigers
            )
    
    return {
        "success": True,
        "data": {
            "evidence_id": str(evidence.evidence_id),
            "tiger_id": str(tiger_id),
            "message": "Tiger linked to investigation successfully"
        }
    }


@router.get("/{investigation_id}/extended")
async def get_investigation_extended(
    investigation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get investigation with extended information (progress, evidence, activity)"""
    from backend.services.investigation_service import InvestigationService
    from backend.services.approval_service import get_approval_service
    from datetime import datetime
    
    service = InvestigationService(db)
    investigation = service.get_investigation(investigation_id)
    
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    # Get steps to determine current phase and progress
    steps = service.get_investigation_steps(investigation_id)
    
    # Get evidence count
    evidence = service.get_investigation_evidence(investigation_id)
    evidence_by_type = {}
    for item in evidence:
        evidence_type = item.source_type or 'unknown'
        evidence_by_type[evidence_type] = evidence_by_type.get(evidence_type, 0) + 1
    
    # Get last activity from steps
    last_activity = None
    if steps:
        last_step = steps[-1]
        last_activity = {
            "agent": last_step.agent_name,
            "action": last_step.step_type,
            "status": last_step.status,
            "timestamp": last_step.timestamp.isoformat() if last_step.timestamp else None
        }
    
    # Determine current phase from steps
    phase_steps = [s for s in steps if 'started' in s.step_type or 'completed' in s.step_type]
    current_phase = None
    if phase_steps:
        last_phase_step = phase_steps[-1]
        if 'research' in last_phase_step.step_type:
            current_phase = 'research'
        elif 'analysis' in last_phase_step.step_type:
            current_phase = 'analysis'
        elif 'validation' in last_phase_step.step_type:
            current_phase = 'validation'
        elif 'reporting' in last_phase_step.step_type:
            current_phase = 'reporting'
    
    # Calculate progress percentage
    phase_order = ['research', 'analysis', 'validation', 'reporting']
    completed_phases = [s.step_type for s in steps if 'completed' in s.step_type]
    progress_percentage = 0
    for i, phase in enumerate(phase_order):
        if any(phase in step for step in completed_phases):
            progress_percentage = ((i + 1) / len(phase_order)) * 100
    
    # Check for pending approvals
    approval_service = get_approval_service(db)
    pending_approvals = approval_service.get_pending_approvals(investigation_id)
    pending_approval = pending_approvals[0] if pending_approvals else None
    
    # Extract entities from summary if available
    entities_identified = []
    if investigation.summary and isinstance(investigation.summary, dict):
        entities_identified = investigation.summary.get('entities', [])
    
    # Calculate time elapsed
    time_elapsed_seconds = 0
    if investigation.started_at:
        if investigation.completed_at:
            time_elapsed_seconds = int((investigation.completed_at - investigation.started_at).total_seconds())
        elif investigation.status in ['active', 'in_progress', 'paused']:
            time_elapsed_seconds = int((datetime.utcnow() - investigation.started_at).total_seconds())
    
    # Estimate cost (simple calculation based on steps)
    cost_so_far = len(steps) * 0.15  # Rough estimate: $0.15 per step
    
    return {
        "success": True,
        "data": {
            "investigation": {
                "id": str(investigation.investigation_id),
                "title": investigation.title,
                "description": investigation.description,
                "status": investigation.status.value if hasattr(investigation.status, 'value') else str(investigation.status),
                "priority": investigation.priority.value if hasattr(investigation.priority, 'value') else str(investigation.priority),
                "created_by": str(investigation.created_by),
                "tags": investigation.tags or [],
                "created_at": investigation.created_at.isoformat() if investigation.created_at else None,
                "updated_at": investigation.updated_at.isoformat() if investigation.updated_at else None,
            },
            "current_phase": current_phase,
            "progress_percentage": int(progress_percentage),
            "evidence_count": len(evidence),
            "evidence_by_type": evidence_by_type,
            "last_activity": last_activity,
            "pending_approval": pending_approval,
            "entities_identified": entities_identified,
            "cost_so_far": round(cost_so_far, 2),
            "time_elapsed_seconds": time_elapsed_seconds,
            "steps_count": len(steps)
        }
    }


# IMPORTANT: Parameterized routes like /{investigation_id} must be defined AFTER all specific routes
# (like /mcp-tools, /web-search, etc.) to ensure specific routes match first
@router.get("/{investigation_id}")
async def get_investigation(
    investigation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get investigation by ID"""
    from backend.services.investigation_service import InvestigationService
    
    service = InvestigationService(db)
    investigation = service.get_investigation(investigation_id)
    
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    return {
        "success": True,
        "data": {
            "id": str(investigation.investigation_id),
            "title": investigation.title,
            "description": investigation.description,
            "status": investigation.status.value if hasattr(investigation.status, 'value') else str(investigation.status),
            "priority": investigation.priority.value if hasattr(investigation.priority, 'value') else str(investigation.priority),
            "created_by": str(investigation.created_by),
            "tags": investigation.tags or [],
            "created_at": investigation.created_at.isoformat() if investigation.created_at else None,
            "updated_at": investigation.updated_at.isoformat() if investigation.updated_at else None,
        }
    }

