"""
ATRW Reference Data Ingestion (CORRECTED)

Ingests ATRW dataset as REFERENCE DATA ONLY for stripe pattern matching.
Does NOT create facility associations - these tigers are not real tigers at real locations.

Purpose:
  - Provide 5,156 stripe patterns for ReID matching algorithms
  - Serve as "fingerprint database" for comparing uploaded images
  - NOT to populate real tiger database

Key Differences from Previous Approach:
  - is_reference=True flag on all records
  - NO origin_facility_id assignments
  - NO fake tiger discoveries
  - Just embeddings for matching

Dataset structure:
  data/models/atrw/images/Amur Tigers/
    ├── train/  (3,392 images)
    └── test/   (1,764 images)
"""

import sys
import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import logging

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Force SQLite database
os.environ['DATABASE_URL'] = 'sqlite:///data/production.db'

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import get_db_session
from backend.database.models import Tiger, TigerImage, TigerStatus, SideView
from sqlalchemy.orm import Session
from uuid import uuid4

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ATRWReferenceIngestion:
    """ATRW reference data ingestion manager"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.atrw_path = Path("data/models/atrw/images/Amur Tigers")
        self.stats = {
            "reference_tigers_created": 0,
            "reference_images_created": 0,
            "images_skipped": 0,
            "errors": 0
        }

    def extract_tiger_id_from_filename(self, filename: str) -> str:
        """Extract tiger ID from ATRW filename"""
        base_name = Path(filename).stem
        return f"ATRW_REF_{base_name}"  # Mark as reference with prefix

    def find_or_create_reference_tiger(self, tiger_name: str) -> Tiger:
        """Find existing reference tiger or create new one"""

        # Check if tiger exists
        tiger = self.db.query(Tiger).filter(Tiger.name == tiger_name).first()

        if tiger:
            return tiger

        # Create new reference tiger
        tiger = Tiger(
            tiger_id=uuid4(),
            name=tiger_name,
            status=TigerStatus.active,
            is_reference=True,  # CRITICAL: This is reference data
            origin_facility_id=None,  # NO facility assignment
            tags=["atrw", "reference"],
            notes="ATRW reference data - not a real tiger, used for stripe pattern matching only"
        )

        self.db.add(tiger)
        self.stats["reference_tigers_created"] += 1
        logger.debug(f"Created reference tiger: {tiger_name}")

        return tiger

    def image_exists(self, image_path: str) -> bool:
        """Check if image already exists in database"""
        return self.db.query(TigerImage).filter(
            TigerImage.image_path == image_path
        ).first() is not None

    def create_reference_image(
        self,
        tiger: Tiger,
        image_path: Path,
        dataset_type: str
    ) -> TigerImage:
        """Create TigerImage record marked as reference"""

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
            verified=True,
            is_reference=True,  # CRITICAL: This is reference data
            meta_data={
                "source": "atrw",
                "dataset_type": dataset_type,
                "ingested_at": datetime.utcnow().isoformat(),
                "subspecies": "amur",
                "purpose": "reference_matching"  # Explicit purpose
            }
        )

        self.db.add(tiger_image)
        self.stats["reference_images_created"] += 1

        return tiger_image

    def scan_directory(self, directory: Path, dataset_type: str) -> List[tuple]:
        """Scan directory for tiger images"""
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
        images: List[tuple],
        dataset_type: str,
        batch_size: int = 100
    ) -> None:
        """Ingest images in batches"""
        total = len(images)

        for i in range(0, total, batch_size):
            batch = images[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size

            logger.info(f"Processing {dataset_type} batch {batch_num}/{total_batches} ({len(batch)} images)...")

            for tiger_name, image_path in batch:
                try:
                    # Find or create reference tiger
                    tiger = self.find_or_create_reference_tiger(tiger_name)

                    # Create reference image record
                    self.create_reference_image(tiger, image_path, dataset_type)

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
        """Run ATRW reference data ingestion"""
        start_time = datetime.now()

        logger.info("="*70)
        logger.info("ATRW REFERENCE DATA INGESTION")
        logger.info("="*70)
        logger.info("IMPORTANT: Ingesting as REFERENCE DATA ONLY")
        logger.info("  - NOT real tigers at real facilities")
        logger.info("  - Used for stripe pattern matching algorithms")
        logger.info("  - is_reference=True flag set on all records")
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
        logger.info(f"\nTotal reference images to process: {total_images}")

        # Ingest train images
        if train_images:
            logger.info("\n" + "="*70)
            logger.info("INGESTING TRAINING SET (REFERENCE DATA)")
            logger.info("="*70)
            self.ingest_batch(train_images, "train", batch_size=100)

        # Ingest test images
        if test_images:
            logger.info("\n" + "="*70)
            logger.info("INGESTING TEST SET (REFERENCE DATA)")
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
        logger.info(f"  Reference tigers created: {self.stats['reference_tigers_created']}")
        logger.info(f"  Reference images created: {self.stats['reference_images_created']}")
        logger.info(f"  Images skipped (duplicates): {self.stats['images_skipped']}")
        logger.info(f"  Errors: {self.stats['errors']}")

        # Verify database state
        logger.info("\n" + "="*70)
        logger.info("DATABASE VERIFICATION")
        logger.info("="*70)

        total_tigers = self.db.query(Tiger).count()
        reference_tigers = self.db.query(Tiger).filter(Tiger.is_reference == True).count()
        real_tigers = self.db.query(Tiger).filter(Tiger.is_reference == False).count()

        total_images = self.db.query(TigerImage).count()
        reference_images = self.db.query(TigerImage).filter(TigerImage.is_reference == True).count()
        real_images = self.db.query(TigerImage).filter(TigerImage.is_reference == False).count()

        logger.info(f"Total tigers: {total_tigers}")
        logger.info(f"  - Reference (ATRW): {reference_tigers}")
        logger.info(f"  - Real (discovered): {real_tigers}")
        logger.info(f"\nTotal images: {total_images}")
        logger.info(f"  - Reference (ATRW): {reference_images}")
        logger.info(f"  - Real (discovered): {real_images}")

        logger.info("\n" + "="*70)
        logger.info("IMPORTANT NOTES")
        logger.info("="*70)
        logger.info("1. Reference data ingested successfully")
        logger.info("2. NO facility associations created (correct)")
        logger.info("3. Real tiger database will grow through investigations")
        logger.info("4. Use Investigation 2.0 to discover and add real tigers")
        logger.info("="*70)

        if self.stats['errors'] == 0:
            logger.info("\n[SUCCESS] Reference data ingestion completed successfully!")
        else:
            logger.warning(f"\n[WARNING] Ingestion completed with {self.stats['errors']} errors")

        return self.stats


def main():
    """Main execution function"""
    logger.info("Starting ATRW reference data ingestion...")

    try:
        # Get database session
        with get_db_session() as db:
            # Create ingestion manager
            ingestion = ATRWReferenceIngestion(db)

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
