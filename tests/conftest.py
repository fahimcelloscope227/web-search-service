from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_search_service
from app.main import app
from app.schemas.search import FetchStatus, SearchHit
from app.services.content_extractor import ExtractedContent
from app.services.providers.base import SearchProvider
from app.services.search_service import SearchService


class FakeProvider(SearchProvider):
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    async def search(self, query: str, limit: int) -> list[SearchHit]:
        self.calls.append((query, limit))
        return [
            SearchHit(title=f"Result {i}", url=f"https://example.com/{i}", snippet=f"snippet {i}")
            for i in range(1, limit + 1)
        ]


class FakeExtractor:
    async def extract(self, url: str) -> ExtractedContent:
        if url.endswith("/2"):
            return ExtractedContent(status=FetchStatus.FAILED, error="timeout")
        return ExtractedContent(status=FetchStatus.OK, text=f"content of {url}", word_count=3)


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
async def client(fake_provider: FakeProvider) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_search_service] = lambda: SearchService(
        fake_provider,
        FakeExtractor(),  # type: ignore[arg-type]
        max_concurrency=5,
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
