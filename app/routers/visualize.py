# app/routers/visualize.py
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from io import BytesIO
import base64
import plotly.graph_objects as go
from app.storage import db

router = APIRouter()


# ---------------------------
# Endpoint: /visualize/author_graph
# ---------------------------
@router.get("/author_graph")
def visualize_author_graph(
    limit: int = Query(25, description="Limit number of co-author pairs"),
    format: str = Query("json", description="Output format: json or plotly"),
):
    """
    Generate a co-author collaboration graph.
    - format=json → returns node/edge JSON (default)
    - format=plotly → returns a base64 PNG of the network
    """
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
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

        if not pairs:
            raise HTTPException(status_code=404, detail="No co-author data found")

        # Build nodes and edges
        nodes = {}
        edges = []
        for a1, a2 in pairs:
            if a1 not in nodes:
                nodes[a1] = {"id": a1}
            if a2 not in nodes:
                nodes[a2] = {"id": a2}
            edges.append((a1, a2))

        # --- JSON output ---
        if format == "json":
            return JSONResponse(
                {
                    "type": "coauthor_graph",
                    "node_count": len(nodes),
                    "edge_count": len(edges),
                    "nodes": list(nodes.values()),
                    "edges": [{"source": a1, "target": a2} for a1, a2 in edges],
                }
            )

        # --- Plotly output ---
        elif format == "plotly":
            # assign coordinates for basic circular layout
            import math
            N = len(nodes)
            node_names = list(nodes.keys())
            positions = {
                name: (
                    math.cos(2 * math.pi * i / N),
                    math.sin(2 * math.pi * i / N)
                )
                for i, name in enumerate(node_names)
            }

            # edges
            edge_x, edge_y = [], []
            for a1, a2 in edges:
                x0, y0 = positions[a1]
                x1, y1 = positions[a2]
                edge_x += [x0, x1, None]
                edge_y += [y0, y1, None]

            # nodes
            node_x = [positions[n][0] for n in node_names]
            node_y = [positions[n][1] for n in node_names]

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=1, color='rgba(100,100,100,0.5)'),
                    hoverinfo='none',
                    mode='lines'
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers+text',
                    text=node_names,
                    textposition='top center',
                    marker=dict(size=12, color='lightblue', line_width=1),
                )
            )

            fig.update_layout(
                showlegend=False,
                title="Co-Author Collaboration Graph",
                margin=dict(l=0, r=0, t=40, b=0),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
            )

            img_bytes = fig.to_image(format="png")
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            return {"image_base64": img_b64, "node_count": len(nodes)}

        else:
            raise HTTPException(status_code=400, detail="format must be 'json' or 'plotly'")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ---------------------------
# Endpoint: /visualize/paper_structure
# ---------------------------
@router.get("/paper_structure")
def visualize_paper_structure(
    paper_id: int,
    format: str = Query("json", description="Output format: json or plotly"),
):
    """
    Visualize structure of a paper (sections + chunk counts).
    - format=json → structured data
    - format=plotly → returns base64 PNG bar chart
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
            raise HTTPException(status_code=404, detail="Paper not found or not chunked")

        sections = [{"section": d[0], "chunks": d[1]} for d in data]

        if format == "json":
            return {
                "type": "paper_structure",
                "paper_id": paper_id,
                "sections": sections,
                "section_count": len(sections),
                "total_chunks": sum(s["chunks"] for s in sections),
            }

        elif format == "plotly":
            fig = go.Figure(
                go.Bar(
                    x=[s["section"] for s in sections],
                    y=[s["chunks"] for s in sections],
                    marker=dict(color="lightcoral"),
                )
            )
            fig.update_layout(
                title=f"Paper {paper_id} Section Breakdown",
                xaxis_title="Section",
                yaxis_title="Chunk Count",
                template="plotly_white",
            )

            img_bytes = fig.to_image(format="png")
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            return {"image_base64": img_b64, "section_count": len(sections)}

        else:
            raise HTTPException(status_code=400, detail="format must be 'json' or 'plotly'")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
