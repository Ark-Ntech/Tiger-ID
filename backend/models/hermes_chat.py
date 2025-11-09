"""OpenAI-powered chat orchestrator with native tool calling support."""

import json
from typing import Optional, List, Dict, Any

import openai
from openai import OpenAI

from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)


class HermesChatModel:
    """Chat orchestrator backed by OpenAI's chat completions API."""

    def __init__(self):
        """Initialize OpenAI client using application settings."""
        self.settings = get_settings()
        openai_settings = getattr(self.settings, "openai", None)

        if openai_settings is None or not getattr(openai_settings, "api_key", None):
            raise ValueError("OpenAI API key is not configured. Set OPENAI_API_KEY.")

        self.client = OpenAI(api_key=openai_settings.api_key)
        self.model_name = openai_settings.model
        self.default_max_tokens = openai_settings.max_tokens
        self.default_temperature = openai_settings.temperature

        logger.info(
            "HermesChatModel initialized with OpenAI model '%s'",
            self.model_name,
        )

    async def chat(
        self,
        message: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Chat with OpenAI model with optional tool calling support.

        Args:
            message: User message
            tools: Optional list of available tools for calling
            conversation_history: Previous messages
            max_tokens: Maximum tokens to generate (falls back to settings)
            temperature: Sampling temperature (falls back to settings)

        Returns:
            Dictionary with response, tool_calls, and success status
        """
        logger.info("OpenAI chat request: %s...", message[:50])
        try:
            openai_tools = self._convert_tools(tools)
            messages = self._build_messages(message, conversation_history, tools)
            
            # Determine which parameters to use based on model
            # GPT-4o and newer use max_completion_tokens, older models use max_tokens
            # GPT-5 and o1 models only support temperature=1.0 (default)
            api_params = {}
            token_limit = max_tokens if max_tokens is not None else self.default_max_tokens
            temp = temperature if temperature is not None else self.default_temperature
            
            if "gpt-4o" in self.model_name or "gpt-5" in self.model_name or "o1" in self.model_name:
                api_params["max_completion_tokens"] = token_limit
                # o1 and GPT-5 models only support temperature=1.0
                if "o1" not in self.model_name and "gpt-5" not in self.model_name:
                    api_params["temperature"] = temp
            else:
                api_params["max_tokens"] = token_limit
                api_params["temperature"] = temp
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **api_params,
                tools=openai_tools if openai_tools else None,
            )

            choice = completion.choices[0]
            response_message = choice.message
            response_text = self._extract_message_content(response_message.content)
            tool_calls = self._parse_tool_calls(response_message.tool_calls)

            logger.info("Chat completed successfully")
            if tool_calls:
                logger.info("Model requested %d tool calls", len(tool_calls))

            return {
                "response": response_text,
                "tool_calls": tool_calls,
                "success": True,
                "model": completion.model or self.model_name,
            }

        except openai.OpenAIError as e:
            error_type = type(e).__name__
            logger.error("OpenAI chat error (%s): %s", error_type, e, exc_info=True)
            raise RuntimeError(f"OpenAI chat error ({error_type}): {str(e)}") from e
        except RuntimeError:
            raise
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                "Unexpected error in OpenAI chat (%s): %s", error_type, e, exc_info=True
            )
            raise RuntimeError(f"OpenAI chat error ({error_type}): {str(e)}") from e

    def _build_messages(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]],
        tools: Optional[List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Construct the message list for OpenAI chat completions."""
        messages: List[Dict[str, Any]] = []

        if history:
            messages.extend(history)

        if tools:
            tool_desc = "\n".join(
                f"- {tool.get('name')}: {tool.get('description', '')}"
                for tool in tools[:20]
                if tool.get("name")
            )
            system_content = (
                "You are an AI assistant for tiger conservation."
            )
            if tool_desc:
                system_content += f" Tools: {tool_desc}"
            system_content += (
                '. Use JSON for tool calls in the format '
                '{"tool_call": {"name": "x", "arguments": {}}}'
            )
            messages.insert(
                0,
                {
                    "role": "system",
                    "content": system_content,
                },
            )

        messages.append({"role": "user", "content": user_message})
        return messages

    @staticmethod
    def _convert_tools(tools: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Convert tool schema to OpenAI function-calling format."""
        if not tools:
            return []

        converted_tools: List[Dict[str, Any]] = []
        for tool in tools:
            name = tool.get("name")
            if not name:
                continue

            description = tool.get("description", "") or "No description provided."
            parameters = tool.get("parameters") or tool.get("inputSchema") or {}
            if not isinstance(parameters, dict) or not parameters:
                parameters = {"type": "object", "properties": {}}

            if "type" not in parameters:
                parameters["type"] = "object"

            converted_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": parameters,
                    },
                }
            )

        return converted_tools

    @staticmethod
    def _extract_message_content(content: Any) -> str:
        """Extract textual response content from OpenAI message."""
        if not content:
            return ""

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_segments = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_segments.append(part.get("text", ""))
            return "".join(text_segments).strip()

        return str(content)

    @staticmethod
    def _parse_tool_calls(tool_calls: Optional[List[Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI tool call structures to internal representation."""
        if not tool_calls:
            return []

        parsed_calls: List[Dict[str, Any]] = []
        for call in tool_calls:
            function_call = getattr(call, "function", None)
            if function_call is None and isinstance(call, dict):
                function_call = call.get("function", {})
            arguments = getattr(function_call, "arguments", None)
            if arguments is None and isinstance(function_call, dict):
                arguments = function_call.get("arguments", {})
            name = getattr(function_call, "name", None)
            if name is None and isinstance(function_call, dict):
                name = function_call.get("name")

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {"raw": arguments}

            if name:
                parsed_calls.append(
                    {
                        "name": name,
                        "arguments": arguments if isinstance(arguments, dict) else {},
                    }
                )

        return parsed_calls


# Singleton instance
_hermes_model: Optional[HermesChatModel] = None


def get_hermes_chat_model() -> HermesChatModel:
    """Get global Hermes chat model instance (singleton)."""
    global _hermes_model
    if _hermes_model is None:
        _hermes_model = HermesChatModel()
    return _hermes_model

