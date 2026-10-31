from __future__ import annotations

import re
import unicodedata


class ClarificationDetector:
    """
    Detect questions that lack essential information
    before legal retrieval and answer generation.
    """

    SPEED_KEYWORDS = (
        "quá tốc độ",
        "vượt tốc độ",
        "vượt quá tốc độ",
        "chạy quá tốc độ",
    )

    SPEED_VALUE_PATTERN = re.compile(
        r"\d+(?:[.,]\d+)?\s*(?:km/h|kmh|km/giờ)",
        re.IGNORECASE,
    )

    @staticmethod
    def normalize(text: str) -> str:
        text = unicodedata.normalize(
            "NFC",
            text.lower().strip(),
        )

        return re.sub(r"\s+", " ", text)

    def detect(self, question: str) -> dict:
        text = self.normalize(question)

        is_speed_question = any(
            keyword in text
            for keyword in self.SPEED_KEYWORDS
        )

        if not is_speed_question:
            return {
                "requires_clarification": False,
                "reason": None,
                "message": None,
            }

        has_speed_value = bool(
            self.SPEED_VALUE_PATTERN.search(text)
        )

        if has_speed_value:
            return {
                "requires_clarification": False,
                "reason": None,
                "message": None,
            }

        return {
            "requires_clarification": True,
            "reason": "missing_speed_excess",
            "message": (
                "Mức xử phạt đối với hành vi chạy quá "
                "tốc độ phụ thuộc vào số km/h vượt quá "
                "tốc độ cho phép. Bạn vui lòng cho biết "
                "phương tiện đã vượt tốc độ quy định "
                "bao nhiêu km/h để tôi xác định "
                "điều khoản phù hợp."
            ),
        }