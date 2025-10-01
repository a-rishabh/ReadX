# app/routers/author.py
from fastapi import APIRouter, Query, HTTPException
from app.storage import db

router = APIRouter()

@router.get("/info")
def author_info(
    name: str = Query(..., description="Author name to look up")
):
    try:
        # 1. Find papers for this author
        sql = """
        SELECT p.id, p.title, p.year, p.venue
        FROM papers p
        JOIN paper_authors pa ON pa.paper_id = p.id
        JOIN authors a ON a.id = pa.author_id
        WHERE a.name ILIKE %s
        ORDER BY p.year DESC NULLS LAST;
        """
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (name,))
                papers = [
                    {"id": r[0], "title": r[1], "year": r[2], "venue": r[3]}
                    for r in cur.fetchall()
                ]

        if not papers:
            return {"author": name, "papers": [], "note": "No papers found in DB"}

        return {
            "author": name,
            "papers": papers,
            # TODO: later expand with Semantic Scholar/ArXiv profile
            "external": None,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
