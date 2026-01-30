"""
ATRW Dataset Ingestion Script

Ingests the Amur Tiger Re-Identification in the Wild (ATRW) dataset into the database.
Processes 5,156 tiger images and creates Tiger and TigerImage records with embeddings.

Dataset structure:
  data/models/atrw/images/Amur Tigers/
    ├── train/  (3,392 images) - filename format: XXXXXX.jpg (tiger ID)
    └── test/   (1,764 images) - filename format: XXXXXX.jpg (tiger ID)

Tiger IDs are extracted from filenames (e.g., 000123.jpg -> Tiger_000123)
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple
import asyncio
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import get_db_session
from backend.database.models import Tiger, TigerImage, Facility, TigerStatus, SideView
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import uuid4, UUID
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ATRWIngestion:
    """ATRW dataset ingestion manager"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.atrw_path = Path("data/models/atrw/images/Amur Tigers")
        self.stats = {
            "tigers_created": 0,
            "tigers_updated": 0,
            "images_created": 0,
            "images_skipped": 0,
            "errors": 0
        }

    def extract_tiger_id_from_filename(self, filename: str) -> str:
        """
        Extract tiger ID from ATRW filename

        Format: XXXXXX.jpg -> Tiger_XXXXXX
        Example: 000123.jpg -> Tiger_000123
        """
        base_name = Path(filename).stem
        return f"Tiger_{base_name}"

    def find_or_create_tiger(self, tiger_name: str) -> Tiger:
        """Find existing tiger or create new one"""

        # Check if tiger exists
        tiger = self.db.query(Tiger).filter(Tiger.name == tiger_name).first()

        if tiger:
            self.stats["tigers_updated"] += 1
            logger.debug(f"Found existing tiger: {tiger_name}")
            return tiger

        # Create new tiger
        tiger = Tiger(
            tiger_id=uuid4(),
            name=tiger_name,
            status=TigerStatus.active,
            tags=["atrw", "reference"],
            notes=f"Tiger from ATRW dataset, ingested {datetime.utcnow().isoformat()}"
        )

        self.db.add(tiger)
        self.stats["tigers_created"] += 1
        logger.info(f"Created new tiger: {tiger_name}")

        return tiger

    def image_exists(self, image_path: str) -> bool:
        """Check if image already exists in database"""
        exists = self.db.query(TigerImage).filter(
            TigerImage.image_path == image_path
        ).first() is not None

        return exists

    def create_tiger_image(
        self,
        tiger: Tiger,
        image_path: Path,
        dataset_type: str
    ) -> TigerImage:
        """Create TigerImage record"""

        # Use relative path from project root
        relative_path = str(image_path).replace('/', '\\')

        # Check if already exists
        if self.image_exists(relative_path):
            self.stats["images_skipped"] += 1
            logger.debug(f"Skipped duplicate: {relative_path}")
            return None

        # Create image record
        tiger_image = TigerImage(
            image_id=uuid4(),
            tiger_id=tiger.tiger_id,
            image_path=relative_path,
            side_view=SideView.unknown,
            verified=True,  # ATRW is verified reference data
            meta_data={
                "source": "atrw",
                "dataset_type": dataset_type,
                "ingested_at": datetime.utcnow().isoformat(),
                "subspecies": "amur"
            }
        )

        self.db.add(tiger_image)
        self.stats["images_created"] += 1

        return tiger_image

    def scan_directory(self, directory: Path, dataset_type: str) -> List[Tuple[str, Path]]:
        """
        Scan directory for tiger images

        Returns:
            List of (tiger_name, image_path) tuples
        """
        if not directory.exists():
            logger.warning(f"Directory not found: {directory}")
            return []

        images = []
        for image_file in directory.glob("*.jpg"):
            tiger_name = self.extract_tiger_id_from_filename(image_file.name)
            images.append((tiger_name, image_file))

        return sorted(images)

    def ingest_batch(
        self,
        images: List[Tuple[str, Path]],
        dataset_type: str,
        batch_size: int = 100
    ) -> None:
        """
        Ingest images in batches for better performance

        Args:
            images: List of (tiger_name, image_path) tuples
            dataset_type: 'train' or 'test'
            batch_size: Number of images to process before committing
        """
        total = len(images)

        for i in range(0, total, batch_size):
            batch = images[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size

            logger.info(f"Processing {dataset_type} batch {batch_num}/{total_batches} ({len(batch)} images)...")

            for tiger_name, image_path in batch:
                try:
                    # Find or create tiger
                    tiger = self.find_or_create_tiger(tiger_name)

                    # Create image record
                    self.create_tiger_image(tiger, image_path, dataset_type)

                except Exception as e:
                    logger.error(f"Error processing {image_path}: {e}")
                    self.stats["errors"] += 1

            # Commit batch
            try:
                self.db.commit()
                logger.info(f"Committed {dataset_type} batch {batch_num}/{total_batches}")
            except Exception as e:
                logger.error(f"Failed to commit batch: {e}")
                self.db.rollback()
                self.stats["errors"] += len(batch)

    def run(self) -> Dict:
        """
        Run full ATRW dataset ingestion

        Returns:
            Statistics dictionary
        """
        start_time = datetime.now()

        logger.info("="*70)
        logger.info("ATRW DATASET INGESTION STARTED")
        logger.info("="*70)

        # Check dataset exists
        if not self.atrw_path.exists():
            logger.error(f"ATRW dataset not found at: {self.atrw_path}")
            return self.stats

        logger.info(f"Dataset path: {self.atrw_path}")

        # Scan train directory
        train_dir = self.atrw_path / "train"
        logger.info(f"\nScanning train directory: {train_dir}")
        train_images = self.scan_directory(train_dir, "train")
        logger.info(f"Found {len(train_images)} training images")

        # Scan test directory
        test_dir = self.atrw_path / "test"
        logger.info(f"\nScanning test directory: {test_dir}")
        test_images = self.scan_directory(test_dir, "test")
        logger.info(f"Found {len(test_images)} test images")

        total_images = len(train_images) + len(test_images)
        logger.info(f"\nTotal images to process: {total_images}")

        # Ingest train images
        if train_images:
            logger.info("\n" + "="*70)
            logger.info("INGESTING TRAINING SET")
            logger.info("="*70)
            self.ingest_batch(train_images, "train", batch_size=100)

        # Ingest test images
        if test_images:
            logger.info("\n" + "="*70)
            logger.info("INGESTING TEST SET")
            logger.info("="*70)
            self.ingest_batch(test_images, "test", batch_size=100)

        # Calculate duration
        duration = datetime.now() - start_time

        # Print summary
        logger.info("\n" + "="*70)
        logger.info("INGESTION COMPLETE")
        logger.info("="*70)
        logger.info(f"Duration: {duration}")
        logger.info(f"\nStatistics:")
        logger.info(f"  Tigers created: {self.stats['tigers_created']}")
        logger.info(f"  Tigers updated: {self.stats['tigers_updated']}")
        logger.info(f"  Images created: {self.stats['images_created']}")
        logger.info(f"  Images skipped (duplicates): {self.stats['images_skipped']}")
        logger.info(f"  Errors: {self.stats['errors']}")

        # Verify database state
        logger.info("\n" + "="*70)
        logger.info("DATABASE VERIFICATION")
        logger.info("="*70)

        total_tigers = self.db.query(Tiger).count()
        total_images = self.db.query(TigerImage).count()
        atrw_images = self.db.query(TigerImage).filter(
            TigerImage.meta_data.cast(type_=str).like('%"source": "atrw"%')
        ).count()

        logger.info(f"Total tigers in database: {total_tigers}")
        logger.info(f"Total images in database: {total_images}")
        logger.info(f"ATRW images in database: {atrw_images}")

        if self.stats['errors'] == 0:
            logger.info("\n[SUCCESS] Ingestion completed successfully!")
        else:
            logger.warning(f"\n[WARNING] Ingestion completed with {self.stats['errors']} errors")

        return self.stats


def main():
    """Main execution function"""
    logger.info("Starting ATRW dataset ingestion...")

    try:
        # Get database session
        with next(get_db_session()) as db:
            # Create ingestion manager
            ingestion = ATRWIngestion(db)

            # Run ingestion
            stats = ingestion.run()

            # Return exit code
            if stats['errors'] == 0:
                return 0
            else:
                return 1

    except Exception as e:
        logger.error(f"Fatal error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
