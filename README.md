# paper-search

Search and rank scientific papers across multiple academic APIs from the command line.

Queries OpenAlex (250M+ works), Semantic Scholar (215M+ papers), and Unpaywall in parallel, merges results by DOI, and outputs ranked papers with citation counts, TLDRs, and PDF links. Use `--save` to persist results to `.claude/papers.md` for use as project context in Claude Code.

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
paper-search search "large language models" -n 10

# Filter by year
paper-search search "vision transformers" --year 2024 --sort date

# Find similar papers (accepts DOI, arXiv ID, or Semantic Scholar ID)
paper-search recommend 1706.03762 -n 10

# Save results to .claude/papers.md in current project
paper-search search "reinforcement learning" --save

# Enable PDF links via Unpaywall
paper-search search "graph neural networks" --email you@example.com
```

## Example Output

```
$ paper-search search "attention mechanism" -n 5

  Results for: attention mechanism
  5 papers, sorted by citations

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
paper-search search "query"
        |
        +--- OpenAlex ---------- phrase search, topic taxonomy, citation ranking
        |
        +--- Semantic Scholar -- TLDR summaries, influential citations
        |
        +--- Unpaywall --------- OA PDF links (when --email is set)
        |
        v
    Merge by DOI -> Rank -> Display / Save
```

Results include: title, authors, citation count (with influential count from S2), abstract, TLDR, DOI, PDF link, and topics.

## Commands

### `search` (alias: `s`)

```
paper-search search "query" [options]
```

| Flag | Description |
|------|-------------|
| `-n, --limit N` | Number of results (default: 10) |
| `-y, --year YYYY` | Filter by publication year |
| `--sort citations\|date\|relevance` | Sort order (default: citations) |
| `--save` | Append results to `.claude/papers.md` |
| `--email EMAIL` | Enable Unpaywall PDF links + faster OpenAlex |
| `--s2-key KEY` | Semantic Scholar API key |

### `recommend` (alias: `r`)

```
paper-search recommend <paper_id> [options]
```

Accepts DOI (`10.1038/s41586-023-06291-2`), arXiv ID (`1706.03762`, `hep-th/9905111`), or Semantic Scholar ID.

Same `--save`, `--email`, `--s2-key`, `-n` flags as search.

## Environment Variables

Set these to avoid passing flags every time:

| Variable | Description |
|----------|-------------|
| `PAPER_SEARCH_EMAIL` | Email for OpenAlex polite pool + Unpaywall |
| `PAPER_SEARCH_S2_KEY` | Semantic Scholar API key |

## The `--save` Flag

When used inside a project directory, `--save` writes results to `.claude/papers.md`. This file persists as context for Claude Code, making your paper references available in future conversations.

```bash
cd my-research-project
paper-search search "federated learning" -n 15 --save
# Creates .claude/papers.md with formatted paper references
```

Running the same query twice with `--save` won't duplicate the section.

## API Keys (Free)

Both APIs offer free keys for higher rate limits:

- **OpenAlex**: Get a key at [openalex.org/settings/api](https://openalex.org/settings/api) ($1/day free)
- **Semantic Scholar**: Request at [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api#api-key) (~1 month wait)

The tool works without keys, just with lower rate limits.

## Development

```bash
git clone https://github.com/Csed-dev/paper-search.git
cd paper-search
uv sync --group dev
uv run pytest
```

Tests use captured API fixtures (no network calls):

```bash
uv run pytest tests/ -v    # 71 tests, runs in <1s
```

To refresh fixtures from live APIs:

```bash
uv run python tests/capture_fixtures.py
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE)
