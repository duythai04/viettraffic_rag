from __future__ import annotations

from src.query.vehicle_detector import VehicleDetector
from src.retrieval.hybrid_retriever import HybridRetriever


class VehicleAwareRetriever:
    def __init__(
        self,
        hybrid_retriever: HybridRetriever,
        vehicle_metadata: dict[str, str | None],
        vehicle_boost: float = 0.005,
        mismatch_penalty: float = 0.005,
    ):
        self.hybrid_retriever = hybrid_retriever
        self.vehicle_detector = VehicleDetector()

        self.vehicle_metadata = vehicle_metadata
        self.vehicle_boost = vehicle_boost
        self.mismatch_penalty = mismatch_penalty

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int = 30,
    ) -> list[dict]:

        if top_k <= 0 or candidate_k <= 0:
            raise ValueError(
                "top_k and candidate_k must be positive"
            )

        vehicle_type = self.vehicle_detector.detect(query)

        results = self.hybrid_retriever.retrieve(
            query=query,
            top_k=max(candidate_k, top_k),
            candidate_k=max(candidate_k, top_k),
        )

        reranked = []

        for result in results:
            item = result.copy()

            chunk_id = item["chunk_id"]

            # Metadata đã được kiểm tra từ JSON cache
            chunk_vehicle = self.vehicle_metadata.get(chunk_id)

            original_score = item["rrf_score"]
            adjusted_score = original_score

            if vehicle_type is not None:
                if chunk_vehicle == vehicle_type:
                    adjusted_score += self.vehicle_boost

                elif (
                    chunk_vehicle is not None
                    and chunk_vehicle != vehicle_type
                ):
                    adjusted_score -= self.mismatch_penalty

            item["vehicle_type"] = chunk_vehicle
            item["adjusted_score"] = adjusted_score

            reranked.append(item)

        reranked.sort(
            key=lambda item: item["adjusted_score"],
            reverse=True,
        )

        return reranked[:top_k]