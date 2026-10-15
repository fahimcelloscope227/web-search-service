from urllib.parse import parse_qs, unquote, urlparse

import httpx
from selectolax.parser import HTMLParser

from app.core.exceptions import SearchProviderError
from app.schemas.search import SearchHit
from app.services.providers.base import SearchProvider


class DuckDuckGoProvider(SearchProvider):
    """Keyless provider using DuckDuckGo's HTML endpoint. Good for local dev; use Serper/CSE in production."""

    name = "duckduckgo"
    _endpoint = "https://html.duckduckgo.com/html/"

    def __init__(self, client: httpx.AsyncClient, timeout: float, user_agent: str) -> None:
        super().__init__(client, timeout)
        self._user_agent = user_agent

    async def search(self, query: str, limit: int) -> list[SearchHit]:
        try:
            response = await self._client.post(
                self._endpoint,
                data={"q": query},
                headers={"User-Agent": self._user_agent},
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SearchProviderError(f"DuckDuckGo request failed: {exc}") from exc

        # DDG answers bot challenges with 202 instead of an error status.
        if response.status_code != 200:
            raise SearchProviderError(f"DuckDuckGo rate-limited the request (HTTP {response.status_code})")
        return self._parse(response.text, limit)

    @staticmethod
    def _parse(html: str, limit: int) -> list[SearchHit]:
        hits: list[SearchHit] = []
        for node in HTMLParser(html).css("div.result:not(.result--ad)"):
            link = node.css_first("a.result__a")
            if link is None:
                continue
            url = _unwrap_redirect(link.attributes.get("href") or "")
            if not url.startswith(("http://", "https://")):
                continue
            snippet = node.css_first(".result__snippet")
            hits.append(
                SearchHit(
                    title=link.text(strip=True),
                    url=url,
                    snippet=snippet.text(strip=True) if snippet else None,
                )
            )
            if len(hits) >= limit:
                break
        return hits


def _unwrap_redirect(href: str) -> str:
    """DDG wraps links as //duckduckgo.com/l/?uddg=<encoded-url>."""
    parsed = urlparse(href)
    if "uddg" in (query := parse_qs(parsed.query)):
        return unquote(query["uddg"][0])
    return href
