from __future__ import annotations

import re
import unicodedata
from typing import Any


class FineValidator:
    """Conservative classification of OCR-derived Vietnamese penalty text.

    This is NOT legal verification. No result is marked 'verified'.
    """

    AMOUNT = r"(?:\d{1,3}(?:\.\d{3})+|\d+)"
    RANGE_RE = re.compile(
        rf"(?P<min>{AMOUNT})\s*dong\s+den\s+(?P<max>{AMOUNT})\s*dong",
        re.I,
    )
    # The second range in a clause may omit the word 'phạt tiền'.
    SECOND_RANGE_RE = re.compile(
        rf"(?P<min>{AMOUNT})\s*dong\s+den\s+(?P<max>{AMOUNT})\s*dong",
        re.I,
    )
    BROKEN_NUMBER_RE = re.compile(r"\b\d{1,3}\.\s+\d{3}(?:\.\d{3})*\b")
    STRAY_DIGIT_RE = re.compile(r"\d(?:\.\d{3})+\s*\n\s*\d+\s*\n?\s*dong\b")
    NON_MONETARY_RE = re.compile(
        r"(?:hinh thuc xu phat bo sung|bien phap khac phuc hau qua|"
        r"ngoai viec bi (?:phat tien|ap dung hinh thuc xu phat))",
        re.I,
    )

    @staticmethod
    def normalize(text: str) -> str:
        text = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
        return "".join(c for c in text if unicodedata.category(c) != "Mn")

    @staticmethod
    def _amount(raw: str) -> int:
        return int(raw.replace(".", ""))

    def validate(self, text: str | None) -> dict[str, Any]:
        original = text or ""
        normalized = self.normalize(original)
        result: dict[str, Any] = {
            "status": "fine_not_found",
            "fine_ranges": [],
            "issues": [],
            "requires_manual_review": True,
            "verified": False,
        }
        if not original.strip():
            result["issues"].append("empty_text")
            return result

        if self.BROKEN_NUMBER_RE.search(normalized):
            result["issues"].append("broken_thousands_separator")
        if self.STRAY_DIGIT_RE.search(normalized):
            result["issues"].append("stray_digit_near_amount")
        # Do not trust even seemingly valid ranges if other digits look corrupt.
        if result["issues"]:
            result["status"] = "suspicious_ocr"
            return result

        for match in self.RANGE_RE.finditer(normalized):
            low = self._amount(match.group("min"))
            high = self._amount(match.group("max"))
            if low <= 0 or high <= 0 or low > high:
                result["issues"].append("invalid_fine_range")
                result["status"] = "suspicious_ocr"
                result["fine_ranges"] = []
                return result
            # Recover the local recipient label without asserting which applies.
            tail = normalized[match.end(): match.end() + 110]
            recipient = None
            recipient_match = re.search(r"\bdoi voi\s+(ca nhan|to chuc)\b", tail)
            if recipient_match:
                recipient = (
                    "individual" if recipient_match.group(1) == "ca nhan" else "organization"
                )
            result["fine_ranges"].append({
                "min_vnd": low,
                "max_vnd": high,
                "recipient_hint": recipient,
                "matched_text": original[match.start():match.end()],
            })

        if len(result["fine_ranges"]) > 1:
            result["status"] = "multiple_fines"
        elif len(result["fine_ranges"]) == 1:
            result["status"] = "extracted_unverified"
        elif self.NON_MONETARY_RE.search(normalized):
            result["status"] = "non_monetary_penalty"
        else:
            result["status"] = "fine_not_found"

        return result

