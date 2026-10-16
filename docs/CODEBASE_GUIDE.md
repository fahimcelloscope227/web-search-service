# Codebase Guide

A tour of this service for someone who knows Python but is new to FastAPI. Python-level
things are stated briefly; FastAPI-specific ideas get the attention.

## 1. What the service does

One endpoint: `GET /api/v1/search?q=<keyword>&limit=<n>`.

1. Ask a **search provider** (DuckDuckGo / Serper / Google CSE) for the top result URLs.
2. **Fetch each page concurrently** and extract its main readable text (strip nav/ads) with `trafilatura`.
3. Return a JSON list of results, each with its content and a per-result `fetch_status`.

One bad page never fails the whole request; a failure from the *search provider itself* returns `502`.

## 2. The request flow (follow one request through the layers)

```
HTTP GET /api/v1/search
   │
   ▼
api/v1/routes/search.py      ← FastAPI route: parses & validates q/limit
   │  (asks for a SearchService via Depends)
   ▼
api/deps.py                  ← builds the SearchService (wires provider + extractor)
   │
   ▼
application/search_service.py ← use case: calls provider, then fetches pages concurrently
   │                 │
   ▼                 ▼
infrastructure/providers/*   infrastructure/content_extractor.py
(search backend)             (download + extract text)
```

Everything in `domain/` is plain Python + Pydantic — it imports no web framework. The outer
layers depend inward. That's the whole point of the Clean Architecture refactor.

## 3. FastAPI concepts you need (the new stuff)

### 3.1 The app object and the "app factory"

`app/main.py`:

```python
def create_app() -> FastAPI:
    app = FastAPI(title=..., version=..., lifespan=lifespan)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    ...
    return app

app = create_app()
```

- `FastAPI()` is the ASGI application object. Uvicorn (the server) imports it as `app.main:app`
  (see the `CMD` in the Dockerfile).
- A **factory function** (`create_app`) instead of a bare module-level `app = FastAPI()` keeps
  setup explicit and testable. Tests import the same `app`.

### 3.2 Routers = grouped endpoints

`APIRouter` is a mini-app you register onto the main app. This project nests them so the URL
prefix is built up in pieces:

- `api/v1/routes/search.py` → `APIRouter(prefix="/search")`
- `api/v1/router.py` → includes the search router
- `main.py` → includes that under `prefix="/api/v1"` (from settings)

Net path: `/api/v1` + `/search` + `""` = `/api/v1/search`. Splitting it means versioning (`v1`)
and the global prefix live in one place each.

### 3.3 Path/query parameters and validation

`api/v1/routes/search.py`:

```python
@router.get("", response_model=SearchResponse)
async def search(
    service: SearchServiceDep,
    settings: SettingsDep,
    q: Annotated[str, Query(min_length=1, max_length=256, description="...")],
    limit: Annotated[int | None, Query(ge=1, le=10)] = None,
) -> SearchResponse:
```

Key FastAPI ideas:

- A function parameter that isn't a dependency becomes a **request input**. Because `q` and `limit`
  are simple types, FastAPI reads them from the **query string** automatically.
