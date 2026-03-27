from paper_search.apis.semantic_scholar import SemanticScholarClient, _parse_paper


class TestParsePaper:
    def test_parses_full_paper(self, s2_paper_fixture):
        paper = _parse_paper(s2_paper_fixture["body"])
        assert paper.title == "Attention is All you Need"
        assert paper.citation_count > 0
        assert paper.influential_citation_count > 0
        assert paper.tldr is not None
        assert paper.source == "semantic_scholar"
        assert "s2" in paper.external_ids

    def test_parses_bulk_result(self, s2_bulk_fixture):
        raw = s2_bulk_fixture["body"]["data"][0]
        paper = _parse_paper(raw)
        assert paper.title
        assert paper.citation_count is not None

    def test_missing_fields(self):
        paper = _parse_paper({"title": "Minimal", "paperId": "abc123"})
        assert paper.title == "Minimal"
        assert paper.doi is None
        assert paper.tldr is None
        assert paper.authors == []

    def test_external_ids(self, s2_paper_fixture):
        paper = _parse_paper(s2_paper_fixture["body"])
        assert "doi" in paper.external_ids or "arxiv" in paper.external_ids

    def test_oa_pdf_parsed(self, s2_paper_fixture):
        paper = _parse_paper(s2_paper_fixture["body"])
        if paper.is_open_access:
            assert len(paper.oa_locations) > 0
            assert paper.oa_locations[0].url_pdf


class TestSemanticScholarClient:
    async def test_bulk_search(self, respx_mock, mock_s2_bulk):
        client = SemanticScholarClient()
        papers = await client.search_papers("attention mechanism", sort="citations", limit=3)
        await client.close()
        assert len(papers) == 3
        citations = [p.citation_count or 0 for p in papers]
        assert citations == sorted(citations, reverse=True)

    async def test_relevance_search(self, respx_mock, mock_s2_relevance):
        client = SemanticScholarClient()
        papers = await client.search_papers("attention mechanism", sort="relevance", limit=5)
        await client.close()
        assert len(papers) > 0

    async def test_get_paper(self, respx_mock, mock_s2_paper):
        client = SemanticScholarClient()
        paper = await client.get_paper("ARXIV:1706.03762")
        await client.close()
        assert paper.title == "Attention is All you Need"

    async def test_get_recommendations(self, respx_mock, mock_s2_recommendations):
        client = SemanticScholarClient()
        papers = await client.get_recommendations("ARXIV:1706.03762", limit=5)
        await client.close()
        assert len(papers) > 0
        assert all(p.source == "semantic_scholar" for p in papers)
