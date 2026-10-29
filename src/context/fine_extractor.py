from __future__ import annotations

import re
import unicodedata


class FineExtractor:
    """
    OCR-aware Vietnamese fine extractor.

    Safety rules:
    - Normalize text labels only.
    - Never repair numeric OCR corruption.
    - Reject suspicious numeric formatting.
    - Do not infer missing fine amounts.
    """

    AMOUNT = r"(?:\d{1,3}(?:\.\d{3})+|\d+)"

    MONEY_PATTERN = re.compile(
        rf"phat\s*[\s.]+\s*tien\s+tu\s+"
        rf"(?P<minimum>{AMOUNT})\s*dong"
        rf"\s+den\s+"
        rf"(?P<maximum>{AMOUNT})\s*dong",
        flags=re.IGNORECASE,
    )

    @staticmethod
    def normalize_text(text: str) -> str:
        text = text.lower()

        # Strip accents for matching labels.
        text = unicodedata.normalize("NFD", text)

        text = "".join(
            char for char in text
            if unicodedata.category(char) != "Mn"
        )

        text = text.replace("đ", "d")

        # Normalize whitespace, but preserve
        # original number boundaries.
        text = re.sub(r"[ \t]+", " ", text)

        return text

    @staticmethod
    def parse_money(value: str) -> int:
        return int(value.replace(".", ""))

    def extract(self, text: str) -> dict | None:

        if not text:
            return None

        normalized = self.normalize_text(text)

        match = self.MONEY_PATTERN.search(
            normalized
        )

        if not match:
            return None

        minimum_raw = match.group("minimum")
        maximum_raw = match.group("maximum")

        minimum = self.parse_money(minimum_raw)
        maximum = self.parse_money(maximum_raw)

        if minimum <= 0 or maximum <= 0:
            return None

        if minimum > maximum:
            return None

        return {
            "min_vnd": minimum,
            "max_vnd": maximum,
            "raw_text": text,
            "status": "extracted_unverified",
        }