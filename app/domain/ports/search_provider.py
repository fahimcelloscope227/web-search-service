from abc import ABC, abstractmethod

from app.domain.models.search_hit import SearchHit


class SearchProvider(ABC):
    """Contract every search backend implements."""

    name: str

    @abstractmethod
    async def search(self, query: str, limit: int) -> list[SearchHit]:
        """Return up to `limit` organic results for `query`, in ranked order."""
