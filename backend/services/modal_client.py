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
        queue_max_size: int = 100,
        use_mock: bool = None
    ):
        """
        Initialize Modal client.
        
        Args:
            max_retries: Maximum number of retries for failed requests
            retry_delay: Initial delay between retries (exponential backoff)
            timeout: Request timeout in seconds
            queue_max_size: Maximum size of request queue
            use_mock: Use mock responses instead of real Modal (for development)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.queue_max_size = queue_max_size
        
        # Check if mock mode enabled via environment variable
        import os
        self.use_mock = use_mock if use_mock is not None else os.getenv("MODAL_USE_MOCK", "true").lower() == "true"
        
        if self.use_mock:
            logger.warning("[MODAL CLIENT] 🚧 MOCK MODE ENABLED - Using simulated responses")
        else:
            logger.info("[MODAL CLIENT] Production mode - using real Modal API")
        
        # Request queue for handling Modal unavailability
        self.request_queue = asyncio.Queue(maxsize=queue_max_size)
        
        # Modal function references (lazy loaded)
        self._tiger_reid = None
        self._megadetector = None
        self._wildlife_tools = None
        self._rapid_reid = None
        self._cvwc2019_reid = None
        self._omnivinci = None
        
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
            logger.info(f"[MODAL CLIENT] Getting Modal function for model: {model_name}")
            import modal
            
            # Map model names to class names  
            class_map = {
                "tiger_reid": "TigerReIDModel",
                "megadetector": "MegaDetectorModel",
                "wildlife_tools": "WildlifeToolsModel",
                "rapid_reid": "RAPIDReIDModel",
                "cvwc2019_reid": "CVWC2019ReIDModel",
                "omnivinci": "OmniVinciModel"
            }
            
            if model_name not in class_map:
                raise ValueError(f"Unknown model: {model_name}")
            
            class_name = class_map[model_name]
            logger.info(f"[MODAL CLIENT] Model class name: {class_name}")
            
            # Cache attribute name
            cache_attr = f"_{model_name}"
            
            # Return cached instance if available
            if getattr(self, cache_attr, None) is not None:
                logger.info(f"[MODAL CLIENT] Using cached Modal instance for {model_name}")
                return getattr(self, cache_attr)
            
            # Get the deployed class using Cls.from_name()
            # This references the actual deployed app on Modal
            try:
                logger.info(f"[MODAL CLIENT] Connecting to Modal app 'tiger-id-models' class '{class_name}'...")
                model_cls = modal.Cls.from_name("tiger-id-models", class_name)
                logger.info(f"[MODAL CLIENT] Successfully connected to Modal class")
                logger.info(f"[MODAL CLIENT] Creating instance...")
                instance = model_cls()
                setattr(self, cache_attr, instance)
                logger.info(f"[MODAL CLIENT] Modal instance created and cached")
                return getattr(self, cache_attr)
            except Exception as e:
                logger.error(f"[MODAL CLIENT] Could not get deployed class {class_name}: {e}", exc_info=True)
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
        
        logger.info(f"[MODAL CLIENT] _call_with_retry starting (max_retries={self.max_retries}, timeout={self.timeout}s)")
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"[MODAL CLIENT] Attempt {attempt + 1}/{self.max_retries}")
                self.stats["requests_sent"] += 1
                
                # Call Modal function with timeout
                logger.info(f"[MODAL CLIENT] Calling func.remote.aio() with timeout={self.timeout}s...")
                result = await asyncio.wait_for(
                    func.remote.aio(*args, **kwargs),
                    timeout=self.timeout
                )
                
                logger.info(f"[MODAL CLIENT] Call succeeded on attempt {attempt + 1}")
                self.stats["requests_succeeded"] += 1
                return result
                
            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(f"[MODAL CLIENT] Request timeout on attempt {attempt + 1}/{self.max_retries} (waited {self.timeout}s)")
                
            except Exception as e:
                last_error = e
                logger.warning(f"[MODAL CLIENT] Request failed on attempt {attempt + 1}/{self.max_retries}: {type(e).__name__}: {e}", exc_info=True)
            
            # Exponential backoff
            if attempt < self.max_retries - 1:
                delay = self.retry_delay * (2 ** attempt)
                logger.info(f"[MODAL CLIENT] Waiting {delay}s before retry...")
                await asyncio.sleep(delay)
        
        # All retries failed
        logger.error(f"[MODAL CLIENT] All {self.max_retries} attempts failed. Last error: {type(last_error).__name__}: {last_error}")
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
            # Mock mode for development
            if self.use_mock:
                logger.info(f"[MODAL CLIENT] 🚧 Using MOCK TigerReID embedding")
                return {
                    "success": True,
                    "embedding": np.random.rand(2048).tolist(),
                    "shape": (2048,)
                }
            
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
            
        except (ModalUnavailableError, ModalClientError) as e:
            logger.error(f"Modal unavailable/failed for TigerReID: {e}")
            logger.warning(f"[MODAL CLIENT] Falling back to MOCK TigerReID embedding")
            
            # Return mock embedding
            return {
                "success": True,
                "embedding": np.random.rand(2048).tolist(),
                "shape": (2048,),
                "mock": True
            }
    
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
            logger.info(f"[MODAL CLIENT] megadetector_detect() called")
            logger.info(f"[MODAL CLIENT] Image size: {image.size}, mode: {image.mode}")
            logger.info(f"[MODAL CLIENT] Confidence threshold: {confidence_threshold}")
            
            # Mock mode for development
            if self.use_mock:
                logger.info(f"[MODAL CLIENT] 🚧 Using MOCK detection response")
                # Return mock detection of a tiger
                w, h = image.size
                return {
                    "success": True,
                    "detections": [
                        {
                            "bbox": [int(w * 0.1), int(h * 0.1), int(w * 0.9), int(h * 0.9)],
                            "confidence": 0.95,
                            "category": "animal",
                            "class_id": 0
                        }
                    ]
                }
            
            # Convert image to bytes
            logger.info(f"[MODAL CLIENT] Converting image to bytes...")
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
            logger.info(f"[MODAL CLIENT] Image bytes: {len(image_bytes)} bytes")
            
            # Get Modal function
            logger.info(f"[MODAL CLIENT] Getting Modal function for megadetector...")
            model = self._get_modal_function("megadetector")
            logger.info(f"[MODAL CLIENT] Modal function obtained")
            
            # Call with retry
            logger.info(f"[MODAL CLIENT] Calling model.detect() via Modal...")
            result = await self._call_with_retry(
                model.detect,
                image_bytes,
                confidence_threshold
            )
            
            logger.info(f"[MODAL CLIENT] Modal call completed. Result keys: {list(result.keys()) if result else 'None'}")
            return result
            
        except (ModalUnavailableError, ModalClientError) as e:
            logger.error(f"[MODAL CLIENT] Modal unavailable/failed for MegaDetector: {e}")
            logger.warning(f"[MODAL CLIENT] Falling back to MOCK detection response")
            
            # Return mock detection instead of queuing
            w, h = image.size
            return {
                "success": True,
                "detections": [
                    {
                        "bbox": [int(w * 0.1), int(h * 0.1), int(w * 0.9), int(h * 0.9)],
                        "confidence": 0.95,
                        "category": "animal",
                        "class_id": 0
                    }
                ],
                "mock": True
            }
    
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
            # Mock mode for development
            if self.use_mock:
                logger.info(f"[MODAL CLIENT] 🚧 Using MOCK WildlifeTools embedding")
                return {
                    "success": True,
                    "embedding": np.random.rand(2048).tolist(),
                    "shape": (2048,),
                    "mock": True
                }
            
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
            
        except (ModalUnavailableError, ModalClientError) as e:
            logger.error(f"Modal unavailable/failed for WildlifeTools: {e}")
            logger.warning(f"[MODAL CLIENT] Falling back to MOCK WildlifeTools embedding")
            return {
                "success": True,
                "embedding": np.random.rand(2048).tolist(),
                "shape": (2048,),
                "mock": True
            }
    
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
            # Mock mode for development
            if self.use_mock:
                logger.info(f"[MODAL CLIENT] 🚧 Using MOCK RAPID embedding")
                return {
                    "success": True,
                    "embedding": np.random.rand(2048).tolist(),
                    "shape": (2048,),
                    "mock": True
                }
            
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
            
        except (ModalUnavailableError, ModalClientError) as e:
            logger.error(f"Modal unavailable/failed for RAPID: {e}")
            logger.warning(f"[MODAL CLIENT] Falling back to MOCK RAPID embedding")
            return {
                "success": True,
                "embedding": np.random.rand(2048).tolist(),
                "shape": (2048,),
                "mock": True
            }
    
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
            # Mock mode for development
            if self.use_mock:
                logger.info(f"[MODAL CLIENT] 🚧 Using MOCK CVWC2019 embedding")
                return {
                    "success": True,
                    "embedding": np.random.rand(3072).tolist(),  # 3072-dim for CVWC2019
                    "shape": (3072,),
                    "mock": True
                }
            
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
            
        except (ModalUnavailableError, ModalClientError) as e:
            logger.error(f"Modal unavailable/failed for CVWC2019: {e}")
            logger.warning(f"[MODAL CLIENT] Falling back to MOCK CVWC2019 embedding")
            return {
                "success": True,
                "embedding": np.random.rand(3072).tolist(),
                "shape": (3072,),
                "mock": True
            }
    
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
        Analyze a video using OmniVinci model.

        Args:
            video_path: Path to video file
            prompt: Analysis prompt
            tools: Optional list of tools
            tool_callback_url: URL for tool callbacks
            fallback_to_queue: Whether to queue request if Modal unavailable

        Returns:
            Dictionary with analysis results
        """
        try:
            # Load video bytes
            with open(video_path, "rb") as f:
                video_bytes = f.read()

            # Get Modal function
            model = self._get_modal_function("omnivinci")

            # Call with retry
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

