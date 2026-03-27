import argparse
import asyncio
import os
import sys
from pathlib import Path

from paper_search.search import search_papers, recommend_papers
from paper_search.formatter import format_terminal, format_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paper-search",
        description="Search and rank scientific papers across OpenAlex, Semantic Scholar, and Unpaywall",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", aliases=["s"], help="Search papers by query")
    search.add_argument("query", help="Search query (topic, title, keywords)")
    search.add_argument("-n", "--limit", type=int, default=10, help="Number of results (default: 10)")
    search.add_argument("-y", "--year", type=int, help="Filter by publication year")
    search.add_argument("--sort", choices=["citations", "date", "relevance"], default="citations", help="Sort order (default: citations)")

    recommend = subparsers.add_parser("recommend", aliases=["r"], help="Find similar papers to a given paper")
    recommend.add_argument("paper_id", help="DOI, arXiv ID, or Semantic Scholar ID")
    recommend.add_argument("-n", "--limit", type=int, default=10, help="Number of recommendations (default: 10)")

    for sub in [search, recommend]:
        sub.add_argument("--save", action="store_true", help="Save results to .claude/papers.md in current directory")
        sub.add_argument("--email", default=os.environ.get("PAPER_SEARCH_EMAIL"), help="Email for polite API access (env: PAPER_SEARCH_EMAIL)")
        sub.add_argument("--s2-key", default=os.environ.get("PAPER_SEARCH_S2_KEY"), help="Semantic Scholar API key (env: PAPER_SEARCH_S2_KEY)")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command in ("search", "s"):
        papers = asyncio.run(search_papers(
            query=args.query,
            limit=args.limit,
            year=args.year,
            sort=args.sort,
            email=args.email,
            s2_api_key=args.s2_key,
        ))
        label = args.query
    else:
        papers = asyncio.run(recommend_papers(
            paper_id=args.paper_id,
            limit=args.limit,
            email=args.email,
            s2_api_key=args.s2_key,
        ))
        label = f"similar to {args.paper_id}"

    if not papers:
        print("No papers found.")
        sys.exit(1)

    sort = args.sort if args.command in ("search", "s") else "relevance"
    print(format_terminal(papers, query=label, sort=sort))

    if args.save:
        save_to_claude_dir(papers, query=label)


def save_to_claude_dir(papers: list, *, query: str) -> None:
    claude_dir = Path.cwd() / ".claude"
    claude_dir.mkdir(exist_ok=True)
    papers_file = claude_dir / "papers.md"

    new_section = format_markdown(papers, query=query)

    if papers_file.exists():
        existing = papers_file.read_text()
        if f"## {query}" in existing:
            print(f"Section for '{query}' already exists in {papers_file}, skipping.")
            return
        papers_file.write_text(existing.rstrip() + "\n\n" + new_section)
    else:
        header = "# Research Papers\n\nRelevant scientific papers for this project.\n\n"
        papers_file.write_text(header + new_section)

    print(f"Saved to {papers_file}")


if __name__ == "__main__":
    main()
