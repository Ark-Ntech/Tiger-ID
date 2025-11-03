"""Base MCP server implementation"""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from backend.utils.logging import get_logger

logger = get_logger(__name__)


class MCPServerBase(ABC):
    """Base class for MCP servers"""
    
    def __init__(self, name: str):
        """
        Initialize MCP server
        
        Args:
            name: Server name
        """
        self.name = name
        self.tools = {}
        self.resources = {}
    
    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool"""
        pass
    
    @abstractmethod
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources"""
        pass
    
    async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """Get a resource"""
        if resource_uri in self.resources:
            return self.resources[resource_uri]
        return {"error": "Resource not found"}


class MCPTool:
    """MCP tool definition"""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler
    ):
        """
        Initialize MCP tool
        
        Args:
            name: Tool name
            description: Tool description
            parameters: Tool parameters schema
            handler: Tool handler function
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    
    async def call(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool handler"""
        return await self.handler(**arguments)

