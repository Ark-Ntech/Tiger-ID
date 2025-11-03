"""Research Agent for gathering information from databases and APIs"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from backend.services.tiger_service import TigerService
from backend.services.facility_service import FacilityService
from backend.services.integration_service import IntegrationService
from backend.services.reference_data_service import ReferenceDataService
from backend.services.evidence_compilation_service import get_evidence_compilation_service
from backend.services.investigation_service import InvestigationService
from backend.services.external_apis.factory import get_api_manager
from backend.database import get_db_session
from backend.utils.logging import get_logger
from backend.utils.uuid_helpers import safe_uuid, parse_uuid

logger = get_logger(__name__)


class ResearchAgent:
    """Agent specialized in querying data sources and gathering facts"""
    
    def __init__(
        self, 
        db: Optional[Session] = None,
        tiger_service: Optional[TigerService] = None,
        skip_ml_models: bool = False
    ):
        """
        Initialize Research Agent
        
        Args:
            db: Database session (optional, will create if not provided)
            tiger_service: TigerService instance (optional, for testing)
            skip_ml_models: Skip ML model initialization (for testing)
        """
        self.db = db
        # Allow dependency injection or skip ML models for testing
        if tiger_service:
            self.tiger_service = tiger_service
        elif not skip_ml_models and db:
            self.tiger_service = TigerService(db)
        else:
            self.tiger_service = None
            
        self.facility_service = FacilityService(db) if db else None
        # Use consolidated API manager from factory
        self.api_manager = get_api_manager()
        # Integration service for syncing external API data
        self.integration_service = IntegrationService(
            session=db,
            usda_client=None,  # Will be initialized from config
            cites_client=None,
            usfws_client=None
        ) if db else None
        # Reference data service
        self.ref_service = ReferenceDataService(db) if db else None
        
        # Investigation service for auto-linking evidence
        self.investigation_service = InvestigationService(db) if db else None
        
        # Evidence compilation service
        if db:
            self.evidence_service = get_evidence_compilation_service(db)
        else:
            self.evidence_service = None
    
    async def query_database(
        self,
        query_type: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Query internal database
        
        Args:
            query_type: Type of query (tiger, facility, etc.)
            params: Query parameters
            
        Returns:
            Query results
        """
        if not self.db:
            with get_db_session() as session:
                self.db = session
                self.tiger_service = TigerService(session)
                self.facility_service = FacilityService(session)
        
        results = {}
        
        try:
            if query_type == "tiger":
                # Search for tiger
                tiger_id = params.get("tiger_id")
                search_query = params.get("search_query")
                
                if tiger_id:
                    tiger_uuid = parse_uuid(tiger_id)
                    tiger = self.tiger_service.get_tiger(tiger_uuid)
                    if tiger:
                        results["tiger"] = {
                            "tiger_id": str(tiger.tiger_id),
                            "name": tiger.name,
                            "alias": tiger.alias,
                            "status": tiger.status,
                            "last_seen_location": tiger.last_seen_location,
                            "last_seen_date": str(tiger.last_seen_date) if tiger.last_seen_date else None,
                            "origin_facility_id": str(tiger.origin_facility_id) if tiger.origin_facility_id else None
                        }
                        # Get images
                        images = self.tiger_service.get_tiger_images(tiger.tiger_id)
                        results["tiger"]["images"] = [
                            {
                                "image_id": str(img.image_id),
                                "image_path": img.image_path,
                                "side_view": img.side_view,
                                "verified": img.verified
                            }
                            for img in images
                        ]
                elif search_query:
                    tigers = self.tiger_service.get_tigers(search_query=search_query)
                    results["tigers"] = [
                        {
                            "tiger_id": str(t.tiger_id),
                            "name": t.name,
                            "alias": t.alias,
                            "status": t.status
                        }
                        for t in tigers
                    ]
            
            elif query_type == "facility":
                # Search for facility
                facility_id = params.get("facility_id")
                usda_license = params.get("usda_license")
                state = params.get("state")
                search_query = params.get("search_query")
                
                if facility_id:
                    facility_uuid = parse_uuid(facility_id)
                    facility = self.facility_service.get_facility(facility_uuid)
                    if facility:
                        results["facility"] = self._format_facility(facility)
                elif usda_license:
                    facility = self.facility_service.get_facility_by_license(usda_license)
                    if facility:
                        results["facility"] = self._format_facility(facility)
                else:
                    facilities = self.facility_service.get_facilities(
                        state=state,
                        search_query=search_query
                    )
                    results["facilities"] = [self._format_facility(f) for f in facilities]
            
            elif query_type == "tiger_by_location":
                # Find tigers by location
                location = params.get("location")
                tigers = self.tiger_service.get_tigers()
                filtered = [
                    t for t in tigers
                    if t.last_seen_location and location.lower() in t.last_seen_location.lower()
                ]
                results["tigers"] = [
                    {
                        "tiger_id": str(t.tiger_id),
                        "name": t.name,
                        "location": t.last_seen_location
                    }
                    for t in filtered
                ]
        
        except Exception as e:
            logger.error("Database query failed", query_type=query_type, error=str(e))
            results["error"] = str(e)
        
        return results
    
    async def query_external_apis(
        self,
        api_type: str,
        params: Dict[str, Any],
        sync_to_db: bool = False,
        investigation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Query external data APIs
        
        Args:
            api_type: Type of API (usda, cites, usfws, all)
            params: Query parameters
            sync_to_db: Whether to sync results to database
            investigation_id: Optional investigation ID for evidence linking
            
        Returns:
            API query results
        """
        results = {}
        
        try:
            # Use integration service if available for syncing to database
            use_integration_service = self.integration_service and sync_to_db
            
            if api_type == "usda" or api_type == "all":
                # USDA API queries
                usda_license = params.get("usda_license")
                facility_name = params.get("facility_name")
                state = params.get("state")
                
                if use_integration_service and usda_license:
                    # Sync facility from USDA
                    facility = await self.integration_service.sync_facility_from_usda(
                        license_number=usda_license,
                        investigation_id=investigation_id
                    )
                    if facility:
                        results["usda_facility"] = {
                            "facility_id": str(facility.facility_id),
                            "exhibitor_name": facility.exhibitor_name,
                            "state": facility.state,
                            "usda_license": facility.usda_license
                        }
                elif usda_license:
                    inspections = await self.api_manager.usda.get_facility_inspections(usda_license)
                    results["usda_inspections"] = inspections
                
                if (facility_name or state) and not use_integration_service:
                    facilities = await self.api_manager.usda.search_facilities(
                        state=state,
                        facility_name=facility_name
                    )
                    if facilities:
                        results["usda_facility"] = facilities[0]
            
            if api_type == "cites" or api_type == "all":
                # CITES API queries
                state = params.get("state")
                year = params.get("year")
                
                if use_integration_service and investigation_id:
                    # Sync CITES records
                    records = await self.integration_service.sync_cites_trade_records(
                        investigation_id=investigation_id,
                        country_origin="US",
                        country_destination=None,
                        year=year,
                        limit=10
                    )
                    results["cites_records"] = records[:10]
                elif self.api_manager.cites:
                    cites_records = await self.api_manager.cites.search_trade_records(
                        species="Panthera tigris",
                        country_origin="US",
                        country_destination=None,
                        year=year
                    )
                    results["cites_records"] = cites_records[:10]  # Limit results
            
            if api_type == "usfws" or api_type == "all":
                # USFWS API queries
                facility_name = params.get("facility_name")
                state = params.get("state")
                
                if use_integration_service and investigation_id:
                    # Sync USFWS permits
                    permits = await self.integration_service.sync_usfws_permits(
                        investigation_id=investigation_id,
                        permit_number=None,
                        applicant_name=facility_name,
                        limit=10
                    )
                    results["usfws_permits"] = permits[:10]
                elif self.api_manager.usfws:
                    cases = await self.api_manager.usfws.search_permits(
                        species="Panthera tigris",
                        applicant_name=facility_name
                    )
                    results["usfws_cases"] = cases[:10]  # Limit results
        
        except Exception as e:
            logger.error("External API query failed", api_type=api_type, error=str(e))
            results["error"] = str(e)
        
        return results
    
    async def gather_all_data(
        self,
        facility_name: Optional[str] = None,
        usda_license: Optional[str] = None,
        state: Optional[str] = None,
        tiger_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gather data from all sources (database and APIs)
        
        Args:
            facility_name: Facility name to search
            usda_license: USDA license number
            state: State location
            tiger_id: Tiger ID to search
            
        Returns:
            Comprehensive data from all sources
        """
        results = {
            "database": {},
            "external_apis": {}
        }
        
        # Query database
        if tiger_id:
            results["database"]["tiger"] = await self.query_database(
                "tiger",
                {"tiger_id": tiger_id}
            )
        
        if facility_name or usda_license:
            results["database"]["facility"] = await self.query_database(
                "facility",
                {
                    "facility_name": facility_name,
                    "usda_license": usda_license,
                    "state": state
                }
            )
        
        # Query external APIs
        results["external_apis"] = await self.query_external_apis(
            "all",
            {
                "facility_name": facility_name,
                "usda_license": usda_license,
                "state": state
            }
        )
        
        return results
    
    def _format_facility(self, facility) -> Dict[str, Any]:
        """Format facility object for response"""
        return {
            "facility_id": str(facility.facility_id),
            "exhibitor_name": facility.exhibitor_name,
            "usda_license": facility.usda_license,
            "state": facility.state,
            "city": facility.city,
            "tiger_count": facility.tiger_count,
            "accreditation_status": facility.accreditation_status,
            "violation_history": facility.violation_history,
            "social_media_links": facility.social_media_links
        }
    
    async def search_web(
        self,
        query: str,
        limit: int = 10,
        investigation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Search the web for information
        
        Args:
            query: Search query
            limit: Maximum number of results
            investigation_id: Optional investigation ID for evidence linking
            
        Returns:
            Web search results
        """
        try:
            from backend.services.web_search_service import get_web_search_service
            
            search_service = get_web_search_service()
            results = await search_service.search(query, limit=limit)
            
            # Auto-link evidence to investigation if investigation_id provided
            if investigation_id and self.evidence_service and "results" in results:
                for result_item in results.get("results", [])[:5]:  # Link top 5 results
                    url = result_item.get("url")
                    if url:
                        try:
                            await self.evidence_service.compile_evidence_from_web(
                                investigation_id=investigation_id,
                                source_url=url,
                                source_type="web_search"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to auto-link evidence for {url}: {e}")
            
            return results
        
        except Exception as e:
            logger.error(f"Web search failed: {e}", exc_info=True)
            return {"error": str(e), "results": []}
    
    async def reverse_image_search(
        self,
        image_url: str,
        investigation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Perform reverse image search
        
        Args:
            image_url: URL of image to search
            investigation_id: Optional investigation ID for evidence linking
            
        Returns:
            Reverse image search results
        """
        try:
            from backend.services.image_search_service import get_image_search_service
            
            image_search = get_image_search_service()
            results = await image_search.reverse_search(image_url=image_url)
            
            # Auto-link evidence to investigation if investigation_id provided
            if investigation_id and self.evidence_service and "results" in results:
                # Create evidence for the original image
                try:
                    await self.evidence_service.compile_evidence_from_web(
                        investigation_id=investigation_id,
                        source_url=image_url,
                        source_type="reverse_image_search"
                    )
                except Exception as e:
                    logger.warning(f"Failed to auto-link evidence for image {image_url}: {e}")
                
                # Link matching results
                for result_item in results.get("results", [])[:3]:  # Link top 3 matches
                    url = result_item.get("url")
                    if url:
                        try:
                            await self.evidence_service.compile_evidence_from_web(
                                investigation_id=investigation_id,
                                source_url=url,
                                source_type="reverse_image_search"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to auto-link evidence for match {url}: {e}")
            
            return results
        
        except Exception as e:
            logger.error(f"Reverse image search failed: {e}", exc_info=True)
            return {"error": str(e), "results": []}
    
    async def search_news(
        self,
        query: Optional[str] = None,
        days: int = 7,
        limit: int = 20,
        investigation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Search for news articles
        
        Args:
            query: Search query (uses default keywords if not provided)
            days: Number of days to search back
            limit: Maximum number of results
            investigation_id: Optional investigation ID for evidence linking
            
        Returns:
            News search results
        """
        try:
            from backend.services.news_monitoring_service import get_news_monitoring_service
            
            news_service = get_news_monitoring_service()
            results = await news_service.search_news(query=query, days=days, limit=limit)
            
            # Auto-link evidence to investigation if investigation_id provided
            if investigation_id and self.evidence_service and "articles" in results:
                for article in results.get("articles", [])[:5]:  # Link top 5 articles
                    url = article.get("url")
                    if url:
                        try:
                            await self.evidence_service.compile_evidence_from_web(
                                investigation_id=investigation_id,
                                source_url=url,
                                source_type="news"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to auto-link evidence for news article {url}: {e}")
            
            return results
        
        except Exception as e:
            logger.error(f"News search failed: {e}", exc_info=True)
            return {"error": str(e), "articles": []}
    
    async def generate_leads(
        self,
        location: Optional[str] = None,
        investigation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Generate investigation leads
        
        Args:
            location: Geographic location filter
            investigation_id: Optional investigation ID for evidence linking
            
        Returns:
            Generated leads
        """
        try:
            from backend.services.lead_generation_service import get_lead_generation_service
            
            lead_service = get_lead_generation_service()
            leads = await lead_service.generate_leads(location=location)
            
            # Auto-link evidence to investigation if investigation_id provided
            if investigation_id and self.evidence_service and self.investigation_service and "leads" in leads:
                for lead in leads.get("leads", [])[:5]:  # Link top 5 leads
                    url = lead.get("url") or lead.get("source_url")
                    if url:
                        try:
                            await self.evidence_service.compile_evidence_from_web(
                                investigation_id=investigation_id,
                                source_url=url,
                                source_type="lead_generation"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to auto-link evidence for lead {url}: {e}")
            
            return leads
        
        except Exception as e:
            logger.error(f"Lead generation failed: {e}", exc_info=True)
            return {"error": str(e), "leads": []}
    
    async def check_reference_facilities(
        self,
        facility_name: Optional[str] = None,
        usda_license: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if facility is in reference dataset
        
        Args:
            facility_name: Facility name to check
            usda_license: USDA license to check
            
        Returns:
            Reference facility matches
        """
        if not self.db:
            with get_db_session() as session:
                self.db = session
                self.ref_service = ReferenceDataService(session)
                return await self.check_reference_facilities(facility_name, usda_license)
        
        if not self.ref_service:
            self.ref_service = ReferenceDataService(self.db)
        
        matches = self.ref_service.find_matching_facilities(
            name=facility_name,
            usda_license=usda_license
        )
        
        return {
            "matches": [
                {
                    "facility_id": str(f.facility_id),
                    "exhibitor_name": f.exhibitor_name,
                    "is_reference": f.is_reference_facility,
                    "state": f.state
                }
                for f in matches
            ],
            "count": len(matches),
            "has_reference_match": any(f.is_reference_facility for f in matches)
        }
    
    async def search_youtube_videos(
        self,
        query: str,
        facility_context: Optional[Dict[str, Any]] = None,
        orchestrator: Optional[Any] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search YouTube videos related to investigation
        
        Args:
            query: Search query (e.g., facility name, location)
            facility_context: Optional facility context for enhanced search
            orchestrator: Optional orchestrator instance to use MCP tools
            max_results: Maximum number of results
        
        Returns:
            Search results with videos
        """
        try:
            # Use orchestrator's MCP tool if available
            if orchestrator and hasattr(orchestrator, 'use_mcp_tool'):
                result = await orchestrator.use_mcp_tool(
                    server_name="youtube",
                    tool_name="youtube_search_videos",
                    arguments={
                        "query": query,
                        "max_results": max_results
                    }
                )
                return result
            else:
                # Fallback to direct API client access
                if self.api_manager.youtube:
                    videos = await self.api_manager.youtube.search_videos(
                        query=query,
                        max_results=max_results
                    )
                    return {
                        "query": query,
                        "videos": videos,
                        "count": len(videos)
                    }
                else:
                    return {"error": "YouTube client not available", "videos": [], "count": 0}
        except Exception as e:
            logger.error("YouTube video search failed", query=query, error=str(e))
            return {"error": str(e), "videos": [], "count": 0}
    
    async def search_meta_pages(
        self,
        query: str,
        facility_context: Optional[Dict[str, Any]] = None,
        orchestrator: Optional[Any] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search Meta/Facebook pages related to investigation
        
        Args:
            query: Search query (e.g., facility name)
            facility_context: Optional facility context for enhanced search
            orchestrator: Optional orchestrator instance to use MCP tools
            limit: Maximum number of results
        
        Returns:
            Search results with pages
        """
        try:
            # Use orchestrator's MCP tool if available
            if orchestrator and hasattr(orchestrator, 'use_mcp_tool'):
                result = await orchestrator.use_mcp_tool(
                    server_name="meta",
                    tool_name="meta_search_pages",
                    arguments={
                        "query": query,
                        "limit": limit
                    }
                )
                return result
            else:
                # Fallback to direct API client access
                if self.api_manager.meta:
                    pages = await self.api_manager.meta.search_pages(query=query, limit=limit)
                    return {
                        "query": query,
                        "pages": pages,
                        "count": len(pages)
                    }
                else:
                    return {"error": "Meta client not available", "pages": [], "count": 0}
        except Exception as e:
            logger.error("Meta page search failed", query=query, error=str(e))
            return {"error": str(e), "pages": [], "count": 0}
    
    async def capture_web_evidence(
        self,
        url: str,
        facility_context: Optional[Dict[str, Any]] = None,
        orchestrator: Optional[Any] = None,
        take_screenshot: bool = True,
        extract_content: bool = True
    ) -> Dict[str, Any]:
        """
        Capture web evidence using Puppeteer browser automation
        
        Args:
            url: URL to capture
            facility_context: Optional facility context
            orchestrator: Optional orchestrator instance to use MCP tools
            take_screenshot: Whether to capture a screenshot
            extract_content: Whether to extract page content
        
        Returns:
            Evidence data with screenshot and/or content
        """
        try:
            # Use orchestrator's MCP tool if available
            if orchestrator and hasattr(orchestrator, 'use_mcp_tool'):
                evidence = {
                    "url": url,
                    "screenshot": None,
                    "content": None,
                    "title": None,
                    "timestamp": None
                }
                
                # Navigate to page
                nav_result = await orchestrator.use_mcp_tool(
                    server_name="puppeteer",
                    tool_name="puppeteer_navigate",
                    arguments={"url": url, "wait_until": "networkidle"}
                )
                
                if nav_result.get("success"):
                    evidence["title"] = nav_result.get("title")
                    evidence["timestamp"] = nav_result.get("url")
                    
                    # Take screenshot if requested
                    if take_screenshot:
                        screenshot_result = await orchestrator.use_mcp_tool(
                            server_name="puppeteer",
                            tool_name="puppeteer_screenshot",
                            arguments={"full_page": True}
                        )
                        if screenshot_result.get("success"):
                            evidence["screenshot"] = screenshot_result.get("screenshot")
                    
                    # Extract content if requested
                    if extract_content:
                        content_result = await orchestrator.use_mcp_tool(
                            server_name="puppeteer",
                            tool_name="puppeteer_get_content",
                            arguments={}
                        )
                        if content_result.get("success"):
                            evidence["content"] = content_result.get("content")
                    
                    return {
                        "url": url,
                        "evidence": evidence,
                        "success": True
                    }
                else:
                    return {
                        "url": url,
                        "error": nav_result.get("error"),
                        "success": False
                    }
            else:
                return {
                    "url": url,
                    "error": "Orchestrator not available for Puppeteer automation",
                    "success": False
                }
        except Exception as e:
            logger.error("Web evidence capture failed", url=url, error=str(e))
            return {"error": str(e), "url": url, "success": False}
    
    async def get_social_media_intelligence(
        self,
        facility_name: str,
        location: Optional[str] = None,
        orchestrator: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Gather social media intelligence for a facility
        
        Args:
            facility_name: Facility name
            location: Optional location
            orchestrator: Optional orchestrator instance to use MCP tools
        
        Returns:
            Combined social media intelligence from YouTube and Meta
        """
        results = {
            "facility_name": facility_name,
            "location": location,
            "youtube": {},
            "meta": {}
        }
        
        # Search YouTube
        youtube_query = f"{facility_name}"
        if location:
            youtube_query += f" {location}"
        
        youtube_result = await self.search_youtube_videos(
            query=youtube_query,
            facility_context={"name": facility_name, "location": location},
            orchestrator=orchestrator,
            max_results=10
        )
        results["youtube"] = youtube_result
        
        # Search Meta/Facebook
        meta_result = await self.search_meta_pages(
            query=facility_name,
            facility_context={"name": facility_name, "location": location},
            orchestrator=orchestrator,
            limit=10
        )
        results["meta"] = meta_result
        
        # Store as evidence if db available
        if self.db and self.investigation_service:
            try:
                # This would need investigation_id - for now just log
                logger.info(
                    "Social media intelligence gathered",
                    facility_name=facility_name,
                    youtube_count=youtube_result.get("count", 0),
                    meta_count=meta_result.get("count", 0)
                )
            except Exception as e:
                logger.warning("Failed to store evidence", error=str(e))
        
        return results
    
    async def close(self):
        """Close API connections"""
        await self.api_manager.close_all()
