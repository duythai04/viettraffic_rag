from __future__ import annotations

from src.embeddings.embedder import LegalEmbedder
from src.vectordb.qdrant_store import QdrantStore


class VectorRetriever:
    def __init__(
        self,
        embedder: LegalEmbedder,
        store: QdrantStore,
    ):
        self.embedder = embedder
        self.store = store

        if self.embedder.dimension != self.store.vector_size:
            raise ValueError(
                "Embedding model dimension does not match Qdrant"
            )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        if not query.strip():
            raise ValueError("Query must not be empty")

        query_vector = self.embedder.embed_query(query)

        return self.store.search(
            query_vector=query_vector,
            top_k=top_k,
        )