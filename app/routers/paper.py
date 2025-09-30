# app/routers/paper.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil

from app.storage import db, vector_store
from app.utils import pdf_parser, grobid_client

router = APIRouter()

DATA_DIR = Path("data/papers")
DATA_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
def upload_paper(file: UploadFile = File(...)):
    try:
        # --- Save uploaded file ---
        paper_path = DATA_DIR / file.filename
        with open(paper_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # --- Try GROBID first ---
        try:
            parsed = grobid_client.parse_with_grobid(str(paper_path))
            title = None  # TEI header parsing can be added later
            authors = parsed["authors"]
            sections = parsed["sections"]
            abstract = parsed.get("abstract")
        except Exception:
            # Fallback → PyMuPDF parser
            parsed = pdf_parser.parse_pdf(paper_path)
            title = parsed["title"]
            authors = parsed["authors"]
            sections = parsed["sections"]
            abstract = parsed["abstract"]

        # --- Insert into DB ---
        paper_id = db.insert_paper(
            filename=file.filename,
            title=title,
            abstract=abstract,
            year=None,
            venue=None,
            path=str(paper_path),
        )

        # --- Insert authors ---
        for author in authors:
            author_id = db.upsert_author(author)
            db.link_paper_author(paper_id, author_id)

        # --- Chunk sections ---
        chunk_pairs: list[tuple[str, str]] = []
        for sec, txt in sections.items():
            chunks = pdf_parser.chunk_text(sec, txt)
            for c in chunks:
                chunk_pairs.append((sec, c))
        db.insert_chunks(paper_id, chunk_pairs)

        # --- Vector index ---
        try:
            vector_store.index_chunks(paper_id, chunk_pairs)
            status = "ingested"
        except Exception as e:
            status = f"ingested (vector index failed: {e})"

        return {
            "paper_id": paper_id,
            "filename": file.filename,
            "stored_path": str(paper_path),
            "title": title,
            "authors": authors,
            "abstract_preview": (abstract[:400] + "...") if abstract else None,
            "chunks_indexed": len(chunk_pairs),
            "status": status,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
