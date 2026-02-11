"""
Seed facility coordinates for all facilities in the Tiger ID database.

Uses a tiered approach:
1. Known facility coordinates (hardcoded for well-known facilities)
2. Facility name + state geocoding via Nominatim (OpenStreetMap)
3. State centroid fallback for remaining facilities

Usage:
    python scripts/seed_facility_coordinates.py
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ============================================================================
# Known facility coordinates (well-known US tiger facilities)
# These are approximate public coordinates sourced from OpenStreetMap/Google Maps
# ============================================================================
KNOWN_FACILITIES: Dict[str, Tuple[float, float]] = {
    # Alabama
    "MONTGOMERY ZOO": (32.3573, -86.2629),
    "TIGERS FOR TOMORROW": (34.2556, -85.9553),
    # Arizona
    "OUT OF AFRICA WILDLIFE PARK": (34.6328, -111.8449),
    "WILDLIFE WORLD ZOO": (33.4713, -112.3007),
    # California
    "ROAR FOUNDATION": (34.5553, -118.3786),
    "SIX FLAGS DISCOVERY KINGDOM": (38.1386, -122.2327),
    "AMERICA'S TEACHING ZOO": (34.2544, -119.2117),
    "PROJECT SURVIVALS CAT HAVEN": (36.8192, -119.2000),
    "MONTEREY ZOO": (36.5750, -121.7550),
    "HESPERIA ZOO": (34.4264, -117.3009),
    "EXOTIC FELINE BREEDING COMPOUND": (33.6943, -116.9519),
    # Florida
    "BIG CAT RESCUE": (28.0653, -82.5803),
    "MCCARTHY'S WILDLIFE SANCTUARY": (26.6867, -80.2508),
    "MIKE STAPLETON": (30.4383, -87.2169),
    "BEARCAT HOLLOW": (30.4733, -87.0400),
    "LIVING TREASURES WILD ANIMAL PARK": (40.9328, -79.8292),
    "DADE CITY'S WILD THINGS": (28.3647, -82.1957),
    "JUNGLE ISLAND": (25.7862, -80.1743),
    "SINGLE VISION": (29.8614, -82.6383),
    "KOWIACHOBEE": (26.1033, -81.7083),
    "BEARADISE RANCH": (28.4533, -82.1667),
    "ZOOLOGICAL WILDLIFE FOUNDATION": (25.5736, -80.4442),
    "NOAHS ARK ANIMAL SANCTUARY": (33.2728, -84.3108),
    "WILD FLORIDA": (28.1483, -80.9750),
    "CATTY SHACK RANCH": (30.3286, -81.5181),
    "PANTHER RIDGE CONSERVATION CENTER": (26.7750, -80.2933),
    "ANIMAL ADVENTURES": (28.0789, -81.7342),
    "OCTAGON WILDLIFE SANCTUARY": (26.7636, -81.8900),
    "PALM BEACH ZOO": (26.6683, -80.0717),
    "LOWRY PARK ZOO": (28.0117, -82.4678),
    "BUSCH GARDENS TAMPA": (28.0372, -82.4234),
    "MIKE STEWART": (30.5942, -87.0517),
    "SAMMY HALL'S CIRCUS": (27.8000, -81.4333),
    # Georgia
    "NOAH'S ARK ANIMAL SANCTUARY": (33.2728, -84.3108),
    "CHESTATEE WILDLIFE PRESERVE": (34.5592, -83.8847),
    # Hawaii
    "PANA'EWA RAINFOREST ZOO": (19.6500, -155.0833),
    # Illinois
    "EXOTIC FELINE RESCUE CENTER": (39.0700, -87.0150),
    # Indiana
    "EXOTIC FELINE RESCUE CENTER": (39.0700, -87.0150),
    "WILSTEM WILDLIFE PARK": (38.4575, -86.6917),
    "INDIANA'S ANIMAL CORNER": (40.4167, -86.8753),
    # Kansas
    "CEDAR COVE FELINE CONSERVATORY": (37.0842, -97.3558),
    # Louisiana
    "MIKE THE TIGER": (30.4133, -91.1842),
    "MIKEY'S MENAGERIE": (30.3122, -91.7667),
    # Maine
    "DEW HAVEN": (44.5450, -68.9550),
    # Maryland
    "CATOCTIN WILDLIFE PRESERVE": (39.6403, -77.4569),
    # Massachusetts
    "SOUTHWICK'S ZOO": (42.0642, -71.5608),
    # Michigan
    "ORRVILLE FARMSTEAD": (42.0000, -84.6000),
    # Minnesota
    "WILDCAT SANCTUARY": (45.5800, -93.6175),
    # Missouri
    "EXOTIC ANIMAL PARADISE": (38.3333, -93.3833),
    "NATIONAL TIGER SANCTUARY": (38.2250, -91.1917),
    "DICKERSON PARK ZOO": (37.2089, -93.3333),
    # Mississippi
    "JACKSON ZOO": (32.3186, -90.2192),
    # Montana
    "DISCOVERY WILDLIFE PARK": (46.6000, -114.0000),
    # Nevada
    "SIEGFRIED & ROY'S SECRET GARDEN": (36.1215, -115.1739),
    "LION HABITAT RANCH": (36.0000, -115.0167),
    # New Jersey
    "TIGER WORLD": (40.5975, -74.5847),
    # New Mexico
    "WILDLIFE WEST NATURE PARK": (35.1097, -106.2342),
    # New York
    "CATSKILL GAME FARM": (42.3047, -74.1536),
    "BRONX ZOO": (40.8506, -73.8769),
    # North Carolina
    "CONSERVATORS CENTER": (36.2717, -79.3950),
    "T.I.G.E.R.S": (33.8000, -78.7500),
    "CAROLINA TIGER RESCUE": (35.8419, -79.0575),
    # North Dakota
    "ROOSEVELT PARK ZOO": (48.2106, -101.2961),
    # Ohio
    "EXOTIC ANIMAL TRAINING": (40.3333, -82.9333),
    # Oklahoma
    "G.W. ZOO": (35.3672, -97.0831),
    "RESCUE RIDGE": (36.1500, -95.9833),
    "TULSA ZOO": (36.1525, -95.9736),
    "ARBUCKLE WILDERNESS": (34.3694, -97.0236),
    # Oregon
    "WILDLIFE SAFARI": (42.9758, -123.3408),
    # Pennsylvania
    "T&D'S CATS OF THE WORLD": (40.6333, -76.7833),
    "CLAWS 'N' PAWS WILD ANIMAL PARK": (41.2583, -75.3750),
    "LEHIGH VALLEY ZOO": (40.6753, -75.6039),
    "LIVING TREASURES WILD ANIMAL PARK": (40.9328, -79.8292),
    # South Carolina
    "MYRTLE BEACH SAFARI": (33.7281, -78.8517),
    # Tennessee
    "TIGER HAVEN": (35.8333, -84.3333),
    "NASHVILLE ZOO": (36.1033, -86.7150),
    # Texas
    "EXOTIC ANIMAL WORLD": (29.7000, -97.0000),
    "INTERNATIONAL EXOTIC ANIMAL SANCTUARY": (31.5578, -97.1308),
    "IN-SYNC EXOTICS": (32.5333, -96.5833),
    "SANTA FE COLLEGE TEACHING ZOO": (29.6517, -82.3783),
    "HOUSTON ZOO": (29.7144, -95.3900),
    "SAN ANTONIO ZOO": (29.4611, -98.4742),
    "TIGER CREEK WILDLIFE REFUGE": (32.0833, -95.9333),
    # Utah
    "HOGLE ZOO": (40.7483, -111.8150),
    # Virginia
    "NATURAL BRIDGE ZOO": (37.6269, -79.5422),
    "NATIONAL ZOOLOGICAL PARK": (38.9296, -77.0498),
    "VIRGINIA SAFARI PARK": (37.7378, -79.5422),
    # Washington
    "WOODLAND PARK ZOO": (47.6683, -122.3503),
    # West Virginia
    "GOOD ZOO": (40.0700, -80.7200),
    # Wisconsin
    "STONEY BROOK FARMS EXOTICS": (44.3333, -88.0000),
    "TIMBAVATI WILDLIFE PARK": (44.3583, -87.6083),
    "SPECIAL MEMORIES ZOO": (44.4333, -89.4333),
    "WILDCAT MOUNTAIN": (43.7192, -90.5767),
    "IRVINE PARK ZOO": (44.8333, -91.4833),
}


# US State centroids (same as in geocoding_service.py)
STATE_CENTROIDS = {
    "AL": (32.806671, -86.791130),
    "AK": (61.370716, -152.404419),
    "AZ": (33.729759, -111.431221),
    "AR": (34.969704, -92.373123),
    "CA": (36.116203, -119.681564),
    "CO": (39.059811, -105.311104),
    "CT": (41.597782, -72.755371),
    "DE": (39.318523, -75.507141),
    "FL": (27.766279, -81.686783),
    "GA": (33.040619, -83.643074),
    "HI": (21.094318, -157.498337),
    "ID": (44.240459, -114.478828),
    "IL": (40.349457, -88.986137),
    "IN": (39.849426, -86.258278),
    "IA": (42.011539, -93.210526),
    "KS": (38.526600, -96.726486),
    "KY": (37.668140, -84.670067),
    "LA": (31.169546, -91.867805),
    "ME": (44.693947, -69.381927),
    "MD": (39.063946, -76.802101),
    "MA": (42.230171, -71.530106),
    "MI": (43.326618, -84.536095),
    "MN": (45.694454, -93.900192),
    "MS": (32.741646, -89.678696),
    "MO": (38.456085, -92.288368),
    "MT": (46.921925, -110.454353),
    "NE": (41.125370, -98.268082),
    "NV": (38.313515, -117.055374),
    "NH": (43.452492, -71.563896),
    "NJ": (40.298904, -74.521011),
    "NM": (34.840515, -106.248482),
    "NY": (42.165726, -74.948051),
    "NC": (35.630066, -79.806419),
    "ND": (47.528912, -99.784012),
    "OH": (40.388783, -82.764915),
    "OK": (35.565342, -96.928917),
    "OR": (44.572021, -122.070938),
    "PA": (40.590752, -77.209755),
    "RI": (41.680893, -71.511780),
    "SC": (33.856892, -80.945007),
    "SD": (44.299782, -99.438828),
    "TN": (35.747845, -86.692345),
    "TX": (31.054487, -97.563461),
    "UT": (40.150032, -111.862434),
    "VT": (44.045876, -72.710686),
    "VA": (37.769337, -78.169968),
    "WA": (47.400902, -121.490494),
    "WV": (38.491226, -80.954453),
    "WI": (44.268543, -89.616508),
    "WY": (42.755966, -107.302490),
    "DC": (38.907192, -77.036871),
}


def find_known_match(facility_name: str) -> Optional[Tuple[float, float]]:
    """
    Try to match a facility name against our known facilities list.
    Uses substring matching to handle variations in naming.
    """
    name_upper = facility_name.upper().strip()

    # Direct match
    for known_name, coords in KNOWN_FACILITIES.items():
        if known_name.upper() in name_upper or name_upper in known_name.upper():
            return coords

    # Try matching significant words (at least 2 words matching)
    name_words = set(name_upper.replace("'", "").replace("(", "").replace(")", "").split())
    # Remove common words
    stop_words = {"THE", "OF", "AND", "&", "A", "AN", "INC", "LLC", "CORP"}
    name_words -= stop_words

    for known_name, coords in KNOWN_FACILITIES.items():
        known_words = set(known_name.upper().replace("'", "").replace("(", "").replace(")", "").split())
        known_words -= stop_words
        overlap = name_words & known_words
        if len(overlap) >= 2:
            return coords

    return None


def add_jitter(lat: float, lon: float, is_state_centroid: bool = False) -> Tuple[float, float]:
    """
    Add small random jitter to coordinates to prevent markers from stacking.
    Uses deterministic jitter based on coordinates themselves.

    For state centroids, adds more jitter (0.5 degrees ~ 35 miles).
    For known locations, adds minimal jitter (0.01 degrees ~ 0.7 miles).
    """
    import hashlib

    # Create a deterministic seed from the coordinates
    seed_str = f"{lat:.6f},{lon:.6f}"
    hash_bytes = hashlib.md5(seed_str.encode()).digest()

    # Extract two pseudo-random values from the hash
    lat_jitter = (hash_bytes[0] - 128) / 128.0  # Range: -1 to 1
    lon_jitter = (hash_bytes[1] - 128) / 128.0  # Range: -1 to 1

    if is_state_centroid:
        # For state centroids, jitter up to 0.5 degrees
        lat_jitter *= 0.5
        lon_jitter *= 0.5
    else:
        # For known locations, minimal jitter
        lat_jitter *= 0.01
        lon_jitter *= 0.01

    return (lat + lat_jitter, lon + lon_jitter)


async def geocode_with_nominatim(
    facility_name: str,
    state: Optional[str],
    geocoder
) -> Optional[Tuple[float, float, str]]:
    """
    Try geocoding a facility via Nominatim.
    Returns (lat, lon, confidence) or None.
    """
    import asyncio

    queries_to_try = []

    # Try facility name + state + USA
    if state:
        queries_to_try.append(f"{facility_name}, {state}, USA")
        # Also try without parenthetical text
        clean_name = facility_name.split("(")[0].strip()
        if clean_name != facility_name:
            queries_to_try.append(f"{clean_name}, {state}, USA")

    for query in queries_to_try:
        try:
            await asyncio.sleep(1.1)  # Nominatim rate limit
            location = await asyncio.to_thread(geocoder.geocode, query)
            if location:
                logger.info(f"  Nominatim geocoded: {query} -> ({location.latitude:.4f}, {location.longitude:.4f})")
                return (location.latitude, location.longitude, "medium")
        except Exception as e:
            logger.warning(f"  Nominatim error for '{query}': {e}")

    return None


async def seed_coordinates():
    """Main function to seed all facility coordinates."""
    import sqlite3

    db_path = os.path.join(str(project_root), "data", "tiger_id.db")
    if not os.path.exists(db_path):
        logger.error(f"Database not found at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all facilities
    cursor.execute("SELECT facility_id, exhibitor_name, city, state, address, coordinates FROM facilities")
    facilities = cursor.fetchall()

    logger.info(f"Found {len(facilities)} facilities to process")

    stats = {
        "known_match": 0,
        "nominatim": 0,
        "state_centroid": 0,
        "no_location": 0,
        "already_geocoded": 0,
        "total": len(facilities),
    }

    # Try to import geopy for Nominatim
    nominatim_available = False
    geocoder = None
    try:
        from geopy.geocoders import Nominatim
        geocoder = Nominatim(user_agent="tiger-id-seed-script")
        nominatim_available = True
        logger.info("Nominatim geocoder available")
    except ImportError:
        logger.warning("geopy not installed - skipping Nominatim geocoding (pip install geopy)")

    updated = 0

    for facility_id, name, city, state, address, existing_coords in facilities:
        # Skip NaN names (bad data)
        if not name or name == "nan":
            stats["no_location"] += 1
            continue

        # Skip if already has valid coordinates
        if existing_coords:
            try:
                coords_data = json.loads(existing_coords)
                if coords_data.get("latitude") and coords_data.get("longitude"):
                    stats["already_geocoded"] += 1
                    continue
            except (json.JSONDecodeError, TypeError):
                pass  # Re-geocode if parsing fails

        lat, lon, confidence, source = None, None, "low", "unknown"

        # Tier 1: Check known facilities
        known_coords = find_known_match(name)
        if known_coords:
            lat, lon = known_coords
            confidence = "high"
            source = "known_facility"
            stats["known_match"] += 1
            logger.info(f"  Known match: {name} -> ({lat:.4f}, {lon:.4f})")

        # Tier 2: Try Nominatim geocoding
        if lat is None and nominatim_available and state:
            result = await geocode_with_nominatim(name, state, geocoder)
            if result:
                lat, lon, confidence = result
                source = "nominatim"
                stats["nominatim"] += 1

        # Tier 3: State centroid fallback
        if lat is None and state and state.upper() in STATE_CENTROIDS:
            base_lat, base_lon = STATE_CENTROIDS[state.upper()]
            # Add deterministic jitter based on facility name
            import hashlib
            hash_bytes = hashlib.md5(name.encode()).digest()
            lat_jitter = (hash_bytes[0] - 128) / 256.0  # Range: -0.5 to 0.5
            lon_jitter = (hash_bytes[1] - 128) / 256.0
            lat = base_lat + lat_jitter
            lon = base_lon + lon_jitter
            confidence = "low"
            source = "state_centroid"
            stats["state_centroid"] += 1
            logger.info(f"  State centroid: {name} ({state}) -> ({lat:.4f}, {lon:.4f})")

        # No location data available
        if lat is None:
            stats["no_location"] += 1
            logger.warning(f"  No location: {name} (state={state})")
            continue

        # Build coordinates JSON
        coords_json = json.dumps({
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "confidence": confidence,
            "source": source,
            "geocoded_at": datetime.utcnow().isoformat(),
        })

        # Update the facility
        cursor.execute(
            "UPDATE facilities SET coordinates = ? WHERE facility_id = ?",
            (coords_json, facility_id)
        )
        updated += 1

    # Commit all changes
    conn.commit()

    logger.info("")
    logger.info("=" * 60)
    logger.info("GEOCODING RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total facilities:    {stats['total']}")
    logger.info(f"Already geocoded:    {stats['already_geocoded']}")
    logger.info(f"Known match:         {stats['known_match']}")
    logger.info(f"Nominatim geocoded:  {stats['nominatim']}")
    logger.info(f"State centroid:      {stats['state_centroid']}")
    logger.info(f"No location data:    {stats['no_location']}")
    logger.info(f"Records updated:     {updated}")
    logger.info("=" * 60)

    # Verify results
    cursor.execute("SELECT COUNT(*) FROM facilities WHERE coordinates IS NOT NULL AND coordinates != ''")
    with_coords = cursor.fetchone()[0]
    logger.info(f"\nFacilities with coordinates: {with_coords}/{stats['total']}")

    # Show sample of geocoded facilities
    cursor.execute("""
        SELECT exhibitor_name, state, coordinates
        FROM facilities
        WHERE coordinates IS NOT NULL AND coordinates != ''
        LIMIT 10
    """)
    logger.info("\n=== SAMPLE GEOCODED FACILITIES ===")
    for name, state, coords_str in cursor.fetchall():
        try:
            coords = json.loads(coords_str)
            logger.info(
                f"  {name[:40]:40s} ({state:2s}) -> "
                f"({coords['latitude']:.4f}, {coords['longitude']:.4f}) "
                f"[{coords.get('confidence', '?')}]"
            )
        except Exception:
            logger.info(f"  {name[:40]:40s} ({state:2s}) -> PARSE ERROR")

    conn.close()
    return stats


if __name__ == "__main__":
    logger.info("Starting facility coordinate seeding...")
    stats = asyncio.run(seed_coordinates())
    logger.info("Done!")
