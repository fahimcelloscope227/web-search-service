from enum import StrEnum


class SearchProviderName(StrEnum):
    SERPER = "serper"  # Google results via serper.dev
    GOOGLE_CSE = "google_cse"  # Google Programmable Search JSON API
    DUCKDUCKGO = "duckduckgo"  # keyless fallback, handy for local dev
