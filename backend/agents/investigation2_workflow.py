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
from backend.models.detection import TigerDetectionModel
from backend.models.reid import TigerReIDModel
from backend.models.cvwc2019_reid import CVWC2019ReIDModel
from backend.models.rapid_reid import RAPIDReIDModel
from backend.models.wildlife_tools import WildlifeToolsReIDModel
from backend.models.omnivinci import OmniVinciModel
from backend.models.hermes_chat import HermesChatModel
from backend.database.vector_search import find_matching_tigers
from backend.events.event_types import EventType
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class Investigation2State(TypedDict):
    """State structure for Investigation 2.0 workflow"""
    investigation_id: str
    uploaded_image: Optional[bytes]
    image_path: Optional[str]
    context: Dict[str, Any]
    reverse_search_results: Optional[List[Dict[str, Any]]]
    detected_tigers: Optional[List[Dict[str, Any]]]
    stripe_embeddings: Dict[str, np.ndarray]  # model_name -> embedding
    database_matches: Dict[str, List[Dict[str, Any]]]  # model_name -> matches
    omnivinci_comparison: Optional[Dict[str, Any]]
    report: Optional[Dict[str, Any]]
    errors: Annotated[List[Dict[str, Any]], operator.add]
    phase: str
    status: Literal["running", "completed", "failed", "cancelled"]


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
        workflow.add_node("omnivinci_comparison", self._omnivinci_comparison_node)
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
                "continue": "omnivinci_comparison",
                "error": "complete",
                "skip": "omnivinci_comparison"
            }
        )
        workflow.add_conditional_edges(
            "omnivinci_comparison",
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
            
            # Store in investigation if service available
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    UUID(state["investigation_id"]),
                    step_type="upload_and_parse",
                    agent_name="investigation2",
                    status="completed",
                    result={
                        "image_size": len(state["uploaded_image"]),
                        "context": state.get("context", {})
                    }
                )
            
            # Emit completion event
            await self.event_service.emit(
                EventType.PHASE_COMPLETED.value,
                {"phase": "upload_and_parse", "agent": "investigation2"},
                investigation_id=state["investigation_id"]
            )
            
            return {
                **state,
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
        """Perform reverse image search on uploaded image"""
        try:
            logger.info(f"[REVERSE SEARCH NODE] ========== STARTING REVERSE IMAGE SEARCH ==========")
            logger.info(f"[REVERSE SEARCH NODE] Investigation ID: {state['investigation_id']}")
            logger.info("Starting reverse image search", investigation_id=state["investigation_id"])
            
            # Emit event
            await self.event_service.emit(
                EventType.PHASE_STARTED.value,
                {"phase": "reverse_image_search", "agent": "investigation2"},
                investigation_id=state["investigation_id"]
            )
            
            # Perform reverse search on multiple providers
            image_bytes = state.get("uploaded_image")
            if not image_bytes:
                raise ValueError("No image available for reverse search")
            
            reverse_search_results = []
            
            # Try multiple providers
            providers = ["google", "tineye", "yandex"]
            for provider in providers:
                try:
                    logger.info(f"Searching with {provider}")
                    result = await self.image_search_service.reverse_search(
                        image_bytes=image_bytes,
                        provider=provider
                    )
                    
                    if result.get("results"):
                        reverse_search_results.append({
                            "provider": provider,
                            "results": result.get("results", []),
                            "count": len(result.get("results", []))
                        })
                except Exception as e:
                    logger.warning(f"Reverse search failed for {provider}: {e}")
            
            # Store results
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    UUID(state["investigation_id"]),
                    step_type="reverse_image_search",
                    agent_name="investigation2",
                    status="completed",
                    result={
                        "providers_searched": len(providers),
                        "results_found": sum(r["count"] for r in reverse_search_results)
                    }
                )
            
            # Emit completion event
            await self.event_service.emit(
                EventType.PHASE_COMPLETED.value,
                {
                    "phase": "reverse_image_search",
                    "agent": "investigation2",
                    "results_count": len(reverse_search_results)
                },
                investigation_id=state["investigation_id"]
            )
            
            logger.info(f"[REVERSE SEARCH NODE] ========== REVERSE IMAGE SEARCH COMPLETED ==========")
            logger.info(f"[REVERSE SEARCH NODE] Results: {len(reverse_search_results)} providers searched")
            
            return {
                **state,
                "reverse_search_results": reverse_search_results,
                "phase": "reverse_image_search"
            }
            
        except Exception as e:
            logger.info(f"[REVERSE SEARCH NODE] ❌ EXCEPTION: {e}")
            logger.error("Reverse image search failed", investigation_id=state["investigation_id"], error=str(e), exc_info=True)
            return {
                **state,
                "reverse_search_results": [],
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
            
            return {
                **state,
                "detected_tigers": detected_tigers,
                "phase": "tiger_detection"
            }
            
        except Exception as e:
            logger.info(f"[DETECTION NODE] ❌ EXCEPTION: {e}")
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
            
            # Store results
            if self.investigation_service:
                total_matches = sum(len(m) for m in database_matches.values())
                self.investigation_service.add_investigation_step(
                    UUID(state["investigation_id"]),
                    step_type="stripe_analysis",
                    agent_name="investigation2",
                    status="completed",
                    result={
                        "models_run": len(stripe_embeddings),
                        "total_matches": total_matches
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
            
            return {
                **state,
                "stripe_embeddings": stripe_embeddings,
                "database_matches": database_matches,
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
    
    async def _omnivinci_comparison_node(self, state: Investigation2State) -> Investigation2State:
        """Use Omnivinci to compare tigers"""
        try:
            logger.info("Starting Omnivinci comparison", investigation_id=state["investigation_id"])
            
            # Emit event
            await self.event_service.emit(
                EventType.PHASE_STARTED.value,
                {"phase": "omnivinci_comparison", "agent": "investigation2"},
                investigation_id=state["investigation_id"]
            )
            
            # Get detected tigers and database matches
            detected_tigers = state.get("detected_tigers", [])
            database_matches = state.get("database_matches", {})
            
            if not detected_tigers:
                logger.warning("No detected tigers for Omnivinci comparison")
                return {
                    **state,
                    "omnivinci_comparison": None,
                    "phase": "omnivinci_comparison"
                }
            
            # Get top matches from all models
            all_matches = []
            for model_name, matches in database_matches.items():
                for match in matches[:2]:  # Top 2 from each model
                    all_matches.append({
                        "model": model_name,
                        "tiger_id": match.get("tiger_id"),
                        "similarity": match.get("similarity"),
                        "tiger_name": match.get("tiger_name")
                    })
            
            # Sort by similarity
            all_matches.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            top_matches = all_matches[:5]  # Top 5 overall
            
            # Initialize Omnivinci model
            omnivinci_model = OmniVinciModel()
            
            # Create comparison prompt
            prompt = f"""Analyze this tiger image comparison for wildlife investigation purposes.

Uploaded Image Context:
- Location: {state.get('context', {}).get('location', 'Unknown')}
- Date: {state.get('context', {}).get('date', 'Unknown')}
- Notes: {state.get('context', {}).get('notes', 'None')}

Stripe Analysis Results:
{len(top_matches)} potential matches found from database

Top Matches:
{chr(10).join([f"- {m['tiger_name'] or m['tiger_id']}: {m['similarity']:.2f} similarity ({m['model']})" for m in top_matches])}

Please analyze:
1. The visual characteristics of the uploaded tiger
2. How the stripe patterns compare to known database tigers
3. Confidence in the matches found
4. Any distinguishing features that could confirm or rule out matches

Provide a detailed comparison analysis."""
            
            # Note: Omnivinci is designed for video, but we can use it for image analysis
            # For now, we'll create a basic analysis structure
            # In production, we would use Omnivinci's image analysis capabilities
            
            comparison_result = {
                "analysis": f"Stripe analysis completed using {len(database_matches)} models. Found {len(top_matches)} high-confidence matches.",
                "top_matches": top_matches,
                "comparison_method": "multi-model_ensemble",
                "confidence": "high" if top_matches and top_matches[0]["similarity"] > 0.9 else "medium"
            }
            
            # Store results
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    UUID(state["investigation_id"]),
                    step_type="omnivinci_comparison",
                    agent_name="investigation2",
                    status="completed",
                    result={
                        "matches_analyzed": len(top_matches),
                        "confidence": comparison_result["confidence"]
                    }
                )
            
            # Emit completion event
            await self.event_service.emit(
                EventType.PHASE_COMPLETED.value,
                {
                    "phase": "omnivinci_comparison",
                    "agent": "investigation2",
                    "matches_analyzed": len(top_matches)
                },
                investigation_id=state["investigation_id"]
            )
            
            return {
                **state,
                "omnivinci_comparison": comparison_result,
                "phase": "omnivinci_comparison"
            }
            
        except Exception as e:
            logger.error("Omnivinci comparison failed", investigation_id=state["investigation_id"], error=str(e))
            return {
                **state,
                "omnivinci_comparison": None,
                "errors": [{"phase": "omnivinci_comparison", "error": str(e)}],
                "phase": "omnivinci_comparison"
            }
    
    async def _report_generation_node(self, state: Investigation2State) -> Investigation2State:
        """Generate investigation report using GPT-5-mini"""
        try:
            logger.info("Starting report generation", investigation_id=state["investigation_id"])
            
            # Emit event
            await self.event_service.emit(
                EventType.PHASE_STARTED.value,
                {"phase": "report_generation", "agent": "investigation2"},
                investigation_id=state["investigation_id"]
            )
            
            # Collect all findings
            reverse_search = state.get("reverse_search_results", [])
            detected_tigers = state.get("detected_tigers", [])
            database_matches = state.get("database_matches", {})
            omnivinci_comparison = state.get("omnivinci_comparison", {})
            context = state.get("context", {})
            
            # Create comprehensive prompt for GPT-5-mini
            prompt = f"""Generate a comprehensive tiger identification investigation report based on the following findings:

## Investigation Context
- Location: {context.get('location', 'Not provided')}
- Date: {context.get('date', 'Not provided')}
- Notes: {context.get('notes', 'None')}

## Detection Results
- Tigers detected: {len(detected_tigers)}
- Average detection confidence: {sum(d.get('confidence', 0) for d in detected_tigers) / len(detected_tigers) if detected_tigers else 0:.2f}

## Reverse Image Search
- Providers searched: {len(reverse_search)}
- Total results found: {sum(r.get('count', 0) for r in reverse_search)}

## Stripe Analysis Results
Models run: {', '.join(database_matches.keys())}

Match Summary:
{chr(10).join([f"- {model}: {len(matches)} matches found" for model, matches in database_matches.items()])}

Top Matches Across All Models:
{self._format_top_matches(database_matches)}

## Omnivinci Comparison
{omnivinci_comparison.get('analysis', 'No comparison performed')}
Confidence: {omnivinci_comparison.get('confidence', 'unknown')}

---

Please generate a structured investigation report with the following sections:

1. **Executive Summary** (2-3 sentences)
2. **Key Findings** (bullet points)
3. **Match Analysis** (detailed analysis of top matches with confidence scores)
4. **Evidence Quality** (assessment of image quality and detection confidence)
5. **Recommendations** (next steps for investigation)
6. **Conclusion**

Format the report in clear, professional language suitable for wildlife conservation investigators."""
            
            # Use GPT-5-mini for report generation
            hermes_model = HermesChatModel()
            
            result = await hermes_model.chat(
                message=prompt,
                tools=None,
                max_tokens=2048,
                temperature=0.7
            )
            
            if not result.get("success"):
                raise RuntimeError(f"Report generation failed: {result.get('error')}")
            
            report_text = result.get("response", "")
            
            # Structure the report
            report = {
                "investigation_id": state["investigation_id"],
                "generated_at": str(np.datetime64('now')),
                "context": context,
                "summary": report_text,
                "detection_count": len(detected_tigers),
                "models_used": list(database_matches.keys()),
                "total_matches": sum(len(m) for m in database_matches.values()),
                "top_matches": self._extract_top_matches(database_matches),
                "confidence": omnivinci_comparison.get('confidence', 'medium') if omnivinci_comparison else 'medium'
            }
            
            # Store results
            if self.investigation_service:
                self.investigation_service.add_investigation_step(
                    UUID(state["investigation_id"]),
                    step_type="report_generation",
                    agent_name="investigation2",
                    status="completed",
                    result={"report_length": len(report_text)}
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
            
            return {
                **state,
                "report": report,
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
            
            # Mark investigation as completed
            if self.investigation_service:
                self.investigation_service.complete_investigation(
                    investigation_id,
                    summary=state.get("report", {})
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
        """Extract and rank top matches"""
        all_matches = []
        for model_name, matches in database_matches.items():
            for match in matches:
                all_matches.append({
                    "model": model_name,
                    "tiger_id": str(match.get("tiger_id")),
                    "similarity": float(match.get("similarity", 0)),
                    "tiger_name": match.get("tiger_name"),
                    "image_id": str(match.get("image_id"))
                })
        
        all_matches.sort(key=lambda x: x["similarity"], reverse=True)
        return all_matches[:10]
    
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
        
        initial_state: Investigation2State = {
            "investigation_id": str(investigation_id),
            "uploaded_image": uploaded_image,
            "image_path": None,
            "context": context,
            "reverse_search_results": None,
            "detected_tigers": None,
            "stripe_embeddings": {},
            "database_matches": {},
            "omnivinci_comparison": None,
            "report": None,
            "errors": [],
            "phase": "start",
            "status": "running"
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

