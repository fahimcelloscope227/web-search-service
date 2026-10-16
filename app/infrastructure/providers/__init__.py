import httpx

from app.core.config import SearchProviderName, Settings
from app.domain.exceptions import ProviderConfigurationError
from app.domain.ports import SearchProvider
from app.infrastructure.providers.duckduckgo import DuckDuckGoProvider
from app.infrastructure.providers.google_cse import GoogleCSEProvider
from app.infrastructure.providers.serper import SerperProvider

__all__ = ["build_provider"]


def build_provider(settings: Settings, client: httpx.AsyncClient) -> SearchProvider:
    timeout = settings.search_timeout_seconds
    match settings.search_provider:
        case SearchProviderName.SERPER:
            if not settings.serper_api_key:
                raise ProviderConfigurationError("SERPER_API_KEY is required for the 'serper' provider")
            return SerperProvider(client, timeout, settings.serper_api_key.get_secret_value())
        case SearchProviderName.GOOGLE_CSE:
            if not (settings.google_api_key and settings.google_cse_id):
                raise ProviderConfigurationError(
                    "GOOGLE_API_KEY and GOOGLE_CSE_ID are required for the 'google_cse' provider"
                )
            return GoogleCSEProvider(
                client, timeout, settings.google_api_key.get_secret_value(), settings.google_cse_id
            )
        case SearchProviderName.DUCKDUCKGO:
            return DuckDuckGoProvider(client, timeout, settings.user_agent)
