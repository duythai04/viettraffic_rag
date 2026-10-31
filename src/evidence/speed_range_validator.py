from __future__ import annotations

import re
import unicodedata


class SpeedRangeValidator:
    """
    Kiểm tra mức vượt tốc độ có thuộc khoảng tốc độ
    được mô tả trong bằng chứng pháp lý hay không.

    Nguyên tắc:
    - Chỉ xử lý mức VƯỢT tốc độ cho phép.
    - Không suy diễn tốc độ thực tế thành mức vượt.
    - Không chấp nhận bằng chứng nếu không xác định
      được khoảng tốc độ áp dụng.
    """

    NUMBER = r"\d+(?:[.,]\d+)?"
    UNIT = r"(?:km\s*/\s*h|km\s*/\s*giờ|kmh)"

    @staticmethod
    def normalize(text: str | None) -> str:
        if text is None:
            return ""

        text = unicodedata.normalize(
            "NFC",
            str(text).lower(),
        )

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def to_float(value: str) -> float:
        return float(value.replace(",", "."))

    def extract_query_speed(
        self,
        question: str,
    ) -> float | None:
        """
        Ví dụ:

        'Xe máy vượt tốc độ 15 km/h'
            -> 15.0

        'Mức vượt quá tốc độ cho phép là 15 km/h'
            -> 15.0

        'Xe chạy 65 km/h'
            -> None
        """

        text = self.normalize(question)

        patterns = [
            (
                rf"mức vượt(?: quá)? tốc độ"
                rf"(?: cho phép| quy định)?"
                rf"(?: là)?\s*"
                rf"({self.NUMBER})\s*{self.UNIT}"
            ),
            (
                rf"(?:vượt|quá) tốc độ"
                rf"(?: cho phép| quy định)?\s*"
                rf"({self.NUMBER})\s*{self.UNIT}"
            ),
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                value = self.to_float(match.group(1))

                if value >= 0:
                    return value

        return None

    def extract_ranges(
        self,
        content: str,
    ) -> list[tuple[float, float, bool]]:
        """
        Kết quả:
            (min_speed, max_speed, max_inclusive)

        Ví dụ:
            từ 05 km/h đến dưới 10 km/h
                -> (5, 10, False)

            từ 10 km/h đến 20 km/h
                -> (10, 20, True)

            trên 20 km/h
                -> (20, inf, False)
        """

        text = self.normalize(content)

        ranges = []

        between_pattern = (
            rf"từ\s*({self.NUMBER})\s*{self.UNIT}\s*"
            rf"đến\s*(dưới\s*)?"
            rf"({self.NUMBER})\s*{self.UNIT}"
        )

        for match in re.finditer(
            between_pattern,
            text,
        ):
            low = self.to_float(match.group(1))
            high = self.to_float(match.group(3))

            high_inclusive = not bool(match.group(2))

            if low <= high:
                ranges.append(
                    (low, high, high_inclusive)
                )

        if ranges:
            return ranges

        above_pattern = (
            rf"(?:trên|lớn hơn)\s*"
            rf"({self.NUMBER})\s*{self.UNIT}"
        )

        for match in re.finditer(
            above_pattern,
            text,
        ):
            low = self.to_float(match.group(1))

            ranges.append(
                (low, float("inf"), False)
            )

        below_pattern = (
            rf"(?:dưới|nhỏ hơn)\s*"
            rf"({self.NUMBER})\s*{self.UNIT}"
        )

        for match in re.finditer(
            below_pattern,
            text,
        ):
            high = self.to_float(match.group(1))

            ranges.append(
                (0.0, high, False)
            )

        return ranges

    def validate(
        self,
        speed: float,
        content: str,
    ) -> bool:
        """
        True:
            Bằng chứng có khoảng tốc độ phù hợp.

        False:
            Không phù hợp hoặc không xác định
            được khoảng tốc độ.
        """

        ranges = self.extract_ranges(content)

        for low, high, high_inclusive in ranges:

            if high == float("inf"):
                if speed > low:
                    return True

            elif high_inclusive:
                if low <= speed <= high:
                    return True

            elif low <= speed < high:
                return True

        return False