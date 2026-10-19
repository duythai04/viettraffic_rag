from src.ingestion.pdf_loader import PDFLoader
from src.preprocessing.cleaner import LegalTextCleaner
from src.ingestion.legal_parser import LegalParser


PDF_PATH = "data/processed/ocr/168-nd-cp.ocr.pdf"

TARGETS = [
    (8, 6),
    (9, 1),
    (12, 2),
    (14, 1),
    (26, 2),
    (32, 9),
    (32, 14),
    (39, 1),
    (43, 5),
    (43, 6),
    (44, 4),
]


def main():
    loader = PDFLoader()
    cleaner = LegalTextCleaner()
    parser = LegalParser()

    text = cleaner.clean(
        loader.load_document_text(PDF_PATH)
    )

    articles = parser.parse_articles(text)

    for article_number, clause_number in TARGETS:
        article = parser.get_article(
            articles,
            article_number,
        )

        if not article:
            continue

        clause = next(
            (
                clause
                for clause in article["clauses"]
                if clause["clause_number"]
                == str(clause_number)
            ),
            None,
        )

        if not clause:
            continue

        print()
        print("=" * 90)
        print(
            f"ĐIỀU {article_number} "
            f"- KHOẢN {clause_number}"
        )
        print("=" * 90)

        for index, line in enumerate(
            clause["content"].splitlines()
        ):
            stripped = line.strip()

            if (
                stripped.startswith("c)")
                or stripped.startswith("d)")
                or stripped.startswith("đ)")
                or stripped.startswith("e)")
            ):
                print(
                    f"{index:03d}: {stripped}"
                )

        print(
            "PARSED:",
            [
                point["point"]
                for point in clause["points"]
            ],
        )


if __name__ == "__main__":
    main()