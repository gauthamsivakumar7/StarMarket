from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/starmarket"
    database_url_async: Optional[str] = None

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # App
    starting_cash: float = 10000.0
    admin_enabled: bool = True
    seed_on_startup: bool = False

    # OpenRouter (LLM provider for NL strategy translation)
    openrouter_api_key: str = ""
    openrouter_model: str = "deepseek/deepseek-v4-flash-0731"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_timeout_seconds: float = 30.0

    # Market data
    market_data_cache_ttl_seconds: int = 60

    @property
    def async_database_url(self) -> str:
        if self.database_url_async:
            return self.database_url_async
        # Convert postgresql:// to postgresql+asyncpg://
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        url = self.database_url
        if "asyncpg" in url:
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
        # Be explicit about the driver: SQLAlchemy's default dialect for a bare
        # "postgresql://" URL depends on the installed SQLAlchemy version, and
        # this project pins psycopg2-binary (not psycopg v3).
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
