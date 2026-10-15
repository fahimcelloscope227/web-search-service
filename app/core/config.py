from enum import StrEnum
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SearchProviderName(StrEnum):
    SERPER = "serper"  # Google results via serper.dev
    GOOGLE_CSE = "google_cse"  # Google Programmable Search JSON API
    DUCKDUCKGO = "duckduckgo"  # keyless fallback, handy for local dev


class Settings(BaseSettings):
    """Application settings, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "web-search-service"
    environment: str = "local"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    search_provider: SearchProviderName = SearchProviderName.DUCKDUCKGO
    serper_api_key: SecretStr | None = None
    google_api_key: SecretStr | None = None
    google_cse_id: str | None = None

    default_result_limit: int = Field(default=5, ge=1, le=10)
    max_result_limit: int = Field(default=10, ge=1, le=10)

    search_timeout_seconds: float = 10.0
    fetch_timeout_seconds: float = 10.0
    max_concurrent_fetches: int = 5
    max_content_chars: int = 5000
    max_page_bytes: int = 3_000_000
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
