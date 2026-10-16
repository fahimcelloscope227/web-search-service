import asyncio
import logging
import time
from datetime import UTC, datetime

from app.domain.models import SearchHit, SearchResponse, SearchResult
from app.domain.ports import ContentExtractor, SearchProvider

logger = logging.getLogger(__name__)


class SearchService:
    """Searches the web for a keyword, then fetches and extracts the top result pages concurrently."""

    def __init__(self, provider: SearchProvider, extractor: ContentExtractor, max_concurrency: int) -> None:
        self._provider = provider
        self._extractor = extractor
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def search(self, query: str, limit: int) -> SearchResponse:
        started = time.perf_counter()
        hits = await self._provider.search(query, limit)
        logger.info("Provider %s returned %d hits for %r", self._provider.name, len(hits), query)

        results = await asyncio.gather(*(self._enrich(rank, hit) for rank, hit in enumerate(hits, start=1)))
        return SearchResponse(
            query=query,
            provider=self._provider.name,
            total_results=len(results),
            results=list(results),
            took_ms=int((time.perf_counter() - started) * 1000),
            searched_at=datetime.now(UTC),
        )

    async def _enrich(self, rank: int, hit: SearchHit) -> SearchResult:
        async with self._semaphore:
            extracted = await self._extractor.extract(str(hit.url))
        return SearchResult(
            rank=rank,
            title=hit.title,
            url=hit.url,
            snippet=hit.snippet,
            content=extracted.text,
            word_count=extracted.word_count,
            truncated=extracted.truncated,
            fetch_status=extracted.status,
            error=extracted.error,
        )
