"""Investigation 2.0 LangGraph workflow for tiger identification"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated, Literal
from uuid import UUID
from sqlalchemy.orm import Session
import operator
import numpy as np
from pathlib import Path
import io
from PIL import Image

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from backend.services.investigation_service import InvestigationService
from backend.services.image_search_service import ImageSearchService
from backend.services.event_service import get_event_service
from backend.services.exif_service import EXIFService
from backend.services.location_synthesis_service import LocationSynthesisService
from backend.services.auto_discovery_service import AutoDiscoveryService
from backend.services.investigation_trigger_service import InvestigationTriggerService
from backend.models.detection import TigerDetectionModel
from backend.models.reid import TigerReIDModel
from backend.models.cvwc2019_reid import CVWC2019ReIDModel
from backend.models.rapid_reid import RAPIDReIDModel
from backend.models.wildlife_tools import WildlifeToolsReIDModel
from backend.models.transreid import TransReIDModel
from backend.models.megadescriptor_b import MegaDescriptorBReIDModel
from backend.models.anthropic_chat import get_anthropic_fast_model, get_anthropic_quality_model
from backend.api.websocket_routes import emit_model_progress
from backend.database.vector_search import find_matching_tigers, store_embedding
from backend.database.models import Tiger, TigerImage, VerificationQueue, TigerStatus, SideView, VerificationStatus
from backend.events.event_types import EventType
from backend.utils.logging import get_logger
from backend.services.tiger.ensemble_strategy import VerifiedEnsembleStrategy

# New MCP servers for enhanced investigation workflow
from backend.mcp_servers import (
    get_sequential_thinking_server,
    get_image_analysis_server,
    get_deep_research_server,
    get_report_generation_server,
)

logger = get_logger(__name__)


class Investigation2State(TypedDict):
    """State structure for Investigation 2.0 workflow"""
    investigation_id: str
    uploaded_image: Optional[bytes]
    image_path: Optional[str]
    context: Dict[str, Any]
    uploaded_image_metadata: Optional[Dict[str, Any]]  # EXIF data including GPS
    reverse_search_results: Optional[List[Dict[str, Any]]]
    detected_tigers: Optional[List[Dict[str, Any]]]
    stripe_embeddings: Dict[str, np.ndarray]  # model_name -> embedding
    database_matches: Dict[str, List[Dict[str, Any]]]  # model_name -> matches
    verified_candidates: Optional[List[Dict[str, Any]]]  # MatchAnything verified candidates
    verification_applied: Optional[bool]  # Whether verification was run
    verification_disagreement: Optional[bool]  # Whether ReID and verification disagree
    report: Optional[Dict[str, Any]]
    reasoning_steps: List[Dict[str, Any]]  # Methodology tracking
    errors: Annotated[List[Dict[str, Any]], operator.add]
    phase: str
    status: Literal["running", "completed", "failed", "cancelled"]
    # New fields for enhanced workflow
    reasoning_chain_id: Optional[str]  # Sequential thinking chain ID
    image_quality: Optional[Dict[str, Any]]  # Image quality assessment results
    deep_research_session_id: Optional[str]  # Deep research session ID
    report_audience: Literal["law_enforcement", "conservation", "internal", "public"]


class Investigation2Workflow:
    """LangGraph workflow for Investigation 2.0"""
    
    def __init__(
        self,
        db: Optional[Session] = None
    ):
        """
        Initialize Investigation 2.0 workflow
        
        Args:
            db: Database session
        """
        self.db = db
        self.investigation_service = InvestigationService(db) if db else None
        self.image_search_service = ImageSearchService()
        self.event_service = get_event_service()
        
        # Initialize checkpointer
        self.checkpointer = MemorySaver()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph StateGraph"""
        workflow = StateGraph(Investigation2State)
        
        # Add nodes
        workflow.add_node("upload_and_parse", self._upload_and_parse_node)
        workflow.add_node("reverse_image_search", self._reverse_image_search_node)
        workflow.add_node("tiger_detection", self._tiger_detection_node)
        workflow.add_node("stripe_analysis", self._stripe_analysis_node)
        workflow.add_node("report_generation", self._report_generation_node)
        workflow.add_node("complete", self._complete_node)

        # Add edges
        workflow.add_edge(START, "upload_and_parse")
        workflow.add_edge("upload_and_parse", "reverse_image_search")
        workflow.add_conditional_edges(
            "reverse_image_search",
            self._should_continue,
            {
                "continue": "tiger_detection",
                "error": "complete",
                "skip": "tiger_detection"
            }
        )
        workflow.add_conditional_edges(
            "tiger_detection",
            self._should_continue,
            {
                "continue": "stripe_analysis",
                "error": "complete",
                "skip": "stripe_analysis"
            }
        )
        workflow.add_conditional_edges(
            "stripe_analysis",
            self._should_continue,
            {
                "continue": "report_generation",
                "error": "complete",
                "skip": "report_generation"
            }
        )
        workflow.add_edge("report_generation", "complete")
        workflow.add_edge("complete", END)
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    async def _upload_and_parse_node(self, state: Investigation2State) -> Investigation2State:
        """Process uploaded image and context"""
        try:
            logger.info("Starting upload and parse phase", investigation_id=state["investigation_id"])

            # Emit event
            await self.event_service.emit(
                EventType.PHASE_STARTED.value,
                {"phase": "upload_and_parse", "agent": "investigation2"},
                investigation_id=state["investigation_id"]
            )

            # Validate image
            if not state.get("uploaded_image"):
                raise ValueError("No image uploaded")

            # Validate image format
            try:
                image = Image.open(io.BytesIO(state["uploaded_image"]))
                image.verify()
                logger.info(f"Image validated: {image.size}, {image.format}")
            except Exception as e:
                raise ValueError(f"Invalid image format: {e}")

            # Extract EXIF metadata (including GPS if available)
            exif_service = EXIFService()
            image_metadata = exif_service.extract_metadata(state["uploaded_image"])

            if image_metadata.get("gps"):
                logger.info(f"GPS data found in EXIF: {image_metadata['gps']['latitude']}, {image_metadata['gps']['longitude']}")
            else:
                logger.info("No GPS data found in image EXIF")

            # Initialize reasoning chain using Sequential Thinking MCP
            reasoning_chain_id = None
            try:
                thinking_server = get_sequential_thinking_server()
                chain_result = await thinking_server.start_reasoning_chain(
                    question=f"Identify the tiger in this uploaded image from {state.get('context', {}).get('location', 'unknown location')}",
                    context={
                        "investigation_id": state["investigation_id"],
                        "location": state.get("context", {}).get("location"),
                        "date": state.get("context", {}).get("date"),
                        "notes": state.get("context", {}).get("notes"),
                        "has_gps": bool(image_metadata.get("gps"))
                    },
                    reasoning_type="investigation"
                )
                reasoning_chain_id = chain_result.get("chain_id")
                logger.info(f"Initialized reasoning chain: {reasoning_chain_id}")
            except Exception as e:
                logger.warning(f"Failed to initialize reasoning chain (non-critical): {e}")

            # Assess image quality using Image Analysis MCP
            image_quality = None
            try:
                image_server = get_image_analysis_server()
                quality_result = await image_server.assess_image_quality(
                    image_data=state["uploaded_image"],
                    detection_results=None  # No detections yet
                )
                image_quality = quality_result
                logger.info(f"Image quality assessed: overall_score={quality_result.get('overall_score', 0):.1%}")

                # Warn if image quality is poor
                if quality_result.get("overall_score", 1.0) < 0.4:
                    logger.warning(f"Low image quality detected: {quality_result.get('issues', [])}")
            except Exception as e:
                logger.warning(f"Failed to assess image quality (non-critical): {e}")

            # Store in investigation if service available
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    UUID(state["investigation_id"]),
                    step_type="upload_and_parse",
                    agent_name="investigation2",
                    status="completed",
                    result={
                        "image_size": len(state["uploaded_image"]),
                        "context": state.get("context", {}),
                        "has_gps": bool(image_metadata.get("gps")),
                        "image_quality_score": image_quality.get("overall_score") if image_quality else None
                    }
                )

            # Emit completion event
            await self.event_service.emit(
                EventType.PHASE_COMPLETED.value,
                {"phase": "upload_and_parse", "agent": "investigation2"},
                investigation_id=state["investigation_id"]
            )

            # Initialize reasoning steps and add first step via MCP
            reasoning_steps = state.get("reasoning_steps", [])

            # Build evidence list
            evidence = [
                f"Image format: {image_metadata.get('image_info', {}).get('format', 'unknown')}",
                f"GPS data: {'found' if image_metadata.get('gps') else 'not found'}",
                f"Context location: {state.get('context', {}).get('location', 'not provided')}"
            ]
            if image_quality:
                evidence.append(f"Image quality score: {image_quality.get('overall_score', 0):.1%}")
                if image_quality.get("issues"):
                    evidence.append(f"Quality issues: {', '.join(image_quality.get('issues', []))}")

            # Add reasoning step via MCP if chain initialized
            if reasoning_chain_id:
                try:
                    thinking_server = get_sequential_thinking_server()
                    await thinking_server.add_reasoning_step(
                        chain_id=reasoning_chain_id,
                        evidence=evidence,
                        reasoning="Validated uploaded image and extracted metadata. Assessed image quality for tiger identification suitability.",
                        conclusion="Image ready for analysis" + (" with GPS coordinates" if image_metadata.get("gps") else ""),
                        confidence=100 if not image_quality or image_quality.get("overall_score", 1.0) >= 0.6 else 70
                    )
                except Exception as e:
                    logger.warning(f"Failed to add reasoning step (non-critical): {e}")

            reasoning_steps.append({
                "step": len(reasoning_steps) + 1,
                "phase": "upload_and_parse",
                "action": f"Uploaded and validated image ({len(state['uploaded_image'])} bytes)",
                "reasoning": "Parsed user context, extracted image metadata, and assessed quality",
                "evidence": evidence,
                "conclusion": "Image ready for analysis" + (" with GPS coordinates" if image_metadata.get("gps") else ""),
                "confidence": 100 if not image_quality or image_quality.get("overall_score", 1.0) >= 0.6 else 70
            })

            return {
                **state,
                "uploaded_image_metadata": image_metadata,
                "reasoning_steps": reasoning_steps,
                "reasoning_chain_id": reasoning_chain_id,
                "image_quality": image_quality,
                "phase": "upload_and_parse",
                "status": "running"
            }
            
        except Exception as e:
            logger.error("Upload and parse failed", investigation_id=state["investigation_id"], error=str(e))
            return {
                **state,
                "errors": [{"phase": "upload_and_parse", "error": str(e)}],
                "phase": "upload_and_parse",
                "status": "failed"
            }
    
    async def _reverse_image_search_node(self, state: Investigation2State) -> Investigation2State:
        """Perform web intelligence search using Anthropic Claude with web search tools"""
        try:
            logger.info(f"[WEB INTELLIGENCE NODE] ========== STARTING WEB INTELLIGENCE SEARCH ==========")
            logger.info(f"[WEB INTELLIGENCE NODE] Investigation ID: {state['investigation_id']}")
            logger.info("Starting web intelligence search with Anthropic Claude", investigation_id=state["investigation_id"])

            # Emit event
            await self.event_service.emit(
                EventType.PHASE_STARTED.value,
                {"phase": "reverse_image_search", "agent": "investigation2"},
                investigation_id=state["investigation_id"]
            )

            # Get context for search query generation
            context = state.get("context", {})
            location = context.get("location", "unknown location")
            date = context.get("date", "recent")
            notes = context.get("notes", "")

            # Use Anthropic fast model to generate optimized search query
            anthropic_fast = get_anthropic_fast_model()

            query_prompt = f"""Generate an optimal web search query for finding information about tiger trafficking and captivity.

Context:
- Location: {location}
- Date: {date}
- Notes: {notes}

Generate a search query that will find:
1. Tiger trafficking news and incidents in this region
2. Known captive tiger facilities
3. Tiger conservation enforcement actions
4. Illegal wildlife trade activities

Return ONLY the search query text, no explanation."""

            logger.info("[WEB INTELLIGENCE] Generating search query...")
            query_result = await anthropic_fast.chat(
                message=query_prompt,
                enable_web_search=False,
                temperature=0.3,
                max_tokens=100
            )

            if not query_result.get("success"):
                raise RuntimeError(f"Query generation failed: {query_result.get('error')}")

            search_query = query_result.get("response", "").strip()
            logger.info(f"[WEB INTELLIGENCE] Generated query: {search_query}")

            # Perform web search with Anthropic + Firecrawl
            logger.info("[WEB INTELLIGENCE] Executing Anthropic web search...")
            search_result = await anthropic_fast.chat(
                message=f"""Search for intelligence about: {search_query}

Provide a comprehensive summary including:
- Recent tiger trafficking incidents
- Known facilities keeping captive tigers
- Law enforcement actions
- Conservation alerts
- Any relevant tiger-related activities in {location}

Focus on factual, verifiable information with specific dates, locations, and sources.""",
                enable_web_search=True,
                temperature=0.5,
                max_tokens=2048
            )

            if not search_result.get("success"):
                raise RuntimeError(f"Web search failed: {search_result.get('error')}")

            # Extract results
            summary = search_result.get("response", "")
            citations = search_result.get("citations", [])

            logger.info(f"[WEB INTELLIGENCE] Search completed: {len(summary)} chars, {len(citations)} citations")

            # Format results in compatible structure
            reverse_search_results = {
                "provider": "anthropic_web_search",
                "query": search_query,
                "summary": summary,
                "citations": citations,
                "total_results": len(citations),
                "providers_searched": 1,
                "model_used": anthropic_fast.model_name,
                "status": "success" if citations else "no_results",
                "error": None if citations else "No web sources found for the query"
            }

            # Enhanced deep research using Deep Research MCP (if facilities/entities found)
            deep_research_session_id = None
            try:
                # Extract potential facility names from web search results
                if summary and len(summary) > 100:
                    research_server = get_deep_research_server()

                    # Start deep research session
                    research_result = await research_server.start_research(
                        topic=f"Tiger trafficking and captive facilities near {location}",
                        depth="standard",  # 10 queries
                        max_queries=10,
                        research_mode="facility_investigation"
                    )
                    deep_research_session_id = research_result.get("session_id")

                    if deep_research_session_id:
                        logger.info(f"Started deep research session: {deep_research_session_id}")

                        # Synthesize findings
                        synthesis = await research_server.synthesize_findings(deep_research_session_id)

                        # Merge deep research into reverse search results
                        if synthesis.get("synthesis"):
                            reverse_search_results["deep_research"] = {
                                "session_id": deep_research_session_id,
                                "synthesis": synthesis.get("synthesis"),
                                "sources_analyzed": synthesis.get("sources_analyzed", 0),
                                "entities_found": synthesis.get("entities_found", []),
                                "confidence": synthesis.get("confidence", 0)
                            }
                            logger.info(f"Deep research completed: {synthesis.get('sources_analyzed', 0)} sources analyzed")
            except Exception as e:
                logger.warning(f"Deep research failed (non-critical): {e}")

            # Store results
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    UUID(state["investigation_id"]),
                    step_type="web_intelligence",
                    agent_name="investigation2",
                    status="completed",
                    result={
                        "provider": "anthropic_web_search",
                        "citations_found": len(citations),
                        "query": search_query
                    }
                )

            # Emit completion event
            await self.event_service.emit(
                EventType.PHASE_COMPLETED.value,
                {
                    "phase": "reverse_image_search",
                    "agent": "investigation2",
                    "results_count": len(citations)
                },
                investigation_id=state["investigation_id"]
            )

            logger.info(f"[WEB INTELLIGENCE NODE] ========== WEB INTELLIGENCE SEARCH COMPLETED ==========")
            logger.info(f"[WEB INTELLIGENCE NODE] Results: {len(citations)} citations")

            # Add reasoning step
            reasoning_steps = state.get("reasoning_steps", [])
            reasoning_chain_id = state.get("reasoning_chain_id")

            # Build evidence list
            evidence = []
            if citations:
                evidence = [
                    f"Found {len(citations)} web sources",
                    f"Generated {len(summary)} character summary",
                    f"Search focused on: {location}"
                ]
                if reverse_search_results.get("deep_research"):
                    dr = reverse_search_results["deep_research"]
                    evidence.append(f"Deep research analyzed {dr.get('sources_analyzed', 0)} additional sources")
                    if dr.get("entities_found"):
                        evidence.append(f"Entities identified: {', '.join(dr.get('entities_found', [])[:5])}")

                conclusion = f"High confidence web intelligence gathered from {len(citations)} authoritative sources"
                confidence = 85 if len(citations) > 5 else 60
            else:
                evidence = [
                    "No web sources returned from search providers",
                    f"Search focused on: {location}",
                    "This may be due to API limitations or no matching results"
                ]
                conclusion = "Web intelligence unavailable - proceeding with other analysis methods"
                confidence = 30

            # Add reasoning step via MCP if chain initialized
            if reasoning_chain_id:
                try:
                    thinking_server = get_sequential_thinking_server()
                    await thinking_server.add_reasoning_step(
                        chain_id=reasoning_chain_id,
                        evidence=evidence,
                        reasoning=f"Generated optimized query based on location ({location}) and context to find tiger trafficking intelligence. Used Anthropic web search with optional deep research expansion.",
                        conclusion=conclusion,
                        confidence=confidence
                    )
                except Exception as e:
                    logger.warning(f"Failed to add reasoning step (non-critical): {e}")

            reasoning_steps.append({
                "step": len(reasoning_steps) + 1,
                "phase": "Web Intelligence",
                "action": f"Executed Anthropic web search with query: {search_query}",
                "reasoning": f"Generated optimized query based on location ({location}) and context to find tiger trafficking intelligence",
                "evidence": evidence,
                "conclusion": conclusion,
                "confidence": confidence
            })

            return {
                **state,
                "reverse_search_results": reverse_search_results,
                "reasoning_steps": reasoning_steps,
                "deep_research_session_id": deep_research_session_id,
                "phase": "reverse_image_search"
            }

        except Exception as e:
            logger.info(f"[WEB INTELLIGENCE NODE] ERROR - EXCEPTION: {e}")
            logger.error("Web intelligence search failed", investigation_id=state["investigation_id"], error=str(e), exc_info=True)
            return {
                **state,
                "reverse_search_results": {"error": str(e), "citations": []},
                "errors": [{"phase": "reverse_image_search", "error": str(e)}],
                "phase": "reverse_image_search"
            }
    
    async def _tiger_detection_node(self, state: Investigation2State) -> Investigation2State:
        """Detect tigers in uploaded image using MegaDetector"""
        try:
            logger.info(f"[DETECTION NODE] ========== STARTING TIGER DETECTION ==========")
            logger.info(f"[DETECTION NODE] Investigation ID: {state['investigation_id']}")
            logger.info("Starting tiger detection", investigation_id=state["investigation_id"])
            
            # Emit event
            logger.info(f"[DETECTION NODE] Emitting phase_started event...")
            await self.event_service.emit(
                EventType.PHASE_STARTED.value,
                {"phase": "tiger_detection", "agent": "investigation2"},
                investigation_id=state["investigation_id"]
            )
            logger.info(f"[DETECTION NODE] Event emitted successfully")
            
            image_bytes = state.get("uploaded_image")
            logger.info(f"[DETECTION NODE] Image bytes available: {len(image_bytes) if image_bytes else 0} bytes")
            if not image_bytes:
                raise ValueError("No image available for detection")
            
            # Initialize detection model
            logger.info(f"[DETECTION NODE] Initializing TigerDetectionModel...")
            detection_model = TigerDetectionModel()
            logger.info(f"[DETECTION NODE] Model initialized successfully")
            
            # Detect tigers
            logger.info(f"[DETECTION NODE] Calling detection_model.detect()...")
            detection_result = await detection_model.detect(image_bytes)
            logger.info(f"[DETECTION NODE] Detection completed. Result keys: {list(detection_result.keys())}")
            
            if detection_result.get("error"):
                logger.info(f"[DETECTION NODE] Detection returned error: {detection_result['error']}")
                logger.warning(f"Detection error: {detection_result['error']}")
            
            detections = detection_result.get("detections", [])
            logger.info(f"[DETECTION NODE] Detected {len(detections)} tigers")
            logger.info(f"Detected {len(detections)} tigers")
            
            # Format detected tigers
            logger.info(f"[DETECTION NODE] Formatting {len(detections)} detected tigers...")
            detected_tigers = []
            for i, det in enumerate(detections):
                logger.info(f"[DETECTION NODE] Processing detection {i}: bbox={det.get('bbox')}, conf={det.get('confidence')}")
                
                # Convert PIL Image crop to bytes for serialization
                crop = det.get("crop")
                crop_bytes = None
                if crop:
                    img_buffer = io.BytesIO()
                    crop.save(img_buffer, format='JPEG')
                    crop_bytes = img_buffer.getvalue()
                
                detected_tigers.append({
                    "index": i,
                    "bbox": det.get("bbox"),
                    "confidence": det.get("confidence"),
                    "crop": crop_bytes,  # Bytes instead of PIL Image for serialization
                    "category": det.get("category", "animal")
                })
            logger.info(f"[DETECTION NODE] Formatted {len(detected_tigers)} tigers")
            
            # Store results
            logger.info(f"[DETECTION NODE] Storing results in database...")
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    UUID(state["investigation_id"]),
                    step_type="tiger_detection",
                    agent_name="investigation2",
                    status="completed",
                    result={
                        "tigers_detected": len(detected_tigers),
                        "average_confidence": sum(d["confidence"] for d in detected_tigers) / len(detected_tigers) if detected_tigers else 0
                    }
                )
                logger.info(f"[DETECTION NODE] Results stored in database")
            
            # Emit completion event
            logger.info(f"[DETECTION NODE] Emitting phase_completed event...")
            await self.event_service.emit(
                EventType.PHASE_COMPLETED.value,
                {
                    "phase": "tiger_detection",
                    "agent": "investigation2",
                    "tigers_detected": len(detected_tigers)
                },
                investigation_id=state["investigation_id"]
            )
            logger.info(f"[DETECTION NODE] Completion event emitted")
            logger.info(f"[DETECTION NODE] ========== TIGER DETECTION COMPLETED ==========")

            # Add reasoning step
            reasoning_steps = state.get("reasoning_steps", [])
            reasoning_chain_id = state.get("reasoning_chain_id")
            avg_conf = sum(d["confidence"] for d in detected_tigers) / len(detected_tigers) if detected_tigers else 0

            evidence = [
                f"Detected {len(detected_tigers)} tiger(s)",
                f"Average confidence: {avg_conf:.1%}",
                f"Bounding boxes extracted for stripe analysis"
            ]
            conclusion = f"Successfully detected {len(detected_tigers)} tiger(s) with {avg_conf:.1%} average confidence"
            confidence = int(avg_conf * 100) if detected_tigers else 50

            # Add reasoning step via MCP if chain initialized
            if reasoning_chain_id:
                try:
                    thinking_server = get_sequential_thinking_server()
                    await thinking_server.add_reasoning_step(
                        chain_id=reasoning_chain_id,
                        evidence=evidence,
                        reasoning="Used MegaDetector (state-of-the-art wildlife detection model) to identify tiger presence and location in image. Extracted bounding boxes for stripe pattern analysis.",
                        conclusion=conclusion,
                        confidence=confidence
                    )
                except Exception as e:
                    logger.warning(f"Failed to add reasoning step (non-critical): {e}")

            reasoning_steps.append({
                "step": len(reasoning_steps) + 1,
                "phase": "Tiger Detection",
                "action": f"Ran MegaDetector on uploaded image",
                "reasoning": "Used state-of-the-art wildlife detection model to identify tiger presence and location in image",
                "evidence": evidence,
                "conclusion": conclusion,
                "confidence": confidence
            })

            return {
                **state,
                "detected_tigers": detected_tigers,
                "reasoning_steps": reasoning_steps,
                "phase": "tiger_detection"
            }
            
        except Exception as e:
            logger.info(f"[DETECTION NODE] ERROR - EXCEPTION: {e}")
            logger.info(f"[DETECTION NODE] Exception type: {type(e).__name__}")
            import traceback
            logger.info(f"[DETECTION NODE] Traceback: {traceback.format_exc()}")
            logger.error("Tiger detection failed", investigation_id=state["investigation_id"], error=str(e), exc_info=True)
            return {
                **state,
                "detected_tigers": [],
                "errors": [{"phase": "tiger_detection", "error": str(e)}],
                "phase": "tiger_detection"
            }
    
    def _consolidate_matches(self, database_matches: Dict[str, List[Dict]]) -> List[Dict]:
        """Consolidate matches from all models into ranked candidates.

        Args:
            database_matches: Dict mapping model names to match lists

        Returns:
            List of consolidated candidates sorted by weighted average score
        """
        from collections import defaultdict
        tiger_scores = defaultdict(lambda: {"scores": [], "tiger_id": None, "tiger_name": None})

        for model_name, matches in database_matches.items():
            for match in matches:
                tid = match.get("tiger_id")
                if tid:
                    tiger_scores[tid]["scores"].append(match.get("similarity", 0))
                    tiger_scores[tid]["tiger_id"] = tid
                    tiger_scores[tid]["tiger_name"] = match.get("tiger_name", "Unknown")

        # Calculate weighted average score
        candidates = []
        for tid, data in tiger_scores.items():
            if data["scores"]:
                avg_score = sum(data["scores"]) / len(data["scores"])
                candidates.append({
                    "tiger_id": tid,
                    "tiger_name": data["tiger_name"],
                    "weighted_score": avg_score,
                    "models_matched": len(data["scores"])
                })

        return sorted(candidates, key=lambda x: x["weighted_score"], reverse=True)

    async def _stripe_analysis_node(self, state: Investigation2State) -> Investigation2State:
        """Run all stripe detection models in parallel"""
        try:
            logger.info(f"[STRIPE NODE] ========== STARTING STRIPE ANALYSIS ==========")
            logger.info(f"[STRIPE NODE] Investigation ID: {state['investigation_id']}")
            logger.info("Starting stripe analysis", investigation_id=state["investigation_id"])
            
            # Emit event
            await self.event_service.emit(
                EventType.PHASE_STARTED.value,
                {"phase": "stripe_analysis", "agent": "investigation2"},
                investigation_id=state["investigation_id"]
            )
            
            detected_tigers = state.get("detected_tigers", [])
            logger.info(f"[STRIPE NODE] Detected tigers in state: {len(detected_tigers)}")
            if not detected_tigers:
                logger.info(f"[STRIPE NODE] WARNING: No detected tigers for stripe analysis")
                logger.warning("No detected tigers for stripe analysis")
                return {
                    **state,
                    "stripe_embeddings": {},
                    "database_matches": {},
                    "phase": "stripe_analysis"
                }
            
            # Use the first detected tiger (highest confidence)
            tiger_crop_bytes = detected_tigers[0].get("crop")
            if not tiger_crop_bytes:
                raise ValueError("No tiger crop available")
            
            # Initialize all models
            models = {
                "tiger_reid": TigerReIDModel(),
                "cvwc2019": CVWC2019ReIDModel(),
                "rapid": RAPIDReIDModel(),
                "wildlife_tools": WildlifeToolsReIDModel()
            }
            
            # Run all models in parallel
            import asyncio
            
            async def run_model(model_name: str, model):
                try:
                    logger.info(f"Running {model_name}")
                    if model_name == "tiger_reid":
                        embedding = await model.generate_embedding_from_bytes(tiger_crop_bytes)
                    else:
                        embedding = await model.generate_embedding(tiger_crop_bytes)
                    
                    if embedding is None:
                        logger.warning(f"{model_name} returned None embedding")
                        return model_name, None, []
                    
                    # Search database for matches
                    if self.db:
                        matches = find_matching_tigers(
                            self.db,
                            query_embedding=embedding,
                            limit=5,
                            similarity_threshold=0.8
                        )
                    else:
                        matches = []
                    
                    logger.info(f"{model_name}: Found {len(matches)} matches")
                    return model_name, embedding, matches
                    
                except Exception as e:
                    logger.error(f"Error with {model_name}: {e}")
                    return model_name, None, []
            
            # Execute all models in parallel
            results = await asyncio.gather(*[
                run_model(name, model) for name, model in models.items()
            ])
            
            # Collect results
            stripe_embeddings = {}
            database_matches = {}

            for model_name, embedding, matches in results:
                if embedding is not None:
                    stripe_embeddings[model_name] = embedding
                database_matches[model_name] = matches

            # Calculate total_matches BEFORE the conditional block so it's always available
            total_matches = sum(len(m) for m in database_matches.values())

            # Store results
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    UUID(state["investigation_id"]),
                    step_type="stripe_analysis",
                    agent_name="investigation2",
                    status="completed",
                    result={
                        "models_run": len(stripe_embeddings),
                        "total_matches": total_matches,
                    }
                )
            
            # Emit completion event
            await self.event_service.emit(
                EventType.PHASE_COMPLETED.value,
                {
                    "phase": "stripe_analysis",
                    "agent": "investigation2",
                    "models_run": len(stripe_embeddings)
                },
                investigation_id=state["investigation_id"]
            )

            # Add reasoning step
            reasoning_steps = state.get("reasoning_steps", [])
            reasoning_chain_id = state.get("reasoning_chain_id")

            # Build detailed evidence
            evidence = [
                f"Generated embeddings from {len(stripe_embeddings)} models",
                f"Found {total_matches} potential matches across all models",
                f"Searched database of reference tigers"
            ]

            # Add per-model breakdown
            for model_name, matches in database_matches.items():
                if matches:
                    top_sim = matches[0].get("similarity", 0) if matches else 0
                    evidence.append(f"{model_name}: {len(matches)} matches (top: {top_sim:.1%})")

            conclusion = f"Stripe analysis complete: {total_matches} potential matches identified"
            confidence = 90 if total_matches > 0 else 60

            # Add reasoning step via MCP if chain initialized
            if reasoning_chain_id:
                try:
                    thinking_server = get_sequential_thinking_server()
                    await thinking_server.add_reasoning_step(
                        chain_id=reasoning_chain_id,
                        evidence=evidence,
                        reasoning="Used ensemble of tiger re-identification models (TigerReID, CVWC2019, RAPID, Wildlife-Tools, TransReID) to match stripe patterns against database. Each model uses different feature extraction approaches for robust identification.",
                        conclusion=conclusion,
                        confidence=confidence
                    )
                except Exception as e:
                    logger.warning(f"Failed to add reasoning step (non-critical): {e}")

            reasoning_steps.append({
                "step": len(reasoning_steps) + 1,
                "phase": "ReID Analysis",
                "action": f"Ran {len(stripe_embeddings)} ReID models for stripe pattern matching",
                "reasoning": "Used ensemble of tiger re-identification models (TigerReID, CVWC2019, RAPID, Wildlife-Tools, TransReID) to match stripe patterns against database",
                "evidence": evidence,
                "conclusion": conclusion,
                "confidence": confidence
            })

            # Run geometric verification on top candidates
            verified_candidates = []
            verification_applied = False
            verification_disagreement = False
            try:
                if database_matches and any(database_matches.values()):
                    consolidated = self._consolidate_matches(database_matches)
                    if consolidated:
                        verified_strategy = VerifiedEnsembleStrategy(
                            use_verification=True,
                            verification_top_k=5
                        )

                        # Get query image from detected tigers (first crop)
                        detected_tigers = state.get("detected_tigers", [])
                        if detected_tigers and detected_tigers[0].get("crop"):
                            query_image = Image.open(io.BytesIO(detected_tigers[0]["crop"]))

                            verified_candidates = await verified_strategy._verify_candidates(
                                query_image=query_image,
                                candidates=consolidated[:5],
                                gallery_images=None,
                                db_session=self.db
                            )
                            verification_applied = True
                            logger.info(f"Verified {len(verified_candidates)} candidates with MatchAnything")

                            # Check for verification disagreement
                            if verified_candidates and consolidated:
                                top_reid_id = consolidated[0].get("tiger_id")
                                top_verified_id = verified_candidates[0].get("tiger_id")
                                if top_reid_id and top_verified_id and top_reid_id != top_verified_id:
                                    verification_disagreement = True
                                    logger.warning(f"Verification disagrees: ReID={top_reid_id}, Verified={top_verified_id}")

                            # Add verification reasoning step
                            if reasoning_chain_id:
                                try:
                                    thinking_server = get_sequential_thinking_server()
                                    verification_evidence = [
                                        f"Verified {len(verified_candidates)} top candidates with MatchAnything",
                                        f"Top verified: {verified_candidates[0].get('tiger_name', 'Unknown')} ({verified_candidates[0].get('combined_score', 0):.1%})" if verified_candidates else "No verified candidates",
                                        f"Verification status: {verified_candidates[0].get('verification_status', 'unknown')}" if verified_candidates else "N/A"
                                    ]
                                    if verification_disagreement:
                                        verification_evidence.append("WARNING: Verification disagrees with ReID ranking")

                                    await thinking_server.add_reasoning_step(
                                        chain_id=reasoning_chain_id,
                                        evidence=verification_evidence,
                                        reasoning="Applied MatchAnything geometric verification to validate top ReID candidates using keypoint matching.",
                                        conclusion="Geometric verification complete" + (" with disagreement - flagged for review" if verification_disagreement else ""),
                                        confidence=85 if not verification_disagreement else 65
                                    )
                                except Exception as e:
                                    logger.warning(f"Failed to add verification reasoning step (non-critical): {e}")

                            reasoning_steps.append({
                                "step": len(reasoning_steps) + 1,
                                "phase": "Geometric Verification",
                                "action": f"Verified {len(verified_candidates)} candidates with MatchAnything",
                                "reasoning": "Applied MatchAnything geometric verification to validate top ReID candidates using keypoint matching",
                                "evidence": [
                                    f"Verified {len(verified_candidates)} top candidates",
                                    f"Top verified: {verified_candidates[0].get('tiger_name', 'Unknown')}" if verified_candidates else "No verified candidates",
                                    f"Disagreement: {verification_disagreement}"
                                ],
                                "conclusion": "Geometric verification complete" + (" with disagreement" if verification_disagreement else ""),
                                "confidence": 85 if not verification_disagreement else 65
                            })
            except Exception as e:
                logger.warning(f"Geometric verification failed (non-critical): {e}")

            return {
                **state,
                "stripe_embeddings": stripe_embeddings,
                "database_matches": database_matches,
                "verified_candidates": verified_candidates,
                "verification_applied": verification_applied,
                "verification_disagreement": verification_disagreement,
                "reasoning_steps": reasoning_steps,
                "phase": "stripe_analysis"
            }
            
        except Exception as e:
            logger.error("Stripe analysis failed", investigation_id=state["investigation_id"], error=str(e))
            return {
                **state,
                "stripe_embeddings": {},
                "database_matches": {},
                "errors": [{"phase": "stripe_analysis", "error": str(e)}],
                "phase": "stripe_analysis"
            }
    
    async def _report_generation_node(self, state: Investigation2State) -> Investigation2State:
        """Generate investigation report using Report Generation MCP + Anthropic Claude"""
        try:
            logger.info("Starting report generation with Report Generation MCP", investigation_id=state["investigation_id"])

            # Emit event
            await self.event_service.emit(
                EventType.PHASE_STARTED.value,
                {"phase": "report_generation", "agent": "investigation2"},
                investigation_id=state["investigation_id"]
            )

            # Determine report audience (default to law_enforcement)
            report_audience = state.get("report_audience", "law_enforcement")

            # Collect all findings
            reverse_search = state.get("reverse_search_results", {})
            detected_tigers = state.get("detected_tigers", [])
            database_matches = state.get("database_matches", {})
            context = state.get("context", {})

            # Calculate confidence from top matches
            top_matches_confidence = self._calculate_match_confidence(database_matches)

            # Extract web intelligence insights from Anthropic web search
            web_intelligence_summary = ""
            if reverse_search and isinstance(reverse_search, dict):
                if reverse_search.get('provider') in ['anthropic_web_search', 'gemini_search_grounding']:
                    citations = reverse_search.get('citations', [])
                    summary = reverse_search.get('summary', '')
                    web_intelligence_summary = f"""

## Web Intelligence (Anthropic Web Search)
**Search Query:** {reverse_search.get('query', 'N/A')}
**Sources Found:** {len(citations)}

**Intelligence Summary:**
{summary}

**Citations:**
"""
                    for i, cite in enumerate(citations[:10], 1):  # Top 10 citations
                        web_intelligence_summary += f"\n{i}. {cite.get('title', 'No title')}"
                        web_intelligence_summary += f"\n   {cite.get('uri', 'No URI')}"
                else:
                    # Legacy format fallback
                    total_results = reverse_search.get('total_results', 0)
                    providers_searched = reverse_search.get('providers_searched', 0)
                    web_intelligence_summary = f"""

## External Search Results
- Providers queried: {providers_searched}
- Total external references found: {total_results}
"""

            # Create comprehensive prompt for Gemini Pro
            prompt = f"""Generate a professional wildlife investigation report for tiger identification based on comprehensive multi-source analysis:

## INVESTIGATION CONTEXT
**Location:** {context.get('location', 'Not specified')}
**Date:** {context.get('date', 'Not specified')}
**Case Notes:** {context.get('notes', 'None provided')}

## AUTOMATED DETECTION (MegaDetector GPU Analysis)
- **Tigers Detected:** {len(detected_tigers)}
- **Detection Confidence:** {sum(d.get('confidence', 0) for d in detected_tigers) / len(detected_tigers) if detected_tigers else 0:.2%}
{web_intelligence_summary}

## STRIPE PATTERN MATCHING (Multi-Model Ensemble)
**Models Deployed:** {', '.join(database_matches.keys())}

**Match Summary by Model:**
{chr(10).join([f"  • {model}: {len(matches)} matches" + (f" (top: {matches[0].get('similarity', 0):.1%})" if matches else "") for model, matches in database_matches.items()])}

**Top Matches Across All Models:**
{self._format_top_matches(database_matches)}

---

**REPORT REQUIREMENTS:**

Generate a structured professional report with these sections:

### 1. EXECUTIVE SUMMARY (3-4 sentences)
- Synthesize key findings from detection, matching, and web intelligence
- State confidence level and reliability
- Mention any critical concerns or high-confidence matches

### 2. DETECTION & IDENTIFICATION FINDINGS
- Tiger detection results and confidence
- Stripe matching results across all models (MegaDescriptor, CVWC2019, TransReID, etc.)
- Consensus analysis (where multiple models agree)
- Cross-model validation strength

### 3. WEB INTELLIGENCE & EXTERNAL CONTEXT
- Synthesize findings from web search
- Relevant tiger trafficking incidents or facilities in the region
- Law enforcement or conservation activities
- Any external references that provide context

### 4. MATCH CONFIDENCE ASSESSMENT
- Evaluate top matches with cross-model validation
- Discuss agreement/disagreement between models
- Assess reliability given image quality and database coverage
- Weighted ensemble analysis

### 5. INVESTIGATIVE RECOMMENDATIONS
**Immediate Actions:**
- Specific next steps based on findings
- Additional data needed
- Verification methods

**Follow-up Investigation:**
- Field work recommendations
- Database expansion needs
- Expert review requirements

### 6. CONCLUSION
- Final assessment of identification confidence
- Key uncertainties or limitations
- Overall investigative outlook

**TONE:** Professional, evidence-based, suitable for law enforcement and conservation officials.
**FORMAT:** Clear sections with bullet points and specific details.
**LENGTH:** Comprehensive but concise - focus on actionable intelligence."""

            # Try using Report Generation MCP server first
            report = None
            report_text = ""
            try:
                report_server = get_report_generation_server()

                # Build investigation data for MCP server
                investigation_data = {
                    "investigation_id": state["investigation_id"],
                    "context": context,
                    "detected_tigers": detected_tigers,
                    "database_matches": database_matches,
                    "reverse_search_results": reverse_search,
                    "image_quality": state.get("image_quality"),
                    "reasoning_steps": state.get("reasoning_steps", []),
                    "top_matches_confidence": top_matches_confidence
                }

                # Generate report via MCP server
                logger.info(f"[REPORT] Generating {report_audience} report via MCP server...")
                mcp_result = await report_server.generate_report(
                    investigation_id=state["investigation_id"],
                    audience=report_audience,
                    format="markdown",
                    investigation_data=investigation_data
                )

                if mcp_result.get("success"):
                    report = mcp_result.get("report", {})
                    report_text = report.get("content", "")
                    logger.info(f"[REPORT] Generated {report_audience} report via MCP: {len(report_text)} chars")
                else:
                    logger.warning(f"[REPORT] MCP report generation failed, falling back to Claude: {mcp_result.get('error')}")

            except Exception as e:
                logger.warning(f"[REPORT] MCP report generation failed (falling back to Claude): {e}")

            # Fallback to Anthropic Claude if MCP failed
            if not report_text:
                anthropic_quality = get_anthropic_quality_model()

                logger.info("[REPORT] Generating report with Anthropic Claude (fallback)...")
                result = await anthropic_quality.chat(
                    message=prompt,
                    enable_web_search=False,
                    max_tokens=4096,
                    temperature=0.7
                )

                if not result.get("success"):
                    raise RuntimeError(f"Report generation failed: {result.get('error')}")

                report_text = result.get("response", "")
                logger.info(f"[REPORT] Generated report via Claude fallback: {len(report_text)} chars")

            # Structure the report if not already structured by MCP
            if not report:
                report = {
                    "investigation_id": state["investigation_id"],
                    "generated_at": str(np.datetime64('now')),
                    "context": context,
                    "summary": report_text,
                    "detection_count": len(detected_tigers),
                    "models_used": list(database_matches.keys()),
                    "total_matches": sum(len(m) for m in database_matches.values()),
                    "top_matches": self._extract_top_matches(database_matches),
                    "confidence": top_matches_confidence,
                    "audience": report_audience,
                    "model_used": "anthropic_fallback"
                }
            else:
                # Ensure all fields are present
                report["detection_count"] = len(detected_tigers)
                report["models_used"] = list(database_matches.keys())
                report["total_matches"] = sum(len(m) for m in database_matches.values())
                report["top_matches"] = self._extract_top_matches(database_matches)
                report["confidence"] = top_matches_confidence
                report["audience"] = report_audience

            # Store results
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    UUID(state["investigation_id"]),
                    step_type="report_generation",
                    agent_name="investigation2",
                    status="completed",
                    result={
                        "report_length": len(report_text),
                        "model": anthropic_quality.model_name
                    }
                )

            # Emit completion event
            await self.event_service.emit(
                EventType.PHASE_COMPLETED.value,
                {
                    "phase": "report_generation",
                    "agent": "investigation2"
                },
                investigation_id=state["investigation_id"]
            )

            # Add reasoning step and finalize reasoning chain
            reasoning_steps = state.get("reasoning_steps", [])
            reasoning_chain_id = state.get("reasoning_chain_id")

            evidence = [
                f"Generated {len(report_text)} character report",
                f"Report audience: {report_audience}",
                f"Incorporated data from {len(database_matches)} models",
                f"Total matches analyzed: {sum(len(m) for m in database_matches.values())}",
                f"Overall confidence: {report.get('confidence', 'medium')}"
            ]
            conclusion = f"Investigation complete: {report_audience} report generated with {report.get('confidence', 'medium')} confidence"
            confidence = {"high": 95, "medium": 75, "low": 55}.get(report.get('confidence', 'medium'), 75)

            # Add final reasoning step and finalize chain via MCP
            if reasoning_chain_id:
                try:
                    thinking_server = get_sequential_thinking_server()

                    # Add report generation step
                    await thinking_server.add_reasoning_step(
                        chain_id=reasoning_chain_id,
                        evidence=evidence,
                        reasoning=f"Synthesized all findings from web intelligence, detection, ReID analysis, and visual comparison into a {report_audience}-focused report.",
                        conclusion=conclusion,
                        confidence=confidence
                    )

                    # Finalize the reasoning chain
                    finalized = await thinking_server.finalize_reasoning(reasoning_chain_id)
                    if finalized.get("success"):
                        # Add reasoning chain summary to report
                        report["reasoning_chain"] = finalized.get("chain", {})
                        report["reasoning_summary"] = finalized.get("summary", "")
                        logger.info(f"[REPORT] Finalized reasoning chain with {finalized.get('total_steps', 0)} steps")

                except Exception as e:
                    logger.warning(f"Failed to finalize reasoning chain (non-critical): {e}")

            reasoning_steps.append({
                "step": len(reasoning_steps) + 1,
                "phase": "Report Generation",
                "action": f"Generated {report_audience} investigation report",
                "reasoning": f"Synthesized all findings from web intelligence, detection, ReID analysis, and visual comparison into cohesive {report_audience}-focused narrative",
                "evidence": evidence,
                "conclusion": conclusion,
                "confidence": confidence
            })

            return {
                **state,
                "report": report,
                "reasoning_steps": reasoning_steps,
                "phase": "report_generation"
            }

        except Exception as e:
            logger.error("Report generation failed", investigation_id=state["investigation_id"], error=str(e))
            return {
                **state,
                "report": {"error": str(e)},
                "errors": [{"phase": "report_generation", "error": str(e)}],
                "phase": "report_generation"
            }
    
    async def _complete_node(self, state: Investigation2State) -> Investigation2State:
        """Complete the investigation"""
        try:
            investigation_id = UUID(state["investigation_id"])

            # Deduplicate errors before completion
            errors = state.get("errors", [])
            unique_errors = []
            seen = set()
            for error in errors:
                error_key = (error.get("phase", ""), error.get("error", ""))
                if error_key not in seen:
                    seen.add(error_key)
                    unique_errors.append(error)

            logger.info(f"[COMPLETE] Deduplicated errors: {len(errors)} -> {len(unique_errors)}")

            # Synthesize location from all sources
            location_service = LocationSynthesisService()
            synthesized_location = location_service.synthesize_tiger_location(
                user_context=state.get("context"),
                web_intelligence=state.get("reverse_search_results"),
                database_matches=state.get("database_matches"),
                image_exif=state.get("uploaded_image_metadata")
            )

            # Add location analysis to report
            report = state.get("report", {})
            if report:
                report["location_analysis"] = synthesized_location

            # Add methodology to report
            if state.get("reasoning_steps"):
                report["methodology"] = state.get("reasoning_steps")

            logger.info(f"[COMPLETE] Location synthesis complete: {len(synthesized_location.get('sources', []))} sources found")

            # Auto-discovery: Create tiger and facility records if new discovery
            context = state.get("context", {})
            source = context.get("source", "user_upload")
            stored_tiger_id = None

            try:
                auto_discovery = AutoDiscoveryService(self.db)
                discovery_result = await auto_discovery.process_investigation_discovery(
                    investigation_id=investigation_id,
                    uploaded_image=state.get("uploaded_image"),
                    stripe_embeddings=state.get("stripe_embeddings", {}),
                    existing_matches=state.get("database_matches", {}),
                    web_intelligence=state.get("reverse_search_results", {}),
                    context=context
                )

                if discovery_result:
                    report["new_discovery"] = discovery_result
                    stored_tiger_id = discovery_result['tiger_id']
                    logger.info(
                        f"[NEW DISCOVERY] Tiger {discovery_result['tiger_id']} added to database at "
                        f"{discovery_result['facility_name']} ({discovery_result['location']})"
                    )

                    # Emit discovery event
                    await self.event_service.emit(
                        EventType.INVESTIGATION_COMPLETED.value,
                        {
                            "investigation_id": state["investigation_id"],
                            "discovery_type": "new_tiger",
                            "tiger_id": discovery_result['tiger_id'],
                            "facility_name": discovery_result['facility_name'],
                            "is_new_facility": discovery_result['is_new_facility']
                        },
                        investigation_id=state["investigation_id"]
                    )
                else:
                    logger.info("[AUTO-DISCOVERY] No new discovery - strong existing match found")

            except Exception as e:
                logger.warning(f"[AUTO-DISCOVERY] Auto-discovery failed (non-critical): {e}")
                # Don't fail the investigation if auto-discovery fails

            # Store user-uploaded tiger in gallery for future matching (if no strong match)
            if not stored_tiger_id and state.get("uploaded_image") and state.get("stripe_embeddings"):
                try:
                    location = synthesized_location.get("primary_location", "Unknown")
                    stored_tiger_id = await self._store_investigation_tiger(
                        image_bytes=state.get("uploaded_image"),
                        embeddings=state.get("stripe_embeddings", {}),
                        investigation_id=investigation_id,
                        location=location,
                        detected_tigers=state.get("detected_tigers", []),
                        existing_matches=state.get("database_matches", {}),
                        context=context
                    )
                    if stored_tiger_id:
                        report["stored_tiger_id"] = stored_tiger_id
                        logger.info(f"[STORE TIGER] Tiger {stored_tiger_id[:8]} stored for future matching")
                except Exception as e:
                    logger.warning(f"[STORE TIGER] Failed to store tiger (non-critical): {e}")

            # Add to verification queue (all tigers go to pending review)
            if stored_tiger_id:
                try:
                    priority = self._determine_verification_priority(state)
                    await self._add_to_verification_queue(
                        entity_type="tiger",
                        entity_id=stored_tiger_id,
                        investigation_id=investigation_id,
                        source=source,
                        priority=priority,
                        notes=f"From Investigation {str(investigation_id)[:8]} - {source}"
                    )
                except Exception as e:
                    logger.warning(f"[VERIFICATION] Failed to add to queue (non-critical): {e}")

            # Link auto-investigation results back to source tiger
            if source == "auto_discovery":
                source_tiger_id = context.get("source_tiger_id")
                if source_tiger_id:
                    try:
                        await self._link_investigation_to_source_tiger(
                            investigation_id=investigation_id,
                            source_tiger_id=source_tiger_id,
                            matches=state.get("database_matches", {}),
                            report=report
                        )
                    except Exception as e:
                        logger.warning(f"[LINK] Failed to link to source tiger (non-critical): {e}")

            # Mark investigation as completed
            if self.investigation_service:
                self.investigation_service.complete_investigation(
                    investigation_id,
                    summary=report
                )

            # Emit completion event
            await self.event_service.emit(
                EventType.INVESTIGATION_COMPLETED.value,
                {
                    "investigation_id": state["investigation_id"],
                    "total_matches": sum(len(m) for m in state.get("database_matches", {}).values()),
                    "models_used": len(state.get("stripe_embeddings", {}))
                },
                investigation_id=state["investigation_id"]
            )

            return {
                **state,
                "report": report,
                "errors": unique_errors,
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
    
    def _should_continue(self, state: Investigation2State) -> str:
        """Determine if workflow should continue"""
        current_phase = state.get("phase", "unknown")
        current_status = state.get("status", "unknown")
        error_count = len(state.get("errors", []))
        
        logger.info(f"[DECISION] ========== SHOULD_CONTINUE CHECK ==========")
        logger.info(f"[DECISION] Current phase: {current_phase}")
        logger.info(f"[DECISION] Current status: {current_status}")
        logger.info(f"[DECISION] Error count: {error_count}")
        
        if state.get("status") in ["failed", "cancelled"]:
            logger.info(f"[DECISION] Decision: ERROR (status is {state.get('status')})")
            return "error"
        
        # Check for critical errors in current phase
        errors = state.get("errors", [])
        if errors:
            logger.info(f"[DECISION] Found {len(errors)} errors in state")
            current_phase = state.get("phase", "")
            critical_phases = ["upload_and_parse", "tiger_detection"]
            if any(error.get("phase") == current_phase for error in errors):
                if current_phase in critical_phases:
                    logger.info(f"[DECISION] Decision: ERROR (critical phase {current_phase} has errors)")
                    return "error"
        
        logger.info(f"[DECISION] Decision: CONTINUE")
        return "continue"
    
    def _format_top_matches(self, database_matches: Dict[str, List[Dict]]) -> str:
        """Format top matches across all models"""
        all_matches = []
        for model_name, matches in database_matches.items():
            for match in matches[:3]:
                all_matches.append({
                    "model": model_name,
                    "tiger_id": match.get("tiger_id"),
                    "similarity": match.get("similarity", 0),
                    "tiger_name": match.get("tiger_name")
                })
        
        all_matches.sort(key=lambda x: x["similarity"], reverse=True)
        
        lines = []
        for i, match in enumerate(all_matches[:10], 1):
            lines.append(
                f"{i}. {match['tiger_name'] or match['tiger_id']} - "
                f"Similarity: {match['similarity']:.2%} ({match['model']})"
            )
        
        return "\n".join(lines) if lines else "No matches found"
    
    def _extract_top_matches(self, database_matches: Dict[str, List[Dict]]) -> List[Dict]:
        """Extract and rank top matches with facility data"""
        all_matches = []
        for model_name, matches in database_matches.items():
            for match in matches:
                all_matches.append({
                    "model": model_name,
                    "tiger_id": str(match.get("tiger_id")),
                    "similarity": float(match.get("similarity", 0)),
                    "confidence": float(match.get("similarity", 0)),  # Use similarity as confidence
                    "tiger_name": match.get("tiger_name"),
                    "image_id": str(match.get("image_id")),
                    "image_url": match.get("image_path"),
                    "facility_id": match.get("facility_id"),
                    "facility_name": match.get("facility_name"),
                    "last_seen_location": match.get("last_seen_location"),
                    "last_seen_date": match.get("last_seen_date")
                })

        all_matches.sort(key=lambda x: x["similarity"], reverse=True)
        return all_matches[:10]

    def _calculate_match_confidence(self, database_matches: Dict[str, List[Dict]]) -> str:
        """
        Calculate overall match confidence based on ensemble results.

        Args:
            database_matches: Dict mapping model names to match lists

        Returns:
            Confidence level: 'high', 'medium', or 'low'
        """
        if not database_matches:
            return "low"

        # Collect top match similarities across all models
        top_similarities = []
        for model_name, matches in database_matches.items():
            if matches:
                top_similarities.append(matches[0].get("similarity", 0))

        if not top_similarities:
            return "low"

        # Calculate average and max similarity
        avg_similarity = sum(top_similarities) / len(top_similarities)
        max_similarity = max(top_similarities)

        # Count models with high-confidence matches
        high_conf_models = len([s for s in top_similarities if s > 0.85])

        # Determine confidence level
        if max_similarity > 0.95 and high_conf_models >= 2:
            return "high"
        elif max_similarity > 0.85 or (avg_similarity > 0.75 and high_conf_models >= 1):
            return "medium"
        else:
            return "low"

    async def _store_investigation_tiger(
        self,
        image_bytes: bytes,
        embeddings: Dict[str, np.ndarray],
        investigation_id: UUID,
        location: str,
        detected_tigers: List[Dict],
        existing_matches: Dict[str, List[Dict]],
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Store user-uploaded tiger in gallery and queue for review.

        Per user requirements:
        - User-uploaded tigers -> VerificationQueue with status="pending", requires_human_review=True
        - Skip if strong match found (>90% similarity)

        Args:
            image_bytes: Raw tiger image bytes
            embeddings: Dict of model_name -> embedding arrays
            investigation_id: Current investigation ID
            location: Synthesized location string
            detected_tigers: List of detected tiger dicts with crops
            existing_matches: Dict of model_name -> matches

        Returns:
            Tiger ID if new tiger created, None if skipped
        """
        from datetime import datetime
        from uuid import uuid4
        import json
        import hashlib

        if not self.db:
            logger.warning("No database session, skipping tiger storage")
            return None

        # Check if strong match found (>90% similarity) - skip if so
        max_similarity = 0.0
        best_match = None
        for model_name, matches in existing_matches.items():
            for match in matches:
                sim = match.get("similarity", 0)
                if sim > max_similarity:
                    max_similarity = sim
                    best_match = match

        if max_similarity > 0.90:
            logger.info(
                f"[STORE TIGER] Skipping - strong match found: "
                f"{best_match.get('tiger_name', 'Unknown')} ({max_similarity:.1%})"
            )
            return None

        # Get the primary embedding (prefer wildlife_tools)
        primary_embedding = None
        for model_name in ["wildlife_tools", "tiger_reid", "cvwc2019", "rapid"]:
            if model_name in embeddings and embeddings[model_name] is not None:
                primary_embedding = embeddings[model_name]
                break

        if primary_embedding is None:
            logger.warning("[STORE TIGER] No embeddings available, skipping storage")
            return None

        # Compute content hash for deduplication
        content_hash = hashlib.sha256(image_bytes).hexdigest()

        # Check if image already exists
        existing_image = self.db.query(TigerImage).filter(
            TigerImage.content_hash == content_hash
        ).first()

        if existing_image:
            logger.info(f"[STORE TIGER] Image already exists: {existing_image.image_id}")
            return str(existing_image.tiger_id)

        # Create Tiger record
        tiger_id = str(uuid4())
        tiger = Tiger(
            tiger_id=tiger_id,
            name=f"Investigation Tiger - {str(investigation_id)[:8]}",
            last_seen_location=location,
            last_seen_date=datetime.utcnow(),
            status=TigerStatus.active.value,
            is_reference=False,  # User upload, not reference data
            discovered_at=datetime.utcnow(),
            discovered_by_investigation_id=str(investigation_id),
            tags=["investigation_upload", "pending_review"],  # JSONList auto-serializes
            notes=f"User upload from Investigation {investigation_id}"
        )
        self.db.add(tiger)
        self.db.flush()

        # Get image crop if available, otherwise use full image
        image_data = image_bytes
        if detected_tigers and detected_tigers[0].get("crop"):
            image_data = detected_tigers[0]["crop"]

        # Create TigerImage with embeddings
        image_id = str(uuid4())
        image_path = f"data/storage/investigations/{investigation_id}/tiger_{tiger_id}.jpg"

        tiger_image = TigerImage(
            image_id=image_id,
            tiger_id=tiger_id,
            image_path=image_path,
            side_view=SideView.unknown.value,
            verified=False,
            is_reference=False,
            content_hash=content_hash,
            discovered_by_investigation_id=str(investigation_id),
            quality_score=context.get("image_quality", {}).get("overall_score", 0) * 100 if context.get("image_quality") else None,
            meta_data=json.dumps({
                "source": context.get("source", "user_upload"),
                "investigation_id": str(investigation_id),
                "location": location,
                "discovered_at": datetime.utcnow().isoformat(),
                "detection_confidence": detected_tigers[0].get("confidence", 0) if detected_tigers else 0
            })
        )
        self.db.add(tiger_image)

        # Store embedding in vector search for future matching
        try:
            store_embedding(self.db, image_id, primary_embedding)
            logger.info(f"[STORE TIGER] Stored embedding for image {image_id[:8]}")
        except Exception as e:
            logger.warning(f"[STORE TIGER] Failed to store embedding: {e}")

        self.db.commit()

        logger.info(
            f"[STORE TIGER] Created new tiger {tiger_id[:8]} from investigation {str(investigation_id)[:8]}"
        )
        return tiger_id

    async def _add_to_verification_queue(
        self,
        entity_type: str,
        entity_id: str,
        investigation_id: UUID,
        source: str,
        priority: str = "medium",
        notes: Optional[str] = None
    ) -> Optional[str]:
        """
        Add an entity to the verification queue for human review.

        Per user requirements:
        - All user uploads start with status="pending"
        - All require human review

        Args:
            entity_type: "tiger" or "facility"
            entity_id: The entity's ID
            investigation_id: Source investigation
            source: "user_upload" or "auto_discovery"
            priority: "high", "medium", "low"
            notes: Optional review notes

        Returns:
            Queue ID if created, None otherwise
        """
        from uuid import uuid4
        from datetime import datetime

        if not self.db:
            return None

        # Check if already in queue
        existing = self.db.query(VerificationQueue).filter(
            VerificationQueue.entity_type == entity_type,
            VerificationQueue.entity_id == entity_id
        ).first()

        if existing:
            logger.info(
                f"[VERIFICATION] {entity_type} {entity_id[:8]} already in queue"
            )
            return str(existing.queue_id)

        queue_id = str(uuid4())
        verification = VerificationQueue(
            queue_id=queue_id,
            entity_type=entity_type,
            entity_id=entity_id,
            priority=priority,
            requires_human_review=True,
            status=VerificationStatus.pending.value,  # Always pending per user requirement
            source=source,
            investigation_id=str(investigation_id),
            review_notes=notes,
            created_at=datetime.utcnow()
        )

        self.db.add(verification)
        self.db.commit()

        logger.info(
            f"[VERIFICATION] Added {entity_type} {entity_id[:8]} to queue "
            f"(source={source}, priority={priority})"
        )
        return queue_id

    def _determine_verification_priority(self, state: Investigation2State) -> str:
        """
        Determine verification priority based on investigation results.

        Args:
            state: Current investigation state

        Returns:
            Priority string: "high", "medium", or "low"
        """
        context = state.get("context", {})
        source = context.get("source", "user_upload")

        if source == "auto_discovery":
            # Auto-discoveries: priority based on detection confidence
            detected_tigers = state.get("detected_tigers", [])
            if detected_tigers:
                avg_conf = sum(d.get("confidence", 0) for d in detected_tigers) / len(detected_tigers)
                if avg_conf >= 0.95:
                    return "high"
                elif avg_conf >= 0.85:
                    return "medium"
            return "low"
        else:
            # User uploads: medium priority by default
            return "medium"

    async def _link_investigation_to_source_tiger(
        self,
        investigation_id: UUID,
        source_tiger_id: str,
        matches: Dict[str, List[Dict]],
        report: Dict
    ):
        """
        Link auto-investigation results back to source tiger.

        Updates the source tiger record with investigation findings.

        Args:
            investigation_id: The auto-investigation ID
            source_tiger_id: Tiger that triggered the investigation
            matches: Database matches found
            report: Generated report
        """
        if not self.db or not source_tiger_id:
            return

        from datetime import datetime

        try:
            tiger = self.db.query(Tiger).filter(
                Tiger.tiger_id == source_tiger_id
            ).first()

            if not tiger:
                logger.warning(f"Source tiger {source_tiger_id} not found")
                return

            # Update tiger with investigation findings
            # Note: tiger.tags uses JSONList() which auto-serializes/deserializes
            existing_tags = tiger.tags if tiger.tags else []
            if "investigated" not in existing_tags:
                existing_tags.append("investigated")
                tiger.tags = existing_tags

            # Add investigation reference to notes
            existing_notes = tiger.notes or ""
            investigation_note = f"\n[Investigation {str(investigation_id)[:8]}] Completed on {datetime.utcnow().isoformat()}"
            if report.get("confidence"):
                investigation_note += f" - Confidence: {report['confidence']}"
            tiger.notes = existing_notes + investigation_note

            self.db.commit()

            logger.info(
                f"[LINK] Linked investigation {str(investigation_id)[:8]} to source tiger {source_tiger_id[:8]}"
            )

        except Exception as e:
            logger.warning(f"Failed to link investigation to source tiger: {e}")

    async def run(
        self,
        investigation_id: UUID,
        uploaded_image: bytes,
        context: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run Investigation 2.0 workflow
        
        Args:
            investigation_id: Investigation ID
            uploaded_image: Uploaded tiger image bytes
            context: Context information (location, date, notes)
            config: Optional configuration for graph execution
        
        Returns:
            Final state with investigation results
        """
        logger.info(f"========== WORKFLOW.RUN() CALLED ==========")
        logger.info(f"Investigation ID: {investigation_id}")
        logger.info(f"Image size: {len(uploaded_image)} bytes")
        logger.info(f"Context: {context}")
        
        # Get report audience from context or default to law_enforcement
        report_audience = context.get("report_audience", "law_enforcement")

        initial_state: Investigation2State = {
            "investigation_id": str(investigation_id),
            "uploaded_image": uploaded_image,
            "image_path": None,
            "context": context,
            "uploaded_image_metadata": None,
            "reverse_search_results": None,
            "detected_tigers": None,
            "stripe_embeddings": {},
            "database_matches": {},
            "verified_candidates": None,
            "verification_applied": None,
            "verification_disagreement": None,
            "report": None,
            "reasoning_steps": [],
            "errors": [],
            "phase": "start",
            "status": "running",
            # New fields for enhanced workflow
            "reasoning_chain_id": None,
            "image_quality": None,
            "deep_research_session_id": None,
            "report_audience": report_audience
        }
        
        try:
            # Start investigation
            logger.info(f"Starting investigation in database...")
            if self.investigation_service:
                investigation = self.investigation_service.start_investigation(investigation_id)
                if not investigation:
                    raise ValueError("Investigation not found")
                logger.info(f"Investigation started in DB")
                
                # Emit investigation started event
                logger.info(f"Emitting investigation_started event...")
                await self.event_service.emit(
                    EventType.INVESTIGATION_STARTED.value,
                    {
                        "investigation_id": str(investigation_id),
                        "title": investigation.title if investigation else "Investigation 2.0"
                    },
                    investigation_id=str(investigation_id)
                )
                logger.info(f"Event emitted")
            
            # Run the graph
            if config is None:
                config = {"configurable": {"thread_id": str(investigation_id)}}
            
            logger.info(f"About to call graph.ainvoke()...")
            logger.info(f"Initial state: phase={initial_state['phase']}, status={initial_state['status']}")
            
            # Execute graph and get final state
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            logger.info(f"graph.ainvoke() completed!")
            logger.info(f"Final state: phase={final_state.get('phase')}, status={final_state.get('status')}")
            logger.info(f"========== WORKFLOW.RUN() COMPLETE ==========")
            
            return final_state
            
        except Exception as e:
            logger.error("Workflow execution failed", investigation_id=str(investigation_id), error=str(e))
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    investigation_id,
                    step_type="workflow_error",
                    agent_name="investigation2",
                    status="failed",
                    result={"error": str(e)}
                )
            raise

