#!/usr/bin/env python3
"""
Comprehensive dataset ingestion script for Tiger ID system.

This script automatically loads all datasets from data/models/ and data/datasets/
into the database, creating Tiger and TigerImage records with embeddings.
"""

import sys
import argparse
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from uuid import uuid4
import json
import pandas as pd
from PIL import Image
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database import get_db_session
from backend.database.models import Tiger, TigerImage, SideView
from backend.database.vector_search import store_embedding
from backend.config.settings import get_settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Image extensions to process
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}


class DatasetIngester:
    """Main class for ingesting datasets into the database"""
    
    def __init__(self, dry_run: bool = False, skip_existing: bool = True):
        """
        Initialize dataset ingester
        
        Args:
            dry_run: If True, don't actually write to database
            skip_existing: If True, skip images that already exist in database
        """
        self.dry_run = dry_run
        self.skip_existing = skip_existing
        self.settings = get_settings()
        self.stats = {
            'tigers_created': 0,
            'tigers_updated': 0,
            'images_processed': 0,
            'images_skipped': 0,
            'errors': 0
        }
    
    def get_dataset_paths(self) -> Dict[str, Path]:
        """Get all dataset paths from configuration"""
        return {
            'atrw': Path(self.settings.datasets.atrw_path),
            'metawild': Path(self.settings.datasets.metawild_path),
            'wildlife_datasets': Path(self.settings.datasets.wildlife_datasets_path),
            'individual_animal_reid': Path(self.settings.datasets.individual_animal_reid_path),
        }
    
    async def ingest_all_datasets(self) -> Dict[str, Any]:
        """Ingest all available datasets"""
        dataset_paths = self.get_dataset_paths()
        results = {}
        
        for dataset_name, dataset_path in dataset_paths.items():
            if not dataset_path.exists():
                logger.warning(f"Dataset path does not exist: {dataset_path}")
                continue
            
            logger.info(f"Processing dataset: {dataset_name} at {dataset_path}")
            
            try:
                if dataset_name == 'atrw':
                    result = await self.ingest_atrw_dataset(dataset_path)
                elif dataset_name == 'metawild':
                    result = await self.ingest_metawild_dataset(dataset_path)
                elif dataset_name == 'wildlife_datasets':
                    result = await self.ingest_wildlife_datasets(dataset_path)
                elif dataset_name == 'individual_animal_reid':
                    result = await self.ingest_individual_animal_reid(dataset_path)
                else:
                    logger.warning(f"Unknown dataset type: {dataset_name}")
                    continue
                
                results[dataset_name] = result
                logger.info(f"✓ Completed {dataset_name}: {result}")
                
            except Exception as e:
                logger.error(f"Error processing {dataset_name}: {e}", exc_info=True)
                self.stats['errors'] += 1
                results[dataset_name] = {'error': str(e)}
        
        return results
    
    async def ingest_atrw_dataset(self, dataset_path: Path) -> Dict[str, Any]:
        """Ingest ATRW (Amur Tiger Re-identification in the Wild) dataset"""
        images_dir = dataset_path / "images"
        annotations_dir = dataset_path / "annotations"
        
        if not images_dir.exists():
            logger.warning(f"ATRW images directory not found: {images_dir}")
            return {'status': 'skipped', 'reason': 'images directory not found'}
        
        tiger_count = 0
        image_count = 0
        
        with get_db_session() as session:
            # ATRW typically has tiger IDs as directory names
            tiger_dirs = [d for d in images_dir.iterdir() if d.is_dir()]
            
            for tiger_dir in tiger_dirs:
                tiger_id_str = tiger_dir.name
                
                # Get or create tiger
                tiger = await self.get_or_create_tiger(
                    session,
                    name=f"ATRW Tiger {tiger_id_str}",
                    alias=tiger_id_str,
                    dataset_source="ATRW"
                )
                
                # Process images in tiger directory
                image_files = [
                    f for f in tiger_dir.iterdir()
                    if f.suffix.lower() in IMAGE_EXTENSIONS
                ]
                
                for image_file in image_files:
                    try:
                        await self.process_image_file(
                            session,
                            image_file,
                            tiger.tiger_id,
                            metadata={
                                'dataset': 'ATRW',
                                'tiger_id_dataset': tiger_id_str,
                                'source_path': str(image_file.relative_to(dataset_path))
                            }
                        )
                        image_count += 1
                    except Exception as e:
                        logger.error(f"Error processing {image_file}: {e}")
                        self.stats['errors'] += 1
                
                tiger_count += 1
            
            if not self.dry_run:
                session.commit()
        
        return {
            'tigers': tiger_count,
            'images': image_count,
            'status': 'success'
        }
    
    async def ingest_metawild_dataset(self, dataset_path: Path) -> Dict[str, Any]:
        """Ingest MetaWild dataset"""
        # MetaWild structure may vary - scan for images
        image_files = list(dataset_path.rglob("*.*"))
        image_files = [f for f in image_files if f.suffix.lower() in IMAGE_EXTENSIONS]
        
        if not image_files:
            logger.warning(f"No images found in MetaWild dataset: {dataset_path}")
            return {'status': 'skipped', 'reason': 'no images found'}
        
        tiger_count = 0
        image_count = 0
        processed_tigers = {}  # Map dataset tiger IDs to database tiger IDs
        
        with get_db_session() as session:
            for image_file in image_files:
                try:
                    # Try to extract tiger ID from path structure
                    # MetaWild may have different structures - adapt as needed
                    path_parts = image_file.relative_to(dataset_path).parts
                    
                    # Common patterns: .../tiger_id/image.jpg or .../identity/image.jpg
                    tiger_id_str = None
                    for part in path_parts:
                        if part.lower() in ['tiger', 'identity', 'id', 'individual']:
                            idx = path_parts.index(part)
                            if idx + 1 < len(path_parts):
                                tiger_id_str = path_parts[idx + 1]
                                break
                    
                    # Fallback: use parent directory name
                    if not tiger_id_str:
                        tiger_id_str = image_file.parent.name
                    
                    # Get or create tiger
                    if tiger_id_str not in processed_tigers:
                        tiger = await self.get_or_create_tiger(
                            session,
                            name=f"MetaWild Tiger {tiger_id_str}",
                            alias=tiger_id_str,
                            dataset_source="MetaWild"
                        )
                        processed_tigers[tiger_id_str] = tiger.tiger_id
                        tiger_count += 1
                    
                    tiger_id = processed_tigers[tiger_id_str]
                    
                    await self.process_image_file(
                        session,
                        image_file,
                        tiger_id,
                        metadata={
                            'dataset': 'MetaWild',
                            'tiger_id_dataset': tiger_id_str,
                            'source_path': str(image_file.relative_to(dataset_path))
                        }
                    )
                    image_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing {image_file}: {e}")
                    self.stats['errors'] += 1
            
            if not self.dry_run:
                session.commit()
        
        return {
            'tigers': tiger_count,
            'images': image_count,
            'status': 'success'
        }
    
    async def ingest_wildlife_datasets(self, dataset_path: Path) -> Dict[str, Any]:
        """Ingest datasets from wildlife-datasets library"""
        try:
            # Try to use wildlife-datasets library if available
            sys.path.insert(0, str(dataset_path))
            from wildlife_datasets.loader import load_dataset
            from wildlife_datasets.datasets import ATRW as WildlifeATRW
            
            # Load ATRW from wildlife-datasets library
            dataset = load_dataset(
                WildlifeATRW,
                root_dataset=str(dataset_path),
                root_dataframe=str(dataset_path / "dataframes")
            )
            
            tiger_count = 0
            image_count = 0
            processed_tigers = {}
            
            with get_db_session() as session:
                # Process dataset dataframe
                df = dataset.df
                
                if 'identity' in df.columns:
                    for identity in df['identity'].unique():
                        if identity not in processed_tigers:
                            tiger = await self.get_or_create_tiger(
                                session,
                                name=f"Wildlife Dataset Tiger {identity}",
                                alias=str(identity),
                                dataset_source="WildlifeDatasets"
                            )
                            processed_tigers[identity] = tiger.tiger_id
                            tiger_count += 1
                        
                        tiger_id = processed_tigers[identity]
                        
                        # Get images for this identity
                        identity_images = df[df['identity'] == identity]
                        
                        for _, row in identity_images.iterrows():
                            if 'path' in row:
                                image_path = dataset_path / row['path']
                                if image_path.exists():
                                    await self.process_image_file(
                                        session,
                                        image_path,
                                        tiger_id,
                                        metadata={
                                            'dataset': 'WildlifeDatasets',
                                            'identity': str(identity),
                                            'source_path': str(image_path.relative_to(dataset_path))
                                        }
                                    )
                                    image_count += 1
                
                if not self.dry_run:
                    session.commit()
            
            return {
                'tigers': tiger_count,
                'images': image_count,
                'status': 'success'
            }
            
        except ImportError:
            logger.warning("wildlife-datasets library not available, skipping")
            return {'status': 'skipped', 'reason': 'library not available'}
        except Exception as e:
            logger.error(f"Error loading wildlife-datasets: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}
    
    async def ingest_individual_animal_reid(self, dataset_path: Path) -> Dict[str, Any]:
        """Ingest datasets from individual-animal-reid directory"""
        # This directory contains references to various datasets
        # Scan for actual dataset directories or metadata files
        
        tiger_count = 0
        image_count = 0
        
        # Look for CSV files with metadata
        csv_files = list(dataset_path.glob("**/*.csv"))
        
        with get_db_session() as session:
            for csv_file in csv_files:
                try:
                    df = pd.read_csv(csv_file)
                    
                    # Common column names: identity, individual_id, image_path, path
                    identity_col = None
                    path_col = None
                    
                    for col in df.columns:
                        if col.lower() in ['identity', 'individual_id', 'id', 'tiger_id']:
                            identity_col = col
                        if col.lower() in ['image_path', 'path', 'file', 'filename']:
                            path_col = col
                    
                    if not identity_col or not path_col:
                        continue
                    
                    processed_tigers = {}
                    
                    for _, row in df.iterrows():
                        identity = str(row[identity_col])
                        image_path_str = str(row[path_col])
                        
                        # Resolve image path
                        image_path = dataset_path / image_path_str
                        if not image_path.exists():
                            # Try relative to CSV file location
                            image_path = csv_file.parent / image_path_str
                        
                        if not image_path.exists() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                            continue
                        
                        # Get or create tiger
                        if identity not in processed_tigers:
                            tiger = await self.get_or_create_tiger(
                                session,
                                name=f"Dataset Tiger {identity}",
                                alias=identity,
                                dataset_source=csv_file.stem
                            )
                            processed_tigers[identity] = tiger.tiger_id
                            tiger_count += 1
                        
                        tiger_id = processed_tigers[identity]
                        
                        await self.process_image_file(
                            session,
                            image_path,
                            tiger_id,
                            metadata={
                                'dataset': csv_file.stem,
                                'identity': identity,
                                'source_path': str(image_path.relative_to(dataset_path))
                            }
                        )
                        image_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing CSV {csv_file}: {e}")
                    self.stats['errors'] += 1
            
            if not self.dry_run:
                session.commit()
        
        return {
            'tigers': tiger_count,
            'images': image_count,
            'status': 'success'
        }
    
    async def get_or_create_tiger(
        self,
        session,
        name: str,
        alias: Optional[str] = None,
        dataset_source: Optional[str] = None
    ) -> Tiger:
        """Get existing tiger or create new one"""
        # Try to find by alias first
        if alias:
            tiger = session.query(Tiger).filter(Tiger.alias == alias).first()
            if tiger:
                self.stats['tigers_updated'] += 1
                return tiger
        
        # Try to find by name
        tiger = session.query(Tiger).filter(Tiger.name == name).first()
        if tiger:
            self.stats['tigers_updated'] += 1
            return tiger
        
        # Create new tiger
        tiger = Tiger(
            name=name,
            alias=alias,
            status="active",
            tags=[dataset_source] if dataset_source else [],
            notes=f"Imported from {dataset_source}" if dataset_source else None
        )
        
        if not self.dry_run:
            session.add(tiger)
            session.flush()  # Get ID without committing
        
        self.stats['tigers_created'] += 1
        return tiger
    
    async def process_image_file(
        self,
        session,
        image_path: Path,
        tiger_id,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[TigerImage]:
        """Process a single image file and add to database"""
        # Check if image already exists
        if self.skip_existing:
            existing = session.query(TigerImage).filter(
                TigerImage.image_path == str(image_path)
            ).first()
            if existing:
                self.stats['images_skipped'] += 1
                return existing
        
        # Create TigerImage record
        tiger_image = TigerImage(
            tiger_id=tiger_id,
            image_path=str(image_path),
            meta_data=metadata or {},
            verified=False  # Dataset images need verification
        )
        
        if not self.dry_run:
            session.add(tiger_image)
            session.flush()  # Get ID without committing
        
        self.stats['images_processed'] += 1
        
        # Note: Embeddings should be generated separately using process_images.py
        # or a background job, as it requires model loading
        
        return tiger_image
    
    def get_stats(self) -> Dict[str, int]:
        """Get ingestion statistics"""
        return self.stats.copy()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Ingest datasets into Tiger ID database'
    )
    parser.add_argument(
        '--dataset',
        choices=['atrw', 'metawild', 'wildlife_datasets', 'individual_animal_reid', 'all'],
        default='all',
        help='Dataset to ingest (default: all)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode - don\'t write to database'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        default=True,
        help='Skip images that already exist in database'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-ingestion (overwrite existing)'
    )
    
    args = parser.parse_args()
    
    ingester = DatasetIngester(
        dry_run=args.dry_run,
        skip_existing=args.skip_existing and not args.force
    )
    
    if args.dry_run:
        logger.info("Running in DRY RUN mode - no changes will be made")
    
    if args.dataset == 'all':
        results = await ingester.ingest_all_datasets()
    else:
        dataset_paths = ingester.get_dataset_paths()
        if args.dataset not in dataset_paths:
            logger.error(f"Unknown dataset: {args.dataset}")
            return
        
        dataset_path = dataset_paths[args.dataset]
        
        if args.dataset == 'atrw':
            results = {args.dataset: await ingester.ingest_atrw_dataset(dataset_path)}
        elif args.dataset == 'metawild':
            results = {args.dataset: await ingester.ingest_metawild_dataset(dataset_path)}
        elif args.dataset == 'wildlife_datasets':
            results = {args.dataset: await ingester.ingest_wildlife_datasets(dataset_path)}
        elif args.dataset == 'individual_animal_reid':
            results = {args.dataset: await ingester.ingest_individual_animal_reid(dataset_path)}
    
    # Print summary
    stats = ingester.get_stats()
    logger.info("\n" + "="*60)
    logger.info("DATASET INGESTION SUMMARY")
    logger.info("="*60)
    logger.info(f"Tigers created: {stats['tigers_created']}")
    logger.info(f"Tigers updated: {stats['tigers_updated']}")
    logger.info(f"Images processed: {stats['images_processed']}")
    logger.info(f"Images skipped: {stats['images_skipped']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info("="*60)
    
    for dataset_name, result in results.items():
        logger.info(f"{dataset_name}: {result}")
    
    logger.info("\n✓ Dataset ingestion complete!")
    logger.info("\nNote: Image embeddings will need to be generated separately")
    logger.info("Run: python scripts/process_images.py --generate-embeddings")


if __name__ == "__main__":
    asyncio.run(main())

