from __future__ import annotations

import re
import unicodedata


class FineEvidenceEnricher:
    """
    Enrich selected legal evidence with fine lookup metadata.

    Only supports explicitly registered, reviewed mappings.

    This class does NOT verify monetary amounts.
    """

    SPEED_MOTORCYCLE_10_TO_20 = (
        "168-2024-ND-CP_dieu-7_khoan-4_diem-a"
    )

    @staticmethod
    def _normalize(text: str) -> str:
        text = unicodedata.normalize(
            "NFC",
            str(text).lower(),
        )
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def _is_motorcycle_question(cls, question: str) -> bool:
        text = cls._normalize(question)

        return bool(
            re.search(
                r"\b(xe máy|xe mô tô|mô tô|xe gắn máy)\b",
                text,
            )
        )

    @classmethod
    def _extract_speed(cls, question: str) -> int | None:
        text = cls._normalize(question)

        # The query must explicitly describe excess speed.
        if not re.search(
            r"(quá tốc độ|vượt tốc độ|vượt quá tốc độ)",
            text,
        ):
            return None

        # Prefer the explicit excess amount.
        patterns = [
            r"(?:vượt|quá)\s+"
            r"(\d{1,3})\s*km\s*/?\s*h",
            r"mức vượt[^\d]{0,30}"
            r"(\d{1,3})\s*km\s*/?\s*h",
            r"tốc độ[^\d]{0,50}"
            r"(\d{1,3})\s*km\s*/?\s*h",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                return int(match.group(1))

        return None

    @classmethod
    def enrich(
        cls,
        question: str,
        context: dict,
    ) -> dict:
        """
        Return a copy of the selected context.

        Do not enrich if the question, vehicle, speed,
        or legal evidence does not match.
        """
        result = dict(context)

        if result.get("chunk_id") != (
            cls.SPEED_MOTORCYCLE_10_TO_20
        ):
            return result

        if not cls._is_motorcycle_question(question):
            return result

        speed = cls._extract_speed(question)

        if speed is None:
            return result

        if not 10 <= speed <= 20:
            return result

        # Reject a contradictory vehicle classification.
        vehicle = result.get("vehicle_type")

        if vehicle not in (None, "", "motorcycle"):
            return result

        # Reject contradictory evidence metadata.
        expected = {
            "clause_id": (
                "168-2024-ND-CP_dieu-7_khoan-4"
            ),
            "vehicle_type": "motorcycle",
            "role": "driver",
            "violation_key": "speed_10_to_20",
        }

        for key, value in expected.items():
            existing = result.get(key)

            if existing not in (None, "", value):
                return result

        result.update(expected)

        return result
