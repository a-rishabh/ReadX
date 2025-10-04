# app/routers/query.py
from fastapi import APIRouter, Query, HTTPException
from app.storage import vector_store, db
from app.llm import gemini
from typing import List, Dict, Any

router = APIRouter()

# ---------------------------
# Helper: Synthesize Answer
# ---------------------------
def synthesize_answer(question: str, contexts: List[Dict[str, Any]]) -> str:
    """
    Given a question and retrieved chunks, synthesize a concise answer.
    """
    if not contexts:
        return "No relevant context found in the database."

    # Build structured context string
    context_text = "\n\n".join(
        [f"[{c['paper_id']} - {c['section']}] {c['content']}" for c in contexts]
    )

    prompt = f"""
You are ReadX — a research assistant AI.
Use the context below to answer the question accurately and concisely.

Question:
{question}

Context:
{context_text}

If the context does not contain the answer, say so clearly.
Only use factual info from the provided text — do not hallucinate.
    """

    try:
        return gemini.ask_gemini(prompt)
    except Exception as e:
        return f"LLM synthesis failed: {str(e)}"

# ---------------------------
# Endpoint: /query/ask
# ---------------------------
@router.get("/ask")
def ask_question(
    question: str = Query(..., description="User question about a paper"),
    paper_id: int | None = Query(None, description="Paper ID to restrict search"),
    top_k: int = Query(5, description="Number of relevant chunks to retrieve"),
):
    """
    Retrieve relevant chunks via vector search and synthesize an answer.
    """
    try:
        results = vector_store.query(question, top_k=top_k, paper_id=paper_id)

        if not results:
            raise HTTPException(status_code=404, detail="No matching content found.")

        # Build clean response structure
        citations = [
            {
                "paper_id": r["paper_id"],
                "section": r["section"],
                "score": r["score"],
            }
            for r in results
        ]

        # Synthesize final answer from LLM
        answer = synthesize_answer(question, results)

        response = {
            "query": question,
            "answer": answer,
            "citations": citations,
        }
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------
# Endpoint: /query/context
# ---------------------------
@router.get("/context")
def get_context(
    paper_id: int = Query(...),
    limit: int = Query(5),
):
    """
    Return a few chunks of context for debugging or front-end previews.
    """
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT section, content
                    FROM paper_chunks
                    WHERE paper_id = %s
                    LIMIT %s;
                    """,
                    (paper_id, limit),
                )
                rows = cur.fetchall()
        return [{"section": r[0], "content": r[1]} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
