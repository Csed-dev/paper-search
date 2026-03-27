import respx

from paper_search.apis.openalex import OpenAlexClient, _parse_work, _reconstruct_abstract


class TestReconstructAbstract:
    def test_basic(self):
        inverted = {"Hello": [0], "world": [1]}
        assert _reconstruct_abstract(inverted) == "Hello world"

    def test_repeated_words(self):
        inverted = {"the": [0, 2], "big": [1], "dog": [3]}
        assert _reconstruct_abstract(inverted) == "the big the dog"

    def test_none(self):
        assert _reconstruct_abstract(None) is None

    def test_empty(self):
        assert _reconstruct_abstract({}) is None


class TestParseWork:
    def test_parses_real_fixture(self, openalex_fixture):
        work = openalex_fixture["body"]["results"][0]
        paper = _parse_work(work)
        assert paper.title
        assert paper.source == "openalex"
        assert paper.citation_count is not None
        assert paper.publication_year is not None

    def test_strips_html_tags(self):
        work = {
            "title": "A short history of<i>SHELX</i>",
            "open_access": {},
            "authorships": [],
            "topics": [],
        }
        paper = _parse_work(work)
        assert "<" not in paper.title
        assert paper.title == "A short history ofSHELX"

    def test_doi_prefix_stripped(self):
        work = {
            "doi": "https://doi.org/10.1234/test",
            "title": "Test",
            "open_access": {},
            "authorships": [],
            "topics": [],
        }
        paper = _parse_work(work)
        assert paper.doi == "10.1234/test"

    def test_authors_parsed(self, openalex_fixture):
        work = openalex_fixture["body"]["results"][0]
        paper = _parse_work(work)
        assert len(paper.authors) > 0
        assert paper.authors[0].name

    def test_openalex_id_stripped(self):
        work = {
            "id": "https://openalex.org/W12345",
            "title": "Test",
            "open_access": {},
            "authorships": [],
            "topics": [],
        }
        paper = _parse_work(work)
        assert paper.external_ids["openalex"] == "W12345"


class TestOpenAlexClient:
    async def test_search_works(self, respx_mock, mock_openalex_search):
        client = OpenAlexClient()
        papers = await client.search_works("attention mechanism", per_page=5)
        await client.close()
        assert len(papers) > 0
        assert all(p.source == "openalex" for p in papers)

    async def test_search_works_citation_sort(self, respx_mock, mock_openalex_search):
        client = OpenAlexClient()
        papers = await client.search_works("attention mechanism", sort="citations", per_page=5)
        await client.close()
        citations = [p.citation_count or 0 for p in papers]
        assert citations == sorted(citations, reverse=True)

    async def test_search_topics(self, respx_mock, mock_openalex_topics):
        client = OpenAlexClient()
        topics = await client.search_topics("machine learning")
        await client.close()
        assert len(topics) > 0
        assert "display_name" in topics[0]
