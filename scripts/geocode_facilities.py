"""Script to batch geocode all facilities in the database"""

import asyncio
import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Force SQLite database
os.environ['DATABASE_URL'] = 'sqlite:///data/production.db'

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import get_db_session
from backend.services.geocoding_service import GeocodingService
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to geocode all facilities"""
    logger.info("Starting facility geocoding batch process")

    # Create geocoding service
    geocoding_service = GeocodingService()

    # Get database session
    try:
        with get_db_session() as session:
            # Run batch geocoding
            stats = await geocoding_service.batch_geocode_facilities(session)

            # Print results
            logger.info("=" * 60)
            logger.info("Batch Geocoding Complete")
            logger.info("=" * 60)
            logger.info(f"Successfully geocoded: {stats['success']} facilities")
            logger.info(f"Failed to geocode: {stats['failed']} facilities")
            logger.info(f"Skipped (already geocoded): {stats['skipped']} facilities")
            logger.info(f"Total facilities: {stats['success'] + stats['failed'] + stats['skipped']}")
            logger.info("=" * 60)

            if stats['failed'] > 0:
                logger.warning(
                    f"{stats['failed']} facilities could not be geocoded. "
                    "Check logs for details."
                )

            return stats

    except Exception as e:
        logger.error(f"Error during batch geocoding: {e}")
        raise


if __name__ == "__main__":
    try:
        stats = asyncio.run(main())
        sys.exit(0 if stats['failed'] == 0 else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
