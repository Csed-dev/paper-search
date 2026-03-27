from pydantic import BaseModel


class Author(BaseModel):
    name: str
    affiliation: str | None = None
    orcid: str | None = None


class OALocation(BaseModel):
    url: str
    url_pdf: str | None = None
    license: str | None = None
    version: str | None = None


class Paper(BaseModel):
    title: str
    doi: str | None = None
    abstract: str | None = None
    tldr: str | None = None
    authors: list[Author] = []
    publication_year: int | None = None
    publication_date: str | None = None
    citation_count: int | None = None
    influential_citation_count: int | None = None
    topics: list[str] = []
    fields_of_study: list[str] = []
    is_open_access: bool = False
    oa_locations: list[OALocation] = []
    source: str = ""
    external_ids: dict[str, str] = {}
