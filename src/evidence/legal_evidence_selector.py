from __future__ import annotations

import re
import unicodedata
from typing import Any

from src.retrieval.vehicle_detector import VehicleDetector


class LegalEvidenceSelector:
    def __init__(
        self,
        max_evidence: int = 3,
        min_score: float = 0.0,
    ):
        if max_evidence < 1:
            raise ValueError("max_evidence must be positive")

        self.max_evidence = max_evidence
        self.min_score = min_score
        self.vehicle_detector = VehicleDetector()

    @staticmethod
    def _normalize(text: str) -> str:
        text = unicodedata.normalize("NFC", text.lower())
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _detect_role(self, question: str) -> str | None:
        text = self._normalize(question)

        passenger_patterns = [
            r"người được chở",
            r"người ngồi sau",
            r"người ngồi trên xe",
            r"hành khách",
        ]

        driver_patterns = [
            r"người điều khiển",
            r"người lái",
            r"tài xế",
            r"lái xe",
        ]

        for pattern in passenger_patterns:
            if re.search(pattern, text):
                return "passenger"

        for pattern in driver_patterns:
            if re.search(pattern, text):
                return "driver"

        return None

    def _detect_evidence_role(
        self,
        context: dict,
    ) -> str | None:
        text = self._normalize(
            " ".join([
                str(context.get("violation") or ""),
                str(context.get("clause_preamble") or ""),
            ])
        )

        if (
            "đối với người được chở" in text
            or "người được chở trên" in text
        ):
            return "passenger"

        if (
            "chở người ngồi trên xe" in text
            or "chở người không đội" in text
        ):
            return "driver_responsible_for_passenger"

        if (
            "khi điều khiển xe" in text
            or "người điều khiển xe" in text
        ):
            return "driver"

        return None

    def _vehicle_score(
        self,
        query_vehicle: str | None,
        context_vehicle: str | None,
    ) -> float:
        if query_vehicle is None:
            return 0.0

        if query_vehicle == context_vehicle:
            return 0.03

        if context_vehicle is None:
            return 0.0

        return -0.03

    def _role_score(
        self,
        query_role: str | None,
        context_role: str | None,
    ) -> float:
        if query_role is None:
            return 0.0

        if query_role == context_role:
            return 0.02

        if context_role is None:
            return 0.0

        return -0.02

    def _keyword_score(
        self,
        question: str,
        context: dict,
    ) -> float:
        question_text = self._normalize(question)

        violation_text = self._normalize(
            str(context.get("violation") or "")
        )

        if not violation_text:
            return 0.0

        keywords = [
            "mũ bảo hiểm",
            "đèn đỏ",
            "đèn tín hiệu",
            "nồng độ cồn",
            "vượt tốc độ",
            "không có giấy phép",
            "đi ngược chiều",
            "không có bảo hiểm",
        ]

        score = 0.0

        for keyword in keywords:
            if keyword in question_text and keyword in violation_text:
                score += 0.01

        if (
            "đèn đỏ" in question_text
            and "đèn tín hiệu giao thông" in violation_text
        ):
            score += 0.02

        return score

    def select(
        self,
        question: str,
        contexts: list[dict],
    ) -> dict[str, Any]:
        if not contexts:
            return {
                "question": question,
                "selected_evidence": [],
                "requires_clarification": True,
            }

        query_vehicle = self.vehicle_detector.detect(question)
        query_role = self._detect_role(question)

        candidates = []

        for context in contexts:
            retrieval_score = float(
                context.get("retrieval_score") or 0.0
            )

            if retrieval_score < self.min_score:
                continue

            context_vehicle = context.get("vehicle_type")
            context_role = self._detect_evidence_role(context)

            vehicle_score = self._vehicle_score(
                query_vehicle,
                context_vehicle,
            )

            role_score = self._role_score(
                query_role,
                context_role,
            )

            keyword_score = self._keyword_score(
                question,
                context,
            )

            final_score = (
                retrieval_score
                + vehicle_score
                + role_score
                + keyword_score
            )

            candidates.append({
                **context,
                "evidence_role": context_role,
                "evidence_score": final_score,
                "score_breakdown": {
                    "retrieval": retrieval_score,
                    "vehicle": vehicle_score,
                    "role": role_score,
                    "keyword": keyword_score,
                },
            })

        candidates.sort(
            key=lambda item: item["evidence_score"],
            reverse=True,
        )

        selected = candidates[:self.max_evidence]

        return {
            "question": question,
            "query_vehicle": query_vehicle,
            "query_role": query_role,
            "selected_evidence": selected,
            "requires_clarification": not bool(selected),
        }