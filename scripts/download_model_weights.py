#!/usr/bin/env python3
"""
Download model weights for Tiger ID system.

This script downloads trained model weights for:
1. TigerReIDModel (tiger_reid_model.pth)
2. RAPID Re-ID model (if enabled)
3. CVWC2019 Re-ID model (if enabled)
4. WildlifeTools models (downloaded via HuggingFace/timm automatically)

Note: Some models may need to be trained locally if pre-trained weights are not available.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import urllib.request
import urllib.error

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.utils.logging import get_logger
from backend.config.settings import get_settings

logger = get_logger(__name__)


def download_file(url: str, destination: Path, chunk_size: int = 8192) -> bool:
    """
    Download a file from URL to destination.
    
    Args:
        url: URL to download from
        destination: Path to save file to
        chunk_size: Chunk size for download
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Downloading from: {url}")
        logger.info(f"Saving to: {destination}")
        
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Download with progress
        def show_progress(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, (block_num * block_size * 100) / total_size)
                print(f"\rProgress: {percent:.1f}%", end='', flush=True)
        
        urllib.request.urlretrieve(url, destination, reporthook=show_progress)
        print()  # New line after progress
        
        if destination.exists() and destination.stat().st_size > 0:
            logger.info(f"✓ Downloaded successfully: {destination}")
            return True
        else:
            logger.error(f"Downloaded file is empty or doesn't exist: {destination}")
            return False
            
    except urllib.error.URLError as e:
        logger.error(f"Error downloading from {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading file: {e}", exc_info=True)
        return False


def download_tiger_reid_weights(destination: Path) -> bool:
    """
    Download TigerReIDModel weights.
    
    Note: Pre-trained weights may not be publicly available.
    If not available, the model will use untrained weights (ResNet50 pretrained on ImageNet).
    
    Args:
        destination: Path to save model weights (e.g., data/models/tiger_reid_model.pth)
        
    Returns:
        True if successful, False otherwise
    """
    destination = Path(destination)
    
    # Check if already exists
    if destination.exists():
        logger.info(f"TigerReIDModel weights already exist at {destination}")
        return True
    
    # TODO: Add actual download URL if pre-trained weights are available
    # For now, provide instructions for training
    logger.warning("=" * 80)
    logger.warning("TigerReIDModel Weights Not Available for Download")
    logger.warning("=" * 80)
    logger.warning("")
    logger.warning("Pre-trained weights for TigerReIDModel are not publicly available.")
    logger.warning("")
    logger.warning("Options:")
    logger.warning("1. Train the model using the ATRW dataset:")
    logger.warning("   - Use scripts/train_tiger_reid.py (if available)")
    logger.warning("   - Or train manually using backend/models/reid.py")
    logger.warning("")
    logger.warning("2. Use untrained model (current default):")
    logger.warning("   - Model will use ResNet50 pretrained on ImageNet")
    logger.warning("   - Embeddings will be less accurate but still functional")
    logger.warning("")
    logger.warning("3. Check for community-trained weights:")
    logger.warning("   - Check HuggingFace: https://huggingface.co/models?search=tiger+reid")
    logger.warning("   - Check model zoo repositories")
    logger.warning("")
    logger.warning("Expected file location: " + str(destination))
    logger.warning("=" * 80)
    
    return False


def download_rapid_weights(destination: Path) -> bool:
    """
    Download RAPID Re-ID model weights.
    
    Args:
        destination: Path to save model weights
        
    Returns:
        True if successful, False otherwise
    """
    destination = Path(destination)
    
    if destination.exists():
        logger.info(f"RAPID model weights already exist at {destination}")
        return True
    
    logger.warning("=" * 80)
    logger.warning("RAPID Model Weights Download")
    logger.warning("=" * 80)
    logger.warning("")
    logger.warning("RAPID model weights need to be downloaded from the RAPID repository.")
    logger.warning("Check: https://github.com/rapid-reid/rapid-reid")
    logger.warning(f"Expected location: {destination}")
    logger.warning("=" * 80)
    
    return False


def download_cvwc2019_weights(destination: Path) -> bool:
    """
    Download CVWC2019 Re-ID model weights.
    
    Args:
        destination: Path to save model weights
        
    Returns:
        True if successful, False otherwise
    """
    destination = Path(destination)
    
    if destination.exists():
        logger.info(f"CVWC2019 model weights already exist at {destination}")
        return True
    
    logger.warning("=" * 80)
    logger.warning("CVWC2019 Model Weights Download")
    logger.warning("=" * 80)
    logger.warning("")
    logger.warning("CVWC2019 model weights need to be downloaded from the CVWC2019 repository.")
    logger.warning("Check: data/models/cvwc2019/ for repository")
    logger.warning(f"Expected location: {destination}")
    logger.warning("=" * 80)
    
    return False


