from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    text = unicodedata.normalize(
        "NFC",
        text.lower().strip(),
    )

    text = re.sub(r"\s+", " ", text)

    return text


class QueryIntentDetector:

    GREETINGS = {
        "xin chào",
        "chào",
        "hello",
        "hi",
        "hey",
        "chào bạn",
    }

    IDENTITY = {
        "bạn là ai",
        "bạn tên gì",
        "bạn làm được gì",
    }

    LEGAL_KEYWORDS = (
        "giao thông",
        "xe máy",
        "xe mô tô",
        "ô tô",
        "xe đạp",
        "xe tải",
        "vượt đèn đỏ",
        "đèn tín hiệu",
        "mũ bảo hiểm",
        "nồng độ cồn",
        "tốc độ",
        "biển báo",
        "giấy phép lái xe",
        "bằng lái",
        "xử phạt",
        "vi phạm",
        "nghị định",
        "điều luật",
        "đường bộ",
    )

    FINE_KEYWORDS = (
        "phạt bao nhiêu",
        "mức phạt",
        "phạt tiền",
        "bao nhiêu tiền",
        "bị phạt",
        "xử phạt bao nhiêu",
        "tiền phạt",
    )

    # Cách hỏi về chế tài, hình thức xử lý.
    SANCTION_PATTERNS = (
        r"\b(?:bị|sẽ bị|có thể bị)\s+"
        r"(?:xử phạt|xử lý)\b",

        r"\b(?:xử phạt|xử lý)\s+"
        r"(?:thế nào|như thế nào|ra sao)\b",

        r"\b(?:hình thức|chế tài)\s+"
        r"(?:xử phạt|xử lý)\b",
    )

    # Câu hỏi tìm hiểu quy định nói chung.
    GENERAL_PATTERNS = (
        r"\bquy định về\b",
        r"\bquy định như thế nào\b",
        r"\bđiều kiện\b",
        r"\bđược phép\b",
        r"\bcó được\b",
    )

    @staticmethod
    def _matches_patterns(
        text: str,
        patterns: tuple[str, ...],
    ) -> bool:
        return any(
            re.search(pattern, text)
            for pattern in patterns
        )

    def detect(self, question: str) -> str:
        if not isinstance(question, str):
            raise TypeError(
                "Question must be a string"
            )

        text = normalize_text(question)

        if not text:
            return "empty"

        cleaned = text.rstrip("!?., ")

        if cleaned in self.GREETINGS:
            return "greeting"

        if cleaned in self.IDENTITY:
            return "identity"

        has_legal_context = any(
            keyword in text
            for keyword in self.LEGAL_KEYWORDS
        )

        has_fine_keyword = any(
            keyword in text
            for keyword in self.FINE_KEYWORDS
        )

        has_sanction_intent = self._matches_patterns(
            text,
            self.SANCTION_PATTERNS,
        )

        has_general_intent = self._matches_patterns(
            text,
            self.GENERAL_PATTERNS,
        )

        # Các câu hỏi rõ ràng về mức tiền phạt.
        if has_fine_keyword:
            return "legal_fine"

        # Các câu hỏi về chế tài xử phạt.
        # Yêu cầu có ngữ cảnh giao thông/pháp luật
        # để tránh phân loại sai câu hỏi ngoài phạm vi.
        if has_sanction_intent and has_legal_context:
            return "legal_fine"

        # Các câu hỏi tìm hiểu quy định nói chung.
        if has_general_intent and has_legal_context:
            return "legal_general"

        if has_legal_context:
            return "legal_general"

        return "out_of_scope"