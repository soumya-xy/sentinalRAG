"""3.0 Index events — ChromaDB vector database."""
from __future__ import annotations
import chromadb
from sentence_transformers import SentenceTransformer
from app.core.config import get_settings
from app.models.event import EventRecord

class EventIndexer:
    def __init__(self):
        settings = get_settings()
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        self.collection = self.client.get_or_create_collection(settings.chroma_collection_name)
        self.embedder = SentenceTransformer(settings.embedding_model_name)

    def upsert(self, events: list[EventRecord]) -> int:
        if not events:
            return 0
        
        docs = [e.caption for e in events]
        embeddings = self.embedder.encode(docs).tolist()
        ids = [e.event_id for e in events]
        metadatas = [
            {
                "video_id": e.video_id,
                "camera_id": e.camera_id,
                "start_timestamp": e.start_timestamp,
                "end_timestamp": e.end_timestamp,
                "confidence_score": e.confidence_score,
            }
            for e in events
        ]
        
        self.collection.upsert(ids=ids, embeddings=embeddings, documents=docs, metadatas=metadatas)
        return len(events)
