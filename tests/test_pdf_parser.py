import pytest
from pathlib import Path
from app.utils import pdf_parser

@pytest.fixture
def sample_text():
    return (
        "A Sample Paper Title\n"
        "John Doe, Jane Smith\n"
        "Department of Computer Science\n"
        "University of Somewhere\n"
        "Abstract\n"
        "This is the abstract section.\n"
        "Introduction\n"
        "This is the introduction section.\n"
        "Methods\n"
        "Method details here.\n"
        "Conclusion\n"
        "Final thoughts."
    )

def test_normalize():
    assert pdf_parser._normalize("  Hello   World \n") == "Hello World"

def test_split_sections(sample_text):
    sections = pdf_parser.split_sections(sample_text)
    assert "abstract" in sections
    assert "introduction" in sections
    assert "methods" in sections
    assert "conclusion" in sections
    assert sections["abstract"].startswith("Abstract")
    assert sections["conclusion"].endswith("Final thoughts.")

def test_is_likely_author():
    assert pdf_parser.is_likely_author("John Doe")
    assert pdf_parser.is_likely_author("Jane A. Smith")
    assert not pdf_parser.is_likely_author("Department of Computer Science")
    assert not pdf_parser.is_likely_author("University of Somewhere")
    assert not pdf_parser.is_likely_author("J")

def test_guess_title_and_authors(sample_text):
    title, authors = pdf_parser.guess_title_and_authors(sample_text)
    assert title == "A Sample Paper Title"
    assert "John Doe" in authors
    assert "Jane Smith" in authors

def test_chunk_text():
    text = "word " * 1000
    chunks = pdf_parser.chunk_text("body", text, max_tokens=100)
    assert len(chunks) > 1
    assert all(isinstance(c, str) for c in chunks)

def test_parse_pdf(monkeypatch, sample_text):
    # Patch extract_text_blocks to return sample_text
    monkeypatch.setattr(pdf_parser, "extract_text_blocks", lambda path: sample_text)
    result = pdf_parser.parse_pdf(Path("dummy.pdf"))
    assert result["title"] == "A Sample Paper Title"
    assert "John Doe" in result["authors"]
    assert "abstract" in result["sections"]
    assert isinstance(result["chunks"], list)
    assert any("abstract" in sec for sec, _ in result["chunks"])