def verify_wildlife_tools_weights() -> bool:
    """
    Verify WildlifeTools models are available.
    
    WildlifeTools models are downloaded automatically via HuggingFace/timm.
    This just verifies the package is installed.
    
    Returns:
        True if WildlifeTools is available, False otherwise
    """
    try:
        import timm
        # Try to load a model to verify
        model = timm.create_model("hf-hub:BVRA/MegaDescriptor-L-384", pretrained=True, num_classes=0)
        logger.info("✓ WildlifeTools models are available via HuggingFace")
        return True
    except ImportError:
        logger.warning("timm not installed. WildlifeTools models require: pip install timm")
        return False
    except Exception as e:
        logger.warning(f"Could not verify WildlifeTools models: {e}")
        return False


def download_all_weights(force: bool = False) -> Dict[str, bool]:
    """
    Download all model weights.
    
    Args:
        force: Force download even if files exist
        
    Returns:
        Dictionary with download results
    """
    settings = get_settings()
    results = {
        "tiger_reid": False,
        "rapid": False,
        "cvwc2019": False,
        "wildlife_tools": False
    }
    
    # TigerReIDModel weights
    logger.info("=" * 80)
    logger.info("TigerReIDModel Weights")
    logger.info("=" * 80)
    tiger_reid_path = Path(settings.models.reid_path)
    if force or not tiger_reid_path.exists():
        results["tiger_reid"] = download_tiger_reid_weights(tiger_reid_path)
    else:
        logger.info(f"✓ TigerReIDModel weights already exist: {tiger_reid_path}")
        results["tiger_reid"] = True
    
    # RAPID weights (if enabled)
    if hasattr(settings.models, 'rapid') and settings.models.rapid.enabled:
        logger.info("")
        logger.info("=" * 80)
        logger.info("RAPID Model Weights")
        logger.info("=" * 80)
        rapid_path = Path(settings.models.rapid.path)
        if force or not rapid_path.exists():
            results["rapid"] = download_rapid_weights(rapid_path)
        else:
            logger.info(f"✓ RAPID model weights already exist: {rapid_path}")
            results["rapid"] = True
    
    # CVWC2019 weights (if enabled)
    if hasattr(settings.models, 'cvwc2019') and settings.models.cvwc2019.enabled:
        logger.info("")
        logger.info("=" * 80)
        logger.info("CVWC2019 Model Weights")
        logger.info("=" * 80)
        cvwc2019_path = Path(settings.models.cvwc2019.path)
        if force or not cvwc2019_path.exists():
            results["cvwc2019"] = download_cvwc2019_weights(cvwc2019_path)
        else:
            logger.info(f"✓ CVWC2019 model weights already exist: {cvwc2019_path}")
            results["cvwc2019"] = True
    
    # WildlifeTools (verify availability)
    logger.info("")
    logger.info("=" * 80)
    logger.info("WildlifeTools Models")
    logger.info("=" * 80)
    results["wildlife_tools"] = verify_wildlife_tools_weights()
    
    return results


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download model weights for Tiger ID system"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force download even if files exist"
    )
    parser.add_argument(
        "--tiger-reid-only",
        action="store_true",
        help="Only download TigerReIDModel weights"
    )
    
    args = parser.parse_args()
    
    if args.tiger_reid_only:
        settings = get_settings()
        tiger_reid_path = Path(settings.models.reid_path)
        success = download_tiger_reid_weights(tiger_reid_path)
        sys.exit(0 if success else 1)
    else:
        results = download_all_weights(force=args.force)
        
        # Summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("Model Weights Download Summary")
        logger.info("=" * 80)
        logger.info(f"TigerReIDModel: {'✓ Available' if results['tiger_reid'] else '✗ Not available (see instructions)'}")
        logger.info(f"RAPID: {'✓ Available' if results['rapid'] else '✗ Not available'}")
        logger.info(f"CVWC2019: {'✓ Available' if results['cvwc2019'] else '✗ Not available'}")
        logger.info(f"WildlifeTools: {'✓ Available' if results['wildlife_tools'] else '✗ Not available'}")
        logger.info("=" * 80)
        
        # Note about untrained model
        if not results["tiger_reid"]:
            logger.warning("")
            logger.warning("⚠ TigerReIDModel will use untrained weights (ResNet50 ImageNet pretrained)")
            logger.warning("This is functional but embeddings may be less accurate.")
            logger.warning("Consider training the model on ATRW dataset for better accuracy.")
        
        sys.exit(0)


if __name__ == "__main__":
    main()

