"""
Configuration management for FPL MCP Server using pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # FPL API Configuration
    fpl_base_url: str = "https://fantasy.premierleague.com"
    fpl_api_timeout: int = 30

    # Cache Configuration (in seconds)
    bootstrap_cache_ttl: int = 14400  # 4 hours
    fixtures_cache_ttl: int = 14400  # 4 hours
    player_summary_cache_ttl: int = 300  # 5 minutes

    # Logging Configuration
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="FPL_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()
