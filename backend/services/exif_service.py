"""EXIF extraction service for extracting GPS and metadata from images"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
from io import BytesIO

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

logger = logging.getLogger(__name__)


class EXIFService:
    """Service for extracting EXIF metadata from images"""

    def __init__(self):
        """Initialize EXIF service"""
        pass

    def extract_location(self, image_bytes: bytes) -> Optional[Dict]:
        """
        Extract GPS coordinates from image EXIF data

        Args:
            image_bytes: Raw image bytes

        Returns:
            Dict with latitude, longitude, altitude if found, None otherwise
        """
        try:
            image = Image.open(BytesIO(image_bytes))
            exif_data = image._getexif()

            if not exif_data:
                logger.debug("No EXIF data found in image")
                return None

            # Find GPS IFD
            gps_ifd = None
            for tag, value in exif_data.items():
                tag_name = TAGS.get(tag, tag)
                if tag_name == "GPSInfo":
                    gps_ifd = value
                    break

            if not gps_ifd:
                logger.debug("No GPS data found in EXIF")
                return None

            # Parse GPS data
            gps_data = {}
            for tag, value in gps_ifd.items():
                tag_name = GPSTAGS.get(tag, tag)
                gps_data[tag_name] = value

            # Extract coordinates
            latitude = self._convert_to_degrees(
                gps_data.get("GPSLatitude"),
                gps_data.get("GPSLatitudeRef")
            )
            longitude = self._convert_to_degrees(
                gps_data.get("GPSLongitude"),
                gps_data.get("GPSLongitudeRef")
            )

            if latitude is None or longitude is None:
                logger.debug("Could not parse GPS coordinates from EXIF")
                return None

            result = {
                "latitude": latitude,
                "longitude": longitude,
                "source": "exif_gps",
                "extracted_at": datetime.utcnow().isoformat()
            }

            # Add altitude if available
            if "GPSAltitude" in gps_data:
                altitude = float(gps_data["GPSAltitude"])
                altitude_ref = gps_data.get("GPSAltitudeRef", 0)
                if altitude_ref == 1:
                    altitude = -altitude
                result["altitude"] = altitude

            logger.info(f"Extracted GPS coordinates: {latitude}, {longitude}")
            return result

        except Exception as e:
            logger.error(f"Error extracting EXIF location: {e}")
            return None

    def extract_metadata(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract all relevant EXIF metadata from image

        Args:
            image_bytes: Raw image bytes

        Returns:
            Dict with GPS, datetime, camera info, and other metadata
        """
        metadata = {
            "gps": None,
            "datetime": None,
            "camera": {},
            "image_info": {},
            "raw_exif": {}
        }

        try:
            image = Image.open(BytesIO(image_bytes))

            # Get basic image info
            metadata["image_info"] = {
                "format": image.format,
                "size": image.size,
                "mode": image.mode
            }

            exif_data = image._getexif()

            if not exif_data:
                logger.debug("No EXIF data found in image")
                return metadata

            # Parse all EXIF tags
            for tag, value in exif_data.items():
                tag_name = TAGS.get(tag, tag)

                # Handle GPS data
                if tag_name == "GPSInfo":
                    metadata["gps"] = self.extract_location(image_bytes)

                # Handle datetime
                elif tag_name in ["DateTime", "DateTimeOriginal", "DateTimeDigitized"]:
                    try:
                        metadata["datetime"] = str(value)
                    except:
                        pass

                # Handle camera info
                elif tag_name in ["Make", "Model", "LensMake", "LensModel"]:
                    metadata["camera"][tag_name.lower()] = str(value)

                # Store raw EXIF for reference
                try:
                    # Convert value to string if it's not already serializable
                    if isinstance(value, bytes):
                        metadata["raw_exif"][tag_name] = value.hex()
                    elif isinstance(value, dict):
                        metadata["raw_exif"][tag_name] = {str(k): str(v) for k, v in value.items()}
                    else:
                        metadata["raw_exif"][tag_name] = str(value)
                except:
                    pass

            logger.info(f"Extracted EXIF metadata: GPS={bool(metadata['gps'])}, DateTime={bool(metadata['datetime'])}, Camera={bool(metadata['camera'])}")
            return metadata

        except Exception as e:
            logger.error(f"Error extracting EXIF metadata: {e}")
            return metadata

    def _convert_to_degrees(self, value, ref) -> Optional[float]:
        """
        Convert GPS coordinates from DMS (degrees, minutes, seconds) to decimal degrees

        Args:
            value: Tuple of (degrees, minutes, seconds)
            ref: Reference ('N', 'S', 'E', 'W')

        Returns:
            Decimal degrees or None if conversion fails
        """
        if not value or not ref:
            return None

        try:
            # Extract degrees, minutes, seconds
            degrees = float(value[0])
            minutes = float(value[1])
            seconds = float(value[2])

            # Convert to decimal degrees
            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

            # Apply reference (S and W are negative)
            if ref in ['S', 'W']:
                decimal = -decimal

            return decimal

        except Exception as e:
            logger.error(f"Error converting GPS coordinates: {e}")
            return None

    def has_gps_data(self, image_bytes: bytes) -> bool:
        """
        Quick check if image has GPS data in EXIF

        Args:
            image_bytes: Raw image bytes

        Returns:
            True if GPS data exists, False otherwise
        """
        location = self.extract_location(image_bytes)
        return location is not None
