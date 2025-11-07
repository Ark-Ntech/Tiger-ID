"""
Modal client service for communicating with Modal inference functions.

This service handles:
- Communication with Modal endpoints
- Request queueing and retry logic
- Fallback handling when Modal is unavailable
- Caching and error handling
"""

import asyncio
import io
from typing import Optional, Dict, Any, List
from pathlib import Path
import numpy as np
from PIL import Image

from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ModalClientError(Exception):
    """Base exception for Modal client errors."""
    pass


class ModalUnavailableError(ModalClientError):
    """Raised when Modal service is unavailable."""
    pass


class ModalClient:
    """Client for communicating with Modal ML inference services."""
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 120,
        queue_max_size: int = 100
    ):
        """
        Initialize Modal client.
        
        Args:
            max_retries: Maximum number of retries for failed requests
            retry_delay: Initial delay between retries (exponential backoff)
            timeout: Request timeout in seconds
            queue_max_size: Maximum size of request queue
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.queue_max_size = queue_max_size
        
        # Request queue for handling Modal unavailability
        self.request_queue = asyncio.Queue(maxsize=queue_max_size)
        
        # Modal function references (lazy loaded)
        self._tiger_reid = None
        self._megadetector = None
        self._wildlife_tools = None
        self._rapid_reid = None
        self._cvwc2019_reid = None
        self._omnivinci = None
        self._hermes_chat = None
        
        # Stats
        self.stats = {
            "requests_sent": 0,
            "requests_succeeded": 0,
            "requests_failed": 0,
            "requests_queued": 0,
        }
    
    def _get_modal_function(self, model_name: str):
        """
        Lazy load Modal function reference from deployed app.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Modal function reference
        """
        try:
            import modal
            
            # Map model names to class names  
            class_map = {
                "tiger_reid": "TigerReIDModel",
                "megadetector": "MegaDetectorModel",
                "wildlife_tools": "WildlifeToolsModel",
                "rapid_reid": "RAPIDReIDModel",
                "cvwc2019_reid": "CVWC2019ReIDModel",
                "omnivinci": "OmniVinciModel",
                "hermes_chat": "HermesChatModel"
            }
            
            if model_name not in class_map:
                raise ValueError(f"Unknown model: {model_name}")
            
            class_name = class_map[model_name]
            
            # Cache attribute name
            cache_attr = f"_{model_name}"
            
            # Return cached instance if available
            if getattr(self, cache_attr, None) is not None:
                return getattr(self, cache_attr)
            
            # Get the deployed class using Cls.from_name()
            # This references the actual deployed app on Modal
            try:
                model_cls = modal.Cls.from_name("tiger-id-models", class_name)
                setattr(self, cache_attr, model_cls())
                return getattr(self, cache_attr)
            except Exception as e:
                logger.error(f"Could not get deployed class {class_name}: {e}")
                raise
                
        except modal.exception.NotFoundError as e:
            logger.error(f"Modal app 'tiger-id-models' or class '{class_name}' not found: {e}")
            raise ModalUnavailableError("Modal app or model not deployed")
        except ImportError as e:
            logger.error(f"Modal module not found: {e}")
            raise ModalUnavailableError("Modal not installed")
        except Exception as e:
            logger.error(f"Failed to get Modal function: {e}")
            raise ModalUnavailableError(f"Failed to connect to Modal: {e}")
    
    async def _call_with_retry(
        self,
        func,
        *args,
        **kwargs
    ) -> Any:
        """
        Call Modal function with retry logic.
        
        Args:
            func: Modal function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self.stats["requests_sent"] += 1
                
                # Call Modal function with timeout
                result = await asyncio.wait_for(
                    func.remote.aio(*args, **kwargs),
                    timeout=self.timeout
                )
                
                self.stats["requests_succeeded"] += 1
                return result
                
            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(f"Request timeout on attempt {attempt + 1}/{self.max_retries}")
                
            except Exception as e:
                last_error = e
                logger.warning(f"Request failed on attempt {attempt + 1}/{self.max_retries}: {e}")
            
            # Exponential backoff
            if attempt < self.max_retries - 1:
                delay = self.retry_delay * (2 ** attempt)
                await asyncio.sleep(delay)
        
        # All retries failed
        self.stats["requests_failed"] += 1
        raise ModalClientError(f"Request failed after {self.max_retries} attempts: {last_error}")
    
    async def _queue_request(
        self,
        model_name: str,
        method_name: str,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Queue request for later processing.
        
        Args:
            model_name: Name of the model
            method_name: Name of the method to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Status dictionary
        """
        try:
            request = {
                "model_name": model_name,
                "method_name": method_name,
                "args": args,
                "kwargs": kwargs
            }
            
            self.request_queue.put_nowait(request)
            self.stats["requests_queued"] += 1
            
            logger.info(f"Queued request for {model_name}.{method_name}")
            
            return {
                "success": False,
                "queued": True,
                "message": "Request queued for later processing",
                "queue_size": self.request_queue.qsize()
            }
            
        except asyncio.QueueFull:
            logger.error(f"Request queue is full (max: {self.queue_max_size})")
            raise ModalClientError("Request queue is full")
    
    # ==================== TigerReID Methods ====================
    
    async def tiger_reid_embedding(
        self,
        image: Image.Image,
        fallback_to_queue: bool = True
    ) -> Dict[str, Any]:
        """
        Generate tiger ReID embedding.
        
        Args:
            image: PIL Image
            fallback_to_queue: Whether to queue request if Modal unavailable
            
        Returns:
            Dictionary with embedding vector
        """
        try:
            # Convert image to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            
            # Get Modal function
            model = self._get_modal_function("tiger_reid")
            
            # Call with retry
            result = await self._call_with_retry(
                model.generate_embedding,
                image_bytes
            )
            
            return result
            
        except ModalUnavailableError as e:
            logger.error(f"Modal unavailable for TigerReID: {e}")
            
            if fallback_to_queue:
                return await self._queue_request(
                    "tiger_reid",
                    "generate_embedding",
                    image_bytes
                )
            else:
                raise
    
    # ==================== MegaDetector Methods ====================
    
    async def megadetector_detect(
        self,
        image: Image.Image,
        confidence_threshold: float = 0.5,
        fallback_to_queue: bool = True
    ) -> Dict[str, Any]:
        """
        Detect animals using MegaDetector.
        
        Args:
            image: PIL Image
            confidence_threshold: Detection confidence threshold
            fallback_to_queue: Whether to queue request if Modal unavailable
            
        Returns:
            Dictionary with detection results
        """
        try:
            # Convert image to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            
            # Get Modal function
            model = self._get_modal_function("megadetector")
            
            # Call with retry
            result = await self._call_with_retry(
                model.detect,
                image_bytes,
                confidence_threshold
            )
            
            return result
            
        except ModalUnavailableError as e:
            logger.error(f"Modal unavailable for MegaDetector: {e}")
            
            if fallback_to_queue:
                return await self._queue_request(
                    "megadetector",
                    "detect",
                    image_bytes,
                    confidence_threshold
                )
            else:
                raise
    
    # ==================== WildlifeTools Methods ====================
    
    async def wildlife_tools_embedding(
        self,
        image: Image.Image,
        fallback_to_queue: bool = True
    ) -> Dict[str, Any]:
        """
        Generate WildlifeTools embedding.
        
        Args:
            image: PIL Image
            fallback_to_queue: Whether to queue request if Modal unavailable
            
        Returns:
            Dictionary with embedding vector
        """
        try:
            # Convert image to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            
            # Get Modal function
            model = self._get_modal_function("wildlife_tools")
            
            # Call with retry
            result = await self._call_with_retry(
                model.generate_embedding,
                image_bytes
            )
            
            return result
            
        except ModalUnavailableError as e:
            logger.error(f"Modal unavailable for WildlifeTools: {e}")
            
            if fallback_to_queue:
                return await self._queue_request(
                    "wildlife_tools",
                    "generate_embedding",
                    image_bytes
                )
            else:
                raise
    
    # ==================== RAPID Methods ====================
    
    async def rapid_reid_embedding(
        self,
        image: Image.Image,
        fallback_to_queue: bool = True
    ) -> Dict[str, Any]:
        """
        Generate RAPID ReID embedding.
        
        Args:
            image: PIL Image
            fallback_to_queue: Whether to queue request if Modal unavailable
            
        Returns:
            Dictionary with embedding vector
        """
        try:
            # Convert image to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            
            # Get Modal function
            model = self._get_modal_function("rapid_reid")
            
            # Call with retry
            result = await self._call_with_retry(
                model.generate_embedding,
                image_bytes
            )
            
            return result
            
        except ModalUnavailableError as e:
            logger.error(f"Modal unavailable for RAPID ReID: {e}")
            
            if fallback_to_queue:
                return await self._queue_request(
                    "rapid_reid",
                    "generate_embedding",
                    image_bytes
                )
            else:
                raise
    
    # ==================== CVWC2019 Methods ====================
    
    async def cvwc2019_reid_embedding(
        self,
        image: Image.Image,
        fallback_to_queue: bool = True
    ) -> Dict[str, Any]:
        """
        Generate CVWC2019 ReID embedding.
        
        Args:
            image: PIL Image
            fallback_to_queue: Whether to queue request if Modal unavailable
            
        Returns:
            Dictionary with embedding vector
        """
        try:
            # Convert image to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            
            # Get Modal function
            model = self._get_modal_function("cvwc2019_reid")
            
            # Call with retry
            result = await self._call_with_retry(
                model.generate_embedding,
                image_bytes
            )
            
            return result
            
        except ModalUnavailableError as e:
            logger.error(f"Modal unavailable for CVWC2019 ReID: {e}")
            
            if fallback_to_queue:
                return await self._queue_request(
                    "cvwc2019_reid",
                    "generate_embedding",
                    image_bytes
                )
            else:
                raise
    
    # ==================== OmniVinci Methods ====================
    
    async def omnivinci_analyze_video(
        self,
        video_path: Path,
        prompt: str = "Analyze this video and describe what you see.",
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_callback_url: Optional[str] = None,
        fallback_to_queue: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze video using OmniVinci with optional agentic tool calling.
        
        Args:
            video_path: Path to video file
            prompt: Analysis prompt
            tools: Optional list of available tools for agentic calling
            tool_callback_url: Optional URL to call back for tool execution
            fallback_to_queue: Whether to queue request if Modal unavailable
            
        Returns:
            Dictionary with analysis results and any tool calls
        """
        try:
            # Read video bytes
            with open(video_path, 'rb') as f:
                video_bytes = f.read()
            
            # Get Modal function
            model = self._get_modal_function("omnivinci")
            
            # Call with retry, passing tools if provided
            result = await self._call_with_retry(
                model.analyze_video,
                video_bytes,
                prompt,
                tools,
                tool_callback_url
            )
            
            return result
            
        except ModalUnavailableError as e:
            logger.error(f"Modal unavailable for OmniVinci: {e}")
            
            if fallback_to_queue:
                return await self._queue_request(
                    "omnivinci",
                    "analyze_video",
                    video_bytes,
                    prompt
                )
            else:
                raise
    
    # ==================== Hermes Chat Methods ====================
    
    async def hermes_chat(
        self,
        message: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        fallback_to_queue: bool = True
    ) -> Dict[str, Any]:
        """
        Chat with Hermes-3 model with tool calling support.
        
        Args:
            message: User message
            tools: Optional list of available tools
            conversation_history: Previous messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            fallback_to_queue: Whether to queue request if Modal unavailable
            
        Returns:
            Dictionary with response, tool_calls, and success status
        """
        try:
            # Get Modal function
            model = self._get_modal_function("hermes_chat")
            
            # Call with retry
            result = await self._call_with_retry(
                model.chat,
                message,
                tools,
                conversation_history,
                max_tokens,
                temperature
            )
            
            return result
            
        except ModalUnavailableError as e:
            logger.error(f"Modal unavailable for Hermes chat: {e}")
            
            if fallback_to_queue:
                return await self._queue_request(
                    "hermes_chat",
                    "chat",
                    message,
                    tools,
                    conversation_history,
                    max_tokens,
                    temperature
                )
            else:
                raise
    
    # ==================== Queue Processing ====================
    
    async def process_queued_requests(self) -> Dict[str, Any]:
        """
        Process queued requests.
        
        Returns:
            Dictionary with processing statistics
        """
        processed = 0
        succeeded = 0
        failed = 0
        
        while not self.request_queue.empty():
            try:
                request = await self.request_queue.get()
                
                # Try to process request
                model = self._get_modal_function(request["model_name"])
                method = getattr(model, request["method_name"])
                
                await self._call_with_retry(
                    method,
                    *request["args"],
                    **request["kwargs"]
                )
                
                succeeded += 1
                
            except Exception as e:
                logger.error(f"Failed to process queued request: {e}")
                failed += 1
            
            finally:
                processed += 1
                self.request_queue.task_done()
        
        logger.info(f"Processed {processed} queued requests: {succeeded} succeeded, {failed} failed")
        
        return {
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get client statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            **self.stats,
            "queue_size": self.request_queue.qsize(),
            "queue_max_size": self.queue_max_size
        }


# Singleton instance
_modal_client = None


def get_modal_client() -> ModalClient:
    """
    Get singleton Modal client instance.
    
    Returns:
        ModalClient instance
    """
    global _modal_client
    
    if _modal_client is None:
        _modal_client = ModalClient()
    
    return _modal_client

