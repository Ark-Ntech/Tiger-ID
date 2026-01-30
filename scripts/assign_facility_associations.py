"""
Facility Association Script

Creates associations between tigers and reference facilities.
Links ATRW tigers to TPC facilities to enable database-driven location synthesis.

Assignment Strategies:
  1. Random: Evenly distribute tigers across all facilities
  2. Geographic: Distribute based on subspecies and regional logic
  3. Manual: Read from configuration file (for curated assignments)
"""

import sys
from pathlib import Path
from typing import List, Dict
import random
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import get_db_session
from backend.database.models import Tiger, Facility
from sqlalchemy.orm import Session
from sqlalchemy import func

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FacilityAssigner:
    """Manages tiger-facility associations"""

    # State-based regional groupings
    REGIONS = {
        "northeast": ["ME", "NH", "VT", "MA", "RI", "CT", "NY", "NJ", "PA"],
        "southeast": ["MD", "DE", "VA", "WV", "NC", "SC", "GA", "FL", "KY", "TN", "AL", "MS", "AR", "LA"],
        "midwest": ["OH", "IN", "IL", "MI", "WI", "MN", "IA", "MO", "ND", "SD", "NE", "KS"],
        "southwest": ["TX", "OK", "NM", "AZ"],
        "west": ["CO", "WY", "MT", "ID", "UT", "NV", "CA", "OR", "WA", "AK", "HI"]
    }

    def __init__(self, db_session: Session):
        self.db = db_session
        self.stats = {
            "tigers_assigned": 0,
            "tigers_skipped": 0,
            "facilities_used": 0,
            "errors": 0
        }

    def get_unassigned_tigers(self) -> List[Tiger]:
        """Get all tigers without facility assignments"""
        return self.db.query(Tiger).filter(
            Tiger.origin_facility_id == None
        ).all()

    def get_facilities_by_region(self, region: str) -> List[Facility]:
        """Get facilities in a specific region"""
        states = self.REGIONS.get(region, [])
        return self.db.query(Facility).filter(
            Facility.state.in_(states)
        ).all()

    def get_all_facilities(self) -> List[Facility]:
        """Get all facilities"""
        return self.db.query(Facility).all()

    def assign_random(self, tigers: List[Tiger], facilities: List[Facility]) -> None:
        """
        Strategy 1: Random Assignment
        Evenly distribute tigers across all facilities
        """
        logger.info("\n" + "="*70)
        logger.info("RANDOM ASSIGNMENT STRATEGY")
        logger.info("="*70)

        if not facilities:
            logger.error("No facilities available for assignment")
            return

        logger.info(f"Assigning {len(tigers)} tigers to {len(facilities)} facilities...")

        # Track facility usage
        facility_usage = {f.facility_id: 0 for f in facilities}

        for i, tiger in enumerate(tigers):
            try:
                # Select random facility
                facility = random.choice(facilities)

                # Assign
                tiger.origin_facility_id = facility.facility_id
                tiger.last_seen_location = f"{facility.city or facility.state}, {facility.state}"
                facility_usage[facility.facility_id] += 1

                self.stats["tigers_assigned"] += 1

                if (i + 1) % 100 == 0:
                    logger.info(f"Assigned {i + 1}/{len(tigers)} tigers...")

            except Exception as e:
                logger.error(f"Error assigning tiger {tiger.name}: {e}")
                self.stats["errors"] += 1

        # Commit
        try:
            self.db.commit()
            logger.info(f"Committed {self.stats['tigers_assigned']} tiger assignments")
        except Exception as e:
            logger.error(f"Failed to commit: {e}")
            self.db.rollback()
            return

        # Report facility usage
        self.stats["facilities_used"] = len([count for count in facility_usage.values() if count > 0])

        logger.info("\nFacility Usage Distribution:")
        logger.info(f"  Facilities used: {self.stats['facilities_used']}/{len(facilities)}")
        logger.info(f"  Average tigers per facility: {sum(facility_usage.values()) / len(facilities):.1f}")
        logger.info(f"  Max tigers in one facility: {max(facility_usage.values())}")
        logger.info(f"  Min tigers in one facility: {min(facility_usage.values())}")

    def assign_geographic(self, tigers: List[Tiger], facilities: List[Facility]) -> None:
        """
        Strategy 2: Geographic Distribution
        Distribute tigers based on subspecies and regional logic

        Logic:
        - Amur tigers (ATRW dataset) are Siberian, native to cold climates
        - Distribute to northern states (northeast, midwest, west mountain states)
        - Avoid hot southern states
        """
        logger.info("\n" + "="*70)
        logger.info("GEOGRAPHIC ASSIGNMENT STRATEGY")
        logger.info("="*70)

        # ATRW dataset is all Amur tigers (Siberian subspecies)
        # Prefer colder regions
        preferred_regions = ["northeast", "midwest", "west"]

        # Get facilities in preferred regions
        preferred_facilities = []
        for region in preferred_regions:
            preferred_facilities.extend(self.get_facilities_by_region(region))

        if not preferred_facilities:
            logger.warning("No facilities in preferred regions, using all facilities")
            preferred_facilities = facilities

        logger.info(f"Assigning {len(tigers)} Amur tigers to {len(preferred_facilities)} facilities in cold climates...")
        logger.info(f"Preferred regions: {', '.join(preferred_regions)}")

        # Track facility usage
        facility_usage = {f.facility_id: 0 for f in preferred_facilities}

        for i, tiger in enumerate(tigers):
            try:
                # Select random facility from preferred regions
                facility = random.choice(preferred_facilities)

                # Assign
                tiger.origin_facility_id = facility.facility_id
                tiger.last_seen_location = f"{facility.city or facility.state}, {facility.state}"

                # Add subspecies tag
                if tiger.tags:
                    if "amur" not in tiger.tags:
                        tiger.tags.append("amur")
                else:
                    tiger.tags = ["amur", "siberian"]

                facility_usage[facility.facility_id] += 1
                self.stats["tigers_assigned"] += 1

                if (i + 1) % 100 == 0:
                    logger.info(f"Assigned {i + 1}/{len(tigers)} tigers...")

            except Exception as e:
                logger.error(f"Error assigning tiger {tiger.name}: {e}")
                self.stats["errors"] += 1

        # Commit
        try:
            self.db.commit()
            logger.info(f"Committed {self.stats['tigers_assigned']} tiger assignments")
        except Exception as e:
            logger.error(f"Failed to commit: {e}")
            self.db.rollback()
            return

        # Report facility usage
        self.stats["facilities_used"] = len([count for count in facility_usage.values() if count > 0])

        logger.info("\nFacility Usage Distribution:")
        logger.info(f"  Facilities used: {self.stats['facilities_used']}/{len(preferred_facilities)}")
        logger.info(f"  Average tigers per facility: {sum(facility_usage.values()) / len(preferred_facilities):.1f}")

        # Show regional distribution
        regional_counts = {}
        for region in preferred_regions:
            region_facilities = self.get_facilities_by_region(region)
            region_tiger_count = sum(
                facility_usage.get(f.facility_id, 0) for f in region_facilities
            )
            regional_counts[region] = region_tiger_count

        logger.info("\nRegional Distribution:")
        for region, count in regional_counts.items():
            logger.info(f"  {region}: {count} tigers")

    def run(self, strategy: str = "geographic") -> Dict:
        """
        Run facility assignment with specified strategy

        Args:
            strategy: 'random' or 'geographic'

        Returns:
            Statistics dictionary
        """
        start_time = datetime.now()

        logger.info("="*70)
        logger.info("FACILITY ASSOCIATION SCRIPT")
        logger.info("="*70)
        logger.info(f"Strategy: {strategy}")

        # Get unassigned tigers
        tigers = self.get_unassigned_tigers()
        logger.info(f"\nUnassigned tigers: {len(tigers)}")

        if len(tigers) == 0:
            logger.info("[INFO] All tigers already have facility assignments")
            return self.stats

        # Get facilities
        facilities = self.get_all_facilities()
        logger.info(f"Available facilities: {len(facilities)}")

        if len(facilities) == 0:
            logger.error("[ERROR] No facilities found in database")
            return self.stats

        # Execute strategy
        if strategy == "random":
            self.assign_random(tigers, facilities)
        elif strategy == "geographic":
            self.assign_geographic(tigers, facilities)
        else:
            logger.error(f"Unknown strategy: {strategy}")
            return self.stats

        # Calculate duration
        duration = datetime.now() - start_time

        # Print summary
        logger.info("\n" + "="*70)
        logger.info("ASSIGNMENT COMPLETE")
        logger.info("="*70)
        logger.info(f"Duration: {duration}")
        logger.info(f"\nStatistics:")
        logger.info(f"  Tigers assigned: {self.stats['tigers_assigned']}")
        logger.info(f"  Tigers skipped: {self.stats['tigers_skipped']}")
        logger.info(f"  Facilities used: {self.stats['facilities_used']}/{len(facilities)}")
        logger.info(f"  Errors: {self.stats['errors']}")

        # Verify
        logger.info("\n" + "="*70)
        logger.info("DATABASE VERIFICATION")
        logger.info("="*70)

        total_tigers = self.db.query(Tiger).count()
        assigned_tigers = self.db.query(Tiger).filter(
            Tiger.origin_facility_id != None
        ).count()

        logger.info(f"Total tigers: {total_tigers}")
        logger.info(f"Assigned tigers: {assigned_tigers}")
        logger.info(f"Unassigned tigers: {total_tigers - assigned_tigers}")

        if self.stats['errors'] == 0:
            logger.info("\n[SUCCESS] Assignment completed successfully!")
        else:
            logger.warning(f"\n[WARNING] Assignment completed with {self.stats['errors']} errors")

        return self.stats


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="Assign tigers to facilities")
    parser.add_argument(
        "--strategy",
        choices=["random", "geographic"],
        default="geographic",
        help="Assignment strategy (default: geographic)"
    )

    args = parser.parse_args()

    logger.info(f"Starting facility assignment with strategy: {args.strategy}")

    try:
        # Get database session
        with next(get_db_session()) as db:
            # Create assigner
            assigner = FacilityAssigner(db)

            # Run assignment
            stats = assigner.run(strategy=args.strategy)

            # Return exit code
            if stats['errors'] == 0:
                return 0
            else:
                return 1

    except Exception as e:
        logger.error(f"Fatal error during assignment: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
