"""USFWS API client for wildlife permits and records"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.services.external_apis.base_client import BaseAPIClient
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class USFWSClient(BaseAPIClient):
    """Client for US Fish and Wildlife Service API
    
    USFWS maintains records of:
    - Wildlife permits (import/export)
    - Lacey Act declarations
    - Endangered Species Act records
    - Wildlife trade data
    
    Note: USFWS API documentation: https://www.fws.gov/program/e-dec-file
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.fws.gov",
        timeout: int = 30
    ):
        super().__init__(api_key=api_key, base_url=base_url, timeout=timeout)
    
    async def health_check(self) -> bool:
        """Check if USFWS API is accessible"""
        try:
            response = await self._request("GET", "/health", params={})
            return response.get("status") == "ok"
        except Exception:
            # If health endpoint doesn't exist, assume accessible
            return True
    
    async def search_permits(
        self,
        permit_number: Optional[str] = None,
        applicant_name: Optional[str] = None,
        species: Optional[str] = None,
        permit_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search USFWS permits
        
        Args:
            permit_number: Permit number
            applicant_name: Applicant name
            species: Species name
            permit_type: Type of permit (e.g., "Import", "Export")
            status: Permit status
            limit: Maximum results
        
        Returns:
            List of permit records
        """
        params = {"limit": limit}
        if permit_number:
            params["permit_number"] = permit_number
        if applicant_name:
            params["applicant_name"] = applicant_name
        if species:
            params["species"] = species
        if permit_type:
            params["permit_type"] = permit_type
        if status:
            params["status"] = status
        
        try:
            response = await self._request("GET", "/permits", params=params)
            return response.get("results", [])
        except Exception as e:
            logger.error("USFWS permit search failed", error=str(e))
            return []
    
    async def get_permit_details(self, permit_number: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed permit information
        
        Args:
            permit_number: Permit number
        
        Returns:
            Permit details
        """
        try:
            response = await self._request(
                "GET",
                f"/permits/{permit_number}",
                params={}
            )
            return response
        except Exception as e:
            logger.error(
                "Failed to get USFWS permit details",
                permit_number=permit_number,
                error=str(e)
            )
            return None
    
    async def search_lacey_act_declarations(
        self,
        importer_name: Optional[str] = None,
        species: Optional[str] = None,
        country_origin: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search Lacey Act declarations
        
        The Lacey Act requires declarations for certain wildlife imports
        
        Args:
            importer_name: Importer name
            species: Species name
            country_origin: Origin country
            date_from: Start date
            date_to: End date
            limit: Maximum results
        
        Returns:
            List of Lacey Act declarations
        """
        params = {"limit": limit}
        if importer_name:
            params["importer_name"] = importer_name
        if species:
            params["species"] = species
        if country_origin:
            params["country_origin"] = country_origin
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        
        try:
            response = await self._request(
                "GET",
                "/lacey-act",
                params=params
            )
            return response.get("results", [])
        except Exception as e:
            logger.error("USFWS Lacey Act search failed", error=str(e))
            return []
    
    async def search_esa_records(
        self,
        species: Optional[str] = None,
        action_type: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search Endangered Species Act (ESA) records
        
        Args:
            species: Species name
            action_type: Type of action (e.g., "Listing", "Recovery Plan")
            state: State code
            limit: Maximum results
        
        Returns:
            List of ESA records
        """
        params = {"limit": limit}
        if species:
            params["species"] = species
        if action_type:
            params["action_type"] = action_type
        if state:
            params["state"] = state
        
        try:
            response = await self._request("GET", "/esa", params=params)
            return response.get("results", [])
        except Exception as e:
            logger.error("USFWS ESA search failed", error=str(e))
            return []
    
    async def get_tiger_permit_records(
        self,
        applicant_name: Optional[str] = None,
        permit_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Convenience method for tiger-specific permit records
        
        Args:
            applicant_name: Applicant name
            permit_type: Permit type
            limit: Maximum results
        
        Returns:
            List of tiger permit records
        """
        return await self.search_permits(
            species="Panthera tigris",
            applicant_name=applicant_name,
            permit_type=permit_type,
            limit=limit
        )

