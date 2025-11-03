"""Tiger ID MCP server implementation"""

from typing import Dict, Any, Optional, List
import numpy as np
import base64
import io
from PIL import Image

from backend.mcp_servers.base_mcp_server import MCPServerBase, MCPTool
from backend.models.reid import TigerReIDModel
from backend.models.detection import TigerDetectionModel
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class TigerIDMCPServer(MCPServerBase):
    """MCP server for tiger identification"""
    
    def __init__(self):
        """
        Initialize Tiger ID MCP server
        """
        super().__init__("tiger_id")
        self.detection_model = TigerDetectionModel()
        self.reid_model = TigerReIDModel()
        
        # Initialize models
        self._initialized = False
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register available tools"""
        self.tools = {
            "identify_tiger": MCPTool(
                name="identify_tiger",
                description="Identify a tiger from an image",
                parameters={
                    "type": "object",
                    "properties": {
                        "image_data": {
                            "type": "string",
                            "description": "Image data (base64 encoded bytes or image path)"
                        },
                        "image_path": {
                            "type": "string",
                            "description": "Path to image file (alternative to image_data)"
                        },
                        "similarity_threshold": {
                            "type": "number",
                            "description": "Minimum similarity for match",
                            "default": 0.8
                        }
                    }
                },
                handler=self._handle_identify_tiger
            ),
            "generate_embedding": MCPTool(
                name="generate_embedding",
                description="Generate embedding vector for a tiger image",
                parameters={
                    "type": "object",
                    "properties": {
                        "image_data": {
                            "type": "string",
                            "description": "Image data (base64 encoded bytes or image path)"
                        },
                        "image_path": {
                            "type": "string",
                            "description": "Path to image file (alternative to image_data)"
                        }
                    },
                    "anyOf": [
                        {"required": ["image_data"]},
                        {"required": ["image_path"]}
                    ]
                },
                handler=self._handle_generate_embedding
            ),
            "detect_tiger": MCPTool(
                name="detect_tiger",
                description="Detect tigers in an image using MegaDetector",
                parameters={
                    "type": "object",
                    "properties": {
                        "image_data": {
                            "type": "string",
                            "description": "Image data (base64 encoded bytes or image path)"
                        },
                        "image_path": {
                            "type": "string",
                            "description": "Path to image file (alternative to image_data)"
                        }
                    }
                },
                handler=self._handle_detect_tiger
            )
        }
    
    async def _ensure_initialized(self):
        """Ensure models are initialized"""
        if not self._initialized:
            await self.detection_model.load_model()
            await self.reid_model.load_model()
            self._initialized = True
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        return [tool.to_dict() for tool in self.tools.values()]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool"""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}
        
        try:
            await self._ensure_initialized()
            return await self.tools[tool_name].call(arguments)
        except Exception as e:
            logger.error("Tool call failed", tool=tool_name, error=str(e))
            return {"error": str(e)}
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources"""
        return []
    
    async def _decode_image(self, image_data: Optional[str] = None, image_path: Optional[str] = None) -> bytes:
        """Decode image from base64 or load from path"""
        if image_path:
            with open(image_path, 'rb') as f:
                return f.read()
        elif image_data:
            # Try base64 decode
            try:
                return base64.b64decode(image_data)
            except Exception:
                # Assume it's already bytes or string path
                if isinstance(image_data, str):
                    with open(image_data, 'rb') as f:
                        return f.read()
                return image_data
        else:
            raise ValueError("Either image_data or image_path must be provided")
    
    async def _handle_identify_tiger(
        self,
        image_data: Optional[str] = None,
        image_path: Optional[str] = None,
        similarity_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """Handle tiger identification"""
        try:
            image_bytes = await self._decode_image(image_data, image_path)
            
            # Detect tiger
            detection_result = await self.detection_model.detect(image_bytes)
            
            if not detection_result.get("detections"):
                return {
                    "identified": False,
                    "message": "No tiger detected in image",
                    "confidence": 0.0
                }
            
            # Extract crop
            tiger_crop = detection_result["detections"][0].get("crop")
            
            if not tiger_crop:
                return {
                    "identified": False,
                    "message": "Failed to extract tiger crop",
                    "confidence": 0.0
                }
            
            # Generate embedding
            embedding = await self.reid_model.generate_embedding(tiger_crop)
            
            return {
                "identified": True,
                "embedding": embedding.tolist(),
                "confidence": detection_result["detections"][0].get("confidence", 0.0),
                "bbox": detection_result["detections"][0].get("bbox"),
                "detection_count": len(detection_result.get("detections", []))
            }
        except Exception as e:
            logger.error("Tiger identification failed", error=str(e))
            return {"error": str(e), "identified": False}
    
    async def _handle_generate_embedding(
        self,
        image_data: Optional[str] = None,
        image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle embedding generation"""
        try:
            image_bytes = await self._decode_image(image_data, image_path)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Generate embedding
            embedding = await self.reid_model.generate_embedding(image)
            
            return {
                "embedding": embedding.tolist(),
                "embedding_dim": len(embedding),
                "success": True
            }
        except Exception as e:
            logger.error("Embedding generation failed", error=str(e))
            return {"error": str(e), "success": False}
    
    async def _handle_detect_tiger(
        self,
        image_data: Optional[str] = None,
        image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle tiger detection"""
        try:
            image_bytes = await self._decode_image(image_data, image_path)
            
            # Detect tigers
            detection_result = await self.detection_model.detect(image_bytes)
            
            detections = []
            for det in detection_result.get("detections", []):
                detections.append({
                    "bbox": det.get("bbox"),
                    "confidence": det.get("confidence", 0.0)
                })
            
            return {
                "detections": detections,
                "count": len(detections),
                "image_size": detection_result.get("image_size")
            }
        except Exception as e:
            logger.error("Tiger detection failed", error=str(e))
            return {"error": str(e), "detections": [], "count": 0}

