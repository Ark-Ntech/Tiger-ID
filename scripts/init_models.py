#!/usr/bin/env python3
"""
Initialize models on startup - checks for required models and downloads if missing.

This script is designed to be run automatically on application startup.
It downloads essential models (MegaDetector) and optionally downloads OmniVinci
if configured to use local models.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.logging import get_logger
from backend.config.settings import get_settings
from scripts.download_models import download_megadetector, download_omnivinci

logger = get_logger(__name__)


def check_model_exists(model_path: Path) -> bool:
    """Check if model file exists."""
    if not model_path:
        return False
    return model_path.exists() and model_path.is_file()


def init_models(force_download: bool = False) -> dict:
    """
    Initialize models on startup.
    
    Args:
        force_download: Force download even if models exist
        
    Returns:
        Dictionary with initialization results
    """
    settings = get_settings()
    results = {
        "megadetector": {"status": "skipped", "path": None},
        "omnivinci": {"status": "skipped", "path": None},
        "errors": []
    }
    
    # Check and download MegaDetector (required)
    try:
        megadetector_path = Path(settings.models.detection.path)
        if not check_model_exists(megadetector_path) or force_download:
            logger.info("MegaDetector model not found, downloading...")
            success = download_megadetector(
                version=settings.models.detection.version,
                model_dir=megadetector_path.parent
            )
            if success:
                results["megadetector"] = {
                    "status": "downloaded",
                    "path": str(megadetector_path)
                }
                logger.info("MegaDetector downloaded successfully")
            else:
                results["megadetector"] = {
                    "status": "failed",
                    "path": str(megadetector_path)
                }
                results["errors"].append("Failed to download MegaDetector")
                logger.warning("MegaDetector download failed - will use YOLOv5 fallback")
        else:
            results["megadetector"] = {
                "status": "exists",
                "path": str(megadetector_path)
            }
            logger.info(f"MegaDetector already exists at {megadetector_path}")
    except Exception as e:
        logger.error(f"Error initializing MegaDetector: {e}")
        results["errors"].append(f"MegaDetector initialization error: {e}")
        results["megadetector"]["status"] = "error"
    
    # Check and download OmniVinci (optional, only if USE_LOCAL=true)
    try:
        if settings.omnivinci.use_local_model:
            omnivinci_path = Path(settings.omnivinci.local_model_path)
            # Check if model directory exists and has content
            if not omnivinci_path.exists() or not any(omnivinci_path.iterdir()) or force_download:
                logger.info("OmniVinci local model not found, downloading...")
                logger.info("Note: OmniVinci is large (~18GB), this may take a while...")
                success = download_omnivinci(model_dir=omnivinci_path)
                if success:
                    results["omnivinci"] = {
                        "status": "downloaded",
                        "path": str(omnivinci_path)
                    }
                    logger.info("OmniVinci downloaded successfully")
                else:
                    results["omnivinci"] = {
                        "status": "failed",
                        "path": str(omnivinci_path)
                    }
                    results["errors"].append("Failed to download OmniVinci")
                    logger.warning("OmniVinci download failed - will skip multi-modal features")
            else:
                results["omnivinci"] = {
                    "status": "exists",
                    "path": str(omnivinci_path)
                }
                logger.info(f"OmniVinci already exists at {omnivinci_path}")
        else:
            logger.info("OmniVinci local model disabled (OMNIVINCI_USE_LOCAL=false)")
            results["omnivinci"]["status"] = "disabled"
    except Exception as e:
        logger.error(f"Error initializing OmniVinci: {e}")
        results["errors"].append(f"OmniVinci initialization error: {e}")
        results["omnivinci"]["status"] = "error"
    
    # Summary
    if results["errors"]:
        logger.warning(f"Model initialization completed with {len(results['errors'])} errors")
        for error in results["errors"]:
            logger.warning(f"  - {error}")
    else:
        logger.info("Model initialization completed successfully")
    
    return results


def main():
    """Main entry point for script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Initialize models for Tiger ID system"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force download even if models exist"
    )
    
    args = parser.parse_args()
    
    results = init_models(force_download=args.force)
    
    # Exit with error code if critical models failed
    if results["megadetector"]["status"] == "failed":
        logger.error("Critical model (MegaDetector) failed to download")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()

