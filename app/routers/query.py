from fastapi import APIRouter, Query
from typing import List, Dict, Any
from app.storage import vector_store, db
from typing import Optional

router = APIRouter()


@router.get("/ask")
def ask_question(
    question: str = Query(...),
    paper_id: Optional[int] = None,
    top_k: int = 3,
):
    query_type = route_question(question, paper_id)

    if query_type.startswith("metadata"):
        # Default: return metadata for the latest ingested paper if paper_id not given
        pid = paper_id or db.get_latest_paper_id()
        paper, authors = db.get_paper_with_authors(pid)

        if query_type == "metadata:authors":
            return {"query": question, "answer": authors, "paper_id": pid}
        if query_type == "metadata:title":
            return {"query": question, "answer": paper.get("title"), "paper_id": pid}
        if query_type == "metadata:venue":
            return {"query": question, "answer": paper.get("venue"), "paper_id": pid}
        if query_type == "metadata:year":
            return {"query": question, "answer": paper.get("year"), "paper_id": pid}

    # Otherwise: semantic content search
    results = vector_store.query(question, top_k=top_k)
    formatted = []
    for r in results:
        pid = int(r["metadata"]["paper_id"])
        paper, authors = db.get_paper_with_authors(pid)
        formatted.append(
            {
                "paper_id": pid,
                "title": paper.get("title"),
                "authors": authors,
                "section": r["metadata"].get("section"),
                "score": r["score"],
                "content_preview": r["content"][:300] + "...",
            }
        )
    return {"query": question, "results": formatted}




def route_question(question: str, paper_id: int | None = None):
    q = question.lower()
    if "author" in q or "who wrote" in q:
        return "metadata:authors"
    if "title" in q:
        return "metadata:title"
    if "venue" in q or "conference" in q:
        return "metadata:venue"
    if "year" in q or "published" in q:
        return "metadata:year"
    return "content"