- `Annotated[str, Query(...)]` attaches validation/metadata. `min_length`, `ge` (>=), `le` (<=) are
  enforced *before your function runs*. A bad request → automatic **422** response; you write no
  validation code for it. (That's what `test_validation_errors` checks.)
- `async def` matters: your handler runs on the event loop, so anything it `await`s (the HTTP calls)
  doesn't block other requests. Use `async def` unless you're calling blocking code.
- The manual `if not query: raise HTTPException(422)` handles the one case `Query` can't: a string
  that's all whitespace (non-empty, so it passes `min_length`, but blank after `.strip()`).

### 3.4 Pydantic models + `response_model`

`domain/models/` defines `SearchResponse`, `SearchResult`, etc. as `BaseModel` subclasses (one
class per file, re-exported from `domain/models/__init__.py` so `from app.domain.models import X` works).

- Returning a `SearchResponse` + declaring `response_model=SearchResponse` makes FastAPI
  **serialize and validate the output**, and generates the OpenAPI schema at `/docs`.
- `HttpUrl` is a Pydantic type that validates URLs. Note the service passes `str(hit.url)` to the
  extractor — `HttpUrl` is not a plain `str`.
- `Field(description=...)` feeds the auto-generated docs.
- `StrEnum` (`FetchStatus`) serializes to its string value (`"ok"`, `"failed"`), so the JSON is clean.

### 3.5 Dependency Injection with `Depends` — the core FastAPI idea

Instead of a route constructing its own objects, it *declares what it needs* and FastAPI supplies it.

`api/deps.py`:

```python
SettingsDep = Annotated[Settings, Depends(get_settings)]

def get_search_service(request: Request, settings: SettingsDep) -> SearchService:
    client = request.app.state.http_client          # shared pooled client (see lifespan)
    extractor = HttpContentExtractor(client, ...)
    return SearchService(build_provider(settings, client), extractor, ...)

SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
```

- `Depends(fn)` tells FastAPI "call `fn`, inject its return value here." Dependencies can depend on
  other dependencies (`get_search_service` itself takes `SettingsDep`) — FastAPI resolves the graph
  per request.
- The `Annotated[... , Depends(...)]` aliases (`SettingsDep`, `SearchServiceDep`) are just reusable
  type labels so routes stay short.
- **Why this matters:** the route never news-up a `SearchService`. In tests you swap the whole thing
  out with one line (see §6). This is how the layers stay decoupled.

### 3.6 Lifespan — startup/shutdown and the shared HTTP client

`main.py`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)
    async with httpx.AsyncClient(limits=limits) as client:
        app.state.http_client = client     # stash it for deps to grab
        yield                              # app runs here
    # client is closed on shutdown
```

- Code before `yield` runs at **startup**, after `yield` at **shutdown**.
- One `httpx.AsyncClient` is created for the whole process and reused (connection pooling). Creating
  a client per request would be slow and leak connections.
- `app.state` is a scratch space on the app; `get_search_service` reads `request.app.state.http_client`.

### 3.7 Centralized error handling

Domain code raises plain exceptions; it does not know about HTTP responses.

- `domain/exceptions.py`: `ServiceError` (and subclasses) carry a `status_code` and `code`. Pure
  Python — uses `http.HTTPStatus`, imports no FastAPI. A provider failure raises `SearchProviderError`.
- `api/errors.py`: `register_exception_handlers(app)` registers `@app.exception_handler(ServiceError)`,
  which turns any raised `ServiceError` into a JSON body `{"error": {"code", "message"}}` with the
  right status. So services just `raise`; the presentation layer decides the HTTP shape.

## 4. The layers (Clean Architecture mapping)

| Folder | Role | Depends on | Framework? |
|---|---|---|---|
| `domain/` | Entities (`models/`), errors (`exceptions/`), interfaces (`ports/`) | nothing internal | No (Pydantic only) |
| `application/` | Use case (`SearchService`) | `domain` | No |
| `infrastructure/` | Adapters: providers, content extractor | `domain` | httpx/trafilatura |
| `api/` | FastAPI routes, DI wiring, error handlers | application, domain, infra | Yes |
| `core/` | Config + logging | nothing internal | pydantic-settings |

**Ports & adapters** (`domain/ports.py`):

- `SearchProvider` is an `ABC` with one abstract method `search(query, limit) -> list[SearchHit]`.
- `ContentExtractor` is a `typing.Protocol` — structural typing, so anything with a matching
  `extract` method qualifies (no inheritance needed; that's why the test's fake extractor "just works").
- `SearchService` depends on these *interfaces*, not concrete classes. Infrastructure provides the
  real implementations (`HttpSearchProvider` subclasses, `HttpContentExtractor`). This is the
  Dependency Inversion that lets you swap backends or fake them in tests.

## 5. The two infrastructure pieces

### Providers (`infrastructure/providers/`)

- `base.py`: `HttpSearchProvider(SearchProvider)` just stores the shared `client` and `timeout`.
- `duckduckgo.py` / `serper.py` / `google_cse.py`: concrete adapters. Each `search()` calls its API,
  wraps network errors in `SearchProviderError`, and maps the response into `list[SearchHit]`.
  DuckDuckGo additionally parses HTML (`selectolax`) and unwraps redirect links.
- `__init__.py`: `build_provider(settings, client)` is a **factory** — a `match` on
  `settings.search_provider` returns the right adapter, raising `ProviderConfigurationError` if an
  API key is missing. This is the only place that knows about all three providers.

### Content extractor (`infrastructure/content_extractor.py`)

- `extract(url)` streams the page, guards against non-HTML and oversized bodies, then runs
  `trafilatura.extract`.
- Note: `await asyncio.to_thread(trafilatura.extract, ...)`. `trafilatura` is **synchronous and
  CPU-bound**; running it directly would block the event loop and stall other requests.
  `to_thread` pushes it onto a worker thread. This is the key async-hygiene lesson.
- Returns an `ExtractedContent` (a frozen dataclass) describing success/empty/failure — never raises
  to the caller, so one bad page is just a `failed` result.

### How concurrency is bounded (`application/search_service.py`)

```python
results = await asyncio.gather(*(self._enrich(rank, hit) for rank, hit in enumerate(hits, 1)))
...
async with self._semaphore:          # asyncio.Semaphore(max_concurrency)
    extracted = await self._extractor.extract(str(hit.url))
