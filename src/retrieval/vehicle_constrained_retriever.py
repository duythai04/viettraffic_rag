from __future__ import annotations


class VehicleConstrainedRetriever:

    def __init__(
        self,
        base_retriever,
        constrained_reranker,
        candidate_k: int = 20,
    ):
        self.base_retriever = base_retriever
        self.constrained_reranker = constrained_reranker
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

        return self.constrained_reranker.rerank(
            query=query,
            candidates=candidates,
            top_k=top_k,
        )