"""
Populate reference database with tiger images and embeddings.

This script:
1. Loads tiger images from ATRW dataset
2. Generates embeddings using deployed Modal models
3. Stores tigers and embeddings in database for matching

Run with:
    python scripts/populate_reference_tigers.py --limit 20
"""

import asyncio
import sys
import os
from pathlib import Path
from uuid import uuid4
from dotenv import load_dotenv
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment and disable mock
load_dotenv()
os.environ["MODAL_USE_MOCK"] = "false"

from backend.database import get_db_session
from backend.database.models import Tiger, TigerImage, TigerStatus
from backend.database.vector_search import store_embedding
from backend.services.modal_client import get_modal_client
from PIL import Image
import io
import json

async def populate_reference_data(limit: int = 20, skip_existing: bool = True):
    """
    Populate reference database with tiger images and embeddings
    
    Args:
        limit: Maximum number of tigers to process
        skip_existing: Skip tigers that already have embeddings
    """
    print("=" * 80)
    print("POPULATING REFERENCE TIGER DATABASE")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Limit: {limit} tigers")
    print(f"  Skip existing: {skip_existing}")
    print(f"  Modal mode: {'PRODUCTION' if os.getenv('MODAL_USE_MOCK') == 'false' else 'MOCK'}")
    print()
    
    # Get database session
    db_gen = get_db_session()
    db = next(db_gen)
    
    try:
        # Find ATRW tiger images
        atrw_base = Path("data/models/atrw/images/Amur Tigers")
        train_path = atrw_base / "train"
        test_path = atrw_base / "test"
        
        if not train_path.exists() and not test_path.exists():
            print("ERROR: ATRW dataset not found at:")
            print(f"  {train_path}")
            print(f"  {test_path}")
            print("\nPlease download ATRW dataset first")
            return
        
        # Collect image files
        image_files = []
        for path in [train_path, test_path]:
            if path.exists():
                image_files.extend(list(path.glob("*.jpg"))[:limit//2])
        
        image_files = image_files[:limit]
        
        print(f"Found {len(image_files)} tiger images")
        print()
        
        # Initialize Modal client
        modal_client = get_modal_client()
        
        # Process each image
        successful = 0
        failed = 0
        skipped = 0
        
        for i, img_path in enumerate(image_files, 1):
            try:
                print(f"[{i}/{len(image_files)}] Processing: {img_path.name}")
                
                # Extract tiger ID from filename (ATRW format: 000001.jpg)
                tiger_number = img_path.stem
                tiger_name = f"Tiger_{tiger_number}"
                
                # Check if tiger already exists
                tiger = db.query(Tiger).filter(Tiger.name == tiger_name).first()
                
                if not tiger:
                    # Create new tiger
                    tiger = Tiger(
                        tiger_id=uuid4(),
                        name=tiger_name,
                        alias=f"ATRW_{tiger_number}",
                        status=TigerStatus.active,
                        notes="Imported from ATRW dataset for reference matching"
                    )
                    db.add(tiger)
                    db.commit()
                    print(f"  Created tiger: {tiger_name}")
                else:
                    print(f"  Tiger exists: {tiger_name}")
                
                # Check if image already has embedding
                existing_image = db.query(TigerImage).filter(
                    TigerImage.tiger_id == tiger.tiger_id,
                    TigerImage.image_path == str(img_path)
                ).first()
                
                if existing_image and existing_image.embedding and skip_existing:
                    print(f"  Skipping (already has embedding)")
                    skipped += 1
                    continue
                
                # Load image
                with open(img_path, 'rb') as f:
                    image_bytes = f.read()
                
                print(f"  Loaded image: {len(image_bytes)} bytes")
                
                # Generate embeddings with Modal (use TigerReID as default)
                print(f"  Generating embedding with TigerReIDModel...")
                
                # Convert bytes to PIL Image for Modal
                pil_image = Image.open(io.BytesIO(image_bytes))
                
                # Call Modal to generate embedding
                embedding_result = await modal_client.tiger_reid_embedding(pil_image)
                
                if not embedding_result or not embedding_result.get('success'):
                    print(f"  ERROR: Embedding generation failed: {embedding_result.get('error') if embedding_result else 'Unknown'}")
                    failed += 1
                    continue
                
                embedding_list = embedding_result.get('embedding')
                if not embedding_list:
                    print(f"  ERROR: No embedding in result")
                    failed += 1
                    continue
                
                print(f"  Generated embedding: {len(embedding_list)} dimensions")
                
                # Store in database using direct SQLite connection
                # SQLAlchemy ORM doesn't handle Vector type correctly in SQLite
                import sqlite3
                
                if not existing_image:
                    # Create new tiger image record
                    image_id = uuid4()
                    
                    # Use direct SQLite connection for proper embedding storage
                    sqlite_conn = sqlite3.connect("data/production.db")
                    sqlite_cursor = sqlite_conn.cursor()
                    
                    sqlite_cursor.execute("""
                        INSERT INTO tiger_images 
                        (image_id, tiger_id, image_path, side_view, quality_score, embedding)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        str(image_id).replace('-', ''),  # SQLite stores UUID without dashes
                        str(tiger.tiger_id).replace('-', ''),
                        str(img_path),
                        "unknown",
                        0.8,
                        json.dumps(embedding_list)
                    ))
                    
                    sqlite_conn.commit()
                    sqlite_conn.close()
                    
                    print(f"  Stored in database (new image)")
                else:
                    # Update existing embedding
                    sqlite_conn = sqlite3.connect("data/production.db")
                    sqlite_cursor = sqlite_conn.cursor()
                    
                    sqlite_cursor.execute("""
                        UPDATE tiger_images 
                        SET embedding = ?
                        WHERE image_id = ?
                    """, (
                        json.dumps(embedding_list),
                        str(existing_image.image_id).replace('-', '')
                    ))
                    
                    sqlite_conn.commit()
                    sqlite_conn.close()
                    
                    print(f"  Stored in database (updated)")
                
                successful += 1
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                break
            except Exception as e:
                print(f"  ERROR: {e}")
                failed += 1
                continue
        
        print()
        print("=" * 80)
        print("POPULATION COMPLETE")
        print("=" * 80)
        print(f"\nResults:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Skipped: {skipped}")
        print(f"  Total processed: {successful + failed + skipped}")
        print()
        
        # Verify database state
        tiger_count = db.query(Tiger).count()
        image_count = db.query(TigerImage).count()
        embedded_count = db.query(TigerImage).filter(TigerImage.embedding.isnot(None)).count()
        
        print(f"Database state:")
        print(f"  Total tigers: {tiger_count}")
        print(f"  Total images: {image_count}")
        print(f"  Images with embeddings: {embedded_count}")
        print()
        
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate reference tiger database")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of tigers to process")
    parser.add_argument("--skip-existing", action="store_true", default=True, help="Skip tigers with existing embeddings")
    parser.add_argument("--force", action="store_true", help="Regenerate all embeddings")
    
    args = parser.parse_args()
    
    skip = not args.force if args.force else args.skip_existing
    
    asyncio.run(populate_reference_data(
        limit=args.limit,
        skip_existing=skip
    ))

