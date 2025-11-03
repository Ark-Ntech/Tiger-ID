"""Factory for creating external API clients"""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml

from backend.services.external_apis.usda_client import USDAClient
from backend.services.external_apis.cites_client import CITESClient
from backend.services.external_apis.usfws_client import USFWSClient
from backend.services.external_apis.youtube_client import YouTubeClient
from backend.services.external_apis.meta_client import MetaClient
from backend.config.settings import get_settings

# Cache for singleton clients
_client_cache: Dict[str, Any] = {}


def get_api_clients(
    force_recreate: bool = False,
    config_path: Optional[Path] = None
) -> Dict[str, Optional[Any]]:
    """
    Get all API clients (cached singleton pattern)
    
    Args:
        force_recreate: Force recreation of clients (bypass cache)
        config_path: Path to config file (default: config/settings.yaml)
    
    Returns:
        Dictionary of API clients (usda, cites, usfws, youtube, meta)
    """
    if not force_recreate and _client_cache:
        return _client_cache
    
    # Load configuration
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
    
    config = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    
    external_apis = config.get("external_apis", {})
    settings = get_settings()
    
    # Create clients
    clients = {
        "usda": None,
        "cites": None,
        "usfws": None,
        "youtube": None,
        "meta": None
    }
    
    # USDA client
    usda_config = external_apis.get("usda", {})
    if usda_config.get("enabled", False) or settings.external_apis.usda_enabled:
        clients["usda"] = USDAClient(
            api_key=usda_config.get("api_key") or settings.external_apis.usda_api_key,
            base_url=usda_config.get("base_url", settings.external_apis.usda_base_url),
            timeout=usda_config.get("timeout", 30)
        )
    
    # CITES client
    cites_config = external_apis.get("cites", {})
    if cites_config.get("enabled", False) or settings.external_apis.cites_enabled:
        clients["cites"] = CITESClient(
            api_key=cites_config.get("api_key") or settings.external_apis.cites_api_key,
            base_url=cites_config.get("base_url", settings.external_apis.cites_base_url),
            timeout=cites_config.get("timeout", 30)
        )
    
    # USFWS client
    usfws_config = external_apis.get("usfws", {})
    if usfws_config.get("enabled", False) or settings.external_apis.usfws_enabled:
        clients["usfws"] = USFWSClient(
            api_key=usfws_config.get("api_key") or settings.external_apis.usfws_api_key,
            base_url=usfws_config.get("base_url", settings.external_apis.usfws_base_url),
            timeout=usfws_config.get("timeout", 30)
        )
    
    # YouTube client
    youtube_config = external_apis.get("youtube", {})
    if youtube_config.get("enabled", False) or settings.external_apis.youtube_enabled:
        clients["youtube"] = YouTubeClient(
            api_key=youtube_config.get("api_key") or settings.external_apis.youtube_api_key,
            base_url=youtube_config.get("base_url", "https://www.googleapis.com/youtube/v3"),
            timeout=youtube_config.get("timeout", 30)
        )
    
    # Meta client
    meta_config = external_apis.get("meta", {})
    if meta_config.get("enabled", False) or settings.external_apis.meta_enabled:
        clients["meta"] = MetaClient(
            access_token=meta_config.get("access_token") or settings.external_apis.meta_access_token,
            app_id=meta_config.get("app_id") or settings.external_apis.meta_app_id,
            app_secret=meta_config.get("app_secret") or settings.external_apis.meta_app_secret,
            api_version=meta_config.get("api_version", "v19.0"),
            base_url=meta_config.get("base_url"),
            timeout=meta_config.get("timeout", 30)
        )
    
    # Cache clients
    _client_cache.update(clients)
    
    return clients


def get_api_manager() -> Dict[str, Any]:
    """
    Get API manager with all clients (for compatibility with old DataAPIManager)
    
    Returns:
        Dictionary with clients accessible as attributes
    """
    clients = get_api_clients()
    
    class APIManager:
        """Manager for all API clients"""
        
        def __init__(self, clients_dict: Dict[str, Any]):
            self.usda = clients_dict.get("usda")
            self.cites = clients_dict.get("cites")
            self.usfws = clients_dict.get("usfws")
            self.youtube = clients_dict.get("youtube")
            self.meta = clients_dict.get("meta")
        
        async def gather_facility_data(
            self,
            facility_name: str,
            usda_license: Optional[str] = None,
            state: Optional[str] = None
        ) -> Dict[str, Any]:
            """Gather data about a facility from all APIs"""
            results = {
                "usda_inspections": [],
                "usda_facility": None,
                "cites_records": [],
                "usfws_cases": []
            }
            
            # USDA data
            if self.usda:
                if usda_license:
                    inspections = await self.usda.get_inspection_reports(usda_license)
                    results["usda_inspections"] = inspections
                
                if facility_name or state:
                    facilities = await self.usda.search_facilities(
                        exhibitor_name=facility_name,
                        state=state
                    )
                    if facilities:
                        results["usda_facility"] = facilities[0]
            
            # CITES records
            if self.cites:
                records = await self.cites.search_trade_records(
                    species="Panthera tigris",
                    country_origin="US",
                    country_destination=None
                )
                results["cites_records"] = records[:10]  # Limit
            
            # USFWS enforcement
            if self.usfws:
                cases = await self.usfws.search_permits(
                    applicant_name=facility_name,
                    species="Panthera tigris"
                )
                results["usfws_cases"] = cases[:10]  # Limit
            
            return results
        
        async def close_all(self):
            """Close all API clients"""
            import asyncio
            # Note: BaseAPIClient manages its own httpx client internally
            # Clients don't expose client directly, so this is a no-op
            # If needed, we can add close() methods to clients later
            pass
    
    return APIManager(clients)


def clear_cache():
    """Clear client cache (useful for testing)"""
    global _client_cache
    _client_cache = {}

