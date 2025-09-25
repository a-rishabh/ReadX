# app/utils/pdf_parser.py
from __future__ import annotations
import re
from pathlib import Path
import fitz  # PyMuPDF

SECTION_HEADINGS = [
    "abstract", "introduction", "background", "related work", "methods",
    "method", "approach", "experiments", "results", "discussion",
    "conclusion", "acknowledgements", "references"
]

def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def extract_text_blocks(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    texts = []
    for page in doc:
        texts.append(page.get_text("text"))
    return "\n".join(texts)

def split_sections(full_text: str) -> dict[str, str]:
    # Heuristic section splitter on common headings
    text = full_text
    indices = []
    for m in re.finditer(
        r"(?im)^(abstract|introduction|background|related work|methods?|approach|experiments?|results?|discussion|conclusions?|acknowledgements|references)\s*$",
        text
    ):
        indices.append((m.start(), m.group(1).lower()))

    indices.sort()
    sections = {}
    if not indices:
        sections["body"] = text
        return sections

    for i, (start, name) in enumerate(indices):
        end = indices[i + 1][0] if i + 1 < len(indices) else len(text)
        sections[name] = text[start:end].strip()

    return sections

def guess_title_and_authors(full_text: str) -> tuple[str | None, list[str]]:
    # Super simple heuristic: title = first non-empty line not too long,
    # authors = next line with commas and without too many words
    lines = [l.strip() for l in full_text.splitlines() if l.strip()]
    title = None
    authors = []
    for i, line in enumerate(lines[:40]):
        if 5 < len(line) < 200 and not line.lower().startswith(("arxiv", "doi:", "preprint")):
            title = _normalize(line)
            # Try next 1-2 lines for authors
            cands = lines[i+1:i+3]
            for c in cands:
                # crude author line detection
                if ("," in c or " and " in c) and len(c) < 200 and not c.lower().startswith(("abstract", "introduction")):
                    # strip affiliations markers like * † 1 2
                    c = re.sub(r"[\*\†\d\^]", "", c)
                    parts = [p.strip() for p in re.split(r",| and ", c) if p.strip()]
                    # filter likely not author tokens
                    parts = [p for p in parts if 2 <= len(p.split()) <= 4]
                    if parts:
                        authors = parts
                        return title, authors
            break
    return title, authors

def chunk_text(section_name: str, text: str, max_tokens: int = 800) -> list[str]:
    # token-agnostic approx: assume ~1.3 words per token; use words count
    words = text.split()
    max_words = max(200, int(max_tokens * 1.3))
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i:i+max_words]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks

def parse_pdf(pdf_path: Path) -> dict:
    full_text = extract_text_blocks(pdf_path)
    sections = split_sections(full_text)
    title, authors = guess_title_and_authors(full_text)

    abstract = None
    for key in ("abstract",):
        if key in sections:
            # remove the heading word
            abstract = re.sub(r"(?i)^abstract", "", sections[key]).strip()
            break

    # Create (section, chunk) pairs
    chunk_pairs: list[tuple[str, str]] = []
    for sec, txt in sections.items():
        chunks = chunk_text(sec, txt)
        for c in chunks:
            chunk_pairs.append((sec, c))

    return {
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "year": None,   # (optional) later via metadata/doi
        "venue": None,  # (optional)
        "sections": sections,
        "chunks": chunk_pairs
    }
