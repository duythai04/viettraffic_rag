import re

from src.ingestion.pdf_loader import PDFLoader
from src.preprocessing.cleaner import LegalTextCleaner
from src.ingestion.legal_parser import LegalParser


PDF_PATH = "data/processed/ocr/168-nd-cp.ocr.pdf"


SUSPICIOUS_POINT_PATTERN = re.compile(
    r"(?m)^[ \t]*"
    r"[._\-|:]*"
    r"[ \t]*"
    r"([01Il])"
    r"[ \t]*\)"
    r"[ \t]*"
    r"(.+)$"
)


def main():
    loader = PDFLoader()
    cleaner = LegalTextCleaner()
    parser = LegalParser()

    text = cleaner.clean(
        loader.load_document_text(PDF_PATH)
    )

    articles = parser.parse_articles(text)

    total_clauses = 0
    total_points = 0
    clauses_with_points = 0
    suspicious = []

    print("=" * 90)
    print("POINT STRUCTURE VALIDATION")
    print("=" * 90)

    for article in articles:
        article_number = article["article_number"]

        for clause in article["clauses"]:
            total_clauses += 1

            clause_number = clause["clause_number"]
            points = clause["points"]

            if points:
                clauses_with_points += 1
                total_points += len(points)

                letters = [
                    point["point"]
                    for point in points
                ]

                print(
                    f"Điều {article_number:<4} "
                    f"| Khoản {clause_number:<3} "
                    f"| Points: {letters}"
                )

            matches = list(
                SUSPICIOUS_POINT_PATTERN.finditer(
                    clause["content"]
                )
            )

            for match in matches:
                suspicious.append(
                    {
                        "article": article_number,
                        "clause": clause_number,
                        "marker": match.group(1),
                        "text": match.group(2).strip(),
                    }
                )

    print()
    print("=" * 90)
    print("SUMMARY")
    print("=" * 90)

    print(f"Total articles: {len(articles)}")
    print(f"Total clauses: {total_clauses}")
    print(
        f"Clauses with points: "
        f"{clauses_with_points}"
    )
    print(f"Total parsed points: {total_points}")
    print(
        f"Suspicious OCR markers: "
        f"{len(suspicious)}"
    )

    if suspicious:
        print()
        print("=" * 90)
        print("SUSPICIOUS POINT MARKERS")
        print("=" * 90)

        for item in suspicious:
            print()
            print(
                f"Điều {item['article']} "
                f"| Khoản {item['clause']} "
                f"| Marker: {item['marker']})"
            )

            print(
                f"Text: {item['text'][:180]}"
            )


if __name__ == "__main__":
    main()