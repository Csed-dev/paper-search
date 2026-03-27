import json
from pathlib import Path

import httpx
import pytest
import respx

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / f"{name}.json").read_text())


def _mock_route(fixture_name: str) -> respx.Route:
    fixture = _load_fixture(fixture_name)
    url = fixture["url"].split("?")[0]
    return respx.get(url).respond(
        status_code=fixture["status_code"],
        json=fixture["body"],
    )


@pytest.fixture()
def mock_openalex_search():
    return _mock_route("openalex_search")


@pytest.fixture()
def mock_openalex_topics():
    return _mock_route("openalex_topics")


@pytest.fixture()
def mock_s2_relevance():
    return _mock_route("s2_relevance_search")


@pytest.fixture()
def mock_s2_bulk():
    return _mock_route("s2_bulk_search")


@pytest.fixture()
def mock_s2_paper():
    fixture = _load_fixture("s2_paper_detail")
    return respx.get("https://api.semanticscholar.org/graph/v1/paper/ARXIV:1706.03762").respond(
        status_code=200,
        json=fixture["body"],
    )


@pytest.fixture()
def mock_s2_recommendations():
    fixture = _load_fixture("s2_recommendations")
    return respx.get("https://api.semanticscholar.org/recommendations/v1/papers/forpaper/ARXIV:1706.03762").respond(
        status_code=200,
        json=fixture["body"],
    )


@pytest.fixture()
def mock_unpaywall_oa():
    fixture = _load_fixture("unpaywall_oa")
    return respx.get("https://api.unpaywall.org/v2/10.1038%2Fnature12373").respond(
        status_code=200,
        json=fixture["body"],
    )


@pytest.fixture()
def mock_unpaywall_closed():
    fixture = _load_fixture("unpaywall_closed")
    return respx.get("https://api.unpaywall.org/v2/10.1016%2Fj.compstruct.2020.112680").respond(
        status_code=200,
        json=fixture["body"],
    )


@pytest.fixture()
def openalex_fixture():
    return _load_fixture("openalex_search")


@pytest.fixture()
def s2_bulk_fixture():
    return _load_fixture("s2_bulk_search")


@pytest.fixture()
def s2_paper_fixture():
    return _load_fixture("s2_paper_detail")


@pytest.fixture()
def unpaywall_oa_fixture():
    return _load_fixture("unpaywall_oa")


@pytest.fixture()
def unpaywall_closed_fixture():
    return _load_fixture("unpaywall_closed")
