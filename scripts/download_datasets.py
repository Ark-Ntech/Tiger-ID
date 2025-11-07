#!/usr/bin/env python3
"""
Download datasets for Tiger ID system.

This script downloads:
1. ATRW (Amur Tiger Re-identification in the Wild) dataset
2. WildlifeReID-10k dataset (if needed for tiger images)

Supports multiple download methods:
- Kaggle API (requires kagglehub or kaggle package)
- Direct download from LILA Science
- Manual download instructions
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)


def check_kaggle_installed() -> bool:
    """Check if kagglehub or kaggle package is installed"""
    try:
        import kagglehub
        return True
    except ImportError:
        try:
            import kaggle
            return True
        except ImportError:
            return False


def download_atrw_kaggle(destination: Path) -> bool:
    """Download ATRW dataset from Kaggle using kagglehub"""
    try:
        import kagglehub
        
        logger.info("Downloading ATRW dataset from Kaggle...")
        logger.info("This may take a while (dataset is large)...")
        
        # Download latest version
        path = kagglehub.dataset_download("quadeer15sh/amur-tiger-reidentification")
        
        logger.info(f"Dataset downloaded to: {path}")
        
        # Copy or move to destination
        source_path = Path(path)
        if source_path.exists():
            # Create destination directory
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # If source is a directory, copy contents
            if source_path.is_dir():
                # Look for images directory
                images_dir = None
                for item in source_path.rglob("images"):
                    if item.is_dir():
                        images_dir = item
                        break
                
                if images_dir:
                    # Copy images directory to destination
                    if destination.exists():
                        shutil.rmtree(destination)
                    shutil.copytree(images_dir, destination)
                    logger.info(f"Copied images to: {destination}")
                else:
                    # Copy entire dataset
                    if destination.exists():
                        shutil.rmtree(destination)
                    shutil.copytree(source_path, destination)
                    logger.info(f"Copied dataset to: {destination}")
            else:
                # Extract if it's a zip file
                import zipfile
                with zipfile.ZipFile(source_path, 'r') as zip_ref:
                    zip_ref.extractall(destination.parent)
                logger.info(f"Extracted dataset to: {destination.parent}")
            
            return True
        else:
            logger.error(f"Downloaded path does not exist: {path}")
            return False
            
    except ImportError:
        logger.error("kagglehub not installed. Install with: pip install kagglehub")
        return False
    except Exception as e:
        logger.error(f"Error downloading ATRW from Kaggle: {e}", exc_info=True)
        return False


def download_atrw_manual_instructions(destination: Path):
    """Print manual download instructions for ATRW"""
    logger.warning("=" * 80)
    logger.warning("MANUAL DOWNLOAD REQUIRED")
    logger.warning("=" * 80)
    logger.warning("")
    logger.warning("Please download the ATRW dataset manually:")
    logger.warning("")
    logger.warning("Option 1: LILA Science (Recommended)")
    logger.warning("  1. Visit: https://lila.science/datasets/atrw")
    logger.warning("  2. Download the dataset")
    logger.warning("  3. Extract to: " + str(destination))
    logger.warning("")
    logger.warning("Option 2: Kaggle")
    logger.warning("  1. Visit: https://www.kaggle.com/datasets/quadeer15sh/amur-tiger-reidentification")
    logger.warning("  2. Requires Kaggle account and API setup")
    logger.warning("  3. Download and extract to: " + str(destination))
    logger.warning("")
    logger.warning("Expected structure:")
    logger.warning(f"  {destination}/")
    logger.warning("    +-- tiger_001/")
    logger.warning("    |   +-- image1.jpg")
    logger.warning("    |   +-- ...")
    logger.warning("    +-- tiger_002/")
    logger.warning("    |   +-- ...")
    logger.warning("    +-- ...")
    logger.warning("")
    logger.warning("After downloading, run this script again to verify.")
    logger.warning("=" * 80)


def download_wildlife_reid_kaggle(destination: Path) -> bool:
    """Download WildlifeReID-10k dataset from Kaggle"""
    try:
        import kagglehub
        
        logger.info("Downloading WildlifeReID-10k dataset from Kaggle...")
        logger.info("This may take a while (dataset is very large ~140k images)...")
        
        # Download latest version
        path = kagglehub.dataset_download("wildlifedatasets/wildlifereid-10k")
        
        logger.info(f"Dataset downloaded to: {path}")
        
        # Copy to destination
        source_path = Path(path)
        if source_path.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            if source_path.is_dir():
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.copytree(source_path, destination)
                logger.info(f"Copied dataset to: {destination}")
            else:
                # Extract if zip
                import zipfile
                with zipfile.ZipFile(source_path, 'r') as zip_ref:
                    zip_ref.extractall(destination.parent)
                logger.info(f"Extracted dataset to: {destination.parent}")
            
            return True
        else:
            logger.error(f"Downloaded path does not exist: {path}")
            return False
            
    except ImportError:
        logger.error("kagglehub not installed. Install with: pip install kagglehub")
        return False
    except Exception as e:
        logger.error(f"Error downloading WildlifeReID-10k from Kaggle: {e}", exc_info=True)
        return False


def verify_atrw_structure(destination: Path) -> bool:
    """Verify ATRW dataset structure"""
    if not destination.exists():
        return False
    
    # Check if it's a directory with tiger subdirectories
    if not destination.is_dir():
        return False
    
    # Look for tiger subdirectories (tiger_001, tiger_002, etc.)
    tiger_dirs = [d for d in destination.iterdir() if d.is_dir() and d.name.startswith('tiger_')]
    
    if len(tiger_dirs) == 0:
        # Maybe images are directly in the directory
        image_files = list(destination.glob('*.jpg')) + list(destination.glob('*.jpeg')) + \
                     list(destination.glob('*.png'))
        if len(image_files) > 0:
            logger.warning(f"Found {len(image_files)} images directly in {destination}")
            logger.warning("Expected structure: images organized by tiger ID in subdirectories")
            return True
        return False
    
    # Count images
    total_images = 0
    for tiger_dir in tiger_dirs:
        images = list(tiger_dir.glob('*.jpg')) + list(tiger_dir.glob('*.jpeg')) + \
                 list(tiger_dir.glob('*.png'))
        total_images += len(images)
    
    logger.info(f"Found {len(tiger_dirs)} tiger directories with {total_images} total images")
    return len(tiger_dirs) > 0 and total_images > 0


def download_atrw(destination: Path, use_kaggle: bool = True) -> bool:
    """
    Download ATRW dataset.
    
    Args:
        destination: Path to extract images to (e.g., data/models/atrw/images)
        use_kaggle: Whether to try Kaggle download first
        
    Returns:
        True if successful, False otherwise
    """
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if already exists and valid
    if verify_atrw_structure(destination):
        logger.info(f"ATRW dataset already exists at {destination}")
        return True
    
    # Try Kaggle download
    if use_kaggle and check_kaggle_installed():
        logger.info("Attempting to download ATRW from Kaggle...")
        if download_atrw_kaggle(destination):
            if verify_atrw_structure(destination):
                logger.info("✓ ATRW dataset downloaded and verified successfully")
                return True
            else:
                logger.warning("Downloaded but structure verification failed")
    
    # Fall back to manual instructions
    download_atrw_manual_instructions(destination)
    return False


def download_wildlife_reid(destination: Path, use_kaggle: bool = True) -> bool:
    """
    Download WildlifeReID-10k dataset.
    
    Args:
        destination: Path to extract dataset to
        use_kaggle: Whether to try Kaggle download first
        
    Returns:
        True if successful, False otherwise
    """
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if already exists
    if destination.exists() and destination.is_dir():
        # Check if it has content
        if any(destination.iterdir()):
            logger.info(f"WildlifeReID-10k dataset already exists at {destination}")
            return True
    
    # Try Kaggle download
    if use_kaggle and check_kaggle_installed():
        logger.info("Attempting to download WildlifeReID-10k from Kaggle...")
        if download_wildlife_reid_kaggle(destination):
            logger.info("✓ WildlifeReID-10k dataset downloaded successfully")
            return True
    
    # Manual instructions
    logger.warning("=" * 80)
    logger.warning("MANUAL DOWNLOAD REQUIRED FOR WildlifeReID-10k")
    logger.warning("=" * 80)
    logger.warning("")
    logger.warning("Visit: https://www.kaggle.com/datasets/wildlifedatasets/wildlifereid-10k")
    logger.warning(f"Extract to: {destination}")
    logger.warning("=" * 80)
    return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download datasets for Tiger ID system"
    )
    parser.add_argument(
        "--atrw-dest",
        type=str,
        default="data/models/atrw/images",
        help="Destination for ATRW images (default: data/models/atrw/images)"
    )
    parser.add_argument(
        "--wildlife-reid-dest",
        type=str,
        default="data/datasets/wildlife-datasets/data/WildlifeReID10k",
        help="Destination for WildlifeReID-10k dataset"
    )
    parser.add_argument(
        "--no-kaggle",
        action="store_true",
        help="Skip Kaggle download, only show manual instructions"
    )
    parser.add_argument(
        "--atrw-only",
        action="store_true",
        help="Only download ATRW dataset"
    )
    parser.add_argument(
        "--wildlife-reid-only",
        action="store_true",
        help="Only download WildlifeReID-10k dataset"
    )
    
    args = parser.parse_args()
    
    results = {
        "atrw": False,
        "wildlife_reid": False
    }
    
    # Download ATRW
    if not args.wildlife_reid_only:
        logger.info("=" * 80)
        logger.info("Downloading ATRW Dataset")
        logger.info("=" * 80)
        results["atrw"] = download_atrw(
            Path(args.atrw_dest),
            use_kaggle=not args.no_kaggle
        )
    
    # Download WildlifeReID-10k
    if not args.atrw_only:
        logger.info("")
        logger.info("=" * 80)
        logger.info("Downloading WildlifeReID-10k Dataset")
        logger.info("=" * 80)
        results["wildlife_reid"] = download_wildlife_reid(
            Path(args.wildlife_reid_dest),
            use_kaggle=not args.no_kaggle
        )
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("Download Summary")
    logger.info("=" * 80)
    logger.info(f"ATRW: {'[OK] Downloaded' if results['atrw'] else '[X] Not downloaded (see instructions above)'}")
    logger.info(f"WildlifeReID-10k: {'[OK] Downloaded' if results['wildlife_reid'] else '[X] Not downloaded (see instructions above)'}")
    logger.info("=" * 80)
    
    if not results["atrw"] and not args.wildlife_reid_only:
        logger.warning("")
        logger.warning("[!] ATRW dataset is required for tiger identification!")
        logger.warning("Please download it manually using the instructions above.")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
