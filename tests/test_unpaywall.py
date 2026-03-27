import respx

from paper_search.apis.unpaywall import UnpaywallClient, _parse_oa_location


class TestParseOALocation:
    def test_with_pdf(self):
        loc = _parse_oa_location({
            "url_for_pdf": "https://example.com/paper.pdf",
            "url_for_landing_page": "https://example.com/paper",
            "license": "cc-by",
            "version": "publishedVersion",
        })
        assert loc is not None
        assert loc.url == "https://example.com/paper.pdf"
        assert loc.url_pdf == "https://example.com/paper.pdf"
        assert loc.license == "cc-by"

    def test_fallback_to_landing_page(self):
        loc = _parse_oa_location({
            "url_for_pdf": None,
            "url": None,
            "url_for_landing_page": "https://example.com/paper",
        })
        assert loc is not None
        assert loc.url == "https://example.com/paper"
        assert loc.url_pdf is None

    def test_all_urls_missing(self):
        loc = _parse_oa_location({"url_for_pdf": None, "url": None, "url_for_landing_page": None})
        assert loc is None

    def test_real_fixture(self, unpaywall_oa_fixture):
        locations = unpaywall_oa_fixture["body"]["oa_locations"]
        parsed = [_parse_oa_location(loc) for loc in locations]
        valid = [p for p in parsed if p is not None]
        assert len(valid) > 0


class TestUnpaywallClient:
    async def test_oa_paper(self, respx_mock, mock_unpaywall_oa):
        client = UnpaywallClient(email="test@papersearch.dev")
        locations = await client.get_oa_locations("10.1038/nature12373")
        await client.close()
        assert len(locations) > 0
        assert any(loc.url_pdf for loc in locations)

    async def test_closed_paper(self, respx_mock, mock_unpaywall_closed):
        client = UnpaywallClient(email="test@papersearch.dev")
        locations = await client.get_oa_locations("10.1016/j.compstruct.2020.112680")
        await client.close()
        assert locations == []

    async def test_not_found(self, respx_mock):
        respx_mock.get("https://api.unpaywall.org/v2/10.9999%2Fnonexistent").respond(status_code=404, text="Not Found")
        client = UnpaywallClient(email="test@papersearch.dev")
        locations = await client.get_oa_locations("10.9999/nonexistent")
        await client.close()
        assert locations == []
