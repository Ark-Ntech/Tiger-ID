"""Unified configuration management using Pydantic Settings"""

from typing import Optional
from pathlib import Path
from enum import Enum
import os
import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, ValidationError, model_validator


class DatabaseSettings(BaseSettings):
    """Database configuration - SQLite only with sqlite-vec for vector search"""
    url: str = Field(default="sqlite:///data/tiger_id.db", alias="DATABASE_URL")
    echo: bool = False

    @model_validator(mode='after')
    def validate_database_url(self):
        # SQLite only
        if not self.url.startswith('sqlite://'):
            raise ValueError(
                'DATABASE_URL must be a SQLite connection string (sqlite:///path/to/db). '
                'PostgreSQL is no longer supported - use SQLite with sqlite-vec for vector search.'
            )

        # Verify sqlite-vec is available
        try:
            import sqlite_vec
        except ImportError:
            raise ValueError(
                'sqlite-vec extension is required for vector search. '
                'Install with: pip install sqlite-vec'
            )
        return self


class StorageSettings(BaseSettings):
    """Storage configuration"""
    type: str = Field(default="local", alias="STORAGE_TYPE")
    local_path: str = Field(default="./data/storage", alias="STORAGE_PATH")
    s3_bucket: Optional[str] = Field(default=None, alias="S3_BUCKET")
    s3_region: Optional[str] = Field(default=None, alias="S3_REGION")


