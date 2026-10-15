import httpx

from app.core.exceptions import SearchProviderError
from app.schemas.search import SearchHit
from app.services.providers.base import SearchProvider


class GoogleCSEProvider(SearchProvider):
    """Google Programmable Search Engine (Custom Search JSON API)."""

    name = "google_cse"
    _endpoint = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, client: httpx.AsyncClient, timeout: float, api_key: str, cse_id: str) -> None:
        super().__init__(client, timeout)
        self._api_key = api_key
        self._cse_id = cse_id

    async def search(self, query: str, limit: int) -> list[SearchHit]:
        try:
            response = await self._client.get(
                self._endpoint,
                # The API caps `num` at 10.
                params={"key": self._api_key, "cx": self._cse_id, "q": query, "num": min(limit, 10)},
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            # Don't leak the API key, which is part of the request URL.
            raise SearchProviderError(f"Google CSE request failed ({type(exc).__name__})") from exc

        items = response.json().get("items", [])
        return [
            SearchHit(title=item.get("title", ""), url=item["link"], snippet=item.get("snippet"))
            for item in items[:limit]
            if item.get("link")
        ]
