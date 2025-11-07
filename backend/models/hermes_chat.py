"""
Hermes-3-Llama-3.1-8B chat orchestrator using Modal.

This module provides chat orchestration with native tool calling.
"""

from typing import Optional, List, Dict, Any

from backend.utils.logging import get_logger
from backend.services.modal_client import get_modal_client
from backend.config.settings import get_settings

logger = get_logger(__name__)


class HermesChatModel:
    """Hermes-3 chat orchestrator using Modal backend"""
    
    def __init__(self):
        """Initialize Hermes chat model with Modal backend."""
        self.settings = get_settings()
        self.modal_client = get_modal_client()
        
        logger.info("HermesChatModel initialized with Modal backend")
    
    async def chat(
        self,
        message: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Chat with Hermes-3 model with tool calling support.
        
        Args:
            message: User message
            tools: Optional list of available tools for calling
            conversation_history: Previous messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Dictionary with response, tool_calls, and success status
        """
        try:
            logger.info(f"Hermes chat: {message[:50]}...")
            if tools:
                logger.info(f"Providing {len(tools)} tools to Hermes for calling")
            
            # Call Modal service
            result = await self.modal_client.hermes_chat(
                message,
                tools,
                conversation_history,
                max_tokens,
                temperature
            )
            
            if result.get("success"):
                logger.info("Chat completed successfully")
                if result.get("tool_calls"):
                    logger.info(f"Model requested {len(result['tool_calls'])} tool calls")
                return result
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"Chat failed: {error_msg}")
                
                # Check if request was queued
                if result.get("queued"):
                    logger.warning("Chat request queued for later processing")
                    return result
                
                raise RuntimeError(f"Hermes chat failed: {error_msg}")
            
        except RuntimeError:
            # Re-raise RuntimeError as-is
            raise
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Error in Hermes chat ({error_type}): {e}", exc_info=True)
            raise RuntimeError(f"Hermes chat error ({error_type}): {str(e)}")


# Singleton instance
_hermes_model: Optional[HermesChatModel] = None


def get_hermes_chat_model() -> HermesChatModel:
    """Get global Hermes chat model instance (singleton)"""
    global _hermes_model
    if _hermes_model is None:
        _hermes_model = HermesChatModel()
    return _hermes_model

