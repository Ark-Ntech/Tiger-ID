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
from backend.models.detection import TigerDetectionModel
from backend.models.reid import TigerReIDModel
from backend.models.cvwc2019_reid import CVWC2019ReIDModel
from backend.models.rapid_reid import RAPIDReIDModel
from backend.models.wildlife_tools import WildlifeToolsReIDModel
from backend.models.omnivinci import OmniVinciModel
from backend.models.anthropic_chat import get_anthropic_fast_model, get_anthropic_quality_model
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
    uploaded_image_metadata: Optional[Dict[str, Any]]  # EXIF data including GPS
    reverse_search_results: Optional[List[Dict[str, Any]]]
    detected_tigers: Optional[List[Dict[str, Any]]]
    stripe_embeddings: Dict[str, np.ndarray]  # model_name -> embedding
    database_matches: Dict[str, List[Dict[str, Any]]]  # model_name -> matches
    omnivinci_comparison: Optional[Dict[str, Any]]
    report: Optional[Dict[str, Any]]
    reasoning_steps: List[Dict[str, Any]]  # Methodology tracking
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

            # Extract EXIF metadata (including GPS if available)
            exif_service = EXIFService()
            image_metadata = exif_service.extract_metadata(state["uploaded_image"])

            if image_metadata.get("gps"):
                logger.info(f"GPS data found in EXIF: {image_metadata['gps']['latitude']}, {image_metadata['gps']['longitude']}")
            else:
                logger.info("No GPS data found in image EXIF")

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
                        "has_gps": bool(image_metadata.get("gps"))
                    }
                )
            
            # Emit completion event
            await self.event_service.emit(
                EventType.PHASE_COMPLETED.value,
                {"phase": "upload_and_parse", "agent": "investigation2"},
                investigation_id=state["investigation_id"]
            )

            # Initialize reasoning steps
            reasoning_steps = state.get("reasoning_steps", [])
            reasoning_steps.append({
                "step": len(reasoning_steps) + 1,
                "phase": "upload_and_parse",
                "action": f"Uploaded and validated image ({len(state['uploaded_image'])} bytes)",
                "reasoning": "Parsed user context and extracted image metadata",
                "evidence": [
                    f"Image format: {image_metadata.get('image_info', {}).get('format', 'unknown')}",
                    f"GPS data: {'found' if image_metadata.get('gps') else 'not found'}",
                    f"Context location: {state.get('context', {}).get('location', 'not provided')}"
                ],
                "conclusion": "Image ready for analysis" + (" with GPS coordinates" if image_metadata.get("gps") else ""),
                "confidence": 100
            })

            return {
                **state,
                "uploaded_image_metadata": image_metadata,
                "reasoning_steps": reasoning_steps,
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
            if citations:
                reasoning_steps.append({
                    "step": len(reasoning_steps) + 1,
                    "phase": "Web Intelligence",
                    "action": f"Executed Anthropic web search with query: {search_query}",
                    "reasoning": f"Generated optimized query based on location ({location}) and context to find tiger trafficking intelligence",
                    "evidence": [
                        f"Found {len(citations)} web sources",
                        f"Generated {len(summary)} character summary",
                        f"Search focused on: {location}"
                    ],
                    "conclusion": f"High confidence web intelligence gathered from {len(citations)} authoritative sources",
                    "confidence": 85 if len(citations) > 5 else 60
                })
            else:
                reasoning_steps.append({
                    "step": len(reasoning_steps) + 1,
                    "phase": "Web Intelligence",
                    "action": f"Attempted web search with query: {search_query}",
                    "reasoning": f"Generated optimized query based on location ({location}) and context to find tiger trafficking intelligence",
                    "evidence": [
                        "No web sources returned from search providers",
                        f"Search focused on: {location}",
                        "This may be due to API limitations or no matching results"
                    ],
                    "conclusion": "Web intelligence unavailable - proceeding with other analysis methods",
                    "confidence": 30
                })

            return {
                **state,
                "reverse_search_results": reverse_search_results,
                "reasoning_steps": reasoning_steps,
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
            avg_conf = sum(d["confidence"] for d in detected_tigers) / len(detected_tigers) if detected_tigers else 0
            reasoning_steps.append({
                "step": len(reasoning_steps) + 1,
                "phase": "Tiger Detection",
                "action": f"Ran MegaDetector on uploaded image",
                "reasoning": "Used state-of-the-art wildlife detection model to identify tiger presence and location in image",
                "evidence": [
                    f"Detected {len(detected_tigers)} tiger(s)",
                    f"Average confidence: {avg_conf:.1%}",
                    f"Bounding boxes extracted for stripe analysis"
                ],
                "conclusion": f"Successfully detected {len(detected_tigers)} tiger(s) with {avg_conf:.1%} average confidence",
                "confidence": int(avg_conf * 100) if detected_tigers else 50
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
            reasoning_steps.append({
                "step": len(reasoning_steps) + 1,
                "phase": "ReID Analysis",
                "action": f"Ran {len(stripe_embeddings)} ReID models for stripe pattern matching",
                "reasoning": "Used ensemble of tiger re-identification models (TigerReID, CVWC2019, RAPID, Wildlife-Tools) to match stripe patterns against database",
                "evidence": [
                    f"Generated embeddings from {len(stripe_embeddings)} models",
                    f"Found {total_matches} potential matches across all models",
                    f"Searched database of reference tigers"
                ],
                "conclusion": f"Stripe analysis complete: {total_matches} potential matches identified",
                "confidence": 90 if total_matches > 0 else 60
            })

            return {
                **state,
                "stripe_embeddings": stripe_embeddings,
                "database_matches": database_matches,
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
            
            # Try OmniVinci for deep visual analysis (graceful failure)
            image_bytes = state.get("uploaded_image")
            
            visual_analysis_text = ""
            analysis_type = "automated_only"
            
            try:
                logger.info("Attempting OmniVinci visual analysis...")
                omnivinci_result = await omnivinci_model.analyze_image(
                    image_bytes=image_bytes,
                    prompt=prompt
                )
                
                if omnivinci_result.get("success"):
                    visual_analysis_text = omnivinci_result.get("analysis", "")
                    analysis_type = "omnivinci_omnimodal"
                    logger.info(f"OmniVinci analysis completed: {len(visual_analysis_text)} characters")
                else:
                    logger.warning(f"OmniVinci unavailable: {omnivinci_result.get('error', 'Unknown')}")
                    visual_analysis_text = "OmniVinci visual analysis not available."
            
            except Exception as e:
                # Gracefully handle OmniVinci errors - don't block workflow
                logger.warning(f"OmniVinci error (non-blocking): {str(e)[:100]}")
                visual_analysis_text = "OmniVinci analysis skipped due to service unavailability."
            
            # Create comparison result (with or without OmniVinci)
            comparison_result = {
                "visual_analysis": visual_analysis_text,
                "top_matches": top_matches,
                "analysis_type": analysis_type,
                "confidence": "high" if top_matches and top_matches[0]["similarity"] > 0.9 else "medium",
                "models_consensus": len([m for m in top_matches if m["similarity"] > 0.85]),
                "omnivinci_available": analysis_type == "omnivinci_omnimodal"
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

            # Add reasoning step
            reasoning_steps = state.get("reasoning_steps", [])
            reasoning_steps.append({
                "step": len(reasoning_steps) + 1,
                "phase": "Visual Analysis",
                "action": f"Analyzed top {len(top_matches)} matches using OmniVinci vision model",
                "reasoning": "Used multi-modal AI to visually compare stripe patterns and provide detailed analysis of match quality",
                "evidence": [
                    f"Compared {len(top_matches)} candidate matches",
                    f"Generated detailed visual analysis",
                    f"Confidence level: {comparison_result.get('confidence', 'medium')}"
                ],
                "conclusion": f"Visual comparison complete with {comparison_result.get('confidence', 'medium')} confidence",
                "confidence": {"high": 90, "medium": 70, "low": 50}.get(comparison_result.get('confidence', 'medium'), 70)
            })

            return {
                **state,
                "omnivinci_comparison": comparison_result,
                "reasoning_steps": reasoning_steps,
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
        """Generate investigation report using Anthropic Claude"""
        try:
            logger.info("Starting report generation with Anthropic Claude", investigation_id=state["investigation_id"])

            # Emit event
            await self.event_service.emit(
                EventType.PHASE_STARTED.value,
                {"phase": "report_generation", "agent": "investigation2"},
                investigation_id=state["investigation_id"]
            )

            # Collect all findings
            reverse_search = state.get("reverse_search_results", {})
            detected_tigers = state.get("detected_tigers", [])
            database_matches = state.get("database_matches", {})
            omnivinci_comparison = state.get("omnivinci_comparison", {})
            context = state.get("context", {})

            # Extract OmniVinci's visual analysis if available
            visual_analysis = ""
            if omnivinci_comparison and omnivinci_comparison.get('visual_analysis'):
                visual_analysis = f"""

## OmniVinci Visual Analysis (Omni-Modal LLM Assessment)
{omnivinci_comparison['visual_analysis']}

Analysis Type: {omnivinci_comparison.get('analysis_type', 'automated')}
Confidence Level: {omnivinci_comparison.get('confidence', 'medium')}
"""

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
{visual_analysis}

---

**REPORT REQUIREMENTS:**

Generate a structured professional report with these sections:

### 1. EXECUTIVE SUMMARY (3-4 sentences)
- Synthesize key findings from detection, matching, visual analysis, and web intelligence
- State confidence level and reliability
- Mention any critical concerns or high-confidence matches

### 2. DETECTION & IDENTIFICATION FINDINGS
- Tiger detection results and confidence
- Stripe matching results across all models
- Consensus analysis (where multiple models agree)
- **Incorporate OmniVinci's detailed visual observations**

### 3. WEB INTELLIGENCE & EXTERNAL CONTEXT
- Synthesize findings from Anthropic web search
- Relevant tiger trafficking incidents or facilities in the region
- Law enforcement or conservation activities
- Any external references that provide context

### 4. VISUAL & BEHAVIORAL ANALYSIS
- **Use OmniVinci's insights** on physical characteristics, pose, behavior
- Image quality and identification suitability
- Environmental context and implications

### 5. MATCH CONFIDENCE ASSESSMENT
- Evaluate top matches with cross-model validation
- Discuss agreement/disagreement between models
- Assess reliability given image quality and database coverage

### 6. INVESTIGATIVE RECOMMENDATIONS
**Immediate Actions:**
- Specific next steps based on findings
- Additional data needed
- Verification methods

**Follow-up Investigation:**
- Field work recommendations
- Database expansion needs
- Expert review requirements

### 7. CONCLUSION
- Final assessment of identification confidence
- Key uncertainties or limitations
- Overall investigative outlook

**TONE:** Professional, evidence-based, suitable for law enforcement and conservation officials.
**FORMAT:** Clear sections with bullet points and specific details.
**LENGTH:** Comprehensive but concise - focus on actionable intelligence."""

            # Use Anthropic quality model for high-quality report generation
            anthropic_quality = get_anthropic_quality_model()

            logger.info("[REPORT] Generating report with Anthropic Claude...")
            result = await anthropic_quality.chat(
                message=prompt,
                enable_web_search=False,
                max_tokens=4096,
                temperature=0.7
            )

            if not result.get("success"):
                raise RuntimeError(f"Report generation failed: {result.get('error')}")

            report_text = result.get("response", "")
            logger.info(f"[REPORT] Generated report: {len(report_text)} chars")

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
                "confidence": omnivinci_comparison.get('confidence', 'medium') if omnivinci_comparison else 'medium',
                "model_used": anthropic_quality.model_name
            }

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

            # Add reasoning step
            reasoning_steps = state.get("reasoning_steps", [])
            reasoning_steps.append({
                "step": len(reasoning_steps) + 1,
                "phase": "Report Generation",
                "action": f"Generated comprehensive investigation report using Anthropic Claude",
                "reasoning": "Synthesized all findings from web intelligence, detection, ReID analysis, and visual comparison into cohesive narrative",
                "evidence": [
                    f"Generated {len(report_text)} character report",
                    f"Incorporated data from {len(database_matches)} models",
                    f"Total matches analyzed: {sum(len(m) for m in database_matches.values())}",
                    f"Overall confidence: {report.get('confidence', 'medium')}"
                ],
                "conclusion": f"Investigation complete: comprehensive report generated with {report.get('confidence', 'medium')} confidence",
                "confidence": {"high": 95, "medium": 75, "low": 55}.get(report.get('confidence', 'medium'), 75)
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
            try:
                auto_discovery = AutoDiscoveryService(self.db)
                discovery_result = await auto_discovery.process_investigation_discovery(
                    investigation_id=investigation_id,
                    uploaded_image=state.get("uploaded_image"),
                    stripe_embeddings=state.get("stripe_embeddings", {}),
                    existing_matches=state.get("database_matches", {}),
                    web_intelligence=state.get("reverse_search_results", {}),
                    context=state.get("context", {})
                )

                if discovery_result:
                    report["new_discovery"] = discovery_result
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

