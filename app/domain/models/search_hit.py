from pydantic import BaseModel, HttpUrl


class SearchHit(BaseModel):
    """A raw result from a search provider, before its page is fetched."""

    title: str
    url: HttpUrl
    snippet: str | None = None
