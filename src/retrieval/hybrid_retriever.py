from __future__ import annotations

from src.lexical.bm25_index import BM25Index
from src.query.normalizer import TrafficQueryNormalizer
from src.retrieval.vector_retriever import VectorRetriever


class HybridRetriever:
    def __init__(
        self,
        vector_retriever: VectorRetriever,
        bm25_index: BM25Index,
        rrf_k: int = 60,
    ):
        if rrf_k <= 0:
            raise ValueError("rrf_k must be positive")

        self.vector_retriever = vector_retriever
        self.bm25_index = bm25_index
        self.normalizer = TrafficQueryNormalizer()
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int = 30,
    ) -> list[dict]:
        if top_k <= 0 or candidate_k <= 0:
            raise ValueError("top_k and candidate_k must be positive")

        queries = self.normalizer.expand(query)

        fused = {}

        for expanded_query in queries:
            dense_results = self.vector_retriever.retrieve(
                query=expanded_query,
                top_k=max(candidate_k, top_k),
            )

            lexical_results = self.bm25_index.search(
                query=expanded_query,
                top_k=max(candidate_k, top_k),
            )

            for source, results in [
                ("dense", dense_results),
                ("bm25", lexical_results),
            ]:
                for rank, result in enumerate(results, start=1):
                    chunk_id = result["chunk_id"]

                    if not chunk_id:
                        continue

                    if chunk_id not in fused:
                        fused[chunk_id] = {
                            **result,
                            "rrf_score": 0.0,
                            "matched_sources": [],
                        }

                    fused[chunk_id]["rrf_score"] += (
                        1.0 / (self.rrf_k + rank)
                    )

                    fused[chunk_id]["matched_sources"].append(
                        {
                            "source": source,
                            "query": expanded_query,
                            "rank": rank,
                        }
                    )

        ranked = sorted(
            fused.values(),
            key=lambda item: item["rrf_score"],
            reverse=True,
        )

        return ranked[:top_k]