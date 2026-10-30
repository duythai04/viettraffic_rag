from __future__ import annotations

import re
import unicodedata


class AnswerValidator:
    MONEY_PATTERN = re.compile(
        r"\b\d[\d.,\s]*\s*(?:đồng|vnd|vnđ|triệu|tỷ)\b",
        re.IGNORECASE,
    )

    LEGAL_REFERENCE_PATTERN = re.compile(
        r"(?:điểm\s+([a-zđ])\s+)?"
        r"(?:khoản\s+(\d+)\s+)?"
        r"điều\s+(\d+)",
        re.IGNORECASE,
    )

    def __init__(self):
        pass

    @staticmethod
    def _normalize(text: str) -> str:
        text = unicodedata.normalize("NFC", text.lower())
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _allowed_references(
        self,
        contexts: list[dict],
    ) -> set[tuple]:
        allowed = set()

        for context in contexts:
            article = context.get("article")
            clause = context.get("clause")
            point = context.get("point")

            if article is None:
                continue

            allowed.add((
                str(article),
                str(clause) if clause is not None else None,
                str(point).lower() if point is not None else None,
            ))

        return allowed

    def _validate_references(
        self,
        answer: str,
        contexts: list[dict],
    ) -> bool:
        allowed = self._allowed_references(contexts)

        matches = self.LEGAL_REFERENCE_PATTERN.findall(answer)

        for point, clause, article in matches:
            reference = (
                article,
                clause or None,
                point.lower() if point else None,
            )

            if reference not in allowed:
                return False

        return True

    def validate(
        self,
        answer: str,
        contexts: list[dict],
        fine_verified: bool = False,
    ) -> dict:
        errors = []

        if not answer or not answer.strip():
            errors.append("empty_answer")

        if not fine_verified and self.MONEY_PATTERN.search(answer):
            errors.append("unverified_fine_amount")

        if not self._validate_references(answer, contexts):
            errors.append("unsupported_legal_reference")

        return {
            "valid": not errors,
            "errors": errors,
        }