```

- `asyncio.gather` fetches all pages concurrently.
- The `Semaphore` caps how many run at once (`max_concurrent_fetches`), so 10 results don't open 10
  simultaneous downloads.

## 6. Configuration (`core/config.py`)

- `Settings(BaseSettings)` from **pydantic-settings** reads values from environment variables / `.env`
  automatically (field name `fetch_timeout_seconds` ← env `FETCH_TIMEOUT_SECONDS`, case-insensitive).
- `SecretStr` for API keys so they don't print in logs/reprs; read with `.get_secret_value()`.
- `@lru_cache` on `get_settings()` makes it a singleton — parsed once, reused everywhere (and easy to
  override in tests).

## 7. Testing (`tests/`)

The DI design makes tests not touch the network.

```python
app.dependency_overrides[get_search_service] = lambda: SearchService(
    fake_provider, FakeExtractor(), max_concurrency=5
)
```

- `app.dependency_overrides[dep] = replacement` swaps a dependency for the whole app during the test.
  Here the real `SearchService` is replaced with one using a fake provider + fake extractor.
- `FakeProvider` subclasses the `SearchProvider` port; `FakeExtractor` just has a matching `extract`
  method (satisfies the `Protocol` structurally — no base class).
- `AsyncClient(transport=ASGITransport(app=app))` calls the app **in-process** (no real server/socket).
- `asyncio_mode = "auto"` (in `pyproject.toml`) lets `async def test_...` run without decorators.

## 8. Running & extending

```bash
make install     # venv + dev deps
make run         # uvicorn with --reload  → http://localhost:8000/docs
make check       # ruff + pytest
make docker-up   # run the container
```

**Add a search backend:**

1. Add a name to `SearchProviderName` in `core/config.py`.
2. Create `infrastructure/providers/<name>.py` subclassing `HttpSearchProvider`, implement `search()`.
3. Add a `case` for it in `build_provider`.

Nothing in `domain/` or `application/` changes — that's the payoff of the layering.

## 9. Where to read next, in order

1. `app/main.py` — how the app is assembled.
2. `app/api/v1/routes/search.py` + `app/api/deps.py` — the HTTP edge and DI.
3. `app/application/search_service.py` — the use case.
4. `app/domain/` — the contracts everything agrees on.
5. `app/infrastructure/` — the real implementations.
