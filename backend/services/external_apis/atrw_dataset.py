"""ATRW (Amur Tiger Re-identification in the Wild) dataset manager"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import httpx
import zipfile
import shutil
from urllib.parse import urlparse

from backend.utils.logging import get_logger

logger = get_logger(__name__)


class ATRWDatasetManager:
    """Manager for ATRW dataset download and integration
    
    ATRW (Amur Tiger Re-identification in the Wild) is the primary training dataset
    with 92 individual tigers and images for re-identification.
    
    Reference: https://ar5iv.labs.arxiv.org/html/1906.05586
    """
    
    def __init__(
        self,
        dataset_dir: Path,
        download_url: Optional[str] = None
    ):
        """
        Initialize ATRW dataset manager
        
        Args:
            dataset_dir: Directory to store the dataset
            download_url: URL to download dataset (if provided)
        """
        self.dataset_dir = Path(dataset_dir)
        self.download_url = download_url or self._get_default_url()
        self.images_dir = self.dataset_dir / "images"
        self.annotations_dir = self.dataset_dir / "annotations"
        
        # Create directories
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.annotations_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_default_url(self) -> str:
        """Get default dataset download URL"""
        # Note: Actual URL may vary - adjust based on dataset availability
        # ATRW dataset may be hosted on GitHub, research lab site, or data repository
        return "https://github.com/cvlab-stonybrook/ATRW_dataset/releases/latest"
    
    async def check_dataset_exists(self) -> bool:
        """Check if dataset is already downloaded"""
        # Check for key files/directories that indicate dataset is present
        required_paths = [
            self.images_dir,
            self.annotations_dir,
            self.dataset_dir / "README.md"  # Dataset should have README
        ]
        return all(path.exists() for path in required_paths)
    
    async def download_dataset(
        self,
        force: bool = False,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Download ATRW dataset
        
        Args:
            force: Force download even if dataset exists
            progress_callback: Optional callback for download progress
        
        Returns:
            Download status and metadata
        """
        if await self.check_dataset_exists() and not force:
            logger.info("ATRW dataset already exists", dataset_dir=str(self.dataset_dir))
            return {
                "status": "exists",
                "dataset_dir": str(self.dataset_dir),
                "message": "Dataset already downloaded"
            }
        
        try:
            logger.info("Downloading ATRW dataset", url=self.download_url)
            
            # Download dataset file
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", self.download_url) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get("content-length", 0))
                    
                    zip_path = self.dataset_dir / "atrw_dataset.zip"
                    downloaded = 0
                    
                    with open(zip_path, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback:
                                progress_callback(downloaded, total_size)
            
            # Extract dataset
            logger.info("Extracting ATRW dataset")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(self.dataset_dir)
            
            # Clean up zip file
            zip_path.unlink()
            
            # Verify extraction
            if await self.check_dataset_exists():
                metadata = await self.get_dataset_metadata()
                return {
                    "status": "success",
                    "dataset_dir": str(self.dataset_dir),
                    "metadata": metadata
                }
            else:
                return {
                    "status": "error",
                    "message": "Dataset extraction failed verification"
                }
                
        except Exception as e:
            logger.error("ATRW dataset download failed", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_dataset_metadata(self) -> Dict[str, Any]:
        """
        Get dataset metadata
        
        Returns:
            Dataset metadata including size, number of tigers, images, etc.
        """
        metadata = {
            "dataset_name": "ATRW",
            "description": "Amur Tiger Re-identification in the Wild",
            "dataset_dir": str(self.dataset_dir),
            "num_tigers": 0,
            "num_images": 0,
            "images_dir": str(self.images_dir),
            "annotations_dir": str(self.annotations_dir)
        }
        
        try:
            # Count images
            image_files = list(self.images_dir.rglob("*.jpg")) + \
                         list(self.images_dir.rglob("*.png"))
            metadata["num_images"] = len(image_files)
            
            # Count tigers (from directory structure or annotations)
            tiger_dirs = [d for d in self.images_dir.iterdir() if d.is_dir()]
            metadata["num_tigers"] = len(tiger_dirs)
            
            # Get dataset size
            total_size = sum(
                f.stat().st_size
                for f in self.dataset_dir.rglob("*")
                if f.is_file()
            )
            metadata["total_size_mb"] = total_size / (1024 * 1024)
            
        except Exception as e:
            logger.warning("Failed to calculate dataset metadata", error=str(e))
        
        return metadata
    
    def get_tiger_images(self, tiger_id: str) -> List[Path]:
        """
        Get image paths for a specific tiger
        
        Args:
            tiger_id: Tiger identifier
        
        Returns:
            List of image paths
        """
        tiger_dir = self.images_dir / tiger_id
        if not tiger_dir.exists():
            return []
        
        return list(tiger_dir.glob("*.jpg")) + list(tiger_dir.glob("*.png"))
    
    def get_all_tiger_ids(self) -> List[str]:
        """Get list of all tiger IDs in dataset"""
        tiger_dirs = [d.name for d in self.images_dir.iterdir() if d.is_dir()]
        return sorted(tiger_dirs)
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """Get general dataset information"""
        return {
            "name": "ATRW",
            "full_name": "Amur Tiger Re-identification in the Wild",
            "num_tigers": 92,
            "paper_url": "https://ar5iv.labs.arxiv.org/html/1906.05586",
            "format": "COCO",
            "annotations": True,
            "description": "Primary training dataset for tiger stripe re-identification"
        }

