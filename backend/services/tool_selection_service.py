"""Service for intelligent tool selection based on investigation context"""

from typing import Dict, Any, List, Optional
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ToolSelectionService:
    """Service for intelligently selecting which tools to use based on investigation context"""
    
    def __init__(self):
        self.available_tools = [
            "web_search",
            "news_search",
            "reverse_image_search",
            "generate_leads",
            "relationship_analysis",
            "data_extraction",
            "evidence_compilation",
            "youtube_search",
            "meta_search",
            "social_media_intelligence"
        ]
    
    def select_tools(
        self,
        inputs: Dict[str, Any],
        investigation_context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Select appropriate tools based on investigation inputs and context
        
        Args:
            inputs: User inputs (images, text, location, facility, etc.)
            investigation_context: Optional investigation context (existing evidence, phase, etc.)
        
        Returns:
            List of tool names to use
        """
        selected_tools = []
        
        # Always include basic database queries
        # (handled separately in research agent)
        
        # Web search - use if there's text query or facility/tiger names
        if inputs.get("query") or inputs.get("text"):
            if self._should_use_web_search(inputs):
                selected_tools.append("web_search")
        
        # News search - use if facility name or location provided
        if inputs.get("facility") or inputs.get("location"):
            selected_tools.append("news_search")
            
            # Also check reference facilities
            if inputs.get("facility") or inputs.get("usda_license"):
                selected_tools.append("check_reference_facilities")
        
        # YouTube search - use if facility name or location provided
        if inputs.get("facility") or inputs.get("location"):
            selected_tools.append("youtube_search")
        
        # Meta search - use if facility name or social media links detected
        if inputs.get("facility") or inputs.get("social_media_links"):
            selected_tools.append("meta_search")
        
        # Social media intelligence - auto-select when facility or location provided
        if inputs.get("facility") or inputs.get("location"):
            selected_tools.append("social_media_intelligence")
        
        # Reverse image search - use if images provided
        if inputs.get("images") and len(inputs.get("images", [])) > 0:
            selected_tools.append("reverse_image_search")
        
        # Lead generation - use if location provided or suspicious patterns detected
        if inputs.get("location"):
            selected_tools.append("generate_leads")
        
        # Relationship analysis - use if facility or tiger provided
        if inputs.get("facility") or inputs.get("tiger_id"):
            selected_tools.append("relationship_analysis")
        
        # Data extraction - use if files provided
        if inputs.get("files") and len(inputs.get("files", [])) > 0:
            selected_tools.append("data_extraction")
        
        # Evidence compilation - always useful if there's existing evidence
        if investigation_context and investigation_context.get("evidence_count", 0) > 0:
            selected_tools.append("evidence_compilation")
        
        logger.info(
            f"Selected tools: {selected_tools}",
            inputs_keys=list(inputs.keys()),
            context=investigation_context
        )
        
        return selected_tools
    
    def _should_use_web_search(self, inputs: Dict[str, Any]) -> bool:
        """Determine if web search should be used"""
        query = inputs.get("query", "") or inputs.get("text", "")
        
        # Use web search if query has substantial content
        if len(query) > 10:
            # Check for investigation-relevant keywords
            keywords = [
                "tiger", "trafficking", "facility", "zoo", "sanctuary",
                "breeding", "exotic", "wildlife", "animal", "permit", "license"
            ]
            query_lower = query.lower()
            if any(keyword in query_lower for keyword in keywords):
                return True
        
        # Use if facility or tiger name provided
        if inputs.get("facility") or inputs.get("tiger_id"):
            return True
        
        return False
    
    def get_tool_priority(self, tool_name: str, context: Dict[str, Any]) -> int:
        """
        Get priority for a tool (higher = more important)
        
        Args:
            tool_name: Name of the tool
            context: Investigation context
        
        Returns:
            Priority score (1-10)
        """
        priorities = {
            "web_search": 7,
            "news_search": 6,
            "reverse_image_search": 8,  # High priority if images available
            "generate_leads": 5,
            "relationship_analysis": 6,
            "data_extraction": 7,
            "evidence_compilation": 4,
            "check_reference_facilities": 9,  # Very high priority
            "youtube_search": 6,
            "meta_search": 6,
            "social_media_intelligence": 7
        }
        
        base_priority = priorities.get(tool_name, 3)
        
        # Adjust based on context
        if tool_name == "reverse_image_search" and context.get("has_images"):
            base_priority = 9
        
        if tool_name == "check_reference_facilities" and context.get("has_facility"):
            base_priority = 10
        
        if tool_name == "news_search" and context.get("is_reference_facility"):
            base_priority = 8
        
        return base_priority
    
    def get_tool_parameters(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get parameters for a tool based on inputs
        
        Args:
            tool_name: Name of the tool
            inputs: User inputs
            context: Optional context
        
        Returns:
            Tool parameters
        """
        params = {}
        
        if tool_name == "web_search":
            params["query"] = inputs.get("query") or inputs.get("text", "")
            params["limit"] = 10
            if inputs.get("facility"):
                params["query"] = f'"{inputs["facility"]}" tiger trafficking'
        
        elif tool_name == "news_search":
            facility = inputs.get("facility")
            location = inputs.get("location")
            if facility:
                params["query"] = f'"{facility}" tiger'
            elif location:
                params["query"] = f'tiger trafficking {location}'
            params["limit"] = 10
        
        elif tool_name == "reverse_image_search":
            params["image_urls"] = inputs.get("images", [])
        
        elif tool_name == "generate_leads":
            params["location"] = inputs.get("location")
            params["keywords"] = ["tiger", "exotic animal", "wildlife"]
        
        elif tool_name == "relationship_analysis":
            params["facility_id"] = inputs.get("facility_id")
            params["tiger_id"] = inputs.get("tiger_id")
        
        elif tool_name == "data_extraction":
            params["files"] = inputs.get("files", [])
        
        elif tool_name == "youtube_search":
            facility = inputs.get("facility")
            location = inputs.get("location")
            if facility:
                params["query"] = f'"{facility}" tiger'
            elif location:
                params["query"] = f'tiger {location}'
            params["max_results"] = 10
        
        elif tool_name == "meta_search":
            facility = inputs.get("facility")
            if facility:
                params["query"] = facility
            params["limit"] = 10
        
        elif tool_name == "social_media_intelligence":
            params["facility_name"] = inputs.get("facility")
            params["location"] = inputs.get("location")
        
        return params

