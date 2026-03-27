import pytest
import respx

from paper_search.models.paper import Author, OALocation, Paper
from paper_search.search import (
    _match_papers,
    _merge_paper,
    _resolve_paper_id,
    recommend_papers,
    search_papers,
)


class TestResolvePaperId:
    def test_new_arxiv_format(self):
        assert _resolve_paper_id("1706.03762") == "ARXIV:1706.03762"

    def test_old_arxiv_hep_th(self):
        assert _resolve_paper_id("hep-th/9905111") == "ARXIV:hep-th/9905111"

    def test_old_arxiv_cs(self):
        assert _resolve_paper_id("cs/0601078") == "ARXIV:cs/0601078"

    def test_doi(self):
        assert _resolve_paper_id("10.1038/s41586-023-06291-2") == "DOI:10.1038/s41586-023-06291-2"

    def test_already_prefixed_doi(self):
        assert _resolve_paper_id("DOI:10.1234/test") == "DOI:10.1234/test"

    def test_already_prefixed_arxiv(self):
        assert _resolve_paper_id("ARXIV:1706.03762") == "ARXIV:1706.03762"

    def test_corpus_id(self):
        assert _resolve_paper_id("CorpusId:215416146") == "CorpusId:215416146"

    def test_s2_hash(self):
        result = _resolve_paper_id("649def34f8be52c8b66281af98ae884c09aef38b")
        assert result == "649def34f8be52c8b66281af98ae884c09aef38b"


class TestMergePaper:
    def test_prefers_openalex_title(self):
        oa = Paper(title="OA Title", doi="10.1234/test", source="openalex")
        s2 = Paper(title="S2 Title", doi="10.1234/test", source="semantic_scholar")
        merged = _merge_paper(oa, s2)
        assert merged.title == "OA Title"

    def test_takes_s2_abstract(self):
        oa = Paper(title="T", abstract="OA abstract", source="openalex")
        s2 = Paper(title="T", abstract="S2 abstract", source="semantic_scholar")
        merged = _merge_paper(oa, s2)
        assert merged.abstract == "S2 abstract"

    def test_takes_s2_tldr(self):
        oa = Paper(title="T", source="openalex")
        s2 = Paper(title="T", tldr="A short summary.", source="semantic_scholar")
        merged = _merge_paper(oa, s2)
        assert merged.tldr == "A short summary."

    def test_takes_s2_influential_citations(self):
        oa = Paper(title="T", citation_count=100, source="openalex")
        s2 = Paper(title="T", influential_citation_count=20, source="semantic_scholar")
        merged = _merge_paper(oa, s2)
        assert merged.citation_count == 100
        assert merged.influential_citation_count == 20

    def test_merges_oa_locations(self):
        oa = Paper(title="T", oa_locations=[OALocation(url="http://a")], source="openalex")
        s2 = Paper(title="T", oa_locations=[OALocation(url="http://b")], source="semantic_scholar")
        merged = _merge_paper(oa, s2)
        assert len(merged.oa_locations) == 2

    def test_merges_external_ids(self):
        oa = Paper(title="T", external_ids={"openalex": "W1"}, source="openalex")
        s2 = Paper(title="T", external_ids={"s2": "abc"}, source="semantic_scholar")
        merged = _merge_paper(oa, s2)
        assert "openalex" in merged.external_ids
        assert "s2" in merged.external_ids

    def test_takes_s2_bibtex(self):
        oa = Paper(title="T", source="openalex")
        s2 = Paper(title="T", bibtex="@article{key, title={T}}", source="semantic_scholar")
        merged = _merge_paper(oa, s2)
        assert merged.bibtex == "@article{key, title={T}}"

    def test_source_is_merged(self):
        oa = Paper(title="T", source="openalex")
        s2 = Paper(title="T", source="semantic_scholar")
        assert _merge_paper(oa, s2).source == "merged"


class TestMatchPapers:
    def test_matches_by_doi(self):
        oa = [Paper(title="Paper A", doi="10.1234/test", citation_count=50, source="openalex")]
        s2 = [Paper(title="Paper A", doi="10.1234/test", tldr="Summary", source="semantic_scholar")]
        result = _match_papers(oa, s2)
        assert len(result) == 1
        assert result[0].source == "merged"
        assert result[0].tldr == "Summary"

    def test_case_insensitive_doi(self):
        oa = [Paper(title="A", doi="10.1234/TEST", source="openalex")]
        s2 = [Paper(title="A", doi="10.1234/test", tldr="OK", source="semantic_scholar")]
        result = _match_papers(oa, s2)
        assert result[0].source == "merged"

    def test_unmatched_oa_papers_kept(self):
        oa = [Paper(title="Only OA", doi="10.9999/unique", source="openalex")]
        s2 = [Paper(title="Only S2", doi="10.8888/other", source="semantic_scholar")]
        result = _match_papers(oa, s2)
        assert len(result) == 1
        assert result[0].title == "Only OA"

    def test_no_doi_no_match(self):
        oa = [Paper(title="No DOI", source="openalex")]
        s2 = [Paper(title="No DOI", source="semantic_scholar")]
        result = _match_papers(oa, s2)
        assert len(result) == 1
        assert result[0].source == "openalex"

    def test_empty_inputs(self):
        assert _match_papers([], []) == []


class TestSearchPapers:
    async def test_returns_papers(self, respx_mock, mock_openalex_search, mock_s2_bulk):
        papers = await search_papers(query="attention mechanism", limit=3)
        assert len(papers) > 0

    async def test_one_api_fails_still_returns(self, respx_mock, mock_openalex_search):
        respx_mock.get("https://api.semanticscholar.org/graph/v1/paper/search/bulk").respond(status_code=500)
        papers = await search_papers(query="attention mechanism", limit=3)
        assert len(papers) > 0
        assert all(p.source == "openalex" for p in papers)

    async def test_both_fail_raises(self, respx_mock):
        respx_mock.get("https://api.openalex.org/works").respond(status_code=500)
        respx_mock.get("https://api.semanticscholar.org/graph/v1/paper/search/bulk").respond(status_code=500)
        with pytest.raises(RuntimeError, match="Both APIs failed"):
            await search_papers(query="attention mechanism", limit=3)


class TestRecommendPapers:
    async def test_returns_recommendations(self, respx_mock, mock_s2_recommendations):
        papers = await recommend_papers(paper_id="1706.03762", limit=5)
        assert len(papers) > 0
