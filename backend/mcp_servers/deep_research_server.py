"""
Deep Research MCP Server

Provides iterative multi-query research capabilities built on DuckDuckGo.
No API keys required - fully local operation.
"""

from typing import Any, Dict, List, Optional
import uuid
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from backend.mcp_servers.base_mcp_server import MCPServerBase, MCPTool
from backend.models.anthropic_chat import AnthropicChatModel
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Try to import DuckDuckGo search
try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False
    logger.warning("duckduckgo-search not available, deep research will be limited")


class ResearchDepth(str, Enum):
    """Research depth levels."""
    QUICK = "quick"      # 3 queries
    STANDARD = "standard"  # 10 queries
    DEEP = "deep"        # 25+ queries


class ResearchMode(str, Enum):
    """Research modes for different investigation types."""
    FACILITY = "facility_investigation"
    PROVENANCE = "tiger_provenance"
    TRAFFICKING = "trafficking_patterns"
    REGULATORY = "regulatory_history"
    GENERAL = "general"


@dataclass
class SearchResult:
    """A single search result."""
    title: str
    url: str
    snippet: str
    source_type: str = "web"
    credibility: str = "unknown"  # high, medium, low, unknown

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source_type": self.source_type,
            "credibility": self.credibility
        }


@dataclass
class ResearchSession:
    """A research session tracking queries and results."""
    session_id: str
    topic: str
    mode: ResearchMode
    depth: ResearchDepth
    queries_executed: List[str] = field(default_factory=list)
    results: List[SearchResult] = field(default_factory=list)
    entities_found: List[str] = field(default_factory=list)
    status: str = "active"  # active, saturated, completed, failed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    max_queries: int = 10

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "topic": self.topic,
            "mode": self.mode.value,
            "depth": self.depth.value,
            "queries_executed": self.queries_executed,
            "results_count": len(self.results),
            "entities_found": self.entities_found,
            "status": self.status,
            "created_at": self.created_at
        }


