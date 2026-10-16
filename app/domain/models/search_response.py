from datetime import datetime

from pydantic import BaseModel

from app.domain.models.search_result import SearchResult


class SearchResponse(BaseModel):
    query: str
    provider: str
    total_results: int
    results: list[SearchResult]
    took_ms: int
    searched_at: datetime