class AuthenticationSettings(BaseSettings):
    """Authentication configuration"""
    jwt_secret_key: str = Field(default="change-me-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, alias="JWT_EXPIRATION_HOURS")
    mfa_enabled: bool = False
    password_min_length: int = 8


class CSRFSettings(BaseSettings):
    """CSRF protection configuration"""
    enabled: bool = Field(default=False, alias="ENABLE_CSRF")
    secret_key: Optional[str] = Field(default=None, alias="CSRF_SECRET_KEY")
    token_lifetime: int = Field(default=3600, alias="CSRF_TOKEN_LIFETIME")


class SMTPSettings(BaseSettings):
    """SMTP email configuration"""
    host: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    port: int = Field(default=587, alias="SMTP_PORT")
    username: Optional[str] = Field(default=None, alias="SMTP_USERNAME")
    password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    use_tls: bool = True
    from_email: Optional[str] = Field(default=None, alias="SMTP_FROM_EMAIL")
    from_name: str = Field(default="Tiger ID", alias="SMTP_FROM_NAME")
    enabled: bool = Field(default=False, alias="EMAIL_ENABLED")


class SentrySettings(BaseSettings):
    """Sentry error tracking configuration"""
    dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    environment: str = Field(default="production", alias="SENTRY_ENVIRONMENT")
    traces_sample_rate: float = 0.1
    profiles_sample_rate: float = 0.1


class ModalSettings(BaseSettings):
    """Modal serverless GPU configuration"""
    enabled: bool = Field(default=True, alias="MODAL_ENABLED")
    workspace: str = Field(default="ark-ntech", alias="MODAL_WORKSPACE")
    app_name: str = Field(default="tiger-id-models", alias="MODAL_APP_NAME")
    max_retries: int = Field(default=3, alias="MODAL_MAX_RETRIES")
    timeout: int = Field(default=120, alias="MODAL_TIMEOUT")
    queue_max_size: int = Field(default=100, alias="MODAL_QUEUE_MAX_SIZE")
    fallback_to_queue: bool = Field(default=True, alias="MODAL_FALLBACK_TO_QUEUE")

    @property
    def deployment_url(self) -> str:
        """Get the Modal deployment dashboard URL"""
        return f"https://modal.com/apps/{self.workspace}/main/deployed/{self.app_name}"




class OpenAISettings(BaseSettings):
    """OpenAI chat model configuration (DEPRECATED - not used, kept for compatibility)

    Note: This application uses Anthropic Claude for AI chat and analysis.
    OpenAI settings are preserved for potential future use but not actively used.
    """
    api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    max_tokens: int = Field(default=2048, alias="OPENAI_MAX_TOKENS")
    temperature: float = Field(default=0.7, alias="OPENAI_TEMPERATURE")


class GeminiSettings(BaseSettings):
    """Google Gemini chat model configuration (deprecated - use AnthropicSettings)"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    flash_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_FLASH_MODEL")
    pro_model: str = Field(default="gemini-2.5-pro", alias="GEMINI_PRO_MODEL")
    max_tokens: int = Field(default=8192, alias="GEMINI_MAX_TOKENS")
    temperature: float = Field(default=0.7, alias="GEMINI_TEMPERATURE")
    enable_search_grounding: bool = Field(default=True, alias="GEMINI_SEARCH_GROUNDING")


class AnthropicSettings(BaseSettings):
    """Anthropic Claude chat model configuration"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    fast_model: str = Field(default="claude-sonnet-4-5-20250929", alias="ANTHROPIC_FAST_MODEL")
    quality_model: str = Field(default="claude-opus-4-5-20251101", alias="ANTHROPIC_QUALITY_MODEL")
    max_tokens: int = Field(default=8192, alias="ANTHROPIC_MAX_TOKENS")
    temperature: float = Field(default=0.7, alias="ANTHROPIC_TEMPERATURE")


class FirecrawlSettings(BaseSettings):
    """Firecrawl configuration"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )
    
    api_key: Optional[str] = Field(default=None, alias="FIRECRAWL_API_KEY")
    timeout: int = 30
    search_enabled: bool = Field(default=True, alias="FIRECRAWL_SEARCH_ENABLED")


class PuppeteerSettings(BaseSettings):
    """Puppeteer browser automation configuration"""
    enabled: bool = Field(default=False, alias="PUPPETEER_ENABLED")
    headless: bool = Field(default=True, alias="PUPPETEER_HEADLESS")
    timeout: int = Field(default=30000, alias="PUPPETEER_TIMEOUT")  # milliseconds
    viewport_width: int = Field(default=1280, alias="PUPPETEER_VIEWPORT_WIDTH")
    viewport_height: int = Field(default=720, alias="PUPPETEER_VIEWPORT_HEIGHT")
    user_agent: str = Field(default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", alias="PUPPETEER_USER_AGENT")


class WebSearchSettings(BaseSettings):
    """Web search provider configuration"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )
    
    # Primary search provider
    provider: str = Field(default="firecrawl", alias="WEB_SEARCH_PROVIDER")  # firecrawl, serper, tavily, perplexity
    
    # Serper API (Google Search API)
    serper_api_key: Optional[str] = Field(default=None, alias="SERPER_API_KEY")
    
    # Tavily API
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    
    # Perplexity API
    perplexity_api_key: Optional[str] = Field(default=None, alias="PERPLEXITY_API_KEY")
    
    # Search settings
    default_limit: int = 10
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour


class MegaDetectorSettings(BaseSettings):
    """MegaDetector configuration"""
    path: str = Field(default="./data/models/md_v5a.0.0.pt", alias="MEGADETECTOR_MODEL_PATH")
    version: str = Field(default="v5", alias="MEGADETECTOR_VERSION")  # v4 or v5
    confidence_threshold: float = 0.5
    nms_threshold: float = 0.45
    enabled: bool = True


class RAPIDSettings(BaseSettings):
    """RAPID (Real-time Animal Pattern re-ID) configuration"""
    path: str = Field(default="./data/models/rapid/checkpoints/model.pth", alias="RAPID_MODEL_PATH")
    similarity_threshold: float = 0.8
    enabled: bool = Field(default=False, alias="RAPID_ENABLED")


class WildlifeToolsSettings(BaseSettings):
    """WildlifeTools configuration"""
    path: str = Field(default="./data/models/wildlife-tools/", alias="WILDLIFETOOLS_MODEL_PATH")
    model_type: str = Field(default="megadescriptor", alias="WILDLIFETOOLS_MODEL_TYPE")  # megadescriptor or wildfusion
    similarity_threshold: float = 0.8
    enabled: bool = Field(default=False, alias="WILDLIFETOOLS_ENABLED")


class CVWC2019Settings(BaseSettings):
    """CVWC2019 Re-ID configuration"""
    path: str = Field(default="./data/models/cvwc2019/checkpoints/model.pth", alias="CVWC2019_MODEL_PATH")
    similarity_threshold: float = 0.8
    enabled: bool = Field(default=False, alias="CVWC2019_ENABLED")


class DatasetSettings(BaseSettings):
    """Dataset configuration"""
    atrw_path: str = Field(default="./data/models/atrw/", alias="ATRW_DATASET_PATH")
    metawild_path: str = Field(default="./data/datasets/metawild/", alias="METAWILD_DATASET_PATH")
    wildlife_datasets_path: str = Field(default="./data/datasets/wildlife-datasets/", alias="WILDLIFE_DATASETS_PATH")
    individual_animal_reid_path: str = Field(default="./data/datasets/individual-animal-reid/", alias="INDIVIDUAL_ANIMAL_REID_PATH")


class ModelSettings(BaseSettings):
    """Model configuration"""
    # Detection models
    detection: MegaDetectorSettings = MegaDetectorSettings()
    
    # Re-ID models
    reid_path: str = Field(default="./data/models/tiger_reid_model.pth", alias="REID_MODEL_PATH")
    reid_similarity_threshold: float = 0.8
    reid_embedding_dim: int = 2048  # ResNet50 without classifier produces 2048-dim embeddings
    rapid: RAPIDSettings = RAPIDSettings()
    wildlife_tools: WildlifeToolsSettings = WildlifeToolsSettings()
    cvwc2019: CVWC2019Settings = CVWC2019Settings()
    
    # Other models
    pose_path: str = Field(default="./data/models/tiger_pose_model.pth", alias="POSE_MODEL_PATH")
    pose_enabled: bool = True
    
    # General settings
    device: str = Field(default="auto", alias="MODEL_DEVICE")  # "auto" will be resolved to "cuda" or "cpu" based on availability
    batch_size: int = Field(default=32, alias="BATCH_SIZE")
    preload_on_startup: bool = Field(default=False, alias="MODEL_PRELOAD_ON_STARTUP")
    cache_ttl: int = Field(default=3600, alias="MODEL_CACHE_TTL")
    max_batch_size: int = Field(default=50, alias="MAX_BATCH_SIZE")
    
    # Dataset settings
    datasets: DatasetSettings = DatasetSettings()


class AutoInvestigationSettings(BaseSettings):
    """Auto-investigation configuration"""
    enabled: bool = Field(default=False, alias="AUTO_INVESTIGATION_ENABLED")
    min_confidence: float = Field(default=0.8, alias="AUTO_INVESTIGATION_MIN_CONFIDENCE")
    priority_mapping: dict = {
        "high": 0.95,
        "medium": 0.8,
        "low": 0.7
    }


class DiscoverySettings(BaseSettings):
    """Continuous tiger discovery configuration"""
    enabled: bool = Field(default=False, alias="DISCOVERY_ENABLED")
    batch_size: int = Field(default=20, alias="DISCOVERY_BATCH_SIZE")
    interval_hours: int = Field(default=6, alias="DISCOVERY_INTERVAL_HOURS")
    max_facilities: int = Field(default=50, alias="DISCOVERY_MAX_FACILITIES")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )


