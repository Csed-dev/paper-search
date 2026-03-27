import asyncio
import sys

from paper_search.apis.openalex import OpenAlexClient
from paper_search.apis.semantic_scholar import SemanticScholarClient
from paper_search.apis.unpaywall import UnpaywallClient
from paper_search.models.paper import Paper


def _merge_paper(openalex: Paper, s2: Paper) -> Paper:
    return Paper(
        title=openalex.title,
        doi=openalex.doi or s2.doi,
        abstract=s2.abstract or openalex.abstract,
        tldr=s2.tldr,
        authors=openalex.authors or s2.authors,
        publication_year=openalex.publication_year or s2.publication_year,
        publication_date=openalex.publication_date or s2.publication_date,
        citation_count=openalex.citation_count,
        influential_citation_count=s2.influential_citation_count,
        topics=openalex.topics or s2.topics,
        fields_of_study=s2.fields_of_study,
        is_open_access=openalex.is_open_access or s2.is_open_access,
        oa_locations=[*openalex.oa_locations, *s2.oa_locations],
        source="merged",
        external_ids={**openalex.external_ids, **s2.external_ids},
    )


def _match_papers(openalex_papers: list[Paper], s2_papers: list[Paper]) -> list[Paper]:
    s2_by_doi: dict[str, Paper] = {}
    for p in s2_papers:
        if p.doi:
            s2_by_doi[p.doi.lower()] = p

    merged = []
    for oa_paper in openalex_papers:
        if oa_paper.doi and oa_paper.doi.lower() in s2_by_doi:
            s2_paper = s2_by_doi[oa_paper.doi.lower()]
            merged.append(_merge_paper(oa_paper, s2_paper))
        else:
            merged.append(oa_paper)
    return merged


async def _enrich_with_unpaywall(papers: list[Paper], email: str) -> list[Paper]:
    client = UnpaywallClient(email=email)
    semaphore = asyncio.Semaphore(3)

    async def _fetch(doi: str) -> list:
        async with semaphore:
            return await client.get_oa_locations(doi)

    try:
        dois = [p.doi for p in papers if p.doi]
        tasks = [_fetch(doi) for doi in dois]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        doi_locations: dict[str, list] = {}
        for doi, result in zip(dois, results):
            if isinstance(result, list):
                doi_locations[doi.lower()] = result

        enriched = []
        for paper in papers:
            if paper.doi and paper.doi.lower() in doi_locations:
                locations = doi_locations[paper.doi.lower()]
                existing_urls = {loc.url for loc in paper.oa_locations}
                new_locations = [loc for loc in locations if loc.url not in existing_urls]
                paper = paper.model_copy(update={
                    "oa_locations": paper.oa_locations + new_locations,
                    "is_open_access": paper.is_open_access or bool(locations),
                })
            enriched.append(paper)
        return enriched
    finally:
        await client.close()


async def search_papers(
    *,
    query: str,
    limit: int = 10,
    year: int | None = None,
    sort: str = "citations",
    email: str | None = None,
    s2_api_key: str | None = None,
) -> list[Paper]:
    openalex = OpenAlexClient(email=email)
    s2 = SemanticScholarClient(api_key=s2_api_key)

    try:
        oa_results, s2_results = await asyncio.gather(
            openalex.search_works(query, sort=sort, publication_year=year, per_page=limit),
            s2.search_papers(query, sort=sort, year=year, limit=limit),
            return_exceptions=True,
        )

        if isinstance(oa_results, BaseException):
            print(f"OpenAlex error: {oa_results}", file=sys.stderr)
        if isinstance(s2_results, BaseException):
            print(f"Semantic Scholar error: {s2_results}", file=sys.stderr)

        oa_papers = oa_results if isinstance(oa_results, list) else []
        s2_papers = s2_results if isinstance(s2_results, list) else []

        if not oa_papers and not s2_papers:
            raise RuntimeError("Both APIs failed")

        papers = _match_papers(oa_papers, s2_papers) if oa_papers else s2_papers

        if email:
            papers = await _enrich_with_unpaywall(papers, email)

        return papers
    finally:
        await asyncio.gather(openalex.close(), s2.close())


_ARXIV_OLD_CATEGORIES = {
    "astro-ph", "cond-mat", "gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th",
    "math-ph", "nlin", "nucl-ex", "nucl-th", "physics", "quant-ph",
    "math", "cs", "q-bio", "q-fin", "stat", "eess", "econ",
}


def _resolve_paper_id(paper_id: str) -> str:
    if paper_id.startswith(("DOI:", "ARXIV:", "CorpusId:", "PMID:")):
        return paper_id
    if paper_id.startswith("10."):
        return f"DOI:{paper_id}"
    prefix = paper_id.split("/")[0] if "/" in paper_id else ""
    if prefix in _ARXIV_OLD_CATEGORIES:
        return f"ARXIV:{paper_id}"
    if "/" in paper_id:
        return f"DOI:{paper_id}"
    stripped = paper_id.replace(".", "")
    if stripped.isdigit():
        return f"ARXIV:{paper_id}"
    return paper_id


async def recommend_papers(
    *,
    paper_id: str,
    limit: int = 10,
    email: str | None = None,
    s2_api_key: str | None = None,
) -> list[Paper]:
    s2 = SemanticScholarClient(api_key=s2_api_key)

    try:
        resolved_id = _resolve_paper_id(paper_id)
        papers = await s2.get_recommendations(resolved_id, limit=limit)

        if email:
            papers = await _enrich_with_unpaywall(papers, email)

        return papers
    finally:
        await s2.close()
