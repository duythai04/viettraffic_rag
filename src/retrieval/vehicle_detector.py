from __future__ import annotations

import re
import unicodedata


class VehicleDetector:
    VEHICLE_PATTERNS = {
        "specialized_vehicle": [
            r"xe máy chuyên dùng",
            r"xe chuyên dùng",
            r"xe công trình",
            r"máy kéo",
        ],
        "bicycle": [
            r"xe đạp điện",
            r"xe đạp máy",
            r"xe đạp",
        ],
        "motorcycle": [
            r"xe máy điện",
            r"xe gắn máy",
            r"xe máy",
            r"xe mô tô",
            r"mô tô",
        ],
        "car": [
            r"ô tô",
            r"xe hơi",
            r"xe con",
            r"xe tải",
            r"xe khách",
            r"xe buýt",
        ],
        "pedestrian": [
            r"người đi bộ",
            r"đi bộ",
        ],
    }

    @staticmethod
    def _normalize(text: str) -> str:
        text = unicodedata.normalize("NFC", text.lower())
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def detect(self, question: str) -> str | None:
        if not isinstance(question, str):
            return None

        text = self._normalize(question)

        for vehicle_type, patterns in self.VEHICLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return vehicle_type

        return None