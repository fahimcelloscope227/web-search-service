from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class SearchHit(BaseModel):
    """A raw result from a search provider, before its page is fetched."""

    title: str
    url: HttpUrl
    snippet: str | None = None


class FetchStatus(StrEnum):
    OK = "ok"
    EMPTY = "empty"  # page loaded but no readable main content
    FAILED = "failed"  # network error, timeout, non-2xx, non-HTML


class SearchResult(BaseModel):
    rank: int = Field(description="1-based position in the search results")
    title: str
    url: HttpUrl
    snippet: str | None = None
    content: str | None = Field(default=None, description="Main readable text extracted from the page")
    word_count: int = 0
    truncated: bool = False
    fetch_status: FetchStatus
    error: str | None = None


class SearchResponse(BaseModel):
    query: str
    provider: str
    total_results: int
    results: list[SearchResult]
    took_ms: int
    searched_at: datetime
