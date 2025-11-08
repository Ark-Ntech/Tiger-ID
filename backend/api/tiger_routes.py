"""
Tiger identification API routes.

Enhanced endpoints for tiger identification with model selection, batch processing,
and multi-model support.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from backend.database import get_db
from backend.auth.auth import get_current_user
from backend.services.tiger_service import TigerService
from backend.utils.response_models import SuccessResponse
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/tigers", tags=["tigers"])


@router.post("/identify")
async def identify_tiger(
    image: UploadFile = File(...),
    model_name: Optional[str] = Form(None),
    similarity_threshold: float = Form(0.8),
    use_all_models: bool = Form(False),
    ensemble_mode: Optional[str] = Form(None),  # 'staggered', 'parallel', or None
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Identify a tiger from an uploaded image.
    
    Supports:
    - Model selection via model_name parameter
    - Multi-model identification via use_all_models flag
    - Custom similarity threshold
    """
    try:
        # Validate file type
        if image.content_type and not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {image.content_type}. Only image files are allowed."
            )
        
        # Validate file size (max 10MB)
        image_bytes = await image.read()
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 10MB limit"
            )
        
        # Reset file pointer
        await image.seek(0)
        
        # Validate similarity threshold
        if not 0.0 <= similarity_threshold <= 1.0:
            raise HTTPException(
                status_code=400,
                detail="similarity_threshold must be between 0.0 and 1.0"
            )
        
        tiger_service = TigerService(db)
        
        # Validate model if specified
        if model_name:
            available_models = tiger_service.get_available_models()
            if model_name not in available_models:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model '{model_name}' not available. Available models: {', '.join(available_models)}"
                )
        
        # Validate ensemble_mode
        if ensemble_mode and ensemble_mode not in ['staggered', 'parallel']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid ensemble_mode: {ensemble_mode}. Must be 'staggered' or 'parallel'"
            )
        
        # Set ensemble mode in service
        if ensemble_mode:
            tiger_service._ensemble_mode = ensemble_mode
        
        result = await tiger_service.identify_tiger_from_image(
            image=image,
            user_id=current_user.user_id,
            similarity_threshold=similarity_threshold,
            model_name=model_name,
            use_all_models=use_all_models
        )
        
        # Clear ensemble mode after use
        if hasattr(tiger_service, '_ensemble_mode'):
            delattr(tiger_service, '_ensemble_mode')
        
        return SuccessResponse(data=result)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error identifying tiger: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/identify/batch")
