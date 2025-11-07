#!/usr/bin/env python3
"""
Dataset preparation script for Tiger ID model testing.

This script extracts and organizes tiger images from ATRW and WildlifeReID-10k datasets,
creates train/val/test splits maintaining tiger identity separation, and generates
ground truth labels for model evaluation.
"""

import sys
import argparse
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
import random
import pandas as pd
from PIL import Image
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.config.settings import get_settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Image extensions to process
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}


class DatasetPreparer:
    """Main class for preparing test datasets"""
    
    def __init__(
        self,
        output_dir: Path,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        min_images_per_tiger: int = 2,
        seed: int = 42
    ):
        """
        Initialize dataset preparer
        
        Args:
            output_dir: Directory to save prepared datasets
            train_ratio: Ratio of tigers for training
            val_ratio: Ratio of tigers for validation
            test_ratio: Ratio of tigers for testing
            min_images_per_tiger: Minimum images required per tiger
            seed: Random seed for reproducibility
        """
        self.output_dir = Path(output_dir)
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.min_images_per_tiger = min_images_per_tiger
        self.seed = seed
        
        # Validate ratios
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, \
            "Ratios must sum to 1.0"
        
        # Set random seed
        random.seed(seed)
        np.random.seed(seed)
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.train_dir = self.output_dir / "train"
        self.val_dir = self.output_dir / "val"
        self.test_dir = self.output_dir / "test"
        
        for dir_path in [self.train_dir, self.val_dir, self.test_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.settings = get_settings()
        self.stats = {
            'tigers_total': 0,
            'tigers_train': 0,
            'tigers_val': 0,
            'tigers_test': 0,
            'images_train': 0,
            'images_val': 0,
            'images_test': 0,
            'tigers_skipped': 0
        }
    
    def prepare_atrw_dataset(self, atrw_path: Path) -> Dict[str, Any]:
        """
        Prepare ATRW dataset for testing
        
        Args:
            atrw_path: Path to ATRW dataset
            
        Returns:
            Dictionary with preparation results
        """
        logger.info(f"Preparing ATRW dataset from {atrw_path}")
        
        images_dir = atrw_path / "images"
        if not images_dir.exists():
            logger.error(f"ATRW images directory not found: {images_dir}")
            return {'status': 'error', 'reason': 'images directory not found'}
        
        # Collect all tiger images
        tiger_images = defaultdict(list)
        
        tiger_dirs = [d for d in images_dir.iterdir() if d.is_dir()]
        logger.info(f"Found {len(tiger_dirs)} tiger directories")
        
        for tiger_dir in tiger_dirs:
            tiger_id = tiger_dir.name
            image_files = [
                f for f in tiger_dir.iterdir()
                if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
            ]
            
            if len(image_files) >= self.min_images_per_tiger:
                tiger_images[tiger_id] = image_files
            else:
                logger.warning(
                    f"Skipping tiger {tiger_id}: only {len(image_files)} images "
                    f"(minimum: {self.min_images_per_tiger})"
                )
                self.stats['tigers_skipped'] += 1
        
        self.stats['tigers_total'] = len(tiger_images)
        logger.info(f"Processing {len(tiger_images)} tigers with sufficient images")
        
        # Split tigers into train/val/test
        tiger_ids = list(tiger_images.keys())
        random.shuffle(tiger_ids)
        
        n_train = int(len(tiger_ids) * self.train_ratio)
        n_val = int(len(tiger_ids) * self.val_ratio)
        n_test = len(tiger_ids) - n_train - n_val
        
        train_tigers = tiger_ids[:n_train]
        val_tigers = tiger_ids[n_train:n_train + n_val]
        test_tigers = tiger_ids[n_train + n_val:]
        
        self.stats['tigers_train'] = len(train_tigers)
        self.stats['tigers_val'] = len(val_tigers)
        self.stats['tigers_test'] = len(test_tigers)
        
        logger.info(
            f"Split: {len(train_tigers)} train, {len(val_tigers)} val, "
            f"{len(test_tigers)} test tigers"
        )
        
        # Process each split
        splits = {
            'train': (train_tigers, self.train_dir),
            'val': (val_tigers, self.val_dir),
            'test': (test_tigers, self.test_dir)
        }
        
        manifest_data = {
            'dataset': 'ATRW',
            'source_path': str(atrw_path),
            'splits': {},
            'metadata': {
                'total_tigers': len(tiger_ids),
                'train_ratio': self.train_ratio,
                'val_ratio': self.val_ratio,
                'test_ratio': self.test_ratio,
                'min_images_per_tiger': self.min_images_per_tiger
            }
        }
        
        for split_name, (tiger_list, split_dir) in splits.items():
            split_manifest = self._process_split(
                split_name, tiger_list, tiger_images, split_dir, atrw_path
            )
            manifest_data['splits'][split_name] = split_manifest
            
            if split_name == 'train':
                self.stats['images_train'] = split_manifest['total_images']
            elif split_name == 'val':
                self.stats['images_val'] = split_manifest['total_images']
            elif split_name == 'test':
                self.stats['images_test'] = split_manifest['total_images']
        
        # Save manifest
        manifest_path = self.output_dir / "atrw_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
        
        logger.info(f"✓ ATRW dataset prepared. Manifest saved to {manifest_path}")
        
        return {
            'status': 'success',
            'manifest_path': str(manifest_path),
            'stats': self.stats.copy()
        }
    
    def _process_split(
        self,
        split_name: str,
        tiger_list: List[str],
        tiger_images: Dict[str, List[Path]],
        split_dir: Path,
        source_path: Path
    ) -> Dict[str, Any]:
        """
        Process a single split (train/val/test)
        
        Args:
            split_name: Name of the split
            tiger_list: List of tiger IDs for this split
            tiger_images: Dictionary mapping tiger IDs to image paths
            split_dir: Directory to save split images
            source_path: Source dataset path
            
        Returns:
            Manifest data for this split
        """
        logger.info(f"Processing {split_name} split...")
        
        split_manifest = {
            'split': split_name,
            'tigers': [],
            'total_images': 0,
            'images': []
        }
        
        for tiger_id in tiger_list:
            tiger_dir = split_dir / tiger_id
            tiger_dir.mkdir(parents=True, exist_ok=True)
            
            tiger_images_list = tiger_images[tiger_id]
            tiger_manifest = {
                'tiger_id': tiger_id,
                'images': [],
                'image_count': len(tiger_images_list)
            }
            
            for img_path in tiger_images_list:
                # Copy image to split directory
                dest_path = tiger_dir / img_path.name
                
                # Handle name conflicts
                counter = 1
                while dest_path.exists():
                    stem = img_path.stem
                    suffix = img_path.suffix
                    dest_path = tiger_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                try:
                    shutil.copy2(img_path, dest_path)
                    
                    # Get image metadata
                    try:
                        with Image.open(dest_path) as img:
                            width, height = img.size
                            image_metadata = {
                                'filename': dest_path.name,
                                'path': str(dest_path.relative_to(split_dir)),
                                'source_path': str(img_path.relative_to(source_path)),
                                'width': width,
                                'height': height,
                                'tiger_id': tiger_id
                            }
                    except Exception as e:
                        logger.warning(f"Failed to read image metadata for {dest_path}: {e}")
                        image_metadata = {
                            'filename': dest_path.name,
                            'path': str(dest_path.relative_to(split_dir)),
                            'source_path': str(img_path.relative_to(source_path)),
                            'tiger_id': tiger_id
                        }
                    
                    tiger_manifest['images'].append(image_metadata)
                    split_manifest['images'].append(image_metadata)
                    
                except Exception as e:
                    logger.error(f"Failed to copy image {img_path} to {dest_path}: {e}")
                    continue
            
            split_manifest['total_images'] += len(tiger_manifest['images'])
            split_manifest['tigers'].append(tiger_manifest)
        
        logger.info(
            f"✓ {split_name} split: {len(tiger_list)} tigers, "
            f"{split_manifest['total_images']} images"
        )
        
        return split_manifest
    
    def prepare_wildlife_reid_10k_tiger_subset(
        self,
        wildlife_datasets_path: Path
    ) -> Dict[str, Any]:
        """
        Prepare WildlifeReID-10k tiger subset for testing
        
        Args:
            wildlife_datasets_path: Path to wildlife-datasets directory
            
        Returns:
            Dictionary with preparation results
        """
        logger.info(f"Preparing WildlifeReID-10k tiger subset from {wildlife_datasets_path}")
        
        try:
            # Try to import wildlife_datasets
            sys.path.insert(0, str(wildlife_datasets_path))
            from wildlife_datasets.datasets import ATRW
            from wildlife_datasets.loader import load_dataset
            
            # Load ATRW dataset from wildlife-datasets
            atrw_dataset = load_dataset(
                ATRW,
                root_dataset=str(wildlife_datasets_path.parent),
                root_dataframe=str(wildlife_datasets_path / "wildlife_datasets" / "tests" / "csv")
            )
            
            if atrw_dataset is None or len(atrw_dataset) == 0:
                logger.warning("WildlifeReID-10k ATRW dataset not available")
                return {'status': 'skipped', 'reason': 'dataset not available'}
            
            # Get metadata DataFrame
            df = atrw_dataset.metadata
            
            # Filter for tiger images if species column exists
            if 'species' in df.columns:
                tiger_df = df[df['species'].str.contains('tiger', case=False, na=False)]
            else:
                # Assume all images are tigers if no species column
                tiger_df = df
            
            if len(tiger_df) == 0:
                logger.warning("No tiger images found in WildlifeReID-10k")
                return {'status': 'skipped', 'reason': 'no tiger images'}
            
            logger.info(f"Found {len(tiger_df)} tiger images in WildlifeReID-10k")
            
            # Group by identity
            tiger_images = defaultdict(list)
            for _, row in tiger_df.iterrows():
                identity = str(row['identity'])
                path = row['path']
                tiger_images[identity].append(path)
            
            # Filter tigers with minimum images
            filtered_tigers = {
                tid: paths for tid, paths in tiger_images.items()
                if len(paths) >= self.min_images_per_tiger
            }
            
            logger.info(
                f"Processing {len(filtered_tigers)} tigers with sufficient images"
            )
            
            # Create output directory for WildlifeReID-10k
            wildlife_output_dir = self.output_dir / "wildlife_reid_10k"
            wildlife_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create manifest
            manifest_data = {
                'dataset': 'WildlifeReID-10k',
                'source_path': str(wildlife_datasets_path),
                'tigers': [],
                'total_images': 0,
                'metadata': {
                    'total_tigers': len(filtered_tigers),
                    'min_images_per_tiger': self.min_images_per_tiger
                }
            }
            
            for tiger_id, image_paths in filtered_tigers.items():
                tiger_manifest = {
                    'tiger_id': tiger_id,
                    'images': [],
                    'image_count': len(image_paths)
                }
                
                for img_path in image_paths:
                    tiger_manifest['images'].append({
                        'path': str(img_path),
                        'tiger_id': tiger_id
                    })
                    manifest_data['total_images'] += 1
                
                manifest_data['tigers'].append(tiger_manifest)
            
            # Save manifest
            manifest_path = wildlife_output_dir / "wildlife_reid_10k_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest_data, f, indent=2)
            
            logger.info(
                f"✓ WildlifeReID-10k tiger subset prepared. "
                f"Manifest saved to {manifest_path}"
            )
            
            return {
                'status': 'success',
                'manifest_path': str(manifest_path),
                'tigers': len(filtered_tigers),
                'images': manifest_data['total_images']
            }
            
        except ImportError as e:
            logger.warning(f"Could not import wildlife_datasets: {e}")
            return {'status': 'skipped', 'reason': f'import error: {e}'}
        except Exception as e:
            logger.error(f"Error preparing WildlifeReID-10k: {e}", exc_info=True)
            return {'status': 'error', 'reason': str(e)}
    
    def create_ground_truth_labels(self) -> Dict[str, Any]:
        """
        Create ground truth labels file for all prepared datasets
        
        Returns:
            Dictionary with ground truth labels
        """
        logger.info("Creating ground truth labels...")
        
        ground_truth = {
            'train': {},
            'val': {},
            'test': {}
        }
        
        # Process ATRW splits
        for split_name in ['train', 'val', 'test']:
            split_dir = self.output_dir / split_name
            if not split_dir.exists():
                continue
            
            tiger_dirs = [d for d in split_dir.iterdir() if d.is_dir()]
            
            for tiger_dir in tiger_dirs:
                tiger_id = tiger_dir.name
                image_files = [
                    f for f in tiger_dir.iterdir()
                    if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
                ]
                
                for img_path in image_files:
                    relative_path = str(img_path.relative_to(self.output_dir))
                    ground_truth[split_name][relative_path] = tiger_id
        
        # Save ground truth
        gt_path = self.output_dir / "ground_truth.json"
        with open(gt_path, 'w') as f:
            json.dump(ground_truth, f, indent=2)
        
        logger.info(f"✓ Ground truth labels saved to {gt_path}")
        
        return {
            'status': 'success',
            'ground_truth_path': str(gt_path),
            'train_images': len(ground_truth['train']),
            'val_images': len(ground_truth['val']),
            'test_images': len(ground_truth['test'])
        }
    
    def generate_dataset_summary(self) -> Dict[str, Any]:
        """
        Generate summary of prepared datasets
        
        Returns:
            Summary dictionary
        """
        summary = {
            'output_directory': str(self.output_dir),
            'statistics': self.stats.copy(),
            'splits': {
                'train_ratio': self.train_ratio,
                'val_ratio': self.val_ratio,
                'test_ratio': self.test_ratio
            },
            'files': []
        }
        
        # List all manifest files
        for manifest_file in self.output_dir.glob("*_manifest.json"):
            summary['files'].append(str(manifest_file.relative_to(self.output_dir)))
        
        if (self.output_dir / "ground_truth.json").exists():
            summary['files'].append("ground_truth.json")
        
        # Save summary
        summary_path = self.output_dir / "dataset_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"✓ Dataset summary saved to {summary_path}")
        
        return summary


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Prepare tiger datasets for model testing"
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/processed/test_datasets',
        help='Output directory for prepared datasets'
    )
    parser.add_argument(
        '--atrw-path',
        type=str,
        default=None,
        help='Path to ATRW dataset (default: from settings)'
    )
    parser.add_argument(
        '--wildlife-datasets-path',
        type=str,
        default=None,
        help='Path to wildlife-datasets directory (default: from settings)'
    )
    parser.add_argument(
        '--train-ratio',
        type=float,
        default=0.7,
        help='Ratio of tigers for training (default: 0.7)'
    )
    parser.add_argument(
        '--val-ratio',
        type=float,
        default=0.15,
        help='Ratio of tigers for validation (default: 0.15)'
    )
    parser.add_argument(
        '--test-ratio',
        type=float,
        default=0.15,
        help='Ratio of tigers for testing (default: 0.15)'
    )
    parser.add_argument(
        '--min-images',
        type=int,
        default=2,
        help='Minimum images per tiger (default: 2)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--skip-wildlife',
        action='store_true',
        help='Skip WildlifeReID-10k preparation'
    )
    
    args = parser.parse_args()
    
    # Get settings
    settings = get_settings()
    
    # Determine paths
    output_dir = Path(args.output_dir)
    atrw_path = Path(args.atrw_path) if args.atrw_path else Path(settings.datasets.atrw_path)
    wildlife_datasets_path = (
        Path(args.wildlife_datasets_path)
        if args.wildlife_datasets_path
        else Path(settings.datasets.wildlife_datasets_path)
    )
    
    # Create preparer
    preparer = DatasetPreparer(
        output_dir=output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        min_images_per_tiger=args.min_images,
        seed=args.seed
    )
    
    results = {}
    
    # Prepare ATRW dataset
    if atrw_path.exists():
        logger.info("=" * 60)
        logger.info("Preparing ATRW dataset")
        logger.info("=" * 60)
        results['atrw'] = preparer.prepare_atrw_dataset(atrw_path)
    else:
        logger.warning(f"ATRW dataset path does not exist: {atrw_path}")
        results['atrw'] = {'status': 'skipped', 'reason': 'path does not exist'}
    
    # Prepare WildlifeReID-10k tiger subset
    if not args.skip_wildlife and wildlife_datasets_path.exists():
        logger.info("=" * 60)
        logger.info("Preparing WildlifeReID-10k tiger subset")
        logger.info("=" * 60)
        results['wildlife_reid_10k'] = preparer.prepare_wildlife_reid_10k_tiger_subset(
            wildlife_datasets_path
        )
    else:
        if args.skip_wildlife:
            logger.info("Skipping WildlifeReID-10k preparation (--skip-wildlife)")
        else:
            logger.warning(
                f"Wildlife datasets path does not exist: {wildlife_datasets_path}"
            )
        results['wildlife_reid_10k'] = {'status': 'skipped'}
    
    # Create ground truth labels
    logger.info("=" * 60)
    logger.info("Creating ground truth labels")
    logger.info("=" * 60)
    results['ground_truth'] = preparer.create_ground_truth_labels()
    
    # Generate summary
    logger.info("=" * 60)
    logger.info("Generating dataset summary")
    logger.info("=" * 60)
    summary = preparer.generate_dataset_summary()
    
    # Print final statistics
    logger.info("=" * 60)
    logger.info("Dataset Preparation Complete")
    logger.info("=" * 60)
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Total tigers: {preparer.stats['tigers_total']}")
    logger.info(
        f"Train: {preparer.stats['tigers_train']} tigers, "
        f"{preparer.stats['images_train']} images"
    )
    logger.info(
        f"Val: {preparer.stats['tigers_val']} tigers, "
        f"{preparer.stats['images_val']} images"
    )
    logger.info(
        f"Test: {preparer.stats['tigers_test']} tigers, "
        f"{preparer.stats['images_test']} images"
    )
    logger.info(f"Skipped: {preparer.stats['tigers_skipped']} tigers")
    
    return results


if __name__ == "__main__":
    main()

