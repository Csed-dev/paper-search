from datetime import date
from unittest.mock import patch

from paper_search.formatter import format_markdown, format_terminal
from paper_search.models.paper import Author, OALocation, Paper

SAMPLE_PAPER = Paper(
    title="Attention Is All You Need",
    doi="10.48550/arXiv.1706.03762",
    abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
    tldr="A new network architecture based solely on attention mechanisms.",
    authors=[Author(name="Ashish Vaswani"), Author(name="Noam Shazeer")],
    publication_year=2017,
    citation_count=170000,
    influential_citation_count=19000,
    is_open_access=True,
    oa_locations=[OALocation(url="https://arxiv.org/pdf/1706.03762", url_pdf="https://arxiv.org/pdf/1706.03762")],
    topics=["Natural Language Processing", "Deep Learning"],
    source="merged",
)


class TestFormatTerminal:
    def test_includes_title(self):
        output = format_terminal([SAMPLE_PAPER], query="test")
        assert "Attention Is All You Need" in output

    def test_includes_citations(self):
        output = format_terminal([SAMPLE_PAPER], query="test")
        assert "170000 citations" in output
        assert "19000 influential" in output

    def test_includes_doi(self):
        output = format_terminal([SAMPLE_PAPER], query="test")
        assert "10.48550/arXiv.1706.03762" in output

    def test_includes_pdf_link(self):
        output = format_terminal([SAMPLE_PAPER], query="test")
        assert "https://arxiv.org/pdf/1706.03762" in output

    def test_includes_tldr(self):
        output = format_terminal([SAMPLE_PAPER], query="test")
        assert "TLDR:" in output

    def test_sort_label(self):
        assert "sorted by relevance" in format_terminal([SAMPLE_PAPER], query="q", sort="relevance")
        assert "sorted by date" in format_terminal([SAMPLE_PAPER], query="q", sort="date")

    def test_oa_marker(self):
        output = format_terminal([SAMPLE_PAPER], query="test")
        assert "[OA]" in output

    def test_author_limit(self):
        many_authors = [Author(name=f"Author {i}") for i in range(8)]
        paper = SAMPLE_PAPER.model_copy(update={"authors": many_authors})
        output = format_terminal([paper], query="test")
        assert "+3 more" in output

    def test_empty_list(self):
        output = format_terminal([], query="test")
        assert "0 papers" in output


class TestFormatMarkdown:
    def test_header(self):
        output = format_markdown([SAMPLE_PAPER], query="LLM research")
        assert "## LLM research" in output
        assert date.today().isoformat() in output

    def test_paper_section(self):
        output = format_markdown([SAMPLE_PAPER], query="test")
        assert "### 1. Attention Is All You Need (2017)" in output
        assert "**Authors:** Ashish Vaswani, Noam Shazeer" in output
        assert "**Citations:** 170000 (19000 influential)" in output
        assert "**Open Access:** Yes" in output
        assert "**DOI:** 10.48550/arXiv.1706.03762" in output

    def test_tldr_blockquote(self):
        output = format_markdown([SAMPLE_PAPER], query="test")
        assert "> A new network architecture" in output

    def test_pdf_link(self):
        output = format_markdown([SAMPLE_PAPER], query="test")
        assert "**PDF:** https://arxiv.org/pdf/1706.03762" in output

    def test_topics(self):
        output = format_markdown([SAMPLE_PAPER], query="test")
        assert "**Topics:** Natural Language Processing, Deep Learning" in output

    def test_no_double_blank_lines(self):
        output = format_markdown([SAMPLE_PAPER], query="test")
        assert "\n\n\n" not in output
