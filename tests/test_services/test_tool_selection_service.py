"""Tests for ToolSelectionService"""

import pytest
from backend.services.tool_selection_service import ToolSelectionService


class TestToolSelectionService:
    """Tests for ToolSelectionService"""
    
    def test_init(self):
        """Test service initialization"""
        service = ToolSelectionService()
        
        assert len(service.available_tools) > 0
        assert "web_search" in service.available_tools
    
    def test_select_tools_with_query(self):
        """Test tool selection with text query"""
        service = ToolSelectionService()
        
        inputs = {"query": "tiger facility investigation"}
        tools = service.select_tools(inputs)
        
        assert "web_search" in tools
    
    def test_select_tools_with_facility(self):
        """Test tool selection with facility"""
        service = ToolSelectionService()
        
        inputs = {"facility": "Test Facility"}
        tools = service.select_tools(inputs)
        
        assert "news_search" in tools
        assert "youtube_search" in tools
        assert "meta_search" in tools
        assert "social_media_intelligence" in tools
        assert "check_reference_facilities" in tools
    
    def test_select_tools_with_location(self):
        """Test tool selection with location"""
        service = ToolSelectionService()
        
        inputs = {"location": "Los Angeles, CA"}
        tools = service.select_tools(inputs)
        
        assert "news_search" in tools
        assert "youtube_search" in tools
        assert "generate_leads" in tools
        assert "social_media_intelligence" in tools
    
    def test_select_tools_with_images(self):
        """Test tool selection with images"""
        service = ToolSelectionService()
        
        inputs = {"images": ["image1.jpg", "image2.jpg"]}
        tools = service.select_tools(inputs)
        
        assert "reverse_image_search" in tools
    
    def test_select_tools_with_tiger_id(self):
        """Test tool selection with tiger ID"""
        service = ToolSelectionService()
        
        inputs = {"tiger_id": "123"}
        tools = service.select_tools(inputs)
        
        assert "relationship_analysis" in tools
    
    def test_select_tools_with_files(self):
        """Test tool selection with files"""
        service = ToolSelectionService()
        
        inputs = {"files": ["doc1.pdf", "doc2.pdf"]}
        tools = service.select_tools(inputs)
        
        assert "data_extraction" in tools
    
    def test_select_tools_with_evidence_context(self):
        """Test tool selection with evidence context"""
        service = ToolSelectionService()
        
        inputs = {}
        context = {"evidence_count": 5}
        tools = service.select_tools(inputs, investigation_context=context)
        
        assert "evidence_compilation" in tools
    
    def test_select_tools_empty_inputs(self):
        """Test tool selection with empty inputs"""
        service = ToolSelectionService()
        
        inputs = {}
        tools = service.select_tools(inputs)
        
        # Should return empty list or minimal tools
        assert isinstance(tools, list)
    
    def test_should_use_web_search_with_keywords(self):
        """Test _should_use_web_search with relevant keywords"""
        service = ToolSelectionService()
        
        inputs = {"query": "tiger trafficking facility investigation"}
        result = service._should_use_web_search(inputs)
        
        assert result is True
    
    def test_should_use_web_search_without_keywords(self):
        """Test _should_use_web_search without relevant keywords"""
        service = ToolSelectionService()
        
        inputs = {"query": "test"}
        result = service._should_use_web_search(inputs)
        
        assert result is False
    
    def test_should_use_web_search_with_facility(self):
        """Test _should_use_web_search with facility"""
        service = ToolSelectionService()
        
        inputs = {"facility": "Test Facility"}
        result = service._should_use_web_search(inputs)
        
        assert result is True
    
    def test_get_tool_priority(self):
        """Test getting tool priority"""
        service = ToolSelectionService()
        
        priority = service.get_tool_priority("web_search", {})
        
        assert isinstance(priority, int)
        assert 1 <= priority <= 10
    
    def test_get_tool_priority_with_context(self):
        """Test getting tool priority with context"""
        service = ToolSelectionService()
        
        context = {"has_images": True}
        priority = service.get_tool_priority("reverse_image_search", context)
        
        assert priority == 9  # High priority with images
    
    def test_select_tools_comprehensive(self):
        """Test comprehensive tool selection"""
        service = ToolSelectionService()
        
        inputs = {
            "query": "tiger facility",
            "facility": "Test Facility",
            "location": "CA",
            "images": ["image.jpg"],
            "tiger_id": "123"
        }
        
        context = {"evidence_count": 3}
        tools = service.select_tools(inputs, investigation_context=context)
        
        # Should include multiple tools
        assert len(tools) > 5
        assert "web_search" in tools
        assert "news_search" in tools
        assert "reverse_image_search" in tools
        assert "relationship_analysis" in tools
        assert "evidence_compilation" in tools

