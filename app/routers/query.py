from fastapi import APIRouter, Query
from typing import List, Dict, Any
from app.storage import vector_store, db

router = APIRouter()


@router.get("/ask")
def ask_question(
    question: str = Query(..., description="Your query about the ingested papers"),
    top_k: int = Query(3, description="Number of top chunks to retrieve"),
) -> Dict[str, Any]:
    """
    Query the knowledge base:
    - Embed the user question
    - Retrieve top_k chunks from Chroma
    - Fetch metadata from Postgres
    - Return structured results
    """
    try:
        results = vector_store.query(question, top_k=top_k)
    except Exception as e:
        return {"error": f"Vector search failed: {e}"}

    formatted = []
    for r in results:
        paper_id = int(r["metadata"]["paper_id"])
        section = r["metadata"].get("section")

        # fetch paper + authors from DB
        paper, authors = db.get_paper_with_authors(paper_id)

        formatted.append(
            {
                "paper_id": paper_id,
                "title": paper.get("title"),
                "authors": authors,
                "section": section,
                "score": r["score"],
                "content_preview": r["content"][:300] + "..." if r["content"] else None,
            }
        )

    return {"query": question, "results": formatted}
