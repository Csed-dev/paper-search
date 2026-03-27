# Contributing to paper-search

## Reporting Bugs

Use the GitHub issue tracker. Search existing issues first. Include: steps to reproduce, expected vs actual behavior, Python version.

## Pull Requests

1. Fork the repository
2. Create a feature branch from `main`
3. Make changes with tests
4. Ensure all tests pass (`uv run pytest`)
5. Submit a pull request

## Development Setup

```bash
git clone https://github.com/YOUR_FORK/paper-search.git
cd paper-search
uv sync --group dev
uv run pytest
```

## Running Tests

Tests use saved API fixtures -- no network calls needed:

```bash
uv run pytest tests/ -v
```

To update fixtures from live APIs (rate limits apply):

```bash
uv run python tests/capture_fixtures.py
```

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `test:` tests
- `chore:` maintenance
