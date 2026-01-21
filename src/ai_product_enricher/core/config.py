"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Zhipu AI API Configuration
    zhipuai_api_key: str = Field(
        ...,
        description="Zhipu AI API key",
    )
    zhipuai_base_url: str = Field(
        default="https://api.z.ai/api/coding/paas/v4",
        description="Zhipu AI API base URL",
    )
    zhipuai_model: str = Field(
        default="GLM-4.7",
        description="Zhipu AI model to use",
    )
    zhipuai_timeout: int = Field(
        default=60,
        ge=10,
        le=300,
        description="API request timeout in seconds",
    )
    zhipuai_max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of API retry attempts",
    )

    # Cloud.ru (GigaChat) API Configuration
    cloudru_api_key: str | None = Field(
        default=None,
        description="Cloud.ru API key (optional, for Russian products)",
    )
    cloudru_base_url: str = Field(
        default="https://foundation-models.api.cloud.ru/v1",
        description="Cloud.ru API base URL",
    )
    cloudru_model: str = Field(
        default="ai-sage/GigaChat3-10B-A1.8B",
        description="Cloud.ru model to use (GigaChat)",
    )
    cloudru_timeout: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Cloud.ru API request timeout in seconds",
    )

    # Application Settings
    app_env: Literal["development", "staging", "production"] = Field(
        default="production",
        description="Application environment",
    )
    app_debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    docs_enabled: bool = Field(
        default=True,
        description="Enable API documentation (Swagger/ReDoc)",
    )
    app_host: str = Field(
        default="0.0.0.0",
        description="Application host",
    )
    app_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Application port",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    # Cache Settings
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Cache TTL in seconds",
    )
    cache_max_size: int = Field(
        default=1000,
        ge=100,
        le=100000,
        description="Maximum cache size",
    )

    # Rate Limiting
    rate_limit_requests: int = Field(
        default=100,
        ge=1,
        description="Maximum requests per period",
    )
    rate_limit_period: int = Field(
        default=60,
        ge=1,
        description="Rate limit period in seconds",
    )

    # Batch Processing
    batch_max_concurrent: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent batch requests",
    )
    batch_max_products: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum products per batch request",
    )

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
