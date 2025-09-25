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

import re

def is_likely_author(name: str) -> bool:
    # Must be 2–4 words
    parts = name.split()
    if not (2 <= len(parts) <= 4):
        return False

    # Each part should start with capital (allow initials like "J.")
    for p in parts:
        if not re.match(r"^[A-Z][a-zA-Z\-\.]*$", p):
            return False

    # Filter out affiliation keywords
    if any(k in name.lower() for k in ["university", "institute", "school", "department", "lab", "new york"]):
        return False

    return True

def guess_title_and_authors(full_text: str) -> tuple[str | None, list[str]]:
    lines = [l.strip() for l in full_text.splitlines() if l.strip()]

    # Title = first big line before abstract/introduction
    title = None
    for line in lines[:30]:
        if (
            5 < len(line) < 200
            and not re.match(r"(arxiv|doi:|preprint)", line, re.I)
            and not line.lower().startswith(("abstract", "introduction"))
        ):
            title = line.strip()
            break

    # Collect metadata zone (before Abstract/Introduction)
    authors_zone = []
    for line in lines:
        if re.match(r"(?i)(abstract|introduction)", line):
            break
        authors_zone.append(line)

    # Try to parse names
    candidates = []
    for line in authors_zone:
        if len(line) > 200 or "@" in line:
            continue
        clean = re.sub(r"[\*\†\d\^]", "", line)
        parts = re.split(r",| and ", clean)
        for p in parts:
            name = p.strip()
            if is_likely_author(name):
                candidates.append(name)

    authors = list(dict.fromkeys(candidates))
    return title, authors

# def guess_title_and_authors(full_text: str) -> tuple[str | None, list[str]]:
#     lines = [l.strip() for l in full_text.splitlines() if l.strip()]

#     # Guess title: first non-empty line that isn't metadata
#     title = None
#     for line in lines[:30]:
#         if (
#             5 < len(line) < 200
#             and not re.match(r"(arxiv|doi:|preprint)", line, re.I)
#             and not line.lower().startswith(("abstract", "introduction"))
#         ):
#             title = line.strip()
#             break

#     # Find metadata zone: lines until Abstract/Introduction
#     authors_zone = []
#     for line in lines:
#         if re.match(r"(?i)(abstract|introduction)", line):
#             break
#         authors_zone.append(line)

#     # Filter possible author lines
#     candidates = []
#     for line in authors_zone:
#         if len(line) > 200:  # skip huge affiliation lines
#             continue
#         if "@" in line or "university" in line.lower() or "institute" in line.lower():
#             continue
#         # remove footnotes/symbols
#         clean = re.sub(r"[\*\†\d\^]", "", line)
#         # possible multiple authors in one line
#         parts = re.split(r",| and ", clean)
#         for p in parts:
#             name = p.strip()
#             if 2 <= len(name.split()) <= 4:  # heuristically a name
#                 candidates.append(name)

#     authors = list(dict.fromkeys(candidates))  # unique, keep order
#     return title, authors

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
