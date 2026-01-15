"""
Generate embeddings for ATRW reference images

This script:
1. Queries all reference tiger images without embeddings
2. Loads each image from disk
3. Generates embedding using TigerReID model via Modal
4. Stores embedding in database
5. Shows progress and statistics

Usage:
    python scripts/generate_reference_embeddings.py
    python scripts/generate_reference_embeddings.py --limit 100  # Process first 100 only
    python scripts/generate_reference_embeddings.py --batch-size 10  # Process 10 at a time
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import argparse
from PIL import Image
import io

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Force SQLite database
os.environ['DATABASE_URL'] = 'sqlite:///data/production.db'

# IMPORTANT: Disable mock mode to use real Modal
os.environ["MODAL_USE_MOCK"] = "false"

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import get_db_session
from backend.database.models import TigerImage
from backend.services.modal_client import ModalClient
from sqlalchemy import and_
import numpy as np


class EmbeddingGenerator:
    """Batch embedding generator for reference images"""

    def __init__(self, batch_size: int = 50, delay_between_batches: float = 2.0):
        """
        Initialize embedding generator

        Args:
            batch_size: Number of images to process in each batch
            delay_between_batches: Seconds to wait between batches (rate limiting)
        """
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.modal_client = ModalClient(
            max_retries=3,
            retry_delay=2.0,
            timeout=120,
            use_mock=False  # Use real Modal
        )

        self.stats = {
            "total": 0,
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }

    async def get_images_without_embeddings(
        self,
        db,
        limit: Optional[int] = None
    ) -> List[TigerImage]:
        """Query reference images without embeddings"""
        query = db.query(TigerImage).filter(
            and_(
                TigerImage.is_reference == True,
                TigerImage.embedding == None
            )
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    async def load_image(self, image_path: str) -> Optional[Image.Image]:
        """Load image from disk"""
        try:
            # Handle relative paths
            if not Path(image_path).is_absolute():
                image_path = Path.cwd() / image_path

            if not Path(image_path).exists():
                print(f"  ⚠️ Image not found: {image_path}")
                return None

            return Image.open(image_path).convert("RGB")
        except Exception as e:
            print(f"  ❌ Error loading image: {e}")
            return None

    async def generate_embedding(
        self,
        image: Image.Image,
        model_name: str = "tiger_reid"
    ) -> Optional[np.ndarray]:
        """Generate embedding using specified model"""
        try:
            if model_name == "tiger_reid":
                result = await self.modal_client.tiger_reid_embedding(image)
            elif model_name == "wildlife_tools":
                result = await self.modal_client.wildlife_tools_embedding(image)
            elif model_name == "rapid_reid":
                result = await self.modal_client.rapid_reid_embedding(image)
            elif model_name == "cvwc2019_reid":
                result = await self.modal_client.cvwc2019_reid_embedding(image)
            else:
                print(f"  ❌ Unknown model: {model_name}")
                return None

            if result.get("success") and result.get("embedding"):
                embedding = np.array(result["embedding"])
                return embedding
            else:
                print(f"  ⚠️ Model returned no embedding: {result.get('message', 'Unknown error')}")
                return None

        except Exception as e:
            print(f"  ❌ Error generating embedding: {e}")
            return None

    async def store_embedding(
        self,
        db,
        tiger_image: TigerImage,
        embedding: np.ndarray
    ) -> bool:
        """Store embedding in database"""
        try:
            # Convert numpy array to list for pgvector/SQLite compatibility
            if isinstance(embedding, np.ndarray):
                embedding_list = embedding.tolist()
            else:
                embedding_list = list(embedding)

            # Ensure correct dimension (2048 for ResNet50)
            if len(embedding_list) != 2048:
                print(f"  ⚠️ Incorrect embedding dimension: {len(embedding_list)}, expected 2048")
                return False

            # Update tiger_image with embedding
            tiger_image.embedding = embedding_list
            db.commit()

            return True

        except Exception as e:
            print(f"  ❌ Error storing embedding: {e}")
            db.rollback()
            return False

    async def process_image(
        self,
        db,
        tiger_image: TigerImage,
        index: int,
        total: int
    ) -> bool:
        """Process a single image"""
        print(f"\n[{index + 1}/{total}] Processing {Path(tiger_image.image_path).name}...")

        # Load image
        image = await self.load_image(tiger_image.image_path)
        if not image:
            self.stats["skipped"] += 1
            return False

        # Generate embedding
        print(f"  📊 Generating embedding...")
        embedding = await self.generate_embedding(image, model_name="tiger_reid")
        if embedding is None:
            self.stats["failed"] += 1
            self.stats["errors"].append({
                "image_id": str(tiger_image.image_id),
                "path": tiger_image.image_path,
                "error": "Failed to generate embedding"
            })
            return False

        print(f"  ✅ Generated embedding: shape={embedding.shape}")

        # Store embedding
        if await self.store_embedding(db, tiger_image, embedding):
            print(f"  💾 Stored embedding in database")
            self.stats["succeeded"] += 1
            return True
        else:
            self.stats["failed"] += 1
            self.stats["errors"].append({
                "image_id": str(tiger_image.image_id),
                "path": tiger_image.image_path,
                "error": "Failed to store embedding"
            })
            return False

    async def process_batch(
        self,
        db,
        images: List[TigerImage],
        batch_num: int,
        total_batches: int
    ):
        """Process a batch of images"""
        print("\n" + "="*70)
        print(f"BATCH {batch_num}/{total_batches}")
        print(f"Processing {len(images)} images")
        print("="*70)

        for i, tiger_image in enumerate(images):
            self.stats["processed"] += 1
            await self.process_image(
                db,
                tiger_image,
                (batch_num - 1) * self.batch_size + i,
                self.stats["total"]
            )

        # Show batch statistics
        print("\n" + "-"*70)
        print(f"Batch {batch_num} Complete:")
        print(f"  Succeeded: {self.stats['succeeded']}")
        print(f"  Failed: {self.stats['failed']}")
        print(f"  Skipped: {self.stats['skipped']}")
        print(f"  Progress: {self.stats['processed']}/{self.stats['total']} ({self.stats['processed']/self.stats['total']*100:.1f}%)")
        print("-"*70)

        # Rate limiting: wait between batches
        if batch_num < total_batches:
            print(f"\nWaiting {self.delay_between_batches}s before next batch...")
            await asyncio.sleep(self.delay_between_batches)

    async def run(self, limit: Optional[int] = None):
        """Run the embedding generation process"""
        start_time = datetime.now()

        print("\n" + "="*70)
        print("ATRW REFERENCE IMAGE EMBEDDING GENERATION")
        print("="*70)
        print()

        with get_db_session() as db:
            # Get images without embeddings
            print("[1] Querying reference images without embeddings...")
            images = await self.get_images_without_embeddings(db, limit=limit)

            if not images:
                print("✅ All reference images already have embeddings!")
                return

            self.stats["total"] = len(images)
            print(f"[OK] Found {len(images)} images without embeddings")
            print()

            # Calculate batches
            total_batches = (len(images) + self.batch_size - 1) // self.batch_size
            print(f"[2] Processing in {total_batches} batches of {self.batch_size} images")
            print(f"    Rate limiting: {self.delay_between_batches}s between batches")
            print()

            # Process in batches
            for batch_num in range(1, total_batches + 1):
                start_idx = (batch_num - 1) * self.batch_size
                end_idx = min(start_idx + self.batch_size, len(images))
                batch = images[start_idx:end_idx]

                await self.process_batch(db, batch, batch_num, total_batches)

        # Final statistics
        duration = datetime.now() - start_time

        print("\n" + "="*70)
        print("EMBEDDING GENERATION COMPLETE")
        print("="*70)
        print(f"Duration: {duration}")
        print(f"Total processed: {self.stats['processed']}")
        print(f"✅ Succeeded: {self.stats['succeeded']} ({self.stats['succeeded']/self.stats['total']*100:.1f}%)")
        print(f"❌ Failed: {self.stats['failed']}")
        print(f"⏭️  Skipped: {self.stats['skipped']}")
        print()

        if self.stats["errors"]:
            print(f"Errors ({len(self.stats['errors'])}):")
            for error in self.stats["errors"][:10]:  # Show first 10 errors
                print(f"  - {error['path']}: {error['error']}")
            if len(self.stats["errors"]) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")

        print("="*70)
        print()

        # Return success if at least 95% succeeded
        success_rate = self.stats['succeeded'] / self.stats['total'] if self.stats['total'] > 0 else 0
        if success_rate >= 0.95:
            print("✅ Embedding generation successful!")
            return 0
        else:
            print(f"⚠️ Embedding generation completed with {self.stats['failed']} failures")
            return 1


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate embeddings for ATRW reference images'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of images to process (default: all)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Number of images per batch (default: 50)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Seconds to wait between batches (default: 2.0)'
    )

    args = parser.parse_args()

    # Verify configuration
    print(f"[CONFIG] DATABASE_URL: {os.getenv('DATABASE_URL')}")
    print(f"[CONFIG] MODAL_USE_MOCK: {os.getenv('MODAL_USE_MOCK')}")
    print(f"[CONFIG] Batch size: {args.batch_size}")
    print(f"[CONFIG] Delay between batches: {args.delay}s")
    if args.limit:
        print(f"[CONFIG] Limit: {args.limit} images")
    print()

    # Run generator
    generator = EmbeddingGenerator(
        batch_size=args.batch_size,
        delay_between_batches=args.delay
    )

    try:
        exit_code = await generator.run(limit=args.limit)
        return exit_code
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
        print(f"Progress: {generator.stats['processed']}/{generator.stats['total']} images")
        return 130
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
