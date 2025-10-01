# app/routers/query.py
from fastapi import APIRouter, Query
from app.storage import db, vector_store
from app.llm import gemini
import re

router = APIRouter()

def is_metadata_question(q: str) -> str | None:
    """Detect if the query is about metadata instead of content."""
    q_lower = q.lower()
    if "author" in q_lower or "who wrote" in q_lower:
        return "authors"
    if "title" in q_lower:
        return "title"
    if "year" in q_lower or "published" in q_lower:
        return "year"
    if "venue" in q_lower or "conference" in q_lower or "journal" in q_lower:
        return "venue"
    return None

@router.get("/ask")
def ask_question(
    question: str = Query(..., description="The user question"),
    paper_id: int = Query(..., description="Paper ID to query"),
    top_k: int = Query(3, description="Top-k chunks to retrieve"),
):
    # 1. Check if metadata question
    meta_field = is_metadata_question(question)
    if meta_field:
        paper, authors = db.get_paper_with_authors(paper_id)
        if not paper:
            return {"query": question, "answer": "Paper not found", "paper_id": paper_id}

        if meta_field == "authors":
            return {"query": question, "answer": authors, "paper_id": paper_id}
        if meta_field == "title":
            return {"query": question, "answer": paper.get("title"), "paper_id": paper_id}
        if meta_field == "year":
            return {"query": question, "answer": paper.get("year"), "paper_id": paper_id}
        if meta_field == "venue":
            return {"query": question, "answer": paper.get("venue"), "paper_id": paper_id}

    # 2. Else → vector search
    results = vector_store.search_chunks(paper_id, question, top_k=top_k)
    context = "\n\n".join([r["content"] for r in results])
    prompt = f"Question: {question}\n\nContext:\n{context}\n\nAnswer concisely with citations."

    try:
        answer = gemini.ask_gemini(prompt)
    except Exception as e:
        return {"query": question, "error": str(e)}

    return {
        "query": question,
        "answer": answer,
        "citations": results,
        "paper_id": paper_id,
    }
