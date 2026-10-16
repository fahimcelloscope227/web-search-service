from pydantic import BaseModel, Field, HttpUrl

from app.domain.models.fetch_status import FetchStatus


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
