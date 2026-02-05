"""Task runner for Investigation 2.0 workflows

Supports both user-triggered and auto-discovery investigations.
Auto-discovery investigations run completely async with DuckDuckGo deep research.
"""

import asyncio
import threading
from typing import Dict, Any, Optional
from uuid import UUID
from pathlib import Path
import time

from backend.database import get_db_session
from backend.agents.investigation2_workflow import Investigation2Workflow
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Global task queue
_task_queue: Dict[str, Dict[str, Any]] = {}
_runner_thread = None
_running = False

# Priority queues: auto-discovery runs at lower priority than user uploads
PRIORITY_USER = 10
PRIORITY_AUTO = 5


def start_task_runner():
    """Start the background task runner"""
    global _runner_thread, _running

    if _runner_thread is not None and _runner_thread.is_alive():
        logger.info("Task runner already running")
        return

    _running = True
    _runner_thread = threading.Thread(target=_run_task_loop, daemon=True, name="Investigation2-TaskRunner")
    _runner_thread.start()
    logger.info("Investigation 2.0 task runner started")


def stop_task_runner():
    """Stop the background task runner"""
    global _running
    _running = False
    logger.info("Investigation 2.0 task runner stopped")


def queue_investigation(
    investigation_id: UUID,
    image_bytes: bytes,
    context: Dict[str, Any],
    async_mode: bool = False,
    priority: Optional[int] = None
):
    """
    Queue an investigation for processing.

    Args:
        investigation_id: The investigation UUID
        image_bytes: Raw image data
        context: Investigation context dict, may include:
            - source: "user_upload" or "auto_discovery"
            - use_deep_research: True to use DuckDuckGo deep research
            - source_tiger_id: Tiger that triggered auto-investigation
            - facility_id: Associated facility ID
        async_mode: If True, runs completely in background (fire-and-forget)
        priority: Queue priority (higher = processed first)
    """
    task_id = str(investigation_id)

    # Determine source and priority
    source = context.get("source", "user_upload")
    if priority is None:
        priority = PRIORITY_AUTO if source == "auto_discovery" else PRIORITY_USER

    # For auto-discovery, ensure deep research is enabled
    if source == "auto_discovery":
        context["use_deep_research"] = True
        context["async_mode"] = True  # Always async for auto-discovery

    _task_queue[task_id] = {
        "investigation_id": investigation_id,
        "image_bytes": image_bytes,
        "context": context,
        "queued_at": time.time(),
        "status": "queued",
        "source": source,
        "priority": priority,
        "async_mode": async_mode or context.get("async_mode", False)
    }

    logger.info(
        f"[QUEUE] Investigation {investigation_id} queued "
        f"(source={source}, priority={priority}, queue_size={len(_task_queue)})"
    )


def _run_task_loop():
    """Background loop that processes queued investigations with priority."""
    logger.info("Task runner loop started")
    print("[RUNNER] Task runner loop started", flush=True)

    while _running:
        try:
            if not _task_queue:
                time.sleep(1)
                continue

            # Get highest priority task (sort by priority descending, then queued_at ascending)
            sorted_tasks = sorted(
                _task_queue.items(),
                key=lambda x: (-x[1].get("priority", 0), x[1].get("queued_at", 0))
            )

            task_id, task_data = sorted_tasks[0]
            del _task_queue[task_id]

            source = task_data.get("source", "user_upload")
            logger.info(
                f"[RUNNER] Processing investigation {task_id} "
                f"(source={source}, priority={task_data.get('priority', 0)})"
            )

            # Run workflow
            try:
                _run_workflow_sync(
                    task_data["investigation_id"],
                    task_data["image_bytes"],
                    task_data["context"]
                )
            except Exception as e:
                logger.error(f"Workflow execution failed for {task_id}: {e}", exc_info=True)
                logger.info(f"[RUNNER] Error processing {task_id}: {e}")

                # For auto-discovery failures, log but don't block queue
                if source == "auto_discovery":
                    logger.warning(
                        f"[AUTO-DISCOVERY] Investigation {task_id} failed, continuing with queue"
                    )

        except Exception as e:
            logger.error(f"Task runner loop error: {e}", exc_info=True)
            time.sleep(1)

    logger.info("Task runner loop stopped")


def _run_workflow_sync(investigation_id: UUID, image_bytes: bytes, context: Dict[str, Any]):
    """Run workflow synchronously in background thread"""
    logger.info(f"[RUNNER] ========== WORKFLOW EXECUTION START ==========")
    logger.info(f"[RUNNER] Investigation ID: {investigation_id}")
    logger.info(f"[RUNNER] Image size: {len(image_bytes)} bytes")
    logger.info(f"[RUNNER] Context: {context}")

    # get_db_session() returns a Session directly, not a generator
    db = get_db_session()
    logger.info(f"[RUNNER] Database session created")
    
    try:
        logger.info(f"[RUNNER] Creating Investigation2Workflow instance...")
        workflow = Investigation2Workflow(db=db)
        logger.info(f"[RUNNER] Workflow instance created successfully")
        
        # Create event loop for this thread
        logger.info(f"[RUNNER] Creating new event loop...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info(f"[RUNNER] Event loop set")
        
        logger.info(f"[RUNNER] Starting workflow.run() execution...")
        final_state = loop.run_until_complete(
            workflow.run(
                investigation_id=investigation_id,
                uploaded_image=image_bytes,
                context=context
            )
        )
        
        logger.info(f"[RUNNER] Workflow.run() returned")
        logger.info(f"[RUNNER] Final state phase: {final_state.get('phase')}")
        logger.info(f"[RUNNER] Final state status: {final_state.get('status')}")
        logger.info(f"[RUNNER] Number of errors: {len(final_state.get('errors', []))}")
        
        loop.close()
        logger.info(f"[RUNNER] Event loop closed")
        
        logger.info(f"[RUNNER] Workflow completed successfully: {final_state.get('status')}")
        logger.info(f"Investigation {investigation_id} workflow completed: {final_state.get('status')}")
        
        logger.info(f"[RUNNER] Committing database changes...")
        db.commit()
        logger.info(f"[RUNNER] Database committed")
        
    except Exception as e:
        logger.error(f"Workflow execution error: {e}", exc_info=True)
        logger.info(f"[RUNNER] Workflow error: {e}")
        try:
            db.rollback()
        except:
            pass
        raise
    finally:
        try:
            db.close()
        except:
            pass


# Auto-start on module import
start_task_runner()

