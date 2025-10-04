# app/routers/visualize.py
from fastapi import APIRouter, Query, HTTPException
from app.storage import db

router = APIRouter()

# ---------------------------
# Endpoint: /visualize/author_graph
# ---------------------------
@router.get("/author_graph")
def visualize_author_graph(limit: int = Query(25, description="Limit number of authors in graph")):
    """
    Generate a co-author collaboration graph as JSON.
    Can be visualized later in UI with Plotly or D3.js.
    """
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                # Pull co-author pairs
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

        # Build graph
        nodes = {}
        edges = []
        for a1, a2 in pairs:
            if a1 not in nodes:
                nodes[a1] = {"id": a1}
            if a2 not in nodes:
                nodes[a2] = {"id": a2}
            edges.append({"source": a1, "target": a2})

        return {
            "type": "coauthor_graph",
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": list(nodes.values()),
            "edges": edges,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# Endpoint: /visualize/paper_structure
# ---------------------------
@router.get("/paper_structure")
def visualize_paper_structure(paper_id: int):
    """
    Visualize the structure of a paper by its sections and chunk counts.
    Returns JSON that can be rendered as a bar or pie chart later.
    """
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT section, COUNT(*) AS chunks
                    FROM paper_chunks
                    WHERE paper_id = %s
                    GROUP BY section;
                    """,
                    (paper_id,),
                )
                data = cur.fetchall()

        if not data:
            raise HTTPException(status_code=404, detail="Paper not found or not chunked yet")

        sections = [{"section": d[0], "chunks": d[1]} for d in data]

        return {
            "type": "paper_structure",
            "paper_id": paper_id,
            "sections": sections,
            "section_count": len(sections),
            "total_chunks": sum(s["chunks"] for s in sections),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
