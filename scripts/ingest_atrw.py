#!/usr/bin/env python3
"""
ATRW Dataset Ingestion Script

Properly ingests the ATRW (Amur Tiger Re-identification in the Wild) dataset
using the CSV files that map image filenames to tiger IDs.

Dataset structure:
- data/models/atrw/images/Amur Tigers/train/*.jpg
- data/models/atrw/images/Amur Tigers/test/*.jpg
- data/models/atrw/images/Amur Tigers/reid_list_train.csv (tiger_id,filename)
- data/models/atrw/images/Amur Tigers/reid_list_test.csv (tiger_id,filename)
"""

import sys
import asyncio
from pathlib import Path
from uuid import uuid4
from datetime import datetime
import pandas as pd
from PIL import Image

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.sqlite_connection import get_sqlite_session
from backend.database.models import Tiger, TigerImage, TigerStatus, SideView
from backend.database.vector_search import store_embedding
from backend.models.reid import TigerReIDModel
from backend.utils.logging import get_logger

logger = get_logger(__name__)


async def ingest_atrw_dataset(dry_run: bool = False, max_images: int = None, model_name: str = "tiger_reid"):
    """
    Ingest ATRW dataset using CSV files.
    
    Args:
        dry_run: If True, don't write to database
        max_images: Maximum images to process (for testing)
        model_name: RE-ID model to use (tiger_reid, wildlife_tools, rapid, cvwc2019)
    """
    logger.info("="*60)
    logger.info("ATRW Dataset Ingestion")
    logger.info("="*60)
    
    # Dataset paths
    atrw_base = project_root / "data" / "models" / "atrw" / "images" / "Amur Tigers"
    train_dir = atrw_base / "train"
    test_dir = atrw_base / "test"
    train_csv = atrw_base / "reid_list_train.csv"
    test_csv = atrw_base / "reid_list_test.csv"
    
    # Verify paths exist
    if not atrw_base.exists():
        logger.error(f"ATRW base directory not found: {atrw_base}")
        logger.error("Please download ATRW dataset from:")
        logger.error("  - https://lila.science/datasets/atrw")
        logger.error("  - https://www.kaggle.com/datasets/quadeer15sh/amur-tiger-reidentification")
        return
    
    if not train_csv.exists() or not test_csv.exists():
        logger.error("CSV files not found!")
        return
    
    # Load CSV files
    logger.info(f"Loading CSV files...")
    train_df = pd.read_csv(train_csv, header=None, names=['tiger_id', 'filename'])
    
    # Test CSV has different format - just filenames (one tiger per image)
    test_df_raw = pd.read_csv(test_csv, header=None, names=['filename'])
    # For test set, filename IS the tiger_id (each image is a unique tiger)
    test_df = pd.DataFrame({
        'tiger_id': test_df_raw['filename'].str.replace('.jpg', '', regex=False),
        'filename': test_df_raw['filename']
    })
    
    logger.info(f"Train set: {len(train_df)} images, {train_df['tiger_id'].nunique()} unique tigers")
    logger.info(f"Test set:  {len(test_df)} images, {test_df['tiger_id'].nunique()} unique tigers")
    
    # Combine datasets
    all_df = pd.concat([
        train_df.assign(split='train'),
        test_df.assign(split='test')
    ])
    
    total_tigers = all_df['tiger_id'].nunique()
    total_images = len(all_df)
    
    logger.info(f"Total: {total_images} images, {total_tigers} unique tigers")
    
    if max_images:
        logger.info(f"Limiting to {max_images} images for testing")
        all_df = all_df.head(max_images)
    
    # Initialize Modal-powered ReID model
    from backend.services.tiger_service import TigerService
    from backend.database import get_db_session
    
    logger.info(f"Initializing {model_name} model (Modal backend)...")
    
    # Use TigerService to get the correct model
    with get_db_session() as session:
        tiger_service = TigerService(session)
        available_models = tiger_service.get_available_models()
        
        if model_name not in available_models:
            logger.warning(f"Model {model_name} not available. Available: {available_models}")
            logger.info(f"Using default model: tiger_reid")
            model_name = "tiger_reid"
        
        reid_model = tiger_service._get_model(model_name)
        await reid_model.load_model()
        logger.info(f"Model {model_name} ready")
    
    # Store model for use in processing loop (outside the with block)
    _reid_model = reid_model
    _model_name = model_name
    
    # Process by tiger ID
    stats = {
        'tigers_created': 0,
        'tigers_existing': 0,
        'images_created': 0,
        'images_skipped': 0,
        'embeddings_generated': 0,
        'errors': []
    }
    
    with get_sqlite_session() as session:
        grouped = all_df.groupby('tiger_id')
        
        for tiger_id_num, group in grouped:
            try:
                # Ensure tiger_id_num is an integer
                try:
                    tiger_id_int = int(tiger_id_num)
                except (ValueError, TypeError):
                    logger.warning(f"Skipping invalid tiger_id: {tiger_id_num}")
                    stats['errors'].append(f"Invalid tiger_id: {tiger_id_num}")
                    continue
                
                tiger_id_str = f"ATRW_{tiger_id_int}"
                
                # Check if tiger exists
                tiger = session.query(Tiger).filter(Tiger.alias == tiger_id_str).first()
                
                if tiger:
                    logger.debug(f"Tiger {tiger_id_str} already exists")
                    stats['tigers_existing'] += 1
                else:
                    # Create new tiger
                    tiger = Tiger(
                        tiger_id=uuid4(),
                        name=f"ATRW Tiger {tiger_id_int}",
                        alias=tiger_id_str,
                        status=TigerStatus.active,
                        metadata={
                            'dataset': 'ATRW',
                            'dataset_tiger_id': tiger_id_int,
                            'num_images': len(group)
                        },
                        created_at=datetime.utcnow()
                    )
                    
                    if not dry_run:
                        session.add(tiger)
                        session.flush()
                    
                    logger.info(f"Created tiger: {tiger_id_str} ({len(group)} images)")
                    stats['tigers_created'] += 1
                
                # Process images for this tiger
                for _, row in group.iterrows():
                    filename = row['filename']
                    split = row['split']
                    
                    # Find image file
                    if split == 'train':
                        image_path = train_dir / filename
                    else:
                        image_path = test_dir / filename
                    
                    if not image_path.exists():
                        logger.warning(f"Image not found: {image_path}")
                        stats['errors'].append(f"Image not found: {filename}")
                        continue
                    
                    # Check if image already exists
                    relative_path = str(image_path.relative_to(project_root))
                    existing_image = session.query(TigerImage).filter(
                        TigerImage.tiger_id == tiger.tiger_id,
                        TigerImage.image_path == relative_path
                    ).first()
                    
                    if existing_image:
                        stats['images_skipped'] += 1
                        continue
                    
                    try:
                        # Load image
                        image = Image.open(image_path)
                        if image.mode != 'RGB':
                            image = image.convert('RGB')
                        
                        # Generate embedding using Modal
                        logger.debug(f"Generating embedding for {filename} using {_model_name}...")
                        embedding = await _reid_model.generate_embedding(image)
                        
                        # Create TigerImage record
                        tiger_image = TigerImage(
                            image_id=uuid4(),
                            tiger_id=tiger.tiger_id,
                            image_path=relative_path,
                            side_view=SideView.unknown,
                        meta_data={
                            'dataset_source': 'ATRW',
                            'split': split,
                            'tiger_id_dataset': tiger_id_int,
                            'filename': filename,
                            'width': image.width,
                            'height': image.height
                        },
                            created_at=datetime.utcnow()
                        )
                        
                        if not dry_run:
                            session.add(tiger_image)
                            session.flush()
                            
                            # Store embedding in pgvector
                            if embedding is not None:
                                store_embedding(session, tiger_image.image_id, embedding)
                                stats['embeddings_generated'] += 1
                        
                        stats['images_created'] += 1
                        
                        if stats['images_created'] % 100 == 0:
                            logger.info(f"Processed {stats['images_created']} images...")
                            if not dry_run:
                                session.commit()
                        
                    except Exception as e:
                        logger.error(f"Error processing image {filename}: {e}")
                        stats['errors'].append(f"{filename}: {str(e)}")
                
                if not dry_run:
                    session.commit()
                
            except Exception as e:
                logger.error(f"Error processing tiger {tiger_id_num}: {e}", exc_info=True)
                stats['errors'].append(f"Tiger {tiger_id_num}: {str(e)}")
                if not dry_run:
                    session.rollback()
                continue
    
    logger.info("="*60)
    logger.info("ATRW Ingestion Complete")
    logger.info("="*60)
    logger.info(f"Tigers created: {stats['tigers_created']}")
    logger.info(f"Tigers existing: {stats['tigers_existing']}")
    logger.info(f"Images created: {stats['images_created']}")
    logger.info(f"Images skipped: {stats['images_skipped']}")
    logger.info(f"Embeddings generated: {stats['embeddings_generated']}")
    logger.info(f"Errors: {len(stats['errors'])}")
    
    return stats


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest ATRW dataset')
    parser.add_argument('--dry-run', action='store_true', help='Don\'t write to database')
    parser.add_argument('--max-images', type=int, help='Max images to process (for testing)')
    parser.add_argument('--model', type=str, default='tiger_reid', 
                       choices=['tiger_reid', 'wildlife_tools', 'rapid', 'cvwc2019'],
                       help='RE-ID model to use for embeddings')
    args = parser.parse_args()
    
    await ingest_atrw_dataset(dry_run=args.dry_run, max_images=args.max_images, model_name=args.model)


if __name__ == '__main__':
    asyncio.run(main())

