# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-03-27

### Added

- BibTeX output (`--bibtex`) with Semantic Scholar citation data and fallback generator
- JSON output (`--json`) for scripting and piping
- File output (`-o refs.bib`) to write results to any file
- Year range filter (`--year 2022-2024`) in addition to single year
- Config file support (`~/.config/paper-search/config.toml`) for email and API keys
- `paper-search open` command to open a paper's PDF in the browser

## [0.1.0] - 2026-03-27

### Added

- Search papers across OpenAlex and Semantic Scholar with `paper-search search`
- Find similar papers with `paper-search recommend`
- Merge results by DOI with TLDR and influential citation enrichment from Semantic Scholar
- Unpaywall integration for OA PDF links (via `--email`)
- `--save` flag to persist results to `.claude/papers.md`
- Environment variable support (`PAPER_SEARCH_EMAIL`, `PAPER_SEARCH_S2_KEY`)
- Offline test suite with captured API fixtures (71 tests)
