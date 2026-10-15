from abc import ABC, abstractmethod

import httpx

from app.schemas.search import SearchHit


class SearchProvider(ABC):
    """Contract every search backend implements."""

    name: str

    def __init__(self, client: httpx.AsyncClient, timeout: float) -> None:
        self._client = client
        self._timeout = timeout

    @abstractmethod
    async def search(self, query: str, limit: int) -> list[SearchHit]:
        """Return up to `limit` organic results for `query`, in ranked order."""
