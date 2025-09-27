from fastapi import APIRouter, Query
from typing import Optional, Dict, Any
from app.storage import vector_store, db
from app.llm.gemini import ask_gemini
from langchain.prompts import PromptTemplate
# from langchain.chat_models import ChatOpenAI

router = APIRouter()

# Define a simple prompt template
QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are an assistant helping users understand research papers.\n\n"
        "Question: {question}\n\n"
        "Context:\n{context}\n\n"
        "Answer concisely in plain English. "
        "If possible, cite the section or authors you drew information from."
    ),
)

def synthesize_answer(question: str, retrieved: list[dict]) -> str:
    if not retrieved:
        return "I couldn't find relevant information in the ingested papers."

    # Build context from retrieved chunks
    context = "\n\n".join(
        f"[paper_id={r['metadata']['paper_id']}, section={r['metadata'].get('section')}] {r['content']}"
        for r in retrieved
    )

    prompt = f"""
    You are an assistant helping users understand research papers.

    Question: {question}

    Context:
    {context}

    Answer concisely in plain English.
    If possible, cite the section or authors you drew information from.
    """

    return ask_gemini(prompt)


@router.get("/ask")
def ask_question(
    question: str = Query(...),
    paper_id: Optional[int] = None,
    top_k: int = 3,
) -> Dict[str, Any]:
    """
    - Metadata questions (authors, title, year, venue) → DB lookup
    - Content questions → vector search + LLM synthesis
    """
    # q = question.lower()
    # if "author" in q or "who wrote" in q:
    #     pid = paper_id or db.get_latest_paper_id()
    #     paper, authors = db.get_paper_with_authors(pid)
    #     return {"query": question, "answer": authors, "paper_id": pid}

    # if "title" in q:
    #     pid = paper_id or db.get_latest_paper_id()
    #     paper, _ = db.get_paper_with_authors(pid)
    #     return {"query": question, "answer": paper.get("title"), "paper_id": pid}

    # if "venue" in q or "conference" in q:
    #     pid = paper_id or db.get_latest_paper_id()
    #     paper, _ = db.get_paper_with_authors(pid)
    #     return {"query": question, "answer": paper.get("venue"), "paper_id": pid}

    # if "year" in q or "published" in q:
    #     pid = paper_id or db.get_latest_paper_id()
    #     paper, _ = db.get_paper_with_authors(pid)
    #     return {"query": question, "answer": paper.get("year"), "paper_id": pid}

    # Default: content search
    results = vector_store.query(question, top_k=top_k)
    answer = synthesize_answer(question, results)

    return {
        "query": question,
        "answer": answer,
        "citations": [
            {
                "paper_id": r["metadata"]["paper_id"],
                "section": r["metadata"].get("section"),
                "score": r["score"],
            }
            for r in results
        ],
    }
