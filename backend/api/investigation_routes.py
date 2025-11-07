"""API routes for investigation tools and web intelligence"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Body
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

