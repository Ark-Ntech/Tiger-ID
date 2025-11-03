"""API client utilities - wrapper for external API clients"""

from typing import Optional, Dict, Any

# Import the actual client classes
from backend.services.external_apis.base_client import BaseAPIClient
from backend.services.external_apis.usda_client import USDAClient
from backend.services.external_apis.cites_client import CITESClient
from backend.services.external_apis.usfws_client import USFWSClient
from backend.services.external_apis.factory import get_api_manager

# Alias classes for backward compatibility
DataAPIClient = BaseAPIClient
USDAAPIClient = USDAClient
CITESAPIClient = CITESClient
USFWSAPIClient = USFWSClient


# DataAPIManager is a function that returns the manager instance
def DataAPIManager():
    """Get API manager instance - convenience function"""
    return get_api_manager()


__all__ = [
    "DataAPIClient",
    "USDAAPIClient",
    "CITESAPIClient",
    "USFWSAPIClient",
    "DataAPIManager",
]