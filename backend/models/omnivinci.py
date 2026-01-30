"""
OmniVinci video analysis model using Modal and NVIDIA API.

This module provides video analysis capabilities using the OmniVinci model
hosted on Modal, which calls the NVIDIA API endpoint.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from PIL import Image

from backend.utils.logging import get_logger
from backend.services.modal_client import get_modal_client
from backend.config.settings import get_settings

logger = get_logger(__name__)


class OmniVinciModel:
    """OmniVinci video analysis model using Modal backend."""
    
    def __init__(self):
        """Initialize OmniVinci model with Modal backend."""
        self.settings = get_settings()
        self.modal_client = get_modal_client()
        
        logger.info("OmniVinciModel initialized with Modal backend")
    
    async def analyze_video(
        self,
        video_path: Path,
        prompt: str = "Analyze this video and describe what you see. Focus on identifying any tigers, their behavior, and the environment.",
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a video using OmniVinci with optional agentic tool calling.
        
        Args:
            video_path: Path to video file
            prompt: Analysis prompt
            tools: Optional list of available tools for agentic calling
            tool_callback_url: Optional URL to call back for tool execution
            
        Returns:
            Dictionary with analysis results and any tool calls
        """
        try:
            logger.info(f"Analyzing video: {video_path}")
            if tools:
                logger.info(f"Providing {len(tools)} tools to OmniVinci for agentic calling")
            
            # Call Modal service with tools
            result = await self.modal_client.omnivinci_analyze_video(
                video_path,
                prompt,
                tools,
                tool_callback_url
            )
            
            if result.get("success"):
                logger.info("Video analysis completed successfully")
                return result
            else:
                # Extract detailed error information
                error_msg = result.get("error", "Unknown error")
                traceback_info = result.get("traceback", "")
                
                # Log detailed error information
                logger.error(f"Video analysis failed: {error_msg}")
                if traceback_info:
                    logger.error(f"OmniVinci traceback: {traceback_info}")
                
                # Check if request was queued
                if result.get("queued"):
                    logger.warning("Video analysis request queued for later processing")
                    return result
                
                # Provide more specific error message
                if "traceback" in result:
                    # Extract the actual error from traceback if available
                    if "Error:" in traceback_info or "Exception:" in traceback_info:
                        # Try to extract the last error line
                        lines = traceback_info.split("\n")
                        for line in reversed(lines):
                            if "Error:" in line or "Exception:" in line or ":" in line:
                                error_msg = line.strip()
                                break
                
                # Create a more descriptive error message
                detailed_error = f"OmniVinci video analysis failed: {error_msg}"
                if "Modal" in str(error_msg) or "modal" in str(error_msg).lower():
                    detailed_error += ". Modal service may be unavailable or misconfigured."
                elif "timeout" in str(error_msg).lower():
                    detailed_error += ". The video processing timed out. Try a shorter video."
                elif "memory" in str(error_msg).lower() or "OOM" in str(error_msg):
                    detailed_error += ". Out of memory. The video may be too large."
                elif "model" in str(error_msg).lower() and "not found" in str(error_msg).lower():
                    detailed_error += ". OmniVinci model not found. Check Modal configuration."
                
                raise RuntimeError(detailed_error)
            
        except RuntimeError:
            # Re-raise RuntimeError as-is (already has detailed message)
            raise
        except Exception as e:
            # Wrap other exceptions with more context
            error_type = type(e).__name__
            logger.error(f"Error analyzing video ({error_type}): {e}", exc_info=True)
            raise RuntimeError(f"OmniVinci analysis error ({error_type}): {str(e)}")
    
    async def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str = "Analyze this tiger image in detail. Describe the tiger's physical characteristics, visible stripe patterns, pose, behavior, and environmental context. Provide insights that would help with individual identification."
    ) -> Dict[str, Any]:
        """
        Analyze an image using OmniVinci's omni-modal understanding.
        
        OmniVinci provides rich visual analysis that goes beyond pattern matching,
        offering contextual understanding of the scene, tiger behavior, and environmental factors.
        
        Args:
            image_bytes: Image as bytes
            prompt: Analysis prompt for what to focus on
            
        Returns:
            Dictionary with detailed analysis results
        """
        try:
            logger.info("Analyzing image with OmniVinci omni-modal model...")
            
            # Call Modal OmniVinci service for image analysis
            result = await self.modal_client.omnivinci_analyze_image(
                image_bytes=image_bytes,
                prompt=prompt
            )
            
            if result.get("success"):
                logger.info(f"OmniVinci image analysis completed: {len(result.get('analysis', ''))} chars")
                return result
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"OmniVinci image analysis failed: {error}")
                raise RuntimeError(f"OmniVinci analysis failed: {error}")
            
        except Exception as e:
            logger.error(f"Error analyzing image with OmniVinci: {e}")
            raise


def get_omnivinci_model() -> OmniVinciModel:
    """
    Get or create OmniVinci model instance.
    
    Returns:
        OmniVinciModel instance
    """
    return OmniVinciModel()

