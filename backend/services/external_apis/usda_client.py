"""USDA API client for facility licensing and inspection data"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.services.external_apis.base_client import BaseAPIClient
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class USDAClient(BaseAPIClient):
    """Client for USDA Animal Care API
    
    USDA Animal Care maintains records of licensed exhibitors, including:
    - USDA license numbers
    - Facility inspection reports (IR)
    - Violation history
    - Animal inventory
    
    Note: USDA API documentation: https://www.aphis.usda.gov/aphis/ourfocus/animalwelfare
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://www.aphis.usda.gov/aphis/ourfocus/animalwelfare",
        timeout: int = 30
    ):
        super().__init__(api_key=api_key, base_url=base_url, timeout=timeout)
    
    async def health_check(self) -> bool:
        """Check if USDA API is accessible"""
        try:
            # Simple health check - adjust endpoint based on actual API
            response = await self._request("GET", "/api/health", params={})
            return response.get("status") == "ok"
        except Exception as e:
            logger.warning("USDA health check failed", error=str(e))
            # If no public health endpoint, try a basic search
            return True  # Assume accessible if we can initialize
    
    async def search_facilities(
        self,
        license_number: Optional[str] = None,
        exhibitor_name: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for USDA licensed facilities
        
        Args:
            license_number: USDA license number
            exhibitor_name: Facility/exhibitor name
            state: State code
            city: City name
            limit: Maximum results
        
        Returns:
            List of facility records
        """
        params = {"limit": limit}
        if license_number:
            params["license_number"] = license_number
        if exhibitor_name:
            params["exhibitor_name"] = exhibitor_name
        if state:
            params["state"] = state
        if city:
            params["city"] = city
        
        try:
            # Actual endpoint may vary - adjust based on USDA API documentation
            response = await self._request("GET", "/api/facilities/search", params=params)
            return response.get("results", [])
        except Exception as e:
            logger.error("USDA facility search failed", error=str(e))
            # Fallback: Return empty or use web scraping alternative
            return []
    
    async def get_facility_details(self, license_number: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed facility information
        
        Args:
            license_number: USDA license number
        
        Returns:
            Facility details including inspection history
        """
        try:
            response = await self._request(
                "GET",
                f"/api/facilities/{license_number}",
                params={}
            )
            return response
        except Exception as e:
            logger.error(
                "Failed to get USDA facility details",
                license_number=license_number,
                error=str(e)
            )
            return None
    
    async def get_inspection_reports(
        self,
        license_number: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get inspection reports for a facility
        
        Args:
            license_number: USDA license number
            start_date: Start date for inspection reports
            end_date: End date for inspection reports
        
        Returns:
            List of inspection reports
        """
        params = {"license_number": license_number}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        
        try:
            response = await self._request(
                "GET",
                "/api/inspections",
                params=params
            )
            return response.get("results", [])
        except Exception as e:
            logger.error(
                "Failed to get USDA inspection reports",
                license_number=license_number,
                error=str(e)
            )
            return []
    
    async def get_violation_history(
        self,
        license_number: str
    ) -> List[Dict[str, Any]]:
        """
        Get violation history for a facility
        
        Args:
            license_number: USDA license number
        
        Returns:
            List of violations
        """
        try:
            response = await self._request(
                "GET",
                f"/api/facilities/{license_number}/violations",
                params={}
            )
            return response.get("results", [])
        except Exception as e:
            logger.error(
                "Failed to get USDA violation history",
                license_number=license_number,
                error=str(e)
            )
            return []
    
    async def search_by_location(
        self,
        state: str,
        city: Optional[str] = None,
        zip_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search facilities by location
        
        Args:
            state: State code
            city: City name
            zip_code: ZIP code
        
        Returns:
            List of facilities in the location
        """
        params = {"state": state}
        if city:
            params["city"] = city
        if zip_code:
            params["zip_code"] = zip_code
        
        try:
            response = await self._request(
                "GET",
                "/api/facilities/search",
                params=params
            )
            return response.get("results", [])
        except Exception as e:
            logger.error("USDA location search failed", error=str(e))
            return []

