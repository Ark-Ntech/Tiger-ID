#!/usr/bin/env python3
"""
Download datasets for Tiger ID system.

This script provides download instructions and helpers for:
- ATRW (Amur Tiger Re-Identification in the Wild)
- MetaWild (multimodal Animal Re-ID dataset)
- Other wildlife datasets
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Dataset download information
BASE_DATASET_DIR = Path(__file__).parent.parent / "data" / "datasets"

ATRW_INFO = {
    "name": "ATRW (Amur Tiger Re-Identification in the Wild)",
    "description": "Primary tiger Re-ID dataset with 92 tigers",
    "sources": {
        "lila": "https://lila.science/datasets/atrw/",
        "kaggle": "https://www.kaggle.com/datasets/quadeer15sh/amur-tiger-reidentification",
        "opendatalab": "https://opendatalab.com/OpenDataLab/ATRW/download",
        "paper": "https://dl.acm.org/doi/10.1145/3394171.3413569"
    },
    "expected_structure": {
        "images": "data/models/atrw/images/",
        "annotations": "data/models/atrw/annotations/"
    }
}

METAWILD_INFO = {
    "name": "MetaWild",
    "description": "Multimodal Animal Re-ID dataset",
    "sources": {
        "paper": "https://dl.acm.org/doi/10.1145/3746027.3758249"
    },
    "expected_structure": {
        "data": "data/datasets/metawild/"
    }
}


def print_download_instructions(dataset_name: str) -> None:
    """
    Print download instructions for a dataset.
    
    Args:
        dataset_name: Name of dataset ("atrw", "metawild")
    """
    if dataset_name == "atrw":
        info = ATRW_INFO
        logger.info(f"\n{info['name']}")
        logger.info(f"Description: {info['description']}")
        logger.info("\nDownload Sources:")
        logger.info(f"  - LILA: {info['sources']['lila']}")
        logger.info(f"  - Kaggle: {info['sources']['kaggle']}")
        logger.info(f"  - OpenDataLab: {info['sources']['opendatalab']}")
        logger.info(f"  - Paper: {info['sources']['paper']}")
        logger.info("\nExpected Structure:")
        logger.info(f"  - Images: {info['expected_structure']['images']}")
        logger.info(f"  - Annotations: {info['expected_structure']['annotations']}")
        logger.info("\nDownload Instructions:")
        logger.info("  1. Visit one of the sources above to download the dataset")
        logger.info("  2. Extract to data/models/atrw/ directory")
        logger.info("  3. Ensure images/ and annotations/ directories exist")
        
    elif dataset_name == "metawild":
        info = METAWILD_INFO
        logger.info(f"\n{info['name']}")
        logger.info(f"Description: {info['description']}")
        logger.info("\nDownload Sources:")
        logger.info(f"  - Paper: {info['sources']['paper']}")
        logger.info("\nExpected Structure:")
        logger.info(f"  - Data: {info['expected_structure']['data']}")
        logger.info("\nNote: MetaWild dataset download instructions are available in the paper.")
        logger.info("Visit the paper link for dataset access information.")
        
    else:
        logger.error(f"Unknown dataset: {dataset_name}")


def verify_dataset_structure(dataset_name: str) -> bool:
    """
    Verify that a dataset has the expected directory structure.
    
    Args:
        dataset_name: Name of dataset ("atrw", "metawild")
        
    Returns:
        True if structure is correct, False otherwise
    """
    if dataset_name == "atrw":
        base_dir = Path(__file__).parent.parent / "data" / "models" / "atrw"
        images_dir = base_dir / "images"
        annotations_dir = base_dir / "annotations"
        
        if not base_dir.exists():
            logger.warning(f"ATRW base directory not found: {base_dir}")
            return False
        
        if not images_dir.exists():
            logger.warning(f"ATRW images directory not found: {images_dir}")
            return False
        
        if not annotations_dir.exists():
            logger.warning(f"ATRW annotations directory not found: {annotations_dir}")
            return False
        
        # Check if directories have content
        image_count = len(list(images_dir.glob("*"))) if images_dir.exists() else 0
        annotation_count = len(list(annotations_dir.glob("*"))) if annotations_dir.exists() else 0
        
        if image_count == 0:
            logger.warning(f"ATRW images directory is empty")
        else:
            logger.info(f"ATRW images directory contains {image_count} items")
        
        if annotation_count == 0:
            logger.warning(f"ATRW annotations directory is empty")
        else:
            logger.info(f"ATRW annotations directory contains {annotation_count} items")
        
        return image_count > 0 or annotation_count > 0
        
    elif dataset_name == "metawild":
        metawild_dir = BASE_DATASET_DIR / "metawild"
        
        if not metawild_dir.exists():
            logger.warning(f"MetaWild directory not found: {metawild_dir}")
            return False
        
        file_count = len(list(metawild_dir.glob("*")))
        if file_count == 0:
            logger.warning(f"MetaWild directory is empty")
            return False
        
        logger.info(f"MetaWild directory contains {file_count} items")
        return True
        
    else:
        logger.error(f"Unknown dataset: {dataset_name}")
        return False


def main():
    """Main function to handle CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Download and verify datasets for Tiger ID system"
    )
    parser.add_argument(
        "--dataset",
        choices=["atrw", "metawild", "all"],
        default="all",
        help="Dataset to check (default: all)"
    )
    parser.add_argument(
        "--instructions",
        action="store_true",
        help="Print download instructions"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify dataset structure"
    )
    
    args = parser.parse_args()
    
    datasets = ["atrw", "metawild"] if args.dataset == "all" else [args.dataset]
    
    for dataset in datasets:
        if args.instructions:
            print_download_instructions(dataset)
        
        if args.verify:
            logger.info(f"\nVerifying {dataset} dataset structure...")
            if verify_dataset_structure(dataset):
                logger.info(f"{dataset} dataset structure verified")
            else:
                logger.warning(f"{dataset} dataset structure verification failed")


if __name__ == "__main__":
    main()

