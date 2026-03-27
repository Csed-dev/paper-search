import httpx

from paper_search.models.paper import Author, OALocation, Paper

BASE_URL = "https://api.semanticscholar.org"

_BASE_FIELDS = [
    "title", "abstract", "year", "citationCount", "influentialCitationCount",
    "isOpenAccess", "openAccessPdf", "authors", "externalIds",
    "fieldsOfStudy", "s2FieldsOfStudy", "publicationDate",
]

PAPER_FIELDS = ",".join([*_BASE_FIELDS, "tldr", "citationStyles"])
BULK_FIELDS = ",".join(_BASE_FIELDS)


def _parse_paper(paper: dict) -> Paper:
    external_ids_raw = paper.get("externalIds", {}) or {}
    doi = external_ids_raw.get("DOI")

    authors = [
        Author(name=a.get("name", ""))
        for a in paper.get("authors", [])
    ]

    oa_pdf = paper.get("openAccessPdf")
    oa_locations = []
    if oa_pdf and oa_pdf.get("url"):
        oa_locations.append(OALocation(
            url=oa_pdf["url"],
            url_pdf=oa_pdf["url"],
            license=oa_pdf.get("license"),
        ))

    tldr_data = paper.get("tldr")
    tldr = tldr_data["text"] if tldr_data else None

    citation_styles = paper.get("citationStyles") or {}
    bibtex = citation_styles.get("bibtex")

    fields_of_study = paper.get("fieldsOfStudy") or []
    s2_fields = paper.get("s2FieldsOfStudy") or []
    topics = [f["category"] for f in s2_fields if f.get("category")]

    external_ids = {}
    if paper.get("paperId"):
        external_ids["s2"] = paper["paperId"]
    if doi:
        external_ids["doi"] = doi
    arxiv_id = external_ids_raw.get("ArXiv")
    if arxiv_id:
        external_ids["arxiv"] = arxiv_id

    return Paper(
        title=paper.get("title", ""),
        doi=doi,
        abstract=paper.get("abstract"),
        tldr=tldr,
        authors=authors,
        publication_year=paper.get("year"),
        publication_date=paper.get("publicationDate"),
        citation_count=paper.get("citationCount"),
        influential_citation_count=paper.get("influentialCitationCount"),
        fields_of_study=fields_of_study,
        topics=topics,
        is_open_access=paper.get("isOpenAccess", False),
        oa_locations=oa_locations,
        bibtex=bibtex,
        source="semantic_scholar",
        external_ids=external_ids,
    )


class SemanticScholarClient:
    def __init__(self, api_key: str | None = None) -> None:
        headers = {}
        if api_key:
            headers["x-api-key"] = api_key
        self._client = httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=30)

    async def search_papers(
        self,
        query: str,
        *,
        sort: str = "citations",
        year: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> list[Paper]:
        if sort == "citations":
            return await self._bulk_search(query, year=year, limit=limit)
        return await self._relevance_search(query, year=year, limit=limit, offset=offset)

    async def _relevance_search(
        self,
        query: str,
        *,
        year: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> list[Paper]:
        params: dict[str, str | int] = {
            "query": query,
            "fields": PAPER_FIELDS,
            "limit": min(limit, 100),
            "offset": offset,
        }
        if year:
            params["year"] = str(year)
        response = await self._client.get("/graph/v1/paper/search", params=params)
        response.raise_for_status()
        return [_parse_paper(p) for p in response.json().get("data", [])]

    async def _bulk_search(
        self,
        query: str,
        *,
        year: str | None = None,
        limit: int = 25,
    ) -> list[Paper]:
        params: dict[str, str | int] = {
            "query": query,
            "fields": BULK_FIELDS,
            "sort": "citationCount:desc",
        }
        if year:
            params["year"] = str(year)
        response = await self._client.get("/graph/v1/paper/search/bulk", params=params)
        response.raise_for_status()
        results = response.json().get("data", [])
        return [_parse_paper(p) for p in results[:limit]]

    async def get_paper(self, paper_id: str) -> Paper:
        response = await self._client.get(
            f"/graph/v1/paper/{paper_id}",
            params={"fields": PAPER_FIELDS},
        )
        response.raise_for_status()
        return _parse_paper(response.json())

    async def get_recommendations(self, paper_id: str, *, limit: int = 10) -> list[Paper]:
        response = await self._client.get(
            f"/recommendations/v1/papers/forpaper/{paper_id}",
            params={"fields": BULK_FIELDS, "limit": limit, "from": "all-cs"},
        )
        response.raise_for_status()
        return [_parse_paper(p) for p in response.json().get("recommendedPapers", [])]

    async def close(self) -> None:
        await self._client.aclose()
