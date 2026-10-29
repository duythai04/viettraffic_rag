from __future__ import annotations

from typing import Any


class VehicleConstrainedReranker:
    """
    Rerank candidates with vehicle-type constraints.

    Strategy:
    1. Detect vehicle type from query.
    2. Separate matching, unknown, and mismatching candidates.
    3. Rerank matching candidates with Cross-Encoder.
    4. Keep unknown candidates as fallback.
    5. Exclude mismatching vehicle-specific candidates
       when the query vehicle is known.
    """

    def __init__(
        self,
        reranker,
        vehicle_detector,
        vehicle_metadata: dict,
    ):
        self.reranker = reranker
        self.vehicle_detector = vehicle_detector
        self.vehicle_metadata = vehicle_metadata

    def _get_vehicle_type(
        self,
        candidate: dict,
    ) -> str | None:

        vehicle = candidate.get("vehicle_type")

        if vehicle is not None:
            return vehicle

        chunk_id = candidate.get("chunk_id")

        return self.vehicle_metadata.get(chunk_id)

    def _detect_query_vehicle(
        self,
        query: str,
    ) -> str | None:

        detector = self.vehicle_detector

        if hasattr(detector, "detect"):
            result = detector.detect(query)
        elif callable(detector):
            result = detector(query)
        else:
            raise TypeError(
                "Vehicle detector must expose detect() "
                "or be callable"
            )

        if isinstance(result, str):
            return result

        if isinstance(result, dict):
            return result.get("vehicle_type")

        return getattr(result, "vehicle_type", None)

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = 5,
    ) -> list[dict]:

        if top_k <= 0:
            raise ValueError("top_k must be positive")

        if not candidates:
            return []

        query_vehicle = self._detect_query_vehicle(query)

        enriched = []

        for candidate in candidates:
            item = candidate.copy()

            item["vehicle_type"] = self._get_vehicle_type(
                item
            )

            enriched.append(item)

        # If vehicle type cannot be detected,
        # use normal Cross-Encoder reranking.
        if query_vehicle is None:
            return self.reranker.rerank(
                query=query,
                candidates=enriched,
                top_k=top_k,
            )

        matching = []
        unknown = []
        mismatching = []

        for item in enriched:
            vehicle = item["vehicle_type"]

            if vehicle == query_vehicle:
                matching.append(item)

            elif vehicle is None:
                unknown.append(item)

            else:
                mismatching.append(item)

        # Rerank vehicle-matching candidates first.
        matching_ranked = self.reranker.rerank(
            query=query,
            candidates=matching,
            top_k=len(matching),
        ) if matching else []

        # Unknown metadata may represent general rules.
        unknown_ranked = self.reranker.rerank(
            query=query,
            candidates=unknown,
            top_k=len(unknown),
        ) if unknown else []

        # Prioritize matching vehicle-specific rules.
        ranked = matching_ranked + unknown_ranked

        # Only use mismatching candidates as a fallback
        # if no compatible candidates exist.
        if not ranked:
            ranked = self.reranker.rerank(
                query=query,
                candidates=mismatching,
                top_k=len(mismatching),
            )

        return ranked[:top_k]