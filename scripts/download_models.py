#!/usr/bin/env python3
"""
Download model weights for various ML models used in Tiger ID system.

This script downloads model weights from various sources:
- MegaDetector (from releases or LILA)
- OmniVinci (from HuggingFace)
- Other models as needed
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Model download URLs and configurations
MEGADETECTOR_V5_URL = "https://github.com/agentmorris/MegaDetector/releases/download/v5.0/md_v5a.0.0.pt"
MEGADETECTOR_V4_URL = "https://github.com/agentmorris/MegaDetector/releases/download/v4.1/md_v4.1.0.pb"

# Default model paths
BASE_MODEL_DIR = Path(__file__).parent.parent / "data" / "models"


def download_file(url: str, destination: Path, chunk_size: int = 8192) -> bool:
    """
    Download a file from URL to destination.
    
    Args:
        url: URL to download from
        destination: Path to save file
        chunk_size: Chunk size for streaming download
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Downloading from {url}...")
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}%", end='', flush=True)
        
        print()  # New line after progress
        logger.info(f"Downloaded to {destination}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download from {url}: {e}")
        return False


def download_megadetector(version: str = "v5", model_dir: Optional[Path] = None) -> bool:
    """
    Download MegaDetector model weights.
    
    Args:
        version: Model version ("v4" or "v5")
        model_dir: Directory to save model (default: data/models/)
        
    Returns:
        True if successful, False otherwise
    """
    model_dir = model_dir or BASE_MODEL_DIR
    
    if version == "v5":
        url = MEGADETECTOR_V5_URL
        filename = "md_v5a.0.0.pt"
    elif version == "v4":
        url = MEGADETECTOR_V4_URL
        filename = "md_v4.1.0.pb"
    else:
        logger.error(f"Unknown MegaDetector version: {version}")
        return False
    
    destination = model_dir / filename
    
    if destination.exists():
        logger.info(f"MegaDetector {version} already exists at {destination}")
        return True
    
    return download_file(url, destination)


def download_omnivinci(model_dir: Optional[Path] = None) -> bool:
    """
    Download OmniVinci model using HuggingFace CLI.
    
    Args:
        model_dir: Directory to save model (default: data/models/omnivinci/omnivinci)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import subprocess
        
        model_dir = model_dir or (BASE_MODEL_DIR / "omnivinci" / "omnivinci")
        model_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Downloading OmniVinci from HuggingFace...")
        logger.info("Note: This requires huggingface-cli to be installed.")
        logger.info("Install with: pip install huggingface_hub[cli]")
        
        cmd = [
            "huggingface-cli",
            "download",
            "nvidia/omnivinci",
            "--local-dir",
            str(model_dir),
            "--local-dir-use-symlinks",
            "False"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"OmniVinci downloaded successfully to {model_dir}")
            return True
        else:
            logger.error(f"Failed to download OmniVinci: {result.stderr}")
            logger.info("You may need to install huggingface-cli: pip install huggingface_hub[cli]")
            return False
            
    except FileNotFoundError:
        logger.error("huggingface-cli not found. Install with: pip install huggingface_hub[cli]")
        return False
    except Exception as e:
        logger.error(f"Failed to download OmniVinci: {e}")
        return False


def main():
    """Main function to handle CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Download model weights for Tiger ID system"
    )
    parser.add_argument(
        "--model",
        choices=["megadetector", "omnivinci", "all"],
        default="all",
        help="Model to download (default: all)"
    )
    parser.add_argument(
        "--megadetector-version",
        choices=["v4", "v5"],
        default="v5",
        help="MegaDetector version (default: v5)"
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=None,
        help="Base directory for models (default: data/models/)"
    )
    
    args = parser.parse_args()
    
    model_dir = args.model_dir or BASE_MODEL_DIR
    
    success = True
    
    if args.model in ["megadetector", "all"]:
        logger.info("Downloading MegaDetector...")
        if not download_megadetector(version=args.megadetector_version, model_dir=model_dir):
            success = False
    
    if args.model in ["omnivinci", "all"]:
        logger.info("Downloading OmniVinci...")
        if not download_omnivinci():
            success = False
    
    if success:
        logger.info("All requested models downloaded successfully!")
    else:
        logger.warning("Some models failed to download. Check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

