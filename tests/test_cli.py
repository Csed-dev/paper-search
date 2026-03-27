from pathlib import Path

from paper_search.cli import save_to_claude_dir
from paper_search.models.paper import Paper

SAMPLE_PAPERS = [
    Paper(title="Paper A", doi="10.1234/a", citation_count=100, publication_year=2023, source="test"),
    Paper(title="Paper B", doi="10.1234/b", citation_count=50, publication_year=2024, source="test"),
]


class TestSaveToClaude:
    def test_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        save_to_claude_dir(SAMPLE_PAPERS, query="test query")
        papers_file = tmp_path / ".claude" / "papers.md"
        assert papers_file.exists()
        content = papers_file.read_text()
        assert "# Research Papers" in content
        assert "## test query" in content
        assert "Paper A" in content
        assert "Paper B" in content

    def test_appends_new_section(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        save_to_claude_dir(SAMPLE_PAPERS, query="first query")
        save_to_claude_dir(SAMPLE_PAPERS, query="second query")
        content = (tmp_path / ".claude" / "papers.md").read_text()
        assert "## first query" in content
        assert "## second query" in content

    def test_skips_duplicate_query(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        save_to_claude_dir(SAMPLE_PAPERS, query="test query")
        save_to_claude_dir(SAMPLE_PAPERS, query="test query")
        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_creates_claude_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert not (tmp_path / ".claude").exists()
        save_to_claude_dir(SAMPLE_PAPERS, query="test")
        assert (tmp_path / ".claude").is_dir()
