import httpx
from pydantic import BaseModel

BASE_URL = "https://api.github.com"


class Repository(BaseModel):
    full_name: str
    description: str | None = None
    url: str
    stars: int
    language: str | None = None
    updated_at: str
    topics: list[str] = []


def _parse_repo(item: dict) -> Repository:
    return Repository(
        full_name=item["full_name"],
        description=item.get("description"),
        url=item["html_url"],
        stars=item.get("stargazers_count", 0),
        language=item.get("language"),
        updated_at=item.get("updated_at", "")[:10],
        topics=item.get("topics", []),
    )


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=30)

    async def search_repos(
        self,
        query: str,
        *,
        sort: str = "stars",
        language: str | None = None,
        min_stars: int | None = None,
        per_page: int = 10,
    ) -> list[Repository]:
        q_parts = [query]
        if language:
            q_parts.append(f"language:{language}")
        if min_stars:
            q_parts.append(f"stars:>={min_stars}")

        params: dict[str, str | int] = {
            "q": " ".join(q_parts),
            "sort": sort,
            "order": "desc",
            "per_page": min(per_page, 100),
        }

        response = await self._client.get("/search/repositories", params=params)
        response.raise_for_status()
        return [_parse_repo(item) for item in response.json().get("items", [])]

    async def close(self) -> None:
        await self._client.aclose()
