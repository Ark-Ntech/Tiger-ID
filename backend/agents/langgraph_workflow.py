"""Langgraph workflow implementation for investigation orchestration"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated, Literal
from uuid import UUID
from sqlalchemy.orm import Session
import operator

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from backend.agents.research_agent import ResearchAgent
from backend.agents.analysis_agent import AnalysisAgent
from backend.agents.validation_agent import ValidationAgent
from backend.agents.reporting_agent import ReportingAgent
from backend.services.investigation_service import InvestigationService
from backend.services.event_service import get_event_service
from backend.services.notification_service import get_notification_service
from backend.events.event_types import EventType
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class InvestigationState(TypedDict):
    """State structure for investigation workflow"""
    investigation_id: str
    user_inputs: Dict[str, Any]
    parsed_inputs: Optional[Dict[str, Any]]
    research_results: Optional[Dict[str, Any]]
    analysis_results: Optional[Dict[str, Any]]
    validation_results: Optional[Dict[str, Any]]
    report: Optional[Dict[str, Any]]
    errors: Annotated[List[Dict[str, Any]], operator.add]
    phase: str
    status: Literal["running", "completed", "failed", "cancelled", "paused"]


class InvestigationWorkflow:
    """Langgraph workflow for investigation orchestration"""
    
    def __init__(
        self,
        db: Optional[Session] = None,
        research_agent: Optional[ResearchAgent] = None,
        analysis_agent: Optional[AnalysisAgent] = None,
        validation_agent: Optional[ValidationAgent] = None,
        reporting_agent: Optional[ReportingAgent] = None
    ):
        """
        Initialize investigation workflow
        
        Args:
            db: Database session
            research_agent: ResearchAgent instance (optional, will create if not provided)
            analysis_agent: AnalysisAgent instance (optional, will create if not provided)
            validation_agent: ValidationAgent instance (optional, will create if not provided)
            reporting_agent: ReportingAgent instance (optional, will create if not provided)
        """
        self.db = db
        self.research_agent = research_agent or ResearchAgent(db, skip_ml_models=True)
        self.analysis_agent = analysis_agent or AnalysisAgent(db)
        self.validation_agent = validation_agent or ValidationAgent(db)
        self.reporting_agent = reporting_agent or ReportingAgent(db)
        self.investigation_service = InvestigationService(db) if db else None
        self.event_service = get_event_service()
        self.notification_service = get_notification_service(db) if db else None
        
        # Initialize checkpointer before building graph (graph compilation needs it)
        self.checkpointer = MemorySaver()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the Langgraph StateGraph"""
        workflow = StateGraph(InvestigationState)
        
        # Add nodes
        workflow.add_node("parse_inputs", self._parse_inputs_node)
        workflow.add_node("research", self._research_node)
        workflow.add_node("analysis", self._analysis_node)
        workflow.add_node("validation", self._validation_node)
        workflow.add_node("reporting", self._reporting_node)
        workflow.add_node("complete", self._complete_node)
        
        # Add edges
        workflow.add_edge(START, "parse_inputs")
        workflow.add_edge("parse_inputs", "research")
        workflow.add_conditional_edges(
            "research",
            self._should_continue,
            {
                "continue": "analysis",
                "error": "complete",
                "skip": "analysis"  # Skip if no evidence found
            }
        )
        workflow.add_conditional_edges(
            "analysis",
            self._should_continue,
            {
                "continue": "validation",
                "error": "complete",
                "skip": "validation"  # Continue even with errors
            }
        )
        workflow.add_conditional_edges(
            "validation",
            self._should_continue,
            {
                "continue": "reporting",
                "error": "complete",
                "skip": "reporting"  # Continue even with errors
            }
        )
        workflow.add_edge("reporting", "complete")
        workflow.add_edge("complete", END)
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    async def _parse_inputs_node(self, state: InvestigationState) -> InvestigationState:
        """Parse and understand user inputs"""
        try:
            user_inputs = state["user_inputs"]
            
            parsed_inputs = {
                "images": user_inputs.get("images", []),
                "text": user_inputs.get("text", ""),
                "files": user_inputs.get("files", []),
                "location": user_inputs.get("location"),
                "facility": user_inputs.get("facility"),
                "tiger_id": user_inputs.get("tiger_id"),
                "query": user_inputs.get("query", "")
            }
            
            logger.info("Parsed user inputs", investigation_id=state["investigation_id"], parsed=parsed_inputs)
            
            # Emit event
            await self.event_service.emit(
                EventType.PHASE_STARTED.value,
                {"phase": "parse_inputs", "agent": "orchestrator"},
                investigation_id=state["investigation_id"]
            )
            
            # Log step
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    UUID(state["investigation_id"]),
                    step_type="parse_inputs",
                    agent_name="orchestrator",
                    status="completed"
                )
            
            return {
                **state,
                "parsed_inputs": parsed_inputs,
                "phase": "parse_inputs"
            }
        except Exception as e:
            logger.error("Parse inputs failed", investigation_id=state["investigation_id"], error=str(e))
            return {
                **state,
                "errors": [{"phase": "parse_inputs", "error": str(e)}],
                "status": "failed"
            }
    
    async def _research_node(self, state: InvestigationState) -> InvestigationState:
        """Research phase - gather information"""
        try:
            parsed_inputs = state.get("parsed_inputs", {})
            investigation_id = UUID(state["investigation_id"])
            
            # Emit phase started event
            await self.event_service.emit(
                EventType.PHASE_STARTED.value,
                {"phase": "research", "agent": "research_agent"},
                investigation_id=state["investigation_id"]
            )
            
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    investigation_id,
                    step_type="research_started",
                    agent_name="research_agent",
                    status="in_progress"
                )
            
            research_results = {
                "database": {},
                "external_apis": {},
                "evidence": [],
                "web_intelligence": {}
            }
            
            # Query database
            if parsed_inputs.get("tiger_id"):
                tiger_data = await self.research_agent.query_database(
                    "tiger",
                    {"tiger_id": parsed_inputs["tiger_id"]}
                )
                research_results["database"]["tiger"] = tiger_data
            
            if parsed_inputs.get("facility") or parsed_inputs.get("location"):
                facility_data = await self.research_agent.query_database(
                    "facility",
                    {
                        "facility_name": parsed_inputs.get("facility"),
                        "state": parsed_inputs.get("location")
                    }
                )
                research_results["database"]["facility"] = facility_data
            
            # Query external APIs
            api_data = await self.research_agent.query_external_apis(
                "all",
                {
                    "facility_name": parsed_inputs.get("facility"),
                    "state": parsed_inputs.get("location"),
                    "usda_license": parsed_inputs.get("usda_license")
                },
                sync_to_db=True,
                investigation_id=investigation_id
            )
            research_results["external_apis"] = api_data
            
            # Web intelligence gathering
            facility_name = parsed_inputs.get("facility")
            if facility_name:
                # Check reference facilities
                ref_matches = await self.research_agent.check_reference_facilities(
                    facility_name=facility_name,
                    usda_license=parsed_inputs.get("usda_license")
                )
                research_results["web_intelligence"]["reference_facility_matches"] = ref_matches
                
                # Web search
                search_query = f'"{facility_name}" tiger facility USDA'
                web_search_results = await self.research_agent.search_web(
                    query=search_query,
                    limit=10,
                    investigation_id=investigation_id
                )
                research_results["web_intelligence"]["web_search"] = web_search_results
                
                # Social media intelligence (if orchestrator available)
                # Note: This would need orchestrator reference for MCP tools
                # For now, use direct API access
                try:
                    social_media = await self.research_agent.get_social_media_intelligence(
                        facility_name=facility_name,
                        location=parsed_inputs.get("location"),
                        orchestrator=None  # Would need orchestrator reference
                    )
                    research_results["web_intelligence"]["social_media"] = social_media
                except Exception as e:
                    logger.warning("Social media intelligence failed", error=str(e))
            
            # Reverse image search
            if parsed_inputs.get("images"):
                image_urls = parsed_inputs.get("images", [])
                reverse_search_results = []
                for image_url in image_urls[:3]:  # Limit to 3 images
                    reverse_results = await self.research_agent.reverse_image_search(
                        image_url=image_url,
                        investigation_id=investigation_id
                    )
                    reverse_search_results.append(reverse_results)
                research_results["web_intelligence"]["reverse_image_search"] = reverse_search_results
            
            # Compile evidence
            evidence = []
            if research_results["database"].get("tiger"):
                evidence.append({
                    "type": "database",
                    "source_type": "database",
                    "content": research_results["database"]["tiger"],
                    "relevance_score": 0.9
                })
            
            if research_results["database"].get("facility"):
                evidence.append({
                    "type": "database",
                    "source_type": "database",
                    "content": research_results["database"]["facility"],
                    "relevance_score": 0.8
                })
            
            # Add external API evidence
            for api_name, api_data in research_results["external_apis"].items():
                if api_data:
                    evidence.append({
                        "type": "external_api",
                        "source_type": api_name,
                        "content": api_data,
                        "relevance_score": 0.7
                    })
            
            research_results["evidence"] = evidence
            
            # Emit phase completed event
            await self.event_service.emit(
                EventType.PHASE_COMPLETED.value,
                {
                    "phase": "research",
                    "agent": "research_agent",
                    "evidence_count": len(evidence)
                },
                investigation_id=state["investigation_id"]
            )
            
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    investigation_id,
                    step_type="research_completed",
                    agent_name="research_agent",
                    status="completed",
                    result={"evidence_count": len(evidence)}
                )
            
            return {
                **state,
                "research_results": research_results,
                "phase": "research"
            }
        except Exception as e:
            logger.error("Research phase failed", investigation_id=state["investigation_id"], error=str(e))
            return {
                **state,
                "research_results": {"evidence": [], "database": {}, "external_apis": {}},
                "errors": [{"phase": "research", "error": str(e)}],
                "phase": "research"
            }
    
    async def _analysis_node(self, state: InvestigationState) -> InvestigationState:
        """Analysis phase - analyze evidence"""
        try:
            research_results = state.get("research_results", {})
            evidence_items = research_results.get("evidence", [])
            investigation_id = UUID(state["investigation_id"])
            
            # Emit phase started event
            await self.event_service.emit(
                EventType.PHASE_STARTED.value,
                {"phase": "analysis", "agent": "analysis_agent"},
                investigation_id=state["investigation_id"]
            )
            
            # Analyze evidence
            analysis_results = await self.analysis_agent.analyze_evidence(
                evidence_items=evidence_items,
                context={"investigation_id": state["investigation_id"]}
            )
            
            # Emit phase completed event
            await self.event_service.emit(
                EventType.PHASE_COMPLETED.value,
                {
                    "phase": "analysis",
                    "agent": "analysis_agent",
                    "confidence": analysis_results.get("confidence", 0.0)
                },
                investigation_id=state["investigation_id"]
            )
            
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    investigation_id,
                    step_type="analysis_completed",
                    agent_name="analysis_agent",
                    status="completed",
                    result={"confidence": analysis_results.get("confidence", 0.0)}
                )
            
            return {
                **state,
                "analysis_results": analysis_results,
                "phase": "analysis"
            }
        except Exception as e:
            logger.error("Analysis phase failed", investigation_id=state["investigation_id"], error=str(e))
            return {
                **state,
                "analysis_results": {
                    "evidence_strength": "low",
                    "confidence": 0.3,
                    "trafficking_probability": 0.3
                },
                "errors": [{"phase": "analysis", "error": str(e)}],
                "phase": "analysis"
            }
    
    async def _validation_node(self, state: InvestigationState) -> InvestigationState:
        """Validation phase - verify findings"""
        try:
            research_results = state.get("research_results", {})
            analysis_results = state.get("analysis_results", {})
            evidence_items = research_results.get("evidence", [])
            investigation_id = UUID(state["investigation_id"])
            
            # Emit phase started event
            await self.event_service.emit(
                EventType.PHASE_STARTED.value,
                {"phase": "validation", "agent": "validation_agent"},
                investigation_id=state["investigation_id"]
            )
            
            # Validate evidence
            validation_results = await self.validation_agent.validate_evidence(
                evidence_items=evidence_items,
                sources=[item.get("source") for item in evidence_items if item.get("source")]
            )
            
            # Emit phase completed event
            await self.event_service.emit(
                EventType.PHASE_COMPLETED.value,
                {
                    "phase": "validation",
                    "agent": "validation_agent",
                    "confidence": validation_results.get("overall_confidence", 0.0)
                },
                investigation_id=state["investigation_id"]
            )
            
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    investigation_id,
                    step_type="validation_completed",
                    agent_name="validation_agent",
                    status="completed",
                    result={"overall_confidence": validation_results.get("overall_confidence", 0.0)}
                )
            
            return {
                **state,
                "validation_results": validation_results,
                "phase": "validation"
            }
        except Exception as e:
            logger.error("Validation phase failed", investigation_id=state["investigation_id"], error=str(e))
            return {
                **state,
                "validation_results": {
                    "overall_confidence": 0.3,
                    "issues": [],
                    "hallucinations": []
                },
                "errors": [{"phase": "validation", "error": str(e)}],
                "phase": "validation"
            }
    
    async def _reporting_node(self, state: InvestigationState) -> InvestigationState:
        """Reporting phase - compile report"""
        try:
            research_results = state.get("research_results", {})
            analysis_results = state.get("analysis_results", {})
            validation_results = state.get("validation_results", {})
            evidence_items = research_results.get("evidence", [])
            investigation_id = UUID(state["investigation_id"])
            
            # Emit phase started event
            await self.event_service.emit(
                EventType.PHASE_STARTED.value,
                {"phase": "reporting", "agent": "reporting_agent"},
                investigation_id=state["investigation_id"]
            )
            
            # Compile report
            report = await self.reporting_agent.compile_report(
                investigation_id=investigation_id,
                evidence_items=evidence_items,
                analysis=analysis_results,
                validation=validation_results
            )
            
            # Emit phase completed event
            await self.event_service.emit(
                EventType.PHASE_COMPLETED.value,
                {
                    "phase": "reporting",
                    "agent": "reporting_agent"
                },
                investigation_id=state["investigation_id"]
            )
            
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    investigation_id,
                    step_type="reporting_completed",
                    agent_name="reporting_agent",
                    status="completed"
                )
            
            return {
                **state,
                "report": report,
                "phase": "reporting"
            }
        except Exception as e:
            logger.error("Reporting phase failed", investigation_id=state["investigation_id"], error=str(e))
            research_results = state.get("research_results", {})
            evidence_items = research_results.get("evidence", [])
            return {
                **state,
                "report": {
                    "summary": f"Investigation completed with some errors. Found {len(evidence_items)} evidence items.",
                    "findings": [],
                    "recommendations": []
                },
                "errors": [{"phase": "reporting", "error": str(e)}],
                "phase": "reporting"
            }
    
    async def _complete_node(self, state: InvestigationState) -> InvestigationState:
        """Complete investigation"""
        try:
            investigation_id = UUID(state["investigation_id"])
            
            if self.investigation_service:
                investigation = self.investigation_service.complete_investigation(
                    investigation_id,
                    summary={
                        "report": state.get("report"),
                        "analysis": state.get("analysis_results"),
                        "validation": state.get("validation_results")
                    }
                )
                
                # Emit investigation completed event
                await self.event_service.emit(
                    EventType.INVESTIGATION_COMPLETED.value,
                    {
                        "investigation_id": state["investigation_id"],
                        "evidence_count": len(state.get("research_results", {}).get("evidence", [])),
                        "confidence": state.get("analysis_results", {}).get("confidence", 0.5)
                    },
                    investigation_id=state["investigation_id"]
                )
                
                # Create notification
                if self.notification_service and investigation and investigation.created_by:
                    try:
                        self.notification_service.create_investigation_notification(
                            user_id=investigation.created_by,
                            investigation_id=investigation_id,
                            notification_type="investigation_completed",
                            message=f"Investigation '{investigation.title}' has been completed.",
                            priority="high"
                        )
                    except Exception as e:
                        logger.warning("Failed to create notification", error=str(e))
            
            return {
                **state,
                "status": "completed",
                "phase": "complete"
            }
        except Exception as e:
            logger.error("Completion failed", investigation_id=state["investigation_id"], error=str(e))
            return {
                **state,
                "status": "failed",
                "errors": [{"phase": "complete", "error": str(e)}],
                "phase": "complete"
            }
    
    def _should_continue(self, state: InvestigationState) -> str:
        """Determine if workflow should continue based on state"""
        if state.get("status") in ["failed", "cancelled", "paused"]:
            return "error"
        
        # Check for errors in current phase
        errors = state.get("errors", [])
        if errors:
            current_phase = state.get("phase", "")
            if any(error.get("phase") == current_phase for error in errors):
                # Continue even with errors, but mark as having errors
                return "continue"
        
        return "continue"
    
    async def run(
        self,
        investigation_id: UUID,
        user_inputs: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run investigation workflow
        
        Args:
            investigation_id: Investigation ID
            user_inputs: User-provided inputs
            config: Optional configuration for graph execution
        
        Returns:
            Final state with investigation results
        """
        initial_state: InvestigationState = {
            "investigation_id": str(investigation_id),
            "user_inputs": user_inputs,
            "parsed_inputs": None,
            "research_results": None,
            "analysis_results": None,
            "validation_results": None,
            "report": None,
            "errors": [],
            "phase": "start",
            "status": "running"
        }
        
        # Start investigation
        try:
            if self.investigation_service:
                investigation = self.investigation_service.start_investigation(investigation_id)
                if not investigation:
                    raise ValueError("Investigation not found")
                
                # Emit investigation started event
                await self.event_service.emit(
                    EventType.INVESTIGATION_STARTED.value,
                    {
                        "investigation_id": str(investigation_id),
                        "title": investigation.title if investigation else "Unknown"
                    },
                    investigation_id=str(investigation_id)
                )
            
            # Run the graph
            if config is None:
                config = {"configurable": {"thread_id": str(investigation_id)}}
            
            # Execute graph and get final state
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            return final_state
        except Exception as e:
            logger.error("Workflow execution failed", investigation_id=str(investigation_id), error=str(e))
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    investigation_id,
                    step_type="workflow_error",
                    agent_name="orchestrator",
                    status="failed",
                    result={"error": str(e)}
                )
            raise
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get available MCP tools for use in Langgraph
        
        Returns:
            List of tool definitions
        """
        tools = []
        
        # Note: To fully integrate MCP tools, we would need to:
        # 1. Get orchestrator reference or MCP server instances
        # 2. Convert MCP tools to Langgraph-compatible tools
        # 3. Make them callable from graph nodes
        
        # For now, return empty list - tools are accessed via agents
        return tools

