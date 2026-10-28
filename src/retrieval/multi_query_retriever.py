from __future__ import annotations

from src.query.normalizer import TrafficQueryNormalizer
from src.retrieval.vector_retriever import VectorRetriever


class MultiQueryRetriever:
    def __init__(
        self,
        vector_retriever: VectorRetriever,
        rrf_k: int = 60,
    ):
        self.vector_retriever = vector_retriever
        self.normalizer = TrafficQueryNormalizer()
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int = 20,
    ) -> list[dict]:
        if top_k <= 0 or candidate_k <= 0:
            raise ValueError("top_k and candidate_k must be positive")

        queries = self.normalizer.expand(query)

        fused = {}

        for expanded_query in queries:
            results = self.vector_retriever.retrieve(
                query=expanded_query,
                top_k=max(candidate_k, top_k),
            )

            for rank, result in enumerate(results, start=1):
                chunk_id = result["chunk_id"]

                if not chunk_id:
                    continue

                if chunk_id not in fused:
                    fused[chunk_id] = {
                        **result,
                        "rrf_score": 0.0,
                        "matched_queries": [],
                    }

                fused[chunk_id]["rrf_score"] += (
                    1.0 / (self.rrf_k + rank)
                )

                fused[chunk_id]["matched_queries"].append(
                    expanded_query
                )

        ranked = sorted(
            fused.values(),
            key=lambda item: item["rrf_score"],
            reverse=True,
        )

        return ranked[:top_k]