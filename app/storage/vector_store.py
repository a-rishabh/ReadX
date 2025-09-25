# app/storage/vector_store.py
from __future__ import annotations
import os
from typing import Iterable
import chromadb
from chromadb.config import Settings

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

_PERSIST_DIR = os.getenv("CHROMA_DIR", "data/embeddings/readx")
_COLLECTION = os.getenv("CHROMA_COLLECTION", "paper_chunks")

_client = chromadb.Client(Settings(is_persistent=True, persist_directory=_PERSIST_DIR))
_collection = _client.get_or_create_collection(_COLLECTION)

# Lazy-load small, fast model
_model = None
def _embed(texts: list[str]) -> list[list[float]]:
    global _model
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers not installed. Add it to requirements.txt.")
    if _model is None:
        _model = SentenceTransformer(os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2"))
    return _model.encode(texts, normalize_embeddings=True).tolist()

def add_chunks(paper_id: int, chunks: Iterable[tuple[str, str]]):
    """
    chunks: iterable of (section, content)
    """
    ids, texts, metas = [], [], []
    for idx, (section, content) in enumerate(chunks):
        ids.append(f"{paper_id}-{idx}")
        texts.append(content)
        metas.append({"paper_id": str(paper_id), "section": section})

    embeddings = _embed(texts)
    _collection.add(ids=ids, documents=texts, metadatas=metas, embeddings=embeddings)

def query(question: str, top_k: int = 3) -> list[dict]:
    """Return top_k matches with metadata + content"""
    q_embed = _embed([question])[0]
    results = _collection.query(
        query_embeddings=[q_embed],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append(
            {
                "content": doc,
                "metadata": meta,
                "score": float(1 - dist),  # higher = more relevant
            }
        )
    return output
