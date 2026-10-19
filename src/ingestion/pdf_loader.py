from pathlib import Path

import pymupdf


class PDFLoader:
  

    def load(self, file_path: str | Path) -> list[dict]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"File is not a PDF: {path}")

        pages = []

        with pymupdf.open(path) as document:
            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text")

                pages.append(
                    {
                        "page_number": page_number,
                        "text": text,
                        "char_count": len(text.strip()),
                        "source": path.name,
                        "source_path": str(path),
                    }
                )

        return pages

    def analyze(self, file_path: str | Path) -> dict:
        pages = self.load(file_path)

        total_pages = len(pages)

        total_chars = sum(
            page["char_count"]
            for page in pages
        )

        empty_pages = sum(
            1
            for page in pages
            if page["char_count"] == 0
        )

        text_pages = total_pages - empty_pages

        if total_pages == 0:
            text_ratio = 0.0
        else:
            text_ratio = text_pages / total_pages

        needs_ocr = (
            total_chars < 1000
            or text_ratio < 0.5
        )

        return {
            "file": Path(file_path).name,
            "total_pages": total_pages,
            "text_pages": text_pages,
            "empty_pages": empty_pages,
            "total_chars": total_chars,
            "text_ratio": round(text_ratio, 3),
            "needs_ocr": needs_ocr,
        }

    def load_document_text(self, file_path: str | Path) -> str:
        pages = self.load(file_path)

        texts = []

        for page in pages:
            text = page["text"].strip()

            if text:
                texts.append(text)

        return "\n\n".join(texts)