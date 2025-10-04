# app/routers/author.py
from fastapi import APIRouter, Query, HTTPException
from app.storage import db

router = APIRouter()

# ---------------------------
# Endpoint: /author/info
# ---------------------------
@router.get("/info")
def get_author_info(name: str = Query(..., description="Author full name")):
    """
    Retrieve author profile including papers, co-authors, and metadata.
    """
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                # Fetch author record
                cur.execute("SELECT id FROM authors WHERE name = %s;", (name,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Author not found")

                author_id = row[0]

                # Fetch papers authored by this person
                cur.execute(
                    """
                    SELECT p.id, p.title, p.venue, p.year
                    FROM papers p
                    JOIN paper_authors pa ON pa.paper_id = p.id
                    WHERE pa.author_id = %s
                    ORDER BY p.year DESC NULLS LAST;
                    """,
                    (author_id,),
                )
                papers = [
                    {
                        "paper_id": r[0],
                        "title": r[1],
                        "venue": r[2],
                        "year": r[3],
                    }
                    for r in cur.fetchall()
                ]

                # Fetch coauthors
                cur.execute(
                    """
                    SELECT DISTINCT a2.name
                    FROM authors a2
                    JOIN paper_authors pa2 ON pa2.author_id = a2.id
                    WHERE pa2.paper_id IN (
                        SELECT paper_id FROM paper_authors WHERE author_id = %s
                    )
                    AND a2.id != %s;
                    """,
                    (author_id, author_id),
                )
                coauthors = [r[0] for r in cur.fetchall()]

        return {
            "author": name,
            "papers": papers,
            "coauthors": coauthors,
            "paper_count": len(papers),
            "coauthor_count": len(coauthors),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# Endpoint: /author/graph
# ---------------------------
@router.get("/graph")
def get_author_graph(limit: int = Query(20, description="Limit number of authors in graph")):
    """
    Generate a simple co-author graph as JSON (nodes + edges).
    This can later power D3.js or LangGraph visualizations.
    """
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                # Get pairs of co-authors
                cur.execute(
                    """
                    SELECT a1.name, a2.name
                    FROM paper_authors pa1
                    JOIN paper_authors pa2 ON pa1.paper_id = pa2.paper_id
                    JOIN authors a1 ON a1.id = pa1.author_id
                    JOIN authors a2 ON a2.id = pa2.author_id
                    WHERE a1.id < a2.id
                    LIMIT %s;
                    """,
                    (limit,),
                )
                pairs = cur.fetchall()

        nodes = {}
        edges = []

        for a1, a2 in pairs:
            if a1 not in nodes:
                nodes[a1] = {"id": a1}
            if a2 not in nodes:
                nodes[a2] = {"id": a2}
            edges.append({"source": a1, "target": a2})

        return {
            "nodes": list(nodes.values()),
            "edges": edges,
            "edge_count": len(edges),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
