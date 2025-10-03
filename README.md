# ReadX

**ReadX** is an AI assistant that helps researchers **read, analyze, and understand research papers**.
Unlike generic “chat with PDF” tools, ReadX adds:

* **Structured metadata via GROBID** → reliable title, author, and section extraction.
* **Author context** → retrieve author profiles, affiliations, and past work.
* **Visual explanations** → break down methods/results into diagrams and charts.
* **Cross-paper analysis** → compare multiple papers side by side.
* **Persistent knowledge base** → build your own library of papers you can query anytime.

---

## Features (MVP → Future)

* ✅ Upload & parse PDFs (fallback: PyMuPDF, preferred: GROBID)
* ✅ Extract metadata (title, authors, abstract, venue, year)
* ✅ Store structured content in **Postgres** (papers, authors, chunks)
* ✅ Embed chunks into **VectorDB** for retrieval
* 🚧 LLM integration (Gemini via LangChain/LangGraph) for Q&A and synthesis
* 🚧 Visualization endpoints (e.g., plots from results section)
* 🚧 ArXiv API ingestion (auto fetch papers)
* 🚧 Multi-agent workflows (summarizer, author analyzer, visualizer)
* 🚧 Slack/Discord bot integration

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for system diagrams.
Key components:

1. **Ingestion**

   * GROBID XML parsing (structured sections, references)
   * PyMuPDF heuristics (fallback when GROBID is unavailable)
2. **Storage**

   * Metadata & relationships → Postgres (`papers`, `authors`, `chunks`)
   * Embeddings → ChromaDB / Weaviate
3. **Orchestration**

   * LangGraph workflows for question answering, author analysis, visualization
   * Gemini as the preferred LLM backend
4. **API/UI**

   * FastAPI endpoints (`/papers`, `/query`, `/author`, `/visualize`)
   * Streamlit chat + visualization frontend

---

## Database Schema

```
┌─────────────────────┐       ┌──────────────────────┐
│       papers        │       │       authors        │
├─────────────────────┤       ├──────────────────────┤
│ id (PK)             │       │ id (PK)              │
│ filename            │       │ name (UNIQUE)        │
│ title               │       └──────────────────────┘
│ abstract            │               ▲
│ year                │               │
│ venue               │               │
│ path                │               │
│ created_at          │               │
└─────────┬───────────┘               │
          │                           │
          ▼                           │
┌───────────────────────┐   ┌────────────────────────┐
│    paper_authors      │   │     paper_chunks       │
├───────────────────────┤   ├────────────────────────┤
│ paper_id (FK→papers)  │   │ id (PK)                │
│ author_id (FK→authors)│   │ paper_id (FK→papers)   │
└───────────────────────┘   │ section                │
                            │ chunk_index            │
                            │ content                │
                            └────────────────────────┘
```

* **papers** → stores global metadata.
* **authors** → unique author names (linked across papers).
* **paper_authors** → many-to-many relation between papers & authors.
* **paper_chunks** → sectioned + chunked content for embedding.

---

## Tech Stack

* **LLM Orchestration** → LangChain, LangGraph
* **LLM Provider** → Gemini (2.5 Flash / Pro, configurable)
* **Backend** → FastAPI
* **Vector Store** → ChromaDB / Weaviate
* **Database** → Postgres (persistent metadata & author graph)
* **UI** → Streamlit + Plotly (charts & visualizations)
* **Infra** → Docker, GitHub Actions, Kubernetes (future)

---

## Setup

```bash
# clone repo
git clone https://github.com/<your-username>/ReadX.git
cd ReadX

# setup virtual environment
python3 -m venv .venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt

# (optional) start GROBID (Docker)
docker run -it -p 8070:8070 lfoppiano/grobid:0.7.2

# start postgres (if local)
brew services start postgresql@15

# run backend
uvicorn app.main:app --reload

# run UI
streamlit run ui/streamlit_app.py
```

---

## Next Steps

* Add TEI body chunking (structured section-level chunks from GROBID)
* Improve author disambiguation (affiliations, emails)
* Add LLM-powered synthesis (`Gemini`) into `/query/ask`
* Expand visualization layer (method diagrams, results plots)

---
