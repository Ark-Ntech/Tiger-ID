"""Firecrawl MCP server for web scraping and search"""

from typing import Dict, Any, List, Optional

from backend.mcp_servers.base_mcp_server import MCPServerBase, MCPTool
from firecrawl import FirecrawlApp
from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)


class FirecrawlMCPServer(MCPServerBase):
    """Firecrawl MCP server for web search and scraping"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Firecrawl MCP server
        
        Args:
            api_key: Firecrawl API key
        """
        super().__init__("firecrawl")
        settings = get_settings()
        self.api_key = api_key or settings.firecrawl.api_key
        self.client = FirecrawlApp(api_key=self.api_key) if self.api_key else None
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register available tools"""
        self.tools = {
            "firecrawl_search": MCPTool(
                name="firecrawl_search",
                description="Search the web for information",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                },
                handler=self._handle_search
            ),
            "firecrawl_scrape": MCPTool(
                name="firecrawl_scrape",
                description="Scrape a single web page with full Firecrawl capabilities (actions, wait_for, mobile, etc.)",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to scrape"
                        },
                        "extract": {
                            "type": "boolean",
                            "description": "Extract structured data using LLM",
                            "default": True
                        },
                        "wait_for": {
                            "type": "integer",
                            "description": "Wait time in milliseconds for dynamic content to load",
                            "default": None
                        },
                        "actions": {
                            "type": "array",
                            "description": "List of actions to perform before scraping (click, scroll, wait, etc.)",
                            "items": {"type": "object"},
                            "default": None
                        },
                        "mobile": {
                            "type": "boolean",
                            "description": "Use mobile user agent",
                            "default": False
                        }
                    },
                    "required": ["url"]
                },
                handler=self._handle_scrape
            ),
            "firecrawl_crawl": MCPTool(
                name="firecrawl_crawl",
                description="Crawl a website and extract all pages",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "Base URL to crawl"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of pages",
                            "default": 10
                        }
                    },
                    "required": ["url"]
                },
                handler=self._handle_crawl
            ),
            "firecrawl_extract": MCPTool(
                name="firecrawl_extract",
                description="Extract structured data from a web page using LLM",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to extract from"
                        },
                        "schema": {
                            "type": "object",
                            "description": "JSON schema for extraction"
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Natural language prompt for extraction"
                        }
                    },
                    "required": ["url"]
                },
                handler=self._handle_extract
            )
        }
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        return [tool.to_dict() for tool in self.tools.values()]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool"""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}
        
        try:
            return await self.tools[tool_name].call(arguments)
        except Exception as e:
            logger.error("Tool call failed", tool=tool_name, error=str(e))
            return {"error": str(e)}
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources"""
        return []
    
    async def _handle_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Handle web search using Firecrawl's native search method if available,
        otherwise fallback to web search service
        """
        if not self.client:
            logger.warning("Firecrawl API key not configured - using fallback")
            # Fallback to web search service
            try:
                from backend.services.web_search_service import get_web_search_service
                search_service = get_web_search_service()
                result = await search_service.search(query, limit=limit, provider="serper")
                return result
            except Exception as e:
                logger.error("Search fallback failed", query=query, error=str(e))
                return {"error": str(e), "results": [], "query": query, "count": 0}
        
        try:
            # Try Firecrawl's native search method if available
            if hasattr(self.client, 'search'):
                logger.info(f"Using Firecrawl native search for: {query[:50]}")
                search_result = self.client.search(query, limit=limit)
                
                # Handle search result (may be async job or immediate result)
                if hasattr(search_result, 'job_id'):
                    # Async job - poll for status
                    job_id = search_result.job_id
                    import asyncio
                    max_polls = 20
                    poll_interval = 1
                    
                    for poll_count in range(max_polls):
                        status = self.client.get_batch_scrape_status(job_id) if hasattr(self.client, 'get_batch_scrape_status') else None
                        if status and (hasattr(status, 'status') and status.status in ["completed", "done"] or isinstance(status, dict) and status.get("status") in ["completed", "done"]):
                            # Get results
                            if hasattr(status, 'data'):
                                results_data = status.data
                            elif isinstance(status, dict):
                                results_data = status.get("data", [])
                            else:
                                results_data = []
                            
                            results = []
                            for item in results_data[:limit]:
                                if hasattr(item, 'markdown'):
                                    results.append({
                                        "title": getattr(item, 'title', ''),
                                        "url": getattr(item, 'url', ''),
                                        "snippet": getattr(item, 'markdown', '')[:200]
                                    })
                                else:
                                    results.append({
                                        "title": item.get("title", ""),
                                        "url": item.get("url", ""),
                                        "snippet": item.get("markdown", "")[:200]
                                    })
                            
                            return {
                                "results": results,
                                "query": query,
                                "count": len(results),
                                "provider": "firecrawl"
                            }
                        await asyncio.sleep(poll_interval)
                    
                    return {"error": "Search job timed out", "results": [], "query": query, "count": 0}
                else:
                    # Immediate result
                    if hasattr(search_result, 'data'):
                        results_data = search_result.data
                    else:
                        results_data = search_result.get("data", []) if isinstance(search_result, dict) else []
                    
                    results = []
                    for item in results_data[:limit]:
                        if hasattr(item, 'markdown'):
                            results.append({
                                "title": getattr(item, 'title', ''),
                                "url": getattr(item, 'url', ''),
                                "snippet": getattr(item, 'markdown', '')[:200]
                            })
                        else:
                            results.append({
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("markdown", "")[:200]
                            })
                    
                    return {
                        "results": results,
                        "query": query,
                        "count": len(results),
                        "provider": "firecrawl"
                    }
            else:
                # Fallback to web search service
                logger.info("Firecrawl search method not available, using web search service")
                from backend.services.web_search_service import get_web_search_service
                search_service = get_web_search_service()
                result = await search_service.search(query, limit=limit, provider="serper")
                return result
                
        except Exception as e:
            logger.error("Search failed", query=query, error=str(e), exc_info=True)
            # Fallback to web search service
            try:
                from backend.services.web_search_service import get_web_search_service
                search_service = get_web_search_service()
                result = await search_service.search(query, limit=limit, provider="serper")
                return result
            except Exception as fallback_error:
                logger.error("Search fallback also failed", error=str(fallback_error))
                return {"error": str(e), "results": [], "query": query, "count": 0}
    
    async def _handle_scrape(
        self, 
        url: str, 
        extract: bool = True,
        wait_for: Optional[int] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        mobile: bool = False
    ) -> Dict[str, Any]:
        """
        Handle page scraping with full Firecrawl capabilities
        
        Args:
            url: URL to scrape
            extract: Extract structured data using LLM
            wait_for: Wait time in milliseconds for dynamic content
            actions: List of actions to perform before scraping (click, scroll, etc.)
            mobile: Use mobile user agent
        """
        if not self.client:
            logger.warning("Firecrawl API key not configured - returning empty result")
            return {
                "url": url,
                "content": "",
                "html": "",
                "extracted": None,
                "warning": "Firecrawl API key not configured. Set FIRECRAWL_API_KEY to enable web scraping."
            }
        
        try:
            # Build scrape parameters with all available options
            scrape_params = {
                "formats": ["markdown", "html"],
                "only_main_content": True
            }
            
            if wait_for:
                scrape_params["wait_for"] = wait_for
            if actions:
                scrape_params["actions"] = actions
            if mobile:
                scrape_params["mobile"] = True
            
            result = self.client.scrape(url, **scrape_params)
            
            # Handle Document object (Firecrawl SDK v4+ returns Document objects)
            if hasattr(result, 'markdown'):
                markdown_content = result.markdown
                html_content = result.html if hasattr(result, 'html') else ""
                metadata = result.metadata if hasattr(result, 'metadata') else {}
            else:
                # Fallback for dict responses
                markdown_content = result.get("markdown", "")
                html_content = result.get("html", "")
                metadata = result.get("metadata", {})
            
            extracted_data = None
            if extract:
                # Use LLM extraction if available
                extracted_data = markdown_content[:1000] if markdown_content else None
            
            return {
                "url": url,
                "content": markdown_content,
                "html": html_content,
                "extracted": extracted_data,
                "title": metadata.get("title", "") if isinstance(metadata, dict) else getattr(metadata, "title", "")
            }
        except Exception as e:
            logger.error("Scrape failed", url=url, error=str(e), exc_info=True)
            return {"error": str(e), "url": url}
    
    async def _handle_crawl(self, url: str, limit: int = 10) -> Dict[str, Any]:
        """
        Handle website crawling using Firecrawl's async job system
        
        Note: Firecrawl's crawl() returns a CrawlJob object that needs to be polled for status.
        This implementation starts the crawl and polls for completion.
        """
        if not self.client:
            logger.warning("Firecrawl API key not configured - returning empty result")
            return {
                "base_url": url,
                "pages": [],
                "count": 0,
                "warning": "Firecrawl API key not configured. Set FIRECRAWL_API_KEY to enable web crawling."
            }
        
        try:
            # Use start_crawl for async job or crawl for synchronous (with polling)
            from firecrawl.v2.types import ScrapeOptions
            
            scrape_options = ScrapeOptions(
                formats=["markdown", "html"],
                only_main_content=True
            )
            
            # Use start_crawl if available (returns CrawlResponse with job_id)
            # Otherwise use crawl (which handles polling internally)
            if hasattr(self.client, 'start_crawl'):
                logger.info(f"Starting crawl job for {url}")
                crawl_response = self.client.start_crawl(
                    url=url,
                    limit=limit,
                    scrape_options=scrape_options
                )
                
                # Get job ID from response
                job_id = crawl_response.job_id if hasattr(crawl_response, 'job_id') else (crawl_response.get("job_id") if isinstance(crawl_response, dict) else None)
                
                if not job_id:
                    logger.error("Crawl job started but no job_id returned")
                    return {"error": "Crawl job failed to start", "base_url": url}
                
                logger.info(f"Crawl job started: {job_id}, polling for status...")
                
                # Poll for crawl status (with timeout)
                import asyncio
                max_polls = 30  # Maximum number of polls
                poll_interval = 2  # Seconds between polls
                
                for poll_count in range(max_polls):
                    status = self.client.get_crawl_status(job_id)
                    
                    # Check if job is complete
                    if hasattr(status, 'status'):
                        job_status = status.status
                    elif isinstance(status, dict):
                        job_status = status.get("status", "unknown")
                    else:
                        job_status = str(status)
                    
                    if job_status in ["completed", "done", "success"]:
                        # Get crawl results
                        if hasattr(status, 'data'):
                            pages_data = status.data
                        elif isinstance(status, dict):
                            pages_data = status.get("data", [])
                        else:
                            pages_data = []
                        
                        pages = []
                        for page in pages_data[:limit]:
                            if hasattr(page, 'markdown'):
                                page_content = page.markdown
                                page_url = page.url if hasattr(page, 'url') else ""
                                page_metadata = page.metadata if hasattr(page, 'metadata') else {}
                            else:
                                page_content = page.get("markdown", "")
                                page_url = page.get("url", "")
                                page_metadata = page.get("metadata", {})
                            
                            pages.append({
                                "url": page_url,
                                "content": page_content[:500] if page_content else "",  # Limit content
                                "title": page_metadata.get("title", "") if isinstance(page_metadata, dict) else getattr(page_metadata, "title", "")
                            })
                        
                        logger.info(f"Crawl completed: {len(pages)} pages")
                        return {
                            "base_url": url,
                            "pages": pages,
                            "count": len(pages),
                            "job_id": job_id
                        }
                    elif job_status in ["failed", "error"]:
                        error_msg = "Crawl job failed"
                        if hasattr(status, 'error'):
                            error_msg = status.error
                        elif isinstance(status, dict):
                            error_msg = status.get("error", error_msg)
                        logger.error(f"Crawl job failed: {error_msg}")
                        return {"error": error_msg, "base_url": url, "job_id": job_id}
                    
                    # Wait before next poll
                    await asyncio.sleep(poll_interval)
                
                # Timeout - return partial results if available
                logger.warning(f"Crawl job timed out after {max_polls * poll_interval} seconds")
                return {
                    "base_url": url,
                    "pages": [],
                    "count": 0,
                    "job_id": job_id,
                    "warning": f"Crawl job timed out. Check status with job_id: {job_id}"
                }
            else:
                # Use crawl method which handles polling internally
                logger.info(f"Using crawl method for {url} (with internal polling)")
                crawl_job = self.client.crawl(
                    url=url,
                    limit=limit,
                    scrape_options=scrape_options,
                    poll_interval=2,
                    timeout=60
                )
                
                # Get job ID
                job_id = crawl_job.job_id if hasattr(crawl_job, 'job_id') else None
                
                # The crawl method should handle polling internally, but we'll check status
                if hasattr(crawl_job, 'data'):
                    pages_data = crawl_job.data
                elif hasattr(crawl_job, 'pages'):
                    pages_data = crawl_job.pages
                else:
                    pages_data = []
                
                pages = []
                for page in pages_data[:limit]:
                    if hasattr(page, 'markdown'):
                        page_content = page.markdown
                        page_url = page.url if hasattr(page, 'url') else ""
                        page_metadata = page.metadata if hasattr(page, 'metadata') else {}
                    else:
                        page_content = page.get("markdown", "")
                        page_url = page.get("url", "")
                        page_metadata = page.get("metadata", {})
                    
                    pages.append({
                        "url": page_url,
                        "content": page_content[:500] if page_content else "",
                        "title": page_metadata.get("title", "") if isinstance(page_metadata, dict) else getattr(page_metadata, "title", "")
                    })
                
                logger.info(f"Crawl completed: {len(pages)} pages")
                return {
                    "base_url": url,
                    "pages": pages,
                    "count": len(pages),
                    "job_id": job_id
                }
            
        except Exception as e:
            logger.error("Crawl failed", url=url, error=str(e), exc_info=True)
            return {"error": str(e), "base_url": url}
    
    async def _handle_extract(self, url: str, schema: Optional[Dict] = None, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle structured data extraction using Firecrawl's extract method
        
        Args:
            url: URL to extract from
            schema: JSON schema for extraction (optional)
            prompt: Natural language prompt for extraction (optional)
        """
        if not self.client:
            logger.warning("Firecrawl API key not configured - returning empty result")
            return {
                "url": url,
                "extracted": "",
                "schema": schema,
                "warning": "Firecrawl API key not configured. Set FIRECRAWL_API_KEY to enable data extraction."
            }
        
        try:
            # Use Firecrawl's extract method if available
            if hasattr(self.client, 'extract'):
                # Start extract job
                extract_job = self.client.start_extract(
                    url=url,
                    schema=schema,
                    prompt=prompt
                )
                
                # Get job ID
                job_id = extract_job.job_id if hasattr(extract_job, 'job_id') else None
                
                if job_id:
                    # Poll for extract status
                    import asyncio
                    max_polls = 20
                    poll_interval = 1
                    
                    for poll_count in range(max_polls):
                        status = self.client.get_extract_status(job_id)
                        
                        if hasattr(status, 'status'):
                            job_status = status.status
                        elif isinstance(status, dict):
                            job_status = status.get("status", "unknown")
                        else:
                            job_status = str(status)
                        
                        if job_status in ["completed", "done", "success"]:
                            # Get extracted data
                            if hasattr(status, 'data'):
                                extracted_data = status.data
                            elif isinstance(status, dict):
                                extracted_data = status.get("data", {})
                            else:
                                extracted_data = {}
                            
                            logger.info(f"Extract completed for {url}")
                            return {
                                "url": url,
                                "extracted": extracted_data,
                                "schema": schema,
                                "job_id": job_id
                            }
                        elif job_status in ["failed", "error"]:
                            error_msg = "Extract job failed"
                            if hasattr(status, 'error'):
                                error_msg = status.error
                            elif isinstance(status, dict):
                                error_msg = status.get("error", error_msg)
                            logger.error(f"Extract job failed: {error_msg}")
                            # Fallback to scrape
                            break
                        
                        await asyncio.sleep(poll_interval)
            
            # Fallback to scrape if extract fails or is not available
            logger.info(f"Using scrape fallback for extraction from {url}")
            scrape_result = await self._handle_scrape(url, extract=False)
            
            return {
                "url": url,
                "extracted": scrape_result.get("content", "")[:1000] if scrape_result.get("content") else "",
                "schema": schema,
                "method": "scrape_fallback"
            }
        except Exception as e:
            logger.error("Extract failed", url=url, error=str(e), exc_info=True)
            return {"error": str(e), "url": url}
