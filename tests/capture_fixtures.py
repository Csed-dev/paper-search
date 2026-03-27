"""Run once to capture real API responses as test fixtures.

Usage: python tests/capture_fixtures.py
"""

import asyncio
import json
from pathlib import Path

import httpx

FIXTURES_DIR = Path(__file__).parent / "fixtures"

REQUESTS = {
    "openalex_search": {
        "url": "https://api.openalex.org/works",
        "params": {
            "search": '"attention mechanism"',
            "select": "id,doi,title,publication_year,publication_date,cited_by_count,open_access,authorships,primary_topic,topics,abstract_inverted_index",
            "per_page": 5,
            "page": 1,
            "sort": "relevance_score:desc",
            "filter": "has_abstract:true",
        },
    },
    "openalex_topics": {
        "url": "https://api.openalex.org/topics",
        "params": {"search": "machine learning", "per_page": 3},
    },
    "s2_relevance_search": {
        "url": "https://api.semanticscholar.org/graph/v1/paper/search",
        "params": {
            "query": "attention mechanism",
            "fields": "title,abstract,year,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,authors,externalIds,fieldsOfStudy,s2FieldsOfStudy,publicationDate,tldr",
            "limit": 5,
            "offset": 0,
        },
    },
    "s2_bulk_search": {
        "url": "https://api.semanticscholar.org/graph/v1/paper/search/bulk",
        "params": {
            "query": "attention mechanism",
            "fields": "title,abstract,year,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,authors,externalIds,fieldsOfStudy,s2FieldsOfStudy,publicationDate",
            "sort": "citationCount:desc",
        },
    },
    "s2_paper_detail": {
        "url": "https://api.semanticscholar.org/graph/v1/paper/ARXIV:1706.03762",
        "params": {
            "fields": "title,abstract,year,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,authors,externalIds,fieldsOfStudy,s2FieldsOfStudy,publicationDate,tldr",
        },
    },
    "s2_recommendations": {
        "url": "https://api.semanticscholar.org/recommendations/v1/papers/forpaper/ARXIV:1706.03762",
        "params": {
            "fields": "title,abstract,year,citationCount,influentialCitationCount,isOpenAccess,openAccessPdf,authors,externalIds,fieldsOfStudy,s2FieldsOfStudy,publicationDate",
            "limit": 5,
            "from": "all-cs",
        },
    },
    "unpaywall_oa": {
        "url": "https://api.unpaywall.org/v2/10.1038/nature12373",
        "params": {"email": "test@papersearch.dev"},
    },
    "unpaywall_closed": {
        "url": "https://api.unpaywall.org/v2/10.1016/j.compstruct.2020.112680",
        "params": {"email": "test@papersearch.dev"},
    },
}


async def capture_all() -> None:
    FIXTURES_DIR.mkdir(exist_ok=True)

    async with httpx.AsyncClient(timeout=30) as client:
        for name, spec in REQUESTS.items():
            print(f"Fetching {name}...")
            response = await client.get(spec["url"], params=spec["params"])
            fixture = {
                "status_code": response.status_code,
                "url": str(response.url),
                "body": response.json() if response.status_code == 200 else response.text,
            }
            path = FIXTURES_DIR / f"{name}.json"
            path.write_text(json.dumps(fixture, indent=2, ensure_ascii=False))
            print(f"  -> {path} ({response.status_code})")

    print(f"\nAll fixtures saved to {FIXTURES_DIR}")


if __name__ == "__main__":
    asyncio.run(capture_all())
