# web-search-service

FastAPI microservice that takes a keyword, searches the web, fetches the top 5 result pages concurrently, and returns each page's main readable content (boilerplate, nav and ads stripped via `trafilatura`).

## Quick start (Docker)

```bash
cp .env.example .env          # pick a provider, add keys if needed
docker compose up --build -d
curl "http://localhost:8000/api/v1/search?q=fastapi%20best%20practices"
```

Interactive docs: http://localhost:8000/docs · Health: http://localhost:8000/health

## API

`GET /api/v1/search?q=<keyword>&limit=<1-10, default 5>`

```json
{
  "query": "fastapi best practices",
  "provider": "serper",
  "total_results": 5,
  "took_ms": 4226,
  "searched_at": "2026-10-15T09:12:03Z",
  "results": [
    {
      "rank": 1,
      "title": "FastAPI Best Practices",
      "url": "https://github.com/zhanymkanov/fastapi-best-practices",
      "snippet": "Opinionated list of best practices...",
      "content": "Opinionated list of best practices and conventions...",
      "word_count": 3473,
      "truncated": true,
      "fetch_status": "ok",
      "error": null
    }
  ]
}
```

`fetch_status` is per result: `ok`, `empty` (page loaded, no readable text), or `failed` (timeout, non-2xx, non-HTML; see `error`). One bad page never fails the whole request. Errors from the search provider itself return `502` with `{"error": {"code", "message"}}`.

## Search providers

Set `SEARCH_PROVIDER` in `.env`:

| Provider | Results from | Needs |
|---|---|---|
| `serper` (recommended for Google) | Google | `SERPER_API_KEY` from https://serper.dev |
| `google_cse` | Google Programmable Search | `GOOGLE_API_KEY` + `GOOGLE_CSE_ID` |
| `duckduckgo` (default) | DuckDuckGo | nothing; good for local dev |

The service doesn't scrape Google's result pages directly, because that breaks against Google's bot detection and goes against its terms of service. To add another backend, subclass `SearchProvider` in `app/services/providers/` and register it in `build_provider`.

## Configuration

All settings are env vars (see `app/core/config.py`): `DEFAULT_RESULT_LIMIT`, `FETCH_TIMEOUT_SECONDS`, `SEARCH_TIMEOUT_SECONDS`, `MAX_CONTENT_CHARS`, `MAX_PAGE_BYTES`, `MAX_CONCURRENT_FETCHES`, `LOG_LEVEL`, `WEB_CONCURRENCY` (uvicorn workers).

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest
ruff check . && ruff format --check .
```

## Layout

```
app/
├── main.py                    # app factory, lifespan (shared pooled httpx client)
├── core/                      # settings, logging, exceptions → JSON error responses
├── api/deps.py                # dependency injection wiring
├── api/v1/routes/search.py    # HTTP endpoint (validation only)
├── schemas/search.py          # Pydantic request/response models
└── services/
    ├── search_service.py      # orchestrates search + concurrent fetching
    ├── content_extractor.py   # download (size/type-guarded) + main-text extraction
    └── providers/             # pluggable search backends
tests/                         # API + parser tests with fake provider/extractor
```
