"""Tests for orchestrator agent"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.orchestrator import OrchestratorAgent
from backend.database import get_db_session, Investigation


@pytest.fixture
def orchestrator(db_session, mock_research_agent, mock_analysis_agent,
                 mock_validation_agent, mock_reporting_agent, mock_mcp_servers):
    """Orchestrator agent fixture with mocked dependencies"""
    # Create orchestrator with injected mock agents
    orch = OrchestratorAgent(
        db=db_session,
        research_agent=mock_research_agent,
        analysis_agent=mock_analysis_agent,
        validation_agent=mock_validation_agent,
        reporting_agent=mock_reporting_agent,
        skip_mcp_servers=True,  # Skip MCP server initialization
        skip_ml_models=True  # Skip ML model loading
    )
    
    # Manually set MCP servers to mocks
    orch.firecrawl_server = mock_mcp_servers.firecrawl
    orch.database_server = mock_mcp_servers.database
    orch.tiger_id_server = mock_mcp_servers.tiger_id
    orch.youtube_server = mock_mcp_servers.youtube
    orch.meta_server = mock_mcp_servers.meta
    
    return orch


class TestOrchestratorAgent:
    """Tests for OrchestratorAgent"""
    
    def test_init(self, orchestrator):
        """Test orchestrator initialization"""
        assert orchestrator.research_agent is not None
        assert orchestrator.analysis_agent is not None
        assert orchestrator.validation_agent is not None
        assert orchestrator.reporting_agent is not None
        assert orchestrator.firecrawl_server is not None
        assert orchestrator.database_server is not None
        assert orchestrator.tiger_id_server is not None
    
    @pytest.mark.asyncio
    async def test_parse_inputs(self, orchestrator):
        """Test parsing user inputs"""
        user_inputs = {
            "text": "Check if Facility XYZ is trafficking tigers",
            "images": [],
            "files": [],
            "location": "Texas",
            "facility": "XYZ Zoo"
        }
        
        parsed = await orchestrator._parse_inputs(user_inputs)
        
        assert "text" in parsed
        assert "location" in parsed
        assert "facility" in parsed
        assert parsed["facility"] == "XYZ Zoo"
    
    @pytest.mark.asyncio
    async def test_use_mcp_tool(self, orchestrator):
        """Test using MCP tools"""
        # Test database tool
        result = await orchestrator.use_mcp_tool(
            "database",
            "query_tigers",
            {"name": "test"}
        )
        
        assert "error" in result or "tigers" in result
    
    @pytest.mark.asyncio
    async def test_launch_investigation(self, orchestrator, sample_investigation_id):
        """Test launching an investigation"""
        from unittest.mock import Mock, AsyncMock
        
        # Mock investigation service to return an investigation
        mock_investigation = Mock()
        mock_investigation.investigation_id = sample_investigation_id
        mock_investigation.title = "Test Investigation"
        mock_investigation.status = "active"
        orchestrator.investigation_service = Mock()
        orchestrator.investigation_service.get_investigation = Mock(return_value=mock_investigation)
        orchestrator.investigation_service.start_investigation = Mock(return_value=mock_investigation)
        orchestrator.investigation_service.add_investigation_step = Mock()
        orchestrator.investigation_service.complete_investigation = Mock(return_value=mock_investigation)
        
        user_inputs = {
            "text": "Investigate Facility XYZ",
            "query": "Is this facility trafficking tigers?",
            "images": [],
            "files": [],
            "location": "Texas",
            "facility": "XYZ Zoo"
        }
        
        result = await orchestrator.launch_investigation(
            investigation_id=sample_investigation_id,
            user_inputs=user_inputs,
            context={}
        )
        
        assert "investigation_id" in result
        assert result["investigation_id"] == str(sample_investigation_id)
        assert "status" in result or "report" in result
    
    @pytest.mark.asyncio
    async def test_close(self, orchestrator):
        """Test closing orchestrator"""
        # Should not raise
        await orchestrator.close()

