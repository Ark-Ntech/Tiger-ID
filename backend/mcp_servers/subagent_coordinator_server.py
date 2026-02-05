"""
Subagent Coordinator MCP Server

Provides tools for managing parallel subagent execution across different pool types.
Coordinates ML inference, research, and report generation subagents with proper
resource management, lifecycle tracking, and WebSocket event emission.
"""

from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid

from pydantic import BaseModel

from backend.mcp_servers.base_mcp_server import MCPServerBase, MCPTool
from backend.config.settings import SUBAGENT_POOLS, get_subagent_pool_config
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class SubagentStatus(str, Enum):
    """Subagent lifecycle states."""
    SPAWNED = "spawned"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class SubagentType(str, Enum):
    """Types of subagent pools."""
    ML_INFERENCE = "ml_inference"
    RESEARCH = "research"
    REPORT_GENERATION = "report_generation"
    IMAGE_PROCESSING = "image_processing"
    WEB_CRAWL = "web_crawl"


class SubagentInfo(BaseModel):
    """Information about a subagent instance."""
    id: str
    type: str  # ml_inference, research, report_generation
    phase: str  # e.g., stripe_analysis
    status: str  # spawned, running, completed, error, cancelled
    progress: int  # 0-100
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    investigation_id: Optional[str] = None
    model_name: Optional[str] = None  # For ML inference subagents


@dataclass
class SubagentTask:
    """
    Internal representation of a subagent task.

    Holds the coroutine, metadata, and asyncio Task object.
    """
    subagent_id: str
    subagent_type: str
    phase: str
    investigation_id: Optional[str]
    model_name: Optional[str]
    status: SubagentStatus
    progress: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    task: Optional[asyncio.Task] = None

    def to_info(self) -> SubagentInfo:
        """Convert to SubagentInfo for external API."""
        return SubagentInfo(
            id=self.subagent_id,
            type=self.subagent_type,
            phase=self.phase,
            status=self.status.value,
            progress=self.progress,
            started_at=self.started_at,
            completed_at=self.completed_at,
            result=self.result,
            error=self.error,
            investigation_id=self.investigation_id,
            model_name=self.model_name
        )


@dataclass
class PoolStatus:
    """Status of a subagent pool."""
    pool_name: str
    max_concurrent: int
    active_count: int
    pending_count: int
    completed_count: int
    error_count: int
    utilization_pct: float


