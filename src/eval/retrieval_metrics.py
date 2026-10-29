from __future__ import annotations

from typing import Sequence


class RetrievalMetrics:
    """
    Metrics for evaluating retrieval quality.

    Supported metrics:
        - Hit@K
        - Recall@K
        - MRR@K
        - Precision@K
    """

    @staticmethod
    def hit_at_k(
        retrieved_ids: Sequence[str],
        relevant_ids: Sequence[str],
        k: int = 1,
    ) -> float:
        """
        Return 1 if at least one relevant document
        appears in the top K results.
        """
        if k <= 0:
            raise ValueError("k must be positive")

        relevant = set(relevant_ids)

        if not relevant:
            return 0.0

        top_k = retrieved_ids[:k]

        return float(
            any(chunk_id in relevant for chunk_id in top_k)
        )

    @staticmethod
    def recall_at_k(
        retrieved_ids: Sequence[str],
        relevant_ids: Sequence[str],
        k: int = 5,
    ) -> float:
        """
        Fraction of relevant documents retrieved
        within the top K results.
        """
        if k <= 0:
            raise ValueError("k must be positive")

        relevant = set(relevant_ids)

        if not relevant:
            return 0.0

        retrieved = set(retrieved_ids[:k])

        return len(retrieved & relevant) / len(relevant)

    @staticmethod
    def precision_at_k(
        retrieved_ids: Sequence[str],
        relevant_ids: Sequence[str],
        k: int = 5,
    ) -> float:
        """
        Fraction of top K positions containing
        relevant documents.
        """
        if k <= 0:
            raise ValueError("k must be positive")

        relevant = set(relevant_ids)

        if not relevant:
            return 0.0

        top_k = retrieved_ids[:k]

        return sum(
            chunk_id in relevant
            for chunk_id in top_k
        ) / k

    @staticmethod
    def mrr_at_k(
        retrieved_ids: Sequence[str],
        relevant_ids: Sequence[str],
        k: int = 10,
    ) -> float:
        """
        Reciprocal rank of the first relevant
        document within the top K results.
        """
        if k <= 0:
            raise ValueError("k must be positive")

        relevant = set(relevant_ids)

        if not relevant:
            return 0.0

        for rank, chunk_id in enumerate(
            retrieved_ids[:k],
            start=1,
        ):
            if chunk_id in relevant:
                return 1.0 / rank

        return 0.0

    @classmethod
    def evaluate(
        cls,
        retrieved_ids: Sequence[str],
        relevant_ids: Sequence[str],
    ) -> dict[str, float]:
        """
        Evaluate a single retrieval query.
        """
        return {
            "hit@1": cls.hit_at_k(
                retrieved_ids, relevant_ids, k=1
            ),
            "hit@5": cls.hit_at_k(
                retrieved_ids, relevant_ids, k=5
            ),
            "recall@5": cls.recall_at_k(
                retrieved_ids, relevant_ids, k=5
            ),
            "precision@5": cls.precision_at_k(
                retrieved_ids, relevant_ids, k=5
            ),
            "mrr@10": cls.mrr_at_k(
                retrieved_ids, relevant_ids, k=10
            ),
        }