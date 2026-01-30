"""Google Gemini-powered chat orchestrator with native tool calling and Search Grounding.

DEPRECATED: This module is deprecated in favor of anthropic_chat.py.
The system now uses Anthropic Claude API for chat orchestration.
This file is kept for fallback compatibility only.
"""

import warnings
warnings.warn(
    "gemini_chat module is deprecated. Use anthropic_chat instead.",
    DeprecationWarning,
    stacklevel=2
)

from google import genai
from google.genai import types
from typing import Optional, List, Dict, Any
from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)


class GeminiChatModel:
    """Chat orchestrator backed by Google Gemini API"""

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initialize Gemini client

        Args:
            model_name: Model to use (gemini-2.5-flash, gemini-2.5-pro, etc.)
        """
        self.settings = get_settings()
        gemini_settings = getattr(self.settings, "gemini", None)

        if not gemini_settings or not gemini_settings.api_key:
            raise ValueError("Gemini API key not configured. Set GEMINI_API_KEY environment variable.")

        # Initialize the client
        self.client = genai.Client(api_key=gemini_settings.api_key)
        self.model_name = model_name

        logger.info(f"GeminiChatModel initialized with model '{model_name}'")

    async def chat(
        self,
        message: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        enable_search_grounding: bool = False,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Chat with Gemini model with optional tool calling and Search Grounding

        Args:
            message: User message
            tools: Optional list of tools (Gemini format)
            enable_search_grounding: Enable Google Search Grounding
            conversation_history: Previous messages
            max_tokens: Max completion tokens
            temperature: Sampling temperature
            response_schema: JSON schema for structured output

        Returns:
            Dictionary with response, tool_calls, citations, and success status
        """
        try:
            logger.info(f"[GEMINI] Chat request with model {self.model_name}")
            logger.info(f"[GEMINI] Message: {message[:100]}...")
            logger.info(f"[GEMINI] Search Grounding: {enable_search_grounding}")

            # Prepare tool configuration
            tool_list = []
            if enable_search_grounding:
                # Use GoogleSearch tool for Search Grounding
                tool_list.append(types.Tool(google_search=types.GoogleSearch()))
                logger.info("[GEMINI] Enabled Search Grounding")
            elif tools:
                # Convert MCP tool format to Gemini function calling format
                tool_config = self._convert_tools_to_gemini(tools)
                tool_list.append(tool_config)
                logger.info(f"[GEMINI] Enabled {len(tools)} function calling tools")

            # Build generation config (including tools)
            config = types.GenerateContentConfig()
            if max_tokens:
                config.max_output_tokens = max_tokens
            if temperature is not None:
                config.temperature = temperature
            if response_schema:
                config.response_mime_type = "application/json"
                config.response_schema = response_schema
            if tool_list:
                config.tools = tool_list

            # Generate response
            logger.info("[GEMINI] Generating content...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=message,
                config=config
            )

            # Extract response text
            response_text = response.text if hasattr(response, 'text') else ''
            logger.info(f"[GEMINI] Response generated: {len(response_text)} chars")

            # Extract tool calls (if any)
            tool_calls = self._parse_gemini_tool_calls(response)
            if tool_calls:
                logger.info(f"[GEMINI] Model requested {len(tool_calls)} tool calls")

            # Extract grounding metadata (citations from Search Grounding)
            citations = self._extract_grounding_metadata(response)
            if citations:
                logger.info(f"[GEMINI] Found {len(citations)} citations from Search Grounding")

            return {
                "response": response_text,
                "tool_calls": tool_calls,
                "citations": citations,
                "success": True,
                "model": self.model_name
            }

        except Exception as e:
            logger.error(f"[GEMINI] Chat error: {e}", exc_info=True)
            return {
                "response": "",
                "tool_calls": [],
                "citations": [],
                "success": False,
                "error": str(e),
                "model": self.model_name
            }

    def _convert_tools_to_gemini(self, tools: List[Dict[str, Any]]) -> types.Tool:
        """Convert MCP tool schema to Gemini function calling format"""
        function_declarations = []

        for tool in tools:
            func_decl = types.FunctionDeclaration(
                name=tool.get("name", "unknown"),
                description=tool.get("description", ""),
                parameters=tool.get("parameters", {})
            )
            function_declarations.append(func_decl)

        # Create a Tool with all function declarations
        return types.Tool(function_declarations=function_declarations)

    def _parse_gemini_tool_calls(self, response) -> List[Dict[str, Any]]:
        """Extract tool calls from Gemini response"""
        tool_calls = []

        if not hasattr(response, 'candidates'):
            return tool_calls

        for candidate in response.candidates:
            if not hasattr(candidate, 'content'):
                continue
            if not hasattr(candidate.content, 'parts'):
                continue

            for part in candidate.content.parts:
                if hasattr(part, 'function_call') and part.function_call is not None:
                    fc = part.function_call
                    # Check if name exists before accessing
                    if hasattr(fc, 'name') and fc.name:
                        tool_calls.append({
                            "name": fc.name,
                            "arguments": dict(fc.args) if hasattr(fc, 'args') and fc.args else {}
                        })

        return tool_calls

    def _extract_grounding_metadata(self, response) -> List[Dict[str, Any]]:
        """Extract citations and sources from Search Grounding"""
        citations = []

        if not hasattr(response, 'candidates'):
            logger.warning("[GEMINI] Response has no candidates attribute")
            return citations

        for candidate in response.candidates:
            if not hasattr(candidate, 'grounding_metadata'):
                continue

            metadata = candidate.grounding_metadata
            if metadata is None:
                continue

            # Extract grounding chunks (the actual sources)
            if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                logger.info(f"[GEMINI] Found {len(metadata.grounding_chunks)} grounding chunks")
                for chunk in metadata.grounding_chunks:
                    if hasattr(chunk, 'web') and chunk.web:
                        citation = {
                            "uri": chunk.web.uri if hasattr(chunk.web, 'uri') else '',
                            "title": chunk.web.title if hasattr(chunk.web, 'title') else ''
                        }
                        citations.append(citation)

            # Also try to extract from grounding_supports (alternative field)
            if hasattr(metadata, 'grounding_supports') and metadata.grounding_supports:
                logger.info(f"[GEMINI] Found {len(metadata.grounding_supports)} grounding supports")
                for support in metadata.grounding_supports:
                    if hasattr(support, 'source') and support.source:
                        citation = {
                            "uri": support.source.uri if hasattr(support.source, 'uri') else '',
                            "title": support.source.display_name if hasattr(support.source, 'display_name') else ''
                        }
                        citations.append(citation)
                        logger.info(f"[GEMINI] Extracted support citation: {citation.get('title', 'no title')[:50]}...")

        # Remove duplicates
        seen = set()
        unique_citations = []
        for cite in citations:
            uri = cite.get("uri", "")
            if uri and uri not in seen:
                seen.add(uri)
                unique_citations.append(cite)

        logger.info(f"[GEMINI] Total unique citations extracted: {len(unique_citations)}")
        return unique_citations


# Singleton instances for both models
_gemini_flash_model: Optional[GeminiChatModel] = None
_gemini_pro_model: Optional[GeminiChatModel] = None


def get_gemini_flash_model() -> GeminiChatModel:
    """Get global Gemini Flash model instance (fast, for orchestration)"""
    global _gemini_flash_model
    if _gemini_flash_model is None:
        _gemini_flash_model = GeminiChatModel(model_name="gemini-2.5-flash")
    return _gemini_flash_model


def get_gemini_pro_model() -> GeminiChatModel:
    """Get global Gemini Pro model instance (high-quality, for analysis)"""
    global _gemini_pro_model
    if _gemini_pro_model is None:
        _gemini_pro_model = GeminiChatModel(model_name="gemini-2.5-pro")
    return _gemini_pro_model
