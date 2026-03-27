# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## 0.1.0 (2026-03-27)


### Features

* initial release of paper-search CLI ([6acdca8](https://github.com/Csed-dev/paper-search/commit/6acdca839edebc9facee31628aaf8aacb788b06c))

## [Unreleased]

## [0.1.0] - 2026-03-27

### Added

- Search papers across OpenAlex and Semantic Scholar with `paper-search search`
- Find similar papers with `paper-search recommend`
- Merge results by DOI with TLDR and influential citation enrichment from Semantic Scholar
- Unpaywall integration for OA PDF links (via `--email`)
- `--save` flag to persist results to `.claude/papers.md`
- Environment variable support (`PAPER_SEARCH_EMAIL`, `PAPER_SEARCH_S2_KEY`)
- Offline test suite with captured API fixtures (71 tests)
