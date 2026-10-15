import asyncio
import logging
from dataclasses import dataclass

import httpx
import trafilatura

from app.schemas.search import FetchStatus

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ExtractedContent:
    status: FetchStatus
    text: str | None = None
    word_count: int = 0
    truncated: bool = False
    error: str | None = None


class ContentExtractor:
    """Downloads a page and pulls out its main readable text (no nav, ads, boilerplate)."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        timeout: float,
        max_chars: int,
        max_bytes: int,
        user_agent: str,
    ) -> None:
        self._client = client
        self._timeout = timeout
        self._max_chars = max_chars
        self._max_bytes = max_bytes
        self._headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def extract(self, url: str) -> ExtractedContent:
        try:
            html = await self._download(url)
        except (httpx.HTTPError, ValueError) as exc:
            logger.info("Fetch failed for %s: %s", url, exc)
            return ExtractedContent(status=FetchStatus.FAILED, error=str(exc) or type(exc).__name__)

        # trafilatura is CPU-bound and synchronous; keep it off the event loop.
        text = await asyncio.to_thread(trafilatura.extract, html, url=url, include_comments=False, include_tables=False)
        if not text:
            return ExtractedContent(status=FetchStatus.EMPTY)

        word_count = len(text.split())
        truncated = len(text) > self._max_chars
        if truncated:
            text = text[: self._max_chars].rsplit(" ", 1)[0] + "…"
        return ExtractedContent(status=FetchStatus.OK, text=text, word_count=word_count, truncated=truncated)

    async def _download(self, url: str) -> str:
        async with self._client.stream(
            "GET", url, headers=self._headers, timeout=self._timeout, follow_redirects=True
        ) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "html" not in content_type:
                raise ValueError(f"Unsupported content type: {content_type or 'unknown'}")

            chunks: list[bytes] = []
            size = 0
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > self._max_bytes:
                    break  # enough to extract from; don't pull huge pages into memory
                chunks.append(chunk)
            encoding = response.encoding or "utf-8"
        return b"".join(chunks).decode(encoding, errors="replace")
