"""OmniVinci Orchestrator Agent for coordinating investigations"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from backend.config.settings import get_settings
from backend.agents.research_agent import ResearchAgent
from backend.agents.analysis_agent import AnalysisAgent
from backend.agents.validation_agent import ValidationAgent
from backend.agents.reporting_agent import ReportingAgent
from backend.services.investigation_service import InvestigationService
from backend.services.event_service import get_event_service
from backend.services.notification_service import get_notification_service
from backend.services.tool_selection_service import ToolSelectionService
from backend.events.event_types import EventType, create_event
from backend.utils.error_handler import handle_error, retry_on_error, fallback_on_error
from backend.utils.error_types import ErrorCategory
from backend.mcp_servers.firecrawl_server import FirecrawlMCPServer
from backend.mcp_servers.database_server import DatabaseMCPServer
from backend.mcp_servers.tiger_id_server import TigerIDMCPServer
from backend.mcp_servers.youtube_server import YouTubeMCPServer
from backend.mcp_servers.meta_server import MetaMCPServer
from backend.database import get_db_session
from backend.utils.logging import get_logger

# Puppeteer is optional (requires playwright)
try:
    from backend.mcp_servers.puppeteer_server import PuppeteerMCPServer
    HAS_PUPPETEER = True
except ImportError:
    PuppeteerMCPServer = None
    HAS_PUPPETEER = False
from backend.agents.langgraph_workflow import InvestigationWorkflow

logger = get_logger(__name__)


class OrchestratorAgent:
    """Orchestrator agent coordinating multi-agent investigation workflow"""
    
    def __init__(
        self, 
        db: Optional[Session] = None, 
        omnivinci_api_key: Optional[str] = None,
        research_agent: Optional[ResearchAgent] = None,
        analysis_agent: Optional[AnalysisAgent] = None,
        validation_agent: Optional[ValidationAgent] = None,
        reporting_agent: Optional[ReportingAgent] = None,
        skip_mcp_servers: bool = False,
        skip_ml_models: bool = False
    ):
        """
        Initialize Orchestrator Agent
        
        Args:
            db: Database session (optional, will create if not provided)
            omnivinci_api_key: OmniVinci API key (optional)
            research_agent: ResearchAgent instance (optional, for testing)
            analysis_agent: AnalysisAgent instance (optional, for testing)
            validation_agent: ValidationAgent instance (optional, for testing)
            reporting_agent: ReportingAgent instance (optional, for testing)
            skip_mcp_servers: Skip MCP server initialization (for testing)
            skip_ml_models: Skip ML model initialization (for testing)
        """
        self.db = db or None
        settings = get_settings()
        self.omnivinci_api_key = omnivinci_api_key or settings.omnivinci.api_key
        
        # Log OmniVinci status
        if not self.omnivinci_api_key:
            logger.warning("OmniVinci API key not configured - multi-modal features will be limited")
            logger.info("Set OMNIVINCI_API_KEY to enable OmniVinci multi-modal understanding")
        else:
            logger.info("OmniVinci API key configured")
        
        # Initialize specialized agents (allow injection for testing)
        if research_agent:
            self.research_agent = research_agent
        else:
            self.research_agent = ResearchAgent(db, skip_ml_models=skip_ml_models)
            
        if analysis_agent:
            self.analysis_agent = analysis_agent
        else:
            self.analysis_agent = AnalysisAgent(db)
            
        if validation_agent:
            self.validation_agent = validation_agent
        else:
            self.validation_agent = ValidationAgent(db)
            
        if reporting_agent:
            self.reporting_agent = reporting_agent
        else:
            self.reporting_agent = ReportingAgent(db)
        
        # Initialize MCP servers (optional for testing)
        if not skip_mcp_servers:
            self.firecrawl_server = FirecrawlMCPServer()
            self.database_server = DatabaseMCPServer(db)
            self.tiger_id_server = TigerIDMCPServer()
            self.youtube_server = YouTubeMCPServer()
            self.meta_server = MetaMCPServer()
            
            # Puppeteer is optional (requires playwright)
            if HAS_PUPPETEER and settings.puppeteer.enabled:
                self.puppeteer_server = PuppeteerMCPServer()
                logger.info("Puppeteer MCP server initialized")
            else:
                self.puppeteer_server = None
                if not HAS_PUPPETEER:
                    logger.info("Puppeteer not available (playwright not installed)")
                elif not settings.puppeteer.enabled:
                    logger.info("Puppeteer disabled in settings")
        else:
            self.firecrawl_server = None
            self.database_server = None
            self.tiger_id_server = None
            self.puppeteer_server = None
            self.youtube_server = None
            self.meta_server = None
        
        # Initialize investigation service
        if db:
            self.investigation_service = InvestigationService(db)
        else:
            self.investigation_service = None
        
        # Initialize event service
        self.event_service = get_event_service()
        
        # Initialize notification service (if db available)
        if db:
            self.notification_service = get_notification_service(db)
        else:
            self.notification_service = None
        
        # Initialize tool selection service
        self.tool_selection_service = ToolSelectionService()
        
        # Initialize Langgraph workflow (optional, feature flag)
        settings = get_settings()
        self.use_langgraph = settings.use_langgraph
        self.langgraph_workflow = None
        if self.use_langgraph:
            try:
                self.langgraph_workflow = InvestigationWorkflow(
                    db=db,
                    research_agent=self.research_agent,
                    analysis_agent=self.analysis_agent,
                    validation_agent=self.validation_agent,
                    reporting_agent=self.reporting_agent
                )
                logger.info("Langgraph workflow initialized")
            except Exception as e:
                logger.warning("Failed to initialize Langgraph workflow, using default orchestrator", error=str(e))
                self.use_langgraph = False
    
    async def launch_investigation(
        self,
        investigation_id: UUID,
        user_inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Launch a complete investigation workflow
        
        Args:
            investigation_id: Investigation ID
            user_inputs: User-provided inputs (images, text, files, etc.)
            context: Additional context
            
        Returns:
            Investigation results
        """
        if not self.db:
            with get_db_session() as session:
                self.db = session
                self.research_agent.db = session
                self.analysis_agent.db = session
                self.validation_agent.db = session
                self.reporting_agent.db = session
                self.investigation_service = InvestigationService(session)
                self.notification_service = get_notification_service(session)
        
        # Check investigation status before starting
        investigation = self.investigation_service.get_investigation(investigation_id)
        if not investigation:
            raise ValueError("Investigation not found")
        
        if investigation.status == "paused":
            raise ValueError("Investigation is paused. Resume it to continue.")
        if investigation.status == "cancelled":
            raise ValueError("Investigation is cancelled.")
        
        # Start investigation
        investigation = self.investigation_service.start_investigation(investigation_id)
        
        # Check for cancellation/pause during execution
        def check_status():
            """Check if investigation was cancelled or paused"""
            inv = self.investigation_service.get_investigation(investigation_id)
            return inv and inv.status in ["cancelled", "paused"]
        
        # Emit investigation started event
        await self.event_service.emit(
            EventType.INVESTIGATION_STARTED.value,
            {
                "investigation_id": str(investigation_id),
                "title": investigation.title if investigation else "Unknown"
            },
            investigation_id=str(investigation_id)
        )
        
        # Log step
        self.investigation_service.add_investigation_step(
            investigation_id,
            step_type="investigation_started",
            agent_name="orchestrator",
            status="completed"
        )
        
        # Step 1: Parse and understand inputs
        try:
            parsed_inputs = await self._parse_inputs(user_inputs)
        except Exception as e:
            error_info = handle_error(e, ErrorCategory.RECOVERABLE, str(investigation_id), "orchestrator")
            await self.event_service.emit(
                EventType.ERROR_OCCURRED.value,
                {"error": error_info.__dict__, "phase": "parse_inputs"},
                investigation_id=str(investigation_id)
            )
            raise
        
        if check_status():
            raise ValueError("Investigation was cancelled or paused")
        
        # Step 2: Research phase - gather information
        try:
            research_results = await self._research_phase(parsed_inputs, investigation_id)
        except Exception as e:
            error_info = handle_error(e, ErrorCategory.RETRYABLE, str(investigation_id), "research_agent")
            await self.event_service.emit(
                EventType.ERROR_OCCURRED.value,
                {"error": error_info.__dict__, "phase": "research"},
                investigation_id=str(investigation_id)
            )
            # Try to continue with empty results
            research_results = {"evidence": [], "database": {}, "external_apis": {}}
            logger.warning("Continuing with empty research results after error")
        
        if check_status():
            raise ValueError("Investigation was cancelled or paused")
        
        # Step 3: Analysis phase - analyze evidence
        try:
            analysis_results = await self._analysis_phase(research_results, investigation_id)
        except Exception as e:
            error_info = handle_error(e, ErrorCategory.RETRYABLE, str(investigation_id), "analysis_agent")
            await self.event_service.emit(
                EventType.ERROR_OCCURRED.value,
                {"error": error_info.__dict__, "phase": "analysis"},
                investigation_id=str(investigation_id)
            )
            # Use default analysis results
            analysis_results = {
                "evidence_strength": "low",
                "confidence": 0.3,
                "trafficking_probability": 0.3
            }
            logger.warning("Continuing with default analysis results after error")
        
        if check_status():
            raise ValueError("Investigation was cancelled or paused")
        
        # Step 4: Validation phase - verify findings
        try:
            validation_results = await self._validation_phase(analysis_results, investigation_id)
        except Exception as e:
            error_info = handle_error(e, ErrorCategory.RECOVERABLE, str(investigation_id), "validation_agent")
            await self.event_service.emit(
                EventType.ERROR_OCCURRED.value,
                {"error": error_info.__dict__, "phase": "validation"},
                investigation_id=str(investigation_id)
            )
            # Use default validation results
            validation_results = {
                "overall_confidence": 0.3,
                "issues": [],
                "hallucinations": []
            }
            logger.warning("Continuing with default validation results after error")
        
        if check_status():
            raise ValueError("Investigation was cancelled or paused")
        
        # Step 5: Reporting phase - compile report
        try:
            report = await self._reporting_phase(
                investigation_id,
                research_results,
                analysis_results,
                validation_results
            )
        except Exception as e:
            error_info = handle_error(e, ErrorCategory.RETRYABLE, str(investigation_id), "reporting_agent")
            await self.event_service.emit(
                EventType.ERROR_OCCURRED.value,
                {"error": error_info.__dict__, "phase": "reporting"},
                investigation_id=str(investigation_id)
            )
            # Create basic report
            report = {
                "summary": f"Investigation completed with some errors. Found {len(research_results.get('evidence', []))} evidence items.",
                "findings": [],
                "recommendations": []
            }
            logger.warning("Continuing with basic report after error")
        
        if check_status():
            raise ValueError("Investigation was cancelled or paused")
        
        # Complete investigation
        investigation = self.investigation_service.complete_investigation(
            investigation_id,
            summary={
                "report": report,
                "analysis": analysis_results,
                "validation": validation_results
            }
        )
        
        # Emit investigation completed event
        await self.event_service.emit(
            EventType.INVESTIGATION_COMPLETED.value,
            {
                "investigation_id": str(investigation_id),
                "evidence_count": len(research_results.get("evidence", [])),
                "confidence": analysis_results.get("confidence", 0.5)
            },
            investigation_id=str(investigation_id)
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
                logger.error(f"Error creating notification: {e}")
        
        return {
            "investigation_id": str(investigation_id),
            "status": "completed",
            "report": report,
            "analysis": analysis_results,
            "validation": validation_results,
            "evidence": research_results.get("evidence", [])
        }
    
    async def _parse_inputs(self, user_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and understand user inputs"""
        parsed = {
            "images": user_inputs.get("images", []),
            "text": user_inputs.get("text", ""),
            "files": user_inputs.get("files", []),
            "location": user_inputs.get("location"),
            "facility": user_inputs.get("facility"),
            "tiger_id": user_inputs.get("tiger_id"),
            "query": user_inputs.get("query", "")
        }
        
        # Use OmniVinci to understand query if available
        # For now, simple parsing
        logger.info("Parsed user inputs", parsed=parsed)
        
        return parsed
    
    async def _research_phase(
        self,
        inputs: Dict[str, Any],
        investigation_id: UUID
    ) -> Dict[str, Any]:
        """Research phase - gather information"""
        # Emit phase started event
        await self.event_service.emit(
            EventType.PHASE_STARTED.value,
            {
                "phase": "research",
                "agent": "research_agent"
            },
            investigation_id=str(investigation_id)
        )
        
        self.investigation_service.add_investigation_step(
            investigation_id,
            step_type="research_started",
            agent_name="research_agent",
            status="in_progress"
        )
        
        research_results = {
            "database": {},
            "external_apis": {},
            "evidence": []
        }
        
        # Query database
        if inputs.get("tiger_id"):
            tiger_data = await self.research_agent.query_database(
                "tiger",
                {"tiger_id": inputs["tiger_id"]}
            )
            research_results["database"]["tiger"] = tiger_data
        
        if inputs.get("facility") or inputs.get("location"):
            facility_data = await self.research_agent.query_database(
                "facility",
                {
                    "facility_name": inputs.get("facility"),
                    "state": inputs.get("location")
                }
            )
            research_results["database"]["facility"] = facility_data
        
        # Query external APIs (with sync to database)
        api_data = await self.research_agent.query_external_apis(
            "all",
            {
                "facility_name": inputs.get("facility"),
                "state": inputs.get("location"),
                "usda_license": inputs.get("usda_license")
            },
            sync_to_db=True,
            investigation_id=investigation_id
        )
        research_results["external_apis"] = api_data
        
        # Web intelligence gathering
        web_intelligence = {}
        
        # Check if facility is in reference dataset
        facility_name = inputs.get("facility")
        usda_license = inputs.get("usda_license")
        if facility_name or usda_license:
            ref_matches = await self.research_agent.check_reference_facilities(
                facility_name=facility_name,
                usda_license=usda_license
            )
            web_intelligence["reference_facility_matches"] = ref_matches
            
            # If matches reference facility, boost priority
            if ref_matches.get("has_reference_match"):
                # Search for news about this facility
                news_query = f'"{facility_name}" tiger' if facility_name else None
                if news_query:
                    news_results = await self.research_agent.search_news(
                        query=news_query,
                        days=30,
                        limit=10,
                        investigation_id=investigation_id
                    )
                    web_intelligence["news_articles"] = news_results
        
        # Web search for facility if mentioned
        if facility_name:
            search_query = f'"{facility_name}" tiger facility USDA'
            web_search_results = await self.research_agent.search_web(
                query=search_query,
                limit=10,
                investigation_id=investigation_id
            )
            web_intelligence["web_search"] = web_search_results
        
        # Reverse image search if tiger image provided
        if inputs.get("images"):
            image_urls = inputs.get("images", [])
            reverse_search_results = []
            for image_url in image_urls[:3]:  # Limit to 3 images
                reverse_results = await self.research_agent.reverse_image_search(
                    image_url=image_url,
                    investigation_id=investigation_id
                )
                reverse_search_results.append(reverse_results)
            web_intelligence["reverse_image_search"] = reverse_search_results
        
        # Generate leads if location specified
        location = inputs.get("location")
        if location:
            leads = await self.research_agent.generate_leads(
                location=location,
                investigation_id=investigation_id
            )
            web_intelligence["leads"] = leads
        
        research_results["web_intelligence"] = web_intelligence
        
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
                "relevance_score": 0.9 if web_intelligence.get("reference_facility_matches", {}).get("has_reference_match") else 0.8
            })
        
        # Add API evidence
        if research_results["external_apis"].get("usda_inspections"):
            for inspection in research_results["external_apis"]["usda_inspections"][:5]:
                evidence.append({
                    "type": "api",
                    "source_type": "web_search",
                    "source_url": f"https://usda.gov/inspections/{inspection.get('id', '')}",
                    "content": inspection,
                    "extracted_text": str(inspection),
                    "relevance_score": 0.7
                })
        
        # Add web intelligence evidence
        if web_intelligence.get("news_articles"):
            for article in web_intelligence["news_articles"].get("articles", [])[:5]:
                evidence.append({
                    "type": "news",
                    "source_type": "web_search",
                    "source_url": article.get("url", ""),
                    "content": article,
                    "extracted_text": article.get("snippet", ""),
                    "relevance_score": 0.8 if ref_matches.get("has_reference_match") else 0.7
                })
        
        if web_intelligence.get("web_search"):
            for result in web_intelligence["web_search"].get("results", [])[:5]:
                evidence.append({
                    "type": "web_search",
                    "source_type": "web_search",
                    "source_url": result.get("url", ""),
                    "content": result,
                    "extracted_text": result.get("snippet", ""),
                    "relevance_score": 0.6
                })
        
        if web_intelligence.get("leads"):
            leads_data = web_intelligence["leads"]
            for listing in leads_data.get("listings", [])[:5]:
                if listing.get("suspicious_score", 0) > 0.7:
                    evidence.append({
                        "type": "lead",
                        "source_type": "web_search",
                        "source_url": listing.get("url", ""),
                        "content": listing,
                        "extracted_text": listing.get("snippet", ""),
                        "relevance_score": listing.get("suspicious_score", 0.7)
                    })
        
        research_results["evidence"] = evidence
        
        # Log step completion
        self.investigation_service.add_investigation_step(
            investigation_id,
            step_type="research_completed",
            agent_name="research_agent",
            status="completed",
            result={"evidence_count": len(evidence)}
        )
        
        # Emit phase completed event
        await self.event_service.emit(
            EventType.PHASE_COMPLETED.value,
            {
                "phase": "research",
                "agent": "research_agent",
                "evidence_count": len(evidence)
            },
            investigation_id=str(investigation_id)
        )
        
        # Emit evidence found events and create notifications
        if self.notification_service:
            investigation = self.investigation_service.get_investigation(investigation_id)
            if investigation and investigation.created_by:
                high_priority_evidence = [
                    ev for ev in evidence[:5]
                    if ev.get("relevance_score", 0) > 0.7
                ]
                
                if high_priority_evidence:
                    try:
                        self.notification_service.create_investigation_notification(
                            user_id=investigation.created_by,
                            investigation_id=investigation_id,
                            notification_type="evidence_found",
                            message=f"Found {len(high_priority_evidence)} high-priority evidence items.",
                            priority="high"
                        )
                    except Exception as e:
                        logger.error(f"Error creating evidence notification: {e}")
        
        # Emit evidence found events
        for ev in evidence[:10]:  # Limit to first 10 to avoid spam
            await self.event_service.emit(
                EventType.EVIDENCE_FOUND.value,
                {
                    "source_type": ev.get("source_type", "unknown"),
                    "relevance_score": ev.get("relevance_score", 0.5),
                    "url": ev.get("source_url")
                },
                investigation_id=str(investigation_id)
            )
        
        return research_results
    
    async def _analysis_phase(
        self,
        research_results: Dict[str, Any],
        investigation_id: UUID
    ) -> Dict[str, Any]:
        """Analysis phase - analyze evidence"""
        # Emit phase started event
        await self.event_service.emit(
            EventType.PHASE_STARTED.value,
            {
                "phase": "analysis",
                "agent": "analysis_agent"
            },
            investigation_id=str(investigation_id)
        )
        
        # Emit agent started event
        await self.event_service.emit(
            EventType.AGENT_STARTED.value,
            {
                "agent": "analysis_agent",
                "action": "analyzing_evidence",
                "evidence_count": len(research_results.get("evidence", []))
            },
            investigation_id=str(investigation_id)
        )
        
        self.investigation_service.add_investigation_step(
            investigation_id,
            step_type="analysis_started",
            agent_name="analysis_agent",
            status="in_progress"
        )
        
        evidence_items = research_results.get("evidence", [])
        
        # Analyze evidence
        analysis = await self.analysis_agent.analyze_evidence(evidence_items)
        
        # Check for contradictions
        contradictions = await self.analysis_agent.identify_contradictions(evidence_items)
        analysis["contradictions"] = contradictions
        
        # Assess trafficking probability
        probability = await self.analysis_agent.assess_trafficking_probability(
            evidence_items,
            analysis
        )
        analysis["trafficking_probability"] = probability
        
        # Log step completion
        self.investigation_service.add_investigation_step(
            investigation_id,
            step_type="analysis_completed",
            agent_name="analysis_agent",
            status="completed",
            result={
                "evidence_strength": analysis["evidence_strength"],
                "confidence": analysis["confidence"]
            }
        )
        
        # Emit agent completed and phase completed events
        await self.event_service.emit(
            EventType.AGENT_COMPLETED.value,
            {
                "agent": "analysis_agent",
                "action": "evidence_analysis_completed",
                "confidence": analysis.get("confidence", 0.5),
                "evidence_strength": analysis.get("evidence_strength", "medium"),
                "reasoning": f"Analyzed {len(research_results.get('evidence', []))} evidence items. Found evidence strength: {analysis.get('evidence_strength', 'medium')}, confidence: {analysis.get('confidence', 0.5):.2f}"
            },
            investigation_id=str(investigation_id)
        )
        
        await self.event_service.emit(
            EventType.PHASE_COMPLETED.value,
            {
                "phase": "analysis",
                "agent": "analysis_agent",
                "confidence": analysis.get("confidence", 0.5)
            },
            investigation_id=str(investigation_id)
        )
        
        return analysis
    
    async def _validation_phase(
        self,
        analysis_results: Dict[str, Any],
        investigation_id: UUID
    ) -> Dict[str, Any]:
        """Validation phase - verify findings"""
        # Emit phase and agent started events
        await self.event_service.emit(
            EventType.PHASE_STARTED.value,
            {"phase": "validation", "agent": "validation_agent"},
            investigation_id=str(investigation_id)
        )
        
        await self.event_service.emit(
            EventType.AGENT_STARTED.value,
            {"agent": "validation_agent", "action": "validating_findings"},
            investigation_id=str(investigation_id)
        )
        
        self.investigation_service.add_investigation_step(
            investigation_id,
            step_type="validation_started",
            agent_name="validation_agent",
            status="in_progress"
        )
        
        # For now, use analysis evidence
        evidence_items = analysis_results.get("evidence_items", [])
        
        # Validate evidence
        validation = await self.validation_agent.validate_evidence(evidence_items)
        
        # Check for hallucinations
        findings = {
            "claims": [
                {
                    "text": indicator.get("description", ""),
                    "sources": [item.get("source_url") for item in evidence_items if item.get("source_url")]
                }
                for indicator in analysis_results.get("trafficking_indicators", [])
            ]
        }
        
        hallucinations = await self.validation_agent.check_for_hallucinations(
            findings,
            evidence_items
        )
        validation["hallucinations"] = hallucinations
        
        # Log step completion
        self.investigation_service.add_investigation_step(
            investigation_id,
            step_type="validation_completed",
            agent_name="validation_agent",
            status="completed",
            result={
                "overall_confidence": validation["overall_confidence"],
                "issues": len(validation["issues"])
            }
        )
        
        # Emit events
        await self.event_service.emit(
            EventType.AGENT_COMPLETED.value,
            {
                "agent": "validation_agent",
                "overall_confidence": validation.get("overall_confidence", 0.5),
                "issues_count": len(validation.get("issues", []))
            },
            investigation_id=str(investigation_id)
        )
        
        await self.event_service.emit(
            EventType.PHASE_COMPLETED.value,
            {
                "phase": "validation",
                "agent": "validation_agent",
                "overall_confidence": validation.get("overall_confidence", 0.5)
            },
            investigation_id=str(investigation_id)
        )
        
        return validation
    
    async def _reporting_phase(
        self,
        investigation_id: UUID,
        research_results: Dict[str, Any],
        analysis_results: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reporting phase - compile report"""
        # Emit phase and agent started events
        await self.event_service.emit(
            EventType.PHASE_STARTED.value,
            {"phase": "reporting", "agent": "reporting_agent"},
            investigation_id=str(investigation_id)
        )
        
        await self.event_service.emit(
            EventType.AGENT_STARTED.value,
            {"agent": "reporting_agent", "action": "compiling_report"},
            investigation_id=str(investigation_id)
        )
        
        self.investigation_service.add_investigation_step(
            investigation_id,
            step_type="reporting_started",
            agent_name="reporting_agent",
            status="in_progress"
        )
        
        # Compile report
        report = await self.reporting_agent.compile_report(
            investigation_id,
            research_results.get("evidence", []),
            analysis_results,
            validation_results
        )
        
        # Log step completion
        self.investigation_service.add_investigation_step(
            investigation_id,
            step_type="reporting_completed",
            agent_name="reporting_agent",
            status="completed",
            result={"report_generated": True}
        )
        
        # Emit events
        await self.event_service.emit(
            EventType.AGENT_COMPLETED.value,
            {"agent": "reporting_agent", "action": "report_compiled"},
            investigation_id=str(investigation_id)
        )
        
        await self.event_service.emit(
            EventType.PHASE_COMPLETED.value,
            {"phase": "reporting", "agent": "reporting_agent"},
            investigation_id=str(investigation_id)
        )
        
        return report
    
    async def use_mcp_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use an MCP tool
        
        Args:
            server_name: MCP server name (firecrawl, database, tiger_id, youtube, meta, puppeteer)
            tool_name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        if server_name == "firecrawl":
            return await self.firecrawl_server.call_tool(tool_name, arguments)
        elif server_name == "database":
            return await self.database_server.call_tool(tool_name, arguments)
        elif server_name == "tiger_id":
            return await self.tiger_id_server.call_tool(tool_name, arguments)
        elif server_name == "youtube":
            return await self.youtube_server.call_tool(tool_name, arguments)
        elif server_name == "meta":
            return await self.meta_server.call_tool(tool_name, arguments)
        elif server_name == "puppeteer":
            if self.puppeteer_server:
                return await self.puppeteer_server.call_tool(tool_name, arguments)
            else:
                return {"error": "Puppeteer server not available. Install playwright or enable in settings."}
        else:
            return {"error": f"Unknown MCP server: {server_name}"}
    
    async def close(self):
        """Close all agent connections"""
        await self.research_agent.close()
        await self.firecrawl_server.client.aclose() if hasattr(self.firecrawl_server, 'client') and self.firecrawl_server.client else None
        
        # Close Puppeteer browser if initialized
        if self.puppeteer_server:
            await self.puppeteer_server.cleanup()
