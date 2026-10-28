from __future__ import annotations

import re
import unicodedata


class VehicleDetector:
    VEHICLE_PATTERNS = {
        "specialized_vehicle": [
            r"\bxe máy chuyên dùng\b",
        ],
        "motorcycle": [
            r"\bxe máy\b",
            r"\bxe mô tô\b",
            r"\bmô tô\b",
            r"\bxe gắn máy\b",
        ],
        "car": [
            r"\bô tô\b",
            r"\bxe hơi\b",
        ],
        "bicycle": [
            r"\bxe đạp\b",
            r"\bxe đạp điện\b",
            r"\bxe đạp máy\b",
        ],
        "pedestrian": [
            r"\bngười đi bộ\b",
            r"\bđi bộ\b",
        ],
    }

    @staticmethod
    def normalize(text: str) -> str:
        text = unicodedata.normalize("NFC", text.lower())
        return re.sub(r"\s+", " ", text).strip()

    def detect(self, query: str) -> str | None:
        query = self.normalize(query)

        # Check specialized vehicle first.
        # Avoid classifying "xe máy chuyên dùng" as motorcycle.
        for vehicle_type, patterns in self.VEHICLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return vehicle_type

        return None