async def identify_tigers_batch(
    images: List[UploadFile] = File(...),
    model_name: Optional[str] = Form(None),
    similarity_threshold: float = Form(0.8),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Identify tigers from multiple images (batch processing).
    
    Supports:
    - Batch processing of multiple images
    - Model selection via model_name parameter
    - Custom similarity threshold
    """
    try:
        if len(images) == 0:
            raise HTTPException(
                status_code=400,
                detail="At least one image is required"
            )
        
        if len(images) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 images per batch request"
            )
        
        # Validate file types and sizes
        for image in images:
            if image.content_type and not image.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type for {image.filename}: {image.content_type}. Only image files are allowed."
                )
            image_bytes = await image.read()
            if len(image_bytes) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {image.filename} exceeds 10MB limit"
                )
            await image.seek(0)
        
        # Validate similarity threshold
        if not 0.0 <= similarity_threshold <= 1.0:
            raise HTTPException(
                status_code=400,
                detail="similarity_threshold must be between 0.0 and 1.0"
            )
        
        tiger_service = TigerService(db)
        
        # Validate model if specified
        if model_name:
            available_models = tiger_service.get_available_models()
            if model_name not in available_models:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model '{model_name}' not available. Available models: {', '.join(available_models)}"
                )
        
        results = await tiger_service.identify_tigers_batch(
            images=images,
            user_id=current_user.user_id,
            similarity_threshold=similarity_threshold,
            model_name=model_name
        )
        
        return SuccessResponse(data={
            "total_images": len(images),
            "results": results
        })
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in batch tiger identification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("")
async def get_tigers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get paginated list of tigers.
    """
    try:
        from backend.database.models import Tiger, TigerImage
        from backend.utils.pagination import PaginatedResponse, paginate_query
        from pathlib import Path
        
        query = db.query(Tiger)
        tigers, total = paginate_query(query, page, page_size)
        
        # Convert to response format
        tiger_data = []
        for tiger in tigers:
            # Get tiger images
            tiger_images = db.query(TigerImage).filter(TigerImage.tiger_id == tiger.tiger_id).limit(5).all()
            images = []
            for img in tiger_images:
                # Create URL for image
                image_url = None
                if img.image_path:
                    img_path = Path(img.image_path)
                    project_root = Path(__file__).parent.parent.parent
                    try:
                        rel_path = img_path.relative_to(project_root)
                        image_url = f"/static/images/{rel_path.as_posix()}"
                    except ValueError:
                        if img_path.exists():
                            rel_path_str = img_path.as_posix().replace(str(project_root), '').lstrip('/').replace('\\', '/')
                            image_url = f"/static/images/{rel_path_str}"
                
                if image_url:
                    images.append({
                        "id": str(img.image_id),
                        "url": image_url,
                        "thumbnail_url": image_url,
                        "uploaded_at": img.created_at.isoformat() if img.created_at else None,
                        "source": getattr(img, 'source', None) or "dataset",
                        "metadata": getattr(img, 'meta_data', {}) or {}
                    })
            
            tiger_data.append({
                "id": str(tiger.tiger_id),
                "name": tiger.name,
                "estimated_age": getattr(tiger, 'estimated_age', None),
                "sex": getattr(tiger, 'sex', None),
                "first_seen": tiger.created_at.isoformat() if tiger.created_at else None,
                "last_seen": tiger.last_seen_date.isoformat() if tiger.last_seen_date else None,
                "confidence_score": getattr(tiger, 'confidence_score', 0.95) or 0.95,
                "images": images,
                "locations": [],
            })
        
        paginated = PaginatedResponse.create(
            data=tiger_data,
            total=total,
            page=page,
            page_size=page_size
        )
        
        return SuccessResponse(
            message="Tigers retrieved successfully",
            data=paginated.model_dump()
        )
        
    except Exception as e:
        logger.error(f"Error getting tigers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/models")
async def get_available_models(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get list of available RE-ID models.
    """
    try:
        tiger_service = TigerService(db)
        models = tiger_service.get_available_models()
        
        return SuccessResponse(
            message="Models retrieved successfully",
            data={
                "models": models,
                "default": "wildlife_tools"
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting available models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("")
async def create_tiger(
    name: str = Form(...),
    alias: Optional[str] = Form(None),
    images: List[UploadFile] = File(...),
    notes: Optional[str] = Form(None),
    model_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Register a new tiger with images.
    
    Accepts:
    - name: Tiger name (required)
    - alias: Tiger alias/identifier (optional)
    - images: List of tiger images (required, at least one)
    - notes: Additional notes (optional)
    - model_name: Model to use for embedding generation (optional)
    """
    try:
        if len(images) == 0:
            raise HTTPException(
                status_code=400,
                detail="At least one image is required"
            )
        
        if len(images) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 images per registration"
            )
        
        # Validate file types and sizes
        for image in images:
            if image.content_type and not image.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type for {image.filename}: {image.content_type}. Only image files are allowed."
                )
            image_bytes = await image.read()
            if len(image_bytes) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {image.filename} exceeds 10MB limit"
                )
            await image.seek(0)
        
        tiger_service = TigerService(db)
        
        # Register new tiger
        result = await tiger_service.register_new_tiger(
            name=name,
            alias=alias,
            images=images,
            notes=notes,
            model_name=model_name,
            user_id=current_user.user_id
        )
        
        return SuccessResponse(
            message="Tiger registered successfully",
            data=result
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering tiger: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{tiger_id}/launch-investigation")
async def launch_investigation_from_tiger(
    tiger_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Launch an investigation for a specific tiger.
    
    Creates an investigation with the tiger pre-linked and automatically
    selects MCP tools (web search, reverse image search, browser automation)
    to find where the tiger appears elsewhere.
    """
    try:
        from backend.services.investigation_service import InvestigationService
        from backend.api.mcp_tools_routes import list_mcp_tools
        
        tiger_service = TigerService(db)
        investigation_service = InvestigationService(db)
        
        # Get tiger details
        tiger = await tiger_service.get_tiger(tiger_id)
        if not tiger:
            raise HTTPException(status_code=404, detail="Tiger not found")
        
        tiger_name = tiger.get("name") or f"Tiger {str(tiger_id)[:8]}"
        
        # Create investigation with tiger context
        investigation = investigation_service.create_investigation(
            title=f"Investigation: {tiger_name}",
            description=f"Investigation launched for tiger {tiger_name}. Searching for appearances across web sources.",
            created_by=current_user.user_id,
            priority="medium",
            tags=["tiger-investigation", "web-search"]
        )
        
        # Link tiger to investigation
        if investigation:
            investigation.related_tigers = [str(tiger_id)]
            db.commit()
        
        # Get available MCP tools
        mcp_tools_response = await list_mcp_tools(current_user, db)
        available_tools = []
        
        if mcp_tools_response.get("data"):
            tools_by_server = mcp_tools_response["data"].get("tools_by_server", {})
            
            # Select relevant tools for tiger investigation
            tool_names = []
            priority_keywords = ["search", "firecrawl", "puppeteer", "browser", "image", "reverse", "web", "crawl"]
            secondary_keywords = ["youtube", "meta", "social", "news"]
            
            for server_name, server_data in tools_by_server.items():
                if isinstance(server_data, dict) and "tools" in server_data:
                    for tool in server_data["tools"]:
                        tool_name = tool.get("name", "")
                        tool_desc = tool.get("description", "").lower()
                        tool_lower = tool_name.lower()
                        
                        # Priority tools for tiger investigation
                        if any(keyword in tool_lower or keyword in tool_desc for keyword in priority_keywords):
                            tool_names.append(tool_name)
                        # Secondary tools
                        elif any(keyword in tool_lower or keyword in tool_desc for keyword in secondary_keywords):
                            tool_names.append(tool_name)
            
            # Ensure we have at least web search and reverse image search
            if not any("search" in tool.lower() for tool in tool_names):
                # Add default search tools if available
                for server_name, server_data in tools_by_server.items():
                    if isinstance(server_data, dict) and "tools" in server_data:
                        for tool in server_data["tools"]:
                            tool_name = tool.get("name", "")
                            if "search" in tool_name.lower() and tool_name not in tool_names:
                                tool_names.insert(0, tool_name)  # Add at beginning
                                break
            
            available_tools = tool_names[:15]  # Limit to 15 tools
        
        # Launch investigation with selected tools
        launch_result = await investigation_service.launch_investigation(
            investigation_id=investigation.investigation_id,
            user_input=f"Find where tiger {tiger_name} (ID: {str(tiger_id)[:8]}) appears across the web. Search for images, news articles, social media posts, and any other appearances of this tiger.",
            files=[],
            user_id=current_user.user_id,
            selected_tools=available_tools
        )
        
        return SuccessResponse(
            message="Investigation launched successfully",
            data={
                "investigation_id": str(investigation.investigation_id),
                "tiger_id": str(tiger_id),
                "tiger_name": tiger_name,
                "selected_tools": available_tools,
                "response": launch_result.get("response", "Investigation launched")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error launching investigation from tiger: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{tiger_id}")
async def get_tiger(
    tiger_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get tiger details by ID.
    """
    try:
        tiger_service = TigerService(db)
        tiger = await tiger_service.get_tiger(tiger_id)
        
        if not tiger:
            raise HTTPException(status_code=404, detail="Tiger not found")
        
        return SuccessResponse(data=tiger)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tiger: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{tiger_id}/images/{image_id}")
async def get_tiger_image(
    tiger_id: UUID,
    image_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    thumbnail: bool = Query(False, description="Return thumbnail if available")
):
    """
    Serve tiger image with optimization and caching.
    
    Supports:
    - Thumbnail generation
    - Image optimization
    - Caching headers
    """
    try:
        from backend.database.models import TigerImage
        from pathlib import Path
        from fastapi.responses import FileResponse
        import os
        
        # Get image record
        image = db.query(TigerImage).filter(
            TigerImage.image_id == image_id,
            TigerImage.tiger_id == tiger_id
        ).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Determine image path
        image_path = None
        if thumbnail and hasattr(image, 'thumbnail_path') and image.thumbnail_path:
            image_path = Path(image.thumbnail_path)
        elif image.image_path:
            image_path = Path(image.image_path)
        
        if not image_path or not image_path.exists():
            raise HTTPException(status_code=404, detail="Image file not found")
        
        # Determine content type
        content_type = "image/jpeg"
        if image_path.suffix.lower() in ['.png']:
            content_type = "image/png"
        elif image_path.suffix.lower() in ['.gif']:
            content_type = "image/gif"
        elif image_path.suffix.lower() in ['.webp']:
            content_type = "image/webp"
        
        # Return file with caching headers
        return FileResponse(
            str(image_path),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=31536000",  # 1 year cache
                "ETag": str(image.image_id),
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving tiger image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

