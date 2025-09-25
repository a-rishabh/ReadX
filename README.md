# ReadX
**ReadX** is an AI assistant that helps researchers **read, analyze, and understand research papers**.  
Unlike generic “chat with PDF” tools, ReadX adds:
- **Author context** → retrieve author profiles, past work, and influence.  
- **Visual explanations** → break down methods/results into diagrams and charts.  
- **Cross-paper analysis** → compare multiple papers side by side.  
- **Persistent knowledge base** → build your own library of papers you can query anytime.  

---

## Features (MVP → Future)
- [ ] Upload & parse PDFs (PyMuPDF / Grobid)  
- [ ] Chunk by sections (abstract, methods, results)  
- [ ] Store embeddings in Chroma/Weaviate  
- [ ] LangGraph workflows (summarizer, author analysis, visualizer)  
- [ ] FastAPI backend (`/summarize`, `/analyze_author`, `/visualize`)  
- [ ] Streamlit UI (chat + visualizations)  
- [ ] ArXiv API ingestion (auto fetch papers)  
- [ ] Slack/Discord bot integration  

---

## Architecture
See [docs/architecture.md](docs/architecture.md) for system diagrams.  
Key components:
1. **Ingestion** → parse PDF, extract metadata & references.  
2. **Storage** → embeddings (VectorDB), metadata (Postgres).  
3. **Orchestration** → LangGraph workflows for different modes.  
4. **API/UI** → FastAPI endpoints + Streamlit frontend.  

---

## Tech Stack
- **LLM Orchestration** → LangChain, LangGraph  
- **Backend** → FastAPI  
- **Vector Store** → ChromaDB / Weaviate  
- **Database** → Postgres (metadata)  
- **UI** → Streamlit + Plotly for visualizations  
- **Infra** → Docker, GitHub Actions, Kubernetes (future)  

---

## Setup
```bash
# clone repo
git clone https://github.com/<your-username>/ReadX.git
cd ReadX

# install dependencies
pip install -r requirements.txt

# run backend
uvicorn app.main:app --reload

# run UI
streamlit run ui/streamlit_app.py