class DeepResearchMCPServer(MCPServerBase):
    """
    MCP server for deep iterative research using DuckDuckGo.

    Provides tools for:
    - Starting research sessions with different depths
    - Expanding research based on findings
    - Synthesizing all findings into coherent summary
    - Visualizing source relationships

    All searches use DuckDuckGo - no API keys required.
    """

    def __init__(self):
        """Initialize the Deep Research MCP server."""
        super().__init__("deep_research")

        # Active research sessions
        self._sessions: Dict[str, ResearchSession] = {}

        # Claude model for query expansion and synthesis
        self._chat_model = None

        # DuckDuckGo search instance
        self._ddgs = DDGS() if HAS_DDGS else None

        self._register_tools()
        logger.info("DeepResearchMCPServer initialized")

    def _register_tools(self):
        """Register available tools."""
        self.tools = {
            "start_research": MCPTool(
                name="start_research",
                description="Start a new research session on a topic. Returns session_id for subsequent operations.",
                parameters={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The topic or entity to research"
                        },
                        "mode": {
                            "type": "string",
                            "enum": [m.value for m in ResearchMode],
                            "description": "Research mode determining query strategy",
                            "default": "general"
                        },
                        "depth": {
                            "type": "string",
                            "enum": [d.value for d in ResearchDepth],
                            "description": "Research depth (quick=3, standard=10, deep=25+ queries)",
                            "default": "standard"
                        },
                        "initial_context": {
                            "type": "object",
                            "description": "Optional context to guide research",
                            "default": {}
                        }
                    },
                    "required": ["topic"]
                },
                handler=self._handle_start_research
            ),
            "expand_research": MCPTool(
                name="expand_research",
                description="Expand research by following promising leads found in initial results.",
                parameters={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "The research session ID"
                        },
                        "direction": {
                            "type": "string",
                            "description": "Optional direction to focus expansion (e.g., 'violations', 'ownership')"
                        },
                        "additional_queries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional specific queries to add"
                        }
                    },
                    "required": ["session_id"]
                },
                handler=self._handle_expand_research
            ),
            "synthesize_findings": MCPTool(
                name="synthesize_findings",
                description="Synthesize all research findings into a coherent summary with citations.",
                parameters={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "The research session ID"
                        },
                        "focus_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional areas to focus synthesis on"
                        }
                    },
                    "required": ["session_id"]
                },
                handler=self._handle_synthesize
            ),
            "get_source_graph": MCPTool(
                name="get_source_graph",
                description="Get a graph of source relationships and credibility scores.",
                parameters={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "The research session ID"
                        }
                    },
                    "required": ["session_id"]
                },
                handler=self._handle_get_source_graph
            ),
            "get_session_status": MCPTool(
                name="get_session_status",
                description="Get the current status of a research session.",
                parameters={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "The research session ID"
                        }
                    },
                    "required": ["session_id"]
                },
                handler=self._handle_get_status
            )
        }

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        return [tool.to_dict() for tool in self.tools.values()]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool."""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}

        try:
            return await self.tools[tool_name].call(arguments)
        except Exception as e:
            logger.error(f"Tool call failed: {tool_name}", error=str(e), exc_info=True)
            return {"error": str(e)}

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources."""
        return []

    def _get_chat_model(self) -> AnthropicChatModel:
        """Get or create the chat model."""
        if self._chat_model is None:
            self._chat_model = AnthropicChatModel(model_name="claude-sonnet-4-5-20250929")
        return self._chat_model

    def _search_duckduckgo(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Execute a DuckDuckGo search."""
        if not HAS_DDGS or not self._ddgs:
            return []

        try:
            results = []
            for r in self._ddgs.text(query, max_results=max_results):
                result = SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", r.get("link", "")),
                    snippet=r.get("body", r.get("snippet", "")),
                    source_type=self._classify_source_type(r.get("href", "")),
                    credibility=self._assess_credibility(r.get("href", ""))
                )
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []

    def _classify_source_type(self, url: str) -> str:
        """Classify the source type based on URL."""
        url_lower = url.lower()

        if any(d in url_lower for d in ['.gov', 'usda.', 'fws.gov', 'usfws.gov']):
            return "government"
        elif any(d in url_lower for d in ['cites.org', 'iucn.org', 'wwf.org', 'traffic.org']):
            return "conservation"
        elif any(d in url_lower for d in ['reuters.', 'apnews.', 'bbc.', 'nytimes.', 'washingtonpost.']):
            return "news"
        elif any(d in url_lower for d in ['facebook.com', 'twitter.com', 'instagram.com', 'tiktok.com']):
            return "social_media"
        elif any(d in url_lower for d in ['.edu']):
            return "academic"
        else:
            return "web"

    def _assess_credibility(self, url: str) -> str:
        """Assess source credibility based on URL."""
        source_type = self._classify_source_type(url)

        if source_type in ["government", "academic"]:
            return "high"
        elif source_type in ["conservation", "news"]:
            return "medium"
        else:
            return "low"

    def _generate_initial_queries(
        self,
        topic: str,
        mode: ResearchMode,
        depth: ResearchDepth
    ) -> List[str]:
        """Generate initial search queries based on mode and depth."""
        base_queries = [f'"{topic}"']

        mode_queries = {
            ResearchMode.FACILITY: [
                f'"{topic}" USDA inspection',
                f'"{topic}" tiger',
                f'"{topic}" exotic animal',
                f'"{topic}" owner',
            ],
            ResearchMode.PROVENANCE: [
                f'"{topic}" breeding',
                f'"{topic}" transfer',
                f'"{topic}" origin',
                f'"{topic}" born',
            ],
            ResearchMode.TRAFFICKING: [
                f'"{topic}" trafficking',
                f'"{topic}" seizure',
                f'"{topic}" illegal',
                f'"{topic}" investigation',
            ],
            ResearchMode.REGULATORY: [
                f'"{topic}" USDA',
                f'"{topic}" CITES',
                f'"{topic}" violation',
                f'"{topic}" license',
            ],
            ResearchMode.GENERAL: [
                f'"{topic}"',
                f'"{topic}" news',
                f'"{topic}" information',
            ]
        }

        queries = mode_queries.get(mode, mode_queries[ResearchMode.GENERAL])

        # Adjust based on depth
        max_queries = {
            ResearchDepth.QUICK: 3,
            ResearchDepth.STANDARD: 10,
            ResearchDepth.DEEP: 25
        }

        return queries[:max_queries[depth]]

    async def _handle_start_research(
        self,
        topic: str,
        mode: str = "general",
        depth: str = "standard",
        initial_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Handle starting a new research session."""
        try:
            if not HAS_DDGS:
                return {
                    "error": "DuckDuckGo search not available. Install: pip install duckduckgo-search",
                    "success": False
                }

            session_id = str(uuid.uuid4())[:8]
            research_mode = ResearchMode(mode)
            research_depth = ResearchDepth(depth)

            max_queries = {"quick": 3, "standard": 10, "deep": 25}

            session = ResearchSession(
                session_id=session_id,
                topic=topic,
                mode=research_mode,
                depth=research_depth,
                max_queries=max_queries[depth]
            )

            # Generate initial queries
            queries = self._generate_initial_queries(topic, research_mode, research_depth)

            # Execute searches
            for query in queries:
                results = self._search_duckduckgo(query, max_results=5)
                session.queries_executed.append(query)
                session.results.extend(results)

                # Extract entities for follow-up
                for r in results:
                    # Simple entity extraction from titles
                    if topic.lower() not in r.title.lower():
                        session.entities_found.append(r.title[:50])

            # Remove duplicates
            seen_urls = set()
            unique_results = []
            for r in session.results:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    unique_results.append(r)
            session.results = unique_results

            self._sessions[session_id] = session

            logger.info(f"Started research session {session_id} on '{topic}' with {len(session.results)} results")

            return {
                "success": True,
                "session_id": session_id,
                "topic": topic,
                "mode": mode,
                "depth": depth,
                "queries_executed": len(session.queries_executed),
                "results_found": len(session.results),
                "entities_discovered": session.entities_found[:10],
                "status": "active",
                "message": f"Research started. Found {len(session.results)} results from {len(session.queries_executed)} queries."
            }

        except Exception as e:
            logger.error(f"Failed to start research: {e}")
            return {"error": str(e), "success": False}

    async def _handle_expand_research(
        self,
        session_id: str,
        direction: Optional[str] = None,
        additional_queries: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Handle expanding research with follow-up queries."""
        try:
            if session_id not in self._sessions:
                return {"error": f"Session {session_id} not found", "success": False}

            session = self._sessions[session_id]

            if session.status != "active":
                return {"error": f"Session is {session.status}", "success": False}

            # Check if we've hit the query limit
            if len(session.queries_executed) >= session.max_queries:
                session.status = "saturated"
                return {
                    "success": True,
                    "session_id": session_id,
                    "status": "saturated",
                    "message": f"Research saturated at {session.max_queries} queries. Use synthesize_findings to summarize."
                }

            # Generate expansion queries
            expansion_queries = []

            if additional_queries:
                expansion_queries.extend(additional_queries)

            if direction:
                expansion_queries.append(f'"{session.topic}" {direction}')

            # Use entities found to generate more queries
            for entity in session.entities_found[:3]:
                if entity not in ' '.join(session.queries_executed):
                    expansion_queries.append(f'"{session.topic}" "{entity}"')

            # Execute new searches
            new_results = 0
            for query in expansion_queries:
                if len(session.queries_executed) >= session.max_queries:
                    break

                if query not in session.queries_executed:
                    results = self._search_duckduckgo(query, max_results=5)
                    session.queries_executed.append(query)

                    for r in results:
                        if r.url not in [sr.url for sr in session.results]:
                            session.results.append(r)
                            new_results += 1

            logger.info(f"Expanded session {session_id}: +{new_results} results")

            return {
                "success": True,
                "session_id": session_id,
                "new_results": new_results,
                "total_results": len(session.results),
                "queries_executed": len(session.queries_executed),
                "remaining_queries": session.max_queries - len(session.queries_executed),
                "status": session.status,
                "message": f"Added {new_results} new results. {session.max_queries - len(session.queries_executed)} queries remaining."
            }

        except Exception as e:
            logger.error(f"Failed to expand research: {e}")
            return {"error": str(e), "success": False}

    async def _handle_synthesize(
        self,
        session_id: str,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Handle synthesizing research findings."""
        try:
            if session_id not in self._sessions:
                return {"error": f"Session {session_id} not found", "success": False}

            session = self._sessions[session_id]

            if not session.results:
                return {
                    "success": False,
                    "error": "No results to synthesize"
                }

            # Prepare results for Claude
            results_text = "\n\n".join([
                f"**Source {i+1}:** {r.title}\n"
                f"URL: {r.url}\n"
                f"Type: {r.source_type} (Credibility: {r.credibility})\n"
                f"Content: {r.snippet}"
                for i, r in enumerate(session.results[:20])  # Limit to 20 for context
            ])

            focus_text = f"Focus areas: {', '.join(focus_areas)}" if focus_areas else "Provide comprehensive synthesis"

            # Use Claude to synthesize
            chat_model = self._get_chat_model()

            prompt = f"""Synthesize the following research findings about "{session.topic}".

## Research Results
{results_text}

## Task
{focus_text}

Create a comprehensive synthesis that:
1. Identifies key facts and findings
2. Notes source credibility for each claim
3. Highlights contradictions or gaps
4. Provides citations for all claims

Output as JSON:
```json
{{
    "summary": "<2-3 paragraph synthesis>",
    "key_findings": [
        {{
            "finding": "<finding>",
            "source_count": <number>,
            "credibility": "<high|medium|low>",
            "citations": ["<source 1>", "<source 2>"]
        }}
    ],
    "contradictions": ["<any contradictions found>"],
    "gaps": ["<what needs more research>"],
    "confidence": "<high|medium|low>"
}}
```"""

            response = await chat_model.chat(
                message=prompt,
                system_prompt="You are a research analyst. Synthesize findings objectively with citations. Respond only with valid JSON."
            )

            if not response.get("success"):
                return {
                    "success": False,
                    "error": response.get("error", "Synthesis failed")
                }

            session.status = "completed"

            return {
                "success": True,
                "session_id": session_id,
                "synthesis": response.get("response", ""),
                "sources_analyzed": len(session.results),
                "queries_executed": len(session.queries_executed),
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"Failed to synthesize: {e}")
            return {"error": str(e), "success": False}

    async def _handle_get_source_graph(self, session_id: str) -> Dict[str, Any]:
        """Handle getting source relationship graph."""
        try:
            if session_id not in self._sessions:
                return {"error": f"Session {session_id} not found", "success": False}

            session = self._sessions[session_id]

            # Build source graph
            sources_by_type = {}
            sources_by_credibility = {"high": [], "medium": [], "low": [], "unknown": []}

            for r in session.results:
                # Group by type
                if r.source_type not in sources_by_type:
                    sources_by_type[r.source_type] = []
                sources_by_type[r.source_type].append({
                    "title": r.title,
                    "url": r.url
                })

                # Group by credibility
                sources_by_credibility[r.credibility].append(r.url)

            return {
                "success": True,
                "session_id": session_id,
                "topic": session.topic,
                "source_graph": {
                    "by_type": {k: len(v) for k, v in sources_by_type.items()},
                    "by_credibility": {k: len(v) for k, v in sources_by_credibility.items()},
                    "total_sources": len(session.results),
                    "unique_domains": len(set(r.url.split('/')[2] if '/' in r.url else r.url for r in session.results))
                },
                "detailed_by_type": sources_by_type
            }

        except Exception as e:
            logger.error(f"Failed to get source graph: {e}")
            return {"error": str(e), "success": False}

    async def _handle_get_status(self, session_id: str) -> Dict[str, Any]:
        """Handle getting session status."""
        try:
            if session_id not in self._sessions:
                return {"error": f"Session {session_id} not found", "success": False}

            session = self._sessions[session_id]

            return {
                "success": True,
                "session": session.to_dict(),
                "results_preview": [r.to_dict() for r in session.results[:5]]
            }

        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {"error": str(e), "success": False}

    # Convenience methods for direct workflow integration
    async def start_research(
        self,
        topic: str,
        depth: str = "standard",
        max_queries: int = 10,
        research_mode: str = "general"
    ) -> Dict[str, Any]:
        """
        Convenience method to start a research session.
        Wraps _handle_start_research for direct workflow use.
        """
        return await self._handle_start_research(
            topic=topic,
            depth=depth,
            max_queries=max_queries,
            research_mode=research_mode
        )

    async def synthesize_findings(self, session_id: str) -> Dict[str, Any]:
        """
        Convenience method to synthesize research findings.
        Wraps _handle_synthesize for direct workflow use.
        """
        return await self._handle_synthesize(session_id=session_id)


# Singleton instance
_server_instance: Optional[DeepResearchMCPServer] = None


def get_deep_research_server() -> DeepResearchMCPServer:
    """Get or create the singleton server instance."""
    global _server_instance
    if _server_instance is None:
        _server_instance = DeepResearchMCPServer()
    return _server_instance
