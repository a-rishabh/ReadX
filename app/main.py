from fastapi import FastAPI, UploadFile, File, Query
from app.routers import paper, query, author, visualize

# Create the FastAPI app
app = FastAPI(
    title="ReadX - Research Paper Assistant",
    description="Backend API for analyzing, summarizing, and visualizing research papers",
    version="0.1.0",
)

# --- Register Routers ---
# Each router will live in app/routers/
# Keeping modular separation for clean architecture
app.include_router(paper.router, prefix="/papers", tags=["Papers"])
app.include_router(query.router, prefix="/query", tags=["Queries"])
app.include_router(author.router, prefix="/author", tags=["Authors"])
app.include_router(visualize.router, prefix="/visualize", tags=["Visualization"])


# --- Root endpoint ---
@app.get("/")
def root():
    return {
        "message": "Welcome to ReadX API 👋",
        "endpoints": {
            "/papers/upload": "Upload and parse research papers",
            "/query/ask": "Ask questions about ingested papers",
            "/author/info": "Get author context (profile, past work)",
            "/visualize/concept": "Generate visual explanations",
        },
    }
