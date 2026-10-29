from __future__ import annotations

from sentence_transformers import CrossEncoder


VEHICLE_LABELS = {
    "motorcycle": "Xe mô tô, xe gắn máy",
    "car": "Xe ô tô",
    "specialized_vehicle": "Xe máy chuyên dùng",
    "bicycle": "Xe đạp",
    "pedestrian": "Người đi bộ",
}


class CrossEncoderReranker:
    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        batch_size: int = 8,
    ):
        self.model = CrossEncoder(model_name)
        self.batch_size = batch_size

    def build_document(self, item: dict) -> str:
        text = item.get("text") or item.get("content")

        if not isinstance(text, str) or not text.strip():
            raise ValueError(
                f"Missing text for chunk: {item.get('chunk_id')}"
            )

        vehicle = item.get("vehicle_type")

        vehicle_label = VEHICLE_LABELS.get(
            vehicle,
            "Không xác định",
        )

        citation = item.get("citation", "")

        return (
            f"Loại phương tiện: {vehicle_label}\n"
            f"Căn cứ pháp lý: {citation}\n"
            f"Nội dung: {text}"
        )

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        if not candidates:
            return []

        pairs = [
            (query, self.build_document(item))
            for item in candidates
        ]

        scores = self.model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )

        reranked = []

        for item, score in zip(candidates, scores):
            result = item.copy()
            result["rerank_score"] = float(score)
            reranked.append(result)

        reranked.sort(
            key=lambda item: item["rerank_score"],
            reverse=True,
        )

        return reranked[:top_k]