"""API routes for investigation tools and web intelligence"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth.auth import get_current_user
from backend.database import get_db, User
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

router = APIRouter(prefix="/api/v1/investigations", tags=["investigations"])


# Request models
class WebSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    provider: Optional[str] = Field(default=None, description="Search provider (firecrawl, serper, tavily)")


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
        results = await search_service.search(
            query=request.query,
            limit=request.limit,
            provider=request.provider
        )
        
        return {
            "results": results.get("results", []),
            "count": results.get("count", 0),
            "query": request.query,
            "provider": results.get("provider", request.provider or "firecrawl")
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
        with get_db_session() as session:
            rel_service = get_relationship_analysis_service(session)
            results = rel_service.analyze_facility_relationships(request.facility_id)
            
            return {
                "relationships": results,
                "facility_id": str(request.facility_id)
            }
    except Exception as e:
        logger.error(f"Relationship analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Relationship analysis failed: {str(e)}")


@router.get("/network-graph", response_model=Dict[str, Any])
async def get_network_graph(
    facility_ids: Optional[List[UUID]] = Query(default=None, description="Facility IDs to include"),
    include_reference: bool = Query(default=True, description="Include reference facilities"),
    current_user: User = Depends(get_current_user)
):
    """
    Get network graph of facility relationships
    
    Args:
        facility_ids: Optional list of facility IDs
        include_reference: Include reference facilities
        current_user: Current authenticated user
        
    Returns:
        Network graph data
    """
    try:
        with get_db_session() as session:
            rel_service = get_relationship_analysis_service(session)
            graph = rel_service.build_network_graph(
                facility_ids=facility_ids,
                include_reference_facilities=include_reference
            )
            
            return {
                "network": graph,
                "node_count": graph.get("node_count", 0),
                "edge_count": graph.get("edge_count", 0)
            }
    except Exception as e:
        logger.error(f"Network graph generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Network graph generation failed: {str(e)}")


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
        with get_db_session() as session:
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
        with get_db_session() as session:
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


@router.get("/mcp-tools", response_model=Dict[str, Any])
async def list_mcp_tools(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all available MCP tools organized by server"""
    tools_by_server = {}
    
    try:
        # Database MCP Server - use the session directly
        db_server = DatabaseMCPServer(db=db)
        db_tools = await db_server.list_tools()
        tools_by_server["database"] = {
            "name": "Database",
            "description": "Query tigers, facilities, and investigations",
            "tools": db_tools
        }
    except Exception as e:
        logger.warning(f"Error loading database tools: {e}")
    
    try:
        # Firecrawl MCP Server
        firecrawl_server = FirecrawlMCPServer()
        firecrawl_tools = await firecrawl_server.list_tools()
        tools_by_server["firecrawl"] = {
            "name": "Firecrawl",
            "description": "Web search and scraping",
            "tools": firecrawl_tools
        }
    except Exception as e:
        logger.warning(f"Error loading firecrawl tools: {e}")
    
    try:
        # TigerID MCP Server
        tiger_id_server = TigerIDMCPServer()
        tiger_tools = await tiger_id_server.list_tools()
        tools_by_server["tiger_id"] = {
            "name": "Tiger Identification",
            "description": "Identify tigers from images",
            "tools": tiger_tools
        }
    except Exception as e:
        logger.warning(f"Error loading tiger ID tools: {e}")
    
    try:
        # YouTube MCP Server
        youtube_server = YouTubeMCPServer()
        youtube_tools = await youtube_server.list_tools()
        tools_by_server["youtube"] = {
            "name": "YouTube",
            "description": "Search YouTube videos and channels",
            "tools": youtube_tools
        }
    except Exception as e:
        logger.warning(f"Error loading YouTube tools: {e}")
    
    try:
        # Meta MCP Server
        meta_server = MetaMCPServer()
        meta_tools = await meta_server.list_tools()
        tools_by_server["meta"] = {
            "name": "Meta/Facebook",
            "description": "Search Facebook pages and posts",
            "tools": meta_tools
        }
    except Exception as e:
        logger.warning(f"Error loading Meta tools: {e}")
    
    try:
        # Puppeteer MCP Server (optional)
        settings = get_settings()
        if HAS_PUPPETEER and settings.puppeteer.enabled:
            puppeteer_server = PuppeteerMCPServer()
            puppeteer_tools = await puppeteer_server.list_tools()
            tools_by_server["puppeteer"] = {
                "name": "Puppeteer",
                "description": "Browser automation and scraping",
                "tools": puppeteer_tools
            }
    except Exception as e:
        logger.warning(f"Error loading Puppeteer tools: {e}")
    
    # Also include high-level investigation tools
    investigation_tools = [
        {
            "name": "web_search",
            "description": "Search the web for information",
            "server": "firecrawl"
        },
        {
            "name": "reverse_image_search",
            "description": "Search for images using reverse image search",
            "server": "image_search"
        },
        {
            "name": "news_search",
            "description": "Search news articles",
            "server": "news_monitoring"
        },
        {
            "name": "generate_leads",
            "description": "Generate investigation leads",
            "server": "lead_generation"
        },
        {
            "name": "relationship_analysis",
            "description": "Analyze relationships between entities",
            "server": "relationship_analysis"
        },
        {
            "name": "evidence_compilation",
            "description": "Compile and organize evidence",
            "server": "evidence_compilation"
        }
    ]
    
    tools_by_server["investigation_tools"] = {
        "name": "Investigation Tools",
        "description": "High-level investigation tools",
        "tools": investigation_tools
    }
    
    return {
        "success": True,
        "data": {
            "servers": tools_by_server,
            "total_tools": sum(len(server["tools"]) for server in tools_by_server.values())
        }
    }

