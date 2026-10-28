from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from src.schemas.chunk import LegalChunk


class LegalEmbedder:
    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str | None = None,
        batch_size: int = 16,
    ):
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")

        self.model_name = model_name
        self.batch_size = batch_size

        self.model = SentenceTransformer(
            model_name,
            device=device,
        )

        self.dimension = self.model.get_embedding_dimension()

        if self.dimension is None:
            raise ValueError(
                "Cannot determine embedding dimension"
            )

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """
        Generate normalized embeddings for a batch of texts.
        """

        if not texts:
            return np.empty(
                (0, self.dimension),
                dtype=np.float32,
            )

        if any(
            not isinstance(text, str) or not text.strip()
            for text in texts
        ):
            raise ValueError("All texts must be non-empty strings")

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

        embeddings = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        if embeddings.shape != (len(texts), self.dimension):
            raise ValueError(
                f"Invalid embedding shape: {embeddings.shape}"
            )

        if not np.isfinite(embeddings).all():
            raise ValueError(
                "Embeddings contain NaN or Infinity"
            )

        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a user query.
        """

        return self.embed_texts([query])[0]

    def embed_chunks(
        self,
        chunks: list[LegalChunk],
    ) -> list[dict]:
        """
        Generate embeddings while preserving chunk metadata.
        """

        if not chunks:
            return []

        texts = [
            chunk.embedding_text
            for chunk in chunks
        ]

        embeddings = self.embed_texts(texts)

        results = []

        for chunk, vector in zip(chunks, embeddings):
            results.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "vector": vector.tolist(),
                    "metadata": chunk.to_dict(),
                }
            )

        return results