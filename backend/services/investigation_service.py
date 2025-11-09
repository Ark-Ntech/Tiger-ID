"""Service layer for Investigation operations"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database.models import (
    Investigation, InvestigationStep, Evidence, 
    VerificationQueue, InvestigationComment
)


class InvestigationService:
    """Service for investigation-related operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_investigation(
        self,
        title: str,
        created_by: UUID,
        description: Optional[str] = None,
        priority: str = "medium",
        tags: Optional[List[str]] = None,
        assigned_to: Optional[List[UUID]] = None
    ) -> Investigation:
        """Create a new investigation"""
        investigation = Investigation(
            title=title,
            description=description,
            created_by=created_by,
            status="draft",
            priority=priority,
            tags=tags or [],
            assigned_to=[str(uuid) for uuid in (assigned_to or [])]
        )
        self.session.add(investigation)
        self.session.commit()
        self.session.refresh(investigation)
        return investigation
    
    def get_investigation(self, investigation_id: UUID) -> Optional[Investigation]:
        """Get investigation by ID"""
        return self.session.query(Investigation).filter(
            Investigation.investigation_id == investigation_id
        ).first()
    
    def get_investigations(
        self,
        status: Optional[str] = None,
        created_by: Optional[UUID] = None,
        assigned_to: Optional[UUID] = None,
        priority: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Investigation]:
        """Get list of investigations with filters"""
        query = self.session.query(Investigation)
        
        if status:
            query = query.filter(Investigation.status == status)
        
        if created_by:
            query = query.filter(Investigation.created_by == created_by)
        
        if assigned_to:
            query = query.filter(
                Investigation.assigned_to.contains([str(assigned_to)])
            )
        
        if priority:
            query = query.filter(Investigation.priority == priority)
        
        return query.order_by(Investigation.created_at.desc()).limit(limit).offset(offset).all()
    
    def update_investigation(
        self,
        investigation_id: UUID,
        **updates
    ) -> Optional[Investigation]:
        """Update investigation record"""
        investigation = self.get_investigation(investigation_id)
        if not investigation:
            return None
        
        for key, value in updates.items():
            if hasattr(investigation, key):
                setattr(investigation, key, value)
        
        self.session.commit()
        self.session.refresh(investigation)
        return investigation
    
    def start_investigation(self, investigation_id: UUID) -> Optional[Investigation]:
        """Start an investigation"""
        investigation = self.get_investigation(investigation_id)
        if not investigation:
            return None
        
        investigation.status = "active"
        investigation.started_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(investigation)
        return investigation
    
    def pause_investigation(self, investigation_id: UUID) -> Optional[Investigation]:
        """Pause an investigation"""
        investigation = self.get_investigation(investigation_id)
        if not investigation:
            return None
        
        if investigation.status not in ["active", "in_progress"]:
            raise ValueError(f"Cannot pause investigation with status: {investigation.status}")
        
        investigation.status = "paused"
        self.session.commit()
        self.session.refresh(investigation)
        return investigation
    
    def resume_investigation(self, investigation_id: UUID) -> Optional[Investigation]:
        """Resume a paused investigation"""
        investigation = self.get_investigation(investigation_id)
        if not investigation:
            return None
        
        if investigation.status != "paused":
            raise ValueError(f"Cannot resume investigation with status: {investigation.status}")
        
        investigation.status = "in_progress"
        self.session.commit()
        self.session.refresh(investigation)
        return investigation
    
    def cancel_investigation(self, investigation_id: UUID, reason: Optional[str] = None) -> Optional[Investigation]:
        """Cancel an investigation"""
        investigation = self.get_investigation(investigation_id)
        if not investigation:
            return None
        
        if investigation.status in ["completed", "cancelled"]:
            raise ValueError(f"Cannot cancel investigation with status: {investigation.status}")
        
        investigation.status = "cancelled"
        if reason:
            if not investigation.summary:
                investigation.summary = {}
            investigation.summary["cancellation_reason"] = reason
        
        self.session.commit()
        self.session.refresh(investigation)
        return investigation
    
    def complete_investigation(
        self,
        investigation_id: UUID,
        summary: Optional[Dict[str, Any]] = None
    ) -> Optional[Investigation]:
        """Complete an investigation"""
        investigation = self.get_investigation(investigation_id)
        if not investigation:
            return None
        
        investigation.status = "completed"
        investigation.completed_at = datetime.utcnow()
        if summary:
            investigation.summary = summary
        
        self.session.commit()
        self.session.refresh(investigation)
        return investigation
    
    def add_investigation_step(
        self,
        investigation_id: UUID,
        step_type: str,
        agent_name: Optional[str] = None,
        status: str = "pending",
        result: Optional[Dict[str, Any]] = None,
        parent_step_id: Optional[UUID] = None
    ) -> InvestigationStep:
        """Add a step to an investigation"""
        step = InvestigationStep(
            investigation_id=investigation_id,
            step_type=step_type,
            agent_name=agent_name,
            status=status,
            result=result or {},
            parent_step_id=parent_step_id
        )
        self.session.add(step)
        self.session.commit()
        self.session.refresh(step)
        return step
    
    def add_evidence(
        self,
        investigation_id: UUID,
        source_type: str,
        source_url: Optional[str] = None,
        content: Optional[Dict[str, Any]] = None,
        extracted_text: Optional[str] = None,
        relevance_score: Optional[float] = None
    ) -> Evidence:
        """Add evidence to an investigation"""
        evidence = Evidence(
            investigation_id=investigation_id,
            source_type=source_type,
            source_url=source_url,
            content=content or {},
            extracted_text=extracted_text,
            relevance_score=relevance_score
        )
        self.session.add(evidence)
        self.session.commit()
        self.session.refresh(evidence)
        return evidence
    
    def get_investigation_steps(self, investigation_id: UUID) -> List[InvestigationStep]:
        """Get all steps for an investigation"""
        return self.session.query(InvestigationStep).filter(
            InvestigationStep.investigation_id == investigation_id
        ).order_by(InvestigationStep.timestamp).all()
    
    def get_investigation_evidence(self, investigation_id: UUID) -> List[Evidence]:
        """Get all evidence for an investigation"""
        return self.session.query(Evidence).filter(
            Evidence.investigation_id == investigation_id
        ).order_by(Evidence.created_at).all()
    
    def _save_investigation_state(
        self,
        investigation_id: UUID,
        current_phase: str,
        state_data: Dict[str, Any]
    ):
        """Save investigation state for pause/resume"""
        investigation = self.get_investigation(investigation_id)
        if not investigation:
            return
        
        if not investigation.summary:
            investigation.summary = {}
        
        investigation.summary['_state'] = {
            'phase': current_phase,
            'data': state_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.session.commit()
    
    def _load_investigation_state(self, investigation_id: UUID) -> Optional[Dict[str, Any]]:
        """Load saved investigation state"""
        investigation = self.get_investigation(investigation_id)
        if investigation and investigation.summary and isinstance(investigation.summary, dict):
            return investigation.summary.get('_state')
        return None
    
    def _classify_request(self, user_input: str, has_files: bool = False) -> str:
        """
        Classify user request as 'investigation' or 'chat'.
        
        Args:
            user_input: User's message
            has_files: Whether files were uploaded
            
        Returns:
            'investigation' or 'chat'
        """
        # If files uploaded, it's likely an investigation
        if has_files:
            return 'investigation'
        
        # Check for investigation keywords
        investigation_keywords = [
            'investigate', 'check', 'verify', 'find', 'search',
            'analyze', 'research', 'look into', 'examine', 'inspect',
            'facility', 'violation', 'permit', 'compliance', 'trafficking'
        ]
        
        # Check for chat keywords
        chat_keywords = [
            'hello', 'hi', 'hey', 'what', 'how', 'can you',
            'tell me', 'explain', 'help', 'thanks', 'thank you'
        ]
        
        user_lower = user_input.lower()
        
        # Count keywords
        investigation_score = sum(1 for kw in investigation_keywords if kw in user_lower)
        chat_score = sum(1 for kw in chat_keywords if kw in user_lower)
        
        # If clearly chat
        if chat_score > investigation_score and len(user_input.split()) < 10:
            return 'chat'
        
        # If investigation keywords present
        if investigation_score > 0:
            return 'investigation'
        
        # Default to chat for short messages
        if len(user_input.split()) < 5:
            return 'chat'
        
        # Default to investigation for longer, detailed requests
        return 'investigation'
    
    async def launch_investigation(
        self,
        investigation_id: UUID,
        user_input: str,
        files: List[Any],
        user_id: UUID,
        selected_tools: Optional[List[str]] = None,
        tiger_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Launch an investigation with user input and files using the OpenAI chat orchestrator (or OmniVinci for video)"""
        from backend.models.hermes_chat import get_hermes_chat_model
        from backend.models.omnivinci import get_omnivinci_model
        from backend.api.mcp_tools_routes import list_mcp_tools
        from backend.database import get_db_session
        from backend.utils.logging import get_logger
        from pathlib import Path
        import tempfile
        import os
        import httpx
        
        logger = get_logger(__name__)
        
        # Classify request type
        request_type = self._classify_request(user_input, has_files=len(files) > 0)
        logger.info(f"Request classified as: {request_type}")
        
        # Update investigation status
        investigation = self.get_investigation(investigation_id)
        if not investigation:
            raise ValueError("Investigation not found")
        
        # Check if investigation is paused or cancelled
        if investigation.status == "paused":
            raise ValueError("Cannot launch paused investigation. Please resume it first.")
        if investigation.status == "cancelled":
            raise ValueError("Cannot launch cancelled investigation.")
        
        investigation = self.start_investigation(investigation_id)
        self.session.commit()
        self.session.refresh(investigation)
        
        # Process files
        file_data: List[Dict[str, Any]] = []
        video_path = None
        image_files: List[Tuple[Any, Dict[str, Any]]] = []
        for file in files:
            entry = {
                "name": getattr(file, "filename", "unknown"),
                "type": getattr(file, "content_type", "unknown"),
            }
            file_data.append(entry)
            content_type = (getattr(file, "content_type", "") or "").lower()
            
            if content_type.startswith("video/"):
                try:
                    video_bytes = await file.read()
                    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
                        tmp_file.write(video_bytes)
                        video_path = Path(tmp_file.name)
                except Exception as e:
                    logger.warning(f"Could not save video file: {e}")
            elif content_type.startswith("image/"):
                image_files.append((file, entry))
        
        tiger_id_value = str(tiger_id) if tiger_id else None
        tiger_event_payload: Optional[Dict[str, Any]] = None
        tiger_image_urls: List[str] = []
        tiger_service = None
        
        if (image_files and not tiger_id_value) or tiger_id_value:
            from backend.services.tiger_service import TigerService
            tiger_service = TigerService(self.session)
        
        if tiger_service and image_files and not tiger_id_value:
            # Attempt to identify existing tiger from uploaded images
            for upload_file, entry in image_files:
                try:
                    await upload_file.seek(0)
                    identify_result = await tiger_service.identify_tiger_from_image(
                        image=upload_file,
                        user_id=user_id,
                        similarity_threshold=0.7,
                        model_name=None
                    )
                    if identify_result.get("identified") and identify_result.get("tiger_id"):
                        tiger_id_value = str(identify_result.get("tiger_id"))
                        entry["identified_tiger_id"] = tiger_id_value
                        entry["tiger_confidence"] = identify_result.get("confidence")
                        tiger_event_payload = {
                            "tiger_id": tiger_id_value,
                            "tiger_name": identify_result.get("tiger_name"),
                            "confidence": identify_result.get("confidence"),
                            "is_new": False,
                        }
                        logger.info(f"Identified tiger {tiger_id_value} from uploaded image {entry['name']}")
                        break
                except Exception as e:
                    logger.warning(f"Automatic tiger identification failed: {e}")
                finally:
                    try:
                        await upload_file.seek(0)
                    except Exception:
                        pass
        
        if tiger_service and image_files and not tiger_id_value:
            # Register new tiger from uploaded images if none identified
            try:
                for upload_file, _ in image_files:
                    try:
                        await upload_file.seek(0)
                    except Exception:
                        pass
                registered = await tiger_service.register_new_tiger(
                    name=f"Investigation Tiger {datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    alias=None,
                    images=[upload_file for upload_file, _ in image_files],
                    notes="Registered via investigation assistant upload",
                    model_name=None,
                    user_id=user_id
                )
                if registered and registered.get("tiger_id"):
                    tiger_id_value = str(registered.get("tiger_id"))
                    tiger_event_payload = {
                        "tiger_id": tiger_id_value,
                        "tiger_name": registered.get("name"),
                        "confidence": None,
                        "is_new": True,
                    }
                    for _, entry in image_files:
                        entry["registered_tiger_id"] = tiger_id_value
                    logger.info(f"Registered new tiger {tiger_id_value} from investigation upload")
            except Exception as e:
                logger.warning(f"Failed to register new tiger from uploaded images: {e}")
            finally:
                for upload_file, _ in image_files:
                    try:
                        await upload_file.seek(0)
                    except Exception:
                        pass
        
        if tiger_service and tiger_id_value:
            try:
                tiger_details = await tiger_service.get_tiger(UUID(tiger_id_value))
                if tiger_details:
                    tiger_images = tiger_details.get("images") or []
                    tiger_image_urls = [
                        img.get("image_path")
                        for img in tiger_images
                        if isinstance(img, dict) and img.get("image_path")
                    ]
                    if tiger_event_payload is None:
                        tiger_event_payload = {
                            "tiger_id": tiger_id_value,
                            "tiger_name": tiger_details.get("name"),
                            "confidence": None,
                            "is_new": False,
                        }
                    if tiger_image_urls:
                        tiger_event_payload["images"] = tiger_image_urls
            except Exception as e:
                logger.warning(f"Failed to load tiger details for {tiger_id_value}: {e}")
        
        if tiger_event_payload and tiger_image_urls and "images" not in tiger_event_payload:
            tiger_event_payload["images"] = tiger_image_urls
        
        try:
            # Get available tools for OpenAI chat / OmniVinci
            # Use next() to get session from generator
            session = next(get_db_session())
            try:
                from backend.auth.auth import get_current_user
                from backend.database.models import User
                
                # Get user for tool listing
                user = session.query(User).filter(User.user_id == user_id).first()
                if not user:
                    raise ValueError("User not found")
                
                # Get MCP tools
                tools_response = await list_mcp_tools(user, session)
                tools_data = tools_response.get("data", {}).get("servers", {})
                
                # Flatten tools into a simple list
                all_tools = []
                for server_name, server_data in tools_data.items():
                    server_tools = server_data.get("tools", [])
                    for tool in server_tools:
                        # Filter by selected_tools if provided
                        if selected_tools and tool.get("name", "") not in selected_tools:
                            continue
                        all_tools.append({
                            "name": tool.get("name", ""),
                            "description": tool.get("description", ""),
                            "server": server_name,
                            "inputSchema": tool.get("inputSchema", {})
                        })
                
                logger.info(f"Providing {len(all_tools)} tools for agentic calling")
            finally:
                session.close()
            
            # Check if we have video content
            has_video = video_path and video_path.exists()
            
            if has_video:
                # Use OmniVinci for video analysis (its true purpose)
                logger.info(f"Using OmniVinci for video analysis: {video_path}")
                omnivinci_model = get_omnivinci_model()
                
                # Create tool callback URL for OmniVinci to call back when it wants to use tools
                tool_callback_url = f"http://localhost:8000/api/v1/investigations/{investigation_id}/tool-callback"
                
                # Prepare prompt for OmniVinci (video analysis)
                prompt = f"""Analyze this video for tiger conservation investigation purposes.

User request: {user_input}

Available Tools (you can request these if needed):
{chr(10).join([f"- {tool.get('name', '')}: {tool.get('description', '')}" for tool in all_tools[:10]])}

Provide a detailed analysis of the video content, identifying any tigers, their behavior, environment, and any relevant conservation concerns."""
                
                result = await omnivinci_model.analyze_video(
                    video_path,
                    prompt,
                    all_tools,
                    tool_callback_url
                )
                
                # Extract response from OmniVinci
                if result.get("success"):
                    analysis = result.get("analysis", "")
                    tool_requests = result.get("tool_requests", [])
                    if tool_requests:
                        logger.info(f"OmniVinci requested {len(tool_requests)} tools")
                        analysis += f"\n\n[Note: {len(tool_requests)} tool(s) were requested for execution]"
                    response_message = analysis
                else:
                    error_msg = result.get("error", "Unknown error")
                    logger.error(f"OmniVinci video analysis failed: {error_msg}")
                    response_message = f"Video analysis error: {error_msg}"
                    
                step_type = "omnivinci_video_analysis"
                agent_name = "omnivinci"
                
            elif request_type == 'investigation':
                # Use Orchestrator for full investigation workflow
                logger.info("Using Orchestrator for full investigation workflow")
                from backend.agents import OrchestratorAgent
                
                orchestrator_session = next(get_db_session())
                try:
                    orchestrator = OrchestratorAgent(db=orchestrator_session)
                    
                    # Prepare user inputs for orchestrator
                    user_inputs = {
                        "query": user_input,
                        "available_tools": all_tools,
                        "selected_tools": selected_tools or [],
                        "files": file_data
                    }
                    if tiger_id_value:
                        user_inputs["tiger_id"] = tiger_id_value
                    if tiger_image_urls:
                        user_inputs["images"] = tiger_image_urls
                    if tiger_event_payload:
                        user_inputs["tiger_metadata"] = tiger_event_payload
                    
                    # Launch full investigation workflow
                    result = await orchestrator.launch_investigation(
                        investigation_id=investigation_id,
                        user_inputs=user_inputs,
                        context={}
                    )
                    
                    # Extract response from orchestrator
                    if result.get("success"):
                        response_text = result.get("summary", "Investigation completed successfully.")
                        logger.info("Orchestrator investigation completed")
                    else:
                        error_msg = result.get("error", "Unknown error")
                        logger.error(f"Orchestrator investigation failed: {error_msg}")
                        response_text = f"Investigation error: {error_msg}"
                    
                    response_message = response_text
                    step_type = "orchestrator_investigation"
                    agent_name = "orchestrator"
                    
                finally:
                    orchestrator_session.close()
                
            else:
                # Use the OpenAI chat model for quick responses and clarification
                logger.info("Using OpenAI chat model for quick response")
                hermes_model = get_hermes_chat_model()
                
                # Format tools for the OpenAI chat model
                hermes_tools = [
                    {
                        "name": tool.get("name"),
                        "description": tool.get("description"),
                        "parameters": tool.get("inputSchema", {})
                    }
                    for tool in all_tools
                ]
                
                # Chat with the OpenAI model (it has native tool calling)
                result = await hermes_model.chat(
                    message=user_input,
                    tools=hermes_tools,
                    conversation_history=None,  # TODO: Implement conversation history storage
                    max_tokens=2048,
                    temperature=0.7
                )
                
                # Extract response from the OpenAI model
                if result.get("success"):
                    response_text = result.get("response", "")
                    tool_calls = result.get("tool_calls", [])
                    
                    if tool_calls:
                        logger.info(f"OpenAI chat requested {len(tool_calls)} tool calls")
                        # Execute tool calls
                        for tool_call in tool_calls:
                            tool_name = tool_call.get("name")
                            tool_args = tool_call.get("arguments", {})
                            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                            
                            # Find the server for this tool
                            tool_server = None
                            for tool in all_tools:
                                if tool.get("name") == tool_name:
                                    tool_server = tool.get("server")
                                    break
                            
                            if tool_server:
                                # Execute the tool via orchestrator
                                from backend.agents import OrchestratorAgent
                                exec_session = next(get_db_session())
                                try:
                                    orchestrator = OrchestratorAgent(db=exec_session)
                                    tool_result = await orchestrator.use_mcp_tool(
                                        server_name=tool_server,
                                        tool_name=tool_name,
                                        arguments=tool_args
                                    )
                                    logger.info(f"Tool {tool_name} executed: {str(tool_result)[:100]}")
                                    # Add tool result to response
                                    response_text += f"\n\n[Tool {tool_name} result: {str(tool_result)[:200]}...]"
                                finally:
                                    exec_session.close()
                    
                    response_message = response_text
                else:
                    error_msg = result.get("error", "Unknown error")
                    logger.error(f"OpenAI chat failed: {error_msg}")
                    response_message = f"Chat error: {error_msg}. Please try again."
                
                step_type = "openai_chat"
                agent_name = "openai"
            
            # Log investigation step
            self.add_investigation_step(
                investigation_id=investigation_id,
                step_type=step_type,
                agent_name=agent_name,
                status="completed",
                result={"response": response_message[:500]}  # Limit result size
            )
            
            # Clean up video file if created
            if video_path and video_path.exists():
                try:
                    os.unlink(video_path)
                except Exception as e:
                    logger.warning(f"Could not delete temporary video file: {e}")
            
            if tiger_event_payload:
                try:
                    from backend.services.websocket_service import get_websocket_manager
                    ws_manager = get_websocket_manager()
                    await ws_manager.send_event(
                        event_type="tiger_identified",
                        data=tiger_event_payload,
                        investigation_id=str(investigation_id)
                    )
                except Exception as e:
                    logger.warning(f"Failed to send tiger identification event: {e}")
            
            result_payload = {
                "investigation_id": str(investigation_id),
                "response": response_message,
                "next_steps": [],
                "evidence_count": 0,
                "status": "in_progress"
            }
            if tiger_id_value:
                result_payload["tiger_id"] = tiger_id_value
            if tiger_event_payload:
                result_payload["tiger_metadata"] = tiger_event_payload
            return result_payload
            
        except Exception as e:
            logger.error(f"Error in launch_investigation: {e}", exc_info=True)
            # If error occurs, mark investigation as cancelled (failed is not valid enum value)
            investigation.status = "cancelled"
            if not investigation.summary:
                investigation.summary = {}
            investigation.summary["error"] = str(e)
            self.session.commit()
            raise
