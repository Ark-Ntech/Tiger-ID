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
        
        result = await tiger_service.identify_tiger_from_image(
            image=image,
            user_id=current_user.user_id,
            similarity_threshold=similarity_threshold,
            model_name=model_name,
            use_all_models=use_all_models
        )
        
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
                "default": "tiger_reid"
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting available models: {e}", exc_info=True)
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

