from httpx import AsyncClient

from tests.conftest import FakeProvider


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_search_returns_five_results_by_default(client: AsyncClient, fake_provider: FakeProvider) -> None:
    response = await client.get("/api/v1/search", params={"q": "  fastapi  "})

    assert response.status_code == 200
    body = response.json()
    assert fake_provider.calls == [("fastapi", 5)]
    assert body["query"] == "fastapi"
    assert body["total_results"] == 5
    assert [r["rank"] for r in body["results"]] == [1, 2, 3, 4, 5]
    assert body["results"][0]["content"] == "content of https://example.com/1"


async def test_failed_fetch_is_reported_per_result(client: AsyncClient) -> None:
    body = (await client.get("/api/v1/search", params={"q": "x"})).json()

    failed = body["results"][1]
    assert failed["fetch_status"] == "failed"
    assert failed["error"] == "timeout"
    assert failed["content"] is None
    assert body["results"][0]["fetch_status"] == "ok"


async def test_custom_limit(client: AsyncClient, fake_provider: FakeProvider) -> None:
    body = (await client.get("/api/v1/search", params={"q": "x", "limit": 3})).json()
    assert body["total_results"] == 3
    assert fake_provider.calls == [("x", 3)]


async def test_validation_errors(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/search")).status_code == 422
    assert (await client.get("/api/v1/search", params={"q": "   "})).status_code == 422
    assert (await client.get("/api/v1/search", params={"q": "x", "limit": 11})).status_code == 422