class SubagentCoordinatorMCPServer(MCPServerBase):
    """
    MCP server for coordinating parallel subagent execution.

    Manages multiple pools of subagents with different resource constraints:
    - ml_inference: 6 concurrent (one per ReID model), 120s timeout
    - research: 5 concurrent, 60s timeout
    - report_generation: 4 concurrent (one per audience), 45s timeout
    - image_processing: 3 concurrent, 30s timeout
    - web_crawl: 10 concurrent, 30s timeout

    Emits WebSocket events for state changes to provide real-time progress.
    """

    def __init__(self):
        """Initialize the Subagent Coordinator MCP server."""
        super().__init__("subagent_coordinator")

        # Subagent registry: subagent_id -> SubagentTask
        self._subagents: Dict[str, SubagentTask] = {}

        # Pool semaphores for concurrency control
        self._pool_semaphores: Dict[str, asyncio.Semaphore] = {}

        # Pool statistics
        self._pool_stats: Dict[str, Dict[str, int]] = {}

        # Initialize pools from settings
        self._initialize_pools()

        # WebSocket emitter callback (set externally)
        self._ws_emitter: Optional[Callable[[str, dict], Awaitable[None]]] = None

        # Register tools
        self._register_tools()

        logger.info("SubagentCoordinatorMCPServer initialized")

    def _initialize_pools(self):
        """Initialize pool semaphores and statistics from settings."""
        for pool_name, config in SUBAGENT_POOLS.items():
            max_concurrent = config.get("max_concurrent", 2)
            self._pool_semaphores[pool_name] = asyncio.Semaphore(max_concurrent)
            self._pool_stats[pool_name] = {
                "completed": 0,
                "errors": 0
            }
            logger.debug(f"Initialized pool '{pool_name}' with max_concurrent={max_concurrent}")

    def set_ws_emitter(self, emitter: Callable[[str, dict], Awaitable[None]]):
        """
        Set the WebSocket emitter callback.

        Args:
            emitter: Async function that takes (investigation_id, message) and broadcasts.
        """
        self._ws_emitter = emitter

    async def _emit_event(self, investigation_id: Optional[str], event: str, data: dict):
        """
        Emit a WebSocket event if emitter is configured.

        Args:
            investigation_id: Target investigation for the event.
            event: Event type name.
            data: Event data payload.
        """
        if self._ws_emitter and investigation_id:
            try:
                await self._ws_emitter(investigation_id, {
                    "event": event,
                    "data": data
                })
            except Exception as e:
                logger.warning(f"Failed to emit WebSocket event: {e}")

    def _register_tools(self):
        """Register available tools."""
        self.tools = {
            "spawn_subagent": MCPTool(
                name="spawn_subagent",
                description="Start a new subagent task. Returns immediately with subagent_id. Use get_subagent_status to track progress.",
                parameters={
                    "type": "object",
                    "properties": {
                        "subagent_type": {
                            "type": "string",
                            "description": "Type of subagent pool to use",
                            "enum": ["ml_inference", "research", "report_generation", "image_processing", "web_crawl"]
                        },
                        "phase": {
                            "type": "string",
                            "description": "Workflow phase this subagent belongs to (e.g., 'stripe_analysis', 'reverse_image_search')"
                        },
                        "investigation_id": {
                            "type": "string",
                            "description": "Optional investigation ID for WebSocket events"
                        },
                        "model_name": {
                            "type": "string",
                            "description": "Optional model name for ML inference subagents"
                        },
                        "task_data": {
                            "type": "object",
                            "description": "Optional data to pass to the subagent task",
                            "default": {}
                        }
                    },
                    "required": ["subagent_type", "phase"]
                },
                handler=self._handle_spawn_subagent
            ),
            "get_subagent_status": MCPTool(
                name="get_subagent_status",
                description="Get the current status of a specific subagent by ID.",
                parameters={
                    "type": "object",
                    "properties": {
                        "subagent_id": {
                            "type": "string",
                            "description": "The unique ID of the subagent"
                        }
                    },
                    "required": ["subagent_id"]
                },
                handler=self._handle_get_subagent_status
            ),
            "list_active_subagents": MCPTool(
                name="list_active_subagents",
                description="List all active (spawned or running) subagents. Optionally filter by type or investigation.",
                parameters={
                    "type": "object",
                    "properties": {
                        "subagent_type": {
                            "type": "string",
                            "description": "Optional filter by subagent type",
                            "enum": ["ml_inference", "research", "report_generation", "image_processing", "web_crawl"]
                        },
                        "investigation_id": {
                            "type": "string",
                            "description": "Optional filter by investigation ID"
                        }
                    }
                },
                handler=self._handle_list_active_subagents
            ),
            "cancel_subagent": MCPTool(
                name="cancel_subagent",
                description="Cancel a running subagent. Returns success status.",
                parameters={
                    "type": "object",
                    "properties": {
                        "subagent_id": {
                            "type": "string",
                            "description": "The unique ID of the subagent to cancel"
                        }
                    },
                    "required": ["subagent_id"]
                },
                handler=self._handle_cancel_subagent
            ),
            "get_pool_status": MCPTool(
                name="get_pool_status",
                description="Get utilization statistics for subagent pools.",
                parameters={
                    "type": "object",
                    "properties": {
                        "pool_name": {
                            "type": "string",
                            "description": "Optional specific pool to check. If omitted, returns all pools.",
                            "enum": ["ml_inference", "research", "report_generation", "image_processing", "web_crawl"]
                        }
                    }
                },
                handler=self._handle_get_pool_status
            ),
            "update_subagent_progress": MCPTool(
                name="update_subagent_progress",
                description="Update the progress of a running subagent. Emits WebSocket event.",
                parameters={
                    "type": "object",
                    "properties": {
                        "subagent_id": {
                            "type": "string",
                            "description": "The unique ID of the subagent"
                        },
                        "progress": {
                            "type": "integer",
                            "description": "Progress percentage (0-100)",
                            "minimum": 0,
                            "maximum": 100
                        },
                        "message": {
                            "type": "string",
                            "description": "Optional status message"
                        }
                    },
                    "required": ["subagent_id", "progress"]
                },
                handler=self._handle_update_progress
            ),
            "complete_subagent": MCPTool(
                name="complete_subagent",
                description="Mark a subagent as completed with optional result data.",
                parameters={
                    "type": "object",
                    "properties": {
                        "subagent_id": {
                            "type": "string",
                            "description": "The unique ID of the subagent"
                        },
                        "result": {
                            "type": "object",
                            "description": "Optional result data from the subagent"
                        }
                    },
                    "required": ["subagent_id"]
                },
                handler=self._handle_complete_subagent
            ),
            "fail_subagent": MCPTool(
                name="fail_subagent",
                description="Mark a subagent as failed with an error message.",
                parameters={
                    "type": "object",
                    "properties": {
                        "subagent_id": {
                            "type": "string",
                            "description": "The unique ID of the subagent"
                        },
                        "error": {
                            "type": "string",
                            "description": "Error message describing the failure"
                        }
                    },
                    "required": ["subagent_id", "error"]
                },
                handler=self._handle_fail_subagent
            )
        }

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        return [tool.to_dict() for tool in self.tools.values()]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name."""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found", "success": False}

        try:
            return await self.tools[tool_name].call(arguments)
        except Exception as e:
            logger.error(f"Tool call failed: {tool_name}", error=str(e), exc_info=True)
            return {"error": str(e), "success": False}

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources."""
        return []

    # =========================================================================
    # Tool Handlers
    # =========================================================================

    async def _handle_spawn_subagent(
        self,
        subagent_type: str,
        phase: str,
        investigation_id: Optional[str] = None,
        model_name: Optional[str] = None,
        task_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Handle spawning a new subagent.

        Creates a subagent entry in SPAWNED state and returns immediately.
        The caller is responsible for executing the actual work and calling
        update_subagent_progress, complete_subagent, or fail_subagent.
        """
        try:
            # Validate pool exists
            if subagent_type not in SUBAGENT_POOLS:
                return {
                    "success": False,
                    "error": f"Unknown subagent type: {subagent_type}. Valid types: {list(SUBAGENT_POOLS.keys())}"
                }

            # Generate unique ID
            subagent_id = f"{subagent_type[:3]}_{uuid.uuid4().hex[:8]}"

            # Create subagent entry
            subagent = SubagentTask(
                subagent_id=subagent_id,
                subagent_type=subagent_type,
                phase=phase,
                investigation_id=investigation_id,
                model_name=model_name,
                status=SubagentStatus.SPAWNED,
                progress=0,
                started_at=datetime.utcnow()
            )

            self._subagents[subagent_id] = subagent

            logger.info(
                f"Spawned subagent: {subagent_id} (type={subagent_type}, phase={phase})"
            )

            # Emit WebSocket event
            await self._emit_event(investigation_id, "subagent_spawned", {
                "subagent_id": subagent_id,
                "subagent_type": subagent_type,
                "phase": phase,
                "model_name": model_name,
                "timestamp": datetime.utcnow().isoformat()
            })

            return {
                "success": True,
                "subagent_id": subagent_id,
                "subagent_type": subagent_type,
                "phase": phase,
                "status": SubagentStatus.SPAWNED.value,
                "pool_config": get_subagent_pool_config(subagent_type),
                "message": f"Subagent {subagent_id} spawned. Call update_subagent_progress to track, complete_subagent when done."
            }

        except Exception as e:
            logger.error(f"Failed to spawn subagent: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_get_subagent_status(
        self,
        subagent_id: str
    ) -> Dict[str, Any]:
        """Handle getting status of a specific subagent."""
        try:
            if subagent_id not in self._subagents:
                return {
                    "success": False,
                    "error": f"Subagent {subagent_id} not found"
                }

            subagent = self._subagents[subagent_id]
            info = subagent.to_info()

            return {
                "success": True,
                "subagent": info.model_dump()
            }

        except Exception as e:
            logger.error(f"Failed to get subagent status: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_list_active_subagents(
        self,
        subagent_type: Optional[str] = None,
        investigation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle listing active subagents with optional filters."""
        try:
            active_statuses = {SubagentStatus.SPAWNED, SubagentStatus.RUNNING}

            results = []
            for subagent in self._subagents.values():
                # Filter by status
                if subagent.status not in active_statuses:
                    continue

                # Filter by type if specified
                if subagent_type and subagent.subagent_type != subagent_type:
                    continue

                # Filter by investigation if specified
                if investigation_id and subagent.investigation_id != investigation_id:
                    continue

                results.append(subagent.to_info().model_dump())

            return {
                "success": True,
                "active_subagents": results,
                "count": len(results)
            }

        except Exception as e:
            logger.error(f"Failed to list active subagents: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_cancel_subagent(
        self,
        subagent_id: str
    ) -> Dict[str, Any]:
        """Handle cancelling a running subagent."""
        try:
            if subagent_id not in self._subagents:
                return {
                    "success": False,
                    "error": f"Subagent {subagent_id} not found"
                }

            subagent = self._subagents[subagent_id]

            # Check if cancellable
            if subagent.status not in {SubagentStatus.SPAWNED, SubagentStatus.RUNNING}:
                return {
                    "success": False,
                    "error": f"Subagent {subagent_id} is in state {subagent.status.value}, cannot cancel"
                }

            # Cancel the asyncio task if it exists
            if subagent.task and not subagent.task.done():
                subagent.task.cancel()

            # Update status
            subagent.status = SubagentStatus.CANCELLED
            subagent.completed_at = datetime.utcnow()

            logger.info(f"Cancelled subagent: {subagent_id}")

            # Emit WebSocket event
            await self._emit_event(subagent.investigation_id, "subagent_cancelled", {
                "subagent_id": subagent_id,
                "timestamp": datetime.utcnow().isoformat()
            })

            return {
                "success": True,
                "subagent_id": subagent_id,
                "message": f"Subagent {subagent_id} cancelled"
            }

        except Exception as e:
            logger.error(f"Failed to cancel subagent: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_get_pool_status(
        self,
        pool_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle getting pool utilization statistics."""
        try:
            pools_to_check = [pool_name] if pool_name else list(SUBAGENT_POOLS.keys())

            pool_statuses = []
            for name in pools_to_check:
                if name not in SUBAGENT_POOLS:
                    continue

                config = SUBAGENT_POOLS[name]
                max_concurrent = config.get("max_concurrent", 2)

                # Count active subagents in this pool
                active_count = sum(
                    1 for s in self._subagents.values()
                    if s.subagent_type == name and s.status in {SubagentStatus.SPAWNED, SubagentStatus.RUNNING}
                )

                # Get stats
                stats = self._pool_stats.get(name, {"completed": 0, "errors": 0})

                utilization = (active_count / max_concurrent * 100) if max_concurrent > 0 else 0

                pool_statuses.append(PoolStatus(
                    pool_name=name,
                    max_concurrent=max_concurrent,
                    active_count=active_count,
                    pending_count=0,  # Not tracking pending queue currently
                    completed_count=stats["completed"],
                    error_count=stats["errors"],
                    utilization_pct=round(utilization, 1)
                ))

            return {
                "success": True,
                "pools": [
                    {
                        "pool_name": p.pool_name,
                        "max_concurrent": p.max_concurrent,
                        "active_count": p.active_count,
                        "pending_count": p.pending_count,
                        "completed_count": p.completed_count,
                        "error_count": p.error_count,
                        "utilization_pct": p.utilization_pct
                    }
                    for p in pool_statuses
                ],
                "total_active": sum(p.active_count for p in pool_statuses)
            }

        except Exception as e:
            logger.error(f"Failed to get pool status: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_update_progress(
        self,
        subagent_id: str,
        progress: int,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle updating subagent progress."""
        try:
            if subagent_id not in self._subagents:
                return {
                    "success": False,
                    "error": f"Subagent {subagent_id} not found"
                }

            subagent = self._subagents[subagent_id]

            # Transition from SPAWNED to RUNNING on first progress update
            if subagent.status == SubagentStatus.SPAWNED:
                subagent.status = SubagentStatus.RUNNING
                logger.info(f"Subagent {subagent_id} now RUNNING")

            # Update progress
            subagent.progress = max(0, min(100, progress))

            logger.debug(f"Subagent {subagent_id} progress: {progress}%")

            # Emit WebSocket event
            await self._emit_event(subagent.investigation_id, "subagent_progress", {
                "subagent_id": subagent_id,
                "progress": subagent.progress,
                "message": message,
                "model_name": subagent.model_name,
                "timestamp": datetime.utcnow().isoformat()
            })

            return {
                "success": True,
                "subagent_id": subagent_id,
                "progress": subagent.progress,
                "status": subagent.status.value
            }

        except Exception as e:
            logger.error(f"Failed to update subagent progress: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_complete_subagent(
        self,
        subagent_id: str,
        result: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Handle marking a subagent as completed."""
        try:
            if subagent_id not in self._subagents:
                return {
                    "success": False,
                    "error": f"Subagent {subagent_id} not found"
                }

            subagent = self._subagents[subagent_id]

            # Update status
            subagent.status = SubagentStatus.COMPLETED
            subagent.progress = 100
            subagent.completed_at = datetime.utcnow()
            subagent.result = result

            # Update pool stats
            pool_name = subagent.subagent_type
            if pool_name in self._pool_stats:
                self._pool_stats[pool_name]["completed"] += 1

            duration_ms = int((subagent.completed_at - subagent.started_at).total_seconds() * 1000)

            logger.info(
                f"Subagent {subagent_id} completed in {duration_ms}ms",
                subagent_type=subagent.subagent_type,
                phase=subagent.phase
            )

            # Emit WebSocket event
            await self._emit_event(subagent.investigation_id, "subagent_completed", {
                "subagent_id": subagent_id,
                "result": result,
                "duration_ms": duration_ms,
                "model_name": subagent.model_name,
                "timestamp": datetime.utcnow().isoformat()
            })

            return {
                "success": True,
                "subagent_id": subagent_id,
                "status": SubagentStatus.COMPLETED.value,
                "duration_ms": duration_ms
            }

        except Exception as e:
            logger.error(f"Failed to complete subagent: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_fail_subagent(
        self,
        subagent_id: str,
        error: str
    ) -> Dict[str, Any]:
        """Handle marking a subagent as failed."""
        try:
            if subagent_id not in self._subagents:
                return {
                    "success": False,
                    "error": f"Subagent {subagent_id} not found"
                }

            subagent = self._subagents[subagent_id]

            # Update status
            subagent.status = SubagentStatus.ERROR
            subagent.completed_at = datetime.utcnow()
            subagent.error = error

            # Update pool stats
            pool_name = subagent.subagent_type
            if pool_name in self._pool_stats:
                self._pool_stats[pool_name]["errors"] += 1

            logger.error(
                f"Subagent {subagent_id} failed: {error}",
                subagent_type=subagent.subagent_type,
                phase=subagent.phase
            )

            # Emit WebSocket event
            await self._emit_event(subagent.investigation_id, "subagent_error", {
                "subagent_id": subagent_id,
                "error": error,
                "model_name": subagent.model_name,
                "timestamp": datetime.utcnow().isoformat()
            })

            return {
                "success": True,
                "subagent_id": subagent_id,
                "status": SubagentStatus.ERROR.value,
                "error": error
            }

        except Exception as e:
            logger.error(f"Failed to mark subagent as failed: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Convenience Methods for Direct Integration
    # =========================================================================

    async def spawn_subagent(
        self,
        subagent_type: str,
        phase: str,
        investigation_id: Optional[str] = None,
        model_name: Optional[str] = None,
        task_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to spawn a subagent.

        Use this for direct workflow integration without going through call_tool.
        """
        return await self._handle_spawn_subagent(
            subagent_type=subagent_type,
            phase=phase,
            investigation_id=investigation_id,
            model_name=model_name,
            task_data=task_data
        )

    async def update_progress(
        self,
        subagent_id: str,
        progress: int,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convenience method to update subagent progress."""
        return await self._handle_update_progress(
            subagent_id=subagent_id,
            progress=progress,
            message=message
        )

    async def complete_subagent(
        self,
        subagent_id: str,
        result: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Convenience method to mark subagent as completed."""
        return await self._handle_complete_subagent(
            subagent_id=subagent_id,
            result=result
        )

    async def fail_subagent(
        self,
        subagent_id: str,
        error: str
    ) -> Dict[str, Any]:
        """Convenience method to mark subagent as failed."""
        return await self._handle_fail_subagent(
            subagent_id=subagent_id,
            error=error
        )

    async def get_subagent(self, subagent_id: str) -> Optional[SubagentInfo]:
        """Get subagent info by ID, or None if not found."""
        if subagent_id in self._subagents:
            return self._subagents[subagent_id].to_info()
        return None

    async def wait_for_subagent(
        self,
        subagent_id: str,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Wait for a subagent to complete.

        Args:
            subagent_id: ID of the subagent to wait for.
            timeout: Maximum time to wait in seconds.

        Returns:
            Dict with subagent result or error.
        """
        if subagent_id not in self._subagents:
            return {"success": False, "error": f"Subagent {subagent_id} not found"}

        subagent = self._subagents[subagent_id]

        # Use pool timeout if not specified
        if timeout is None:
            pool_config = get_subagent_pool_config(subagent.subagent_type)
            timeout = pool_config.get("timeout", 60)

        start_time = datetime.utcnow()
        while True:
            if subagent.status in {SubagentStatus.COMPLETED, SubagentStatus.ERROR, SubagentStatus.CANCELLED}:
                break

            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout:
                # Timeout - mark as error
                await self.fail_subagent(subagent_id, f"Timeout after {timeout}s")
                break

            await asyncio.sleep(0.1)

        return await self._handle_get_subagent_status(subagent_id)

    def cleanup_completed(self, max_age_seconds: int = 3600) -> int:
        """
        Remove completed/failed subagents older than max_age_seconds.

        Args:
            max_age_seconds: Maximum age of completed subagents to keep.

        Returns:
            Number of subagents removed.
        """
        now = datetime.utcnow()
        to_remove = []

        for subagent_id, subagent in self._subagents.items():
            if subagent.status not in {SubagentStatus.COMPLETED, SubagentStatus.ERROR, SubagentStatus.CANCELLED}:
                continue

            if subagent.completed_at:
                age = (now - subagent.completed_at).total_seconds()
                if age > max_age_seconds:
                    to_remove.append(subagent_id)

        for subagent_id in to_remove:
            del self._subagents[subagent_id]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old subagents")

        return len(to_remove)


# Singleton instance
_server_instance: Optional[SubagentCoordinatorMCPServer] = None


def get_subagent_coordinator_server() -> SubagentCoordinatorMCPServer:
    """Get or create the singleton server instance."""
    global _server_instance
    if _server_instance is None:
        _server_instance = SubagentCoordinatorMCPServer()
    return _server_instance
