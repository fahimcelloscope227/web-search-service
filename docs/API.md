# API Reference

HTTP API for `web-search-service`. Searches the web for a keyword, fetches the top result pages
concurrently, and returns each page's main readable text.

- **Base URL (local):** `http://localhost:8000`
- **Content type:** all responses are `application/json`
- **Interactive docs:** `GET /docs` (Swagger UI) · `GET /openapi.json` (raw schema)

---

## `GET /health`

Liveness probe. Also reports the active search provider.

**Request**

```bash
curl http://localhost:8000/health
```

**200 response**

```json
{ "status": "ok", "provider": "duckduckgo" }
```

| Field | Type | Description |
|---|---|---|
| `status` | string | Always `"ok"` when the process is serving. |
| `provider` | string | Active backend: `serper` \| `google_cse` \| `duckduckgo`. |

---

## `GET /api/v1/search`

Search the web and return the top pages with extracted content.

### Query parameters

| Name | Type | Required | Constraints | Default | Description |
|---|---|---|---|---|---|
| `q` | string | yes | 1–256 chars, not blank after trimming | — | Keyword or phrase to search. |
| `limit` | integer | no | 1–10 | `5` | Number of result pages to fetch and extract. |

Notes:
- `q` is trimmed; a value that is only whitespace is rejected with `422`.
- `limit` is additionally capped server-side by `MAX_RESULT_LIMIT` (default `10`).

### Request

```bash
curl "http://localhost:8000/api/v1/search?q=fastapi%20best%20practices&limit=3"
```

### 200 response

```json
{
  "query": "fastapi best practices",
  "provider": "serper",
  "total_results": 3,
  "took_ms": 4226,
  "searched_at": "2026-10-16T09:12:03Z",
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

### Response body

| Field | Type | Description |
|---|---|---|
| `query` | string | The trimmed query that was searched. |
| `provider` | string | Backend that produced the results. |
| `total_results` | integer | Number of items in `results`. |
| `took_ms` | integer | Server-side wall time for the whole request, in milliseconds. |
| `searched_at` | string (ISO 8601, UTC) | When the search ran. |
| `results` | array<SearchResult> | Ranked results. |

#### `SearchResult`

| Field | Type | Description |
|---|---|---|
| `rank` | integer | 1-based position in the results. |
| `title` | string | Result title from the provider. |
| `url` | string (URL) | Result URL. |
| `snippet` | string \| null | Provider-supplied snippet, if any. |
| `content` | string \| null | Extracted main text. `null` when `fetch_status` is not `ok`. |
| `word_count` | integer | Word count of `content` (`0` when there is none). |
| `truncated` | boolean | `true` if `content` was cut to `MAX_CONTENT_CHARS` (ends with `…`). |
| `fetch_status` | string | `ok` \| `empty` \| `failed` — see below. |
| `error` | string \| null | Failure reason when `fetch_status` is `failed`. |

#### `fetch_status` values

| Value | Meaning |
|---|---|
| `ok` | Page fetched and readable text extracted. |
| `empty` | Page loaded but no main content could be extracted. |
| `failed` | Fetch failed: network error, timeout, non-2xx, or non-HTML. See `error`. |

A per-result failure does **not** fail the request — one bad page is reported as a `failed` result
alongside the successful ones.

---

## Errors

### Service errors

Failures originating from the service (not input validation) use a consistent envelope:

```json
{ "error": { "code": "search_provider_error", "message": "Serper request failed: ..." } }
```

| HTTP status | `code` | When |
|---|---|---|
| `502 Bad Gateway` | `search_provider_error` | The upstream search provider failed or rate-limited the request. |
| `500 Internal Server Error` | `provider_misconfigured` | Selected provider is missing required credentials (e.g. `SERPER_API_KEY`). |
| `500 Internal Server Error` | `internal_error` | Unclassified service error. |

### Validation errors (`422 Unprocessable Entity`)

Parameter validation failures use FastAPI's standard format:

```json
{
  "detail": [
    { "type": "string_too_short", "loc": ["query", "q"], "msg": "String should have at least 1 character" }
  ]
}
```

A blank-after-trim `q` returns a simpler message:

```json
{ "detail": "Query must not be blank" }
```

Triggers: missing `q`, `q` shorter than 1 or longer than 256 chars, `q` only whitespace, or `limit`
outside `1–10`.

---

## Providers

Selected via the `SEARCH_PROVIDER` environment variable.

| Provider | Results from | Requires |
|---|---|---|
| `serper` | Google (via serper.dev) | `SERPER_API_KEY` |
| `google_cse` | Google Programmable Search | `GOOGLE_API_KEY` + `GOOGLE_CSE_ID` |
| `duckduckgo` (default) | DuckDuckGo | nothing |

Relevant tuning env vars: `DEFAULT_RESULT_LIMIT`, `MAX_RESULT_LIMIT`, `SEARCH_TIMEOUT_SECONDS`,
`FETCH_TIMEOUT_SECONDS`, `MAX_CONCURRENT_FETCHES`, `MAX_CONTENT_CHARS`, `MAX_PAGE_BYTES`. See
`app/core/config/settings.py` for the full list and defaults.
