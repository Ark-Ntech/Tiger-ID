"""UUID utility functions"""

from typing import Optional
from uuid import UUID


def safe_uuid(uuid_string: Optional[str]) -> Optional[UUID]:
    """
    Safely convert string to UUID, returning None if invalid
    
    Args:
        uuid_string: String representation of UUID
    
    Returns:
        UUID object or None if invalid
    """
    if not uuid_string:
        return None
    
    try:
        return UUID(uuid_string)
    except (ValueError, TypeError):
        return None


def parse_uuid(uuid_string: str) -> UUID:
    """
    Parse string to UUID, raising ValueError if invalid
    
    Args:
        uuid_string: String representation of UUID
    
    Returns:
        UUID object
    
    Raises:
        ValueError: If string is not a valid UUID
    """
    if not uuid_string:
        raise ValueError("UUID string cannot be empty")
    
    try:
        return UUID(uuid_string)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid UUID string: {uuid_string}") from e


def uuid_to_string(uuid_value: Optional[UUID]) -> Optional[str]:
    """
    Convert UUID to string, handling None
    
    Args:
        uuid_value: UUID object or None
    
    Returns:
        String representation or None
    """
    if uuid_value is None:
        return None
    
    return str(uuid_value)

