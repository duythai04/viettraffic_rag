from src.ingestion.pdf_loader import PDFLoader
from src.preprocessing.cleaner import LegalTextCleaner
from src.ingestion.legal_parser import LegalParser


PDF_PATH = "data/processed/ocr/168-nd-cp.ocr.pdf"


def main():
    loader = PDFLoader()
    cleaner = LegalTextCleaner()
    parser = LegalParser()

    text = cleaner.clean(
        loader.load_document_text(PDF_PATH)
    )

    articles = parser.parse_articles(text)

    total_missing = 0

    for article in articles:
        article_number = article["article_number"]

        for clause in article["clauses"]:
            points = clause["points"]

            if not points:
                continue

            validation = (
                parser.validate_point_sequence(
                    points
                )
            )

            missing = validation[
                "missing_points"
            ]

            if not missing:
                continue

            total_missing += 1

            print()
            print("=" * 90)
            print(
                f"ĐIỀU {article_number} "
                f"- KHOẢN "
                f"{clause['clause_number']}"
            )
            print(
                f"MISSING: {missing}"
            )
            print(
                "PARSED:",
                [
                    point["point"]
                    for point in points
                ],
            )
            print("-" * 90)

            for index, line in enumerate(
                clause["content"].splitlines()
            ):
                stripped = line.strip()

                if not stripped:
                    continue

                print(
                    f"{index:03d}: {stripped}"
                )

    print()
    print("=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print(
        f"Clauses with missing points: "
        f"{total_missing}"
    )


if __name__ == "__main__":
    main()