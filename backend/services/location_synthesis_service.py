"""Location synthesis service for combining location data from multiple sources"""

import logging
from typing import Dict, Optional, List, Any
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)


class LocationSynthesisService:
    """Service for synthesizing tiger location from multiple data sources"""

    def __init__(self):
        """Initialize location synthesis service"""
        self.cache = {}

    def synthesize_tiger_location(
        self,
        user_context: Optional[Dict] = None,
        web_intelligence: Optional[Dict] = None,
        database_matches: Optional[List[Dict]] = None,
        image_exif: Optional[Dict] = None
    ) -> Dict:
        """
        Combine all location sources into hierarchical structure

        Args:
            user_context: User-provided context (location, date, notes)
            web_intelligence: Web search results with citations
            database_matches: ReID model matches from database
            image_exif: EXIF metadata from uploaded image

        Returns:
            Hierarchical location structure with confidence scores
        """
        logger.info("Starting location synthesis from multiple sources")

        sources = []
        all_locations = []

        # 1. Extract location from EXIF GPS data (highest confidence)
        if image_exif and image_exif.get("gps"):
            gps = image_exif["gps"]
            location = {
                "type": "exif",
                "confidence": "high",
                "coordinates": {
                    "lat": gps.get("latitude"),
                    "lon": gps.get("longitude")
                },
                "source": "Image EXIF GPS data",
                "extracted_at": gps.get("extracted_at")
            }
            if gps.get("altitude"):
                location["altitude"] = gps["altitude"]

            sources.append(location)
            all_locations.append(location)
            logger.info(f"Added EXIF GPS location: {location['coordinates']}")

        # 2. Extract location from user context
        if user_context:
            try:
                user_location = self._extract_location_from_context(user_context)
                if user_location:
                    sources.append(user_location)
                    all_locations.append(user_location)
                    logger.info(f"Added user context location: {user_location.get('city', user_location.get('state', 'unknown'))}")
            except Exception as e:
                logger.warning(f"Failed to extract location from user context: {e}")

        # 3. Extract locations from database matches (tiger sightings)
        if database_matches:
            try:
                db_locations = self._extract_locations_from_matches(database_matches)
                sources.extend(db_locations)
                all_locations.extend(db_locations)
                logger.info(f"Added {len(db_locations)} locations from database matches")
            except Exception as e:
                logger.warning(f"Failed to extract locations from database matches: {e}")

        # 4. Extract locations from web intelligence
        if web_intelligence and isinstance(web_intelligence, dict):
            try:
                web_locations = self._extract_locations_from_web_intelligence(web_intelligence)
                sources.extend(web_locations)
                all_locations.extend(web_locations)
                logger.info(f"Added {len(web_locations)} locations from web intelligence")
            except Exception as e:
                logger.warning(f"Failed to extract locations from web intelligence: {e}")

        # Determine primary location
        primary_location = self._determine_primary_location(sources)

        # Identify alternative locations
        alternative_locations = [
            loc for loc in all_locations
            if loc != primary_location
        ]

        result = {
            "primary_location": primary_location,
            "sources": sources,
            "alternative_locations": alternative_locations,
            "total_sources": len(sources),
            "synthesis_timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"Location synthesis complete: {len(sources)} sources, primary location confidence: {primary_location.get('confidence', 'unknown')}")
        return result

    def _extract_location_from_context(self, context: Any) -> Optional[Dict]:
        """Extract location from user-provided context"""
        # Handle case where context is a string instead of dict
        if isinstance(context, str):
            location_text = context
        elif isinstance(context, dict):
            location_text = context.get("location", "")
        else:
            return None

        if not location_text:
            return None

        # Parse location text (could be city, state, facility name, etc.)
        location = {
            "type": "user_context",
            "confidence": "medium",
            "raw_text": location_text,
            "source": "User-provided context"
        }

        # Try to extract structured location components
        # Simple parsing - look for state abbreviations
        state_pattern = r'\b([A-Z]{2})\b'
        state_match = re.search(state_pattern, location_text)
        if state_match:
            location["state"] = state_match.group(1)

        # Extract city names (simple heuristic)
        # Look for capitalized words before state
        if "state" in location:
            city_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,?\s*' + location["state"]
            city_match = re.search(city_pattern, location_text)
            if city_match:
                location["city"] = city_match.group(1)

        # If no structured data extracted, store as region
        if "state" not in location and "city" not in location:
            location["region"] = location_text

        return location

    def _extract_locations_from_matches(self, matches: Any) -> List[Dict]:
        """Extract locations from database matches (tiger facilities)"""
        locations = []

        # Handle case where matches is a dict with model names as keys
        if isinstance(matches, dict):
            # Flatten dict of lists into single list
            all_matches = []
            for model_matches in matches.values():
                if isinstance(model_matches, list):
                    all_matches.extend(model_matches)
            matches = all_matches
        elif not isinstance(matches, list):
            return []

        for match in matches:
            facility = match.get("facility")
            if not facility:
                continue

            location = {
                "type": "database_match",
                "confidence": "high",  # Database records are reliable
                "facility": facility.get("name") or facility.get("exhibitor_name"),
                "source": f"Database match (similarity: {match.get('similarity', 0):.2f})",
                "tiger_id": match.get("tiger_id"),
                "match_similarity": match.get("similarity")
            }

            # Add structured location data
            if facility.get("city"):
                location["city"] = facility["city"]
            if facility.get("state"):
                location["state"] = facility["state"]
            if facility.get("address"):
                location["address"] = facility["address"]

            # Add coordinates if available
            if facility.get("coordinates"):
                try:
                    coords = json.loads(facility["coordinates"]) if isinstance(facility["coordinates"], str) else facility["coordinates"]
                    location["coordinates"] = {
                        "lat": coords.get("latitude"),
                        "lon": coords.get("longitude")
                    }
                except:
                    pass

            locations.append(location)

        return locations

    def _extract_locations_from_web_intelligence(self, web_intel: Dict) -> List[Dict]:
        """Extract locations mentioned in web intelligence citations"""
        locations = []

        citations = web_intel.get("citations", [])
        summary = web_intel.get("summary", "")

        # Extract location mentions from summary
        location_mentions = self._find_location_mentions(summary)

        for mention in location_mentions:
            location = {
                "type": "web_intelligence",
                "confidence": "low",  # Web mentions are less reliable
                "source": "Web intelligence summary",
                "mention": mention,
                "found_in": "summary"
            }
            locations.append(location)

        # Extract locations from citation snippets
        for citation in citations:
            snippet = citation.get("snippet", "")
            title = citation.get("title", "")

            citation_locations = self._find_location_mentions(snippet + " " + title)

            for mention in citation_locations:
                location = {
                    "type": "web_intelligence",
                    "confidence": "low",
                    "source": f"Web citation: {citation.get('title', 'Unknown')}",
                    "citation_uri": citation.get("uri"),
                    "mention": mention,
                    "found_in": "citation"
                }
                locations.append(location)

        # Deduplicate locations
        unique_locations = []
        seen_mentions = set()
        for loc in locations:
            mention = loc.get("mention", "")
            if mention and mention not in seen_mentions:
                unique_locations.append(loc)
                seen_mentions.add(mention)

        return unique_locations

    def _find_location_mentions(self, text: str) -> List[str]:
        """Find location mentions in text using simple patterns"""
        if not text:
            return []

        mentions = []

        # US States (full names and abbreviations)
        us_states = [
            "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
            "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
            "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
            "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
            "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
            "New Hampshire", "New Jersey", "New Mexico", "New York",
            "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
            "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
            "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
            "West Virginia", "Wisconsin", "Wyoming"
        ]

        # Look for state mentions
        for state in us_states:
            if state.lower() in text.lower():
                mentions.append(state)

        # Look for common location patterns
        # Pattern: City, State
        city_state_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2}|[A-Z][a-z]+)'
        city_state_matches = re.findall(city_state_pattern, text)
        for city, state in city_state_matches:
            mentions.append(f"{city}, {state}")

        # Look for facilities/zoos
        facility_keywords = ["zoo", "sanctuary", "facility", "park", "center", "reserve"]
        for keyword in facility_keywords:
            pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+' + keyword + r')'
            matches = re.findall(pattern, text, re.IGNORECASE)
            mentions.extend(matches)

        return list(set(mentions))  # Deduplicate

    def _determine_primary_location(self, sources: List[Dict]) -> Dict:
        """
        Determine the primary (most likely) location from all sources

        Priority order:
        1. EXIF GPS (highest confidence)
        2. Database match with high similarity
        3. User context
        4. Web intelligence
        """
        if not sources:
            return {
                "type": "unknown",
                "confidence": "none",
                "source": "No location sources available"
            }

        # Sort by confidence and type priority
        confidence_scores = {
            "high": 3,
            "medium": 2,
            "low": 1,
            "none": 0
        }

        type_priority = {
            "exif": 10,
            "database_match": 8,
            "user_context": 5,
            "web_intelligence": 2
        }

        def score_location(loc: Dict) -> float:
            conf_score = confidence_scores.get(loc.get("confidence", "none"), 0)
            type_score = type_priority.get(loc.get("type", "unknown"), 0)

            # Bonus for having coordinates
            coord_bonus = 5 if loc.get("coordinates") else 0

            # Bonus for database matches with high similarity
            match_bonus = 0
            if loc.get("type") == "database_match" and loc.get("match_similarity"):
                if loc["match_similarity"] > 0.9:
                    match_bonus = 5
                elif loc["match_similarity"] > 0.8:
                    match_bonus = 3

            return type_score + conf_score + coord_bonus + match_bonus

        # Find highest scoring location
        primary = max(sources, key=score_location)

        logger.info(f"Primary location determined: type={primary.get('type')}, confidence={primary.get('confidence')}")
        return primary

    def get_location_hierarchy(self, location: Dict) -> Dict:
        """
        Build location hierarchy from coordinates to region

        Returns:
            {
                "coordinates": {"lat": float, "lon": float},
                "facility": str,
                "city": str,
                "state": str,
                "region": str,
                "confidence": str
            }
        """
        hierarchy = {
            "coordinates": location.get("coordinates"),
            "facility": location.get("facility"),
            "city": location.get("city"),
            "state": location.get("state"),
            "region": location.get("region"),
            "confidence": location.get("confidence", "unknown")
        }

        # Clean up None values
        return {k: v for k, v in hierarchy.items() if v is not None}

    def get_cached_synthesis(self, investigation_id: str) -> Optional[Dict]:
        """Get cached location synthesis for an investigation"""
        return self.cache.get(investigation_id)

    def cache_synthesis(self, investigation_id: str, synthesis: Dict):
        """Cache location synthesis result"""
        self.cache[investigation_id] = synthesis
