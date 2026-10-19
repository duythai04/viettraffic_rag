import re


class LegalTextCleaner:
    """
    Clean extracted/OCR legal text while preserving
    legal structure such as Điều, Khoản and Điểm.
    """

    def clean(self, text: str) -> str:
        if not text:
            return ""

        # Normalize line endings
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        # Remove null characters
        text = text.replace("\x00", "")

        # Normalize non-breaking spaces
        text = text.replace("\xa0", " ")

        # Remove excessive spaces/tabs inside lines
        text = re.sub(r"[ \t]+", " ", text)

        # Remove spaces before newline
        text = re.sub(r" +\n", "\n", text)

        # Remove spaces at beginning of lines
        text = re.sub(r"(?m)^ +", "", text)

        # Maximum two consecutive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()