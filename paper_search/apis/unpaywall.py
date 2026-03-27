from urllib.parse import quote

import httpx

from paper_search.models.paper import OALocation

BASE_URL = "https://api.unpaywall.org/v2"


def _parse_oa_location(loc: dict) -> OALocation | None:
    url = loc.get("url_for_pdf") or loc.get("url") or loc.get("url_for_landing_page")
    if not url:
        return None
    return OALocation(
        url=url,
        url_pdf=loc.get("url_for_pdf"),
        license=loc.get("license"),
        version=loc.get("version"),
    )


class UnpaywallClient:
    def __init__(self, email: str) -> None:
        self.email = email
        self._client = httpx.AsyncClient(base_url=BASE_URL, timeout=30)

    async def get_oa_locations(self, doi: str) -> list[OALocation]:
        encoded_doi = quote(doi, safe="")
        response = await self._client.get(f"/{encoded_doi}", params={"email": self.email})
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()
        if not data.get("is_oa"):
            return []
        locations = [_parse_oa_location(loc) for loc in data.get("oa_locations", [])]
        return [loc for loc in locations if loc is not None]

    async def close(self) -> None:
        await self._client.aclose()
