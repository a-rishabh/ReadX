# app/routers/paper.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import os

from app.storage import db
from app.storage import vector_store
from app.utils.pdf_parser import parse_pdf

from app.utils.grobid_client import parse_pdf_with_grobid, extract_authors_from_tei




router = APIRouter()

UPLOAD_DIR = Path("data/papers")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Ensure DB tables exist when this module loads
db.init_db()

@router.post("/upload")
async def upload_paper(file: UploadFile = File(...)):
    """
    Upload a research paper (PDF), parse it, store metadata/chunks in Postgres,
    and index chunks in Chroma for retrieval.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Save to disk
    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        f.write(await file.read())

    # Parse PDF → metadata + chunks
    try:
        parsed = parse_pdf(dest)
    except Exception as e:
        # cleanup if parse fails
        try:
            os.remove(dest)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {e}")

    tei_xml = parse_pdf_with_grobid(dest, service="processHeaderDocument")
    authors = extract_authors_from_tei(tei_xml)
    title = parsed.get("title")
    abstract = parsed.get("abstract")
    year = parsed.get("year")
    venue = parsed.get("venue")
    # authors = parsed.get("authors", [])
    chunks = parsed.get("chunks", [])

    # Insert paper row
    paper_id = db.insert_paper(
        filename=file.filename,
        title=title,
        abstract=abstract,
        year=year,
        venue=venue,
        path=str(dest),
    )

    # Upsert authors + link
    for a in authors:
        try:
            author_id = db.upsert_author(a)
            db.link_paper_author(paper_id, author_id)
        except Exception:
            # ignore single author failure; continue
            continue

    # Store chunks in Postgres
    if chunks:
        db.insert_chunks(paper_id, chunks)

    # Index chunks in Chroma
    try:
        if chunks:
            vector_store.add_chunks(paper_id, chunks)
    except Exception as e:
        # Still return success for DB; surface vector index failure for debugging
        return {
            "paper_id": paper_id,
            "filename": file.filename,
            "stored_path": str(dest),
            "title": title,
            "authors": authors,
            "abstract_preview": (abstract[:300] + "...") if abstract else None,
            "chunks_indexed": 0,
            "vector_index_error": str(e),
            "status": "ingested (vector index failed)",
        }

    return {
        "paper_id": paper_id,
        "filename": file.filename,
        "stored_path": str(dest),
        "title": title,
        "authors": authors,
        "abstract_preview": (abstract[:300] + "...") if abstract else None,
        "chunks_indexed": len(chunks),
        "status": "ingested",
    }
