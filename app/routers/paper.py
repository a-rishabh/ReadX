from fastapi import APIRouter, UploadFile, File
import os
from pathlib import Path

router = APIRouter()

# Temporary storage for uploaded PDFs
UPLOAD_DIR = Path("data/papers")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_paper(file: UploadFile = File(...)):
    """
    Upload a research paper (PDF).
    For now: just save to /data/papers.
    Later: parse text, extract metadata, embed, store in eDB.
    """
    file_path = UPLOAD_DIR / file.filename
    
    # Save file to disk
    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {
        "filename": file.filename,
        "path": str(file_path),
        "status": "saved",
    }
