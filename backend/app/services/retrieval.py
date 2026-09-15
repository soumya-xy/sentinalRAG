"""4.2 / 4.3 Similarity retrieval via ChromaDB vector search."""
from __future__ import annotations
import chromadb
from sentence_transformers import SentenceTransformer
from app.core.config import get_settings
from app.models.event import EventRecord

def retrieve_events(question: str, events: list[EventRecord], *, top_k: int = 3) -> list[EventRecord]:
    if not events:
        return []

    settings = get_settings()
    client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    collection = client.get_or_create_collection(settings.chroma_collection_name)
    embedder = SentenceTransformer(settings.embedding_model_name)

    query_vec = embedder.encode([question]).tolist()
    results = collection.query(query_embeddings=query_vec, n_results=top_k)

    retrieved_ids = results["ids"][0] if results and "ids" in results and results["ids"] else []
    
    event_map = {e.event_id: e for e in events}
    matched = [event_map[eid] for eid in retrieved_ids if eid in event_map]
    return matched or events[:top_k]
