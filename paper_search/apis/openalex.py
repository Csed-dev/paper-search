import re

import httpx

from paper_search.models.paper import Author, OALocation, Paper

_HTML_TAG = re.compile(r"<[^>]+>")

BASE_URL = "https://api.openalex.org"

WORK_FIELDS = ",".join([
    "id", "doi", "title", "publication_year", "publication_date",
    "cited_by_count", "open_access", "authorships",
    "primary_topic", "topics", "abstract_inverted_index",
])


def _reconstruct_abstract(inverted_index: dict | None) -> str | None:
    if not inverted_index:
        return None
    max_pos = max(pos for positions in inverted_index.values() for pos in positions)
    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words)


def _parse_work(work: dict) -> Paper:
    oa = work.get("open_access", {})
    doi_raw = work.get("doi")
    doi = doi_raw.replace("https://doi.org/", "") if doi_raw else None

    authors = []
    for authorship in work.get("authorships", []):
        author_data = authorship.get("author", {})
        institutions = authorship.get("institutions", [])
        affiliation = institutions[0]["display_name"] if institutions else None
        orcid = author_data.get("orcid")
        if orcid:
            orcid = orcid.replace("https://orcid.org/", "")
        authors.append(Author(
            name=author_data.get("display_name", ""),
            affiliation=affiliation,
            orcid=orcid,
        ))

    topics = []
    for topic in work.get("topics", []):
        topics.append(topic.get("display_name", ""))

    oa_locations = []
    oa_url = oa.get("oa_url")
    if oa_url:
        oa_locations.append(OALocation(url=oa_url))

    openalex_id = work.get("id", "")
    if openalex_id.startswith("https://openalex.org/"):
        openalex_id = openalex_id.replace("https://openalex.org/", "")

    external_ids = {"openalex": openalex_id}
    if doi:
        external_ids["doi"] = doi

    raw_title = work.get("title", "")
    title = _HTML_TAG.sub("", raw_title) if "<" in raw_title else raw_title

    return Paper(
        title=title,
        doi=doi,
        abstract=_reconstruct_abstract(work.get("abstract_inverted_index")),
        authors=authors,
        publication_year=work.get("publication_year"),
        publication_date=work.get("publication_date"),
        citation_count=work.get("cited_by_count"),
        topics=topics,
        is_open_access=oa.get("is_oa", False),
        oa_locations=oa_locations,
        source="openalex",
        external_ids=external_ids,
    )


class OpenAlexClient:
    def __init__(self, *, api_key: str | None = None, email: str | None = None) -> None:
        params = {}
        if api_key:
            params["api_key"] = api_key
        if email:
            params["mailto"] = email
        self._client = httpx.AsyncClient(base_url=BASE_URL, params=params, timeout=30)

    async def search_works(
        self,
        query: str,
        *,
        sort: str = "citations",
        publication_year: str | None = None,
        per_page: int = 25,
        page: int = 1,
    ) -> list[Paper]:
        search_query = f'"{query}"' if " " in query else query
        fetch_size = per_page * 3 if sort == "citations" else per_page

        params: dict[str, str | int] = {
            "search": search_query,
            "select": WORK_FIELDS,
            "per_page": min(fetch_size, 100),
            "page": page,
            "sort": "relevance_score:desc",
        }

        filters = ["has_abstract:true"]
        if publication_year:
            if "-" in publication_year:
                start, end = publication_year.split("-", 1)
                if start:
                    filters.append(f"publication_year:>{int(start) - 1}")
                if end:
                    filters.append(f"publication_year:<{int(end) + 1}")
            else:
                filters.append(f"publication_year:{publication_year}")
        params["filter"] = ",".join(filters)

        response = await self._client.get("/works", params=params)
        response.raise_for_status()
        papers = [_parse_work(w) for w in response.json().get("results", [])]

        if sort == "citations":
            papers.sort(key=lambda p: p.citation_count or 0, reverse=True)
            return papers[:per_page]
        if sort == "date":
            papers.sort(key=lambda p: p.publication_date or "", reverse=True)
            return papers[:per_page]
        return papers[:per_page]

    async def search_topics(self, query: str, *, per_page: int = 5) -> list[dict]:
        response = await self._client.get("/topics", params={
            "search": query,
            "per_page": per_page,
        })
        response.raise_for_status()
        return response.json().get("results", [])

    async def close(self) -> None:
        await self._client.aclose()
