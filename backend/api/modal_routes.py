"""
Modal integration API routes.

Endpoints for Modal model status, statistics, and management.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth.auth import get_current_user
from backend.services.modal_client import get_modal_client
from backend.services.tiger_service import TigerService
from backend.utils.response_models import SuccessResponse
from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)

router = APIRouter(prefix="/modal", tags=["modal"])


@router.get("/status")
async def get_modal_status(
    current_user = Depends(get_current_user)
):
    """
    Get Modal integration status and statistics.
    
    Returns:
        Modal connection status, model availability, and usage statistics
    """
    try:
        settings = get_settings()
        modal_client = get_modal_client()
        
        # Get Modal client statistics
        stats = modal_client.get_stats()
        
        # Check Modal configuration
        modal_config = {
            "enabled": settings.modal.enabled,
            "app_name": settings.modal.app_name,
            "max_retries": settings.modal.max_retries,
            "timeout": settings.modal.timeout,
            "queue_max_size": settings.modal.queue_max_size,
            "fallback_to_queue": settings.modal.fallback_to_queue
        }
        
        # Try to check Modal app deployment
        try:
            import modal
            app = modal.App.lookup("tiger-id-models", create_if_missing=False)
            deployment_status = "deployed"
            deployment_url = "https://modal.com/apps/ark-ntech/main/deployed/tiger-id-models"
        except modal.exception.NotFoundError:
            deployment_status = "not_deployed"
            deployment_url = None
        except Exception as e:
            deployment_status = "unknown"
            deployment_url = None
            logger.warning(f"Could not check Modal deployment: {e}")
        
        return SuccessResponse(data={
            "modal": {
                "status": "connected" if modal_config["enabled"] else "disabled",
                "deployment": deployment_status,
                "deployment_url": deployment_url,
                "configuration": modal_config,
                "statistics": stats
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting Modal status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_modal_models(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all available Modal models.
    
    Returns:
        List of all Modal-powered models with metadata
    """
    try:
        tiger_service = TigerService(db)
        available_models = tiger_service.get_available_models()
        
        # Model metadata with Modal GPU information
        model_info = {
            "tiger_reid": {
                "name": "TigerReID",
                "description": "Tiger re-identification using ResNet50",
                "gpu": "T4",
                "backend": "Modal",
                "embedding_dim": 2048,
                "type": "reid"
            },
            "wildlife_tools": {
                "name": "WildlifeTools",
                "description": "MegaDescriptor embeddings",
                "gpu": "A100-40GB",
                "backend": "Modal",
                "embedding_dim": 1536,
                "type": "reid"
            },
            "rapid": {
                "name": "RAPID",
                "description": "Real-time Animal Pattern ReID",
                "gpu": "T4",
                "backend": "Modal",
                "embedding_dim": 2048,
                "type": "reid"
            },
            "cvwc2019": {
                "name": "CVWC2019",
                "description": "Part-pose guided tiger ReID",
                "gpu": "T4",
                "backend": "Modal",
                "embedding_dim": 2048,
                "type": "reid"
            },
            "megadetector": {
                "name": "MegaDetector",
                "description": "Animal detection v5",
                "gpu": "T4",
                "backend": "Modal",
                "type": "detection"
            },
            "omnivinci": {
                "name": "OmniVinci",
                "description": "Video+audio analysis (Open Source)",
                "gpu": "A100-40GB",
                "backend": "Modal",
                "type": "video_analysis",
                "source": "https://huggingface.co/nvidia/omnivinci",
                "license": "Apache 2.0"
            }
        }
        
        # Filter to only available models
        models = {
            name: info for name, info in model_info.items()
            if name in available_models or name in ["megadetector", "omnivinci"]
        }
        
        return SuccessResponse(data={
            "models": models,
            "total": len(models),
            "backend": "Modal serverless GPU",
            "default_model": "tiger_reid"
        })
        
    except Exception as e:
        logger.error(f"Error getting Modal models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/status")
async def get_queue_status(
    current_user = Depends(get_current_user)
):
    """
    Get Modal request queue status.
    
    Returns:
        Queue size and queued request information
    """
    try:
        modal_client = get_modal_client()
        stats = modal_client.get_stats()
        
        return SuccessResponse(data={
            "queue": {
                "size": stats["queue_size"],
                "max_size": stats["queue_max_size"],
                "requests_queued": stats["requests_queued"],
                "utilization": f"{(stats['queue_size'] / stats['queue_max_size'] * 100):.1f}%"
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/process")
async def process_queued_requests(
    current_user = Depends(get_current_user)
):
    """
    Process queued Modal requests.
    
    Attempts to process all requests in the queue.
    """
    try:
        modal_client = get_modal_client()
        result = await modal_client.process_queued_requests()
        
        return SuccessResponse(data={
            "processed": result["processed"],
            "succeeded": result["succeeded"],
            "failed": result["failed"],
            "message": f"Processed {result['processed']} requests: {result['succeeded']} succeeded, {result['failed']} failed"
        })
        
    except Exception as e:
        logger.error(f"Error processing queue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/omnivinci/tools")
async def get_omnivinci_tools(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get available tools for OmniVinci agentic calling.
    
    Returns a simplified list of tools that OmniVinci can use.
    """
    try:
        from backend.api.mcp_tools_routes import list_mcp_tools
        
        # Get all MCP tools
        tools_response = await list_mcp_tools(current_user, db)
        tools_data = tools_response.get("servers", {})
        
        # Flatten tools into a simple list for OmniVinci
        all_tools = []
        for server_name, server_data in tools_data.items():
            server_tools = server_data.get("tools", [])
            for tool in server_tools:
                all_tools.append({
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "server": server_name,
                    "inputSchema": tool.get("inputSchema", {})
                })
        
        return SuccessResponse(data={
            "tools": all_tools,
            "total": len(all_tools),
            "servers": list(tools_data.keys())
        })
        
    except Exception as e:
        logger.error(f"Error getting OmniVinci tools: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))