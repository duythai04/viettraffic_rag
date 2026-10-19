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

    problems = []

    for article in articles:
        article_number = article["article_number"]

        for clause in article["clauses"]:
            points = clause["points"]

            if not points:
                continue

            result = parser.validate_point_sequence(
                points
            )

            has_problem = (
                bool(result["duplicate_points"])
                or bool(result["unknown_points"])
                or bool(result["missing_points"])
                or bool(result["out_of_order"])
            )

            if not has_problem:
                continue

            problem = {
                "article": article_number,
                "clause": clause["clause_number"],
                "points": [
                    point["point"]
                    for point in points
                ],
                "duplicate": result[
                    "duplicate_points"
                ],
                "missing": result[
                    "missing_points"
                ],
                "unknown": result[
                    "unknown_points"
                ],
                "out_of_order": result[
                    "out_of_order"
                ],
            }

            problems.append(problem)

    print("=" * 90)
    print("POINT VALIDATION")
    print("=" * 90)

    for problem in problems:
        print()
        print(
            f"Điều {problem['article']} "
            f"| Khoản {problem['clause']}"
        )

        print(
            "Points:",
            problem["points"],
        )

        print(
            "Missing:",
            problem["missing"],
        )

        print(
            "Duplicate:",
            problem["duplicate"],
        )

        print(
            "Unknown:",
            problem["unknown"],
        )

        print(
            "Out of order:",
            problem["out_of_order"],
        )

    print()
    print("=" * 90)
    print("SUMMARY")
    print("=" * 90)

    print(
        f"Total articles: {len(articles)}"
    )

    print(
        f"Problem clauses: {len(problems)}"
    )


if __name__ == "__main__":
    main()