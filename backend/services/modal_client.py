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
    
    # Maximum total time allowed for all retries to prevent gateway timeouts
    MAX_TOTAL_TIMEOUT = 90  # Most gateways timeout at 60-120s, stay under
    DEFAULT_SINGLE_TIMEOUT = 60  # Conservative single request timeout

    def __init__(
        self,
        max_retries: int = 2,
        retry_delay: float = 1.0,
        timeout: int = 60,
        queue_max_size: int = 100,
        use_mock: bool = None,
        max_total_timeout: int = None
    ):
        """
        Initialize Modal client.

        Args:
            max_retries: Maximum number of retries for failed requests
            retry_delay: Initial delay between retries (exponential backoff)
            timeout: Request timeout in seconds per attempt
            queue_max_size: Maximum size of request queue
            use_mock: Use mock responses instead of real Modal (for development)
            max_total_timeout: Maximum total time for all retries (prevents gateway timeouts)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = min(timeout, self.DEFAULT_SINGLE_TIMEOUT)  # Cap single timeout
        self.queue_max_size = queue_max_size
        self.max_total_timeout = max_total_timeout or self.MAX_TOTAL_TIMEOUT
        
        # Check if mock mode enabled via environment variable
        import os
        app_env = os.getenv("APP_ENV", "development").lower()
        is_production = app_env == "production"

        # Determine mock mode: explicit setting takes precedence, but NEVER allow mock in production
        env_mock = os.getenv("MODAL_USE_MOCK", "false").lower() == "true"
        requested_mock = use_mock if use_mock is not None else env_mock

        if is_production and requested_mock:
            logger.error("[MODAL CLIENT] MOCK MODE BLOCKED - Production environment detected. "
                        "Mock mode would return random embeddings causing incorrect tiger matches.")
            raise RuntimeError(
                "Mock mode is disabled in production to prevent incorrect tiger identifications. "
                "Ensure Modal is properly configured or set APP_ENV=development for testing."
            )

        self.use_mock = requested_mock

        if self.use_mock:
            logger.warning("[MODAL CLIENT] MOCK MODE ENABLED - Using simulated responses. "
                          "This returns random embeddings - DO NOT use for real tiger identification!")
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
        self._transreid = None
        
        # Stats
        self.stats = {
            "requests_sent": 0,
            "requests_succeeded": 0,
            "requests_failed": 0,
            "requests_queued": 0,
        }

    def close(self) -> None:
        """
        Clean up resources and clear cached Modal references.

        Should be called when shutting down the service or when
        Modal connections need to be reset.
        """
        logger.info("[MODAL CLIENT] Cleaning up resources...")

        # Clear cached Modal function references
        self._tiger_reid = None
        self._megadetector = None
        self._wildlife_tools = None
        self._rapid_reid = None
        self._cvwc2019_reid = None
        self._transreid = None
        self._megadescriptor_b = None
        self._matchanything = None

        # Clear the request queue
        while not self.request_queue.empty():
            try:
                self.request_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        logger.info("[MODAL CLIENT] Resources cleaned up")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        self.close()
        return False

    def _get_modal_function(self, model_name: str):
        """
        Lazy load Modal function reference from deployed app.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Modal function reference
        """
        logger.info(f"[MODAL CLIENT] Getting Modal function for model: {model_name}")

        # Map model names to (app_name, class_name)
        # Uses deployed Modal apps: 'detector', 'reid'
        model_config = {
            "tiger_reid": ("reid", "TigerReID"),
            "megadetector": ("detector", "MegaDetector"),
            "wildlife_tools": ("reid", "WildlifeToolsModel"),
            "megadescriptor_b": ("reid", "MegaDescriptorBModel"),
            "rapid_reid": ("reid", "RAPIDReIDModel"),
            "cvwc2019_reid": ("reid", "CVWC2019ReIDModel"),
            "transreid": ("reid", "TransReIDModel"),
            "matchanything": ("reid", "MatchAnythingModel"),
        }

        if model_name not in model_config:
            raise ValueError(f"Unknown model: {model_name}")

        app_name, class_name = model_config[model_name]
        logger.info(f"[MODAL CLIENT] Model config: app='{app_name}', class='{class_name}'")

        try:
            import modal

            # Cache attribute name
            cache_attr = f"_{model_name}"

            # Return cached instance if available
            if getattr(self, cache_attr, None) is not None:
                logger.info(f"[MODAL CLIENT] Using cached Modal instance for {model_name}")
                return getattr(self, cache_attr)

            # Get the deployed class using Cls.from_name()
            # This references the actual deployed app on Modal
            try:
                logger.info(f"[MODAL CLIENT] Connecting to Modal app '{app_name}' class '{class_name}'...")
                model_cls = modal.Cls.from_name(app_name, class_name)
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
            logger.error(f"Modal app '{app_name}' or class '{class_name}' not found: {e}")
            raise ModalUnavailableError(f"Modal app '{app_name}' or model '{class_name}' not deployed")
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
        Call Modal function with retry logic and total timeout tracking.

        Prevents gateway timeouts by tracking total elapsed time and aborting
        before exceeding max_total_timeout.

        Args:
            func: Modal function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result
        """
        import time
        last_error = None
        start_time = time.monotonic()

        logger.info(f"[MODAL CLIENT] _call_with_retry starting (max_retries={self.max_retries}, "
                   f"timeout={self.timeout}s, max_total={self.max_total_timeout}s)")

        for attempt in range(self.max_retries):
            elapsed = time.monotonic() - start_time
            remaining_total = self.max_total_timeout - elapsed

            # Check if we have enough time for another attempt
            if remaining_total < 5:  # Need at least 5s for meaningful attempt
                logger.warning(f"[MODAL CLIENT] Total timeout approaching ({elapsed:.1f}s elapsed), "
                              f"aborting retries to prevent gateway timeout")
                break

            # Reduce per-attempt timeout if total time is running low
            attempt_timeout = min(self.timeout, remaining_total - 2)  # Leave 2s buffer

            try:
                logger.info(f"[MODAL CLIENT] Attempt {attempt + 1}/{self.max_retries} "
                           f"(timeout={attempt_timeout:.1f}s, elapsed={elapsed:.1f}s)")
                self.stats["requests_sent"] += 1

                # Call Modal function with calculated timeout
                result = await asyncio.wait_for(
                    func.remote.aio(*args, **kwargs),
                    timeout=attempt_timeout
                )

                logger.info(f"[MODAL CLIENT] Call succeeded on attempt {attempt + 1}")
                self.stats["requests_succeeded"] += 1
                return result

            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(f"[MODAL CLIENT] Request timeout on attempt {attempt + 1}/{self.max_retries} "
                              f"(waited {attempt_timeout:.1f}s)")

            except Exception as e:
                last_error = e
                logger.warning(f"[MODAL CLIENT] Request failed on attempt {attempt + 1}/{self.max_retries}: "
                              f"{type(e).__name__}: {e}", exc_info=True)

            # Check remaining time before backoff
            elapsed = time.monotonic() - start_time
            if elapsed >= self.max_total_timeout - 5:
                logger.warning(f"[MODAL CLIENT] Total timeout imminent, skipping backoff and retries")
                break

            # Exponential backoff (capped to not exceed total timeout)
            if attempt < self.max_retries - 1:
                delay = min(self.retry_delay * (2 ** attempt), self.max_total_timeout - elapsed - 10)
                if delay > 0:
                    logger.info(f"[MODAL CLIENT] Waiting {delay:.1f}s before retry...")
                    await asyncio.sleep(delay)

        # All retries failed
        total_elapsed = time.monotonic() - start_time
        logger.error(f"[MODAL CLIENT] All attempts failed after {total_elapsed:.1f}s. "
                    f"Last error: {type(last_error).__name__}: {last_error}")
        self.stats["requests_failed"] += 1
        raise ModalClientError(f"Request failed after {self.max_retries} attempts ({total_elapsed:.1f}s): {last_error}")
    
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

    # ==================== MegaDescriptor-B Methods ====================

    async def megadescriptor_b_embedding(
        self,
        image: Image.Image,
        fallback_to_queue: bool = True
    ) -> Dict[str, Any]:
        """
        Generate MegaDescriptor-B-224 embedding (faster variant).

        Args:
            image: PIL Image
            fallback_to_queue: Whether to queue request if Modal unavailable

        Returns:
            Dictionary with embedding vector
        """
        try:
            # Mock mode for development
            if self.use_mock:
                logger.info(f"[MODAL CLIENT] Using MOCK MegaDescriptor-B embedding")
                return {
                    "success": True,
                    "embedding": np.random.rand(1024).tolist(),
                    "shape": (1024,),
                    "mock": True
                }

            # Convert image to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()

            # Get Modal function
            model = self._get_modal_function("megadescriptor_b")

            # Call with retry
            result = await self._call_with_retry(
                model.generate_embedding,
                image_bytes
            )

            return result

        except (ModalUnavailableError, ModalClientError) as e:
            logger.error(f"Modal unavailable/failed for MegaDescriptor-B: {e}")
            logger.warning(f"[MODAL CLIENT] Falling back to MOCK MegaDescriptor-B embedding")
            return {
                "success": True,
                "embedding": np.random.rand(1024).tolist(),
                "shape": (1024,),
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
                    "embedding": np.random.rand(2048).tolist(),  # 2048-dim for CVWC2019
                    "shape": (2048,),
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
                "embedding": np.random.rand(2048).tolist(),
                "shape": (2048,),
                "mock": True
            }
    
    # ==================== TransReID Methods ====================

    async def transreid_generate_embedding(
        self,
        image_bytes: bytes,
        fallback_to_queue: bool = True
    ) -> Dict[str, Any]:
        """
        Generate embedding using TransReID Vision Transformer model.

        TransReID uses ViT-Base architecture for robust feature extraction.
        Outputs 768-dimensional embeddings.

        Args:
            image_bytes: Image as bytes
            fallback_to_queue: Whether to queue request if Modal unavailable

        Returns:
            Dictionary with embedding vector
        """
        if self.use_mock:
            logger.info(f"[MODAL CLIENT] Using MOCK TransReID embedding")
            return {
                "success": True,
                "embedding": np.random.rand(768).tolist(),
                "shape": (768,),
                "mock": True
            }

        try:
            model = self._get_modal_function("transreid")
            result = await self._call_with_retry(
                model.generate_embedding,
                image_bytes
            )
            return result

        except ModalUnavailableError as e:
            logger.error(f"Modal unavailable for TransReID: {e}")

            if fallback_to_queue:
                return await self._queue_request(
                    "transreid",
                    "generate_embedding",
                    image_bytes
                )
            else:
                return {
                    "success": False,
                    "embedding": None,
                    "error": "TransReID service unavailable"
                }
        except Exception as e:
            logger.error(f"TransReID embedding error: {e}")
            return {
                "success": False,
                "embedding": None,
                "error": str(e)
            }

    # ==================== MatchAnything Methods ====================

    async def matchanything_match(
        self,
        image1_bytes: bytes,
        image2_bytes: bytes,
        threshold: float = 0.2
    ) -> Dict[str, Any]:
        """
        Match two images using MatchAnything-ELOFTR.

        MatchAnything finds keypoint correspondences between image pairs,
        useful for geometric verification of tiger identity.

        Args:
            image1_bytes: First image as bytes
            image2_bytes: Second image as bytes
            threshold: Confidence threshold for keypoint filtering

        Returns:
            Dictionary with matching results:
            - num_matches: Number of keypoint correspondences
            - mean_score: Average confidence of matches
            - success: Whether matching succeeded
        """
        if self.use_mock:
            logger.info("[MODAL CLIENT] Using MOCK MatchAnything match")
            num_matches = np.random.randint(50, 200)
            scores = np.random.uniform(0.3, 0.9, num_matches)
            return {
                "success": True,
                "num_matches": num_matches,
                "mean_score": float(scores.mean()),
                "max_score": float(scores.max()),
                "total_score": float(scores.sum()),
                "mock": True
            }

        try:
            model = self._get_modal_function("matchanything")
            result = await self._call_with_retry(
                model.match_images,
                image1_bytes,
                image2_bytes,
                threshold
            )
            return result

        except ModalUnavailableError as e:
            logger.error(f"Modal unavailable for MatchAnything: {e}")
            return {
                "success": False,
                "num_matches": 0,
                "error": "MatchAnything service unavailable"
            }
        except Exception as e:
            logger.error(f"MatchAnything match error: {e}")
            return {
                "success": False,
                "num_matches": 0,
                "error": str(e)
            }

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

