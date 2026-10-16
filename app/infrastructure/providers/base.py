import httpx

from app.domain.ports import SearchProvider


class HttpSearchProvider(SearchProvider):
    """Base for providers that talk to an HTTP search backend over a shared client."""

    def __init__(self, client: httpx.AsyncClient, timeout: float) -> None:
        self._client = client
        self._timeout = timeout
