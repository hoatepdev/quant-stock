"""Configuration management using pydantic-settings."""
from functools import lru_cache
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=5432)
    DB_NAME: str = Field(default="vietnam_quant")
    DB_USER: str = Field(default="postgres")
    DB_PASSWORD: str = Field(default="postgres")
    DATABASE_URL: str = Field(default="")

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_URL: str = Field(default="")

    # API Keys
    SSI_API_KEY: str = Field(default="")
    SSI_SECRET_KEY: str = Field(default="")
    DNSE_API_KEY: str = Field(default="")
    DNSE_SECRET_KEY: str = Field(default="")

    # Application Configuration
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    API_WORKERS: int = Field(default=4)

    # Rate Limiting
    SSI_RATE_LIMIT_REQUESTS: int = Field(default=100)
    SSI_RATE_LIMIT_PERIOD: int = Field(default=60)
    API_RATE_LIMIT_REQUESTS: int = Field(default=1000)
    API_RATE_LIMIT_PERIOD: int = Field(default=60)

    # Data Configuration
    DATA_SOURCE: str = Field(default="vnstock")
    BACKFILL_START_DATE: str = Field(default="2020-01-01")
    BACKFILL_BATCH_SIZE: int = Field(default=10)
    MAX_RETRIES: int = Field(default=3)
    RETRY_BACKOFF_FACTOR: float = Field(default=2.0)

    # Cache Configuration
    CACHE_TTL_SECONDS: int = Field(default=300)
    PRICE_DATA_CACHE_TTL: int = Field(default=3600)
    FACTOR_CACHE_TTL: int = Field(default=1800)

    # Market Configuration
    VIETNAM_EXCHANGES: Union[str, List[str]] = Field(default="HOSE,HNX,UPCOM")
    DEFAULT_EXCHANGE: str = Field(default="HOSE")
    TRADING_HOURS_START: str = Field(default="09:00")
    TRADING_HOURS_END: str = Field(default="15:00")

    # Security
    API_SECRET_KEY: str = Field(default="your_secret_key_here")
    ALLOWED_ORIGINS: Union[str, List[str]] = Field(default="http://localhost:3000")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: str, info) -> str:  # type: ignore
        """Construct DATABASE_URL if not provided."""
        if v:
            return v
        values = info.data
        return (
            f"postgresql://{values.get('DB_USER')}:{values.get('DB_PASSWORD')}"
            f"@{values.get('DB_HOST')}:{values.get('DB_PORT')}/{values.get('DB_NAME')}"
        )

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, v: str, info) -> str:  # type: ignore
        """Construct REDIS_URL if not provided."""
        if v:
            return v
        values = info.data
        return (
            f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}"
            f"/{values.get('REDIS_DB')}"
        )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse ALLOWED_ORIGINS from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("VIETNAM_EXCHANGES", mode="before")
    @classmethod
    def parse_exchanges(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse VIETNAM_EXCHANGES from comma-separated string or list."""
        if isinstance(v, str):
            return [exchange.strip() for exchange in v.split(",") if exchange.strip()]
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings instance
    """
    return Settings()
