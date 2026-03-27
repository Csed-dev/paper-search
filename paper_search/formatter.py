import json
import re
from datetime import date

from paper_search.models.paper import Paper


def format_terminal(papers: list[Paper], *, query: str, sort: str = "citations") -> str:
    lines = [f"  Results for: {query}", f"  {len(papers)} papers, sorted by {sort}", ""]
    for i, p in enumerate(papers, 1):
        citations = f"[{p.citation_count} citations]" if p.citation_count is not None else ""
        influential = f" ({p.influential_citation_count} influential)" if p.influential_citation_count else ""
        year = f" ({p.publication_year})" if p.publication_year else ""
        oa = " [OA]" if p.is_open_access else ""
        lines.append(f"  {i:>3}. {p.title}{year} {citations}{influential}{oa}")

        if p.authors:
            author_names = ", ".join(a.name for a in p.authors[:5])
            if len(p.authors) > 5:
                author_names += f" +{len(p.authors) - 5} more"
            lines.append(f"       {author_names}")

        if p.tldr:
            lines.append(f"       TLDR: {p.tldr}")

        if p.doi:
            lines.append(f"       DOI: {p.doi}")

        pdf_urls = [loc.url_pdf for loc in p.oa_locations if loc.url_pdf]
        if pdf_urls:
            lines.append(f"       PDF: {pdf_urls[0]}")

        lines.append("")
    return "\n".join(lines)


def format_markdown(papers: list[Paper], *, query: str) -> str:
    today = date.today().isoformat()
    lines = [f"## {query}", f"", f"*Searched on {today}, {len(papers)} results*", ""]

    for i, p in enumerate(papers, 1):
        year = f" ({p.publication_year})" if p.publication_year else ""
        lines.append(f"### {i}. {p.title}{year}")
        lines.append("")

        if p.authors:
            author_names = ", ".join(a.name for a in p.authors[:5])
            if len(p.authors) > 5:
                author_names += f" +{len(p.authors) - 5} more"
            lines.append(f"**Authors:** {author_names}")

        if p.citation_count is not None:
            influential = f" ({p.influential_citation_count} influential)" if p.influential_citation_count else ""
            lines.append(f"**Citations:** {p.citation_count}{influential}")

        if p.is_open_access:
            lines.append("**Open Access:** Yes")

        if p.doi:
            lines.append(f"**DOI:** {p.doi}")

        if p.tldr:
            lines.append("")
            lines.append(f"> {p.tldr}")

        if p.abstract:
            short = p.abstract[:300] + "..." if len(p.abstract) > 300 else p.abstract
            lines.append("")
            lines.append(short)

        pdf_urls = [loc.url_pdf for loc in p.oa_locations if loc.url_pdf]
        if pdf_urls:
            lines.append("")
            lines.append(f"**PDF:** {pdf_urls[0]}")

        if p.topics:
            lines.append("")
            lines.append(f"**Topics:** {', '.join(p.topics[:5])}")

        lines.append("")
    return "\n".join(lines)


def format_json(papers: list[Paper]) -> str:
    return json.dumps([p.model_dump(exclude_none=True) for p in papers], indent=2, ensure_ascii=False)


def _generate_bibtex_key(paper: Paper) -> str:
    first_author = paper.authors[0].name.split()[-1] if paper.authors else "Unknown"
    first_author = re.sub(r"[^a-zA-Z]", "", first_author)
    year = paper.publication_year or "nd"
    title_word = re.sub(r"[^a-zA-Z]", "", (paper.title.split() or ["untitled"])[0])
    return f"{first_author}{year}{title_word}"


def _generate_bibtex_entry(paper: Paper, *, key: str | None = None) -> str:
    if key is None:
        key = _generate_bibtex_key(paper)
    authors = " and ".join(a.name for a in paper.authors)
    lines = [f"@article{{{key},"]
    lines.append(f"  title = {{{paper.title}}},")
    if authors:
        lines.append(f"  author = {{{authors}}},")
    if paper.publication_year:
        lines.append(f"  year = {{{paper.publication_year}}},")
    if paper.doi:
        lines.append(f"  doi = {{{paper.doi}}},")
    if paper.abstract:
        lines.append(f"  abstract = {{{paper.abstract[:500]}}},")
    lines.append("}")
    return "\n".join(lines)


def format_bibtex(papers: list[Paper]) -> str:
    seen_keys: dict[str, int] = {}
    entries = []
    for p in papers:
        if p.bibtex:
            entries.append(p.bibtex)
        else:
            key = _generate_bibtex_key(p)
            count = seen_keys.get(key, 0)
            seen_keys[key] = count + 1
            if count > 0:
                key = f"{key}{chr(ord('a') + count)}"
            entries.append(_generate_bibtex_entry(p, key=key))
    return "\n\n".join(entries) + "\n"
