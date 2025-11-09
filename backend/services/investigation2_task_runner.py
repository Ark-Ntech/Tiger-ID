"""Task runner for Investigation 2.0 workflows"""

import asyncio
import threading
from typing import Dict, Any
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
    context: Dict[str, Any]
):
    """Queue an investigation for processing"""
    task_id = str(investigation_id)
    _task_queue[task_id] = {
        "investigation_id": investigation_id,
        "image_bytes": image_bytes,
        "context": context,
        "queued_at": time.time(),
        "status": "queued"
    }
    logger.info(f"Queued investigation {investigation_id} for processing (queue size: {len(_task_queue)})")
    logger.info(f"[QUEUE] Investigation {investigation_id} queued (queue size: {len(_task_queue)})")


def _run_task_loop():
    """Background loop that processes queued investigations"""
    logger.info("Task runner loop started")
    print("[RUNNER] Task runner loop started", flush=True)
    
    while _running:
        try:
            if not _task_queue:
                time.sleep(1)
                continue
            
            # Get next task
            task_id = list(_task_queue.keys())[0]
            task_data = _task_queue.pop(task_id)
            
            logger.info(f"[RUNNER] Processing investigation {task_id}")
            logger.info(f"Processing investigation {task_id}")
            
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
    
    db_gen = get_db_session()
    db = next(db_gen)
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

