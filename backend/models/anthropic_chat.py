"""Anthropic Claude-powered chat orchestrator with native tool calling and web search."""

import anthropic
from typing import Optional, List, Dict, Any
from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)


class AnthropicChatModel:
    """Chat orchestrator backed by Anthropic Claude API"""

    def __init__(self, model_name: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize Anthropic client

        Args:
            model_name: Model to use (claude-sonnet-4-5-20250929, claude-opus-4-5-20251101, etc.)
        """
        self.settings = get_settings()
        anthropic_settings = getattr(self.settings, "anthropic", None)

        if not anthropic_settings or not anthropic_settings.api_key:
            raise ValueError("Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable.")

        # Initialize the async client
        self.client = anthropic.AsyncAnthropic(api_key=anthropic_settings.api_key)
        self.model_name = model_name
        self.default_max_tokens = anthropic_settings.max_tokens
        self.default_temperature = anthropic_settings.temperature

        logger.info(f"AnthropicChatModel initialized with model '{model_name}'")

    async def chat(
        self,
        message: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        enable_web_search: bool = False,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chat with Claude model with optional tool calling and web search

        Args:
            message: User message
            tools: Optional list of tools (will be converted to Anthropic format)
            enable_web_search: Enable web search via Firecrawl MCP
            conversation_history: Previous messages
            max_tokens: Max completion tokens
            temperature: Sampling temperature
            system_prompt: Optional system prompt

        Returns:
            Dictionary with response, tool_calls, citations, and success status
        """
        try:
            logger.info(f"[ANTHROPIC] Chat request with model {self.model_name}")
            logger.info(f"[ANTHROPIC] Message: {message[:100]}...")
            logger.info(f"[ANTHROPIC] Web search: {enable_web_search}")

            # Build messages list
            messages = []

            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role in ["user", "assistant"]:
                        messages.append({"role": role, "content": content})

            # Add current message
            messages.append({"role": "user", "content": message})

            # Prepare tool configuration
            tool_list = []
            if enable_web_search:
                # Add web search tool for Search Grounding replacement
                tool_list.append(self._get_web_search_tool())
                logger.info("[ANTHROPIC] Enabled web search tool")

            if tools:
                # Convert MCP tool format to Anthropic format
                converted_tools = self._convert_tools_to_anthropic(tools)
                tool_list.extend(converted_tools)
                logger.info(f"[ANTHROPIC] Enabled {len(tools)} custom tools")

            # Build request kwargs
            request_kwargs = {
                "model": self.model_name,
                "max_tokens": max_tokens or self.default_max_tokens,
                "messages": messages
            }

            if temperature is not None:
                request_kwargs["temperature"] = temperature
            elif self.default_temperature is not None:
                request_kwargs["temperature"] = self.default_temperature

            if system_prompt:
                request_kwargs["system"] = system_prompt

            if tool_list:
                request_kwargs["tools"] = tool_list

            # Generate response
            logger.info("[ANTHROPIC] Generating content...")
            response = await self.client.messages.create(**request_kwargs)

            # Extract response text and tool calls
            response_text = ""
            tool_calls = []

            for content_block in response.content:
                if content_block.type == "text":
                    response_text += content_block.text
                elif content_block.type == "tool_use":
                    tool_calls.append({
                        "id": content_block.id,
                        "name": content_block.name,
                        "arguments": content_block.input
                    })

            logger.info(f"[ANTHROPIC] Response generated: {len(response_text)} chars")

            # Handle web search tool calls if enabled
            citations = []
            if enable_web_search and tool_calls:
                # Execute web search tools and get citations
                search_results = await self._execute_web_search_tools(tool_calls)
                citations = search_results.get("citations", [])

                # If we got search results, make a follow-up call with results
                if search_results.get("results"):
                    response_text, citations = await self._synthesize_with_search_results(
                        messages, tool_calls, search_results, request_kwargs
                    )
                    tool_calls = []  # Clear tool calls since we've handled them

            if tool_calls:
                logger.info(f"[ANTHROPIC] Model requested {len(tool_calls)} tool calls")

            if citations:
                logger.info(f"[ANTHROPIC] Found {len(citations)} citations from web search")

            return {
                "response": response_text,
                "tool_calls": tool_calls,
                "citations": citations,
                "success": True,
                "model": self.model_name
            }

        except Exception as e:
            logger.error(f"[ANTHROPIC] Chat error: {e}", exc_info=True)
            return {
                "response": "",
                "tool_calls": [],
                "citations": [],
                "success": False,
                "error": str(e),
                "model": self.model_name
            }

    def _convert_tools_to_anthropic(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert MCP tool schema to Anthropic tool format"""
        anthropic_tools = []

        for tool in tools:
            anthropic_tool = {
                "name": tool.get("name", "unknown"),
                "description": tool.get("description", ""),
                "input_schema": tool.get("parameters", {"type": "object", "properties": {}})
            }
            anthropic_tools.append(anthropic_tool)

        return anthropic_tools

    def _get_web_search_tool(self) -> Dict[str, Any]:
        """Get web search tool definition for Search Grounding replacement"""
        return {
            "name": "web_search",
            "description": "Search the web for current information. Use this to find recent news, facts, and data.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to execute"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }

    async def _execute_web_search_tools(self, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute web search tool calls using Firecrawl MCP"""
        results = []
        citations = []

        for tool_call in tool_calls:
            if tool_call.get("name") == "web_search":
                query = tool_call.get("arguments", {}).get("query", "")
                num_results = tool_call.get("arguments", {}).get("num_results", 5)

                if query:
                    try:
                        search_result = await self._firecrawl_search(query, num_results)
                        results.append({
                            "tool_call_id": tool_call.get("id"),
                            "query": query,
                            "results": search_result.get("results", [])
                        })

                        # Extract citations from search results
                        for result in search_result.get("results", []):
                            citations.append({
                                "uri": result.get("url", ""),
                                "title": result.get("title", ""),
                                "snippet": result.get("description", "")
                            })

                    except Exception as e:
                        logger.warning(f"[ANTHROPIC] Web search failed for '{query}': {e}")
                        results.append({
                            "tool_call_id": tool_call.get("id"),
                            "query": query,
                            "error": str(e)
                        })

        return {"results": results, "citations": citations}

    async def _try_duckduckgo(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Free web search using DuckDuckGo (no API key required)"""
        try:
            from ddgs import DDGS

            results = []
            ddgs = DDGS()
            for r in ddgs.text(query, max_results=num_results):
                results.append({
                    "url": r.get("href", ""),
                    "title": r.get("title", ""),
                    "description": r.get("body", "")
                })

            logger.info(f"[ANTHROPIC] DuckDuckGo returned {len(results)} results for '{query}'")
            return {"results": results, "provider": "duckduckgo"}

        except Exception as e:
            logger.error(f"[ANTHROPIC] DuckDuckGo search error: {e}")
            return {"results": [], "provider": "duckduckgo", "error": str(e)}

    async def _firecrawl_search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Execute search with fallback providers: DuckDuckGo (free) -> Firecrawl"""
        # Try DuckDuckGo first (free, no API key required)
        result = await self._try_duckduckgo(query, num_results)
        if result.get("results"):
            return result

        # Fallback to Firecrawl if DuckDuckGo fails
        logger.info("[ANTHROPIC] DuckDuckGo returned no results, trying Firecrawl fallback...")
        result = await self._try_firecrawl(query, num_results)
        if result.get("results"):
            return result

        # All providers failed
        logger.warning("[ANTHROPIC] All search providers failed or returned no results")
        return {"results": [], "error": "All search providers failed", "providers_tried": ["duckduckgo", "firecrawl"]}

    async def _try_firecrawl(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Try Firecrawl search provider"""
        try:
            from firecrawl import FirecrawlApp

            firecrawl_settings = getattr(self.settings, "firecrawl", None)
            if not firecrawl_settings or not firecrawl_settings.api_key:
                logger.warning("[ANTHROPIC] Firecrawl API key not configured")
                return {"results": [], "provider": "firecrawl", "error": "API key not configured"}

            app = FirecrawlApp(api_key=firecrawl_settings.api_key)

            # Execute search - Firecrawl API may vary, try different parameter formats
            try:
                search_results = app.search(query, limit=num_results)
            except TypeError:
                # Fallback for different API versions
                search_results = app.search(query)

            # Format results
            formatted_results = []
            if isinstance(search_results, list):
                for result in search_results[:num_results]:
                    formatted_results.append({
                        "url": result.get("url", ""),
                        "title": result.get("title", ""),
                        "description": result.get("description", result.get("content", "")[:500])
                    })
            elif isinstance(search_results, dict) and "data" in search_results:
                for result in search_results["data"][:num_results]:
                    formatted_results.append({
                        "url": result.get("url", ""),
                        "title": result.get("title", ""),
                        "description": result.get("description", result.get("content", "")[:500])
                    })

            logger.info(f"[ANTHROPIC] Firecrawl returned {len(formatted_results)} results for '{query}'")
            return {"results": formatted_results, "provider": "firecrawl"}

        except Exception as e:
            logger.error(f"[ANTHROPIC] Firecrawl search error: {e}")
            return {"results": [], "provider": "firecrawl", "error": str(e)}

    async def _synthesize_with_search_results(
        self,
        original_messages: List[Dict],
        tool_calls: List[Dict],
        search_results: Dict[str, Any],
        original_kwargs: Dict
    ) -> tuple:
        """Make follow-up call with search results to synthesize response"""
        try:
            # Build tool results
            tool_results = []
            for result in search_results.get("results", []):
                tool_result_content = ""
                if result.get("error"):
                    tool_result_content = f"Search failed: {result['error']}"
                else:
                    # Format search results as readable text
                    search_items = result.get("results", [])
                    tool_result_content = f"Search results for '{result['query']}':\n\n"
                    for i, item in enumerate(search_items, 1):
                        tool_result_content += f"{i}. {item.get('title', 'No title')}\n"
                        tool_result_content += f"   URL: {item.get('url', '')}\n"
                        tool_result_content += f"   {item.get('description', '')}\n\n"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": result.get("tool_call_id"),
                    "content": tool_result_content
                })

            # Build messages with tool results
            messages = original_messages.copy()

            # Add assistant message with tool use
            assistant_content = []
            for tc in tool_calls:
                if tc.get("name") == "web_search":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": tc.get("id"),
                        "name": "web_search",
                        "input": tc.get("arguments", {})
                    })

            if assistant_content:
                messages.append({"role": "assistant", "content": assistant_content})

            # Add tool results as user message
            if tool_results:
                messages.append({"role": "user", "content": tool_results})

            # Make follow-up call without tools
            follow_up_kwargs = {
                "model": self.model_name,
                "max_tokens": original_kwargs.get("max_tokens", self.default_max_tokens),
                "messages": messages
            }

            if original_kwargs.get("temperature"):
                follow_up_kwargs["temperature"] = original_kwargs["temperature"]
            if original_kwargs.get("system"):
                follow_up_kwargs["system"] = original_kwargs["system"]

            logger.info("[ANTHROPIC] Making follow-up call with search results...")
            response = await self.client.messages.create(**follow_up_kwargs)

            # Extract response text
            response_text = ""
            for content_block in response.content:
                if content_block.type == "text":
                    response_text += content_block.text

            return response_text, search_results.get("citations", [])

        except Exception as e:
            logger.error(f"[ANTHROPIC] Error synthesizing with search results: {e}")
            # Return original results if synthesis fails
            return "", search_results.get("citations", [])


# Singleton instances for both models
_anthropic_fast_model: Optional[AnthropicChatModel] = None
_anthropic_quality_model: Optional[AnthropicChatModel] = None


def get_anthropic_fast_model() -> AnthropicChatModel:
    """Get global Anthropic fast model instance (Sonnet, for orchestration)"""
    global _anthropic_fast_model
    if _anthropic_fast_model is None:
        settings = get_settings()
        model_name = settings.anthropic.fast_model if settings.anthropic else "claude-sonnet-4-5-20250929"
        _anthropic_fast_model = AnthropicChatModel(model_name=model_name)
    return _anthropic_fast_model


def get_anthropic_quality_model() -> AnthropicChatModel:
    """Get global Anthropic quality model instance (Opus, for high-quality analysis)"""
    global _anthropic_quality_model
    if _anthropic_quality_model is None:
        settings = get_settings()
        model_name = settings.anthropic.quality_model if settings.anthropic else "claude-opus-4-5-20251101"
        _anthropic_quality_model = AnthropicChatModel(model_name=model_name)
    return _anthropic_quality_model
