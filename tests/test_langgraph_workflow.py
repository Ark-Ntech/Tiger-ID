"""Tests for Langgraph workflow implementation"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from backend.agents.langgraph_workflow import InvestigationWorkflow, InvestigationState


class TestInvestigationWorkflow:
    """Tests for InvestigationWorkflow"""
    
    @pytest.fixture
    def workflow(self, db_session, mock_research_agent, mock_analysis_agent, 
                 mock_validation_agent, mock_reporting_agent, mock_investigation_service,
                 mock_event_service, mock_notification_service):
        """Create workflow instance with mocked agents"""
        # Create workflow with injected mock agents
        workflow = InvestigationWorkflow(
            db=db_session,
            research_agent=mock_research_agent,
            analysis_agent=mock_analysis_agent,
            validation_agent=mock_validation_agent,
            reporting_agent=mock_reporting_agent
        )
        
        # Replace services with mocks
        workflow.investigation_service = mock_investigation_service
        workflow.event_service = mock_event_service
        workflow.notification_service = mock_notification_service
        
        return workflow
    
    @pytest.mark.asyncio
    async def test_workflow_initialization(self, workflow):
        """Test workflow initialization"""
        assert workflow is not None
        assert workflow.research_agent is not None
        assert workflow.analysis_agent is not None
        assert workflow.validation_agent is not None
        assert workflow.reporting_agent is not None
    
    @pytest.mark.asyncio
    async def test_parse_inputs_node(self, workflow):
        """Test parse inputs node"""
        state: InvestigationState = {
            "investigation_id": str(uuid4()),
            "user_inputs": {
                "text": "test query",
                "facility": "Test Facility",
                "location": "CA"
            },
            "parsed_inputs": None,
            "research_results": None,
            "analysis_results": None,
            "validation_results": None,
            "report": None,
            "errors": [],
            "phase": "start",
            "status": "running"
        }
        
        # Mocks are already configured via fixtures
        result = await workflow._parse_inputs_node(state)
        
        assert result["parsed_inputs"] is not None
        assert result["parsed_inputs"]["facility"] == "Test Facility"
        assert result["parsed_inputs"]["location"] == "CA"
        assert result["phase"] == "parse_inputs"
    
    @pytest.mark.asyncio
    async def test_research_node(self, workflow):
        """Test research node"""
        state: InvestigationState = {
            "investigation_id": str(uuid4()),
            "user_inputs": {},
            "parsed_inputs": {
                "facility": "Test Facility",
                "location": "CA"
            },
            "research_results": None,
            "analysis_results": None,
            "validation_results": None,
            "report": None,
            "errors": [],
            "phase": "parse_inputs",
            "status": "running"
        }
        
        # Mock research agent methods  
        workflow.research_agent.query_database = AsyncMock(return_value={})
        workflow.research_agent.query_external_apis = AsyncMock(return_value={})
        workflow.research_agent.check_reference_facilities = AsyncMock(return_value={"has_reference_match": False})
        workflow.research_agent.search_web = AsyncMock(return_value={"results": []})
        workflow.research_agent.get_social_media_intelligence = AsyncMock(return_value={"youtube": {}, "meta": {}})
        workflow.research_agent.reverse_image_search = AsyncMock(return_value={"matches": []})
        
        # Mocks already configured via fixtures
        result = await workflow._research_node(state)
        
        assert result["research_results"] is not None
        assert "evidence" in result["research_results"]
        assert result["phase"] == "research"
    
    @pytest.mark.asyncio
    async def test_analysis_node(self, workflow):
        """Test analysis node"""
        state: InvestigationState = {
            "investigation_id": str(uuid4()),
            "user_inputs": {},
            "parsed_inputs": {},
            "research_results": {
                "evidence": [{"type": "database", "content": {"test": "data"}}]
            },
            "analysis_results": None,
            "validation_results": None,
            "report": None,
            "errors": [],
            "phase": "research",
            "status": "running"
        }
        
        # Mock analysis agent
        workflow.analysis_agent.analyze_evidence = AsyncMock(return_value={
            "confidence": 0.8,
            "trafficking_probability": 0.7,
            "evidence_strength": "moderate"
        })
        
        # Mocks already configured via fixtures
        result = await workflow._analysis_node(state)
        
        assert result["analysis_results"] is not None
        assert result["analysis_results"]["confidence"] == 0.8
        assert result["phase"] == "analysis"
    
    @pytest.mark.asyncio
    async def test_validation_node(self, workflow):
        """Test validation node"""
        state: InvestigationState = {
            "investigation_id": str(uuid4()),
            "user_inputs": {},
            "parsed_inputs": {},
            "research_results": {
                "evidence": [{"type": "database", "content": {"test": "data"}}]
            },
            "analysis_results": {
                "confidence": 0.8
            },
            "validation_results": None,
            "report": None,
            "errors": [],
            "phase": "analysis",
            "status": "running"
        }
        
        # Mock validation agent
        workflow.validation_agent.validate_evidence = AsyncMock(return_value={
            "overall_confidence": 0.75,
            "issues": [],
            "hallucinations": []
        })
        
        # Mocks already configured via fixtures
        result = await workflow._validation_node(state)
        
        assert result["validation_results"] is not None
        assert result["validation_results"]["overall_confidence"] == 0.75
        assert result["phase"] == "validation"
    
    @pytest.mark.asyncio
    async def test_reporting_node(self, workflow):
        """Test reporting node"""
        state: InvestigationState = {
            "investigation_id": str(uuid4()),
            "user_inputs": {},
            "parsed_inputs": {},
            "research_results": {
                "evidence": [{"type": "database", "content": {"test": "data"}}]
            },
            "analysis_results": {
                "confidence": 0.8
            },
            "validation_results": {
                "overall_confidence": 0.75
            },
            "report": None,
            "errors": [],
            "phase": "validation",
            "status": "running"
        }
        
        # Mock reporting agent
        workflow.reporting_agent.compile_report = AsyncMock(return_value={
            "summary": "Test report",
            "findings": [],
            "recommendations": []
        })
        
        # Mocks already configured via fixtures
        result = await workflow._reporting_node(state)
        
        assert result["report"] is not None
        assert result["report"]["summary"] == "Test report"
        assert result["phase"] == "reporting"
    
    @pytest.mark.asyncio
    async def test_complete_node(self, workflow):
        """Test complete node"""
        investigation_id = uuid4()
        state: InvestigationState = {
            "investigation_id": str(investigation_id),
            "user_inputs": {},
            "parsed_inputs": {},
            "research_results": {
                "evidence": [{"type": "database", "content": {"test": "data"}}]
            },
            "analysis_results": {
                "confidence": 0.8
            },
            "validation_results": {
                "overall_confidence": 0.75
            },
            "report": {
                "summary": "Test report"
            },
            "errors": [],
            "phase": "reporting",
            "status": "running"
        }
        
        # Mock investigation service
        mock_investigation = Mock()
        mock_investigation.created_by = uuid4()
        mock_investigation.title = "Test Investigation"
        
        workflow.investigation_service.complete_investigation = Mock(return_value=mock_investigation)
        workflow.notification_service.create_investigation_notification = Mock(return_value=None)
        
        # Mocks already configured via fixtures
        result = await workflow._complete_node(state)
        
        assert result["status"] == "completed"
        assert result["phase"] == "complete"
    
    @pytest.mark.asyncio
    async def test_should_continue(self, workflow):
        """Test should_continue conditional function"""
        # Test continue
        state: InvestigationState = {
            "investigation_id": str(uuid4()),
            "user_inputs": {},
            "parsed_inputs": {},
            "research_results": None,
            "analysis_results": None,
            "validation_results": None,
            "report": None,
            "errors": [],
            "phase": "research",
            "status": "running"
        }
        
        result = workflow._should_continue(state)
        assert result == "continue"
        
        # Test error state
        state["status"] = "failed"
        result = workflow._should_continue(state)
        assert result == "error"
        
        # Test with errors
        state["status"] = "running"
        state["errors"] = [{"phase": "research", "error": "test error"}]
        result = workflow._should_continue(state)
        assert result == "continue"  # Continues even with errors
    
    @pytest.mark.asyncio
    async def test_run_workflow(self, workflow):
        """Test running the complete workflow"""
        investigation_id = uuid4()
        user_inputs = {
            "facility": "Test Facility",
            "location": "CA"
        }
        
        # Mock all agents and services
        workflow.research_agent.query_database = AsyncMock(return_value={})
        workflow.research_agent.query_external_apis = AsyncMock(return_value={})
        workflow.research_agent.check_reference_facilities = AsyncMock(return_value={"has_reference_match": False})
        workflow.research_agent.search_web = AsyncMock(return_value={"results": []})
        workflow.research_agent.get_social_media_intelligence = AsyncMock(return_value={"youtube": {}, "meta": {}})
        workflow.analysis_agent.analyze_evidence = AsyncMock(return_value={"confidence": 0.8})
        workflow.validation_agent.validate_evidence = AsyncMock(return_value={"overall_confidence": 0.75})
        workflow.reporting_agent.compile_report = AsyncMock(return_value={"summary": "Test"})
        
        workflow.investigation_service.start_investigation = Mock(return_value=Mock(title="Test"))
        workflow.investigation_service.complete_investigation = Mock(return_value=Mock(created_by=uuid4(), title="Test"))
        
        # Mock graph.ainvoke to return a completed state
        with patch.object(workflow.graph, 'ainvoke', new_callable=AsyncMock) as mock_ainvoke:
            # Mock final state
            final_state: InvestigationState = {
                "investigation_id": str(investigation_id),
                "user_inputs": user_inputs,
                "parsed_inputs": {"facility": "Test Facility"},
                "research_results": {"evidence": []},
                "analysis_results": {"confidence": 0.8},
                "validation_results": {"overall_confidence": 0.75},
                "report": {"summary": "Test"},
                "errors": [],
                "phase": "complete",
                "status": "completed"
            }
            mock_ainvoke.return_value = final_state
            
            result = await workflow.run(investigation_id, user_inputs)
            
            assert result["status"] == "completed"
            assert result["report"] is not None
            mock_ainvoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_in_nodes(self, workflow):
        """Test error handling in workflow nodes"""
        state: InvestigationState = {
            "investigation_id": str(uuid4()),
            "user_inputs": {},
            "parsed_inputs": {},
            "research_results": None,
            "analysis_results": None,
            "validation_results": None,
            "report": None,
            "errors": [],
            "phase": "start",
            "status": "running"
        }
        
        # Test research node error handling
        workflow.research_agent.query_database = AsyncMock(side_effect=Exception("Test error"))
        
        # Mocks already configured via fixtures
        result = await workflow._research_node(state)
        
        assert result["research_results"] is not None
        assert len(result["errors"]) > 0
        assert result["errors"][0]["phase"] == "research"
    
    def test_get_tools(self, workflow):
        """Test get_tools method"""
        tools = workflow.get_tools()
        
        # Tools list should be returned (even if empty)
        assert isinstance(tools, list)