# ============================================================================
# Subagent Pool Configuration
# ============================================================================
# Controls concurrent execution limits and timeouts for different subagent types

SUBAGENT_POOLS = {
    "ml_inference": {
        "max_concurrent": 6,  # One per ReID model
        "timeout": 120,       # 2 minutes max
        "priority": 1,        # Higher priority
    },
    "research": {
        "max_concurrent": 5,
        "timeout": 60,        # 1 minute max
        "priority": 2,
    },
    "report_generation": {
        "max_concurrent": 4,  # One per audience type
        "timeout": 45,
        "priority": 3,
    },
    "image_processing": {
        "max_concurrent": 3,
        "timeout": 30,
        "priority": 1,
    },
    "web_crawl": {
        "max_concurrent": 10,
        "timeout": 30,
        "priority": 4,
    },
}

# Model-specific configuration for stripe analysis
REID_MODELS = {
    "wildlife_tools": {"weight": 0.40, "embedding_dim": 1536, "calibration_temp": 1.0},
    "cvwc2019_reid": {"weight": 0.30, "embedding_dim": 2048, "calibration_temp": 0.85},
    "transreid": {"weight": 0.20, "embedding_dim": 768, "calibration_temp": 1.1},
    "megadescriptor_b": {"weight": 0.15, "embedding_dim": 1024, "calibration_temp": 1.0},
    "tiger_reid": {"weight": 0.10, "embedding_dim": 2048, "calibration_temp": 0.9},
    "rapid_reid": {"weight": 0.05, "embedding_dim": 2048, "calibration_temp": 0.95},
}

# Subagent retry configuration
SUBAGENT_RETRY_CONFIG = {
    "max_retries": 3,
    "retry_delay": 1.0,  # seconds
    "exponential_backoff": True,
}


def get_subagent_pool_config(pool_name: str) -> dict:
    """
    Get configuration for a subagent pool.

    Args:
        pool_name: Name of the subagent pool (e.g., 'ml_inference', 'research')

    Returns:
        Dictionary with max_concurrent, timeout, and priority settings.
        Returns default values if pool_name is not found.
    """
    return SUBAGENT_POOLS.get(pool_name, {
        "max_concurrent": 2,
        "timeout": 60,
        "priority": 5,
    })


