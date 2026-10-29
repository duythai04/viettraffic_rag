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
        "ô tô",
        "vượt đèn đỏ",
        "mũ bảo hiểm",
        "nồng độ cồn",
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
    )

    def detect(self, question: str) -> str:

        text = normalize_text(question)

        if not text:
            return "empty"

        cleaned = text.rstrip("!?., ")

        if cleaned in self.GREETINGS:
            return "greeting"

        if cleaned in self.IDENTITY:
            return "identity"

        if any(
            keyword in text
            for keyword in self.FINE_KEYWORDS
        ):
            return "legal_fine"

        if any(
            keyword in text
            for keyword in self.LEGAL_KEYWORDS
        ):
            return "legal_general"

        return "out_of_scope"