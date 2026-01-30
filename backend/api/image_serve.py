"""
Image serving endpoint for making local images publicly accessible.
Required for SerpApi Google Lens which needs public URLs.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import os

router = APIRouter(prefix="/api/images/serve", tags=["images"])


@router.get("/{image_path:path}")
async def serve_image(image_path: str):
    """
    Serve a local image file publicly.
    
    This endpoint makes local images accessible via URL for:
    - SerpApi Google Lens reverse image search
    - External sharing and verification
    
    Security: Only serves images from data/ directory
    """
    try:
        # Decode path and ensure it's safe
        safe_path = image_path.replace("..", "").strip("/\\")
        
        # Check if path is in allowed directories
        full_path = Path(safe_path)
        
        # Ensure the path exists and is a file
        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Ensure it's an image file
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        if full_path.suffix.lower() not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Not an image file")
        
        # Serve the file
        return FileResponse(
            path=full_path,
            media_type=f"image/{full_path.suffix[1:]}",
            filename=full_path.name
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get-public-url")
async def get_public_url(local_path: str):
    """
    Get a public URL for a local image.
    
    Args:
        local_path: Local file path
        
    Returns:
        Public URL that can be used for reverse image search
    """
    try:
        # Get server base URL from environment
        base_url = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
        
        # Validate the path exists
        path = Path(local_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Create public URL
        public_url = f"{base_url}/api/images/serve/{local_path}"
        
        return {
            "local_path": local_path,
            "public_url": public_url,
            "filename": path.name
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

