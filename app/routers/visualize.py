# app/routers/visualize.py
from fastapi import APIRouter, Query, HTTPException
from collections import Counter
import re
from app.storage import db

router = APIRouter()

@router.get("/concept")
def visualize_section(
    paper_id: int = Query(..., description="Paper ID to visualize"),
    section: str = Query("abstract", description="Section name to visualize")
):
    """
    Very basic visualization: return top keywords from a section of a paper.
    Later we can plug into Plotly to render diagrams/charts.
    """
    try:
        # Fetch chunks for the section
        sql = """
        SELECT content
        FROM paper_chunks
        WHERE paper_id = %s AND section ILIKE %s;
        """
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (paper_id, section))
                texts = [r[0] for r in cur.fetchall()]

        if not texts:
            return {"paper_id": paper_id, "section": section, "keywords": []}

        text = " ".join(texts)
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())  # only words ≥4 chars
        freq = Counter(words).most_common(15)

        return {
            "paper_id": paper_id,
            "section": section,
            "keywords": [{"word": w, "count": c} for w, c in freq],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
