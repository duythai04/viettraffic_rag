import re
import unicodedata


class TrafficQueryNormalizer:
    LEGAL_EXPANSIONS = {
        "vượt đèn đỏ": (
            "không chấp hành hiệu lệnh của đèn tín hiệu giao thông"
        ),
        "vượt đèn vàng": (
            "không chấp hành hiệu lệnh của đèn tín hiệu giao thông"
        ),
        "không đội mũ bảo hiểm": (
            "không đội mũ bảo hiểm cho người đi mô tô xe máy"
        ),
    }

    def normalize(self, query: str) -> str:
        query = unicodedata.normalize("NFC", query)
        query = re.sub(r"\s+", " ", query)
        return query.strip()

    def expand(self, query: str) -> list[str]:
        normalized = self.normalize(query)

        if not normalized:
            raise ValueError("Query must not be empty")

        queries = [normalized]
        lower_query = normalized.lower()

        for phrase, legal_expression in self.LEGAL_EXPANSIONS.items():
            if phrase in lower_query:
                queries.append(legal_expression)

        return list(dict.fromkeys(queries))