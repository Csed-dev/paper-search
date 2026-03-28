import argparse
import asyncio
import os
import re
import sys
import webbrowser
from pathlib import Path

from paper_search.config import load_config
from paper_search.formatter import format_bibtex, format_json, format_markdown, format_terminal, format_repos_terminal
from paper_search.search import search_papers, recommend_papers


def _validate_year(value: str) -> str:
    if "-" in value:
        parts = value.split("-", 1)
        if not all(p.isdigit() for p in parts if p):
            raise argparse.ArgumentTypeError(f"Invalid year range: {value} (expected e.g. 2022-2024)")
    elif not value.isdigit():
        raise argparse.ArgumentTypeError(f"Invalid year: {value} (expected e.g. 2024 or 2022-2024)")
    return value


def _resolve_option(args_val: str | None, env_key: str, config: dict, config_key: str) -> str | None:
    return args_val or os.environ.get(env_key) or config.get(config_key)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paper-search",
        description="Search and rank scientific papers across OpenAlex, Semantic Scholar, and Unpaywall",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("papers", aliases=["p"], help="Search papers by query")
    search.add_argument("query", help="Search query (topic, title, keywords)")
    search.add_argument("-n", "--limit", type=int, default=10, help="Number of results (default: 10)")
    search.add_argument("-y", "--year", type=_validate_year, help="Publication year or range (e.g. 2024, 2022-2024)")
    search.add_argument("--sort", choices=["citations", "date", "relevance"], default="citations", help="Sort order (default: citations)")

    recommend = subparsers.add_parser("recommend", aliases=["r"], help="Find similar papers to a given paper")
    recommend.add_argument("paper_id", help="DOI, arXiv ID, or Semantic Scholar ID")
    recommend.add_argument("-n", "--limit", type=int, default=10, help="Number of recommendations (default: 10)")

    repos = subparsers.add_parser("repos", help="Search GitHub repositories")
    repos.add_argument("query", help="Search query")
    repos.add_argument("-n", "--limit", type=int, default=10, help="Number of results (default: 10)")
    repos.add_argument("--sort", choices=["stars", "forks", "updated"], default="stars", help="Sort order (default: stars)")
    repos.add_argument("--language", help="Filter by programming language (e.g. python)")
    repos.add_argument("--min-stars", type=int, help="Minimum star count")
    repos.add_argument("--json", action="store_true", dest="json_output", help="Output JSON format")
    repos.add_argument("-o", "--output", help="Write output to file")

    open_cmd = subparsers.add_parser("open", help="Open a paper's PDF in the browser")
    open_cmd.add_argument("paper_id", help="DOI, arXiv ID, or Semantic Scholar ID")

    for sub in [search, recommend, open_cmd]:
        sub.add_argument("--email", help="Email for polite API access (env: PAPER_SEARCH_EMAIL)")
        sub.add_argument("--s2-key", help="Semantic Scholar API key (env: PAPER_SEARCH_S2_KEY)")

    for sub in [search, recommend]:
        sub.add_argument("--save", action="store_true", help="Save results to .claude/papers.md in current directory")
        sub.add_argument("--bibtex", action="store_true", help="Output BibTeX format")
        sub.add_argument("--json", action="store_true", dest="json_output", help="Output JSON format")
        sub.add_argument("-o", "--output", help="Write output to file (e.g. refs.bib)")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config()

    if args.command == "repos":
        _handle_repos(args, config)
        return

    email = _resolve_option(getattr(args, "email", None), "PAPER_SEARCH_EMAIL", config, "email")
    s2_key = _resolve_option(getattr(args, "s2_key", None), "PAPER_SEARCH_S2_KEY", config, "s2_key")

    if args.command == "open":
        _handle_open(args.paper_id, email=email, s2_api_key=s2_key)
        return

    if args.command in ("papers", "p"):
        papers = asyncio.run(search_papers(
            query=args.query,
            limit=args.limit,
            year=args.year,
            sort=args.sort,
            email=email,
            s2_api_key=s2_key,
        ))
        label = args.query
    else:
        papers = asyncio.run(recommend_papers(
            paper_id=args.paper_id,
            limit=args.limit,
            email=email,
            s2_api_key=s2_key,
        ))
        label = f"similar to {args.paper_id}"

    if not papers:
        print("No papers found.")
        sys.exit(1)

    if args.json_output:
        output = format_json(papers)
    elif args.bibtex:
        output = format_bibtex(papers)
    else:
        sort = args.sort if args.command in ("papers", "p") else "relevance"
        output = format_terminal(papers, query=label, sort=sort)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Written to {args.output}")
    else:
        print(output)

    if args.save:
        _save_to_claude_dir(papers, query=label)


def _handle_repos(args: argparse.Namespace, config: dict) -> None:
    from paper_search.apis.github import GitHubClient

    token = _resolve_option(None, "GITHUB_TOKEN", config, "github_token")

    async def _fetch():
        client = GitHubClient(token=token)
        try:
            return await client.search_repos(
                args.query,
                sort=args.sort,
                language=args.language,
                min_stars=args.min_stars,
                per_page=args.limit,
            )
        finally:
            await client.close()

    repos = asyncio.run(_fetch())

    if not repos:
        print("No repositories found.")
        sys.exit(1)

    if args.json_output:
        output = format_json(repos)
    else:
        output = format_repos_terminal(repos, query=args.query, sort=args.sort)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Written to {args.output}")
    else:
        print(output)


def _handle_open(paper_id: str, *, email: str | None, s2_api_key: str | None) -> None:
    from paper_search.apis.semantic_scholar import SemanticScholarClient
    from paper_search.search import _resolve_paper_id

    async def _fetch() -> str | None:
        client = SemanticScholarClient(api_key=s2_api_key)
        try:
            resolved = _resolve_paper_id(paper_id)
            paper = await client.get_paper(resolved)
            pdf_urls = [loc.url_pdf for loc in paper.oa_locations if loc.url_pdf]
            if pdf_urls:
                return pdf_urls[0]
            if paper.doi:
                return f"https://doi.org/{paper.doi}"
            return None
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return None
        finally:
            await client.close()

    url = asyncio.run(_fetch())
    if not url:
        print("No URL found for this paper.")
        sys.exit(1)
    print(f"Opening {url}")
    webbrowser.open(url)


def _save_to_claude_dir(papers: list, *, query: str) -> None:
    claude_dir = Path.cwd() / ".claude"
    claude_dir.mkdir(exist_ok=True)
    papers_file = claude_dir / "papers.md"

    new_section = format_markdown(papers, query=query)

    if papers_file.exists():
        existing = papers_file.read_text()
        if re.search(rf"^## {re.escape(query)}$", existing, re.MULTILINE):
            print(f"Section for '{query}' already exists in {papers_file}, skipping.")
            return
        papers_file.write_text(existing.rstrip() + "\n\n" + new_section)
    else:
        header = "# Research Papers\n\nRelevant scientific papers for this project.\n\n"
        papers_file.write_text(header + new_section)

    print(f"Saved to {papers_file}")


if __name__ == "__main__":
    main()
