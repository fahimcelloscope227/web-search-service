from enum import StrEnum


class FetchStatus(StrEnum):
    OK = "ok"
    EMPTY = "empty"  # page loaded but no readable main content
    FAILED = "failed"  # network error, timeout, non-2xx, non-HTML
