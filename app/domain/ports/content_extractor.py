from typing import Protocol

from app.domain.models.extracted_content import ExtractedContent


class ContentExtractor(Protocol):
    async def extract(self, url: str) -> ExtractedContent: ...
