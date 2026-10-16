from app.infrastructure.providers.duckduckgo import DuckDuckGoProvider

HTML = """
<div class="result result--ad"><a class="result__a" href="https://ads.example.com">Ad</a></div>
<div class="result">
  <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Ffastapi.tiangolo.com%2F&rut=abc">FastAPI</a>
  <a class="result__snippet">Modern, fast web framework.</a>
</div>
<div class="result">
  <a class="result__a" href="https://docs.python.org/3/">Python docs</a>
</div>
"""


def test_parse_skips_ads_and_unwraps_redirects() -> None:
    hits = DuckDuckGoProvider._parse(HTML, limit=5)

    assert [str(h.url) for h in hits] == ["https://fastapi.tiangolo.com/", "https://docs.python.org/3/"]
    assert hits[0].title == "FastAPI"
    assert hits[0].snippet == "Modern, fast web framework."
    assert hits[1].snippet is None


def test_parse_respects_limit() -> None:
    assert len(DuckDuckGoProvider._parse(HTML, limit=1)) == 1
