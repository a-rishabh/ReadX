# app/routers/paper.py
from fastapi import APIRouter, UploadFile, File
import shutil, os
from app.storage import db
from app.utils.grobid_client import parse_pdf_with_grobid, extract_authors_from_tei, extract_abstract_from_tei, extract_affiliations_from_tei

router = APIRouter()

UPLOAD_DIR = "data/papers"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_paper(file: UploadFile = File(...)):
    stored_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(stored_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ✅ Call GROBID for metadata
    tei_xml = parse_pdf_with_grobid(stored_path, service="processHeaderDocument")
    authors = extract_authors_from_tei(tei_xml)
    affiliations = extract_affiliations_from_tei(tei_xml)
    abstract = extract_abstract_from_tei(tei_xml)

    # Insert into DB
    paper_id = db.insert_paper(
        filename=file.filename,
        title=None,  # could extract from TEI too
        abstract=abstract,
        year=None,
        venue=None,
        path=stored_path,
        tei_xml=tei_xml
    )

    # Link authors + affiliations
    for author in authors:
        author_id = db.upsert_author(author)
        db.link_paper_author(paper_id, author_id)

        if author in affiliations:
            for aff in affiliations[author]:
                aff_id = db.upsert_affiliation(aff)
                db.link_author_affiliation(author_id, aff_id)

    return {
        "paper_id": paper_id,
        "filename": file.filename,
        "stored_path": stored_path,
        "authors": authors,
        "affiliations": affiliations,
        "abstract": abstract[:300] + "..." if abstract else None,
        "status": "ingested with GROBID"
    }
