"""
Auto-Discovery Service

Automatically discovers and creates tiger and facility records during investigations.
Powers the investigation-driven database growth strategy.

When Gemini finds "Tiger at XYZ Facility" in web intelligence:
  1. Check if facility exists (fuzzy matching)
  2. Create facility if new (with geocoding)
  3. Create tiger record linked to facility
  4. Store stripe embedding for future matching
  5. Return discovery metadata for reporting

This enables the database to grow organically with each investigation.
"""

import logging
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from difflib import SequenceMatcher

from backend.database.models import Tiger, TigerImage, Facility, TigerStatus, SideView
from backend.services.geocoding_service import GeocodingService
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class AutoDiscoveryService:
    """Manages automatic discovery of tigers and facilities during investigations"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.geocoding_service = GeocodingService()

    def extract_facility_info(self, web_intelligence: Dict) -> List[Dict]:
        """
        Extract facility information from Gemini web intelligence

        Args:
            web_intelligence: Gemini search results with citations

        Returns:
            List of facility info dicts with name, location, confidence
        """
        facilities = []

        # Extract from citations
        for citation in web_intelligence.get("citations", []):
            snippet = citation.get("snippet", "")
            title = citation.get("title", "")

            # Look for facility mentions
            facility_info = self._parse_facility_from_text(snippet + " " + title)
            if facility_info:
                facility_info["source"] = citation.get("uri")
                facility_info["confidence"] = citation.get("relevance_score", 0.5)
                facilities.append(facility_info)

        # Extract from summary
        summary = web_intelligence.get("summary", "")
        if summary:
            summary_facilities = self._parse_facility_from_text(summary)
            if summary_facilities:
                summary_facilities["source"] = "gemini_summary"
                summary_facilities["confidence"] = 0.8
                facilities.append(summary_facilities)

        # Deduplicate facilities
        unique_facilities = self._deduplicate_facilities(facilities)

        logger.info(f"Extracted {len(unique_facilities)} unique facilities from web intelligence")
        return unique_facilities

    def _parse_facility_from_text(self, text: str) -> Optional[Dict]:
        """
        Parse facility name and location from text

        Looks for patterns like:
        - "XYZ Zoo, Dallas, Texas"
        - "ABC Wildlife Sanctuary in Austin, TX"
        - "Tiger facility in Miami, Florida"
        """
        import re

        # Common facility keywords
        facility_keywords = [
            "zoo", "sanctuary", "park", "facility", "center", "refuge",
            "preserve", "rescue", "foundation", "reserve"
        ]

        # Look for facility patterns
        for keyword in facility_keywords:
            # Pattern: "Name {keyword} in City, State"
            pattern = rf'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+{keyword}\s+in\s+([A-Z][a-z]+),\s*([A-Z]{{2}}|[A-Z][a-z]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {
                    "name": f"{match.group(1)} {keyword.title()}",
                    "city": match.group(2),
                    "state": match.group(3)
                }

            # Pattern: "Name {keyword}, City, State"
            pattern = rf'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+{keyword},\s*([A-Z][a-z]+),\s*([A-Z]{{2}}|[A-Z][a-z]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {
                    "name": f"{match.group(1)} {keyword.title()}",
                    "city": match.group(2),
                    "state": match.group(3)
                }

        return None

    def _deduplicate_facilities(self, facilities: List[Dict]) -> List[Dict]:
        """Remove duplicate facilities using name similarity"""
        if not facilities:
            return []

        unique = []
        for facility in facilities:
            is_duplicate = False
            for existing in unique:
                similarity = SequenceMatcher(
                    None,
                    facility.get("name", "").lower(),
                    existing.get("name", "").lower()
                ).ratio()

                if similarity > 0.8:  # 80% similar = duplicate
                    is_duplicate = True
                    # Keep the one with higher confidence
                    if facility.get("confidence", 0) > existing.get("confidence", 0):
                        unique.remove(existing)
                        unique.append(facility)
                    break

            if not is_duplicate:
                unique.append(facility)

        return unique

    async def find_or_create_facility(
        self,
        facility_info: Dict,
        investigation_id: UUID
    ) -> Tuple[Facility, bool]:
        """
        Find existing facility or create new one

        Args:
            facility_info: Dict with name, city, state
            investigation_id: Investigation that discovered this facility

        Returns:
            (Facility, is_new) tuple
        """
        name = facility_info.get("name")
        city = facility_info.get("city")
        state = facility_info.get("state")

        # Try exact match first
        existing = self.db.query(Facility).filter(
            Facility.exhibitor_name == name
        ).first()

        if existing:
            logger.info(f"Found existing facility: {name}")
            return (existing, False)

        # Try fuzzy match
        all_facilities = self.db.query(Facility).filter(
            Facility.state == state
        ).all()

        for facility in all_facilities:
            similarity = SequenceMatcher(
                None,
                name.lower(),
                facility.exhibitor_name.lower()
            ).ratio()

            if similarity > 0.85:
                logger.info(f"Found similar facility: {facility.exhibitor_name} (similarity: {similarity:.2f})")
                return (facility, False)

        # Create new facility
        logger.info(f"Creating new facility: {name}")

        facility = Facility(
            facility_id=uuid4(),
            exhibitor_name=name,
            city=city,
            state=state,
            data_source="investigation_auto_discovery",
            is_reference_facility=False,  # Real discovered facility
            discovered_at=datetime.utcnow(),
            discovered_by_investigation_id=investigation_id
        )

        # Geocode facility
        try:
            coords = await self.geocoding_service.geocode_facility(facility)
            if coords:
                import json
                facility.coordinates = json.dumps(coords)
                logger.info(f"Geocoded facility: {coords.get('latitude')}, {coords.get('longitude')}")
        except Exception as e:
            logger.warning(f"Failed to geocode facility: {e}")

        self.db.add(facility)
        self.db.commit()

        logger.info(f"[NEW FACILITY] Created: {name} in {city}, {state}")
        return (facility, True)

    def create_discovered_tiger(
        self,
        image_bytes: bytes,
        stripe_embedding: Optional[bytes],
        facility: Facility,
        investigation_id: UUID,
        confidence: float,
        bounding_box: Optional[Dict] = None
    ) -> Tuple[Tiger, TigerImage]:
        """
        Create a newly discovered tiger record

        Args:
            image_bytes: Uploaded tiger image
            stripe_embedding: Stripe pattern embedding from ReID model
            facility: Facility where tiger was discovered
            investigation_id: Investigation that discovered this tiger
            confidence: Gemini confidence in discovery
            bounding_box: Optional bounding box from MegaDetector

        Returns:
            (Tiger, TigerImage) tuple
        """
        # Generate tiger name
        tiger_name = f"Tiger discovered {datetime.utcnow().strftime('%Y-%m-%d')} at {facility.exhibitor_name}"

        # Create tiger record
        tiger = Tiger(
            tiger_id=uuid4(),
            name=tiger_name,
            origin_facility_id=facility.facility_id,
            last_seen_location=f"{facility.city}, {facility.state}" if facility.city else facility.state,
            last_seen_date=datetime.utcnow(),
            status=TigerStatus.active,
            is_reference=False,  # This is a real tiger
            discovered_at=datetime.utcnow(),
            discovered_by_investigation_id=investigation_id,
            discovery_confidence=confidence,
            tags=["discovered", "auto_identified"],
            notes=f"Discovered through Investigation {investigation_id} via Gemini web intelligence"
        )

        self.db.add(tiger)
        self.db.flush()  # Get tiger_id

        # Create tiger image record
        # Save image to storage (in production, use S3 or local storage)
        image_path = f"data/storage/investigations/{investigation_id}/discovered_tiger_{tiger.tiger_id}.jpg"

        tiger_image = TigerImage(
            image_id=uuid4(),
            tiger_id=tiger.tiger_id,
            image_path=image_path,
            embedding=stripe_embedding,
            side_view=SideView.unknown,
            verified=False,  # Requires human verification
            is_reference=False,  # Real tiger image
            discovered_by_investigation_id=investigation_id,
            meta_data={
                "source": "investigation_discovery",
                "investigation_id": str(investigation_id),
                "facility": facility.exhibitor_name,
                "discovered_at": datetime.utcnow().isoformat(),
                "confidence": confidence,
                "bounding_box": bounding_box
            }
        )

        self.db.add(tiger_image)
        self.db.commit()

        logger.info(f"[NEW TIGER] Discovered: {tiger_name} at {facility.exhibitor_name}")
        return (tiger, tiger_image)

    def should_create_new_tiger(
        self,
        existing_matches: Any,
        min_similarity: float = 0.90
    ) -> bool:
        """
        Determine if we should create a new tiger record

        Args:
            existing_matches: List of matches or dict with model names as keys
            min_similarity: Minimum similarity to consider a match

        Returns:
            True if no strong matches found (new discovery)
        """
        if not existing_matches:
            return True

        # Handle case where matches is a dict with model names as keys
        all_matches = []
        if isinstance(existing_matches, dict):
            for model_matches in existing_matches.values():
                if isinstance(model_matches, list):
                    all_matches.extend(model_matches)
        elif isinstance(existing_matches, list):
            all_matches = existing_matches
        else:
            return True  # Unknown format, create new tiger

        if not all_matches:
            return True

        # Check best match
        best_match = max(all_matches, key=lambda x: x.get("similarity", 0) if isinstance(x, dict) else 0)
        best_similarity = best_match.get("similarity", 0) if isinstance(best_match, dict) else 0

        if best_similarity < min_similarity:
            logger.info(f"Best match similarity {best_similarity:.2f} < threshold {min_similarity}, creating new tiger")
            return True

        logger.info(f"Found strong match (similarity: {best_similarity:.2f}), not creating new tiger")
        return False

    async def process_investigation_discovery(
        self,
        investigation_id: UUID,
        uploaded_image: bytes,
        stripe_embeddings: Dict,
        existing_matches: Any,
        web_intelligence: Dict,
        context: Any
    ) -> Optional[Dict]:
        """
        Main orchestration function for auto-discovery

        Called from Investigation 2.0 workflow complete_node.
        Analyzes investigation results and creates records if needed.

        Args:
            investigation_id: Current investigation ID
            uploaded_image: User-uploaded image
            stripe_embeddings: ReID model embeddings
            existing_matches: Matches found against database (list or dict)
            web_intelligence: Gemini search results
            context: User-provided context (dict or string)

        Returns:
            Discovery metadata if new records created, None otherwise
        """
        logger.info(f"Processing auto-discovery for investigation {investigation_id}")

        # Check if we should create new tiger
        if not self.should_create_new_tiger(existing_matches):
            logger.info("Strong existing match found, skipping auto-discovery")
            return None

        # Extract facilities from web intelligence
        discovered_facilities = self.extract_facility_info(web_intelligence)

        if not discovered_facilities:
            logger.info("No facilities found in web intelligence, skipping auto-discovery")
            return None

        # Use top facility
        top_facility_info = discovered_facilities[0]
        logger.info(f"Top facility: {top_facility_info.get('name')} (confidence: {top_facility_info.get('confidence')})")

        # Find or create facility
        facility, is_new_facility = await self.find_or_create_facility(
            top_facility_info,
            investigation_id
        )

        # Create tiger record
        tiger, tiger_image = self.create_discovered_tiger(
            image_bytes=uploaded_image,
            stripe_embedding=stripe_embeddings.get("tiger_reid"),  # Use primary ReID model
            facility=facility,
            investigation_id=investigation_id,
            confidence=top_facility_info.get("confidence", 0.7)
        )

        # Build discovery metadata
        discovery = {
            "tiger_id": str(tiger.tiger_id),
            "tiger_name": tiger.name,
            "facility_id": str(facility.facility_id),
            "facility_name": facility.exhibitor_name,
            "location": f"{facility.city}, {facility.state}" if facility.city else facility.state,
            "coordinates": facility.coordinates,
            "is_new_facility": is_new_facility,
            "confidence": tiger.discovery_confidence,
            "discovered_at": tiger.discovered_at.isoformat()
        }

        logger.info(f"[AUTO-DISCOVERY SUCCESS] New tiger added to database: {tiger.name}")
        return discovery
