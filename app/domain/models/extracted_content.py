from dataclasses import dataclass

from app.domain.models.fetch_status import FetchStatus


@dataclass(frozen=True, slots=True)
class ExtractedContent:
    status: FetchStatus
    text: str | None = None
    word_count: int = 0
    truncated: bool = False
    error: str | None = None
