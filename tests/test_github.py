import json
from pathlib import Path

from paper_search.apis.github import GitHubClient, Repository, _parse_repo

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture():
    return json.loads((FIXTURES_DIR / "github_search.json").read_text())


class TestParseRepo:
    def test_parses_fixture(self):
        fixture = _load_fixture()
        item = fixture["body"]["items"][0]
        repo = _parse_repo(item)
        assert repo.full_name
        assert repo.url.startswith("https://github.com/")
        assert repo.stars > 0

    def test_handles_missing_description(self):
        repo = _parse_repo({
            "full_name": "test/repo",
            "html_url": "https://github.com/test/repo",
            "stargazers_count": 42,
            "updated_at": "2026-01-01T00:00:00Z",
        })
        assert repo.description is None
        assert repo.stars == 42

    def test_topics_parsed(self):
        fixture = _load_fixture()
        items_with_topics = [i for i in fixture["body"]["items"] if i.get("topics")]
        if items_with_topics:
            repo = _parse_repo(items_with_topics[0])
            assert len(repo.topics) > 0


class TestGitHubClient:
    async def test_search_repos(self, respx_mock):
        fixture = _load_fixture()
        respx_mock.get("https://api.github.com/search/repositories").respond(
            status_code=200, json=fixture["body"],
        )
        client = GitHubClient()
        repos = await client.search_repos("transformer attention", per_page=5)
        await client.close()
        assert len(repos) == 5
        assert all(isinstance(r, Repository) for r in repos)
        assert all(r.stars > 0 for r in repos)