class ExternalAPISettings(BaseSettings):
    """External API configuration"""
    usda_api_key: Optional[str] = Field(default=None, alias="USDA_API_KEY")
    usda_enabled: bool = False
    usda_base_url: str = "https://www.aphis.usda.gov"
    
    cites_api_key: Optional[str] = Field(default=None, alias="CITES_API_KEY")
    cites_enabled: bool = False
    cites_base_url: str = "https://trade.cites.org/api"
    
    usfws_api_key: Optional[str] = Field(default=None, alias="USFWS_API_KEY")
    usfws_enabled: bool = False
    usfws_base_url: str = "https://api.fws.gov"
    
    youtube_api_key: Optional[str] = Field(default=None, alias="YOUTUBE_API_KEY")
    youtube_enabled: bool = False
    
    meta_access_token: Optional[str] = Field(default=None, alias="META_ACCESS_TOKEN")
    meta_app_id: Optional[str] = Field(default=None, alias="META_APP_ID")
    meta_app_secret: Optional[str] = Field(default=None, alias="META_APP_SECRET")
    meta_enabled: bool = False


class AppSettings(BaseSettings):
    """Application settings"""
    
    # App metadata
    name: str = "Tiger Trafficking Investigation System"
    version: str = "1.0.0"
    environment: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    frontend_url: str = Field(default="http://localhost:8501", alias="FRONTEND_URL")
    use_langgraph: bool = Field(default=False, alias="USE_LANGGRAPH")
    
    # Sub-settings
    database: DatabaseSettings = DatabaseSettings()
    storage: StorageSettings = StorageSettings()
    authentication: AuthenticationSettings = AuthenticationSettings()
    csrf: CSRFSettings = CSRFSettings()
    smtp: SMTPSettings = SMTPSettings()
    sentry: SentrySettings = SentrySettings()
    modal: ModalSettings = ModalSettings()
    openai: OpenAISettings = OpenAISettings()
    gemini: GeminiSettings = GeminiSettings()
    anthropic: AnthropicSettings = AnthropicSettings()
    firecrawl: FirecrawlSettings = FirecrawlSettings()
    puppeteer: PuppeteerSettings = PuppeteerSettings()
    web_search: WebSearchSettings = WebSearchSettings()
    models: ModelSettings = ModelSettings()
    datasets: DatasetSettings = DatasetSettings()
    auto_investigation: AutoInvestigationSettings = AutoInvestigationSettings()
    discovery: DiscoverySettings = DiscoverySettings()
    external_apis: ExternalAPISettings = ExternalAPISettings()
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="allow"
    )
    
    @model_validator(mode='after')
    def validate_secret_key(self):
        # Validate secret key length only in production
        if self.environment == 'production':
            if len(self.secret_key) < 32:
                raise ValueError('SECRET_KEY must be at least 32 characters long in production')
            if self.secret_key == 'change-me-in-production':
                raise ValueError('SECRET_KEY must be changed in production')
            if len(self.authentication.jwt_secret_key) < 32:
                raise ValueError('JWT_SECRET_KEY must be at least 32 characters long in production')
            if self.authentication.jwt_secret_key == 'change-me-in-production':
                raise ValueError('JWT_SECRET_KEY must be changed in production')
        return self
    
    @classmethod
    def from_yaml(cls, yaml_path: Optional[Path] = None) -> "AppSettings":
        """
        Load settings from YAML file, overriding with environment variables
        
        Args:
            yaml_path: Path to YAML config file (default: config/settings.yaml)
        
        Returns:
            AppSettings instance
        """
        if yaml_path is None:
            yaml_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        
        # Load YAML if exists (for reference, env vars still take precedence)
        yaml_config = {}
        if yaml_path.exists():
            try:
                with open(yaml_path, "r") as f:
                    yaml_config = yaml.safe_load(f) or {}
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to load YAML config: {e}")
        
        # Create settings instance - Pydantic will load from .env and env vars
        # Environment variables take precedence over YAML
        settings = cls()
        
        return settings


# Global settings instance
_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """Get global settings instance (singleton)"""
    global _settings
    if _settings is None:
        try:
            _settings = AppSettings.from_yaml()
        except ValidationError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Configuration validation failed: {e}")
            raise ValueError(f"Invalid configuration: {e}") from e
    return _settings


def reload_settings():
    """Reload settings (useful for testing)"""
    global _settings
    _settings = None
    return get_settings()

