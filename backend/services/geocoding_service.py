"""Geocoding service for converting addresses to coordinates using OpenStreetMap Nominatim"""

import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime
import json

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class GeocodingService:
    """Service for geocoding facility addresses to coordinates"""

    def __init__(self):
        """Initialize geocoding service with Nominatim (OpenStreetMap)"""
        self.provider = "nominatim"
        self.geocoder = Nominatim(user_agent="tiger-id-investigation-system")
        self.cache: Dict[str, Dict] = {}
        self.rate_limit_delay = 1.0  # Nominatim requires 1 second between requests

    async def geocode_address(
        self,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: str = "USA"
    ) -> Optional[Dict]:
        """
        Convert address components to coordinates

        Args:
            address: Street address
            city: City name
            state: State name
            country: Country name (default USA)

        Returns:
            Dict with latitude, longitude, confidence, and geocoded_at timestamp
            Returns None if geocoding fails
        """
        # Build query string
        query_parts = []
        if address:
            query_parts.append(address)
        if city:
            query_parts.append(city)
        if state:
            query_parts.append(state)
        query_parts.append(country)

        query = ", ".join(query_parts)

        # Check cache
        if query in self.cache:
            logger.debug(f"Using cached geocoding result for: {query}")
            return self.cache[query]

        try:
            # Rate limiting for Nominatim
            await asyncio.sleep(self.rate_limit_delay)

            # Geocode using geopy
            location = await asyncio.to_thread(self.geocoder.geocode, query)

            if location:
                result = {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "confidence": "high",
                    "geocoded_at": datetime.utcnow().isoformat(),
                    "address_used": query,
                    "raw_address": location.address
                }

                # Cache result
                self.cache[query] = result

                logger.info(f"Successfully geocoded: {query} -> ({location.latitude}, {location.longitude})")
                return result
            else:
                logger.warning(f"No geocoding result found for: {query}")
                return None

        except GeocoderTimedOut:
            logger.error(f"Geocoding timeout for: {query}")
            return None
        except GeocoderServiceError as e:
            logger.error(f"Geocoding service error for {query}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected geocoding error for {query}: {e}")
            return None

    async def geocode_facility(self, facility) -> Optional[Dict]:
        """
        Geocode a facility and return coordinates

        Args:
            facility: Facility database model object

        Returns:
            Dict with coordinates or None if geocoding fails
        """
        # Try full address first
        if facility.address:
            result = await self.geocode_address(
                address=facility.address,
                city=facility.city,
                state=facility.state
            )
            if result:
                return result

        # Fallback: Try city + state
        if facility.city and facility.state:
            result = await self.geocode_address(
                city=facility.city,
                state=facility.state
            )
            if result:
                result["confidence"] = "medium"  # Lower confidence for city-level
                return result

        # Fallback: Try just state (centroid)
        if facility.state:
            result = await self.geocode_address(
                state=facility.state
            )
            if result:
                result["confidence"] = "low"  # Lowest confidence for state-level
                return result

        logger.warning(f"Failed to geocode facility: {facility.exhibitor_name}")
        return None

    async def batch_geocode_facilities(self, session: Session) -> Dict[str, int]:
        """
        Geocode all facilities missing coordinates in the database

        Args:
            session: Database session

        Returns:
            Dict with statistics: {success: int, failed: int, skipped: int}
        """
        from backend.database.models import Facility

        stats = {"success": 0, "failed": 0, "skipped": 0}

        # Get all facilities
        facilities = session.query(Facility).all()

        logger.info(f"Starting batch geocoding for {len(facilities)} facilities")

        for facility in facilities:
            # Skip if already has coordinates
            if facility.coordinates:
                try:
                    coords = json.loads(facility.coordinates) if isinstance(facility.coordinates, str) else facility.coordinates
                    if coords and "latitude" in coords and "longitude" in coords:
                        stats["skipped"] += 1
                        continue
                except:
                    pass  # If parsing fails, re-geocode

            # Geocode facility
            result = await self.geocode_facility(facility)

            if result:
                # Update facility coordinates
                facility.coordinates = json.dumps(result)
                stats["success"] += 1
                logger.info(f"Geocoded facility {facility.exhibitor_name}: {result['latitude']}, {result['longitude']}")
            else:
                stats["failed"] += 1
                logger.warning(f"Failed to geocode facility: {facility.exhibitor_name}")

        # Commit changes
        try:
            session.commit()
            logger.info(f"Batch geocoding complete: {stats}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to commit geocoded facilities: {e}")
            raise

        return stats

    def get_state_centroid(self, state: str) -> Optional[Dict]:
        """
        Get approximate centroid coordinates for US states

        Args:
            state: State name or abbreviation

        Returns:
            Dict with latitude and longitude, or None if state not found
        """
        # US state centroids (approximate)
        STATE_CENTROIDS = {
            "AL": {"lat": 32.806671, "lon": -86.791130},
            "AK": {"lat": 61.370716, "lon": -152.404419},
            "AZ": {"lat": 33.729759, "lon": -111.431221},
            "AR": {"lat": 34.969704, "lon": -92.373123},
            "CA": {"lat": 36.116203, "lon": -119.681564},
            "CO": {"lat": 39.059811, "lon": -105.311104},
            "CT": {"lat": 41.597782, "lon": -72.755371},
            "DE": {"lat": 39.318523, "lon": -75.507141},
            "FL": {"lat": 27.766279, "lon": -81.686783},
            "GA": {"lat": 33.040619, "lon": -83.643074},
            "HI": {"lat": 21.094318, "lon": -157.498337},
            "ID": {"lat": 44.240459, "lon": -114.478828},
            "IL": {"lat": 40.349457, "lon": -88.986137},
            "IN": {"lat": 39.849426, "lon": -86.258278},
            "IA": {"lat": 42.011539, "lon": -93.210526},
            "KS": {"lat": 38.526600, "lon": -96.726486},
            "KY": {"lat": 37.668140, "lon": -84.670067},
            "LA": {"lat": 31.169546, "lon": -91.867805},
            "ME": {"lat": 44.693947, "lon": -69.381927},
            "MD": {"lat": 39.063946, "lon": -76.802101},
            "MA": {"lat": 42.230171, "lon": -71.530106},
            "MI": {"lat": 43.326618, "lon": -84.536095},
            "MN": {"lat": 45.694454, "lon": -93.900192},
            "MS": {"lat": 32.741646, "lon": -89.678696},
            "MO": {"lat": 38.456085, "lon": -92.288368},
            "MT": {"lat": 46.921925, "lon": -110.454353},
            "NE": {"lat": 41.125370, "lon": -98.268082},
            "NV": {"lat": 38.313515, "lon": -117.055374},
            "NH": {"lat": 43.452492, "lon": -71.563896},
            "NJ": {"lat": 40.298904, "lon": -74.521011},
            "NM": {"lat": 34.840515, "lon": -106.248482},
            "NY": {"lat": 42.165726, "lon": -74.948051},
            "NC": {"lat": 35.630066, "lon": -79.806419},
            "ND": {"lat": 47.528912, "lon": -99.784012},
            "OH": {"lat": 40.388783, "lon": -82.764915},
            "OK": {"lat": 35.565342, "lon": -96.928917},
            "OR": {"lat": 44.572021, "lon": -122.070938},
            "PA": {"lat": 40.590752, "lon": -77.209755},
            "RI": {"lat": 41.680893, "lon": -71.511780},
            "SC": {"lat": 33.856892, "lon": -80.945007},
            "SD": {"lat": 44.299782, "lon": -99.438828},
            "TN": {"lat": 35.747845, "lon": -86.692345},
            "TX": {"lat": 31.054487, "lon": -97.563461},
            "UT": {"lat": 40.150032, "lon": -111.862434},
            "VT": {"lat": 44.045876, "lon": -72.710686},
            "VA": {"lat": 37.769337, "lon": -78.169968},
            "WA": {"lat": 47.400902, "lon": -121.490494},
            "WV": {"lat": 38.491226, "lon": -80.954453},
            "WI": {"lat": 44.268543, "lon": -89.616508},
            "WY": {"lat": 42.755966, "lon": -107.302490}
        }

        state_upper = state.upper()
        if state_upper in STATE_CENTROIDS:
            return {
                "latitude": STATE_CENTROIDS[state_upper]["lat"],
                "longitude": STATE_CENTROIDS[state_upper]["lon"],
                "lat": STATE_CENTROIDS[state_upper]["lat"],  # Keep for backwards compatibility
                "lon": STATE_CENTROIDS[state_upper]["lon"],  # Keep for backwards compatibility
                "confidence": "low",
                "geocoded_at": datetime.utcnow().isoformat(),
                "source": "state_centroid"
            }

        return None
