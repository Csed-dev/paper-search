# paper-search

Search and rank scientific papers and GitHub repositories from the command line.

Queries OpenAlex (250M+ works), Semantic Scholar (215M+ papers), and Unpaywall in parallel, merges results by DOI, and outputs ranked papers with citation counts, TLDRs, and PDF links. Search GitHub for related code repositories. Export as BibTeX or JSON, save to `.claude/papers.md` for project context, or open PDFs directly in the browser.

## Installation

```bash
uv tool install paper-search
```

Or from source:

```bash
git clone https://github.com/Csed-dev/paper-search.git
cd paper-search
uv sync
```

## Quick Start

```bash
# Search papers by topic, ranked by citations
paper-search papers "large language models" -n 10

# Filter by year or year range
paper-search papers "vision transformers" --year 2022-2024 --sort date

# Find similar papers (accepts DOI, arXiv ID, or Semantic Scholar ID)
paper-search recommend 1706.03762 -n 10

# Search GitHub repositories
paper-search repos "transformer attention" --language python --min-stars 100

# Export as BibTeX
paper-search papers "reinforcement learning" -n 5 --bibtex -o refs.bib

# Export as JSON for scripting
paper-search papers "graph neural networks" --json | jq '.[].title'

# Save results to .claude/papers.md in current project
paper-search papers "federated learning" --save

# Open a paper's PDF in the browser
paper-search open 1706.03762
```

## Example Output

```
$ paper-search papers "attention mechanism" -n 3

  Results for: attention mechanism
  3 papers, sorted by citations

    1. Faster R-CNN: Towards Real-Time Object Detection with Region Proposal Networks (2016) [52848 citations] (9606 influential) [OA]
       Shaoqing Ren, Kaiming He, Ross Girshick, Jian Sun
       DOI: 10.1109/tpami.2016.2577031
       PDF: https://arxiv.org/pdf/1506.01497

    2. Effective Approaches to Attention-based Neural Machine Translation (2015) [8517 citations] [OA]
       Thang Luong, Hieu Pham, Christopher D. Manning
       DOI: 10.18653/v1/d15-1166

    3. Attention mechanisms in computer vision: A survey (2022) [2242 citations] [OA]
       Meng-Hao Guo, Tian-Xing Xu, Jiangjiang Liu, Zheng-Ning Liu, Peng-Tao Jiang +5 more
       DOI: 10.1007/s41095-022-0271-y
       PDF: https://arxiv.org/pdf/2111.07624
```

## What It Does

```
paper-search papers "query"
        |
        +--- OpenAlex ---------- phrase search, topic taxonomy, citation ranking
        |
        +--- Semantic Scholar -- TLDR summaries, influential citations, BibTeX
        |
        +--- Unpaywall --------- OA PDF links (when --email is set)
        |
        v
    Merge by DOI -> Rank -> Display / Save / Export
```

## Commands

### `papers` (alias: `p`)

```
paper-search papers "query" [options]
```

| Flag | Description |
|------|-------------|
| `-n, --limit N` | Number of results (default: 10) |
| `-y, --year YEAR` | Publication year or range (e.g. `2024`, `2022-2024`) |
| `--sort citations\|date\|relevance` | Sort order (default: citations) |
| `--save` | Append results to `.claude/papers.md` |
| `--bibtex` | Output BibTeX format |
| `--json` | Output JSON format |
| `-o FILE` | Write output to file (e.g. `-o refs.bib`) |
| `--email EMAIL` | Enable Unpaywall PDF links + faster OpenAlex |
| `--s2-key KEY` | Semantic Scholar API key |

### `repos`

```
paper-search repos "query" [options]
```

| Flag | Description |
|------|-------------|
| `-n, --limit N` | Number of results (default: 10) |
| `--sort stars\|forks\|updated` | Sort order (default: stars) |
| `--language LANG` | Filter by programming language (e.g. `python`) |
| `--min-stars N` | Minimum star count |
| `--json` | Output JSON format |
| `-o FILE` | Write output to file |

Uses `GITHUB_TOKEN` env var if available (30 req/min vs 10 req/min without).

### `recommend` (alias: `r`)

```
paper-search recommend <paper_id> [options]
```

Accepts DOI (`10.1038/s41586-023-06291-2`), arXiv ID (`1706.03762`, `hep-th/9905111`), or Semantic Scholar ID.

Same flags as papers: `--save`, `--bibtex`, `--json`, `-o`, `--email`, `--s2-key`, `-n`.

### `open`

```
paper-search open <paper_id>
```

Opens the paper's PDF (or DOI landing page) in the default browser.

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `PAPER_SEARCH_EMAIL` | Email for OpenAlex polite pool + Unpaywall |
| `PAPER_SEARCH_S2_KEY` | Semantic Scholar API key |
| `GITHUB_TOKEN` | GitHub token for higher rate limits |

### Config File

Create `~/.config/paper-search/config.toml` to avoid passing flags every time:

```toml
email = "you@example.com"
s2_key = "your-semantic-scholar-api-key"
github_token = "ghp_..."
```

Priority: CLI flags > environment variables > config file.

## The `--save` Flag

When used inside a project directory, `--save` writes results to `.claude/papers.md`. This file persists as context for Claude Code, making your paper references available in future conversations.

```bash
cd my-research-project
paper-search papers "federated learning" -n 15 --save
# Creates .claude/papers.md with formatted paper references
```

Running the same query twice with `--save` won't duplicate the section.

## API Keys (Free)

All APIs work without keys, just with lower rate limits:

- **OpenAlex**: Get a key at [openalex.org/settings/api](https://openalex.org/settings/api) ($1/day free)
- **Semantic Scholar**: Request at [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api#api-key) (~1 month wait)
- **GitHub**: Use an existing `GITHUB_TOKEN` or create one at [github.com/settings/tokens](https://github.com/settings/tokens)

## Development

```bash
git clone https://github.com/Csed-dev/paper-search.git
cd paper-search
uv sync --group dev
uv run pytest
```

Tests use captured API fixtures (no network calls):

```bash
uv run pytest tests/ -v    # 84 tests, runs in <1s
```

To refresh fixtures from live APIs:

```bash
uv run python tests/capture_fixtures.py
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE)
