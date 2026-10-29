from __future__ import annotations


class RerankedRetriever:
    def __init__(
        self,
        base_retriever,
        reranker,
        candidate_k: int = 20,
    ):
        self.base_retriever = base_retriever
        self.reranker = reranker
        self.candidate_k = candidate_k

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:

        candidates = self.base_retriever.retrieve(
            query=query,
            top_k=self.candidate_k,
            candidate_k=self.candidate_k,
        )

        if not candidates:
            return []

        return self.reranker.rerank(
            query=query,
            candidates=candidates,
            top_k=top_k,
        )