from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from mark_core.config import get_settings

settings = get_settings()
COLLECTION = "mark_memory"

_client: QdrantClient | None = None


def get_qdrant() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=settings.qdrant_url)
    return _client


def ensure_collection() -> None:
    client = get_qdrant()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION not in collections:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=settings.embedding_dim, distance=Distance.COSINE),
        )
