import httpx

from app.core.exceptions import SearchProviderError
from app.schemas.search import SearchHit
from app.services.providers.base import SearchProvider


class SerperProvider(SearchProvider):
    """Google search results via https://serper.dev."""

    name = "serper"
    _endpoint = "https://google.serper.dev/search"

    def __init__(self, client: httpx.AsyncClient, timeout: float, api_key: str) -> None:
        super().__init__(client, timeout)
        self._api_key = api_key

    async def search(self, query: str, limit: int) -> list[SearchHit]:
        try:
            response = await self._client.post(
                self._endpoint,
                json={"q": query, "num": limit},
                headers={"X-API-KEY": self._api_key},
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SearchProviderError(f"Serper request failed: {exc}") from exc

        organic = response.json().get("organic", [])
        return [
            SearchHit(title=item.get("title", ""), url=item["link"], snippet=item.get("snippet"))
            for item in organic[:limit]
            if item.get("link")
        ]
