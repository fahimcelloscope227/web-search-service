from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.services.content_extractor import ContentExtractor
from app.services.providers import build_provider
from app.services.search_service import SearchService

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_search_service(request: Request, settings: SettingsDep) -> SearchService:
    # One pooled HTTP client per app, created in the lifespan handler.
    client = request.app.state.http_client
    extractor = ContentExtractor(
        client,
        timeout=settings.fetch_timeout_seconds,
        max_chars=settings.max_content_chars,
        max_bytes=settings.max_page_bytes,
        user_agent=settings.user_agent,
    )
    return SearchService(build_provider(settings, client), extractor, settings.max_concurrent_fetches)


SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
