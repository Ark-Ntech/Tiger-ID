"""Database MCP server implementation"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
import numpy as np

from backend.mcp_servers.base_mcp_server import MCPServerBase, MCPTool
from backend.database import (
    get_db_session,
    Tiger,
    Facility,
    Investigation
)
from backend.database.vector_search import find_matching_tigers
from backend.utils.logging import get_logger
from backend.utils.uuid_helpers import safe_uuid, parse_uuid

logger = get_logger(__name__)


class DatabaseMCPServer(MCPServerBase):
    """MCP server for database queries"""
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize Database MCP server
        
        Args:
            db: Database session (optional)
        """
        super().__init__("database")
        self.db = db
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register available tools"""
        self.tools = {
            "query_tigers": MCPTool(
                name="query_tigers",
                description="Query tiger database with filters",
                parameters={
                    "type": "object",
                    "properties": {
                        "tiger_id": {"type": "string", "description": "Tiger ID"},
                        "name": {"type": "string", "description": "Tiger name (partial match)"},
                        "status": {"type": "string", "description": "Tiger status"},
                        "facility_id": {"type": "string", "description": "Facility ID"},
                        "limit": {"type": "integer", "description": "Maximum results", "default": 100}
                    }
                },
                handler=self._handle_query_tigers
            ),
            "query_facilities": MCPTool(
                name="query_facilities",
                description="Query facility database with filters",
                parameters={
                    "type": "object",
                    "properties": {
                        "facility_id": {"type": "string", "description": "Facility ID"},
                        "usda_license": {"type": "string", "description": "USDA license number"},
                        "state": {"type": "string", "description": "State location"},
                        "search_query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Maximum results", "default": 100}
                    }
                },
                handler=self._handle_query_facilities
            ),
            "search_tiger_by_embedding": MCPTool(
                name="search_tiger_by_embedding",
                description="Search for tigers by image embedding similarity",
                parameters={
                    "type": "object",
                    "properties": {
                        "embedding": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Embedding vector"
                        },
                        "similarity_threshold": {
                            "type": "number",
                            "description": "Minimum similarity score",
                            "default": 0.8
                        },
                        "limit": {"type": "integer", "description": "Maximum results", "default": 10}
                    },
                    "required": ["embedding"]
                },
                handler=self._handle_search_by_embedding
            ),
            "query_investigations": MCPTool(
                name="query_investigations",
                description="Query investigations with filters",
                parameters={
                    "type": "object",
                    "properties": {
                        "investigation_id": {"type": "string", "description": "Investigation ID"},
                        "status": {"type": "string", "description": "Investigation status"},
                        "created_by": {"type": "string", "description": "User ID"},
                        "priority": {"type": "string", "description": "Priority level"},
                        "limit": {"type": "integer", "description": "Maximum results", "default": 100}
                    }
                },
                handler=self._handle_query_investigations
            )
        }
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        return [tool.to_dict() for tool in self.tools.values()]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool"""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}
        
        try:
            return await self.tools[tool_name].call(arguments)
        except Exception as e:
            logger.error("Tool call failed", tool=tool_name, error=str(e))
            return {"error": str(e)}
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources"""
        return []
    
    async def _handle_query_tigers(
        self,
        tiger_id: Optional[str] = None,
        name: Optional[str] = None,
        status: Optional[str] = None,
        facility_id: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Handle tiger query"""
        session = self.db or get_db_session()
        
        try:
            query = session.query(Tiger)
            
            if tiger_id:
                tiger_uuid = parse_uuid(tiger_id)
                query = query.filter(Tiger.tiger_id == tiger_uuid)
            if name:
                query = query.filter(Tiger.name.ilike(f"%{name}%"))
            if status:
                query = query.filter(Tiger.status == status)
            if facility_id:
                facility_uuid = parse_uuid(facility_id)
                query = query.filter(Tiger.origin_facility_id == facility_uuid)
            
            tigers = query.limit(limit).all()
            
            results = [
                {
                    "tiger_id": str(t.tiger_id),
                    "name": t.name,
                    "alias": t.alias,
                    "status": t.status,
                    "last_seen_location": t.last_seen_location,
                    "last_seen_date": t.last_seen_date.isoformat() if t.last_seen_date else None
                }
                for t in tigers
            ]
            
            return {
                "tigers": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error("Tiger query failed", error=str(e))
            return {"error": str(e), "tigers": []}
        finally:
            if not self.db:
                session.close()
    
    async def _handle_query_facilities(
        self,
        facility_id: Optional[str] = None,
        usda_license: Optional[str] = None,
        state: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Handle facility query"""
        session = self.db or get_db_session()
        
        try:
            query = session.query(Facility)
            
            if facility_id:
                facility_uuid = parse_uuid(facility_id)
                query = query.filter(Facility.facility_id == facility_uuid)
            if usda_license:
                query = query.filter(Facility.usda_license == usda_license)
            if state:
                query = query.filter(Facility.state == state)
            if search_query:
                query = query.filter(Facility.exhibitor_name.ilike(f"%{search_query}%"))
            
            facilities = query.limit(limit).all()
            
            results = [
                {
                    "facility_id": str(f.facility_id),
                    "exhibitor_name": f.exhibitor_name,
                    "state": f.state,
                    "city": f.city,
                    "usda_license": f.usda_license,
                    "tiger_count": f.tiger_count,
                    "accreditation_status": f.accreditation_status
                }
                for f in facilities
            ]
            
            return {
                "facilities": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error("Facility query failed", error=str(e))
            return {"error": str(e), "facilities": []}
        finally:
            if not self.db:
                session.close()
    
    async def _handle_search_by_embedding(
        self,
        embedding: List[float],
        similarity_threshold: float = 0.8,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Handle embedding similarity search"""
        session = self.db or get_db_session()
        
        try:
            embedding_array = np.array(embedding)
            
            matches = find_matching_tigers(
                session,
                query_embedding=embedding_array,
                similarity_threshold=similarity_threshold,
                limit=limit
            )
            
            return {
                "matches": matches,
                "count": len(matches)
            }
        except Exception as e:
            logger.error("Embedding search failed", error=str(e))
            return {"error": str(e), "matches": []}
        finally:
            if not self.db:
                session.close()
    
    async def _handle_query_investigations(
        self,
        investigation_id: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Handle investigation query"""
        session = self.db or get_db_session()
        
        try:
            query = session.query(Investigation)
            
            if investigation_id:
                inv_uuid = parse_uuid(investigation_id)
                query = query.filter(Investigation.investigation_id == inv_uuid)
            if status:
                query = query.filter(Investigation.status == status)
            if created_by:
                user_uuid = parse_uuid(created_by)
                query = query.filter(Investigation.created_by == user_uuid)
            if priority:
                query = query.filter(Investigation.priority == priority)
            
            investigations = query.order_by(Investigation.created_at.desc()).limit(limit).all()
            
            results = [
                {
                    "investigation_id": str(inv.investigation_id),
                    "title": inv.title,
                    "status": inv.status,
                    "priority": inv.priority,
                    "created_at": inv.created_at.isoformat() if inv.created_at else None
                }
                for inv in investigations
            ]
            
            return {
                "investigations": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error("Investigation query failed", error=str(e))
            return {"error": str(e), "investigations": []}
        finally:
            if not self.db:
                session.close()

