from __future__ import annotations

import uuid

import numpy as np
from qdrant_client import QdrantClient, models


class QdrantStore:
    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection_name: str = "viettraffic_legal",
        vector_size: int = 1024,
    ):
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self.vector_size = vector_size

    def create_collection(self):
        """Create collection if it does not exist."""

        if self.client.collection_exists(self.collection_name):
            info = self.client.get_collection(self.collection_name)
            params = info.config.params.vectors

            if not isinstance(params, models.VectorParams):
                raise ValueError(
                    "Existing collection does not use a single dense vector"
                )

            if params.size != self.vector_size:
                raise ValueError(
                    f"Vector size mismatch: "
                    f"collection={params.size}, expected={self.vector_size}"
                )

            if params.distance != models.Distance.COSINE:
                raise ValueError("Collection distance must be COSINE")

            print(f"Collection '{self.collection_name}' already exists")
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance.COSINE,
            ),
        )

        print(f"Created collection: {self.collection_name}")

    @staticmethod
    def _point_id(chunk_id: str) -> str:
        """Generate a stable UUID from a chunk ID."""

        return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))

    def upsert(
        self,
        vectors: np.ndarray,
        metadata: list[dict],
        batch_size: int = 64,
    ) -> None:
        """Upload vectors and legal metadata to Qdrant."""

        vectors = np.asarray(vectors, dtype=np.float32)

        if vectors.ndim != 2:
            raise ValueError("Vectors must be a 2D array")

        if vectors.shape[1] != self.vector_size:
            raise ValueError("Invalid vector dimension")

        if len(vectors) != len(metadata):
            raise ValueError("Vector/metadata count mismatch")

        if not np.isfinite(vectors).all():
            raise ValueError("Vectors contain NaN or Infinity")

        if batch_size <= 0:
            raise ValueError("batch_size must be positive")

        chunk_ids = [item["chunk_id"] for item in metadata]

        if len(set(chunk_ids)) != len(chunk_ids):
            raise ValueError("Duplicate chunk IDs")

        for start in range(0, len(metadata), batch_size):
            end = start + batch_size

            points = []

            for vector, item in zip(
                vectors[start:end],
                metadata[start:end],
            ):
                points.append(
                    models.PointStruct(
                        id=self._point_id(item["chunk_id"]),
                        vector=vector.tolist(),
                        payload=item,
                    )
                )

            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True,
            )

            print(
                f"Uploaded {min(end, len(metadata))}/{len(metadata)}"
            )

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
    ) -> list[dict]:
        """Search for semantically similar legal chunks."""

        query_vector = np.asarray(
            query_vector,
            dtype=np.float32,
        )

        if query_vector.shape != (self.vector_size,):
            raise ValueError("Invalid query vector dimension")

        if not np.isfinite(query_vector).all():
            raise ValueError("Invalid query vector values")

        if top_k <= 0:
            raise ValueError("top_k must be positive")

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector.tolist(),
            limit=top_k,
            with_payload=True,
        )

        return [
            {
                "score": point.score,
                "chunk_id": (point.payload or {}).get("chunk_id"),
                "citation": (point.payload or {}).get("citation"),
                "content": (point.payload or {}).get("content"),
                "metadata": point.payload or {},
            }
            for point in response.points
        ]